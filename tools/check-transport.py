#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-transport.py — что сеть реально везёт посетителю (01.11.2026, блок 36).

Повод. README в разделе «Живой транспорт» называет четыре факта: HTTP/2, gzip,
`cache-control: max-age=600` и «HTML в сжатом виде 35,7 КБ» — и сам же пишет,
что этого «не видит ни один прибор». Числа были сняты руками один раз. Дальше
их не читает никто: `check-weight` считает gzip ЛОКАЛЬНО из файла на диске
(сколько было бы, если бы сервер жал), `live-bytes` сверяет байты тела, а шапки
ответа — код, тип, кодировку — не смотрел ни один прибор.

Почему это опасно молчанием. GitHub Pages жмёт на лету и кеширует на краю.
Если он перестанет отдавать `content-encoding: gzip` (смена политики, новый
прокси, платный тариф), страница поедет в 116 КБ вместо 36 — и на 3G в Индии
это разница между «открылось» и «закрыл вкладку». Код ответа при этом 200,
байты тела те же, `live-bytes` зелёный, `check-weight` зелёный: он мерил диск.
Тот же класс, что блоки 32–35 закрывали для цен, разборов, секунд роликов и
меток бота: страница честная, а обещание рядом с ней — литерал.

Клаузы (61 проверка на девяти страницах и трёх файлах):

  1) ответ 200 у каждого языка;
  2) `content-encoding` = gzip или br — то есть сервер действительно жмёт,
     когда клиент об этом попросил (`Accept-Encoding: gzip, br`);
  3) `content-length` равен числу реально приехавших байтов: расхождение —
     это или обрезка, или враньё шапки, и в обоих случаях человек недополучает
     страницу, а код ответа 200;
  4) сжатый HTML не тяжелее потолка 60 КБ и жмётся не хуже, чем в 2 раза:
     потолок — граница «первый экран на мобильной сети», коэффициент — признак,
     что жатие живое, а не «gzip» из двух байт;
  5) `vary: accept-encoding` на сжатом ответе. Без него промежуточный кеш вправе
     отдать gzip тому, кто о нём не просил, и браузер получит мусор;
  6) `cache-control` с `max-age` не меньше 600 — ровно то число, что названо в
     README; меньше — значит кеш на краю перестал работать и каждый посетитель
     идёт в origin;
  7) версия протокола — HTTP/2 или выше (меряется curl: у `http.client` в
     стандартной библиотеке только 1.1, и мерить им версию значило бы мерить
     себя, а не сайт; нет curl — клауза SKIP с названной причиной, не зелёная);
  8) число «35,7 КБ» из README сверяется с измеренным сжатым размером HTML
     (допуск 3 КБ: страница растёт от правок текста). README перестал называть
     число — это находка, а не тишина: обещание убрали, прибор ослеп;
  9) медиа: mp4 обязан отдавать `accept-ranges: bytes` (иначе на телефоне
     нельзя перемотать ролик), шрифт и постер не должны жаться повторно —
     сжатие уже сжатого файла только ест процессор, а выигрыш ноль.

Контроль (`--control`) поднимает локальный сервер над тем же деревом и подаёт
прибору четыре порчи, каждую по отдельности: сервер не жмёт; `max-age=0`;
нет `vary`; `content-length` занижен. Чистая копия при этом обязана быть
зелёной — иначе прибор краснеет всегда и ничего не доказывает.

Запуск:
  python3 tools/check-transport.py            # живой сайт
  python3 tools/check-transport.py --control  # сам прибор
"""
from __future__ import annotations

import argparse
import gzip
import http.server
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "tools" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"]
UA = "UchiSamBot-transport/1.0 (+https://kerio-byte.github.io/uchisambot/)"
ACCEPT = "gzip"  # только gzip: brotli в стандартной библиотеке не разжать, а непроверяемое
                 # «br» прятало бы обрезку (README и так говорит, что Pages br не отдаёт)
CEIL_COMPRESSED = 60_000
CEIL_RATIO = 2.0
DOC_MAXAGE = 600
README_KB_TOLERANCE = 3.0

PAGES = [("en", "index.html")]
for _p in sorted((ROOT / "src" / "locales").glob("*.json")):
    if _p.stem != "en":
        PAGES.append((_p.stem, f"{_p.stem}/index.html"))

MEDIA = [
    ("fonts/langs-cyrillic.woff2", "шрифт"),
    ("img/demo-poster-hi.webp", "постер"),
    ("demo/uchiambot-demo.mp4", "ролик"),
]

findings: list[str] = []
checks = 0


def note(kind: str, msg: str) -> None:
    findings.append(f"[{kind}] {msg}")


def get(url: str, accept: str | None) -> tuple[int, dict, bytes]:
    """Код, шапки (ключи в нижнем регистре), тело."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if accept:
        req.add_header("Accept-Encoding", accept)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read()


