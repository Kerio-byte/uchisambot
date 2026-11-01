#!/usr/bin/env python3
"""check-og-ink.py — на карточках превью действительно написан свой язык.

Повод (01.11.2026, тридцатый блок). Прибор `og-cards --check` сверяет PNG с реестром
`tools/og-cards.lock.json`: размер, вес файла, `img_sha` против отпечатка, `text_sha`
против словаря. Реестр при этом пишет САМ рендерер, в том же прогоне, которым рисует
карточки. Значит проверка доказывает ровно одно: «файл не менялся с тех пор, как его
отрисовали». Что на нём нарисовано — не проверяет никто, и три поломки проходят
зелёными:

  1) перерисовали все девять карточек одной английской строкой (например, словарь
     открылся не тот) — `text_sha` у каждого языка свой и на месте, `img_sha` совпадает
     с тем, что нарисовалось: девять одинаковых картинок, каждая «OK»;
  2) отрисовали пустую карточку (шрифт не загрузился, `document.fonts` не дождались) —
     реестр честно запишет отпечаток пустоты, и это тоже «OK»;
  3) текст не влез и уехал за край: подгонка кегля упирается в минимум 24 px (tag) и
     20 px (desc) и молча останавливается — обрезка не видна никому, потому что карточку
     превью в браузере не открывают, её показывает Telegram в углу сообщения.

Что меряет этот прибор (числами, без модели):

  * размер ровно 1200x630 и вес файла (пустой PNG весит копейки);
  * «знаки» = пиксели темнее фона в текстовой колонке (x от 386, левее стоит иконка);
  * строки: сколько их и не касается ли какая-нибудь верхнего/нижнего края;
  * правый край: не доходит ли краска до границы кадра (обрезанный текст);
  * отличие: каждая пара карточек обязана отличаться заметным числом пикселей —
    это и есть «у каждого языка своя картинка» (правило владельца 15.10).

Чего прибор НЕ делает (названо, чтобы «не измерили» не читалось как «измерили и хорошо»):
не читает буквы и не проверяет, что на карточке именно этот язык, а не соседний
кириллический. Такой замер — работа глаза, а не арифметики.

Запуск:
  python3 tools/check-og-ink.py              # девять карточек в img/
  python3 tools/check-og-ink.py --root DIR   # то же на копии дерева (DIR/img/og-*.png)
  python3 tools/check-og-ink.py --control    # проверка самого прибора: четыре мутанта
  python3 tools/check-og-ink.py --json       # машинный вывод
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _og():
    """Константы рендерера берём у него самого, а не копией: две копии расходятся."""
    spec = importlib.util.spec_from_file_location("og_cards", HERE / "og-cards.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


OG = _og()
LANGS = list(OG.LANGS)
W, H = OG.W, OG.H

# Текстовая колонка: 88 (левый отступ) + 220 (иконка) + 78 (зазор); правая граница с
# запасом 12 px до края кадра. Левее 386 стоит иконка — её краска не текст.
ZONE_X0 = 88 + 220 + 78
EDGE = 12
ZONE_X1 = W - EDGE

INK_LEVEL = 200     # фон карточки светлый (яркость ~238), текст темнее 200
TOP_SAFE = 8        # ни одна строка не начинается выше и не кончается ниже
BOTTOM_SAFE = 8
BANDS_MIN = 4       # имя, подзаголовок, строка возможностей (1-2), ссылка
BANDS_MAX = 6
MIN_INK = 15000     # при 1200x630 полный текст даёт ~66 000 пикселей краски
MIN_BYTES = 15000   # пустая карточка весит копейки
MIN_DIFF = 0.002    # доля различающихся пикселей колонки между двумя языками


def _mask(im: Image.Image) -> Image.Image:
    return im.convert("L").point(lambda v: 255 if v < INK_LEVEL else 0)


def _bands(zone: Image.Image) -> list[tuple[int, int]]:
    """Строки с краской, склеенные в полосы; разрыв до 6 px — это не новая полоса."""
    width = zone.width
    rows = zone.tobytes()
    counts = [rows[y * width:(y + 1) * width].count(255) for y in range(H)]
    out: list[tuple[int, int]] = []
    start = None
    gap = 0
    for y in range(H):
        if counts[y]:
            if start is None:
                start = y
            gap = 0
        elif start is not None:
            gap += 1
            if gap > 6:
                out.append((start, y - gap))
                start = None
                gap = 0
    if start is not None:
        out.append((start, H - 1 - gap))
    return out


def check_card(p: Path) -> tuple[list[str], dict]:
    """Одна карточка: находки и числа для отчёта."""
    bad: list[str] = []
    if not p.exists():
        return [f"нет файла {p.name}"], {}
    with Image.open(p) as im:
        im = im.convert("RGB")
        size, nbytes = im.size, p.stat().st_size
        if size != (W, H):
            bad.append(f"{p.stem}: размер {size[0]}x{size[1]}, ждали {W}x{H}")
        zone = _mask(im).crop((ZONE_X0, 0, ZONE_X1, H))
    counts = zone.tobytes()
    ink = sum(1 for b in counts if b == 255)
    if nbytes < MIN_BYTES:
        bad.append(f"{p.stem}: файл {nbytes} B — пустая карточка")
    if ink < MIN_INK:
        bad.append(f"{p.stem}: знаков {ink} (порог {MIN_INK}) — текста на карточке нет")
    bands = _bands(zone)
    if not (BANDS_MIN <= len(bands) <= BANDS_MAX):
        bad.append(f"{p.stem}: полос текста {len(bands)}, ждали {BANDS_MIN}-{BANDS_MAX}")
    if bands:
        if bands[0][0] < TOP_SAFE:
            bad.append(f"{p.stem}: первая строка в {bands[0][0]} px от верха — срезана")
        if bands[-1][1] > H - 1 - BOTTOM_SAFE:
            bad.append(f"{p.stem}: последняя строка в {H - 1 - bands[-1][1]} px от низа — срезана")
        for y0, y1 in bands:
            box = zone.crop((0, y0, ZONE_X1 - ZONE_X0, y1 + 1)).getbbox()
            if box is None:
                continue
            maxx = ZONE_X0 + box[2]
            if maxx >= ZONE_X1:
                bad.append(f"{p.stem}: краска у правого края (x={maxx} при границе {ZONE_X1}) — текст обрезан")
                break
    return bad, {"ink": ink, "bands": len(bands), "bytes": nbytes, "size": list(size)}


def check_tree(img_dir: Path) -> tuple[list[str], dict]:
    bad: list[str] = []
    stats: dict = {}
    masks: dict[str, Image.Image] = {}
    for lang in LANGS:
        p = img_dir / f"og-{lang}.png"
        b, s = check_card(p)
        bad += b
        stats[lang] = s
        if p.exists():
            with Image.open(p) as im:
                masks[lang] = _mask(im).crop((ZONE_X0, 0, ZONE_X1, H))
    # Отличие: у каждого языка своя картинка.
    zone_area = (ZONE_X1 - ZONE_X0) * H
    worst = (1.0, "")
    drawn = [lg for lg in LANGS if lg in masks]
    for i, a in enumerate(drawn):
        for b_lg in drawn[i + 1:]:
            hist = _diff_hist(masks[a], masks[b_lg])
            diff = (zone_area - hist[0]) / zone_area
            if diff < worst[0]:
                worst = (diff, f"{a}/{b_lg}")
            if diff < MIN_DIFF:
                bad.append(
                    f"{a} и {b_lg}: отличаются на {diff:.4%} пикселей текста (порог {MIN_DIFF:.1%}) — "
                    f"одна карточка на два языка"
                )
    stats["worst_diff"] = {"pair": worst[1], "share": round(worst[0], 6)}
    return bad, stats


def _diff_hist(a: Image.Image, b: Image.Image):
    from PIL import ImageChops
    return ImageChops.difference(a, b).histogram()


def control(verbose: bool = True) -> int:
    """Четыре состояния мира, каждое обязано быть названо своим именем."""
    tmp = Path(tempfile.mkdtemp(prefix="og-ink-ctl-"))
    caught: list[str] = []
    try:
        clean = tmp / "clean" / "img"
        clean.mkdir(parents=True)
        for lg in LANGS:
            shutil.copy(ROOT / "img" / f"og-{lg}.png", clean / f"og-{lg}.png")
        bad, _ = check_tree(clean)
        if bad:
            print("КОНТРОЛЬ СЛОМАН: чистая копия не зелёная —", "; ".join(bad[:3]))
            return 1

        def run(name: str, prepare) -> None:
            d = tmp / name / "img"
            d.mkdir(parents=True)
            for lg in LANGS:
                shutil.copy(ROOT / "img" / f"og-{lg}.png", d / f"og-{lg}.png")
            prepare(d)
            found, _ = check_tree(d)
            hit = bool(found)
            if verbose:
                print(f"{'поймал' if hit else 'НЕ ПОЙМАЛ'} {name}: {found[0] if found else '—'}")
            if hit:
                caught.append(name)

        def blank(d: Path) -> None:
            with Image.open(d / "og-ru.png") as im:
                im = im.convert("RGB")
                im.paste((255, 255, 255), (ZONE_X0, 0, W, H))
                im.save(d / "og-ru.png")

        def double(d: Path) -> None:
            shutil.copy(d / "og-en.png", d / "og-es.png")

        def clipped(d: Path) -> None:
            with Image.open(d / "og-uk.png") as im:
                im = im.convert("RGB")
                part = im.crop((ZONE_X0, 0, ZONE_X1, H)).resize((int((ZONE_X1 - ZONE_X0) * 1.35), H))
                im.paste((255, 255, 255), (ZONE_X0, 0, W, H))
                im.paste(part, (ZONE_X0, 0))
                im.save(d / "og-uk.png")

        def missing(d: Path) -> None:
            (d / "og-tr.png").unlink()

        run("пустая карточка", blank)
        run("две карточки одним языком", double)
        run("текст за краем", clipped)
        run("карточки нет", missing)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = 4
    print(f"МУТАНТЫ {len(caught)}/{total}")
    return 0 if len(caught) == total else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="карточки og: на них действительно есть текст своего языка")
    ap.add_argument("--root", default="", help="дерево с img/og-*.png (по умолчанию это)")
    ap.add_argument("--control", action="store_true", help="проверка самого прибора: четыре мутанта")
    ap.add_argument("--json", action="store_true", help="машинный вывод")
    a = ap.parse_args()

    if a.control:
        return control()

    img_dir = (Path(a.root).resolve() if a.root else ROOT) / "img"
    bad, stats = check_tree(img_dir)
    if a.json:
        print(json.dumps({"findings": bad, "stats": stats, "langs": len(LANGS)}, ensure_ascii=False))
        return 1 if bad else 0
    for lang in LANGS:
        s = stats.get(lang) or {}
        print(f"  {lang:3} {s.get('size', ['?', '?'])[0]}x{s.get('size', ['?', '?'])[1]}"
              f" знаков={s.get('ink', 0):6} полос={s.get('bands', 0)} {s.get('bytes', 0)} B")
    worst = stats.get("worst_diff") or {}
    print(f"ближе всего друг к другу: {worst.get('pair', '-')} — отличаются на "
          f"{(worst.get('share') or 0):.2%} пикселей текста")
    if bad:
        print(f"НАХОДОК {len(bad)}:")
        for line in bad:
            print("  FAIL", line)
        return 1
    print(f"КАРТОЧКИ: {len(LANGS)}, находок 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
