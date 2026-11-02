#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-public-surface.py — что мир видит, кроме страниц.

Повод (02.11.2026, сорок восьмой блок). Сайт выкладывается из ветки `gh-pages`, и
в ней ровно 107 файлов из `tools/publish-tree.manifest()`. Живой сайт сверяется с
деревом побайтово (`live-bytes`, 107 файлов), шапки и адреса читает
`check-site-technical`, сеть — `check-transport`. Все они смотрят на то, что
должно отдаваться. Ни один не смотрит на обратное: отдаётся ли ЛИШНЕЕ.

Почему это не мелочь. До 24.10.2026 источником публикации был корень `main`, и
`/README.md` (196 КБ инженерного дневника), `/tools/build.py`, `/index-src.html`,
`/demo/*.py`, `/evidence/` отвечали 200 любому, кто угадает имя. Переключение
источника на `gh-pages` закрыло это одной настройкой репозитория — и ровно так же
одной настройкой открывается обратно (`gh api -X PUT repos/.../pages`). А
`live-bytes` этого НЕ увидит: в корне `main` лежат те же самые собранные страницы,
и все 107 файлов публикации совпадут байт в байт. Приборы останутся зелёными,
мастерская — снова публичной. Сегодня все семь проверенных адресов мастерской
отвечают 404 (замер 02.11), но это факт, а не защита: никто его не повторял.

Три класса:

  UP      — канарейки: две страницы скачиваются и сверяются побайтово с деревом.
            Без этого класса 404 ниже ничего не значит: лежащий хост, чужой адрес
            или DNS-ошибка дают те же 404, и прибор был бы зелёным, не измерив
            ничего.
  HIDDEN  — каждый адрес мастерской обязан ответить 404. Список не написан
            руками: берётся ВЕРХНИЙ уровень дерева и проверяется, входит ли он в
            список публикации. Появился новый каталог с исходниками — он попал в
            пробы сам. Для каталога пробуются и сам каталог (`dir/`), и образец
            файла внутри: каталог может отдавать 404, а файл — 200.
  BRANCH  — ветка публикации против списка публикации в обе стороны: лишний файл
            на ветке (его отдаст Pages) и пропавший файл (его отдаст 404, а
            манифест обещает) краснеют с именами.

Коды возврата: 0 — чисто; 1 — расхождение; 3 — проверить нельзя (нет сети, нет
локальной ссылки на ветку, пустой список проб) — ПРОПУСК, а не зелёное.

  python3 tools/check-public-surface.py
  python3 tools/check-public-surface.py --offline      # только ветка, без сети
  python3 tools/check-public-surface.py --control      # пять мутантов на своём сервере
