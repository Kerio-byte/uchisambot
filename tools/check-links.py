#!/usr/bin/env python3
"""check-links.py — проверка внешних адресов лендинга, сложенная в репозиторий.

Повод. До 30.10.2026 реестр ссылок (tools/links-last-seen.json) обновлялся
одноразовым скриптом вне репозитория: результат коммитился, а сам прибор — нет.
Следующий запуск снова начинал бы с пустых рук, и «68 адресов, 0 отказов»
держалось бы на памяти человека, а не на коде.

Что делает:

  1) собирает все http(s)-адреса из собранного дерева — девять страниц,
     юридические, 404, llms.txt, sitemap.xml, robots.txt;
  2) проверяет каждый: HEAD, при отказе сервера — GET с ограничением тела;
     редиректы проходятся (urllib), итоговый код — вердикт;
  3) пишет tools/links-last-seen.json: когда проверено, сколько адресов,
     сколько отказов и непроверяемых, вердикт по каждому.

Классы вердикта:

  ok          — 2xx после редиректов;
  dead        — 404/410: адрес мёртв, это дефект страницы, код возврата 1;
  blocked     — 401/403/429/999 и edge-5xx (502/503/504/520–524/526):
                край или апстрим сломан — Cloudflare, лимит, origin лежит;
                адрес при этом может быть живым; в отказы не пишется, но
                и в «ok» не выдаётся;
  error       — сеть/таймаут/DNS, 500 и прочий 5xx не из края: код возврата 1.

Запуск:
  python3 tools/check-links.py            # проверить и обновить реестр
  python3 tools/check-links.py --offline  # только собрать адреса, без сети
  python3 tools/check-links.py --control  # проверка самого прибора, без сети

Возврат 0 — мёртвых и ошибочных нет, 1 — есть.

Повод (31.10.2026). До этого дня прибор проверял 116 живых адресов и всегда
был зелёным: «0 мёртвых» держалось на том, что мёртвых не попадалось, а не
на том, что прибор умеет их назвать. Соседние приборы (`check-redirects.py`,
`visual-pass.py`) контроль уже имели. Здесь появился свой: локальный сервер
отдаёт семь заведомо известных ответов, и прибор обязан разложить их ровно
по классам — 200 и 405-затем-200 в ok, 404 и 410 в dead, 403 и 429 в blocked,
500-на-both в error. Ошибка раскладки — код 1; реестр в этом режиме не
пишется вовсе.

Повод (04.11.2026, блок 79). Край fazier.com (Cloudflare) отвечал нам
HTTP 502 (03.11 — в реестре; свип «links» покрасился), а адрес жив:
сайт отвечает 200 на origin-адресе (188.114.97.1), а независимый
фетч (r.jina.ai) читает главную. 502 — это заявление края «апстрим
сломан, может восстановиться», а не мёртвый адрес; класс blocked
создан ровно для этого («край не пускает, адрес может быть живым»),
поэтому edge-5xx (502/503/504 и 520–524, 526 от Cloudflare) добавлены
в него. 500 остаётся error: это сбой приложения, не край. Контроль
посадил: /edge502 и /edge503 обязаны лечь в blocked, /broken (500) —
в error.

Повод (04.11.2026, блок 92). Край fazier.com (Cloudflare) таймаутнул
первый зонд (TIME=15 с), а адрес жив: три независимых фетча дали 200
за 4–6 с, второй прогон самого прибора — зелёный. Таймаут — медленный
край, тот же класс, что 502 в блоке 79, поэтому _transient
(TimeoutError/ConnectionResetError, в чистом виде или внутри URLError)
получает один повтор того же метода до вердикта error; стойкий сетевой
сбой остаётся error. Контроль добавил /reset (соединение рвётся без
ответа): обязан остаться error после повтора.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import glob
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "tools" / "links-last-seen.json"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
URL_RE = re.compile(r"https?://[^\s\"'<>()\\)]+")
TIME = 15
# 5xx от края/апстрима: «апстрим сломан, может восстановиться» — адрес жив.
# 500 и прочие 5xx не из края — сбой приложения, остаются в error.
EDGE_UPSTREAM = frozenset({502, 503, 504, 520, 521, 522, 523, 524, 526})


def sources() -> list[Path]:
    """Файлы собранного дерева, в которых вообще могут быть адреса."""
    out = [ROOT / "index.html", ROOT / "privacy.html", ROOT / "terms.html",
           ROOT / "404.html", ROOT / "llms.txt", ROOT / "sitemap.xml",
           ROOT / "robots.txt"]
    out += sorted(Path(p) for p in glob.glob(str(ROOT / "*/index.html")))
    return [p for p in out if p.exists()]


def is_namespace(url: str) -> bool:
    """Адреса XML-пространств имён (xmlns, xlink) — не ссылки, кликать нечего."""
    parts = urlsplit(url)
    return (parts.hostname or "").endswith("w3.org") and \
        parts.path.startswith(("/1999/", "/2000/", "/2001/"))


def collect() -> list[str]:
    seen: dict[str, None] = {}
    for path in sources():
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw in URL_RE.findall(text):
            url = raw.rstrip(".,;:")
            url = url.replace("&amp;", "&")
            if is_namespace(url):
                continue
            if urlsplit(url).scheme in ("http", "https") and url not in seen:
                seen[url] = None
    return sorted(seen)


def _transient(exc: BaseException) -> bool:
    """Транзитный сбой транспорта: таймаут или сброшенное соединение,
    в чистом виде или внутри URLError. HTTPError сюда не попадает."""
    if isinstance(exc, (TimeoutError, ConnectionResetError)):
        return True
    if isinstance(exc, urllib.error.URLError):
        return isinstance(getattr(exc, "reason", None),
                          (TimeoutError, ConnectionResetError))
    return False


def probe(url: str) -> tuple[str, str]:
    """(класс, подробность). Класс — ok / dead / blocked / error / endpoint."""
    host = (urlsplit(url).hostname or "").lower()
    if host == "api.web3forms.com":
        return "endpoint", "адрес приёма формы, отвечает только на POST"
    last = ""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en;q=0.8",
        })
        try:
            with urllib.request.urlopen(req, timeout=TIME) as resp:
                return "ok", str(resp.status)
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code in (404, 410):
                return "dead", last
            if exc.code in (401, 403, 429, 999):
                return "blocked", last
            if exc.code in EDGE_UPSTREAM:
                return "blocked", last
            # прочие 4xx/5xx — пробуем другим методом, потом решаем
        except Exception as exc:                     # сеть, DNS, таймаут, TLS
            last = type(exc).__name__
            if _transient(exc):
                # Край может ответить медленно (fazier/Cloudflare, 04.11,
                # блок 92): один повтор того же метода до вердикта;
                # стойкий сбой — всё ещё error.
                try:
                    with urllib.request.urlopen(req, timeout=TIME) as resp:
                        return "ok", str(resp.status)
                except Exception as exc2:             # повтор тоже не пришёл
                    last = f"{type(exc).__name__}->{type(exc2).__name__}"
    return "error", last


def control() -> int:
    """Проверка самого прибора: локальный сервер отдаёт известные ответы.

    Сеть не нужна: сервер поднимается на 127.0.0.1 со случайным портом.
    Раскладка по классам сравнивается с ожиданием; любое расхождение — провал.
    """
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def _answer(self, code: int, body: bytes = b"") -> None:
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def do_HEAD(self) -> None:
            self._route()

        def do_GET(self) -> None:
            self._route()

        def _route(self) -> None:
            path = urlsplit(self.path).path
            if path == "/ok":
                self._answer(200, b"ok")
            elif path == "/missing":
                self._answer(404)
            elif path == "/gone":
                self._answer(410)
            elif path == "/forbidden":
                self._answer(403)
            elif path == "/flood":
                self._answer(429)
            elif path == "/broken":
                self._answer(500)
            elif path == "/edge502":
                self._answer(502)
            elif path == "/edge503":
                self._answer(503)
            elif path == "/head405":
                self._answer(405 if self.command == "HEAD" else 200, b"ok")
            elif path == "/reset":
                # Соединение рвётся без ответа: клиент видит сброс,
                # прибор обязан повторить и всё равно лечь в error.
                self.close_connection = True
                try:
                    self.connection.shutdown(2)
                except OSError:
                    pass
            else:
                self._answer(404)

        def log_message(self, *a) -> None:      # тишина в выводе прибора
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    rows = [
        ("/ok", "ok"), ("/missing", "dead"), ("/gone", "dead"),
        ("/forbidden", "blocked"), ("/flood", "blocked"),
        ("/edge502", "blocked"), ("/edge503", "blocked"),
        ("/broken", "error"), ("/head405", "ok"), ("/reset", "error"),
    ]
    bad = 0
    try:
        for path, want in rows:
            got, note = probe(base + path)
            mark = "ok " if got == want else "FAIL"
            if got != want:
                bad += 1
            print(f"  {mark} {path:<11} ждали {want:<8} получили {got} ({note})")
    finally:
        server.shutdown()
        server.server_close()
    print(f"поймал {len(rows) - bad} из {len(rows)}")
    print(f"CHECKS: {len(rows)}, FAILED: {bad}")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="только собрать адреса, сеть не трогать")
    ap.add_argument("--control", action="store_true",
                    help="проверка самого прибора: локальные известные ответы")
    args = ap.parse_args()

    if args.control:
        return control()

    urls = collect()
    if args.offline:
        print(f"адресов собрано: {len(urls)} (сеть не трогали)")
        return 0

    verdicts: dict[str, str] = {}
    details: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(probe, u): u for u in urls}
        for fut in concurrent.futures.as_completed(futures):
            url = futures[fut]
            try:
                cls, note = fut.result()
            except Exception as exc:                 # не должно случаться
                cls, note = "error", type(exc).__name__
            verdicts[url] = cls
            if cls != "ok":
                details[url] = note

    dead = sorted(u for u, v in verdicts.items() if v == "dead")
    errors = sorted(u for u, v in verdicts.items() if v == "error")
    blocked = sorted(u for u, v in verdicts.items() if v == "blocked")
    endpoints = sorted(u for u, v in verdicts.items() if v == "endpoint")
    hosts = sorted({urlsplit(u).hostname or "" for u in urls})

    data = {
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "addresses": len(urls),
        "failed": len(dead) + len(errors),
        "unverified": len(blocked),
        "endpoints": len(endpoints),
        "hosts": hosts,
        "verdicts": verdicts,
        "details": details,
    }
    REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")

    print(f"адресов: {len(urls)}  ok: "
          f"{len(urls) - len(dead) - len(errors) - len(blocked) - len(endpoints)}"
          f"  мёртвых: {len(dead)}  ошибок: {len(errors)}"
          f"  край не пустил: {len(blocked)}  адресов формы: {len(endpoints)}")
    for label, group in (("МЁРТВЫЙ", dead), ("ОШИБКА", errors),
                         ("НЕ ПРОВЕРЕН", blocked)):
        for url in group:
            print(f"  {label}: {url} — {details.get(url, '')}")
    print("реестр:", REGISTRY.relative_to(ROOT))
    return 0 if not dead and not errors else 1


if __name__ == "__main__":
    sys.exit(main())
