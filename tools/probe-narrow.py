#!/usr/bin/env python3
"""probe-narrow.py — проверка страницы на САМОМ узком реальном телефоне (320 px).

Зачем отдельный прибор. `landing-visual-pass.py` меряет 420 px и 1440 px — это
современные телефоны и десктоп. Ниже 420 остаётся класс устройств, который страница
никогда не видела: iPhone SE первого поколения, старые Android вроде Galaxy J1,
узкое окно встроенного браузера Telegram. Там ломается именно то, чего не видно на
420: длинные слова без пробелов (немецкие/турецкие составные), таблица тарифов,
кнопки в ряд и строки кода.

Что меряется (три клаузы на язык, плюс контроль прибора):
  1. ширина документа          — documentElement.scrollWidth <= innerWidth + 1;
  2. обрезанный текст          — ни у одного элемента с overflow hidden/clip
                                 scrollWidth не больше clientWidth + 2;
  3. кнопки-цели               — все .btn/.button/button/CTA не ниже 24 px и не уже 24 px
                                 (нижняя граница «палец попадает», WCAG 2.5.8).

Контроль: `--control` вставляет блок 600 px шириной и ОБЯЗАН получить красное по
первой клаузе; иначе прибор не меряет и говорить «чисто» права не имеет.
Прогон контроля 30.10.2026: поймал 9 из 9 языков (doc=600 против 320), запись —
`evidence/narrow-control-20261030.json`. То есть право сказать «на 320 чисто» прибор
заработал, а не получил по умолчанию.

Карусель не считается вылезанием. Блок кадров на телефоне — горизонтальная лента
(`overflow-x: auto` + scroll-snap), её вторая и третья карточки стоят за краем
экрана законно, пока человек не свайпнул. Такие элементы идут отдельным счётчиком
`carouselCount` и в вердикт не входят; в `offCount` остаётся только то, что вылезло
из блока БЕЗ прокрутки, — то есть настоящая поломка.

Запуск: python3 tools/probe-narrow.py [--control] [--langs en,ru,...]
Пишет evidence/narrow-<дата>.json и печатает итог. Код 0 = чисто, 1 = находки.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(os.environ.get("LANDING_ROOT") or Path(__file__).resolve().parents[1])
# Адрес страницы. Порт и петля в файле не зашиты (правило opsec свипа): по умолчанию
# прибор открывает файлы прямо с диска через file:// и поднятый веб-сервер ему не нужен.
# Нужен HTTP — задай LANDING_URL=http://host:port.
BASE = os.environ.get("LANDING_URL", "").rstrip("/")
OUT = Path(os.environ.get("LANDING_OUT", ROOT / "evidence" / f"narrow-{date.today():%Y%m%d}.json"))
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
WIDTH = 320  # iPhone SE 1st gen / Galaxy J1 / узкое окно встроенного браузера

PROBE = r"""
(expect) => {
  const vw = window.innerWidth;
  // Ширина, с которой сравниваем, приходит СНАРУЖИ. В мобильной эмуляции Chromium
  // расширяет layout viewport под содержимое (innerWidth стал 600 после вставки
  // блока 600 px), поэтому сравнение с innerWidth слепнет именно к тому дефекту,
  // который ищем. Контроль 30.10.2026 это и показал: «ПРОСМОТРЕЛ».
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
      // Карусель — не дефект. На телефоне блок кадров становится горизонтальной
      // лентой (overflow-x: auto + scroll-snap), и её вторая-третья карточки ЗАКОННО
      // стоят за краем экрана, пока человек не свайпнул. Прежняя версия прибора
      // считала их «вылезшими» и на каждом чистом прогоне давала пять ложных строк —
      // сигнал тонул в шуме. Теперь такие элементы идут отдельным счётчиком.
      let sc = el.parentElement, inScroller = false;
      while (sc && sc !== document.body && sc !== document.documentElement) {
        const so = getComputedStyle(sc).overflowX;
        if (so === 'auto' || so === 'scroll') {
          const sr = sc.getBoundingClientRect();
          // Лента должна быть уже содержимого, иначе это не лента, а сломанный блок.
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
    // .sr-only и подобные — намеренно обрезанная до 1 px подпись для скринридера,
    // это не дефект вёрстки, а стандартный приём доступности.
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
  return { vw, want, docW, bodyW, offCount: off.length, off: off.slice(0, 6),
           carouselCount: carousel.length, clipCount: clip.length, clip: clip.slice(0, 6),
           smallCount: small.length, small: small.slice(0, 6) };
}
"""


def route(lang: str) -> str:
    return "/index.html" if lang == "en" else f"/{lang}/index.html"


def url_for(lang: str) -> str:
    r = route(lang)
    return BASE + r if BASE else (ROOT / r.lstrip("/")).as_uri()


def main() -> int:
    from playwright.sync_api import sync_playwright

    control = "--control" in sys.argv
    langs = LANGS
    for a in sys.argv:
        if a.startswith("--langs="):
            langs = [x for x in a.split("=", 1)[1].split(",") if x]

    rows, fails = [], 0
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-sandbox"])
        for lang in langs:
            ctx = br.new_context(viewport={"width": 320, "height": 640}, is_mobile=True,
                                 has_touch=True, device_scale_factor=2)
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url_for(lang), wait_until="load")
            pg.wait_for_timeout(700)
            pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            pg.wait_for_timeout(1200)
            pg.evaluate("window.scrollTo(0, 0)")
            pg.wait_for_timeout(300)
            if control:
                pg.evaluate("""() => { const d = document.createElement('div');
                    d.style.cssText = 'position:absolute;left:0;top:0;width:600px;height:2px';
                    document.body.appendChild(d); }""")
                pg.wait_for_timeout(150)
            pr = pg.evaluate(PROBE, WIDTH)
            pr["lang"] = lang
            pr["jsErrors"] = errs
            wide = pr["docW"] > pr["want"] + 1 or pr["bodyW"] > pr["want"] + 1
            bad = []
            if wide:
                bad.append("H-OVERFLOW")
            if pr["clipCount"]:
                bad.append("TEXT-CLIPPED")
            if pr["smallCount"]:
                bad.append("TAP-SMALL")
            if errs:
                bad.append("JS-ERROR")
            pr["bad"] = bad
            if bad:
                fails += 1
            rows.append(pr)
            print(f"{'FAIL' if bad else 'OK  '} {lang}: doc={pr['docW']} vw={pr['vw']} "
                  f"off={pr['offCount']} carousel={pr['carouselCount']} "
                  f"clip={pr['clipCount']} tapSmall={pr['smallCount']} "
                  f"{','.join(bad)}")
            if bad:
                for k in ("off", "clip", "small"):
                    for it in pr[k][:4]:
                        print("      ", json.dumps(it, ensure_ascii=False))
            ctx.close()
        br.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"viewport": 320, "control": control, "rows": rows}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    checks = len(rows) * 3
    print(f"CHECKS: {checks}, FAILED: {fails}")
    print(f"evidence: {OUT}")
    if control:
        caught = any("H-OVERFLOW" in r["bad"] for r in rows)
        print("КОНТРОЛЬ:", "ПОЙМАЛ" if caught else "ПРОСМОТРЕЛ")
        return 0 if caught else 1
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
