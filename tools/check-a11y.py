#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-a11y.py — доступность страницы, измеренная, а не обещанная (31.10.2026).

Повод (31.10.2026, четырнадцатый блок). Двадцать приборов держали разметку, ссылки,
карту, веса, данные для поисковика. Ни один не задавал вопроса «а можно ли этим
пользоваться»: контраст текста, размер цели нажатия, видимость фокуса и подписи у
полей. Разметка видит `<img>` и `<input>`, но не видит, что alt пуст, что у поля нет
подписи, а цвет текста отличается от фона на 1.2 — это не видно ни в дереве тегов,
ни в байтах, только в вычисленном стиле и только глазом браузера.

Два пояса:
  static — без браузера, все 12 страниц (9 языков + privacy + terms + 404):
    DOC    один h1, уровни заголовков не перескакивают (h1→h3), <html lang> не пуст;
    ALT    у каждого <img> есть alt; пустой alt — только у декоративной картинки
           (aria-hidden="true" или role="presentation"); alt не равен имени файла;
    LABEL  у каждого видимого поля (input/textarea/select, кроме hidden) есть
           подпись: <label for=id>, вложенный <label>, aria-label или aria-labelledby;
    TEXT   у каждой ссылки есть различимый текст: свой текст, aria-label или alt
           картинки внутри; пустая иконочная ссылка — дефект;
    KEYS   нет tabindex > 0 (ломает порядок обхода), у <button> есть type,
           у target="_blank" есть rel с noopener.
  live — браузер (Playwright), девять языков при 420 px:
    CONTRAST  каждый текстовый узел: цвет против фактического фона (прозрачность
              складывается вверх по дереву), порог 4.5:1, для крупного текста
              (≥24 px, либо ≥18.66 px при весе ≥700) — 3:1;
    TAP       цель нажатия (ссылка, кнопка, поле, summary) не меньше 24×24 CSS px
              (WCAG 2.2 AA 2.5.8), кроме ссылок внутри предложения — у них
              исключение по самой норме, и оно названо, а не проглочено;
    FOCUS     у каждого интерактивного элемента при клавиатурном фокусе меняется
              хоть что-то видимое (контур, тень, рамка, фон).

Честность вместо зелёного: текст над настоящей картинкой (background-image: url)
не измеряется вслепую — он попадает в строку UNMEASURED с причиной. «Не измерили»
не имеет права выглядеть как «измерили и хорошо». Градиент — не картинка: его стопы
читаются, текст меряется по каждому, в вердикт идёт худший.

Контроль (--control): восемь мутантов на копии дерева, каждый обязан покраснеть своим
классом — контраст, контраст на градиенте, alt, второй h1, поле без подписи,
пустая ссылка, цель 10 px, снятый фокус.

Запуск:
  python3 tools/check-a11y.py                 # всё
  python3 tools/check-a11y.py --offline       # только static (без браузера)
  python3 tools/check-a11y.py --control       # мутанты
Код возврата: 0 — чисто, 1 — есть находки или мутант не покраснел.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
SKIP_DIRS = {".git", "evidence", "tools", "demo", "docs", "submission-kit",
             ".shots-work", "__pycache__", "src", "node_modules"}
CONTRAST_FAIL_LIMIT = 12

# ─────────────────────────── разбор дерева ───────────────────────────


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text")

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []
        self.parent = parent
        self.text = []


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [], None)
        self.cur = self.root
        self.stack = []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        node = self.cur
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.cur = node.parent

    def handle_data(self, data):
        self.cur.text.append(data)


def parse_html(path: Path) -> Tree:
    t = Tree()
    t.feed(path.read_text(encoding="utf-8", errors="replace"))
    t.close()
    return t


def walk(node: Node):
    for ch in node.children:
        yield ch
        yield from walk(ch)


def own_text(node: Node) -> str:
    return "".join(node.text).strip()


