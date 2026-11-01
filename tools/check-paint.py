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
ОПУБЛИКОВАННОГО дерева (`tools/publish-tree.py --stage`) и открываются Chromium в
мобильном окне 420 px. Наблюдатели ставятся ДО загрузки страницы (`add_init_script`),
поэтому считается весь путь, а не хвост после `load`:

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

Слепота названа: нет записи LCP — наблюдатель не сработал, это `BLIND`, а не «чисто»;
высота документа меньше 1000 px — страница не отрисована, тоже `BLIND`. Пустой список
сдвигов законен: страница может стоять ровно, это и есть цель.

Ложный зелёный исключён контролем (`--control`, копия опубликованного дерева):
  чистая копия обязана быть ЗЕЛЁНОЙ, затем три мутанта, каждый обязан покраснеть
  строкой CLS и назвать сдвинувшийся элемент:
    M1 late-block — блок 300 px вставляется в начало body через 300 мс (поздняя
                    вставка скриптом, классический сдвиг);
    M2 no-dims    — картинка без width/height в начале body (грузясь, растёт с нуля);
    M3 late-text  — абзац дописывается в шапку после готовности шрифтов.
  Замер контроля: чистый лист CLS 0.000; мутанты 0.310 / 0.930 / 0.106 — пойманы все
  три, и названный элемент везде `main#main`, то есть ЖЕРТВА сдвига, а не виновник.
  Это не недоделка, а свойство метрики: CLS знает, что поехало, и не знает, кто
  толкнул. Поэтому доказательством меры служит не имя мутанта в отчёте, а РАЗНЫЕ
  величины на разные дефекты: одинаковое число на три разных дефекта означало бы,
  что прибор читает флаг, а не считает.
  Все три меряются тем же прибором и той же страницей, что и живой прогон.

Запуск:
  python3 tools/check-paint.py                 # 9 языков из опубликованного дерева
  python3 tools/check-paint.py --root DIR      # из другого дерева (каталог сайта)
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
  window.__paint = { cls: 0, clsIn: 0, shifts: [], lcp: 0, lcpEl: '', fcp: 0, err: '' };
  try {
    new PerformanceObserver((l) => {
      for (const e of l.getEntries()) {
        window.__paint.cls += e.value;
        if (!e.hadRecentInput) window.__paint.clsIn += e.value;
        window.__paint.shifts.push({
          v: Math.round(e.value * 10000) / 10000,
          t: Math.round(e.startTime),
          in: e.hadRecentInput,
          src: (e.sources || []).map((s) => d(s.node)).slice(0, 3),
        });
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


def probe(browser, url: str) -> dict:
    ctx = browser.new_context(viewport={"width": 420, "height": 900}, is_mobile=True,
                              has_touch=True, device_scale_factor=2)
    pg = ctx.new_page()
    pg.add_init_script(MEASURE)
    bad: list[str] = []
    m: dict = {}
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
            bad.append("OBSERVER " + m["err"][:160])
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
    except Exception as e:
        bad.append(f"NOT-OPENED {e}")
    ctx.close()
    return dict(url=url, cls=m.get("cls", 0), clsIn=m.get("clsIn", 0),
                shifts=len(m.get("shifts", [])),
                lcp=m.get("lcp", 0), fcp=m.get("fcp", 0), bad=sorted(set(bad)))


def run(browser, base: str, pages: list[str]) -> tuple[list[dict], int]:
    rows, fails = [], 0
    for p in pages:
        r = probe(browser, base + p)
        if r["bad"]:
            fails += 1
        rows.append(r)
        print(f"{'FAIL' if r['bad'] else 'OK  '} {p:9s} CLS {float(r['cls']):.3f} "
              f"(без ввода {float(r['clsIn']):.3f}) сдвигов={r['shifts']:2d} "
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
    else:
        raise SystemExit("неизвестный мутант " + kind)
    if "</body>" not in html:
        raise SystemExit("нет </body> — мутант не поставить")
    page.write_text(html.replace("</body>", add + "</body>", 1), encoding="utf-8")


def control(browser, work: Path) -> int:
    fails = 0
    clean = work / "clean"
    shutil.copytree(work / "pub", clean)
    srv, base = serve(clean)
    rows, bad = run(browser, base, ["/"])
    srv.shutdown()
    if bad:
        print("КОНТРОЛЬ СЛОМАН: чистая копия не зелёная — красное ниже ничего не доказывает")
        for b in rows[0]["bad"]:
            print("   " + b)
        return 1

    plan = ["late-block", "no-dims", "late-text"]
    caught, vals = 0, []
    for kind in plan:
        d = work / ("m-" + kind)
        mutant(work / "pub", d, kind)
        srv, base = serve(d)
        rows, bad = run(browser, base, ["/"])
        srv.shutdown()
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
    return 1 if fails or caught != len(plan) or not distinct else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", help="каталог сайта (по умолчанию — опубликованное дерево)")
    ap.add_argument("--control", action="store_true", help="доказательство прибора на мутантах")
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
            rows, fails = run(browser, base, PAGES)
            srv.shutdown()
            browser.close()

        worst = max((float(r["cls"]) for r in rows if not r["bad"]), default=0.0)
        print(f"ИТОГО страниц {len(rows)}, провалов {fails}, худший CLS {worst:.3f} "
              f"(порог {CLS_LIMIT:.2f}), потолок LCP {LCP_LIMIT_MS} мс")
        print(f"CHECKS: {len(rows)}, FAILED: {fails}")
        return 1 if fails else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
