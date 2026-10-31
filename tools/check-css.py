#!/usr/bin/env python3
"""Прибор: таблица стилей как её видит браузер, а не как её видит чтение.

Пятнадцатый блок. Четырнадцать приборов держали разметку, ссылки, карту сайта,
веса и доступность. Стили не держал никто: `<style>` — это 500+ строк текста,
который читается глазами страницы, но не читается ни одним инструментом дерева.
Класс дефектов, который живёт ТОЛЬКО здесь:

  * опечатка в имени свойства (`paddding:0`) — браузер молча выбрасывает
    объявление, страница выглядит почти как задумано, и заметить это можно
    только в инспекторе;
  * `url("fonts/x.woff2")`, которого нет на диске — шрифт молча падает на
    запасной, а иногда и в невидимый текст;
  * `@font-face` на семейство, которое нигде не используется, — мёртвые
    байты в первом экране;
  * `font-family:"Manrope"` без объявленного `@font-face` — тот же невидимый
    подмен;
  * `var(--brand)` без определения и без запасного значения — цвет
    становится недействительным, а не «примерно таким»;
  * непарная скобка — браузер выбрасывает не строку, а весь остаток правила.

Классы: `SYNTAX` (скобки, объявления, пустые селекторы), `ASSETS` (каждый
`url()` внутри стилей указывает на файл, лежащий на диске; никаких file://
и localhost), `FONTS` (у @font-face есть семейство, локальный woff2 и
потребитель; у используемого семейства есть объявление), `VARS` (каждая
`var(--x)` без запасного значения где-то определена), `ACCEPT` (у браузера
спрошено про КАЖДОЕ объявление: `CSS.supports(prop, value)`).

`ACCEPT` — единственный пояс, который требует браузера: принять или
выбросить объявление решает парсер, а не текст. Он спрашивает один раз,
на about:blank, про все страницы сразу.

`--control` — семь мутантов на копии дерева, каждый обязан покраснеть своим
классом. Без него прибор — обещание.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"evidence", ".shots-work", "tools", "src", "demo", "submission-kit",
             "img", "fonts", "docs", "node_modules", ".git"}
# Для копии дерева пропускается только то, что прибору не принадлежит: страницы
# ссылаются на fonts/ и img/, и если их не скопировать, ASSETS покраснеет на
# честном дереве — находка прибора, а не сайта.
COPY_IGNORE = {"evidence", ".shots-work", "__pycache__", ".git"}

GENERIC = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded", "math", "emoji",
    "fangsong", "-apple-system", "blinkmacsystemfont", "segoe ui", "roboto",
    "arial", "helvetica", "helvetica neue", "verdana", "tahoma", "trebuchet ms",
    "times new roman", "georgia", "courier new", "noto sans", "noto color emoji",
    "apple color emoji", "segoe ui emoji", "symbol", "inherit", "initial",
    "unset", "revert",
}

# Блоки-дескрипторы: внутри не свойства, а дескрипторы (@font-face, @keyframes).
DESCRIPTOR_AT = ("@font-face", "@keyframes", "@-webkit-keyframes", "@property",
                 "@counter-style", "@font-feature-values", "@page")
NESTED_AT = ("@media", "@supports", "@layer", "@container", "@scope", "@document")


# ─────────────────────────────── страницы ───────────────────────────────

def pages(root: Path) -> list[Path]:
    out = []
    top = root / "index.html"
    if top.is_file():
        out.append(top)
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIRS and (d / "index.html").is_file():
            out.append(d / "index.html")
    for name in ("privacy.html", "terms.html", "404.html"):
        p = root / name
        if p.is_file():
            out.append(p)
    return out


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


# ─────────────────────────────── разбор CSS ───────────────────────────────

def strip_comments(css: str) -> tuple[str, list[str]]:
    problems = []
    opens, closes = css.count("/*"), css.count("*/")
    if opens != closes:
        problems.append("незакрытый комментарий /* без */")
    out, i, n = [], 0, len(css)
    while i < n:
        if css.startswith("/*", i):
            j = css.find("*/", i + 2)
            if j == -1:
                break
            # комментарий заменяется пробелом: смещения и переводы строк важны
            out.append(" ")
            i = j + 2
            continue
        out.append(css[i])
        i += 1
    return "".join(out), problems


def split_blocks(text: str):
    """Верхний уровень: [(prelude, body)] и признак непарной скобки."""
    out, problems = [], []
    i, n, depth, start = 0, len(text), 0, 0
    prelude, body_start = "", 0
    while i < n:
        c = text[i]
        if c == "{":
            if depth == 0:
                prelude, body_start, depth = text[start:i].strip(), i + 1, 1
                i += 1
                continue
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                out.append((prelude, text[body_start:i]))
                start = i + 1
            elif depth < 0:
                problems.append("лишняя '}' без открывающей")
                depth = 0
                start = i + 1
        i += 1
    if depth > 0:
        problems.append(f"не закрыто {depth} блок(ов) — браузер выбросит остаток правила")
    tail = text[start:].strip()
    if tail and depth == 0:
        problems.append(f"текст вне правила: {tail[:40]!r}")
    return out, problems


def split_decls(body: str):
    """Объявления внутри тела правила; кавычки и скобки учитываются."""
    parts, buf, i, n = [], [], 0, len(body)
    quote = None
    paren = 0
    while i < n:
        c = body[i]
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            buf.append(c)
        elif c == "(":
            paren += 1
            buf.append(c)
        elif c == ")":
            paren = max(0, paren - 1)
            buf.append(c)
        elif c == ";" and paren == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def parse_page(html_text: str):
    """Возвращает decls [(prop, value, ctx)], font_faces [dict], url_refs, problems."""
    css = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", html_text, re.S | re.I))
    problems: list[tuple[str, str]] = []
    if not css.strip():
        return [], [], [], problems, 0
    css, cp = strip_comments(css)
    problems += [("SYNTAX", p) for p in cp]
    # Скобки считаются без содержимого кавычек: `content:"{"` — законный текст.
    bare = re.sub(r'"[^"]*"|\'[^\']*\'', '""', css)
    if bare.count("{") != bare.count("}"):
        problems.append(("SYNTAX", f"скобки не сходятся: {bare.count('{')} открывающих "
                                   f"против {bare.count('}')} закрывающих"))

    decls: list[tuple[str, str, tuple]] = []
    faces: list[dict] = []
    style_rules = 0

    def walk(text: str, ctx: tuple):
        nonlocal style_rules
        top, probs = split_blocks(text)
        problems.extend(("SYNTAX", p) for p in probs)
        for prelude, body in top:
            pre = prelude.lower()
            if pre.startswith("@"):
                if pre.startswith(DESCRIPTOR_AT):
                    d = split_decls(body)
                    kv = _kv(d, problems)
                    if pre.startswith("@font-face"):
                        faces.append({"decls": kv, "ctx": ctx})
                    for prop, value in kv:
                        decls.append((prop, value, ctx + (prelude,)))
                    continue
                if pre.startswith(NESTED_AT):
                    m_at = re.match(r"@[-A-Za-z]+", prelude)
                    cond = prelude[m_at.end():].strip() if m_at else ""
                    if not cond:
                        problems.append(("SYNTAX", f"пустое условие {prelude.split()[0]}"))
                    walk(body, ctx + (prelude,))
                    continue
                # неизвестная at-rule — не выдумываем про неё норму
                continue
            style_rules += 1
            if not prelude.strip():
                problems.append(("SYNTAX", "правило без селектора"))
            for prop, value in _kv(split_decls(body), problems):
                decls.append((prop, value, ctx))

    walk(css, ())
    url_refs = [(m.group(1).strip().strip("\"'"), m.group(0)) for m in
                re.finditer(r"url\(\s*([^)]*)\)", css, re.I)]
    return decls, faces, url_refs, problems, style_rules


def _kv(pairs, problems):
    out = []
    for part in pairs:
        if part.startswith("@"):        # вложенная at-rule на месте объявления
            continue
        if ":" not in part:
            problems.append(("SYNTAX", f"объявление без двоеточия: {part[:40]!r}"))
            continue
        prop, value = part.split(":", 1)
        prop, value = prop.strip(), value.strip()
        if not prop:
            problems.append(("SYNTAX", f"пустое имя свойства в {part[:40]!r}"))
            continue
        if not value:
            problems.append(("SYNTAX", f"пустое значение у {prop}"))
            continue
        out.append((prop, value))
    return out


# ─────────────────────────────── пояса ───────────────────────────────

def check_static(page: Path) -> tuple[list[tuple[str, str]], list[tuple[str, str]], int]:
    """Возвращает (находки, объявления к опросу браузера, сколько не спрошено)."""
    html_text = page.read_text(encoding="utf-8")
    decls, faces, urls, problems, rules = parse_page(html_text)
    findings = list(problems)

    # ASSETS — каждый url() внутри стилей на файл, который лежит на диске
    for raw, whole in urls:
        u = raw.strip()
        if not u:
            findings.append(("ASSETS", f"пустой url(): {whole}"))
            continue
        low = u.lower()
        if low.startswith(("data:", "http://", "https://", "//", "#")):
            if low.startswith("http://"):
                findings.append(("ASSETS", f"незащищённый адрес в стилях: {u}"))
            continue
        if low.startswith(("file:", "localhost", "127.0.0.1")):
            findings.append(("ASSETS", f"локальный путь в стилях: {u}"))
            continue
        clean = u.split("?")[0].split("#")[0]
        target = (page.parent / clean.lstrip("/")) if not clean.startswith("/") \
            else (ROOT / clean.lstrip("/"))
        if not target.is_file():
            findings.append(("ASSETS", f"url() в пустоту: {clean}"))

    # FONTS — объявленное семейство имеет woff2 и потребителя
    declared = set()
    for face in faces:
        fam = next((v for p, v in face["decls"] if p.lower() == "font-family"), "")
        fam = fam.strip().strip("\"'")
        if not fam:
            findings.append(("FONTS", "@font-face без font-family"))
            continue
        declared.add(fam.lower())
        src = next((v for p, v in face["decls"] if p.lower() == "src"), "")
        if not src:
            findings.append(("FONTS", f"@font-face {fam} без src"))
        elif "format(" not in src:
            findings.append(("FONTS", f"@font-face {fam}: src без подсказки format()"))
        else:
            local = [m.group(1).strip().strip("\"'") for m in re.finditer(r"url\(([^)]*)\)", src)]
            if not local:
                findings.append(("FONTS", f"@font-face {fam}: src без локального файла"))
            if "font-display" not in {p.lower() for p, _ in face["decls"]}:
                findings.append(("FONTS", f"@font-face {fam} без font-display"))

    used_families = set()
    custom = {p: v for p, v, _c in decls if p.startswith("--")}

    def family_of(value: str) -> str:
        """Первый шрифт из списка; для font: — после размера; var() раскрывается."""
        v = value.strip()
        m_var = re.match(r"var\(\s*(--[A-Za-z0-9_-]+)\s*\)$", v)
        if m_var:
            return family_of(custom.get(m_var.group(1), ""))
        return v.split(",")[0].strip().strip("\"'").lower()

    SIZE = re.compile(r"(?<![\w-])(?:\d*\.?\d+(?:px|rem|em|%|pt|vh|vw)|(?:xx-)?(?:small|large)|"
                      r"medium|larger|smaller)(?:/[^\s,]+)?", re.I)

    for prop, value, ctx in decls:
        low = prop.lower()
        if low not in ("font-family", "font"):
            continue
        if any(c.startswith("@font-face") for c in ctx):
            continue
        if low == "font":
            m = SIZE.search(value)
            if not m:
                continue
            stack = value[m.end():]
        else:
            stack = value
        names = [n.strip().strip("\"'").lower() for n in stack.split(",")]
        if names and names[0].startswith("var("):
            names[0] = family_of(names[0])
        names = [n for n in names if n and not n.startswith("--")]
        used_families.update(names)
        first = names[0] if names else ""
        if not first or first.startswith("--"):
            continue
        if first not in declared and first not in GENERIC:
            findings.append(("FONTS", f"семейство {first!r} используется, но @font-face его нет"))

    for fam in sorted(declared - used_families):
        findings.append(("FONTS", f"@font-face {fam}: объявлен, но нигде не используется"))

    # VARS — var(--x) без запасного значения должен быть определён
    defined = {p for p, _v, _c in decls if p.startswith("--")}
    for m in re.finditer(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(,?)", "\n".join(
            f"{p}:{v}" for p, v, _c in decls)):
        name, comma = m.group(1), m.group(2)
        if name not in defined and not comma:
            findings.append(("VARS", f"{name} не определена и без запасного значения"))

    to_ask = []
    skipped = 0
    for prop, value, ctx in decls:
        if prop.startswith("--"):
            continue
        if any(any(c.lower().startswith(a) for a in DESCRIPTOR_AT) for c in ctx):
            continue
        if prop.startswith("-") or prop.startswith("*"):
            # собственные свойства с префиксом браузера — их принимает парсер
            # конкретного движка, а CSS.supports о них молчит; не выдаём молчание
            # за находку и называем число вслух
            skipped += 1
            continue
        clean = re.sub(r"\s*!\s*important\s*$", "", value, flags=re.I).strip()
        if not clean:
            continue
        to_ask.append((prop, clean))
    return findings, to_ask, skipped


def ask_browser(browser, pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """CSS.supports по каждому объявлению: примет парсер или выбросит молча."""
    page = browser.new_page()
    try:
        page.goto("about:blank")
        pairs = list(dict.fromkeys(pairs))
        res = page.evaluate(
            """(pairs) => pairs.map(([p, v]) => {
                 let ok = true;
                 try { ok = CSS.supports(p, v); } catch (e) { ok = true; }
                 return ok;
               })""", [[p, v] for p, v in pairs])
    finally:
        page.close()
    return [pair for pair, ok in zip(pairs, res) if not ok]


# ─────────────────────────────── контроль ───────────────────────────────

def drop_brace(h: str) -> str:
    """Убирает первую закрывающую скобку ВНУТРИ <style>, а не в JSON-LD."""
    m = re.search(r"<style\b[^>]*>", h)
    if not m:
        return h
    i = h.find("}", m.end())
    return h if i == -1 else h[:i] + h[i + 1:]


MUTANTS = [
    ("SYNTAX", "снятая закрывающая скобка", drop_brace),
    ("SYNTAX", "объявление без двоеточия",
     lambda h: h.replace("</style>", "\n.mutant{color red}\n</style>", 1)),
    ("ASSETS", "url() в пустоту",
     lambda h: h.replace("</style>", '\n.mutant{background:url("img/nope-404.png")}\n</style>', 1)),
    ("FONTS", "@font-face без потребителя",
     lambda h: h.replace("</style>", '\n@font-face{font-family:"Ghost Face";'
                          'src:url("fonts/manrope-latin.woff2") format("woff2");'
                          'font-display:swap}\n</style>', 1)),
    ("FONTS", "семейство без @font-face",
     lambda h: h.replace("</style>", '\n.mutant{font-family:"Nowhere Sans",sans-serif}\n</style>', 1)),
    ("VARS", "неизвестная переменная",
     lambda h: h.replace("</style>", "\n.mutant{color:var(--nope-not-defined)}\n</style>", 1)),
    ("ACCEPT", "опечатка в имени свойства",
     lambda h: h.replace("</style>", "\n.mutant{paddding:0;colour:red}\n</style>", 1)),
]


def run_control(offline: bool = False) -> int:
    all_pages = pages(ROOT)
    target = next((p for p in all_pages if p.parent.name == "ru"), all_pages[0])
    relpath = target.relative_to(ROOT)
    template = target.read_text(encoding="utf-8")
    tmp = Path(tempfile.mkdtemp(prefix="css-"))
    copy = tmp / "copy"
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(*COPY_IGNORE))
    ok = 0
    pw = browser = None
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
            found, to_ask, _skip = check_static(copy / relpath)
            if browser is not None and to_ask:
                dropped = ask_browser(browser, to_ask)
                found = found + [("ACCEPT", f"{p}:{v}") for p, v in dropped]
            got = [c for c, _ in found]
            if cls in got:
                ok += 1
                hit = next(m for c, m in found if c == cls)
                print(f"  поймал   {name}: {cls} — {hit[:70]}")
            else:
                print(f"  НЕ ПОЙМАЛ {name}: класс {cls} не покраснел (находки: {sorted(set(got))})")
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
    ap.add_argument("--offline", action="store_true", help="без браузера (только текст)")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    if a.control:
        print(f"КОНТРОЛЬ: {len(MUTANTS)} мутантов, каждый обязан покраснеть своим классом")
        ok = run_control(a.offline)
        print(f"МУТАНТЫ {ok}/{len(MUTANTS)}")
        return 0 if ok == len(MUTANTS) else 1

    findings: list[tuple[str, str]] = []
    to_ask: list[tuple[str, str]] = []
    total_decls = skipped = 0
    for p in pages(root):
        f, ask, skip = check_static(p)
        findings += [(c, f"{rel(root, p)}: {m}") for c, m in f]
        to_ask += ask
        total_decls += len(ask)
        skipped += skip
    print(f"STYLE: {len(pages(root))} страниц, объявлений к опросу {total_decls}, "
          f"с префиксом браузера (не спрошено) {skipped}")

    if not a.offline:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                dropped = ask_browser(browser, to_ask)
            finally:
                browser.close()
        for prop, value in dropped:
            findings.append(("ACCEPT", f"браузер выбросит: {prop}: {value[:60]}"))
        print(f"ACCEPT: у браузера спрошено {len(set(to_ask))} объявлений, выбросит {len(dropped)}")

    if findings:
        by: dict[str, list[str]] = {}
        for cls, msg in findings:
            by.setdefault(cls, []).append(msg)
        for cls in sorted(by):
            print(f"[{cls}] {len(by[cls])}")
            for m in by[cls][:8]:
                print(f"   {m}")
        if a.json:
            print(json.dumps(findings, ensure_ascii=False))
        return 1
    print("ИТОГО ok: находок нет")
    return 0


if __name__ == "__main__":
    sys.exit(main())
