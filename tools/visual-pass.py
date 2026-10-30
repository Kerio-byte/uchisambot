#!/usr/bin/env python3
"""visual-pass.py — геометрия страницы на 420 px и на десктопе, плюс снимки.

Повод. До 30.10.2026 «визуальный блок» опирался на landing-visual-pass.py,
лежавший вне репозитория в каталоге одноразовых скриптов. Каталог чистится
через сутки — к этому запуску прибора уже не было. Осталось бы снова собирать
его руками, а «смотрел глазами» держалось бы на памяти.

Что делает:

  1) открывает девять страниц в двух окнах — телефон 420x900 и десктоп
     1440x900 — и снимает геометрию тем же мерилом, что probe-narrow.py
     (выражение берётся из него импортом, а не копией: две копии одного
     мерила расходятся в первый же месяц);
  2) кладёт полноэкранные снимки в evidence/visual-<дата>/ — материал для
     глаз человека; сам прибор смотрит числами;
  3) считает дефектами: вылезание за ширину окна, обрезанный текст в блоках
     с overflow hidden, ошибки JS. Мелкие кнопки — только на телефоне
     (WCAG 2.5.8 про палец); на десктопе они идут справочно.

Запуск:
  python3 tools/visual-pass.py                 # 9 языков, оба окна, снимки
  python3 tools/visual-pass.py --no-shots      # только числа
  python3 tools/visual-pass.py --langs=en,ru   # подмножество
  python3 tools/visual-pass.py --frames        # ещё и кадры по блокам для глаза

Повод (31.10.2026). Глаз (`landing-eye.py`) читает кадры ОДНОГО блока:
`evidence/visual-<дата>/<lang>-{m,d}-<section>.png`. Резал их одноразовый
`landing-visual-pass.py` вне репозитория — у него нет ни `--help`, ни
`--langs`, и он падает на первом `goto`. К 31.10 кадров за сегодня не было
вовсе: зарегистрированный прибор снимал только полные страницы, а глаз
без своих кадров отвечает `FAIL: нет кадров` — то есть «смотрел глазами»
держалось на скрипте, которого уже нет. `--frames` режет кадры здесь же,
теми же окнами и в том же каталоге, что ждёт глаз.

Возврат 0 — дефектов нет, 1 — есть.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = os.environ.get("LANDING_URL", "").rstrip("/")
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
VIEWPORTS = [("mobile", 420, 900, True), ("desktop", 1440, 900, False)]

spec = importlib.util.spec_from_file_location(
    "probe_narrow", ROOT / "tools" / "probe-narrow.py")
assert spec and spec.loader, "probe-narrow.py не найден рядом"
probe_narrow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe_narrow)  # только строки и константы, main под guard
PROBE = probe_narrow.PROBE


def url_for(lang: str) -> str:
    rel = "/index.html" if lang == "en" else f"/{lang}/index.html"
    return BASE + rel if BASE else (ROOT / rel.lstrip("/")).as_uri()


# Блоки, которые глаз просит по имени (ключи совпадают с SECTION_MARK в
# landing-eye.py), и их селекторы. Список держится здесь, а не в голове:
# разойдётся с глазом — кадр получит имя, которого глаз не спросит.
SECTIONS = {
    "head": "header.top",
    "hero": "section.hero",
    "band": ".band",
    "principle": ".principle-band",
    "ref": ".ref-band",
    "parents": ".parents-band",
    "contact": "#contact",
    "footer": "footer",
}


def cut_frames(pg, shots: Path, lang: str, side: str) -> int:
    """Кадры одного блока — ровно те имена, что ждёт landing-eye.py."""
    cut = 0
    for name, sel in SECTIONS.items():
        el = pg.query_selector(sel)
        if el is None:
            continue
        box = el.bounding_box()
        if not box or box["height"] < 8 or box["width"] < 8:
            continue
        el.screenshot(path=str(shots / f"{lang}-{side}-{name}.png"))
        cut += 1
    return cut


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default=",".join(LANGS))
    ap.add_argument("--no-shots", action="store_true")
    ap.add_argument("--control", action="store_true",
                    help="вставить блок шире окна: прибор ОБЯЗАН покраснеть")
    ap.add_argument("--frames", action="store_true",
                    help="резать кадры по блокам для landing-eye.py")
    args = ap.parse_args()
    langs = [x for x in args.langs.split(",") if x]
    day = f"{date.today():%Y%m%d}"
    shots = ROOT / "evidence" / f"visual-{day}"
    # Контрольный прогон пишет СВОЙ файл: 30.10.2026 ровно эта ошибка уже была
    # у узкого прибора — контроль затирал чистое доказательство.
    control = args.control
    if not args.no_shots and not control:
        shots.mkdir(parents=True, exist_ok=True)
    if args.frames and control:
        ap.error("--frames с --control несовместимы: контроль не пишет кадров")

    rows, fails, frames = [], 0, 0
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-sandbox"])
        for name, width, height, mobile in VIEWPORTS:
            for lang in langs:
                ctx = br.new_context(
                    viewport={"width": width, "height": height},
                    is_mobile=mobile, has_touch=mobile,
                    device_scale_factor=1)
                pg = ctx.new_page()
                errs: list[str] = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(url_for(lang), wait_until="load")
                pg.wait_for_timeout(600)
                pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                pg.wait_for_timeout(1000)
                pg.evaluate("window.scrollTo(0, 0)")
                pg.wait_for_timeout(250)
                if control:
                    pg.evaluate("""(w) => { const d = document.createElement('div');
                        d.style.cssText = 'position:absolute;left:0;top:0;width:' + (w + 200) +
                        'px;height:2px';
                        document.body.appendChild(d); }""", width)
                    pg.wait_for_timeout(120)
                pr = pg.evaluate(PROBE, width)
                pr.update({"lang": lang, "viewport": name, "width": width,
                           "jsErrors": errs})
                bad = []
                if pr["docW"] > width + 1 or pr["bodyW"] > width + 1:
                    bad.append("H-OVERFLOW")
                if pr["clipCount"]:
                    bad.append("TEXT-CLIPPED")
                if mobile and pr["smallCount"]:
                    bad.append("TAP-SMALL")
                if errs:
                    bad.append("JS-ERROR")
                pr["bad"] = bad
                fails += 1 if bad else 0
                rows.append(pr)
                print(f"{'FAIL' if bad else 'OK  '} {name:<7} {lang}: "
                      f"doc={pr['docW']}/{width} off={pr['offCount']} "
                      f"carousel={pr['carouselCount']} clip={pr['clipCount']} "
                      f"tapSmall={pr['smallCount']} {','.join(bad)}")
                for key in ("off", "clip", "small"):
                    for item in pr[key][:3]:
                        print("       ", json.dumps(item, ensure_ascii=False))
                if not args.no_shots and not control:
                    shot = shots / f"{name}-{lang}.png"
                    pg.screenshot(path=str(shot), full_page=(name == "mobile"))
                    pr["shot"] = str(shot.relative_to(ROOT))
                if args.frames:
                    side = "m" if mobile else "d"
                    frames += cut_frames(pg, shots, lang, side)
                ctx.close()
        br.close()

    out = ROOT / "evidence" / f"visual-{day}{'-control' if control else ''}.json"
    out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"CHECKS: {len(rows) * 3}, FAILED: {fails}")
    print(f"evidence: {out}")
    if not args.no_shots and not control:
        print(f"снимки: {shots.relative_to(ROOT)} ({len(rows)} шт.)")
    if args.frames:
        want = len(SECTIONS) * len(rows)
        print(f"кадры по блокам: {frames} из {want} возможных")
        if want and frames < len(langs) * 2:
            print("FAIL: кадров меньше, чем блоков у одного языка — глаз прочитает пустоту")
            fails += 1
    if control:
        caught = sum(1 for r in rows if "H-OVERFLOW" in r["bad"])
        print(f"КОНТРОЛЬ: поймал {caught} из {len(rows)}")
        return 0 if caught == len(rows) else 1
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
