#!/usr/bin/env python3
"""Чистая копия репозитория собирается побайтно в то же дерево.

Повод (01.11.2026, двадцать девятый блок). Прибор `build` в `check-all.py` называется
«сборка проверяется на воспроизводимость», и это правда только наполовину: два прогона
делаются В ОДНОМ дереве, а сравниваются два снимка `git status`. Такой замер не видит
главного класса — сборки, которая читает собственный мусор. Если генератор начнёт
читать свой прошлый вывод (`tools/lastmod.json`, готовую страницу, случайно оставленный
файл), то в прогретом дереве второй прогон ничего не изменит, снимки совпадут, прибор
скажет «ok». А на чистой копии (другой человек, другой сервер, CI) та же сборка выдаст
другие байты — и это увидят не здесь, а в живом сайте.

Что делает этот прибор. Берёт из git РОВНО закоммиченное (`git archive HEAD`) в пустой
каталог, собирает там `tools/build.py` и сверяет побайтно ВЕСЬ список публикации
(`publish-tree.manifest()` — тот же список, которым сайт выкладывается, включая картинки
и шрифты), а не только страницы. Ни один файл не исключён по имени каталога: именно
такой skip-лист однажды спрятал от сверки 91 файл из 107 (`live-bytes.py`).

Что прибор НЕ проверяет и говорит об этом вслух: если в дереве лежат незакоммиченные
правки источников, сравнивать нечего — чистая копия их не содержит, и любой вердикт
был бы ложью. Тогда прибор печатает ПРОПУСК и код 3, а не зелёное.

Контроль (`--control`). Три мутанта: испорченный байт в странице, испорченный байт в
картинке, удалённый шрифт. Прибор обязан назвать ровно этот файл в каждом случае;
мутант с картинкой доказывает, что сверка не ограничена текстом.

Код возврата: 0 — чистая сборка совпала с деревом, 1 — разошлась, 3 — проверить нельзя
(грязное дерево, нет git, сборка в копии упала).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Единственный файл, которому позволено быть грязным: это не исходник сборки, а реестр
# живой сверки ссылок, он обновляется каждым живым прогоном (метка времени замера).
ALLOWED_DIRTY = {"tools/links-last-seen.json"}


def published(root: Path) -> list[str]:
    """Список публикации по дереву `root` — из publish-tree, не копией."""
    spec = importlib.util.spec_from_file_location("publish_tree", root / "tools" / "publish-tree.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("tools/publish-tree.py не читается")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.set_root(root)
    return list(mod.manifest())


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hashes_of(root: Path, files: list[str]) -> dict[str, str]:
    out = {}
    for rel in files:
        p = root / rel
        out[rel] = sha(p) if p.is_file() else "(нет файла)"
    return out


def compare(expected: dict[str, str], tree: Path) -> list[str]:
    """Расхождения между снятыми хешами и деревом. Пусто — сборка совпала."""
    bad = []
    for rel, want in expected.items():
        p = tree / rel
        if not p.is_file():
            bad.append(f"{rel}: нет в дереве")
        elif sha(p) != want:
            bad.append(f"{rel}: байты разошлись")
    return sorted(bad)


def dirty_publish_inputs() -> list[str]:
    """Незакоммиченные правки, из-за которых сравнивать чистое дерево нечестно."""
    p = subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT),
                       capture_output=True, text=True)
    if p.returncode != 0:
        return ["(git status не отвечает)"]
    bad = []
    for line in p.stdout.splitlines():
        rel = line[3:].strip().strip('"')
        if not rel or rel in ALLOWED_DIRTY:
            continue
        bad.append(rel)
    return bad


def clean_checkout(dest: Path) -> None:
    """Ровно закоммиченное дерево: git archive HEAD, распакованный без оболочки."""
    p = subprocess.run(["git", "archive", "HEAD"], cwd=str(ROOT), capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("git archive не отдал дерево: " + p.stderr.decode("utf-8", "replace")[:200])
    with tarfile.open(fileobj=io.BytesIO(p.stdout)) as tf:
        tf.extractall(dest, filter="data")


def build_in(tree: Path) -> str:
    p = subprocess.run([sys.executable, "tools/build.py"], cwd=str(tree),
                       capture_output=True, text=True)
    if p.returncode != 0:
        return ((p.stdout or "") + (p.stderr or ""))[-400:]
    return ""


def run() -> int:
    bad = dirty_publish_inputs()
    if bad:
        print("ПРОПУСК: в дереве незакоммиченные правки — чистая копия их не содержит, "
              "вердикт был бы ложью")
        for rel in bad[:10]:
            print(f"  грязно: {rel}")
        return 3
    with tempfile.TemporaryDirectory(prefix="landing-repro-") as tmp:
        clean = Path(tmp) / "clean"
        clean.mkdir()
        clean_checkout(clean)
        err = build_in(clean)
        if err:
            print("ПРОПУСК: сборка чистой копии упала — сравнивать нечего")
            print("  " + err.splitlines()[-1] if err.splitlines() else "")
            return 3
        files = published(clean)
        expected = hashes_of(clean, files)
        diffs = compare(expected, ROOT)
        text = [f for f in files if not f.startswith(("img/", "fonts/"))]
        media = [f for f in files if f.startswith(("img/", "fonts/"))]
        if diffs:
            print(f"РАСХОЖДЕНИЙ {len(diffs)} из {len(files)}: чистая сборка не равна дереву")
            for line in diffs[:12]:
                print("  " + line)
            return 1
        print(f"ok: чистая копия HEAD собрана и совпала с деревом — файлов {len(files)} "
              f"(текст {len(text)}, медиа {len(media)}), расхождений 0")
        return 0


def control() -> int:
    """Три мутанта: страница, картинка, шрифт. Каждый обязан быть назван по имени."""
    with tempfile.TemporaryDirectory(prefix="landing-repro-ctl-") as tmp:
        clean = Path(tmp) / "clean"
        clean.mkdir()
        clean_checkout(clean)
        err = build_in(clean)
        if err:
            print(f"КОНТРОЛЬ НЕ ПРОВЕДЁН: сборка чистой копии упала — {err.splitlines()[-1] if err.splitlines() else ''}")
            return 3
        files = published(clean)
        expected = hashes_of(clean, files)
        page = next((f for f in files if f.endswith(".html")), None)
        image = next((f for f in files if f.startswith("img/") and f.lower().endswith((".png", ".jpg", ".webp"))), None)
        font = next((f for f in files if f.startswith("fonts/")), None)
        mutants = [("страница", page), ("картинка", image), ("шрифт", font)]
        caught = 0
        for name, rel in mutants:
            if rel is None:
                print(f"  мутант «{name}»: в списке публикации нет подходящего файла — мутант не построен")
                continue
            target = clean / rel
            original = target.read_bytes()
            try:
                if name == "шрифт":
                    target.unlink()
                else:
                    target.write_bytes(original + b"mutant")
                diffs = compare(expected, clean)
            finally:
                target.write_bytes(original)
            named = [d for d in diffs if d.startswith(rel + ":")]
            if named:
                caught += 1
                print(f"  ok  мутант «{name}» ({rel}) — поймал: {named[0]}")
            else:
                print(f"  ХУДО мутант «{name}» ({rel}) — прибор промолчал")
        total = sum(1 for _, rel in mutants if rel is not None)
        print(f"КОНТРОЛЬ: поймал {caught}/{total}")
        return 0 if caught == total else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Чистая копия репозитория собирается побайтно в то же дерево")
    ap.add_argument("--control", action="store_true", help="проверить сам прибор тремя мутантами")
    a = ap.parse_args()
    return control() if a.control else run()


if __name__ == "__main__":
    sys.exit(main())
