#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сабсеты шрифтов для переключателя языка (генерируются один раз, лежат в git).

Зачем: переключатель показывает ДЕВЯТЬ названий языков своими письменностями.
Основные страницы держат полные сабсеты по письменностям, и когда <details>
открывается, браузер честно качает всё, чего не хватает для этих девяти слов:
  en/tr: +140.8 КБ (cyrillic 14.2 + vietnamese 8.3 + devanagari 118.4)
  ru/uk: +126.7 КБ, vi: +132.5 КБ, hi: +22.5 КБ
То есть смена языка — самое дорогое действие на странице.
Эти три файла содержат ровно те глифы, что нужны девяти названиям, и объявлены
УЗКИМ unicode-range, поэтому в переключателе побеждают они, а полные сабсеты
остаются только там, где на них есть текст страницы.

Требования: fonttools + brotli (в сборке не участвует — ассеты закоммичены).
Запуск: python3 tools/make-lang-fonts.py  (печатает размеры и cmap-проверку)
"""
import hashlib
import json
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

# Названия языков ровно как в LABELS (tools/build.py). Хвостовые/ведущие пробелы
# не нужны: пробел берётся из Manrope latin.
NAMES = {
    "cyrillic": "РусскийУкраїнська",
    "vietnamese": "TiếngViệt",
    "devanagari": "हिन्दी",
}
SRC = {
    "cyrillic": "manrope-cyrillic.woff2",
    "vietnamese": "manrope-vietnamese.woff2",
    "devanagari": "noto-sans-devanagari.woff2",
}
DST = {
    "cyrillic": "langs-cyrillic.woff2",
    "vietnamese": "langs-vietnamese.woff2",
    "devanagari": "langs-devanagari.woff2",
}


def build(key: str) -> Path:
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]     # сохранить шейпинг (деванагари: half/pres/abvs…)
    opts.hinting = False
    opts.desubroutinize = True
    opts.name_IDs = ["*"]
    opts.name_languages = ["*"]
    opts.notdef_outline = True
    opts.recalc_bounds = True
    font = subset.load_font(str(FONTS / SRC[key]), opts)
    sub = subset.Subsetter(options=opts)
    sub.populate(text=NAMES[key])
    sub.subset(font)
    out = FONTS / DST[key]
    subset.save_font(font, str(out), opts)
    font.close()
    return out


def css_range(text: str, cmap: set) -> str:
    """unicode-range ТОЧНО по глифам файла: в него попадают только символы названий,
    которые в файле реально есть (латиница «Tiếng Việt» приходит из Manrope latin).
    Шире объявлять нельзя — иначе сабсет «забирает» чужие символы и молча
    отдаёт их системному шрифту."""
    cps = sorted({ord(ch) for ch in text if ch != " " and ord(ch) in cmap})
    return ",".join(f"U+{cp:04X}" for cp in cps)


def main() -> None:
    lock = {}
    for key in SRC:
        out = build(key)
        f = TTFont(str(out), lazy=True)
        cmap = set()
        for t in f["cmap"].tables:
            cmap |= set(t.cmap)
        missing = [ch for ch in NAMES[key] if ord(ch) not in cmap and ch != " "]
        axes = [a.axisTag for a in f["fvar"].axes] if "fvar" in f else []
        f.close()
        data = out.read_bytes()
        lock[key] = {
            "file": f"fonts/{DST[key]}",
            "range": css_range(NAMES[key], cmap),
            "names": NAMES[key],
            "source": SRC[key],
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        print(f"{DST[key]:28s} {out.stat().st_size:6d} B  glyphs={len(cmap):3d} "
              f"axes={axes} missing={missing} range={lock[key]['range']}")
    (ROOT / "tools" / "lang-fonts.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("tools/lang-fonts.json записан")


if __name__ == "__main__":
    main()
