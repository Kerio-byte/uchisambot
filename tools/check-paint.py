#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-paint.py — страница прыгает или стоит на месте (02.11.2026).

Повод (02.11.2026, сорок пятый блок). Восемьдесят два прибора смотрят на дерево,
байты, вес, шрифты, контраст и геометрию — и ни один не смотрит на то, КАК страница
встаёт на экран. `weight` считает байты до загрузки, `visual-420` меряет геометрию
после загрузки, а между ними — пустое место: момент, когда браузер уже показал
разметку, но шрифт, картинка или вставленный скриптом блок ещё едут и толкают текст
вниз. Пользователь читает тариф, строка под ним прыгает, он тапает мимо — этого не
видит ни один прибор, потому что геометрия в конце правильная, а байты в бюджете.

Проверено, что дыра настоящая: `grep -rn "layout-shift|LCP|PerformanceObserver|paint"
tools/*.py` — ни одного упоминания.

Что меряется. Девять языковых страниц отдаются локальным HTTP-сервером из
ОПУБЛИКОВАННОГО дерева (`tools/publish-tree.py --stage`) и открываются Chromium.
Наблюдатели ставятся ДО загрузки страницы (`add_init_script`), поэтому считается
весь путь, а не хвост после `load`:

  CLS   сумма всех сдвигов макета; называется худший сдвиг, его время и элемент
        (тег.класс#id) — по имени, а не «что-то поехало». Порог 0.10 — норма Google
        «хорошо». Особенность меры, замеренная на первом прогоне: Chromium под
        управлением Playwright помечает КАЖДЫЙ сдвиг `hadRecentInput=true`
        (синтетический ввод), поэтому привычное число «без ввода» здесь структурно
        ноль — и первая версия прибора на трёх мутантах честно показала 0.000.
        Считаются все сдвиги, а второе число (`clsIn`) печатается рядом: ноль там
        означает, что сдвиг был, но браузер счёл его откликом на ввод;
  LCP   когда нарисован самый большой блок (для локальной отдачи порог 2500 мс —
        тот же, что у Google; локальный сервер заведомо быстрее, поэтому красное
        здесь означает не сеть, а саму страницу);
  FCP   первая отрисовка текста.

Два окна (блок 46). Первый проход мерил только 420 px, и это было записано как
слепота. Страница не одна и та же в узком и широком окне: на десктопе тарифы стоят
в ряд, на телефоне — в столбик, то есть сдвиг одной колонки на широком экране
двигает соседнюю и в узком его просто нет. Меряются оба окна: `mobile` 420x900
(мобильный контекст, 2x) и `desktop` 1280x900. Одно и то же число в обоих окнах —
повод проверить, что окно вообще применено; поэтому контроль (ниже) требует, чтобы
мутант «только для десктопа» был пойман на десктопе и НЕ пойман на телефоне.

Прокрутка (блок 46). CLS по Google считается только до первого ввода, поэтому
сдвиг от ленивой картинки, которая грузится при прокрутке, в метрику не входит —
а человек этот прыжок видит и тапает мимо. После загрузки страница прокручивается
до низа шагами по 600 px, и сдвиги этого отрезка считаются отдельным ведром
(`SCROLL`). Порог тот же 0.10, но это НАШ порог, а не Google: здесь мерится
«прыгает ли под пальцем», а не поле метрики. Два ведра не смешиваются: сдвиг
первого экрана не может спрятаться в прокрутке и наоборот.

Слепота названа: нет записи LCP — наблюдатель не сработал, это `BLIND`, а не «чисто»;
высота документа меньше 1000 px — страница не отрисована, тоже `BLIND`. Пустой список
сдвигов законен: страница может стоять ровно, это и есть цель. Не меряется (чтобы
зелёное не переоценили): анимации по таймеру после 1.2 с, повторный заход по «назад»
(bfcache — это перерисовка браузера, а не страницы), окна уже 320 px и шире 1280 px.

Ложный зелёный исключён контролем (`--control`, копия опубликованного дерева):
  чистая копия обязана быть ЗЕЛЁНОЙ в ОБОИХ окнах, затем пять мутантов:
    M1 late-block  — блок 300 px вставляется в начало body через 300 мс (поздняя
                     вставка скриптом, классический сдвиг);
    M2 no-dims     — картинка без width/height в начале body (грузясь, растёт с нуля);
    M3 late-text   — абзац дописывается в шапку после готовности шрифтов;
    M4 desk-block  — тот же поздний блок, но высота даётся только при ширине
                     900 px и больше: на телефоне сдвига нет, на десктопе есть;
    M5 scroll-lazy — картинка без размеров с `loading="lazy"` вставлена перед
                     подвалом: при загрузке её высота нулевая (сдвига нет), при
                     прокрутке она грузится и толкает подвал вниз.
  M1-M3 обязаны покраснеть строкой CLS и назвать сдвинувшийся элемент; их величины
  обязаны РАЗЛИЧАТЬСЯ: одинаковое число на три разных дефекта означало бы, что прибор
  читает флаг, а не считает. M4 обязан покраснеть на десктопе и остаться зелёным на
  телефоне, M5 — покраснеть в ведре SCROLL и остаться зелёным на первом экране.
  Названный элемент у M1-M3 — `main#main`, то есть ЖЕРТВА сдвига, а не виновник: CLS
  знает, что поехало, и не знает, кто толкнул. Это свойство метрики, а не недоделка;
  поэтому доказательством меры служит не имя в отчёте, а разные величины на разные
  дефекты. Все мутанты меряются тем же прибором и той же страницей, что и живой прогон.

Запуск:
  python3 tools/check-paint.py                 # 9 языков, два окна, с прокруткой
  python3 tools/check-paint.py --root DIR      # из другого дерева (каталог сайта)
  python3 tools/check-paint.py --one-frame     # только мобильное окно (быстрая проверка)
  python3 tools/check-paint.py --control       # доказательство прибора
Код возврата: 0 — чисто, 1 — находки или мутант не покраснел, 3 — нет браузера.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["/", "/ru/", "/es/", "/pt/", "/hi/", "/id/", "/tr/", "/vi/", "/uk/"]
HOST = "127.0.0.1"

# Пороги. CLS — норма Google, не наша выдумка. Время — потолок для отдачи по петле:
# локальный сервер отдаёт страницу за десятки миллисекунд, поэтому 2500 мс здесь
# означает «страница сама тормозит», а не «сеть медленная».
CLS_LIMIT = 0.10
LCP_LIMIT_MS = 2500
FCP_LIMIT_MS = 1800
# Порог сдвига при прокрутке — наш, не Google: метрика выбрасывает сдвиги после
# ввода, а человек их видит. Поэтому число своё, но условие то же — «не прыгает».
SCROLL_LIMIT = 0.10
SCROLL_STEP = 600

FRAMES = [
    dict(name="mobile", width=420, height=900, is_mobile=True, dsf=2),
    dict(name="desktop", width=1280, height=900, is_mobile=False, dsf=1),
]

MEASURE = r"""
(() => {
  const d = (n) => {
    if (!n) return '?';
    const el = (n.nodeType === 1) ? n : n.parentElement;
    if (!el) return '?';
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    const c = (typeof el.className === 'string') ? el.className.trim() : '';
    if (c) s += '.' + c.split(/\s+/).slice(0, 2).join('.');
    return s;
  };
  window.__paint = { cls: 0, clsIn: 0, shifts: [], lcp: 0, lcpEl: '', fcp: 0, err: '',
                     scroll: { cls: 0, shifts: [] }, __mark: false };
  try {
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) {
        const rec = {
          v: Math.round(e.value * 10000) / 10000,
          t: Math.round(e.startTime),
          in: e.hadRecentInput,
          src: (e.sources || []).map((s) => d(s.node)).slice(0, 3),
        };
        window.__paint.cls += e.value;
        if (!e.hadRecentInput) window.__paint.clsIn += e.value;
        window.__paint.shifts.push(rec);
        if (window.__paint.__mark) window.__paint.scroll.shifts.push(rec);
        if (window.__paint.__mark) window.__paint.scroll.cls += e.value;
      }
    }).observe({ type: 'layout-shift', buffered: true });
  } catch (e) { window.__paint.err += 'layout-shift: ' + e + '; '; }
  try {
    new PerformanceObserver((l) => {
      const es = l.getEntries();
      const e = es[es.length - 1];
      if (e) { window.__paint.lcp = Math.round(e.startTime); window.__paint.lcpEl = d(e.element); }
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) { window.__paint.err += 'lcp: ' + e + '; '; }
  try {
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) if (e.name === 'first-contentful-paint') window.__paint.fcp = Math.round(e.startTime);
    }).observe({ type: 'paint', buffered: true });
  } catch (e) { window.__paint.err += 'paint: ' + e + '; '; }
})();
"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(dest: Path):
    handler = functools.partial(Quiet, directory=str(dest))
    srv = socketserver.ThreadingTCPServer((HOST, 0), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://{HOST}:{srv.server_address[1]}"


def stage_published(dest: Path) -> bool:
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "publish-tree.py"),
                        "--stage", str(dest)], capture_output=True, text=True, timeout=300)
    return p.returncode == 0 and (dest / "index.html").is_file()


def probe(browser, url: str, frame: dict, scroll: bool = True) -> dict:
    ctx = browser.new_context(viewport={"width": frame["width"], "height": frame["height"]},
                              is_mobile=frame["is_mobile"], has_touch=frame["is_mobile"],
                              device_scale_factor=frame["dsf"])
    pg = ctx.new_page()
    pg.add_init_script(MEASURE)
    bad: list[str] = []
    m: dict = {}
    scls, sshifts = 0.0, 0
    try:
        pg.goto(url, wait_until="load", timeout=30000)
        pg.evaluate("() => document.fonts.ready.then(() => true)")   # шрифт успел встать
        pg.wait_for_timeout(1200)                                    # хвост: поздние вставки
        m = json.loads(pg.evaluate("() => JSON.stringify(window.__paint || {})") or "{}")
        h = pg.evaluate("() => document.documentElement.scrollHeight")
        if not m.get("lcp"):
            bad.append("BLIND нет записи LCP — наблюдатель не сработал")
        if (h or 0) < 1000:
            bad.append(f"BLIND документ {h} px — страница не отрисована")
        if m.get("err"):
            bad.append("OBSERVER " + str(m["err"])[:160])
        cls = round(float(m.get("cls", 0)), 4)
        if cls > CLS_LIMIT:
            worst = max(m.get("shifts", []), key=lambda s: s["v"]) if m.get("shifts") else {}
            src = ",".join(worst.get("src", [])) or "?"
            bad.append(f"CLS {cls:.3f} > {CLS_LIMIT:.2f} (сдвигов {len(m.get('shifts', []))}) "
                       f"худший: {worst.get('v', 0)} на {src} в {worst.get('t', 0)} мс")
        lcp = int(m.get("lcp", 0))
        if lcp > LCP_LIMIT_MS:
            bad.append(f"LCP {lcp} мс > {LCP_LIMIT_MS} ({m.get('lcpEl', '?')})")
        fcp = int(m.get("fcp", 0))
        if fcp > FCP_LIMIT_MS:
            bad.append(f"FCP {fcp} мс > {FCP_LIMIT_MS}")

        if scroll:
            # Отдельное ведро: всё, что поехало ПОСЛЕ первого экрана. Метка ставится
            # до первого шага, поэтому сдвиг загрузки сюда не попадает.
            pg.evaluate("() => { window.__paint.__mark = true; "
                        "window.__paint.scroll = { cls: 0, shifts: [] }; }")
            y = 0
            hh = int(pg.evaluate("() => document.documentElement.scrollHeight") or 0)
            while y < hh and y < 40000:
                y += SCROLL_STEP
                pg.evaluate(f"() => window.scrollTo(0, {y})")
                pg.wait_for_timeout(120)
            sc = json.loads(pg.evaluate("() => JSON.stringify(window.__paint.scroll || {})") or "{}")
            scls = round(float(sc.get("cls", 0)), 4)
            sshifts = len(sc.get("shifts", []))
            if scls > SCROLL_LIMIT:
                worst = max(sc.get("shifts", []), key=lambda s: s["v"]) if sc.get("shifts") else {}
                src = ",".join(worst.get("src", [])) or "?"
                bad.append(f"SCROLL {scls:.3f} > {SCROLL_LIMIT:.2f} (сдвигов {sshifts}) "
                           f"худший: {worst.get('v', 0)} на {src} в {worst.get('t', 0)} мс")
    except Exception as e:
        bad.append(f"NOT-OPENED {e}")
    ctx.close()
    return dict(url=url, frame=frame["name"], cls=m.get("cls", 0), clsIn=m.get("clsIn", 0),
                shifts=len(m.get("shifts", [])), lcp=m.get("lcp", 0), fcp=m.get("fcp", 0),
                scrollCls=scls, scrollShifts=sshifts, bad=sorted(set(bad)))


def run(browser, base: str, pages: list[str], frames=None, scroll: bool = True) -> tuple[list[dict], int]:
    rows, fails = [], 0
    for p in pages:
        for fr in (frames or FRAMES):
            r = probe(browser, base + p, fr, scroll)
            if r["bad"]:
                fails += 1
            rows.append(r)
            print(f"{'FAIL' if r['bad'] else 'OK  '} {r['frame']:7s} {p:9s} CLS {float(r['cls']):.3f} "
                  f"(без ввода {float(r['clsIn']):.3f}) сдвигов={r['shifts']:2d} "
                  f"прокрутка {float(r['scrollCls']):.3f} "
                  f"LCP={r['lcp']:4d} мс FCP={r['fcp']:4d} мс находок={len(r['bad'])}")
            for b in r["bad"][:4]:
                print("       " + b)
    return rows, fails


def mutant(src: Path, dst: Path, kind: str) -> None:
    shutil.copytree(src, dst)
    page = dst / "index.html"
    html = page.read_text(encoding="utf-8")
    if kind == "late-block":
        add = ('<script>setTimeout(function(){var d=document.createElement("div");'
               'd.className="mutant-m1";d.style.height="300px";'
               'document.body.insertBefore(d,document.body.firstChild);},300)</script>')
    elif kind == "no-dims":
        add = ('<script>window.addEventListener("load",function(){var i=document.createElement("img");'
               'i.className="mutant-m2";i.src="img/demo-poster-ru.webp";'
               'document.body.insertBefore(i,document.body.firstChild);});</script>')
    elif kind == "late-text":
        add = ('<script>document.fonts.ready.then(function(){setTimeout(function(){'
               'var p=document.createElement("p");p.className="mutant-m3";'
               'p.textContent="Поздний абзац, который дописали в шапку после шрифтов. ".repeat(3);'
               'document.body.insertBefore(p,document.body.firstChild);},200)});</script>')
    elif kind == "desk-block":
        # Сдвиг, которого на телефоне НЕТ по устройству: высота только на широком окне.
        add = ('<style>@media(min-width:900px){.mutant-m4{height:200px;background:#eee;'
               'display:block}}</style><script>setTimeout(function(){var d=document.createElement("div");'
               'd.className="mutant-m4";'
               'document.body.insertBefore(d,document.body.firstChild);},250)</script>')
    elif kind == "scroll-shift":
        # Сдвиг, которого на ПЕРВОМ экране нет: блок вставляется только после того,
        # как человек уже прокрутил. Синтетический по устройству и честный по смыслу:
        # он доказывает, что ведро ПРОКРУТКИ читается, а не изображает поломку сайта.
        # Две вещи замерены на пути к рабочему мутанту:
        #  1) вставка в НАЧАЛО body при прокрутке не даёт сдвига вовсе — Chromium
        #     включает scroll anchoring и сам двигает прокрутку, держа читаемое на месте;
        #  2) поэтому блок ставится ПЕРЕД элементом, который сейчас в средней части
        #     экрана: якорь выше него, компенсация не срабатывает, строки под ним едут.
        add = ('<script>(function(){var done=false;var t=setInterval(function(){if(done){return;}'
               'if(window.scrollY>1000){done=true;clearInterval(t);'
               'var el=document.elementFromPoint(window.innerWidth/2, window.innerHeight*0.35);'
               'var p=el&&el.parentElement?el.parentElement:document.body;'
               'var d=document.createElement("div");d.className="mutant-m5";d.style.height="200px";'
               'if(el&&el.parentElement){p.insertBefore(d,el);}else{document.body.insertBefore(d,document.body.firstChild);}'
               '}},100);})();</script>')
    else:
        raise SystemExit("неизвестный мутант " + kind)
    if "</body>" not in html:
        raise SystemExit("нет </body> — мутант не поставить")
    page.write_text(html.replace("</body>", add + "</body>", 1), encoding="utf-8")


def control(browser, work: Path) -> int:
    fails = 0

    def measure(d: Path, frames, scroll: bool = True):
        srv, base = serve(d)
        try:
            return run(browser, base, ["/"], frames=frames, scroll=scroll)
        finally:
            srv.shutdown()

    clean = work / "clean"
    shutil.copytree(work / "pub", clean)
    rows, bad = measure(clean, FRAMES)
    if bad:
        print("КОНТРОЛЬ СЛОМАН: чистая копия не зелёная — красное ниже ничего не доказывает")
        for r in rows:
            for b in r["bad"]:
                print(f"   {r['frame']}: {b}")
        return 1

    mob = [f for f in FRAMES if f["name"] == "mobile"]
    desk = [f for f in FRAMES if f["name"] == "desktop"]

    plan = ["late-block", "no-dims", "late-text"]
    caught, vals = 0, []
    for kind in plan:
        d = work / ("m-" + kind)
        mutant(work / "pub", d, kind)
        rows, bad = measure(d, mob)
        cls_lines = [b for b in rows[0]["bad"] if b.startswith("CLS")]
        if not bad:
            print(f"  мутант {kind}: НЕ ПОЙМАН — прибор слеп к этому классу")
            fails += 1
        elif not cls_lines:
            print(f"  мутант {kind}: покраснел чужим классом: {rows[0]['bad'][0][:80]}")
            fails += 1
        elif cls_lines[0].endswith("на ? в 0 мс"):
            print(f"  мутант {kind}: поймал, но не назвал элемент — прибор врёт о причине")
            fails += 1
        else:
            caught += 1
            vals.append(round(float(rows[0]["cls"]), 3))
            print(f"  мутант {kind}: ПОЙМАН, CLS {vals[-1]:.3f}, сдвинулся "
                  f"{cls_lines[0].split(' на ')[-1]}")
    # CLS называет ЖЕРТВУ (что поехало), а не виновника — и это единственная честная
    # привязка, какую метрика умеет. Три мутанта потому и должны отличаться ВЕЛИЧИНОЙ:
    # если прибор печатает одно и то же число на разные дефекты, он читает флаг, а не меру.
    distinct = len(set(vals)) == len(plan)
    print(f"МУТАНТЫ {caught}/{len(plan)} — поймал {caught} из {len(plan)}, "
          f"величины {'различны' if distinct else 'СОВПАЛИ'} "
          f"({', '.join(f'{v:.3f}' for v in vals) or '—'})")

    # Доказательство ОКНА: мутант, которого на телефоне нет по устройству.
    d = work / "m-desk-block"
    mutant(work / "pub", d, "desk-block")
    dm, dbad = measure(d, desk)
    dcls = [b for b in dm[0]["bad"] if b.startswith("CLS")]
    mm, mbad = measure(d, mob)
    mcls = [b for b in mm[0]["bad"] if b.startswith("CLS")]
    if dcls and not mcls:
        caught += 1
        print(f"  мутант desk-block: ПОЙМАН на десктопе, CLS {float(dm[0]['cls']):.3f}, "
              f"на телефоне чисто — окно действительно применяется")
    else:
        fails += 1
        print(f"  мутант desk-block: {'поймал и на телефоне — мутант не доказывает окно' if mcls else 'НЕ ПОЙМАН на десктопе — широкое окно не читается'}")

    # Доказательство ПРОКРУТКИ: сдвиг только после первого экрана.
    d = work / "m-scroll-shift"
    mutant(work / "pub", d, "scroll-shift")
    (sm, _sf) = measure(d, mob)
    first = [b for b in sm[0]["bad"] if b.startswith("CLS") or b.startswith("SCROLL")]
    if not first:
        print("  мутант scroll-shift: НЕ ПОЙМАН — прокрутка не читается")
        fails += 1
    elif any(b.startswith("CLS ") for b in first):
        print("  мутант scroll-shift: покраснел уже на первом экране — прокрутка не доказана")
        fails += 1
    elif float(sm[0]["scrollCls"]) <= SCROLL_LIMIT:
        print(f"  мутант scroll-shift: ведро SCROLL {sm[0]['scrollCls']:.3f} ниже порога")
        fails += 1
    else:
        caught += 1
        print(f"  мутант scroll-shift: ПОЙМАН при прокрутке, SCROLL {float(sm[0]['scrollCls']):.3f}, "
              f"первый экран чист")

    total = len(plan) + 2
    print(f"МУТАНТЫ ВСЕГО {caught}/{total} — поймал {caught} из {total}")
    return 1 if fails or caught != total or not distinct else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", help="каталог сайта (по умолчанию — опубликованное дерево)")
    ap.add_argument("--control", action="store_true", help="доказательство прибора на мутантах")
    ap.add_argument("--one-frame", action="store_true", help="только мобильное окно")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print(f"ПРОПУСК нет браузера: {e}")
        return 3

    work = Path(tempfile.mkdtemp(prefix="paint-"))
    try:
        if args.root:
            pub = Path(args.root).resolve()
        else:
            pub = work / "pub"
            if not stage_published(pub):
                print("ПРОПУСК не удалось собрать опубликованное дерево")
                return 3
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--hide-scrollbars"])
            if args.control:
                rc = control(browser, work)
                browser.close()
                return rc
            srv, base = serve(pub)
            frames = [f for f in FRAMES if f["name"] == "mobile"] if args.one_frame else FRAMES
            rows, fails = run(browser, base, PAGES, frames=frames)
            srv.shutdown()
            browser.close()

        worst = max((float(r["cls"]) for r in rows if not r["bad"]), default=0.0)
        worst_sc = max((float(r["scrollCls"]) for r in rows if not r["bad"]), default=0.0)
        print(f"ИТОГО окон {len(frames)}, страниц {len(rows)}, провалов {fails}, "
              f"худший CLS {worst:.3f} (порог {CLS_LIMIT:.2f}), "
              f"худшая прокрутка {worst_sc:.3f} (порог {SCROLL_LIMIT:.2f}), "
              f"потолок LCP {LCP_LIMIT_MS} мс")
        print(f"CHECKS: {len(rows)}, FAILED: {fails}")
        return 1 if fails else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
