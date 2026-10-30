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


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default=",".join(LANGS))
    ap.add_argument("--no-shots", action="store_true")
    ap.add_argument("--control", action="store_true",
                    help="вставить блок шире окна: прибор ОБЯЗАН покраснеть")
    args = ap.parse_args()
    langs = [x for x in args.langs.split(",") if x]
    day = f"{date.today():%Y%m%d}"
    shots = ROOT / "evidence" / f"visual-{day}"
    # Контрольный прогон пишет СВОЙ файл: 30.10.2026 ровно эта ошибка уже была
    # у узкого прибора — контроль затирал чистое доказательство.
    control = args.control
    if not args.no_shots and not control:
        shots.mkdir(parents=True, exist_ok=True)

    rows, fails = [], 0
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
                ctx.close()
        br.close()

    out = ROOT / "evidence" / f"visual-{day}{'-control' if control else ''}.json"
    out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"CHECKS: {len(rows) * 3}, FAILED: {fails}")
    print(f"evidence: {out}")
    if not args.no_shots and not control:
        print(f"снимки: {shots.relative_to(ROOT)} ({len(rows)} шт.)")
    if control:
        caught = sum(1 for r in rows if "H-OVERFLOW" in r["bad"])
        print(f"КОНТРОЛЬ: поймал {caught} из {len(rows)}")
        return 0 if caught == len(rows) else 1
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