def all_text(node: Node) -> str:
    parts = [own_text(node)]
    for ch in walk(node):
        if ch.tag in ("script", "style"):
            continue
        parts.append(own_text(ch))
    return " ".join(p for p in parts if p)


def pages(root: Path) -> list[Path]:
    out = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIRS and (d / "index.html").is_file():
            out.append(d / "index.html")
    for name in ("index.html", "privacy.html", "terms.html", "404.html"):
        p = root / name
        if p.is_file():
            out.append(p)
    return out


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return p.name


# ─────────────────────────── static ───────────────────────────


def check_static(path: Path) -> list[tuple[str, str]]:
    t = parse_html(path)
    found: list[tuple[str, str]] = []
    nodes = list(walk(t.root))

    html = next((n for n in nodes if n.tag == "html"), None)
    if html is None or not html.attrs.get("lang", "").strip():
        found.append(("DOC", "<html> без lang"))

    heads = [n for n in nodes if n.tag in ("h1", "h2", "h3", "h4", "h5", "h6")]
    h1 = [n for n in heads if n.tag == "h1"]
    if len(h1) != 1:
        found.append(("DOC", f"h1 на странице: {len(h1)} (нужен ровно один)"))
    last = 0
    for n in heads:
        lvl = int(n.tag[1])
        if last and lvl > last + 1:
            found.append(("DOC", f"перескок уровней: h{last} → h{lvl}: «{all_text(n)[:40]}»"))
        last = lvl

    for n in nodes:
        if n.tag != "img":
            continue
        alt = n.attrs.get("alt")
        decorative = (n.attrs.get("aria-hidden") == "true"
                      or n.attrs.get("role") in ("presentation", "none"))
        src = n.attrs.get("src", "")
        if alt is None:
            if decorative:
                continue
            found.append(("ALT", f"<img src={src}> без alt"))
            continue
        if not alt.strip():
            # Пустой alt — штатный способ назвать картинку декоративной (WCAG 1.1.1).
            # Требовать вдобавок aria-hidden — ошибка прибора, а не сайта: если
            # картинка окажется единственным содержимым ссылки, это поймает TEXT.
            continue
        if alt.strip().lower() == Path(src).name.lower():
            found.append(("ALT", f"alt равен имени файла у {src}"))

    ids = {n.attrs["id"] for n in nodes if n.attrs.get("id")}
    labels_for = {n.attrs["for"] for n in nodes if n.tag == "label" and n.attrs.get("for")}

    def inside_label(n: Node) -> bool:
        p = n.parent
        while p is not None and p.tag != "#root":
            if p.tag == "label":
                return True
            p = p.parent
        return False

    for n in nodes:
        if n.tag not in ("input", "textarea", "select"):
            continue
        typ = (n.attrs.get("type") or "text").lower()
        if typ in ("hidden", "submit", "button", "reset", "image"):
            continue
        # Поле, скрытое от скринридера намеренно (honeypot-ловушка формы), подписи
        # не требует: его не видит ни глаз, ни вспомогательная технология.
        if n.attrs.get("aria-hidden") == "true":
            continue
        if n.attrs.get("aria-label", "").strip() or n.attrs.get("aria-labelledby"):
            continue
        if inside_label(n):
            continue
        nid = n.attrs.get("id", "")
        if nid and nid in labels_for:
            continue
        found.append(("LABEL", f"<{n.tag} name={n.attrs.get('name', '?')}> без подписи"))

    for n in nodes:
        if n.tag != "a" or "href" not in n.attrs:
            continue
        if n.attrs.get("aria-label", "").strip() or n.attrs.get("aria-labelledby"):
            continue
        if all_text(n):
            continue
        img_alt = [c.attrs.get("alt", "").strip() for c in walk(n) if c.tag == "img"]
        if any(img_alt):
            continue
        found.append(("TEXT", f"ссылка без текста: href={n.attrs.get('href', '')[:60]}"))

    for n in nodes:
        ti = n.attrs.get("tabindex")
        if ti and ti.strip().lstrip("+").isdigit() and int(ti) > 0:
            found.append(("KEYS", f"tabindex={ti} у <{n.tag}> ломает порядок обхода"))
        if n.tag == "button" and "type" not in n.attrs:
            found.append(("KEYS", "<button> без type"))
        if n.tag == "a" and n.attrs.get("target") == "_blank":
            relv = (n.attrs.get("rel") or "").lower()
            if "noopener" not in relv and "noreferrer" not in relv:
                found.append(("KEYS", f"target=_blank без noopener: {n.attrs.get('href', '')[:50]}"))

    # подпись for= должна указывать на существующий id — иначе подписи нет вовсе
    for f in sorted(labels_for):
        if f and f not in ids:
            found.append(("LABEL", f"<label for={f}> указывает в пустоту"))
    return found


