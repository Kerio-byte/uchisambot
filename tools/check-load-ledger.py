#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-load-ledger.py — что браузер попросил и что ему ответили (01.11.2026).

Повод (01.11.2026, двадцать седьмой блок). Сорок приборов смотрят на дерево файлов,
шесть — на браузер, и все они читают страницу по `file://` (проверено: `url_for()`
в check-text-zoom строит `Path.as_uri()`). У `file://` нет кодов ответа: картинка,
которой нет, просто не появляется, и ни один прибор об этом не говорит. Единственное
место, где сайт спрашивают «по адресу», — `publish-tree.py --verify-served`, и оно
берёт список адресов РЕГУЛЯРКОЙ по разметке: `<img src>`, `<a href>`, `<link href>`.
Всё, что грузит CSS (`url()`), `srcset`, `poster`, JS и сам браузер (favicon), в этот
список не попадает — то есть «публикация проверена» означало «проверены адреса,
которые мы сами придумали», а не «проверено то, что браузер попросит».

Более того, до сих пор никто не читал журнал браузера. `pageerror` собирают три
прибора, и только как довесок к геометрии: упавший на загрузке скрипт оставил бы
форму и переключатель языка мёртвыми, а страница при этом выглядела бы целой.

Что меряется. Десять страниц (9 языков + privacy + terms + 404) отдаются локальным
HTTP-сервером из ОПУБЛИКОВАННОГО дерева (`tools/publish-tree.py --stage`), и каждая
открывается браузером в мобильном окне 420 px. Слушаются три канала:
  STATUS     каждый ответ; 4xx/5xx — находка (`BAD-STATUS`);
  FAILED     запрос, который не дошёл (`REQUEST-FAILED`); перед вердиктом адрес
             перепрашивается напрямую — если он отвечает 200, это обрыв навигации,
             а не дефект сайта, и он не красит отчёт (ложный красный тоже ложь);
  CONSOLE    сообщения типа error и необработанные исключения страницы
             (`CONSOLE-ERROR`, `JS-ERROR`).
Плюс страховка от слепоты: меньше 3 запросов на страницу — `BLIND` (страница не
открылась, «чисто» было бы ложью), и глобально: если за весь прогон браузер не
попросил ни одного шрифта и меньше десятка картинок, прибор не читал страницу.

Ложный зелёный исключён контролем (`--control`, копия опубликованного дерева):
  чистая копия обязана быть ЗЕЛЁНОЙ, затем четыре мутанта, каждый своей строкой:
    M1 css   — `background-image:url(img/missing-m1.png)` -> BAD-STATUS 404
    M2 js    — `throw new Error(...)` -> JS-ERROR
    M3 log   — `console.error(...)` -> CONSOLE-ERROR
    M4 set   — `<img srcset="img/missing-m4.png 2x">` -> BAD-STATUS 404
  М1 и М4 — ровно тот класс, которого не видит регулярка по разметке.

Запуск:
  python3 tools/check-load-ledger.py              # 12 страниц из опубликованного дерева
  python3 tools/check-load-ledger.py --root DIR   # из другого дерева
  python3 tools/check-load-ledger.py --control    # доказательство прибора
Код возврата: 0 — чисто, 1 — находки или мутант не покраснел, 3 — нет браузера.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["/", "/ru/", "/es/", "/pt/", "/hi/", "/id/", "/tr/", "/vi/", "/uk/",
         "/privacy.html", "/terms.html", "/404.html"]
HOST = "127.0.0.1"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(dest: Path):
    handler = functools.partial(Quiet, directory=str(dest))
    srv = socketserver.ThreadingTCPServer((HOST, 0), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://{HOST}:{srv.server_address[1]}"


def direct_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status == 200
    except Exception:
        return False


def probe(browser, url: str) -> dict:
    ctx = browser.new_context(viewport={"width": 420, "height": 900}, is_mobile=True,
                              has_touch=True, device_scale_factor=2)
    pg = ctx.new_page()
    bad: list[str] = []
    types: dict[str, int] = {}
    reqs = [0]
    js_errs: list[str] = []
    console: list[str] = []

    def on_resp(r):
        reqs[0] += 1
        rt = r.request.resource_type
        types[rt] = types.get(rt, 0) + 1
        if r.status >= 400:
            bad.append(f"BAD-STATUS {r.status} {r.request.resource_type} {r.url}")

    def on_fail(r):
        reqs[0] += 1
        types[r.resource_type] = types.get(r.resource_type, 0) + 1
        if direct_ok(r.url):
            return          # адрес живой: обрыв навигации, не дефект сайта
        bad.append(f"REQUEST-FAILED {r.resource_type} {r.url} {r.failure}")

    def on_console(m):
        if m.type == "error":
            console.append(m.text)

    pg.on("response", on_resp)
    pg.on("requestfailed", on_fail)
    pg.on("console", on_console)
    pg.on("pageerror", lambda e: js_errs.append(str(e)))

    try:
        pg.goto(url, wait_until="load", timeout=30000)
        pg.wait_for_timeout(500)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")   # догрузить ленивое
        pg.wait_for_timeout(900)
        pg.evaluate("window.scrollTo(0, 0)")
        pg.wait_for_timeout(300)
        title = pg.title()
    except Exception as e:
        title = ""
        bad.append(f"NOT-OPENED {e}")
    ctx.close()

    for m in console:
        bad.append(f"CONSOLE-ERROR {m[:160]}")
    for e in js_errs:
        bad.append(f"JS-ERROR {e[:160]}")
    if reqs[0] < 3:
        bad.append(f"BLIND requests={reqs[0]}")
    return dict(url=url, title=title, reqs=reqs[0], types=types, bad=bad)


def run(browser, base: str, pages: list[str], label: str = "") -> tuple[list[dict], int]:
    rows, fails = [], 0
    for p in pages:
        pr = probe(browser, base + p)
        pr["bad"] = sorted(set(pr["bad"]))
        if pr["bad"]:
            fails += 1
        rows.append(pr)
        t = pr["types"]
        print(f"{'FAIL' if pr['bad'] else 'OK  '} {label}{p:15s} запросов={pr['reqs']:3d} "
              f"img={t.get('image',0):2d} шрифт={t.get('font',0)} скрипт={t.get('script',0)} "
              f"стиль={t.get('stylesheet',0)} находок={len(pr['bad'])}")
        for b in pr["bad"][:6]:
            print("       " + b)
    return rows, fails


def stage_published(dest: Path) -> bool:
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "publish-tree.py"),
                        "--stage", str(dest)], capture_output=True, text=True, timeout=300)
    return p.returncode == 0 and dest.exists()


