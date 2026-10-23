#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/publish-tree.py — что именно уезжает в свет.

Зачем (23.10.2026). GitHub Pages отдаёт ВЕСЬ корень репозитория: страницы лежат
рядом со сборочной мастерской (tools/, src/locales, demo/*.py|sh, README.md с
инженерным дневником). Замер: 154 файла в репозитории, из них 37 — не сайт;
/README.md (196 КБ) и /tools/build.py отвечают 200. Пока витрина и мастерская
делят один корень, любая заметка с адресом или путём уезжает в открытый веб.

Этот скрипт — единственный список того, что считается сайтом. Он умеет:
  --check          проверить список: всё на месте, ни одного файла мастерской,
                   и КАЖДАЯ внутренняя ссылка со страниц ведёт на файл из списка;
  --stage DIR      разложить список в DIR (для ветки публикации);
  --list           напечатать список.

Проверка «ничего лишнего» ловит обратное: файл, который лежит в корне и
отдаётся, но в список не входит. Проверка «ничего не забыли» ловит переезд на
отдельную ветку, который унёс бы с собой половину картинок.
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
BASE = json.loads((ROOT / "tools" / "site.json").read_text(encoding="utf-8"))["base"]
LANGS = ["ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]

# Ровно то, что нужно странице. Ничего из tools/, src/, demo/*.py|sh|json, README.md.
PUBLIC_FILES = [
    "index.html", "index.html.md",
    "privacy.html", "privacy.html.md",
    "terms.html", "terms.html.md",
    "404.html", "sitemap.xml", "robots.txt", "llms.txt", ".nojekyll",
    "210a46fb97554124948a7b1a74a15d5f.txt",   # ключ IndexNow: его читает поиск
]
PUBLIC_DIRS = ["img", "fonts"]
PUBLIC_DEMO = ["*.mp4"]                      # видео (полные демо + петли героя)

# Мастерская: лежит в том же корне, но сайтом не является.
BACKSTAGE = [
    "README.md", "index-src.html", "tools/", "src/", "demo/*.py", "demo/*.sh",
    "demo/*.json", "evidence/", ".gitignore",
]


def manifest() -> list[str]:
    out = [f for f in PUBLIC_FILES if (ROOT / f).exists()]
    for d in PUBLIC_DIRS:
        out += [str(p.relative_to(ROOT)) for p in sorted((ROOT / d).rglob("*")) if p.is_file()]
    for lang in LANGS:
        out.append(f"{lang}/index.html")
        out.append(f"{lang}/index.html.md")
    for pat in PUBLIC_DEMO:
        out += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "demo").glob(pat))]
    return sorted(set(out))


def served_files() -> list[str]:
    """Всё, что Pages реально отдаёт: файлы, попавшие в git.

    Pages публикует коммит, а не рабочий каталог, — поэтому источник истины здесь
    индекс git, а не обход дерева: неотслеживаемый evidence/ (289 файлов заметок)
    в сети не появляется, а два ранних файла отчётов, закоммиченных до .gitignore,
    отдаются по прямым адресам (проверено запросом) — они и попадают в список.
    На копии без .git (негативный контроль) — обход дерева без кэшей.
    """
    try:
        top = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True, timeout=60).stdout.strip()
        # Копия дерева часто лежит ВНУТРИ другого репозитория (рабочий каталог агента):
        # тогда `git -C копия ls-files` отвечает списком ЧУЖОГО репозитория, и все
        # файлы копии выглядят неотслеживаемыми. Сверяем корень с ROOT.
        if top and Path(top).resolve() == ROOT.resolve():
            out = subprocess.run(["git", "-C", str(ROOT), "ls-files"],
                                 capture_output=True, text=True, check=True,
                                 timeout=60).stdout.split()
            if out:
                return sorted(out)
    except Exception:
        pass
    files = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if any(part in (".git", "__pycache__", ".shots-work") for part in rel.parts):
            continue
        if p.is_file():
            files.append(str(rel))
    return sorted(files)


def backstage_files() -> list[str]:
    pub = set(manifest())
    return [f for f in served_files() if f not in pub]


# ---------- ссылки ----------

_HREF = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.I)
_MD = re.compile(r"\]\(([^)\s]+)\)")
_LOC = re.compile(r"<loc>([^<]+)</loc>")


def _local_target(url: str, page: str) -> str | None:
    """Куда ведёт ссылка внутри сайта: путь относительно корня, или None (внешнее)."""
    if url.startswith(("mailto:", "tel:", "data:", "javascript:", "#")):
        return None
    if url.startswith(BASE):
        path = url[len(BASE):]
        return path.split("#")[0].split("?")[0] or "index.html"
    if url.startswith("/"):
        # абсолютный путь от корня домена: на project-странице это не наш корень
        return None
    u = urlparse(url)
    if u.scheme or u.netloc:
        return None
    path = url.split("#")[0].split("?")[0]
    if not path:
        return None
    base_dir = Path(page).parent
    joined = posixpath.normpath((base_dir / path).as_posix())
    if joined == ".":
        return ""
    return joined.lstrip("./") + ("/" if path.endswith("/") else "")


def references(files: list[str]) -> list[tuple[str, str, str]]:
    """(файл, ссылка, ожидаемый путь) для каждой внутренней ссылки опубликованного файла."""
    out = []
    for rel in files:
        p = ROOT / rel
        if p.suffix not in (".html", ".md", ".txt", ".xml"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        found = []
        if p.suffix == ".html":
            found = _HREF.findall(text)
        elif p.suffix == ".md":
            found = _MD.findall(text)
        elif p.suffix == ".xml":
            found = _LOC.findall(text)
        for url in found:
            tgt = _local_target(url, rel)
            if tgt is None:
                continue
            out.append((rel, url, tgt))
    return out


def check() -> int:
    pub = manifest()
    back = backstage_files()
    problems = []

    # 1) всё из списка существует
    for f in pub:
        if not (ROOT / f).is_file():
            problems.append(f"нет файла из списка: {f}")

    # 2) мастерская не попала в список
    for f in back:
        if f in pub:
            problems.append(f"мастерская в списке публикации: {f}")

    # 3) каждая внутренняя ссылка ведёт на файл из списка
    pubset = set(pub)
    dangling = []
    for src, url, tgt in references(pub):
        cand = tgt
        if cand.endswith("/") or cand == "":
            cand = cand + "index.html"
        if cand not in pubset:
            dangling.append(f"{src}: {url} -> {cand}")
    problems += [f"ссылка на файл вне публикации: {d}" for d in dangling[:20]]

    # 4) обратный счёт: страница не смотрит в мастерскую
    for src, url, tgt in references(pub):
        for b in ("tools/", "src/", "demo/captions", "index-src.html", "README.md", "evidence/"):
            if tgt.startswith(b):
                problems.append(f"страница ссылается на мастерскую: {src}: {url}")

    size = sum((ROOT / f).stat().st_size for f in pub if (ROOT / f).is_file())
    print(f"публикация: {len(pub)} файлов, {size / 1048576:.1f} МБ")
    print(f"мастерская (в публикацию не идёт): {len(back)} файлов")
    for b in back:
        print(f"   - {b}")
    print(f"внутренних ссылок проверено: {len(references(pub))}")
    if problems:
        print("ПРОВАЛ:")
        for p in problems:
            print("  " + p)
        return 1
    print("ПРОВЕРЕНО: список полон, лишнего нет, все внутренние ссылки внутри списка")
    return 0


def stage(dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    for f in manifest():
        target = dest / f
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, target)
    print(f"разложено: {len(manifest())} файлов -> {dest}")
    return 0


def verify_served(dest: Path) -> int:
    """Отдать дерево локальным сервером и попросить каждый адрес, как это сделает посетитель.

    Проверяем не «файл лежит», а «по этому адресу отвечает 200»: именно так ломается
    переезд на отдельную ветку — файл есть, а ссылка ведёт в пустоту (регистр букв,
    путь с точкой, забытый /index.html).
    """
    import functools
    import http.server
    import socketserver
    import threading
    import urllib.request

    files = [str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()]
    urls = set()
    for rel in files:
        p = dest / rel
        if p.suffix == ".html":
            urls.add(rel)
        if p.suffix not in (".html", ".md", ".txt", ".xml"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        found = _HREF.findall(text) if p.suffix == ".html" else (
            _MD.findall(text) if p.suffix == ".md" else _LOC.findall(text))
        for url in found:
            tgt = _local_target(url, rel)
            if tgt is None:
                continue
            if tgt == "" or tgt.endswith("/"):
                tgt = tgt + "index.html"
            urls.add(tgt)

    class _Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):        # без строк на каждый запрос: нужен итог, не шум
            pass

        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(dest), **kw)

    handler = _Quiet
    with socketserver.TCPServer(("[адрес]", 0), handler) as srv:
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        bad = []
        for u in sorted(urls):
            try:
                with urllib.request.urlopen(f"http://[адрес]:{port}/{u}", timeout=15) as r:
                    if r.status != 200:
                        bad.append(f"{u} -> {r.status}")
            except Exception as e:
                bad.append(f"{u} -> {e}")
        srv.shutdown()
    print(f"адресов проверено: {len(urls)}, ошибок: {len(bad)}")
    for b in bad[:10]:
        print("   ПРОБЛЕМА " + b)
    if bad:
        return 1
    print("ПУБЛИКАЦИЯ ПРОВЕРЕНА: локальный сервер отдаёт каждый адрес дерева")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--stage", metavar="DIR")
    ap.add_argument("--verify-served", metavar="DIR")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for f in manifest():
            print(f)
        return 0
    if a.stage:
        return stage(Path(a.stage))
    if a.verify_served:
        return verify_served(Path(a.verify_served))
    return check()


if __name__ == "__main__":
    sys.exit(main())