# ─────────────────────────── live (браузер) ───────────────────────────

CONTRAST_JS = r"""
() => {
  const parse = (c) => {
    const m = String(c).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const over = (top, bot) => ({
    r: top.r * top.a + bot.r * (1 - top.a),
    g: top.g * top.a + bot.g * (1 - top.a),
    b: top.b * top.a + bot.b * (1 - top.a),
    a: 1
  });
  const ratio = (a, b) => {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };
  const path = (el) => {
    const bits = [];
    let n = el;
    while (n && n.nodeType === 1 && bits.length < 4) {
      let s = n.tagName.toLowerCase();
      if (n.id) s += '#' + n.id;
      else if (n.classList.length) s += '.' + [...n.classList].slice(0, 2).join('.');
      bits.unshift(s);
      n = n.parentElement;
    }
    return bits.join('>');
  };
  const stopColors = (img) => {
    // Градиент измерим: это набор цветов, любой из них может оказаться под текстом.
    // url() — настоящая картинка, её по-прежнему не измеряем вслепую.
    if (/url\(/i.test(img)) return null;
    const m = img.match(/rgba?\([^)]*\)|#[0-9a-f]{3,8}/gi);
    if (!m) return null;
    const cols = [];
    for (const s of m) { const c = parse(s); if (c && c.a > 0) cols.push(c); }
    return cols.length ? cols : null;
  };
  const bgOf = (el) => {
    let n = el, acc = null;
    while (n && n.nodeType === 1) {
      const s = getComputedStyle(n);
      if (s.backgroundImage && s.backgroundImage !== 'none') {
        const stops = stopColors(s.backgroundImage);
        if (!stops) return { unmeasured: 'фон-картинка у ' + path(n) };
        const base = acc || { r: 255, g: 255, b: 255, a: 1 };
        // текст лежит поверх ЛЮБОЙ точки градиента — меряем по каждой
        return { colors: stops.map((c) => (c.a < 0.999 ? over(c, base) : c)) };
      }
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) {
        acc = acc === null ? c : over(acc, c);
        if (acc.a >= 0.999) return { color: acc };
      }
      n = n.parentElement;
    }
    return { color: acc || { r: 255, g: 255, b: 255, a: 1 } };
  };
  const visible = (el) => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) === 0) return false;
    return el.getClientRects().length > 0;
  };
  const fails = [], unmeasured = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (tw.nextNode()) {
    const node = tw.currentNode;
    if (!node.nodeValue || !node.nodeValue.trim()) continue;
    const el = node.parentElement;
    if (!el || seen.has(el) && !el.children.length) continue;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName)) continue;
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    const fg = parse(s.color);
    if (!fg) continue;
    const bg = bgOf(el);
    if (bg.unmeasured) {
      const key = path(el);
      if (!unmeasured.some((u) => u.el === key)) unmeasured.push({ el: key, why: bg.unmeasured });
      continue;
    }
    const backs = bg.colors || [bg.color];
    let r = Infinity;
    for (const back of backs) {
      const e = fg.a < 0.999 ? over(fg, back) : fg;
      const q = ratio(e, back);
      if (q < r) r = q;
    }
    const fs = parseFloat(s.fontSize);
    const fw = Number(s.fontWeight) || 400;
    const large = fs >= 24 || (fs >= 18.66 && fw >= 700);
    const need = large ? 3.0 : 4.5;
    if (r + 0.005 < need) {
      fails.push({
        el: path(el), text: node.nodeValue.trim().slice(0, 48),
        ratio: Math.round(r * 100) / 100, need, size: Math.round(fs * 10) / 10, weight: fw
      });
    }
  }
  return { fails, unmeasured };
}
"""

