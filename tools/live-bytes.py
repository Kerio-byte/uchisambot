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
"""
import argparse
import hashlib
import importlib.util
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://kerio-byte.github.io/uchisambot/"
TEXT_SUFFIXES = {".html", ".xml", ".txt", ".md"}


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


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "live-bytes/2.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


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
        print(f"КОНТРОЛЬ: {'поймал' if ok else 'НЕ ПОЙМАЛ'} {len(caught & want)} из {len(want)} — "
              f"испорчено {sorted(str(x) for x in want)}, прибор сказал "
              f"{sorted(str(x) for x in caught) or 'ничего'}")
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
