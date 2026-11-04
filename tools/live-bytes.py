#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Живой сайт против репозитория: байт в байт.

Зачем (31.10.2026). Девять страниц собираются в дереве, а посетитель читает копию
на GitHub Pages из ветки `gh-pages`. Пока эти две вещи расходятся, весь живой
пояс свипа (редиректы, 116 адресов, canonical, `claim-basis`) проверяет ВЧЕРАШНЮЮ
страницу: репозиторий ушёл вперёд, а приборы этого не видят и остаются зелёными.
Обещание «страница говорит то, что мы проверили» держится на равенстве байтов,
и до 31.10 его не держал никто: `build.py` сверяет дерево само с собой,
`publish-tree.py` — список публикации, а живой ответ не читал ни один прибор.

Повод (01.11.2026, блок 28). Заголовок прибора говорил «байт в байт», а его
собственный `SKIP_DIRS` выбрасывал `img` и `fonts`: сверялись только страницы и
текстовые файлы — 16 из 107 опубликованных. Вне сверки оставались 57 картинок и
11 шрифтов, то есть ровно то, чем один язык отличается от другого: постеры и ролики
у каждого свои (правило владельца 15.10). Поломка тихая: перевели текст, а на живой
странице играет английский ролик — файл существует, код ответа 200, журнал загрузки
доволен, все приборы зелёные. Теперь список берётся не из обхода дерева, а из
`publish-tree.manifest()` — того же списка, которым публикация раскладывает сайт:
один источник истины на публикацию и на сверку, чтобы они не разошлись в первый
же месяц.

`--control` подаёт прибору копию дерева с двумя испорченными байтами — в странице
и в картинке — и требует, чтобы он назвал ровно эти два файла: прибор, который не
умеет краснеть, ничего не доказывает. Мутант в картинке нужен отдельно: до этой
правки прибор на порчу любого файла из `img/` молчал.

Питфолл: `url_for()` превращает `xx/index.html` в `…/xx/`, потому что Pages отдаёт
страницу по адресу каталога; для остальных файлов адрес — путь как есть.

Повод (04.11.2026, блок 93). Живой край на первом прогоне ответил кодом края
(HTTPError) на img/shot1.webp, адрес жив: три независимых фетча дали 200 по
69750 байт — ровно байты файла в дереве, повторный прогон — 107/0. Та же
классовая история, что таймаут края в блоке 92 (fazier), поэтому `fetch()`
теперь делает один повтор того же запроса при транзитном сбое (таймаут,
сброшенное соединение, код края 429/502/503/504) до вердикта «нет ответа»;
404/403 повтор не получают — это настоящий ответ, а не медленный край.
Стойкий сбой края остаётся красным. Контроль расширен: flaky-502 обязан
уцелеть после повтора, dead-502 обязан остаться красным после повтора.