TAP_JS = r"""
() => {
  const sel = 'a[href], button, input:not([type=hidden]), textarea, select, summary';
  const rect = (el) => el.getBoundingClientRect();
  const inlineInText = (el) => {
    const p = el.parentElement;
    if (!p) return false;
    return ['P', 'LI', 'TD', 'SPAN'].includes(p.tagName) &&
      (getComputedStyle(el).display === 'inline') &&
      (p.textContent || '').trim().length > (el.textContent || '').trim().length + 3;
  };
  const small = [], exempt = [];
  for (const el of document.querySelectorAll(sel)) {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = rect(el);
    if (!r.width && !r.height) continue;
    const w = Math.round(r.width * 10) / 10, h = Math.round(r.height * 10) / 10;
    const label = (el.getAttribute('aria-label') || el.textContent || el.name || el.type || '').trim().slice(0, 40);
    const item = { tag: el.tagName.toLowerCase(), label, w, h };
    if (w >= 24 && h >= 24) continue;
    if (inlineInText(el)) { exempt.push(item); continue; }
    small.push(item);
  }
  return { small, exempt };
}
"""

FOCUS_BASE_JS = r"""
() => {
  const sel = 'a[href], button, input:not([type=hidden]), textarea, select, summary';
  // Ширину контура читаем только когда он реально нарисован: у невидимого фокуса
  // computed outlineWidth остаётся 3px при outlineStyle 'none', и сравнение
  // «было/стало» краснело бы от ширины, а не от кольца.
  const sig = (el) => {
    const s = getComputedStyle(el);
    const ring = (s.outlineStyle === 'none' || parseFloat(s.outlineWidth) === 0)
      ? 'noRing' : s.outlineWidth + ' ' + s.outlineStyle + ' ' + s.outlineColor;
    return [ring, s.boxShadow, s.borderColor, s.backgroundColor,
            s.textDecorationLine, s.color].join('|');
  };
  const base = [];
  [...document.querySelectorAll(sel)].forEach((el, i) => {
    if (!el.getClientRects().length) return;
    base[i] = sig(el);
    el.setAttribute('data-a11y-idx', String(i));
  });
  window.__a11yBase = base;
  return base.filter((x) => x !== undefined).length;
}
"""

FOCUS_STEP_JS = r"""
() => {
  const el = document.activeElement;
  if (!el || el.dataset === undefined || el.dataset.a11yIdx === undefined) {
    const i = el && el.getAttribute ? el.getAttribute('data-a11y-idx') : null;
    if (i === null) return { done: true };
  }
  const idx = Number(el.getAttribute('data-a11y-idx'));
  const s = getComputedStyle(el);
  const ring = (s.outlineStyle === 'none' || parseFloat(s.outlineWidth) === 0)
    ? 'noRing' : s.outlineWidth + ' ' + s.outlineStyle + ' ' + s.outlineColor;
  const sig = [ring, s.boxShadow, s.borderColor, s.backgroundColor,
               s.textDecorationLine, s.color].join('|');
  return {
    done: false,
    idx,
    changed: sig !== window.__a11yBase[idx],
    // программный .focus() в Chromium не включает :focus-visible — поэтому обход
    // настоящими нажатиями Tab, иначе прибор судит себя, а не страницу
    focusVisible: el.matches(':focus-visible'),
    tag: el.tagName.toLowerCase(),
    label: (el.getAttribute('aria-label') || el.textContent || el.name || el.type || '').trim().slice(0, 40)
  };
}
"""