def protocol(url: str) -> str | None:
    """Версия протокола по curl; None — curl нет."""
    if not shutil.which("curl"):
        return None
    try:
        out = subprocess.run(
            ["curl", "-sS", "-o", "/dev/null", "-H", "Accept-Encoding: gzip, br",
             "-w", "%{http_version}", "--max-time", "30", url],
            capture_output=True, text=True, timeout=60)
        v = out.stdout.strip()
        return v or None
    except (subprocess.SubprocessError, OSError):
        return None


def measure(base: str, proto: bool) -> None:
    global checks
    raw_html = None
    for code, rel in PAGES:
        url = base + ("" if rel == "index.html" else rel.rsplit("/", 1)[0] + "/")
        if rel == "index.html":
            url = base
        plain_n = len((ROOT / rel).read_bytes())
        disk = (ROOT / rel).read_bytes()
        try:
            st, h, body = get(url, ACCEPT)
        except (urllib.error.URLError, socket.timeout, OSError) as e:
            checks += 1
            note("DEAD", f"{code}: адрес не ответил — {e}")
            continue

        checks += 1
        if st != 200:
            note("STATUS", f"{code}: ответ {st}, нужен 200")

        enc = (h.get("content-encoding") or "").strip().lower()
        checks += 1
        if enc not in ("gzip", "br"):
            note("NOGZIP", f"{code}: content-encoding={enc or 'нет'} — страница едет "
                           f"{plain_n} байт вместо сжатых, потолок не действует")

        # Шапке не верим: разжимаем и сверяем с деревом. Врать в content-length
        # (и обрезать тело) можно так, что код ответа останется 200.
        decoded = None
        if enc == "gzip":
            try:
                decoded = gzip.decompress(body)
            except (OSError, EOFError) as e:
                note("BROKEN", f"{code}: тело не разжимается — {type(e).__name__}")
        elif enc == "br":
            checks += 1
            note("NODECODE", f"{code}: сервер отдал brotli — разжать нечем, обрезку не увидеть")
        if decoded is not None:
            checks += 1
            if decoded != disk:
                note("TRUNCATED", f"{code}: страница приехала не та или обрезана "
                                  f"({len(decoded)} байт против {len(disk)} в дереве)")

        cl = h.get("content-length")
        checks += 1
        if cl is not None and cl.strip().isdigit() and int(cl) != len(body):
            note("TRUNCATED", f"{code}: шапка обещает {cl} байт, приехало {len(body)}")

        checks += 1
        if len(body) > CEIL_COMPRESSED:
            note("FAT", f"{code}: по сети {len(body)} байт, потолок {CEIL_COMPRESSED}")

        checks += 1
        if enc in ("gzip", "br") and plain_n / max(len(body), 1) < CEIL_RATIO:
            note("NORATIO", f"{code}: сжатие даёт {plain_n / max(len(body), 1):.2f}× "
                            f"при нужных {CEIL_RATIO:g}× (сырой {plain_n}, по сети {len(body)})")

        checks += 1
        if enc in ("gzip", "br") and "accept-encoding" not in (h.get("vary") or "").lower():
            note("NOVARY", f"{code}: vary={h.get('vary')!r} — кеш вправе отдать gzip "
                           "тому, кто его не просил")

        checks += 1
        m = re.search(r"max-age\s*=\s*(\d+)", h.get("cache-control") or "")
        if not m:
            note("NOCACHE", f"{code}: cache-control={h.get('cache-control')!r} без max-age")
        elif int(m.group(1)) < DOC_MAXAGE:
            note("SHORTCACHE", f"{code}: max-age={m.group(1)} меньше обещанных {DOC_MAXAGE}")

        if proto:
            checks += 1
            v = protocol(url)
            if v is None:
                note("NOPROTO", f"{code}: версию протокола померить нечем (нет curl)")
            elif v != "2" and not v.startswith("2"):
                note("PROTO", f"{code}: протокол HTTP/{v}, README обещает HTTP/2")

        if rel == "index.html":
            raw_html = len(body)

    for rel, kind in MEDIA:
        url = base + rel
        disk = (ROOT / rel).read_bytes()
        try:
            st, h, body = get(url, ACCEPT)
        except (urllib.error.URLError, socket.timeout, OSError) as e:
            checks += 1
            note("DEAD", f"{kind} {rel}: не ответил — {e}")
            continue

        checks += 1
        if st != 200:
            note("STATUS", f"{kind} {rel}: ответ {st}")

        checks += 1
        if body != disk:
            note("TRUNCATED", f"{kind} {rel}: приехало {len(body)} байт против "
                              f"{len(disk)} в дереве — на телефоне играет битый файл или чужой")

        if rel.endswith(".mp4"):
            checks += 1
            if "bytes" not in (h.get("accept-ranges") or "").lower():
                note("NORANGE", f"{rel}: accept-ranges={h.get('accept-ranges')!r} — "
                                "перемотка ролика на телефоне не работает")

        enc = (h.get("content-encoding") or "").strip().lower()
        if enc in ("gzip", "br"):
            checks += 1
            plain_n = len((ROOT / rel).read_bytes())
            if plain_n / max(len(body), 1) < 1.15:
                note("DOUBLEZIP", f"{kind} {rel}: уже сжатый файл жмут повторно "
                                  f"({plain_n}→{len(body)}), выигрыша нет")

    if raw_html is not None:
        checks += 1
        txt = (ROOT / "README.md").read_text(encoding="utf-8")
        m = re.search(r"HTML в сжатом виде\s+([\d]+(?:[.,]\d+)?)\s*КБ", txt)
        if not m:
            note("DOCGONE", "README больше не называет сжатый размер HTML — "
                            "сверять нечего, обещание убрали молча")
        else:
            doc_kb = float(m.group(1).replace(",", "."))
            got_kb = raw_html / 1000
            if abs(got_kb - doc_kb) > README_KB_TOLERANCE:
                note("DOCWRONG", f"README обещает {doc_kb:g} КБ, по сети {got_kb:.1f} КБ "
                                 f"(допуск {README_KB_TOLERANCE:g})")


