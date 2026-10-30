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
  blocked     — 401/403/429/999: край не пускает робота (Cloudflare, лимит),
                адрес при этом может быть живым; в отказы не пишется, но
                и в «ok» не выдаётся;
  error       — сеть/таймаут/DNS: код возврата 1.

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
            # прочие 4xx/5xx — пробуем другим методом, потом решаем
        except Exception as exc:                     # сеть, DNS, таймаут, TLS
            last = type(exc).__name__
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
            elif path == "/head405":
                self._answer(405 if self.command == "HEAD" else 200, b"ok")
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
        ("/broken", "error"), ("/head405", "ok"),
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