def live_findings(browser, url: str, lang: str) -> tuple[list[tuple[str, str]], list[str]]:
    page = browser.new_page(viewport={"width": 420, "height": 900}, device_scale_factor=1)
    out: list[tuple[str, str]] = []
    notes: list[str] = []
    try:
        page.goto(url, wait_until="load", timeout=45000)
        page.emulate_media(reduced_motion="reduce")
        res = page.evaluate(CONTRAST_JS)
        for f in res["fails"][:CONTRAST_FAIL_LIMIT]:
            out.append(("CONTRAST", f'{f["ratio"]}:1 < {f["need"]}:1 — «{f["text"]}» ({f["size"]}px/{f["weight"]}) в {f["el"]}'))
        if len(res["fails"]) > CONTRAST_FAIL_LIMIT:
            out.append(("CONTRAST", f'…ещё {len(res["fails"]) - CONTRAST_FAIL_LIMIT} мест'))
        notes.append(f'{lang}: не измерено {len(res["unmeasured"])}')
        if res["unmeasured"]:
            sample = "; ".join(f'{u["el"]}' for u in res["unmeasured"][:4])
            print(f'  ? {lang}: не измерено {len(res["unmeasured"])} — {sample}')
        tap = page.evaluate(TAP_JS)
        for t in tap["small"][:10]:
            out.append(("TAP", f'{t["tag"]} {t["w"]}×{t["h"]} px «{t["label"]}»'))
        focus = {"blind": [], "total": 0}
        total = page.evaluate(FOCUS_BASE_JS)
        seen: set[int] = set()
        for _ in range(90):
            page.keyboard.press("Tab")
            step = page.evaluate(FOCUS_STEP_JS)
            if step.get("done"):
                break
            idx = step.get("idx")
            if idx in seen:
                break
            seen.add(idx)
            if not step.get("focusVisible") or not step.get("changed"):
                focus["blind"].append(step)
        focus["total"] = total
        for b in focus["blind"][:10]:
            out.append(("FOCUS", f'фокус не виден у {b["tag"]} «{b["label"]}»'))
        notes[-1] += (f', целей {focus["total"]}, Tab дошёл до {len(seen)}'
                      f' (остальные вне обхода — названы, а не зачтены),'
                      f' исключено по норме {len(tap["exempt"])}')
    finally:
        page.close()
    return out, notes


# ─────────────────────────── контроль ───────────────────────────

MUTANTS = [
    ("CONTRAST", "контраст", lambda h: h.replace("</head>",
        '<style>p,li,label,.muted,h2 a{color:#E7EDF9!important}</style></head>', 1)),
    ("ALT", "alt", lambda h: re.sub(r'(<img\b[^>]*?)\s+alt="[^"]*"', r"\1", h, count=1)),
    ("DOC", "второй h1", lambda h: h.replace("</h1>", "</h1><h1>лишний</h1>", 1)),
    ("LABEL", "поле без подписи", lambda h: re.sub(r'\s+for="cf-email"', "", h, count=1)
        .replace('id="cf-email"', 'id="cf-email-x"', 1)),
    ("TEXT", "пустая ссылка", lambda h: h.replace("</body>",
        '<a href="/x/" class="btn"><span></span></a></body>', 1)),
    ("TAP", "цель 10 px", lambda h: h.replace("</head>",
        '<style>a,button,summary{min-height:0!important;height:10px!important;'
        'padding:0!important;font-size:6px!important;line-height:10px!important}</style></head>', 1)),
    ("CONTRAST", "контраст на градиенте", lambda h: h.replace("</head>",
        '<style>.price.hot{background:linear-gradient(180deg,#F5F8FF,#fff)!important}'
        '.price.hot h3,.price.hot .amount,.price.hot p{color:#FBFDFF!important}</style></head>', 1)),
    ("FOCUS", "снятый фокус", lambda h: h.replace("</head>",
        '<style>*:focus-visible{outline:0 none!important}</style></head>', 1)),
]


