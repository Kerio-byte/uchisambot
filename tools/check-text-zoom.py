#!/usr/bin/env python3
"""check-text-zoom.py — страница с УВЕЛИЧЕННЫМ ШРИФТОМ: 200 % текста в тех же коробках.

Повод (31.10.2026, двадцатый блок). Пятьдесят пять батарей держали эту страницу, и все
они смотрели на текст одного размера — того, который задал автор. `narrow-320` мерил
320 px, `visual-420` — 420 px, `a11y` — контраст и цели нажатия. Размер ШРИФТА при этом
не менял никто: все три инструмента открывают страницу с настройками по умолчанию.

А человек приходит с другой настройкой. В Telegram на Android страница открывается во
встроенном WebView, и он подчиняется системному «Размер шрифта» — у людей с плохим
зрением он стоит на «Очень большой», это текст в 1.3–2 раза крупнее авторского при
ТОЙ ЖЕ ширине окна. На iPhone то же делает «Крупный текст» и масштаб в Safari. То есть
класс посетителей, для которых текст удваивается, а коробки — нет, существует и он
не маленький: это родители школьников, та самая аудитория страницы.

Дефект этого класса не виден ни одному прибору в каталоге: при 100 % всё цело, при 200 %
слово в заголовке шире своего блока и уезжает под обрез `overflow: hidden`, строка в
кнопке не влезает в фиксированную высоту, ряд языков разъезжается на четыре строки и
налезает на логотип. Глазом это тоже не видно — глаз смотрит на 100 %, как и приборы.

Что меряется (на каждом из девяти языков, три клаузы):
  1. H-OVERFLOW     ширина документа не выросла за окно: doc.scrollWidth <= want + 1.
                    Из вылезших элементов исключаются те, что внутри НАСТОЯЩЕЙ ленты
                    (overflow-x: auto со своей прокруткой) — они законно за краем.
  2. TEXT-CLIPPED   текст не обрезан: у каждого текстового узла его прямоугольник
                    (Range.getBoundingClientRect) обязан лежать внутри padding-box
                    каждого предка, который режет (overflow hidden/clip по этой оси).
                    Проверяются ОБЕ оси: по высоте — фиксированная высота блока,
                    по ширине — длинное слово без переноса.
  3. TAP-SMALL      цель нажатия осталась не меньше 24x24 CSS px (WCAG 2.5.8) —
                    увеличение шрифта не должно превращать кнопку в строку текста.

Зум ставится не «примерно»: каждому элементу страницы его вычисленный font-size
умножается на 2 инлайново — ровно так работает текстовый зум (текст крупнее, коробки
те же). Прибор печатает, СКОЛЬКО элементов он увеличил: если меньше полусотни, он
слепой и говорить «чисто» права не имеет (строка INSTRUMENT BLIND, код 1).

Ложный зелёный исключён контролем (`--control`, копия дерева):
  копия без правок обязана быть ЗЕЛЁНОЙ (иначе красное ниже ничего не доказывает),
  затем три мутанта, каждый обязан покраснеть своим сообщением:
    M1 clip  — заголовок в `height:30px;overflow:hidden`  -> TEXT-CLIPPED
    M2 wide  — блок 900 px с текстом `nowrap`             -> H-OVERFLOW
    M3 tap   — кнопка `width:12px;height:12px`            -> TAP-SMALL

Запуск:
  python3 tools/check-text-zoom.py                  # 9 языков, 420 px, зум 200 %
  python3 tools/check-text-zoom.py --zoom 1.5       # мягче
  python3 tools/check-text-zoom.py --control        # доказательство прибора
  python3 tools/check-text-zoom.py --langs=ru,hi    # только эти
Код возврата: 0 — чисто, 1 — находки или мутант не покраснел.
Пишет evidence/text-zoom-<дата>.json (контроль — отдельным файлом).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(os.environ.get("LANDING_ROOT") or Path(__file__).resolve().parents[1])
# Порт и петля в коде не зашиты (правило opsec свипа): по умолчанию страница открывается
# файлом с диска, веб-сервер не нужен. Нужен HTTP — задай LANDING_URL=http://host:port.
BASE = os.environ.get("LANDING_URL", "").rstrip("/")
OUT = Path(os.environ.get("LANDING_OUT",
                          ROOT / "evidence" / f"text-zoom-{date.today():%Y%m%d}.json"))
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
WIDTH = 420          # современный телефон; 320 px держит отдельная батарея narrow-320
ZOOM = 2.0           # WCAG 1.4.4 Resize text: 200 % без потери содержания

# Зум текста: каждому элементу — его вычисленный размер, умноженный на ZOOM.
APPLY = r"""
(z) => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'HEAD', 'META', 'LINK', 'TITLE']);
  // Два прохода — и это не стиль. Первый проход только ЧИТАЕТ авторские размеры;
  // если писать инлайн по ходу чтения, у ребёнка с font-size:1em вычисленный размер
  // уже включает увеличенного предка, и зум складывается каскадом (2 -> 4 -> 8 -> 1024 px).
  // 31.10.2026 прибор именно так и соврал на первом прогоне: «font: 1024» в находках.
  const items = [];
  for (const el of document.querySelectorAll('body *')) {
    if (skip.has(el.tagName)) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (!isFinite(fs) || fs <= 0.5) continue;
    items.push([el, fs]);
  }
  for (const [el, fs] of items) {
    el.style.setProperty('font-size', (fs * z).toFixed(2) + 'px', 'important');
  }
  return items.length;
}
"""

PROBE = r"""
(want) => {
  const name = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (typeof el.className === 'string' && el.className.trim()) {
      s += '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.');
    }
    return s;
  };
  const srOnly = (el) => {
    const c = (typeof el.className === 'string') ? el.className : '';
    return /sr-only|visually-hidden|screen-reader|a11y-hidden/.test(c);
  };
  // rect элемента, который режет: padding-box = границы, ВНУТРИ которых обязан лежать текст
  const box = (el) => {
    const r = el.getBoundingClientRect();
    return { top: r.top + el.clientTop, left: r.left + el.clientLeft,
             right: r.left + el.clientLeft + el.clientWidth,
             bottom: r.top + el.clientTop + el.clientHeight };
  };
  const docW = document.documentElement.scrollWidth;
  const bodyW = document.body.scrollWidth;
  // Диагностика «документ шире окна, а виновника нет»: элементы, которые фильтр выше
  // отбросил (нулевая высота, opacity 0, visibility hidden), тоже могут растить
  // scrollWidth — прибор обязан назвать их, иначе он говорит «не знаю» молча.
  const widest = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.right <= want + 1) continue;
    const cs = getComputedStyle(el);
    widest.push({ el: name(el), right: Math.round(r.right), w: Math.round(r.width),
                  h: Math.round(r.height),
                  why: cs.display === 'none' ? 'display:none'
                     : cs.visibility === 'hidden' ? 'visibility:hidden'
                     : cs.opacity === '0' ? 'opacity:0'
                     : (r.width < 1 || r.height < 1) ? 'zero-size' : 'reported' });
  }
  widest.sort((a, b) => b.right - a.right);
  // Закрытая гармошка — не обрез. В `<details>` без open ответ лежит ниже сложенного
  // блока и режется его `overflow: hidden`: это ровно то, что делает аккордеон.
  // 31.10.2026 без этой оговорки прибор давал 11 ложных строк на КАЖДОМ прогоне —
  // и на 100 %, и на 200 %, то есть мерил норму, а не дефект.
  const inClosed = (el) => {
    let a = el;
    while (a && a !== document.body) {
      if (a.tagName === 'DETAILS' && !a.open) {
        const s = a.querySelector(':scope > summary');
        if (!s || !s.contains(el)) return true;   // ответ закрытой гармошки
      }
      a = a.parentElement;
    }
    return false;
  };

  // ---- 1. вылезание за окно (ленты исключаются) -------------------------------
  const off = [], carousel = [];
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.right > want + 1.5 || r.left < -1.5) {
      let sc = el.parentElement, inScroller = false;
      while (sc && sc !== document.body && sc !== document.documentElement) {
        const so = getComputedStyle(sc).overflowX;
        if (so === 'auto' || so === 'scroll') {
          const sr = sc.getBoundingClientRect();
          if (sc.scrollWidth > sc.clientWidth + 2 && sr.right <= want + 1.5) inScroller = true;
          break;
        }
        sc = sc.parentElement;
      }
      const rec = { el: name(el), left: Math.round(r.left), right: Math.round(r.right),
                    text: (el.textContent || '').trim().slice(0, 40) };
      (inScroller ? carousel : off).push(rec);
    }
  }

  // ---- 2. текст, вылезший за режущего предка: обе оси ------------------------
  const clip = [];
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node, checked = 0;
  while ((node = walker.nextNode())) {
    const txt = (node.nodeValue || '').trim();
    if (!txt) continue;
    const parent = node.parentElement;
    if (!parent || srOnly(parent) || inClosed(node)) continue;
    const pcs = getComputedStyle(parent);
    if (pcs.display === 'none' || pcs.visibility === 'hidden' || pcs.opacity === '0') continue;
    if (parseFloat(pcs.fontSize) < 2) continue;
    const rg = document.createRange();
    rg.selectNodeContents(node);
    const tr = rg.getBoundingClientRect();
    if (tr.width < 1 || tr.height < 1) continue;      // узел не отрисован
    checked++;
    let a = parent;
    while (a && a !== document.documentElement) {
      const acs = getComputedStyle(a);
      const hidesY = (acs.overflowY === 'hidden' || acs.overflowY === 'clip');
      const hidesX = (acs.overflowX === 'hidden' || acs.overflowX === 'clip');
      if ((hidesY || hidesX) && a.clientWidth > 0 && a.clientHeight > 0 && !srOnly(a)) {
        const b = box(a);
        const dyR = hidesY ? tr.bottom - b.bottom : -1e9;   // текст ниже низа
        const dyL = hidesY ? b.top - tr.top : -1e9;         // текст выше верха
        const dxR = hidesX ? tr.right - b.right : -1e9;     // текст правее
        const dxL = hidesX ? b.left - tr.left : -1e9;       // текст левее
        const dy = Math.max(dyR, dyL), dx = Math.max(dxR, dxL);
        const worst = Math.max(dy, dx);
        if (worst > 1.5) {
          const key = name(a) + '|' + txt.slice(0, 30);
          if (!seen.has(key)) {
            seen.add(key);
            clip.push({ el: name(a), axis: dy >= dx ? 'y' : 'x',
                        side: dy >= dx ? (dy > dyR ? 'top' : 'bottom')
                                       : (dx > dxR ? 'left' : 'right'),
                        dx: Math.round(dx), dy: Math.round(dy),
                        over: Math.round(worst), font: Math.round(parseFloat(pcs.fontSize)),
                        cw: a.clientWidth, ch: a.clientHeight,
                        box: [Math.round(b.left), Math.round(b.top),
                              Math.round(b.right), Math.round(b.bottom)],
                        txt: [Math.round(tr.left), Math.round(tr.top),
                              Math.round(tr.right), Math.round(tr.bottom)],
                        open: a.tagName === 'DETAILS' ? a.open : undefined,
                        text: txt.slice(0, 48) });
          }
          break;
        }
      }
      a = a.parentElement;
    }
  }

  // ---- 3. цели нажатия не ссохлись ------------------------------------------
  const small = [];
  for (const el of document.querySelectorAll('button, .btn, a.btn, .button, a[role="button"]')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.height < 23.5 || r.width < 23.5) {
      small.push({ el: name(el), w: Math.round(r.width), h: Math.round(r.height),
                   text: (el.textContent || '').trim().slice(0, 30) });
    }
  }

  return { want, docW, bodyW, textNodes: checked,
           widest: widest.filter(w => w.why !== 'reported').slice(0, 4),
           offCount: off.length, off: off.slice(0, 6),
           carouselCount: carousel.length,
           clipCount: clip.length, clip: clip.slice(0, 8),
           smallCount: small.length, small: small.slice(0, 6),
           pageH: Math.round(document.documentElement.scrollHeight) };
}
"""


def route(lang: str) -> str:
    return "/index.html" if lang == "en" else f"/{lang}/index.html"


def url_for(lang: str, root: Path = ROOT) -> str:
    r = route(lang)
    return BASE + r if BASE else (root / r.lstrip("/")).as_uri()


def verdict(pr: dict) -> list[str]:
    bad = []
    if pr["docW"] > pr["want"] + 1 or pr["bodyW"] > pr["want"] + 1:
        bad.append("H-OVERFLOW")
    if pr["clipCount"]:
        bad.append("TEXT-CLIPPED")
    if pr["smallCount"]:
        bad.append("TAP-SMALL")
    if pr["textNodes"] < 40 or pr["docW"] < 100:
        bad.append("BLIND")      # страница не прочиталась — «чисто» было бы ложью
    return bad


def run(browser, langs: list[str], zoom: float, root: Path, label: str,
        width: int = WIDTH) -> tuple[list[dict], int]:
    rows, fails = [], 0
    for lang in langs:
        ctx = browser.new_context(viewport={"width": width, "height": 900}, is_mobile=True,
                                  has_touch=True, device_scale_factor=2)
        pg = ctx.new_page()
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url_for(lang, root), wait_until="load")
        pg.wait_for_timeout(600)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")   # догрузить ленивое
        pg.wait_for_timeout(900)
        pg.evaluate("window.scrollTo(0, 0)")
        pg.wait_for_timeout(250)
        zoomed = pg.evaluate(APPLY, zoom)
        pg.wait_for_timeout(250)
        pr = pg.evaluate(PROBE, width)
        pr.update({"lang": lang, "zoomed": zoomed, "jsErrors": errs})
        bad = verdict(pr)
        if errs:
            bad.append("JS-ERROR")
        pr["bad"] = bad
        if bad:
            fails += 1
        rows.append(pr)
        print(f"{'FAIL' if bad else 'OK  '} {label}{lang}: doc={pr['docW']} want={pr['want']} "
              f"zoom={zoomed}el clip={pr['clipCount']} off={pr['offCount']} "
              f"carousel={pr['carouselCount']} tap={pr['smallCount']} "
              f"h={pr['pageH']} {','.join(bad)}")
        if bad:
            for k in ("off", "clip", "small"):
                for it in pr[k][:3]:
                    print("      ", json.dumps(it, ensure_ascii=False))
            if "H-OVERFLOW" in bad:
                for w in pr["widest"][:4]:
                    print("      ?", json.dumps(w, ensure_ascii=False))
        ctx.close()
    return rows, fails


def mutant_tree(src: Path, mut: str) -> Path:
    """Копия дерева (как у соседних контролей) + один дефект в ru/index.html."""
    import shutil
    import tempfile
    skip = {".git", "evidence", ".shots-work", "tools", "src", "docs", "submission-kit",
            "__pycache__"}
    dst = Path(tempfile.mkdtemp(prefix="zoom-mut-"))
    for item in src.iterdir():
        if item.name in skip:
            continue
        (shutil.copytree(item, dst / item.name) if item.is_dir()
         else shutil.copy2(item, dst / item.name))
    ru = dst / "ru" / "index.html"
    html = ru.read_text(encoding="utf-8")
    if mut == "clip":
        marker = "</h1>"
        i = html.find(marker)
        assert i > 0, "не нашёл h1 для мутанта clip"
        j = html.rfind("<h1", 0, i)
        html = html[:j] + '<div style="height:30px;overflow:hidden">' + html[j:i + 5] + "</div>" + html[i + 5:]
    elif mut == "wide":
        html = html.replace("</body>", '<div style="width:900px;white-space:nowrap;'
                                        'font-size:28px">mutant wide line that cannot wrap</div>'
                                        "</body>", 1)
    elif mut == "tap":
        html = html.replace("</body>", '<button type="button" style="width:12px;height:12px">'
                                        "m</button></body>", 1)
    else:
        raise SystemExit(f"неизвестный мутант {mut}")
    ru.write_text(html, encoding="utf-8")
    return dst


def run_control(zoom: float) -> int:
    import shutil
    from playwright.sync_api import sync_playwright

    print(f"КОНТРОЛЬ прибора (зум {zoom:g}): чистая копия обязана быть зелёной, "
          f"три мутанта — красными")
    results: dict[str, object] = {}
    ok = True
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        # A. нетронутая копия: без этого красное на мутанте ничего не доказывает
        import tempfile
        clean = Path(tempfile.mkdtemp(prefix="zoom-clean-"))
        skip = {".git", "evidence", ".shots-work", "tools", "src", "docs", "submission-kit",
                "__pycache__"}
        for item in ROOT.iterdir():
            if item.name in skip:
                continue
            (shutil.copytree(item, clean / item.name) if item.is_dir()
             else shutil.copy2(item, clean / item.name))
        rows, fails = run(br, ["ru"], zoom, clean, "clean/ru ")
        results["clean"] = {"fails": fails, "bad": [r["bad"] for r in rows]}
        if fails:
            print("  КОНТРОЛЬ НЕ СОСТОЯЛСЯ: нетронутая копия красная — "
                  "красное на мутантах ничего не доказывает")
            ok = False
        shutil.rmtree(clean, ignore_errors=True)
        # B. мутанты
        for mut, want_msg in (("clip", "TEXT-CLIPPED"), ("wide", "H-OVERFLOW"),
                              ("tap", "TAP-SMALL")):
            tree = mutant_tree(ROOT, mut)
            rows, fails = run(br, ["ru"], zoom, tree, f"{mut}/ru ")
            caught = [r for r in rows if want_msg in r["bad"]]
            got = caught[0]["bad"] if caught else []
            print(f"  мутант {mut}: ожидалось {want_msg}, получено {got or 'ничего'} "
                  f"-> {'ПОЙМАН' if caught else 'ПРОСМОТРЕЛ'}")
            results[mut] = {"expected": want_msg, "caught": bool(caught), "bad": got}
            if not caught:
                ok = False
            shutil.rmtree(tree, ignore_errors=True)
        br.close()

    out = OUT.with_name("text-zoom-control-" + OUT.name.split("text-zoom-", 1)[-1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"zoom": zoom, "control": results}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"КОНТРОЛЬ: {'ПРОЙДЕН' if ok else 'ПРОВАЛЕН'} — evidence: {out}")
    return 0 if ok else 1


def main() -> int:
    from playwright.sync_api import sync_playwright

    zoom = ZOOM
    langs = LANGS
    width = WIDTH
    for a in sys.argv[1:]:
        if a.startswith("--zoom="):
            zoom = float(a.split("=", 1)[1])
        elif a.startswith("--width="):
            width = int(a.split("=", 1)[1])
        elif a.startswith("--langs="):
            langs = [x for x in a.split("=", 1)[1].split(",") if x]
    if "--control" in sys.argv:
        return run_control(zoom)

    print(f"зум текста {zoom:g}x, ширина {width} px, языков {len(langs)}")
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        rows, fails = run(br, langs, zoom, ROOT, "", width)
        br.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"zoom": zoom, "width": width, "rows": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    checks = len(rows) * 3
    print(f"CHECKS: {checks}, FAILED: {fails}")
    print(f"evidence: {OUT}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