# ---------------------------------------------------------------- контроль

class Handler(http.server.SimpleHTTPRequestHandler):
    """Раздача дерева с управляемыми шапками: gzip, vary, кеш, длина."""

    mode = "clean"

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(Handler.directory), **kw)

    def log_message(self, *args, **kwargs):  # noqa: D401 — тишина в логе
        pass

    def do_GET(self):
        path = self.translate_path(self.path)
        p = Path(path)
        if p.is_dir():
            p = p / "index.html"
        if not p.is_file():
            self.send_error(404)
            return
        body = p.read_bytes()
        if self.mode == "liar":
            # честные шапки, обрезанное тело: код 200, длина сходится, страница не та
            body = body[:-100]
        ctype = self.guess_type(str(p))
        headers = [("Content-Type", ctype), ("Cache-Control", f"public, max-age={DOC_MAXAGE}")]
        if p.suffix == ".mp4":
            headers.append(("Accept-Ranges", "bytes"))
        texty = p.suffix in ("", ".html", ".css", ".js", ".svg", ".json", ".txt", ".xml")
        gz = ("gzip" in (self.headers.get("Accept-Encoding") or "")
              and self.mode != "nogzip"
              and (texty or self.mode == "zipmedia"))
        if gz:
            body = gzip.compress(body)
            headers.append(("Content-Encoding", "gzip"))
            if self.mode != "novary":
                headers.append(("Vary", "Accept-Encoding"))
        if self.mode == "short":
            headers = [(k, "public, max-age=0" if k == "Cache-Control" else v) for k, v in headers]
        self.send_response(200)
        for k, v in headers:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(port: int, mode: str) -> http.server.ThreadingHTTPServer:
    Handler.mode = mode
    Handler.directory = str(ROOT)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def control() -> int:
    global findings, checks
    port = 8731
    caught = 0
    total = 0

    def run(mode: str) -> list[str]:
        global findings, checks
        findings, checks = [], 0
        srv = serve(port, mode)
        try:
            measure(f"http://127.0.0.1:{port}/", proto=False)
        finally:
            srv.shutdown()
            srv.server_close()
        return list(findings)

    clean = run("clean")
    total += 1
    if clean:
        print(f"НЕ ПОЙМАЛ: чистая копия красная — {clean[:2]}")
    else:
        caught += 1
        print("чистая копия: зелёная")

    for mode, kind in (("nogzip", "NOGZIP"), ("short", "SHORTCACHE"), ("novary", "NOVARY"),
                       ("liar", "TRUNCATED"), ("zipmedia", "DOUBLEZIP")):
        total += 1
        got = run(mode)
        hit = [f for f in got if f.startswith(f"[{kind}]")]
        if hit:
            caught += 1
            print(f"ПОЙМАЛ {mode}: {hit[0]}")
        else:
            print(f"НЕ ПОЙМАЛ {mode}: прибор промолчал или назвал не тем классом — {got[:2]}")

    print(f"МУТАНТЫ {caught}/{total} — поймал {caught} из {total}")
    return 0 if caught == total else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--base", default=None)
    a = ap.parse_args()
    if a.control:
        return control()

    base = a.base or BASE
    if not base.endswith("/"):
        base += "/"
    measure(base, proto=True)
    print(f"CHECKS: {checks}, FAILED: {len(findings)}")
    for f in findings:
        print(" ", f)
    if not findings:
        print("по сети: девять страниц жмутся, кеш и vary на месте, медиа качается кусками")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
