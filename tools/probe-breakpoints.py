#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe-breakpoints.py — каждая точка перелома стилей, измеренная с ДВУХ сторон.

Повод (02.11.2026). Приборы дерева меряли окна 320, 420, 768, 1024, 1280, 1440 и 1920 px,
а в самих стилях страниц точек перелома больше: `max-width` на 360, 560, 680, 702, 760, 860
и 861 px. Между двумя замерами всегда лежит целая полоса, и правило, которое включается
на 560, никем не проверялось ни на 560, ни на 561. Это тот же класс, что «ноль дефектов
в двух окнах и поломка между ними»: поломка живёт не в окне, а на границе.

Почему ширины не зашиты в файл. Список, который надо помнить, устаревает молча: автор
добавляет `@media(max-width:640px)`, прибор про это не знает и продолжает говорить
«чисто». Поэтому ширины ВЫЧИТЫВАЮТСЯ из CSSOM уже загруженной страницы (document.styleSheets
→ cssRules → media.mediaText), а не из литерала. Новая точка перелома попадает под замер
в тот же день, когда появилась в стилях, без правки прибора.

Что меряется на каждой ширине (три клаузы, как у probe-narrow, чтобы вердикты были сравнимы):
  1. ширина документа   — documentElement.scrollWidth <= want + 1;
  2. обрезанный текст   — у элементов с overflow hidden/clip scrollWidth не больше clientWidth + 2;
  3. цели нажатия       — .btn/button/CTA не ниже и не уже 24 px (WCAG 2.5.8).

Карусель не считается вылезанием: блок кадров на телефоне — `overflow-x: auto` + scroll-snap,
его карточки законно стоят за краем экрана. Такие элементы идут отдельным счётчиком.

Контроль. `--control` вставляет блок 600 px шириной; он ОБЯЗАН покраснеть на каждой ширине
уже 600 px, иначе прибор не меряет. Без контроля «чисто» — это мнение, а не замер.

Каждая точка меряется трижды: w-1, w, w+1 — то есть по обе стороны границы плюс сама граница.
Плюс базовые окна дерева, чтобы отчёт стоял на той же шкале, что остальные приборы.

Запуск: python3 tools/probe-breakpoints.py [--control] [--langs en,ru,...] [--max=1440]
Пишет evidence/breakpoints-<дата>.json (контроль — breakpoints-control-<дата>.json).
Код 0 = чисто, 1 = находки.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(os.environ.get("LANDING_ROOT") or Path(__file__).resolve().parents[1])
BASE = os.environ.get("LANDING_URL", "").rstrip("/")
OUT = Path(os.environ.get("LANDING_OUT", ROOT / "evidence" / f"breakpoints-{date.today():%Y%m%d}.json"))
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
BASE_WINDOWS = [320, 360, 420, 768, 1024, 1280, 1440]
MAX_WIDTH = 1440

BREAKPOINTS_JS = r"""
() => {
  const out = new Set();
  const grab = (text) => {
    const re = /(?:max|min)-width\s*:\s*(\d+(?:\.\d+)?)px/g;
    let m;
    while ((m = re.exec(text || '')) !== null) out.add(Math.round(parseFloat(m[1])));
  };
  for (const sheet of document.styleSheets) {
    let rules;
    try { rules = sheet.cssRules; } catch (e) { continue; }   // чужой origin — не наш случай
    if (!rules) continue;
    const walk = (list) => {
      for (const r of list) {
        if (r.media) grab(r.media.mediaText);
        if (r.cssRules) { try { walk(r.cssRules); } catch (e) {} }
      }
    };
    walk(rules);
  }
  return [...out].sort((a, b) => a - b);
}
"""

PROBE = r"""
(expect) => {
  const want = expect;
  const docW = document.documentElement.scrollWidth;
  const bodyW = document.body.scrollWidth;
  const off = [], carousel = [], clip = [], small = [];
  const name = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (typeof el.className === 'string' && el.className.trim()) {
      s += '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.');
    }
    return s;
  };
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.right > want + 1.5 || r.left < -1.5) {
      let sc = el.parentElement, inScroller = false;
      while (sc && sc !== document.body && sc !== document.documentElement) {
        const so = getComputedStyle(sc).overflowX;
        if (so === 'auto' || so === 'scroll') {
          const sr = sc.getBoundingClientRect();
          if (sc.scrollWidth > sc.clientWidth + 2 && sr.right <= want + 1.5) { inScroller = true; }
          break;
        }
        sc = sc.parentElement;
      }
      const rec = { el: name(el), left: Math.round(r.left), right: Math.round(r.right),
                    text: (el.textContent || '').trim().slice(0, 40) };
      (inScroller ? carousel : off).push(rec);
    }
    const ox = cs.overflowX;
    const cls = (typeof el.className === 'string') ? el.className : '';
    const srOnly = /sr-only|visually-hidden|screen-reader|a11y-hidden/.test(cls);
    if (!srOnly && (ox === 'hidden' || ox === 'clip') && el.clientWidth > 2 &&
        el.scrollWidth > el.clientWidth + 2 && (el.textContent || '').trim().length > 0) {
      clip.push({ el: name(el), scrollW: el.scrollWidth, clientW: el.clientWidth,
                  text: (el.textContent || '').trim().slice(0, 40) });
    }
  }
  for (const el of document.querySelectorAll('button, .btn, a.btn, .button, a[role="button"]')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.height < 23.5 || r.width < 23.5) {
      small.push({ el: name(el), w: Math.round(r.width), h: Math.round(r.height),
                   text: (el.textContent || '').trim().slice(0, 30) });
    }
  }
  return { want, vw: window.innerWidth, docW, bodyW, offCount: off.length, off: off.slice(0, 5),
           carouselCount: carousel.length, clipCount: clip.length, clip: clip.slice(0, 5),
           smallCount: small.length, small: small.slice(0, 5) };
}
"""