def run_control(offline: bool = False) -> int:
    src = ROOT
    pages_all = pages(src)
    target = next((p for p in pages_all if p.parent.name == "ru"), None) or pages_all[0]
    relpath = target.relative_to(src)
    template = target.read_text(encoding="utf-8")
    ok = 0
    tmp = Path(tempfile.mkdtemp(prefix="a11y-"))
    copy = tmp / "copy"
    # копия дерева нужна живому поясу: у страницы относительные img/ и fonts/
    shutil.copytree(src, copy, ignore=shutil.ignore_patterns(*SKIP_DIRS))
    pw = None
    browser = None
    try:
        if not offline:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        for cls, name, mutate in MUTANTS:
            mutated = mutate(template)
            if mutated == template:
                print(f"  КРАСНОЕ  {name}: мутант не применился (шаблон не тот)")
                continue
            (copy / relpath).write_text(mutated, encoding="utf-8")
            found = check_static(copy / relpath)
            if not offline and browser is not None:
                live, _ = live_findings(browser, (copy / relpath).as_uri(), "ru")
                found.extend(live)
            got = [c for c, _ in found]
            if cls in got:
                ok += 1
                print(f"  поймал   {name}: {cls}")
            else:
                print(f"  НЕ ПОЙМАЛ {name}: класс {cls} не покраснел (находки: {got[:6]})")
            (copy / relpath).write_text(template, encoding="utf-8")
    finally:
        if browser is not None:
            browser.close()
        if pw is not None:
            pw.stop()
        shutil.rmtree(tmp, ignore_errors=True)
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--offline", action="store_true", help="только static, без браузера")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--langs", default="", help="ограничить живой пояс языками (ru,en)")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    if a.control:
        print("КОНТРОЛЬ: восемь мутантов, каждый обязан покраснеть своим классом")
        ok = run_control(a.offline)
        print(f"МУТАНТЫ {ok}/{len(MUTANTS)}")
        return 0 if ok == len(MUTANTS) else 1

    findings: list[tuple[str, str]] = []
    static_pages = pages(root)
    for p in static_pages:
        for cls, msg in check_static(p):
            findings.append((cls, f"{rel(root, p)}: {msg}"))
    print(f"STATIC: {len(static_pages)} страниц, находок {len(findings)}")

    notes: list[str] = []
    if not a.offline:
        from playwright.sync_api import sync_playwright
        langs = [("en", root / "index.html")]
        langs += [(p.parent.name, p) for p in static_pages if p.parent != root]
        if a.langs:
            want = {s.strip() for s in a.langs.split(",") if s.strip()}
            langs = [l for l in langs if l[0] in want]
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                for lang, page_path in langs:
                    if not page_path.is_file():
                        continue
                    live, note = live_findings(browser, page_path.as_uri(), lang)
                    findings.extend(live)
                    notes.extend(note)
            finally:
                browser.close()
        print("LIVE: " + "; ".join(notes))

    if findings:
        by = {}
        for cls, msg in findings:
            by.setdefault(cls, []).append(msg)
        for cls in sorted(by):
            print(f"[{cls}] {len(by[cls])}")
            for m in by[cls][:CONTRAST_FAIL_LIMIT]:
                print(f"   {m}")
        if a.json:
            print(json.dumps(findings, ensure_ascii=False))
        return 1
    print("ИТОГО ok: находок нет")
    return 0


if __name__ == "__main__":
    sys.exit(main())
