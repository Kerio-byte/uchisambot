#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/shot-docs.py — кадры документов (privacy, terms, 404) для глаза.

Повод (06.11.2026, блок 101). `landing-eye.py --docs privacy,terms,404` ждёт
именно `{doc}-{m|d}.png` в своём каталоге кадров, но прибор, который бы эти
кадры резал, в дереве не было: глаз по документам краснел «нет кадров» и
контроль про себя говорил «пропущен» — то есть ветвь документов проверена
не была, а не что документов нет. До 06.11 эту ветвь в свип не звали, поэтому
дыра была невидима.

Что делает. Открывает документ из дерева (по пути `{doc}.html`) в ДВУХ окнах —
420×900 mobile и 1440×900 desktop, device_scale_factor=2 (как кадры страниц в
`visual-pass.py`, 31.10.2026: 1x на десктопе мелкая типографика нечитаетса,
глаз сливает строки) — и режет кадр блока: на мобильном весь контент
(full_page), на десктопе видимая область. Имена ровно те, что ждёт глаз:
`privacy-m.png`, `privacy-d.png`, `terms-m.png`, `terms-d.png`, `404-m.png`,
`404-d.png`.

Контроль (--control): вставляет в документ блок, шире окна, и ОБЯЗАН покраснеть
H-OVERFLOW — тот же приём, что у `visual-pass.py --control` и `probe-narrow.py
--control`: прибор, который не ловит очевидный дефект, сам по себе дефект.
Контрольный прогон пишет СВОЙ файл (прецедент 30.10.2026: контроль затирал
чистое доказательство чужого прогона).

Код возврата: 0 — зелёное, 1 — дефект, 2 — контроль не доказал прибор.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ("privacy", "terms", "404")

# Проба ширины — та же логика, что в probe-narrow.py/visual-pass.py:
# docW/bodyW больше окна, есть ли переполнение в блоках.
PROBE = """(width) => {
  const docW = Math.max(document.documentElement.scrollWidth,
                        document.body ? document.body.scrollWidth : 0);
  const bodyW = document.body ? document.body.scrollWidth : 0;
  let off = 0;
  if (document.body) {
    for (const el of document.body.querySelectorAll('*')) {
      if (el.scrollWidth > width + 1) off++;
    }
  }
  return {docW: docW, bodyW: bodyW, offCount: off};
}"""


def url_for(doc: str) -> str:
    rel = f"{doc}.html"
    base = os.environ.get("LANDING_URL", "").rstrip("/")
    if base:
        return base + "/" + rel
    return (ROOT / rel).as_uri()


def shoot(pw, doc: str, out: Path) -> list[dict]:
    rows = []
    for name, width, height, mobile in (
        ("mobile", 420, 900, True),
        ("desktop", 1440, 900, False),
    ):
        ctx = pw.new_context(
            viewport={"width": width, "height": height},
            is_mobile=mobile, has_touch=mobile,
            device_scale_factor=2)
        pg = ctx.new_page()
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url_for(doc), wait_until="load")
        pg.wait_for_timeout(400)
        pr = pg.evaluate(PROBE, width)
        pr.update({"doc": doc, "viewport": name, "width": width,
                   "jsErrors": errs})
        bad = []
        if pr["docW"] > width + 1 or pr["bodyW"] > width + 1:
            bad.append("H-OVERFLOW")
        if pr["offCount"]:
            bad.append("OVERFLOW-EL")
        if errs:
            bad.append("JS-ERROR")
        pr["bad"] = bad
        rows.append(pr)
        side = "m" if mobile else "d"
        png = out / f"{doc}-{side}.png"
        pg.screenshot(path=str(png), full_page=mobile)
        pr["shot"] = str(png.relative_to(ROOT))
        print(f"{'FAIL' if bad else 'OK  '} {doc} {name}: "
              f"doc={pr['docW']}/{width} off={pr['offCount']} {','.join(bad)}")
        ctx.close()
    return rows


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docs", default=",".join(DOCS))
    ap.add_argument("--out", default="",
                    help="каталог кадров (по умолчанию evidence/eye-docs-frames)")
    ap.add_argument("--control", action="store_true",
                    help="вставить блок шире окна: прибор ОБЯЗАН поймать H-OVERFLOW")
    args = ap.parse_args()

    docs = [d.strip() for d in args.docs.split(",") if d.strip()]
    day = __import__("datetime").date.today().strftime("%Y%m%d")
    out = Path(args.out) if args.out else ROOT / "evidence" / "eye-docs-frames"
    if args.control:
        out = out.with_name(out.name + "-control")
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-sandbox"])
        for doc in docs:
            if not (ROOT / f"{doc}.html").is_file():
                print(f"FAIL {doc}: нет {doc}.html в дереве")
                br.close()
                return 1
            rows.extend(shoot(br, doc, out))
            if args.control:
                # контроль: вставляем блок шире окна, прибор обязан поймать
                for name, width, mobile in (("mobile", 420, True),
                                           ("desktop", 1440, False)):
                    ctx = br.new_context(
                        viewport={"width": width, "height": 900},
                        is_mobile=mobile, has_touch=mobile,
                        device_scale_factor=2)
                    pg = ctx.new_page()
                    pg.goto(url_for(doc), wait_until="load")
                    pg.wait_for_timeout(300)
                    pg.evaluate("""(w) => { const d = document.createElement('div');
                      d.style.cssText = 'position:absolute;left:0;top:0;width:' + (w + 200) +
                      'px;height:2px';
                      document.body.appendChild(d); }""", width)
                    pg.wait_for_timeout(100)
                    pr = pg.evaluate(PROBE, width)
                    caught = pr["docW"] > width + 1
                    print(f"{'OK  ' if caught else 'FAIL'} control {doc} {name}: "
                          f"doc={pr['docW']}/{width} caught={caught}")
                    ctx.close()
                    if not caught:
                        br.close()
                        return 2
        br.close()

    fails = sum(1 for r in rows if r["bad"])
    out_json = out / f"shot-docs-{day}.json"
    out_json.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"CHECKS: {len(rows) * 3}, FAILED: {fails}")
    print(f"кадры: {out.relative_to(ROOT)} ({len(docs) * 2} шт.)")
    print(f"evidence: {out_json.relative_to(ROOT)}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
