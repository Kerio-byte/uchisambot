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

Граница 360 (02.11.2026). В стилях страниц девятнадцать блоков `@media(max-width:360px)`,
а приборы дерева мерили 320 и 420 — саму границу не видел никто, ни с одной стороны.
Это тот же класс, что «ноль дефектов в двух окнах и поломка между ними»: ровно на 360
правила включаются, на 361 выключаются, и обе стороны обязаны быть чистыми. Ширина стала
параметром (`--width=360`), чтобы класс закрывался замером, а не рассуждением.

Запуск: python3 tools/probe-narrow.py [--control] [--langs en,ru,...] [--width=320] [--set=legal]
Пишет evidence/narrow-<дата>.json (при нестандартной ширине — narrow-w<ширина>-<дата>.json,
для --set=legal — narrow-legal[-w<ширина>][-control]-<дата>.json) и печатает итог.
Код 0 = чисто, 1 = находки.

Страницы вне девяти языков (02.11.2026, блок 60). `--set=legal` гоняет те же три клаузы
по privacy.html, terms.html и 404.html: до этого их мерил только a11y — статикой и одним
окном 420. Футер лендинга ведёт на privacy и terms с каждого языка, то есть узкий телефон
открывает их так же часто, как саму страницу, а вёрстка там своя: длинные перечни, адреса
почты, таблицы. Прибор тот же — второй такой же прибор был бы вторым источником правды.
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
# Страницы вне девяти языков. Их видит каждый посетитель с футера страницы, но узкая
# проба ходила только по языкам: у юридических страниц своя вёрстка (длинные перечни,
# адреса, таблицы), и ломается она иначе, чем лендинг.
LEGAL = [("privacy", "/privacy.html", "Privacy Policy", 800),
         ("terms", "/terms.html", "Terms of Service", 800),
         ("404", "/404.html", "Page not found", 40)]
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
    identity_control = "--identity-control" in sys.argv
    langs = LANGS
    pageset = "langs"
    width = WIDTH
    for a in sys.argv:
        if a.startswith("--langs="):
            langs = [x for x in a.split("=", 1)[1].split(",") if x]
        elif a.startswith("--width="):
            width = int(a.split("=", 1)[1])
        elif a.startswith("--set="):
            pageset = a.split("=", 1)[1]

    # 30.10.2026 (проверка блока 53). Докстринг обещал отдельный файл для контроля, а код писал
    # оба прогона в один path: контрольный прогон затирал ЧИСТОЕ доказательство (narrow-<дата>.json
    # после --control содержал vw=600 и H-OVERFLOW). Ровно та же ошибка, что у юридической батареи.
    # 02.11.2026: ширина стала параметром, и имя файла обязано нести её — иначе замер на 360
    # затирал бы доказательство замера на 320. Та же ошибка, что выше, на шаг дальше.
    global OUT
    # 02.11.2026 (блок 60). Страницы вне девяти языков — privacy, terms, 404 — не мерил
    # ни один узкий прибор дерева: проба ходила только по девяти языкам, а a11y смотрел
    # эти три страницы статикой и одним окном 420. Имя файла доказательства собирается
    # из частей ОДИН раз, потому что правка по одному суффиксу уже дважды затирала чужое
    # доказательство (блок 53 — контроль поверх чистого, блок 59 — 360 поверх 320).
    if not os.environ.get("LANDING_OUT"):
        stem = ["narrow-legal"] if pageset == "legal" else ["narrow"]
        # Порядок частей сохранён от прежнего кода (narrow-control-w360-…): имена уже
        # лежащих в evidence файлов и ссылки на них в README не должны поменяться.
        if control:
            stem.append("control")
        if identity_control:
            stem.append("identity")
        if width != WIDTH:
            stem.append(f"w{width}")
        OUT = OUT.with_name("-".join(stem) + f"-{date.today():%Y%m%d}.json")

    if pageset == "legal":
        rows_spec = LEGAL
        if identity_control:
            # Контроль канарейки: каждой странице подсовываем ЧУЖОЕ имя. Если канарейка
            # не покраснеет, зелёный прогон legal ничего не значит — он и на пустом
            # документе зелёный.
            rows_spec = [(n, p, LEGAL[(i + 1) % len(LEGAL)][2], f)
                         for i, (n, p, _, f) in enumerate(LEGAL)]
        targets = [(name, BASE + path if BASE else (ROOT / path.lstrip("/")).as_uri(), needle, floor)
                   for name, path, needle, floor in rows_spec]
    else:
        targets = [(lang, url_for(lang), "", 0) for lang in langs]

    rows, fails = [], 0
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--no-sandbox"])
        for label, url, needle, floor in targets:
            ctx = br.new_context(viewport={"width": width, "height": 640}, is_mobile=True,
                                 has_touch=True, device_scale_factor=2)
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url, wait_until="load")
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
            pr = pg.evaluate(PROBE, width)
            pr["lang"] = label
            pr["page"] = url
            pr["width"] = width
            pr["jsErrors"] = errs
            # Канарейка личности страницы. Без неё «ноль находок» можно получить, сняв мерку
            # с пустого документа или с чужой страницы по неверному адресу: ни вылезания,
            # ни обрезки там нет по определению. Так уже случалось в дереве (публичная
            # поверхность ловила мёртвый сайт отдельной канарейкой).
            an = pg.evaluate("""() => ({title: document.title || '',
                                      text: (document.body.innerText || '').trim().length})""")
            pr["title"] = an["title"]
            pr["textLen"] = an["text"]
            wrong_page = bool(needle) and (needle.lower() not in an["title"].lower() or an["text"] < floor)
            wide = pr["docW"] > pr["want"] + 1 or pr["bodyW"] > pr["want"] + 1
            bad = []
            if wrong_page:
                bad.append("PAGE-IDENTITY")
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
            print(f"{'FAIL' if bad else 'OK  '} {label}: doc={pr['docW']} vw={pr['vw']} "
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
    OUT.write_text(json.dumps({"viewport": width, "control": control, "identityControl": identity_control,
                               "rows": rows}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    checks = len(rows) * (4 if pageset == "legal" else 3)
    print(f"CHECKS: {checks}, FAILED: {fails}")
    print(f"evidence: {OUT}")
    if identity_control:
        hit = sum(1 for r in rows if "PAGE-IDENTITY" in r["bad"])
        caught = bool(rows) and hit == len(rows)
        print(f"КОНТРОЛЬ ЛИЧНОСТИ: {'ПОЙМАЛ' if caught else 'ПРОСМОТРЕЛ'} поймал {hit} из {len(rows)}")
        return 0 if caught else 1
    if control:
        hit = sum(1 for r in rows if "H-OVERFLOW" in r["bad"])
        caught = hit > 0
        # Число пойманных печатается отдельным словом «поймал N из M»: раннер читает
        # именно эту форму (CAUGHT_RE), и без неё контроль из трёх страниц выглядел
        # как «поймал 1» — то есть будто проба открыла одну страницу из трёх.
        print(f"КОНТРОЛЬ: {'ПОЙМАЛ' if caught else 'ПРОСМОТРЕЛ'} поймал {hit} из {len(rows)}")
        return 0 if caught else 1
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