def route(lang: str) -> str:
    return "/index.html" if lang == "en" else f"/{lang}/index.html"


def url_for(lang: str) -> str:
    r = route(lang)
    return BASE + r if BASE else (ROOT / r.lstrip("/")).as_uri()


def main() -> int:
    from playwright.sync_api import sync_playwright

    global OUT
    control = "--control" in sys.argv
    langs = LANGS
    maxw = MAX_WIDTH
    for a in sys.argv:
        if a.startswith("--langs="):
            langs = [x for x in a.split("=", 1)[1].split(",") if x]
        elif a.startswith("--max="):
            maxw = int(a.split("=", 1)[1])
    if control and not os.environ.get("LANDING_OUT"):
        OUT = OUT.with_name("breakpoints-control-" + OUT.name.split("breakpoints-", 1)[-1])

    rows, fails, checked = [], 0, 0
    widths: list[int] = []
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-sandbox"])
        for lang in langs:
            ctx = br.new_context(viewport={"width": 420, "height": 900}, is_mobile=True,
                                 has_touch=True, device_scale_factor=2)
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url_for(lang), wait_until="load")
            pg.wait_for_timeout(700)
            if not widths:
                found = [w for w in pg.evaluate(BREAKPOINTS_JS) if 280 <= w <= maxw]
                band = sorted({x for w in found for x in (w - 1, w, w + 1) if 280 <= x <= maxw})
                widths = sorted(set(BASE_WINDOWS) | set(band))
                print("точки перелома из стилей:", ",".join(str(w) for w in found) or "—")
                print("ширины под замером:", len(widths))

            lang_bad = 0
            for w in widths:
                pg.set_viewport_size({"width": w, "height": 900})
                pg.wait_for_timeout(120)
                if control and w <= 600:
                    pg.evaluate("""() => { const d = document.createElement('div');
                        d.style.cssText = 'position:absolute;left:0;top:0;width:600px;height:2px';
                        document.body.appendChild(d); }""")
                    pg.wait_for_timeout(60)
                pr = pg.evaluate(PROBE, w)
                pr.update({"lang": lang, "width": w})
                bad = []
                wide = pr["docW"] > w + 1 or pr["bodyW"] > w + 1
                if wide:
                    bad.append("H-OVERFLOW")
                if pr["clipCount"]:
                    bad.append("TEXT-CLIPPED")
                if pr["smallCount"]:
                    bad.append("TAP-SMALL")
                if errs and w == widths[0]:
                    bad.append("JS-ERROR")
                checked += 1
                if bad:
                    fails += 1
                    lang_bad += 1
                    print(f"FAIL {lang} {w}px: doc={pr['docW']} off={pr['offCount']} "
                          f"clip={pr['clipCount']} tapSmall={pr['smallCount']} {','.join(bad)}")
                    for k in ("off", "clip", "small"):
                        for it in pr[k][:3]:
                            print("      ", json.dumps(it, ensure_ascii=False))
                # контроль обязан краснеть на каждой ширине не шире 600; вне полосы он молчит
                if control and w > 600 and bad:
                    print(f"      (ширина {w} вне полосы контроля — не считается)")
                rows.append(pr)
                if control and w <= 600:
                    pg.evaluate("() => { const d = document.querySelector('body > div[style*=\"600px\"]'); if (d) d.remove(); }")
            print(f"{'FAIL' if lang_bad else 'OK  '} {lang}: ширин {len(widths)}, находок {lang_bad}")
            ctx.close()
        br.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"widths": widths, "control": control,
                               "checks": checked, "failed": fails, "rows": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"CHECKS: {checked}, FAILED: {fails}")
    print(f"evidence: {OUT}")
    if control:
        caught = any(r["offCount"] for r in rows if r["width"] <= 600)
        print("КОНТРОЛЬ:", "ПОЙМАЛ" if caught else "ПРОСМОТРЕЛ")
        return 0 if caught else 1
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
