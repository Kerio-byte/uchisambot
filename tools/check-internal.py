#!/usr/bin/env python3
"""check-internal.py — внутренние ссылки, якоря и своё имущество страниц.

Read-only. Ловит пять классов:
  1) href на файл/каталог, которого нет на диске;
  2) #якорь, которого нет на целевой странице (включая ../#anchor);
  3) src картинки/видео/скрипта на файл, которого нет на диске;
  4) poster у видео — тот же класс, что src;
  5) страницу, которую сайт обязан иметь, но её нет (12: корень, восемь
     языков, privacy, terms, 404).

До 31.10.2026 классы 3–5 не проверял никто: `check-links.py` смотрит только
наружу, `check-site-technical.py` — шапки и числа. Пропавшая картинка давала
битую страницу на всех девяти языках и ни одного красного прибора. Класс 5 был
мёртвой веткой: список страниц молча выкидывал отсутствующие, поэтому «12
страниц» в отчёте держалось на том, что все 12 случайно были на месте.

  python3 tools/check-internal.py
  python3 tools/check-internal.py --control   # сам прибор: обязан покраснеть
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
EXPECTED = ["index.html", "privacy.html", "terms.html", "404.html"]
EXPECTED += [f"{l}/index.html" for l in LANGS]

HREF = re.compile(r'\bhref="([^"]+)"')
SRC = re.compile(r'\bsrc="([^"]+)"')
POSTER = re.compile(r'\bposter="([^"]+)"')
SRCSET = re.compile(r'\bsrcset="([^"]+)"')
ID = re.compile(r'\bid="([^"]+)"')

# Внешнее и не-адреса: не наша забота, за наружу отвечает check-links.py.
# «#» здесь стоять НЕ может: 31.10 контроль поймал ровно это — с ним из проверки
# молча выпали все 56 ссылок на свой же якорь (167 ссылок вместо 223).
SKIP_PREFIX = ("http://", "https://", "//", "mailto:", "tel:", "javascript:",
               "data:", "about:")

COUNTERS = ("checks", "fails", "links", "externals", "assets", "broken_files",
            "broken_anchors", "broken_src", "missing_pages", "pages")

cache: dict = {}


def ids_of(path: Path) -> set:
    if not path.exists():
        return set()
    return set(ID.findall(path.read_text(encoding="utf-8", errors="replace")))


def anchors(path: Path) -> set:
    if path not in cache:
        cache[path] = ids_of(path)
    return cache[path]


def resolve(base: Path, url: str, root: Path, page: Path):
    """Куда ведёт относительный адрес. Возвращает (файл, якорь).
    root — тот корень, который сканируем: абсолютный адрес контрольной выдумки
    обязан вести внутрь выдумки, а не в живой сайт (31.10, поймано контролем).
    page — сама страница: ссылка «#anchor» ведёт в неё, а не в её каталог."""
    path, _, frag = url.partition("#")
    path = path.split("?")[0]
    if not path:
        return page, frag
    if path.startswith("/"):
        tgt = (root / path.lstrip("/")).resolve()
    else:
        tgt = (base / path).resolve()
    if path.endswith("/") or tgt.is_dir():
        tgt = tgt / "index.html"
    return tgt, frag


def scan(root: Path) -> dict:
    """Корень -> счётчики, список проблем, имя ожидаемого числа страниц.
    Одна и та же функция для сайта и для контрольной выдумки: прибор,
    проверенный другой дорогой, проверяет не себя."""
    cache.clear()
    c = {k: 0 for k in COUNTERS}
    problems: list[str] = []

    pages = [root / rel for rel in EXPECTED]
    present = [p for p in pages if p.exists()]
    missing = [p for p in pages if not p.exists()]
    c["pages"] = len(present)
    c["missing_pages"] = len(missing)
    c["checks"] += len(pages)
    c["fails"] += len(missing)
    problems += [f"нет страницы: {p.relative_to(root)}" for p in missing]

    for page in present:
        html = page.read_text(encoding="utf-8", errors="replace")
        rel = page.relative_to(root)

        # 1–2: ссылки и якоря
        for m in HREF.finditer(html):
            url = m.group(1)
            if url.startswith(SKIP_PREFIX):
                if url.startswith(("http://", "https://", "//")):
                    c["externals"] += 1
                continue
            c["links"] += 1
            c["checks"] += 1
            tgt, frag = resolve(page.parent, url, root, page)
            if not tgt.exists():
                c["broken_files"] += 1
                c["fails"] += 1
                problems.append(f"{rel}: нет файла  {url}")
                continue
            if frag and not frag.startswith(":~:") and frag not in anchors(tgt):
                c["broken_anchors"] += 1
                c["fails"] += 1
                problems.append(
                    f"{rel}: нет якоря  {url}  -> #{frag} в {tgt.relative_to(root)}")

        # 3–4: своё имущество — картинки, видео, скрипты, постеры
        for rx in (SRC, POSTER):
            for m in rx.finditer(html):
                url = m.group(1)
                if url.startswith(SKIP_PREFIX):
                    continue
                c["assets"] += 1
                c["checks"] += 1
                tgt, _ = resolve(page.parent, url, root, page)
                if not tgt.exists():
                    c["broken_src"] += 1
                    c["fails"] += 1
                    problems.append(f"{rel}: нет файла на диске  {url}")

        # тот же класс для кандидатов srcset (сегодня их нет, но появятся —
        # пропажа кандидата иначе будет молчаливой)
        for m in SRCSET.finditer(html):
            for cand in m.group(1).split(","):
                url = cand.strip().split(" ")[0]
                if not url or url.startswith(SKIP_PREFIX):
                    continue
                c["assets"] += 1
                c["checks"] += 1
                tgt, _ = resolve(page.parent, url, root, page)
                if not tgt.exists():
                    c["broken_src"] += 1
                    c["fails"] += 1
                    problems.append(f"{rel}: нет файла из srcset  {url}")

    return {"c": c, "problems": problems, "pages_expected": len(pages)}


