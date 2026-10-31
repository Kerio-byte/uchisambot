#!/usr/bin/env python3
"""check-markup.py — сама разметка страниц, а не то, что в ней написано.

До 31.10.2026 у дерева было девятнадцать приборов и ни одного, который смотрел
бы на HTML как на разметку. Ссылки держал `check-internal`, карту — `check-sitemap`,
слова — `landing-sweep`, веса — `check-weight`. Всё это читает страницу как
текст и набор адресов. Никто не держал дерево тегов, и молчаливый `</div>`,
съеденный правкой, оставлял браузеру догадку: он закроет блок сам, страница
останется «похожей», свип зелёный, а вложенность после этого места — чужая.
Так же молчали дубль `id`, ссылка на якорь, которого нет, и атрибут без кавычек:
`class=hero` браузер угадает, а следующий атрибут в том же теге уже потеряется.

Пять классов:
  1) TAG  — дерево тегов: непарный закрывающий, незакрытый непустой элемент,
            самозакрытый непустой (`<div/>` — браузер прочтёт как `<div>`),
            закрытие пустого (`</br>`, `</img>`);
  2) ID   — повтор `id` на странице, пустой `id`, пробел внутри значения;
  3) REF  — `href="#..."` обязан указывать на существующий `id` этой же страницы;
  4) ATTR — значение без кавычек, повтор имени атрибута в одном теге, пустое имя;
  5) HEAD — то, без чего страница не страница: `lang`, `charset` в первых 1024
            байтах, `viewport`, непустой `title`, ровно один `h1`, `alt` у каждой
            картинки.

Страницы берутся из дерева: корень, каталоги языков, прочие `.html` кроме
страницы ошибки и кроме того, что `robots.txt` велит не читать (`index-src.html` —
исходник мастерской, в нём живут `{плейсхолдеры}`, и он не публикуется).

  python3 tools/check-markup.py
  python3 tools/check-markup.py --control   # сам прибор: обязан покраснеть на семи
  python3 tools/check-markup.py --root DIR  # проверять копию дерева
  python3 tools/check-markup.py --json      # машинный отчёт в evidence/
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

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# Закрытие можно не писать — по HTML5 браузер закроет сам.
OPTIONAL = {"p", "li", "td", "th", "tr", "dt", "dd", "option", "optgroup",
            "thead", "tbody", "tfoot", "colgroup", "html", "head", "body"}
# Кто кого закрывает своим появлением (только эти пары: остальное — дефект).
IMPLICIT = {"li": {"li"}, "p": {"p"}, "tr": {"tr", "td", "th"},
            "td": {"td", "th"}, "th": {"td", "th"}, "option": {"option"},
            "dt": {"dt", "dd"}, "dd": {"dt", "dd"},
            "thead": {"tbody", "tfoot", "tr"}, "tbody": {"thead", "tfoot", "tr"},
            "tfoot": {"thead", "tbody", "tr"}}
RAW = {"script", "style", "textarea", "title"}
TWO = re.compile(r"^[a-z]{2}$")
HTMLLANG = re.compile(r'<html[^>]*\blang="([^"]*)"', re.I)


class Probe:
    def __init__(self) -> None:
        self.checks = 0
        self.problems: list[str] = []

    def ok(self, cond: bool, msg: str) -> bool:
        self.checks += 1
        if not cond:
            self.problems.append(msg)
        return cond


def text_of(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def disallowed(root: Path) -> set[str]:
    shut: set[str] = set()
    for line in text_of(root / "robots.txt").splitlines():
        line = line.strip()
        if not line.lower().startswith("disallow:"):
            continue
        rest = line.split(":", 1)[1].strip().lstrip("/")
        if rest and "*" not in rest and "/" not in rest:
            shut.add(rest)
    return shut


def pages(root: Path) -> list[Path]:
    """Страницы сайта: корень, языки, прочие корневые .html (без 404 и запрета)."""
    out: list[Path] = []
    shut = disallowed(root)
    if (root / "index.html").is_file():
        out.append(root / "index.html")
    out += sorted(p / "index.html" for p in root.iterdir()
                  if p.is_dir() and TWO.match(p.name) and (p / "index.html").is_file())
    out += sorted(p for p in root.iterdir()
                  if p.is_file() and p.suffix == ".html"
                  and p.name not in ("index.html", "404.html") and p.name not in shut)
    return out


class Tag:
    __slots__ = ("name", "attrs", "self_closing", "line", "raw_pos")

    def __init__(self, name: str, attrs, self_closing: bool, line: int) -> None:
        self.name = name
        self.attrs = attrs          # [(name, value, quoted, line)]
        self.self_closing = self_closing
        self.line = line


def tokenize(text: str):
    """Теги и закрытия по порядку. Комментарии, DOCTYPE и сырой текст — мимо.

    Возвращает список ("open", Tag) / ("close", Tag) и список дефектов разбора
    (незакрытая кавычка в теге)."""
    out = []
    bad = []
    i = 0
    n = len(text)
    line = 1
    while i < n:
        j = text.find("<", i)
        if j < 0:
            break
        line += text.count("\n", i, j)
        if text.startswith("<!--", j):
            k = text.find("-->", j + 4)
            end = (k + 3) if k >= 0 else n
            line += text.count("\n", j, end)
            i = end
            continue
        if text.startswith("<![CDATA[", j):
            k = text.find("]]>", j + 9)
            end = (k + 3) if k >= 0 else n
            line += text.count("\n", j, end)
            i = end
            continue
        if text.startswith("<!", j) or text.startswith("<?", j):
            k = text.find(">", j)
            end = (k + 1) if k >= 0 else n
            line += text.count("\n", j, end)
            i = end
            continue
        # имя тега
        k = j + 1
        closing = False
        if k < n and text[k] == "/":
            closing = True
            k += 1
        m = re.match(r"[A-Za-z][^\s/>]*", text[k:k + 80])
        if not m:
            i = j + 1
            continue
        name = m.group(0).lower()
        k += m.end()
        attrs = []
        self_closing = False
        start_line = line
        closed = False
        while k < n:
            ch = text[k]
            if ch in " \t\r\n":
                line += 1 if ch == "\n" else 0
                k += 1
                continue
            if ch == ">":
                k += 1
                closed = True
                break
            if ch == "/":
                if k + 1 < n and text[k + 1] == ">":
                    self_closing = True
                    k += 2
                    closed = True
                    break
                k += 1
                continue
            am = re.match(r"[^\s/>=]+", text[k:k + 200])
            if not am:
                k += 1
                continue
            aname = am.group(0)
            aline = line
            k += am.end()
            while k < n and text[k] in " \t\r\n":
                line += 1 if text[k] == "\n" else 0
                k += 1
            value = None
            quoted = True
            if k < n and text[k] == "=":
                k += 1
                while k < n and text[k] in " \t\r\n":
                    line += 1 if text[k] == "\n" else 0
                    k += 1
                if k < n and text[k] in "\"'":
                    q = text[k]
                    end = text.find(q, k + 1)
                    if end < 0:
                        bad.append(f"UNQUOTED строка {aline}: кавычка в <{name}> не закрыта")
                        end = n - 1
                    value = text[k + 1:end]
                    line += text.count("\n", k, end)
                    k = end + 1
                else:
                    vm = re.match(r"[^\s>]*", text[k:k + 500])
                    value = vm.group(0)
                    quoted = False
                    k += vm.end()
            attrs.append((aname, value, quoted, aline))
        if not closed:
            bad.append(f"TAG строка {start_line}: тег <{name}> не закончен")
        tag = Tag(name, attrs, self_closing, start_line)
        out.append(("close" if closing else "open", tag))
        i = k
        if name in RAW and not closing and not self_closing:
            m2 = re.compile(r"</%s\s*>" % re.escape(name), re.I).search(text, i)
            end = m2.start() if m2 else n
            line += text.count("\n", i, end)
            i = end
    return out, bad


def scan_page(rel: str, text: str, p: Probe) -> None:
    toks, bad = tokenize(text)
    for b in bad:
        p.ok(False, f"{b} [{rel}]")

    stack: list[Tag] = []
    ids: dict[str, int] = {}
    refs: list[tuple[str, int]] = []
    h1 = 0
    imgs_no_alt = 0
    title = None
    foreign = 0

    for kind, t in toks:
        if kind == "open":
            if t.name in ("svg", "math"):
                foreign += 1
            # повтор имени атрибута и значение без кавычек
            seen = set()
            for aname, value, quoted, aline in t.attrs:
                p.ok(bool(aname), f"ATTR строка {aline}: пустое имя атрибута в <{t.name}> [{rel}]")
                low = aname.lower()
                p.ok(low not in seen,
                     f"ATTR строка {aline}: атрибут {aname} второй раз в <{t.name}> [{rel}]")
                seen.add(low)
                if value is not None:
                    p.ok(quoted,
                         f"ATTR строка {aline}: <{t.name} {aname}={value[:24]}> без кавычек [{rel}]")
                if low == "id" and value is not None:
                    p.ok(value.strip() == value and " " not in value.strip(),
                         f"ID строка {aline}: пробел в id=\"{value}\" [{rel}]")
                    p.ok(bool(value.strip()), f"ID строка {aline}: пустой id [{rel}]")
                    if value:
                        p.ok(value not in ids,
                             f"ID строка {aline}: id=\"{value}\" уже был на строке {ids.get(value)} [{rel}]")
                        ids.setdefault(value, aline)
                if low == "href" and value and value.startswith("#") and len(value) > 1:
                    refs.append((value[1:], aline))
            if t.name == "h1":
                h1 += 1
            if t.name == "img" and not any(a.lower() == "alt" for a, *_ in t.attrs):
                imgs_no_alt += 1
            if t.name == "title" and title is None:
                m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
                title = (m.group(1).strip() if m else "")
            # Пустой элемент: `<br/>` и `<img/>` в HTML5 законны (слэш
            # игнорируется), незаконно обратное — `</br>`, его ловит ветка
            # закрытия ниже.
            if t.name in VOID:
                continue
            if t.self_closing and foreign == 0:
                p.ok(False,
                     f"TAG строка {t.line}: <{t.name}/> самозакрыт, браузер прочтёт как открытый [{rel}]")
                continue
            if t.self_closing and foreign > 0:
                continue
            while stack and t.name in IMPLICIT and stack[-1].name in IMPLICIT.get(t.name, set()):
                stack.pop()
            stack.append(t)
        else:
            name = t.name
            if name in VOID:
                p.ok(False, f"TAG строка {t.line}: закрытие пустого </{name}> [{rel}]")
                continue
            if stack and stack[-1].name == name:
                stack.pop()
            else:
                # есть ли он глубже — значит верхние не закрыты
                depth = next((i for i in range(len(stack) - 1, -1, -1)
                              if stack[i].name == name), None)
                if depth is None:
                    p.ok(False,
                         f"TAG строка {t.line}: </{name}> без открытия [{rel}]")
                else:
                    for below in stack[depth + 1:]:
                        p.ok(below.name in OPTIONAL,
                             f"TAG строка {below.line}: <{below.name}> не закрыт перед </{name}> "
                             f"(строка {t.line}) [{rel}]")
                    del stack[depth:]
            if name in ("svg", "math") and foreign > 0:
                foreign -= 1

    for t in stack:
        p.ok(t.name in OPTIONAL,
             f"TAG строка {t.line}: <{t.name}> не закрыт до конца страницы [{rel}]")

    for frag, aline in refs:
        p.ok(frag in ids, f"REF строка {aline}: href=\"#{frag}\" — такого id на странице нет [{rel}]")

    p.ok(h1 == 1, f"HEAD: заголовков h1 {h1}, а должен быть ровно один [{rel}]")
    p.ok(bool(title), f"HEAD: пустой или отсутствующий <title> [{rel}]")
    p.ok(imgs_no_alt == 0, f"HEAD: картинок без alt {imgs_no_alt} [{rel}]")
    m = HTMLLANG.search(text)
    p.ok(bool(m and m.group(1).strip()), f"HEAD: у <html> нет lang [{rel}]")
    # Одно требование, две половины: объявлен и объявлен рано. Браузер читает
    # первые 1024 байта и, не найдя кодировки, угадывает её сам.
    mc = re.search(r'<meta\s+charset="?utf-8"?', text, re.I)
    p.ok(bool(mc) and mc.start() < 1024,
         f"HEAD: нет <meta charset=\"utf-8\"> в первых 1024 байтах [{rel}]")
    p.ok(bool(re.search(r'<meta[^>]+name="viewport"', text, re.I)),
         f"HEAD: нет <meta name=\"viewport\"> [{rel}]")
    p.ok(len(ids) > 0, f"HEAD: на странице нет ни одного id [{rel}]")


def scan(root: Path) -> dict:
    p = Probe()
    files = pages(root)
    for f in files:
        scan_page(f.relative_to(root).as_posix(), text_of(f), p)
    return {"c": {"checks": p.checks, "fails": len(p.problems), "pages": len(files)},
            "problems": p.problems}


def report(res: dict) -> int:
    c = res["c"]
    print(f"страниц: {c['pages']}  проверок: {c['checks']}")
    for prob in res["problems"][:30]:
        print("  " + prob)
    if len(res["problems"]) > 30:
        print(f"  ... ещё {len(res['problems']) - 30}")
    print(f"CHECKS: {c['checks']}, FAILED: {c['fails']}")
    return 1 if c["fails"] else 0


# ---- контроль прибора: семь мутантов на копии дерева -----------------------

def _copy(root: Path, dst: Path) -> None:
    for f in pages(root):
        target = dst / f.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
    (dst / "robots.txt").write_text(text_of(root / "robots.txt"), encoding="utf-8")


def _first(root: Path) -> Path:
    return pages(root)[0]


def control(root: Path) -> int:
    caught: list[tuple[str, bool]] = []

    def must(m, what: str):
        if m is None:
            raise SystemExit(f"контроль: в странице нет {what} — мутант не поставить")
        return m

    def leg(name: str, tag: str, mutate) -> None:
        d = Path(tempfile.mkdtemp(prefix="markup-ctl-"))
        try:
            _copy(root, d)
            page = _first(d)
            mutate(page, page.read_text(encoding="utf-8"))
            probs = scan(d)["problems"]
            caught.append((name, any(x.startswith(tag) for x in probs)))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def put(page: Path, text: str) -> None:
        page.write_text(text, encoding="utf-8")

    def drop_div_close(page: Path, text: str) -> None:
        k = must(text.find("</div>", text.find("<body")), "</div> после <body>")
        if k < 0:
            raise SystemExit("контроль: нет </div> после <body>")
        put(page, text[:k] + text[k + len("</div>"):])

    def stray_close(page: Path, text: str) -> None:
        k = text.find("<body")
        put(page, text[:k] + "</section>" + text[k:])

    def dup_id(page: Path, text: str) -> None:
        m = must(re.search(r'\bid="([^"]+)"', text), "ни одного id")
        first = m.group(1)
        m2 = must(re.search(r'\bid="([^"]+)"', text[m.end():]), "второго id")
        second = m2.group(1)
        start = m.end() + m2.start()
        put(page, text[:start] + text[start:].replace(f'id="{second}"', f'id="{first}"', 1))

    def dead_ref(page: Path, text: str) -> None:
        put(page, text.replace('href="#main"', 'href="#net-takogo-yakorya"', 1))

    def bare_attr(page: Path, text: str) -> None:
        m = must(re.search(r'<div class="([^"]*)"', text), "<div class>")
        put(page, text[:m.start()] + f"<div class={m.group(1)}" + text[m.end():])

    def no_viewport(page: Path, text: str) -> None:
        put(page, re.sub(r'<meta[^>]+name="viewport"[^>]*>', "", text, count=1))

    def self_closed(page: Path, text: str) -> None:
        m = must(re.search(r'<div class="([^"]*)"', text), "<div class>")
        put(page, text[:m.start()] + f'<div class="{m.group(1)}"/>' + text[m.end():])

    leg("незакрытый блок", "TAG", drop_div_close)
    leg("лишнее закрытие", "TAG", stray_close)
    leg("дубль id", "ID", dup_id)
    leg("якорь в никуда", "REF", dead_ref)
    leg("атрибут без кавычек", "ATTR", bare_attr)
    leg("нет viewport", "HEAD", no_viewport)
    leg("самозакрытый блок", "TAG", self_closed)

    good = sum(1 for _, ok in caught if ok)
    print("КОНТРОЛЬ: " + "  ".join(f"{n} — {'поймал' if ok else 'ПРОСМОТРЕЛ'}"
                                   for n, ok in caught))
    print(f"поймал {good} из {len(caught)}")
    return 0 if good == len(caught) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="разметка: дерево тегов, id, якоря, атрибуты, голова")
    ap.add_argument("--control", action="store_true", help="проверить сам прибор на семи выдумках")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", metavar="PATH", help="машинный отчёт в файл")
    args = ap.parse_args()
    if args.control:
        return control(Path(args.root).resolve())
    res = scan(Path(args.root).resolve())
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
    return report(res)


if __name__ == "__main__":
    sys.exit(main())
