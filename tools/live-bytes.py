#!/usr/bin/env python3
"""Живой сайт против репозитория: байт в байт.

Зачем (31.10.2026). Девять страниц собираются в дереве, а посетитель читает копию
на GitHub Pages из ветки `gh-pages`. Пока эти две вещи расходятся, весь живой
пояс свипа (редиректы, 116 адресов, canonical, `claim-basis`) проверяет ВЧЕРАШНЮЮ
страницу: репозиторий ушёл вперёд, а приборы этого не видят и остаются зелёными.
Обещание «страница говорит то, что мы проверили» держится на равенстве байтов,
и до 31.10 его не держал никто: `build.py` сверяет дерево само с собой,
`publish-tree.py` — список публикации, а живой ответ не читал ни один прибор.

`--control` подаёт прибору копию дерева с одним испорченным байтом и требует,
чтобы он назвал ровно этот файл: прибор, который не умеет краснеть, ничего
не доказывает.
"""
import argparse
import hashlib
import re
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://kerio-byte.github.io/uchisambot/"
SKIP_DIRS = {"src", "demo", "docs", "evidence", "submission-kit", "img", "fonts",
             "tools", "__pycache__", ".git"}


def deployed(root: Path):
    """Страницы и текстовые файлы, которые читает человек или робот.

    Мастерская (`.shots-work`, скрытые каталоги) и исходники (`index-src.html`)
    в публикацию не идут: живой сайт их не отдаёт, и спрашивать с него нечего.
    """
    out = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts) or not p.is_file():
            continue
        if rel.name.endswith("-src.html"):
            continue
        if p.suffix not in {".html", ".xml", ".txt"}:
            continue
        out.append(rel)
    return out


def url_for(rel: Path) -> str:
    if rel.name == "index.html":
        parent = rel.parent.as_posix()
        return BASE if parent == "." else f"{BASE}{parent}/"
    return f"{BASE}{rel.as_posix()}"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "live-bytes/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def compare(root: Path, verbose: bool = True):
    files = deployed(root)
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
    """Копия дерева с одним испорченным байтом обязана покраснеть именно им."""
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "tree"
        copy.mkdir()
        victim = None
        for rel in deployed(ROOT):
            dst = copy / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)
            if victim is None and rel.name == "index.html":
                victim = rel
        if victim is None:
            print("КОНТРОЛЬ: НЕ ПОЙМАН — в дереве нет ни одной страницы")
            return 1
        page = copy / victim
        text = page.read_text(encoding="utf-8")
        page.write_text(text.replace("</title>", " </title>", 1), encoding="utf-8")
        _files, bad = compare(copy, verbose=False)
        caught = [rel for rel, _ in bad]
        ok = set(caught) == {victim}
        print(f"КОНТРОЛЬ: {'поймал' if ok else 'НЕ ПОЙМАЛ'} 1 из 1 — "
              f"испорчен {victim}, прибор сказал {caught or 'ничего'}")
        return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Живой сайт против дерева: байт в байт.")
    ap.add_argument("--root", default=str(ROOT), help="дерево для сверки")
    ap.add_argument("--control", action="store_true", help="проверить сам прибор")
    ap.add_argument("--quiet", action="store_true", help="только расхождения")
    args = ap.parse_args()
    if args.control:
        return control()
    files, bad = compare(Path(args.root), verbose=not args.quiet)
    print(f"\nИТОГО: {len(files)} файлов, расхождений {len(bad)}")
    if bad:
        print("ПРОВАЛЕНО: живой сайт не равен дереву (публикация отстала?)")
        for rel, why in bad:
            print(f"  {rel}: {why}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