def mutation(src: Path, dst: Path, kind: str) -> None:
    shutil.copytree(src, dst)
    page = dst / "index.html"
    html = page.read_text(encoding="utf-8")
    if kind == "css":
        add = '<style>body{background-image:url(img/missing-m1.png)}</style>'
    elif kind == "js":
        add = '<script>throw new Error("mutant-m2")</script>'
    elif kind == "log":
        add = '<script>console.error("mutant-m3")</script>'
    elif kind == "set":
        add = '<img src="img/demo-poster-ru.webp" srcset="img/missing-m4.png 2x" alt="" width="8" height="8">'
    else:
        raise SystemExit("неизвестный мутант " + kind)
    if "</body>" not in html:
        raise SystemExit("нет </body> — мутант не поставить")
    page.write_text(html.replace("</body>", add + "</body>", 1), encoding="utf-8")


def control(browser, work: Path) -> int:
    """Чистая копия зелёная, четыре мутанта пойманы каждый своим сообщением."""
    from playwright.sync_api import sync_playwright  # noqa: F401 — только загрузка

    fails = 0
    clean = work / "clean"
    shutil.copytree(work / "pub", clean)
    srv, base = serve(clean)
    rows, bad = run(browser, base, ["/"], "чистая ")
    srv.shutdown()
    if bad:
        print("КОНТРОЛЬ СЛОМАН: чистая копия не зелёная — красное ниже ничего не доказывает")
        for r in rows:
            for b in r["bad"]:
                print("   " + b)
        return 1
    print("чистая копия зелёная: прибор не краснеет от воздуха")

    want = {"css": "BAD-STATUS 404", "js": "JS-ERROR", "log": "CONSOLE-ERROR", "set": "BAD-STATUS 404"}
    caught = 0
    for kind, needle in want.items():
        dst = work / f"m-{kind}"
        mutation(work / "pub", dst, kind)
        srv, base = serve(dst)
        rows, _ = run(browser, base, ["/"], f"мутант {kind:4s} ")
        srv.shutdown()
        hit = [b for r in rows for b in r["bad"] if needle in b]
        if hit:
            caught += 1
            print(f"   поймал: {hit[0][:120]}")
        else:
            fails += 1
            print(f"   НЕ ПОЙМАЛ {kind} — прибор слеп к этому классу")
    print(f"МУТАНТЫ {caught}/{len(want)}")
    return 0 if (fails == 0 and caught == len(want)) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="журнал загрузки: что браузер попросил и что ответили")
    ap.add_argument("--root", default="", help="отдать это дерево (по умолчанию — опубликованное)")
    ap.add_argument("--base", default="", help="мерить живой сайт по этому адресу, без сервера")
    ap.add_argument("--control", action="store_true", help="доказать, что прибор умеет краснеть")
    ap.add_argument("--pages", default="", help="через запятую, если нужны не все")
    a = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print(f"ПРОПУСК: нет браузера ({e})")
        return 3

    work = Path(tempfile.mkdtemp(prefix="load-ledger-"))
    try:
        if a.control:
            if not stage_published(work / "pub"):
                print("ПРОПУСК: не удалось разложить опубликованное дерево")
                return 3
            with sync_playwright() as p:
                br = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
                rc = control(br, work)
                br.close()
            return rc

        tree: Path | None = None
        srv = None
        base = ""
        if a.base:
            base = a.base.rstrip("/")
        elif a.root:
            tree = Path(a.root).resolve()
        else:
            tree = work / "pub"
            if not stage_published(tree):
                print("ПРОПУСК: не удалось разложить опубликованное дерево")
                return 3
        pages = [x.strip() for x in a.pages.split(",") if x.strip()] or PAGES
        if srv is None and not a.base:
            assert tree is not None
            srv, base = serve(tree)
        try:
            with sync_playwright() as p:
                br = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
                rows, fails = run(br, base, pages)
                br.close()
        finally:
            if srv is not None:
                srv.shutdown()

        total = sum(r["reqs"] for r in rows)
        imgs = sum(r["types"].get("image", 0) for r in rows)
        fonts = sum(r["types"].get("font", 0) for r in rows)
        print(f"ИТОГО: страниц {len(rows)}, запросов {total}, картинок {imgs}, шрифтов {fonts}, "
              f"страниц с находками {fails}")
        if fonts == 0 or imgs < 10:
            print("INSTRUMENT BLIND: браузер не просил картинок/шрифтов — он читал не страницу")
            return 1
        if fails:
            return 1
        print("ЖУРНАЛ ЧИСТ: каждый запрос страницы получил ответ, ошибок консоли и падений JS нет")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