def report(res: dict) -> int:
    c, problems = res["c"], res["problems"]
    print(f"страницы: {c['pages']}/{res['pages_expected']}  ссылки: {c['links']}"
          f"  своё (src/poster): {c['assets']}  внешних: {c['externals']}")
    print(f"битых файлов: {c['broken_files']}  битых якорей: {c['broken_anchors']}"
          f"  битых src: {c['broken_src']}  нет страниц: {c['missing_pages']}")
    for p in problems[:25]:
        print("  " + p)
    if len(problems) > 25:
        print(f"  ... ещё {len(problems) - 25}")
    # Числа для раннера: без них строка в таблице показывала «-» и глубина
    # проверки не была видна никому.
    print(f"CHECKS: {c['checks']}, FAILED: {c['fails']}")
    return 1 if c["fails"] else 0


def control() -> int:
    """Сам прибор обязан покраснеть на выдумке с четырьмя известными дефектами
    и остаться зелёным на чистой выдумке. Второе важно не меньше: прибор,
    который всегда красный, «ловит» всё и не значит ничего."""
    tmp = Path(tempfile.mkdtemp(prefix="internal-control-"))
    caught: list[tuple[str, bool]] = []

    dirty = tmp / "dirty"
    dirty.mkdir()
    (dirty / "index.html").write_text(
        '<a href="ok.html#here">ok</a>\n'
        '<a href="gone.html">файла нет</a>\n'
        '<a href="#nowhere">якоря нет</a>\n'
        '<img src="img/absent.webp" alt="">\n'
        '<img src="data:image/gif;base64,AAA" alt="">\n'
        '<a href="https://example.com/">наружу</a>\n', encoding="utf-8")
    (dirty / "ok.html").write_text('<h1 id="here">ok</h1>', encoding="utf-8")
    d = scan(dirty)["c"]
    caught.append(("битый файл", d["broken_files"] >= 1))
    caught.append(("битый якорь", d["broken_anchors"] >= 1))
    caught.append(("битый src", d["broken_src"] >= 1))
    caught.append(("нет страницы", d["missing_pages"] >= 1))

    clean = tmp / "clean"
    clean.mkdir()
    for rel in EXPECTED:
        tgt = clean / rel
        tgt.parent.mkdir(parents=True, exist_ok=True)
        # языковые страницы лежат на уровень глубже: свой файл им нужен с «../»
        up = "../" if "/" in rel else ""
        tgt.write_text('<h1 id="here">ok</h1>\n<a href="#here">self</a>\n'
                       f'<img src="{up}img/logo.svg" alt="">\n', encoding="utf-8")
    (clean / "img").mkdir()
    (clean / "img" / "logo.svg").write_text("<svg/>", encoding="utf-8")
    cl = scan(clean)["c"]
    caught.append(("чистая выдумка без дефектов", cl["fails"] == 0 and cl["checks"] > 0))

    good = sum(1 for _, ok in caught if ok)
    print("КОНТРОЛЬ: " + "  ".join(f"{n} — {'поймал' if ok else 'ПРОСМОТРЕЛ'}"
                                   for n, ok in caught))
    print(f"поймал {good} из {len(caught)}")
    return 0 if good == len(caught) else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="внутренние ссылки, якоря и своё имущество страниц")
    ap.add_argument("--control", action="store_true",
                    help="проверить сам прибор на выдумке")
    ap.add_argument("--root", default=str(ROOT),
                    help="корень для проверки (по умолчанию — каталог репозитория)")
    args = ap.parse_args()
    if args.control:
        return control()
    return report(scan(Path(args.root).resolve()))


if __name__ == "__main__":
    sys.exit(main())
