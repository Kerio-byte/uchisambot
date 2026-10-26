#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сабсет деванагари под текст сайта (генерируется один раз, файл лежит в git).

Зачем (26.10.2026). Полный Noto Sans Devanagari — 121 192 Б — грузится на КАЖДОМ
заходе на /hi/ и это 19 % веса первого экрана хинди-страницы (замер холодной
загрузки: 937 КБ, из них ролик 345, HTML 120, шрифт 118). При этом страница
использует 57 кодпойнтов деванагари: остальные ~600 глифов шрифта не рисуют ни
одной буквы. Сабсет с теми же контурами и всеми layout-фичами (иначе хинди
разваливается: слоги, half-формы, репха) весит 70 КБ — на 51 КБ меньше, при
побайтово тех же формах букв.

Почему отдельный файл, а не пересборка на месте: шрифт — ассет, он лежит в git и
не зависит от того, есть ли на машине fonttools/brotli (в сборке их нет).
Сборка ТОЛЬКО читает реестр tools/deva-subset.json и падает, если тексту страницы
нужен кодпойнт, которого в сабсете нет, — тогда запускать этот скрипт снова.

Требования: fonttools + brotli (например, uv venv + uv pip install fonttools brotli).
Запуск:  python3 tools/subset-deva.py           — пересобрать и записать реестр
         python3 tools/subset-deva.py --check   — только сверить, ничего не писать
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
# Исходник живёт ВНЕ публикуемого каталога fonts/ (26.10.2026): странице он больше не
# нужен, а публикация — это только то, что сайт называет. Готовый сабсет — в fonts/.
SRC = ROOT / "tools" / "font-src" / "noto-sans-devanagari.woff2"
DST = FONTS / "noto-sans-devanagari-hi.woff2"
REG = ROOT / "tools" / "deva-subset.json"

# Откуда берём текст (26.10.2026): ИСТОЧНИКИ, а не только собранные страницы.
# Урок контроля: правка словаря добавляет букву, сборка падает («буквы нет в сабсете»),
# а генератор, читающий собранные страницы, этой буквы ещё не видит — страница ведь не
# пересобралась. Тупик. Теперь набор собирается из словарей и шаблона, а собранные
# страницы (если лежат) добавляются сверху как проверка.
PAGES = ["index.html", "404.html", "privacy.html", "terms.html"] + [
    f"{l}/index.html" for l in ("ru", "es", "pt", "hi", "id", "tr", "vi", "uk")
]
SOURCES = ["index-src.html", "src/locales/hi.json", "tools/build.py",
           "privacy.html", "terms.html"]
DEVA = re.compile(r"[\u0900-\u097f]")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_text(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    html = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = html.replace("&amp;", "&").replace("&nbsp;", " ").replace("&#64;", "@")
    return html


def collect() -> tuple[str, list[str]]:
    """Все кодпойнты деванагари на сайте: источники + собранные страницы.

    Источники (словарь хинди, шаблон, сборщик, legal) — то, что МОЖЕТ появиться на сайте
    после правки; собранные страницы — то, что на сайте есть сейчас. Объединение
    закрывает тупик «правка словаря → сборка падает → генератор не видит букву».
    """
    chars: set[str] = set()
    where: list[str] = []
    for rel in SOURCES + PAGES:
        p = ROOT / rel
        if not p.is_file():
            continue
        if rel.endswith(".json"):
            raw = p.read_text(encoding="utf-8")
        else:
            raw = page_text(p)
        found = set(DEVA.findall(raw))
        if found:
            chars |= found
            where.append(f"{rel}({len(found)})")
    return "".join(sorted(chars, key=ord)), where


def build(chars: str) -> None:
    from fontTools import subset
    from fontTools.ttLib import TTFont

    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]      # шейпинг деванагари обязателен целиком
    # hinting НЕ выбрасывать (26.10.2026). С выброшенным hinting'ом сабсет весил на 28 Б
    # меньше, но рисовал текст иначе: пиксельное сравнение на живой /hi/ показало 12 631
    # расхождение в заголовке и 35 288 в лиде при той же вёрстке. С сохранёнными
    # инструкциями (prep + glyf) картинка совпадает с полным шрифтом в ноль пикселей.
    opts.hinting = True
    opts.desubroutinize = True
    opts.name_IDs = ["*"]
    opts.name_languages = ["*"]
    opts.notdef_outline = True
    opts.recalc_bounds = True
    font = subset.load_font(str(SRC), opts)
    sub = subset.Subsetter(options=opts)
    sub.populate(text=chars)
    sub.subset(font)
    font.flavor = "woff2"
    font.save(str(DST))
    cmap = set(TTFont(str(DST)).getBestCmap().keys())
    missing = [c for c in chars if ord(c) not in cmap]
    if missing:
        raise SystemExit(f"сабсет не содержит {missing} — шрифт не годится")
    feats = sorted({fr.FeatureTag for fr in TTFont(str(DST))["GSUB"].table.FeatureList.FeatureRecord})
    print(f"сабсет: {DST.name} {DST.stat().st_size} Б из {SRC.stat().st_size} Б "
          f"({DST.stat().st_size / SRC.stat().st_size:.0%}), кодпойнтов {len(chars)}, "
          f"GSUB-фич {len(feats)}")
    REG.write_text(json.dumps({
        "_note": ("Сабсет деванагари под текст сайта (26.10.2026). Единственный источник: "
                  "кодпойнты собраны из собранных страниц. Сборка падает, если тексту нужен "
                  "кодпойнт вне charters — тогда пересобрать: python3 tools/subset-deva.py. "
                  "Исходник tools/font-src/noto-sans-devanagari.woff2 лежит вне публикуемого "
                  "каталога fonts/ и в сайт не уезжает."),
        "source": f"tools/font-src/{SRC.name}",
        "source_sha256": sha(SRC),
        "source_bytes": SRC.stat().st_size,
        "file": f"fonts/{DST.name}",
        "sha256": sha(DST),
        "bytes": DST.stat().st_size,
        "codepoints": [f"U+{ord(c):04X}" for c in chars],
        "charters": chars,
        "count": len(chars),
        "generated": "tools/subset-deva.py",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def check() -> int:
    if not REG.is_file() or not DST.is_file():
        print("нет реестра или файла — запустите без --check")
        return 1
    reg = json.loads(REG.read_text(encoding="utf-8"))
    ok = True
    if reg.get("source_sha256") != sha(SRC):
        print("ПРОТУХ: источник изменился, сабсет собран из другого файла")
        ok = False
    if reg.get("sha256") != sha(DST):
        print("ПРОТУХ: файл сабсета не совпадает с реестром")
        ok = False
    chars, _ = collect()
    extra = [c for c in chars if c not in reg.get("charters", "")]
    if extra:
        print(f"НЕ ПОКРЫТО: сайт использует {[(c, f'U+{ord(c):04X}') for c in extra]}")
        ok = False
    print(f"реестр: {reg.get('count')} кодпойнтов, {reg.get('bytes')} Б; "
          f"на сайте сейчас {len(chars)}; {'OK' if ok else 'ПЕРЕСОБРАТЬ'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        return check()
    chars, where = collect()
    print(f"деванагари на сайте: {len(chars)} кодпойнтов, страницы: {', '.join(where)}")
    build(chars)
    return 0


if __name__ == "__main__":
    sys.exit(main())