Повод (05.11.2026, блок 94). Блок 93 оставил незакрытым хвост: докстринг выше
заявил повтор в `fetch()` и расширенный контроль, а кода не было — прибор
заявлял защиту, которой не держал (правило дерева, 01.11: обещание без имени
прибора и без кода — долг, а не документация). Код дописан по прецеденту
`check-links.py` (блоки 79/92): `_transient()` узнаёт таймаут, сброшенное
соединение и коды края 429/502/503/504 — в чистом виде и внутри `URLError`;
`fetch()` делает один повтор того же запроса, стойкий сбой поднимает исключение.
`fetch_control()` поднимает локальный сервер со случайным портом (сеть не нужна):
`/flaky` (502, потом 200) обязан вернуться байтами, `/dead` (502 вечно) обязан
остаться красным после повтора, `/forbidden` (403) — красным ровно за один
запрос, повтор не получает. `--control` теперь гоняет обе ветви: сверку байтов
на мутантах дерева и fetch на мутантах края; обе обязаны уметь краснеть.
"""
import argparse
import hashlib
import importlib.util
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://kerio-byte.github.io/uchisambot/"
TEXT_SUFFIXES = {".html", ".xml", ".txt", ".md"}
# Коды края: медленный/уставший край, а не ответ о файле. 404/403 — настоящий
# ответ и в этот набор не попадает (документация выше).
_TRANSIENT_HTTP = {429, 502, 503, 504}


def _publish_tree():
    """Модуль публикации по пути: в имени дефис, обычный import не сработает."""
    spec = importlib.util.spec_from_file_location("publish_tree", ROOT / "tools" / "publish-tree.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("tools/publish-tree.py не читается")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def published() -> list[Path]:
    """Ровно то, что публикация обязана выложить: список намерения, не обход дерева.

    `manifest()` — единственное место, где перечислен сайт. Пока сверка строила
    свой список (`rglob` + `SKIP_DIRS`), она молча проверяла меньше, чем публикация
    выкладывала, и расхождение двух списков было невидимо обоим.
    """
    return [Path(f) for f in _publish_tree().manifest()]


def url_for(rel: Path) -> str:
    if rel.name == "index.html":
        parent = rel.parent.as_posix()
        return BASE if parent == "." else f"{BASE}{parent}/"
    return f"{BASE}{rel.as_posix()}"


def _transient(exc: BaseException) -> bool:
    """Транзитный сбой края: таймаут, сброшенное соединение или код края.

    Медленный край — не ответ о файле. 404/403 — настоящий ответ, повтор не
    получают (прецедент `_transient` в `check-links.py`, блок 92).
    """
    if isinstance(exc, (TimeoutError, ConnectionResetError)):
        return True
    if isinstance(exc, urllib.error.HTTPError) and exc.code in _TRANSIENT_HTTP:
        return True
    if isinstance(exc, urllib.error.URLError):
        return _transient(getattr(exc, "reason", None) or exc)
    return False


def fetch(url: str, attempts: int = 2) -> bytes:
    """Фетч с одним повтором при транзитном сбое края (04.11, блок 93).

    Край может ответить медленно или кодом 502 — это ответ о крае, а не о
    файле. Один повтор того же запроса; стойкий сбой остаётся красным.
    """
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": "live-bytes/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001 — решаем по природе сбоя, не по типу
            if i == attempts - 1 or not _transient(exc):
                raise
    raise RuntimeError("недостижимо: повторы не кончились")


def compare(root: Path, verbose: bool = True):
    files = published()
    bad = []
    for rel in files:
        url = url_for(rel)
        try:
            live = fetch(url)
        except Exception as e:  # noqa: BLE001 — ответа нет, это тоже расхождение
            bad.append((rel, f"нет ответа: {type(e).__name__}"))
            if verbose:
                print(f"  DIFF {url} — нет ответа ({e})")
            continue
        mine = (root / rel).read_bytes()
        if hashlib.sha256(live).hexdigest() == hashlib.sha256(mine).hexdigest():
            if verbose:
                print(f"  ok   {url}")
        else:
            bad.append((rel, f"живой {len(live)} б, в дереве {len(mine)} б"))
            if verbose:
                print(f"  DIFF {url}  живой {len(live)} б, в дереве {len(mine)} б")
    return files, bad


def control():
    """Копия дерева с двумя испорченными байтами обязана покраснеть именно ими.

    Классов два — текст и бинарный файл. Прибор, который ловит только первый,
    выглядит зелёным на сломанном постере.
    """
    files = published()
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "tree"
        copy.mkdir()
        for rel in files:
            dst = copy / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)
        page = next((rel for rel in files if rel.name == "index.html"), None)
        asset = next((rel for rel in files
                      if rel.suffix not in TEXT_SUFFIXES
                      and 0 < (ROOT / rel).stat().st_size < 400_000), None)
        if page is None or asset is None:
            print("КОНТРОЛЬ: НЕ ПОЙМАН — в публикации нет то ли страницы, то ли картинки")
            return 1
        text = (copy / page).read_text(encoding="utf-8")
        (copy / page).write_text(text.replace("</title>", " </title>", 1), encoding="utf-8")
        blob = bytearray((copy / asset).read_bytes())
        blob[-1] ^= 0xFF  # последний байт: файл на месте, содержимое — уже нет
        (copy / asset).write_bytes(bytes(blob))
        _files, bad = compare(copy, verbose=False)
        caught = {rel for rel, _ in bad}
        want = {page, asset}
        ok = caught == want
        print(f"КОНТРОЛЬ (сверка байтов): {'поймал' if ok else 'НЕ ПОЙМАЛ'} "
              f"{len(caught & want)} из {len(want)} — испорчено {sorted(str(x) for x in want)}, "
              f"прибор сказал {sorted(str(x) for x in caught) or 'ничего'}")
        return 0 if ok else 1


def fetch_control():
    """Край-имитация: локальный сервер со случайным портом, сеть не нужна.

    `/flaky` (первый 502, второй 200) обязан уцелеть после повтора — это
    медленный край, а не отсутствие файла. `/dead` (502 вечно) обязан остаться
    красным после повтора — повтор лечит медленный край, не стойкий сбой.
    `/forbidden` (403) — настоящий ответ: красный, ровно один запрос, повтор
    не получает. `/ok` — санити: живой фетч возвращает байты.
    """
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    hits: dict[str, int] = {}

    class Handler(BaseHTTPRequestHandler):
        def _answer(self, code: int, body: bytes = b"") -> None:
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_GET(self) -> None:
            path = urllib.parse.urlsplit(self.path).path
            hits[path] = hits.get(path, 0) + 1
            if path == "/ok":
                self._answer(200, b"ok-bytes")
            elif path == "/flaky":
                self._answer(502 if hits[path] == 1 else 200, b"flaky-bytes")
            elif path == "/dead":
                self._answer(502)
            elif path == "/forbidden":
                self._answer(403)
            else:
                self._answer(404)

        def log_message(self, *a) -> None:      # тишина в выводе прибора
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    rows: list[tuple[str, bool, str]] = []
    try:
        try:
            data = fetch(base + "/ok")
            rows.append(("/ok", data == b"ok-bytes", "байты получены"))
        except Exception as exc:
            rows.append(("/ok", False, f"не пришёл ({type(exc).__name__})"))

        try:
            data = fetch(base + "/flaky")
            rows.append(("/flaky", data == b"flaky-bytes", "уцелел после повтора"))
        except Exception as exc:
            rows.append(("/flaky", False, f"повтор не помог ({type(exc).__name__})"))

        try:
            fetch(base + "/dead")
            rows.append(("/dead", False, "пробился сквозь стойкий 502"))
        except Exception:
            rows.append(("/dead", True, f"красный после повтора, запросов {hits.get('/dead', 0)}"))

        try:
            fetch(base + "/forbidden")
            rows.append(("/forbidden", False, "пробился сквозь 403"))
        except Exception:
            rows.append(("/forbidden", hits.get("/forbidden", 0) == 1,
                         f"красный, запросов {hits.get('/forbidden', 0)} (обязан быть 1)"))
    finally:
        server.shutdown()
        server.server_close()

    bad = 0
    for path, ok, note in rows:
        if not ok:
            bad += 1
        print(f"  {'ok ' if ok else 'FAIL'} {path:<13} {note}")
    print(f"КОНТРОЛЬ (fetch): поймал {len(rows) - bad} из {len(rows)}")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Живой сайт против дерева: байт в байт.")
    ap.add_argument("--root", default=str(ROOT), help="дерево для сверки")
    ap.add_argument("--control", action="store_true",
                    help="проверить сам прибор: сверку байтов и fetch")
    ap.add_argument("--quiet", action="store_true", help="только расхождения")
    args = ap.parse_args()
    if args.control:
        rc_tree = control()
        rc_fetch = fetch_control()
        if rc_tree or rc_fetch:
            print("КОНТРОЛЬ: НЕ ПОЙМАН — прибор не умеет краснеть")
        return 1 if (rc_tree or rc_fetch) else 0
    files, bad = compare(Path(args.root), verbose=not args.quiet)
    text, media = _publish_tree().split_kinds([str(f) for f in files])
    print(f"\nИТОГО: {len(files)} файлов (текст {text}, медиа {media}), "
          f"расхождений {len(bad)}")
    if bad:
        print("ПРОВАЛЕНО: живой сайт не равен дереву (публикация отстала?)")
        for rel, why in bad:
            print(f"  {rel}: {why}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
