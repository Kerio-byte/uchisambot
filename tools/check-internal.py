#!/usr/bin/env python3
"""check-internal.py — проверка внутренних ссылок и якорей на всех страницах сайта.

Read-only. Ничего не пишет, только печатает итог. Ловит три класса:
  1) относительные href, которые указывают на несуществующий файл/каталог;
  2) #якоря, которых нет на целевой странице (включая ссылки на ../#anchor);
  3) языковые ссылки на страницы, которых нет на диске.

  python3 tools/check-internal.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
PAGES = [ROOT / "index.html"] + [ROOT / l / "index.html" for l in LANGS]
PAGES += [ROOT / "privacy.html", ROOT / "terms.html", ROOT / "404.html"]
PAGES = [p for p in PAGES if p.exists()]

HREF = re.compile(r'href="([^"]+)"')
ID = re.compile(r'\bid="([^"]+)"')


def ids_of(path: Path) -> set:
    if not path.exists():
        return set()
    return set(ID.findall(path.read_text(encoding="utf-8", errors="replace")))


cache: dict = {}


def anchors(path: Path) -> set:
    if path not in cache:
        cache[path] = ids_of(path)
    return cache[path]


def target(page: Path, url: str):
    """Куда ведёт относительная ссылка. Возвращает (файл или None, якорь)."""
    path, _, frag = url.partition("#")
    path = path.split("?")[0]
    if not path:
        return page, frag
    if path.startswith("/"):
        base = ROOT
        path = path.lstrip("/")
    else:
        base = page.parent
    tgt = (base / path).resolve()
    if url.split("?")[0].endswith("/") or tgt.is_dir():
        tgt = tgt / "index.html"
    return tgt, frag


def main() -> int:
    checked = broken_files = broken_anchors = external = 0
    problems = []
    for page in PAGES:
        html = page.read_text(encoding="utf-8", errors="replace")
        for m in HREF.finditer(html):
            url = m.group(1)
            if url.startswith(("http://", "https://")):
                external += 1
                continue
            if url.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            checked += 1
            tgt, frag = target(page, url)
            rel = page.relative_to(ROOT)
            if not tgt.exists():
                broken_files += 1
                problems.append(f"{rel}: нет файла  {url}  -> {tgt.relative_to(ROOT)}")
                continue
            if frag and frag != "" and not frag.startswith(":~:"):
                if frag not in anchors(tgt):
                    broken_anchors += 1
                    problems.append(f"{rel}: нет якоря  {url}  -> #{frag} в {tgt.relative_to(ROOT)}")
    print(f"страниц: {len(PAGES)}  внутренних ссылок: {checked}  внешних: {external}")
    print(f"битых файлов: {broken_files}  битых якорей: {broken_anchors}")
    for p in problems[:25]:
        print("  " + p)
    if len(problems) > 25:
        print(f"  ... ещё {len(problems) - 25}")
    return 1 if (broken_files or broken_anchors) else 0


if __name__ == "__main__":
    sys.exit(main())