"""
from __future__ import annotations

import argparse
import hashlib
import http.server
import importlib.util
import json
import socketserver
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def manifest() -> list[str]:
    spec = importlib.util.spec_from_file_location("publish_tree", ROOT / "tools" / "publish-tree.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("tools/publish-tree.py не читается")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.manifest())


BASE = "https://kerio-byte.github.io/uchisambot/"
CANARY = ("index.html", "ru/index.html")
UA = "landing-public-surface/1.0 (+check-public-surface.py)"
# Пробы, которые не выводятся из дерева: их нельзя пропустить ни при какой раскладке.
ALWAYS = (".git/", ".git/config", "README.md", "index-src.html")

checks = 0
fails: list[str] = []


def check(ok: bool, message: str) -> bool:
    global checks
    checks += 1
    if not ok:
        fails.append(message)
        print(f"  FAIL {message}")
    return ok


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, method: str = "HEAD") -> tuple[int, bytes]:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read() if method == "GET" else b""
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception as exc:  # сеть, DNS, TLS
        return 0, str(exc).encode()


def probes_from_tree(root: Path, published: set[str]) -> list[str]:
    """Верхний уровень дерева, которого нет в списке публикации."""
    out: list[str] = []
    for entry in sorted(root.iterdir()):
        name = entry.name
        if name.startswith(".") and name not in (".git",):
            continue
        if name in published or any(p.startswith(name + "/") for p in published):
            continue  # это сайт
        if entry.is_dir():
            out.append(name + "/")
            sample = next(
                (p for p in sorted(entry.rglob("*"))
                 if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts),
                None,
            )
            if sample is not None:
                out.append(sample.relative_to(root).as_posix())
        else:
            out.append(name)
    return out


def branch_paths(root: Path, ref: str = "origin/gh-pages") -> list[str] | None:
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", "--name-only", ref],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def run_live(base: str, root: Path, probes: list[str]) -> None:
    print(f"UP: канарейки против {base}")
    for rel in CANARY:
        status, body = fetch(base + rel, "GET")
        local = root / rel
        if not local.exists():
            check(False, f"UP: нет файла {rel} в дереве — сверять не с чем")
            continue
        if not check(status == 200, f"UP: {rel} ответил {status}, ждали 200 — 404 ниже ничего не докажут"):
            continue
        check(sha(body) == sha(local.read_bytes()),
              f"UP: {rel} скачался ({len(body)} Б), но байты не наши — это не наш сайт")

    print(f"HIDDEN: {len(probes)} адресов мастерской обязаны отвечать 404: " + ", ".join(probes))
    if len(probes) < 3:
        check(False, f"HIDDEN: проб {len(probes)} — список пуст, класс ничего не проверил")
        return
    for rel in probes:
        status, _ = fetch(base + rel)
        check(status == 404, f"HIDDEN: {rel} отвечает {status}, а мастерская не публикуется")


def run_branch(root: Path, published: list[str], paths: list[str] | None) -> None:
    if paths is None:
        print("BRANCH: ПРОПУСК — локальной ссылки origin/gh-pages нет (git fetch --all)")
        check(False, "BRANCH: ссылка origin/gh-pages не читается — ветка не проверена")
        return
    listed, man = set(paths), set(published)
    print(f"BRANCH: на ветке {len(listed)} файлов, в списке публикации {len(man)}")
    extra = sorted(listed - man)
    missing = sorted(man - listed)
    for name in extra:
        check(False, f"BRANCH: лишний файл на ветке — {name} (Pages его отдаст)")
    for name in missing:
        check(False, f"BRANCH: пропавший файл — {name} (список обещает, ветка отдаст 404)")
    check(not extra and not missing,
          f"BRANCH: ветка и список разошлись: лишних {len(extra)}, пропавших {len(missing)}")


# --------------------------------------------------------------------------- control

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D401, ANN002
        pass


def serve(directory: Path) -> tuple[socketserver.TCPServer, str]:
    handler = lambda *a, **kw: Quiet(*a, directory=str(directory), **kw)  # noqa: E731
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


def control() -> int:
    global checks, fails
    ok_cases = 0
    published = manifest()
    probes = ["README.md", "tools/", "tools/build.py", ".git/config"]

    def case(name: str, mutate, expect_fail: bool, must_mention: str = "") -> None:
        nonlocal ok_cases
        global checks, fails
        checks, fails = 0, []
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "site"
            tree.mkdir()
            for rel in CANARY:
                (tree / rel).parent.mkdir(parents=True, exist_ok=True)
                (tree / rel).write_bytes((ROOT / rel).read_bytes())
            lst = Path(tmp) / "branch.txt"
            lst.write_text("\n".join(published) + "\n", encoding="utf-8")
            mutate(tree, lst)
            srv, base = serve(tree)
            try:
                run_live(base, ROOT, probes)
                run_branch(ROOT, published, lst.read_text(encoding="utf-8").split())
            finally:
                srv.shutdown()
        red = bool(fails)
        good = (red == expect_fail) and (not expect_fail or any(must_mention in f for f in fails))
        print(f"  {'ok  ' if good else 'FAIL'} {name}: провалов {len(fails)}"
              + ("" if good else f" — ждали {'красное с ' + must_mention if expect_fail else 'зелёное'}"))
        if good:
            ok_cases += 1
        return None

    case("чистая копия", lambda t, l: None, False)
    case("README.md в дереве публикации", lambda t, l: (t / "README.md").write_text("дневник"), True, "README.md")
    case("нет канарейки index.html", lambda t, l: (t / "index.html").unlink(), True, "404 ниже ничего не докажут")
    case("лишний файл на ветке", lambda t, l: l.write_text(l.read_text() + "notes.txt\n"), True, "notes.txt")
    case("пропавший файл на ветке", lambda t, l: l.write_text("\n".join(published[1:]) + "\n"), True, "пропавший")

    print(f"КОНТРОЛЬ: поймал {ok_cases}/5")
    return 0 if ok_cases == 5 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=BASE)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--probes", help="файл со списком проб (по одной в строке)")
    ap.add_argument("--branch-list", help="файл со списком ветки (для контроля)")
    ap.add_argument("--offline", action="store_true", help="только класс BRANCH")
    ap.add_argument("--control", action="store_true")
    args = ap.parse_args()

    if args.control:
        return control()

    root = Path(args.root).resolve()
    published = manifest()
    paths = (Path(args.branch_list).read_text(encoding="utf-8").split()
             if args.branch_list else branch_paths(root))

    if not args.offline:
        if args.probes:
            probes = [p for p in Path(args.probes).read_text(encoding="utf-8").split() if p]
        else:
            probes = probes_from_tree(root, set(published)) + list(ALWAYS)
            probes = sorted(dict.fromkeys(probes))
        run_live(args.base_url, root, probes)
    run_branch(root, published, paths)

    print(f"ИТОГО: проверок {checks}, провалов {len(fails)}")
    if fails:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
