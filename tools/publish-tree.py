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
  --control        доказать, что умеет краснеть: пять заведомо кривых деревьев,
                   каждое обязано покраснеть СВОИМ сообщением (31.10.2026);
  --root DIR       проверить другое дерево (этим пользуется --control);
  --stage DIR      разложить список в DIR (для ветки публикации);
  --list           напечатать список.

Проверка «ничего лишнего» ловит обратное: файл, который лежит в корне и
отдаётся, но в список не входит. Проверка «ничего не забыли» ловит переезд на
отдельную ветку, который унёс бы с собой половину картинок.

Пятая проверка (24.10.2026). Список проверял себя: «лишнего нет» значило «в
списке нет файлов мастерской», но НИКТО не спрашивал, нужен ли сайту каждый
файл из списка. Каталоги `img/` и `fonts/` уезжают целиком, поэтому всё, что
туда положено, становится сайтом молча. Так уехали четыре скриншота 16:9 для
сторонних каталогов (`img/screen1..4.png`, 1,07 МБ — сделаны для загрузки в
PeerPush/LaunchIgniter, на сайте нет ни одной ссылки) и два макета старой
вёрстки (`img/shot4.webp`, `img/shot4-ru.webp` — четвёртый кадр прежней
карусели, интерфейс до правки меню). Теперь каждый опубликованный файл обязан
быть НАЗВАН каким-нибудь опубликованным текстом (html/md/txt/xml); исключения
перечислены поимённо в PUBLIC_UNLINKED, каждое — с причиной.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
BASE = json.loads((ROOT / "tools" / "site.json").read_text(encoding="utf-8"))["base"]
LANGS = ["ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]


def set_root(p: Path) -> None:
    """Переключить корень проверки (нужен контролю: он гоняет прибор по мутанту).

    До 31.10.2026 корень был вморожен в константу на импорте, и единственный
    способ проверить прибор на заведомо кривом дереве — скопировать сам скрипт
    внутрь мутанта. Такой контроль проверял бы копию, а не тот файл, что лежит
    в репозитории.
    """
    global ROOT, BASE
    ROOT = Path(p).resolve()
    site = ROOT / "tools" / "site.json"
    if site.is_file():
        BASE = json.loads(site.read_text(encoding="utf-8"))["base"]


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
    "demo/*.json", "evidence/", ".gitignore", "submission-kit/",
    # 31.10.2026: `docs/council-20261015.md` — разбор решений совета, файл лежит в
    # отслеживаемых и при публикации КОРНЯ уезжал бы по адресу /docs/. Живьём его
    # нет (сайт собирается с ветки публикации), но модель «Pages отдаёт всё, что в
    # git» обязана называть каждый такой файл, иначе следующий переезд на корень
    # увезёт его молча. Решение: docs/ объявлен мастерской поимённо, а не забыт.
    "docs/",
]

# Служебные каталоги, которые не отдаёт даже Pages: их существование не считается
# публикацией, и в контроль полноты они не входят.
LOCAL_ONLY = (".git", "__pycache__", ".shots-work")


# Публикуется, но ни одной страницей не называется — и это правильно. Каждая
# строка здесь отвечает на вопрос «кто просит этот файл, если не страница».
PUBLIC_UNLINKED = {
    ".nojekyll": "флаг GitHub Pages: без него Pages прогоняет Jekyll",
    "210a46fb97554124948a7b1a74a15d5f.txt": "ключ IndexNow: поисковик читает его по адресу",
    "robots.txt": "робот берёт его по соглашению, ссылок на него нет",
    "404.html": "его отдаёт хост на несуществующий адрес, со страниц не линкуется",
}


def manifest() -> list[str]:
    """Список того, что обязано быть сайтом — независимо от того, что сейчас на диске.

    До 31.10.2026 корневые файлы попадали в список только если существовали
    (`if (ROOT / f).exists()`), поэтому проверка «всё из списка существует» не
    могла покраснеть: пропавший llms.txt или robots.txt просто выпадал из списка,
    и дерево оставалось зелёным. Список — это намерение, а не наблюдение; наличие
    проверяет `check()`, раскладку — `stage()` (и она теперь назовёт пропажу).
    """
    out = list(PUBLIC_FILES)
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


def is_backstage(rel: str) -> bool:
    """Файл объявлен мастерской: имя целиком, каталог с «/» или шаблон с «*»."""
    for pat in BACKSTAGE:
        if pat.endswith("/"):
            if rel.startswith(pat):
                return True
        elif fnmatch.fnmatchcase(rel, pat) or rel == pat:
            return True
    return False


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
        if p.suffix not in (".html", ".md", ".txt", ".xml") or not p.is_file():
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


def unlinked(files: list[str]) -> list[tuple[str, int]]:
    """Файлы публикации, которые не называет ни один опубликованный текст.

    Названный файл не обязан быть ссылкой: шрифт живёт в `url(...)` внутри CSS,
    макет — в `poster=`, карточка og — в `og:image`. Достаточно, чтобы имя
    встретилось в опубликованном html/md/txt/xml: это доказывает, что файл
    кому-то нужен. Исключения — PUBLIC_UNLINKED.
    """
    texts = {f: (ROOT / f).read_text(encoding="utf-8", errors="replace")
             for f in files
             if Path(f).suffix in (".html", ".md", ".txt", ".xml") and (ROOT / f).is_file()}
    out = []
    for f in files:
        if f in texts or f in PUBLIC_UNLINKED or not (ROOT / f).is_file():
            continue
        name = Path(f).name
        if not any(name in body for body in texts.values()):
            size = (ROOT / f).stat().st_size if (ROOT / f).is_file() else 0
            out.append((f, size))
    return out


def check() -> int:
    pub = manifest()
    back = backstage_files()
    problems = []
    checks = 0

    # 1) всё из списка существует
    for f in pub:
        checks += 1
        if not (ROOT / f).is_file():
            problems.append(f"нет файла из списка: {f}")

    # 2) граница сайта и мастерской — в ОБЕ стороны.
    #
    # До 31.10.2026 здесь стояла проверка, которая не могла покраснеть ни на одном
    # дереве: `backstage_files()` по определению возвращает `served - pub`, а цикл
    # проверял `if f in pub` внутри этого списка. Условие ложно всегда, то есть
    # «мастерская не попала в список» было зелёным даже если в `pub` лежал весь
    # `tools/`. Теперь один и тот же предикат спрашивают с двух сторон: файл,
    # который хост отдаёт, обязан быть либо сайтом, либо объявленной мастерской;
    # файл, объявленный сайтом, не имеет права быть мастерской.
    for f in back:
        checks += 1
        if not is_backstage(f):
            problems.append(f"файл отдаётся, но не объявлен ни сайтом, ни мастерской: {f}")
    for f in pub:
        checks += 1
        if is_backstage(f):
            problems.append(f"мастерская объявлена сайтом: {f}")

    # 3) каждая внутренняя ссылка ведёт на файл из списка
    pubset = set(pub)
    dangling = []
    refs = references(pub)
    for src, url, tgt in refs:
        checks += 1
        cand = tgt
        if cand.endswith("/") or cand == "":
            cand = cand + "index.html"
        if cand not in pubset:
            dangling.append(f"{src}: {url} -> {cand}")
    problems += [f"ссылка на файл вне публикации: {d}" for d in dangling[:20]]

    # 4) обратный счёт: страница не смотрит в мастерскую
    for src, url, tgt in refs:
        checks += 1
        for b in ("tools/", "src/", "demo/captions", "index-src.html", "README.md", "evidence/", "docs/"):
            if tgt.startswith(b):
                problems.append(f"страница ссылается на мастерскую: {src}: {url}")

    # 5) у каждого опубликованного файла есть читатель (24.10.2026)
    lost = unlinked(pub)
    for f, size in lost:
        checks += 1
        problems.append(f"файл публикуется, но сайт его не называет: {f} ({size // 1024} КБ)")
    checks += len(pub) - len(lost)

    unlinked_by_decision = len(set(PUBLIC_UNLINKED) & set(pub))
    size = sum((ROOT / f).stat().st_size for f in pub if (ROOT / f).is_file())
    print(f"публикация: {len(pub)} файлов, {size / 1048576:.1f} МБ")
    print(f"названо страницами: {len(pub) - len(lost) - unlinked_by_decision} файлов, "
          f"без ссылки по решению: {unlinked_by_decision}, без читателя: {len(lost)}")
    print(f"мастерская (в публикацию не идёт): {len(back)} файлов")
    for b in back:
        print(f"   - {b}")
    print(f"внутренних ссылок проверено: {len(refs)}")
    print(f"CHECKS: {checks}, FAILED: {len(problems)}")
    if problems:
        print("ПРОВАЛ:")
        for p in problems:
            print("  " + p)
        return 1
    print("ПРОВЕРЕНО: список полон, лишнего нет, все внутренние ссылки внутри списка")
    return 0


def stage(dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    missing = []
    staged = 0
    for f in manifest():
        src = ROOT / f
        if not src.is_file():
            missing.append(f)
            continue
        target = dest / f
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        staged += 1
    print(f"разложено: {staged} файлов -> {dest}")
    if missing:
        # Список — намерение: молча разложить меньше, чем обещано, нельзя.
        print(f"НЕ РАЗЛОЖЕНО ({len(missing)}): " + ", ".join(missing[:10]))
        return 1
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


def _synthetic(root: Path) -> None:
    """Чистое мини-дерево с тем же набором файлов, что у сайта, но заглушками."""
    root.mkdir(parents=True, exist_ok=True)
    names = [f for f in PUBLIC_FILES if f.endswith((".html", ".md", ".txt", ".xml"))]
    body = "".join(f"<p>{f}</p>" for f in names) + "<!-- .nojekyll -->"
    (root / "index.html").write_text(
        '<html><body><img src="img/pic.png"><a href="fonts/f.ttf">f</a>'
        '<a href="privacy.html">p</a><a href="terms.html">t</a>'
        f"{body}</body></html>", encoding="utf-8")
    for f in names:
        if f != "index.html":
            (root / f).write_text(f"# {f}\n", encoding="utf-8")
    (root / ".nojekyll").write_text("", encoding="utf-8")
    (root / "sitemap.xml").write_text("<urlset></urlset>", encoding="utf-8")
    (root / "img").mkdir(exist_ok=True)
    (root / "img" / "pic.png").write_bytes(b"png")
    (root / "fonts").mkdir(exist_ok=True)
    (root / "fonts" / "f.ttf").write_bytes(b"ttf")
    for lang in LANGS:
        d = root / lang
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(
            '<html><body><img src="../img/pic.png"><a href="../index.html">h</a></body></html>',
            encoding="utf-8")
        (d / "index.html.md").write_text("# x\n\n[home](../index.html)\n", encoding="utf-8")


# мутант: (имя, что ломаем, чем прибор обязан покраснеть)
def _mutants() -> list[tuple[str, str, Callable[[Path], None]]]:
    def missing(d: Path) -> None:
        (d / "llms.txt").unlink()

    def undeclared(d: Path) -> None:
        (d / "stray-notes.txt").write_text("заметки\n", encoding="utf-8")

    def orphan(d: Path) -> None:
        (d / "img" / "orphan.png").write_bytes(b"png")

    def dangling(d: Path) -> None:
        p = d / "index.html"
        p.write_text(p.read_text(encoding="utf-8") + '<a href="gone.html">g</a>', encoding="utf-8")

    def workshop(d: Path) -> None:
        (d / "tools").mkdir(exist_ok=True)
        (d / "tools" / "secret.py").write_text("x = 1\n", encoding="utf-8")
        p = d / "index.html"
        p.write_text(p.read_text(encoding="utf-8") + '<a href="tools/secret.py">s</a>',
                     encoding="utf-8")

    return [
        ("файл из списка пропал", "нет файла из списка", missing),
        ("отдаётся файл, которого нет ни в сайте, ни в мастерской",
         "не объявлен ни сайтом, ни мастерской", undeclared),
        ("в публикации лежит картинка, которую никто не называет",
         "сайт его не называет", orphan),
        ("страница ссылается на несуществующий файл",
         "ссылка на файл вне публикации", dangling),
        ("страница ссылается в мастерскую", "ссылается на мастерскую", workshop),
    ]


def control() -> int:
    """Пять мутантов: прибор обязан покраснеть на каждом и по СВОЕЙ причине.

    Зачем (31.10.2026). Пять проверок этого файла ни разу не были увидены
    красными: дерево в репозитории чистое, значит «зелено» могло значить и
    «проверено», и «проверка мертва». Вторая проверка была ровно такой —
    тавтологией по построению. Контроль подаёт прибору заведомо кривые деревья и
    требует не просто ненулевой код, а ту строку, которую ждёт именно этот дефект:
    код возврата 1 от чужой причины тоже считается «не поймал».
    """
    base = Path(tempfile.mkdtemp(prefix="publish-tree-base-"))
    caught = 0
    mutants = _mutants()
    try:
        _synthetic(base)
        rc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--root", str(base)],
                            capture_output=True, text=True, timeout=120)
        clean = rc.returncode == 0
        print(f"  чистое дерево: {'зелёное' if clean else 'КРАСНОЕ (прибор шумит)'} — "
              f"{'ok' if clean else rc.stdout[-400:]}")
        if not clean:
            return 1
        for i, (title, marker, mutate) in enumerate(mutants, 1):
            d = base.parent / f"publish-tree-mutant-{i}"
            shutil.copytree(base, d)
            mutate(d)
            r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--root", str(d)],
                               capture_output=True, text=True, timeout=120)
            ok = r.returncode == 1 and marker in r.stdout
            caught += 1 if ok else 0
            why = "поймал" if ok else (
                "ПРОСМОТРЕЛ" if r.returncode == 0 else "покраснел по чужой причине")
            print(f"  {i}. {title}: {why}")
            shutil.rmtree(d, ignore_errors=True)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    total = len(mutants)
    print(f"КОНТРОЛЬ: поймал {caught} из {total}")
    if caught != total:
        print("ПРОВАЛ: прибор не доказал, что умеет краснеть")
        return 1
    print("ПРИБОР ДОКАЗАН: каждое из пяти нарушений ловится своим сообщением")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="список публикации: что именно уезжает в свет")
    ap.add_argument("--check", action="store_true", help="проверить дерево (по умолчанию)")
    ap.add_argument("--control", action="store_true", help="доказать, что прибор умеет краснеть")
    ap.add_argument("--root", metavar="DIR", help="корень другого дерева (для контроля)")
    ap.add_argument("--stage", metavar="DIR")
    ap.add_argument("--verify-served", metavar="DIR")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.root:
        set_root(Path(a.root))
    if a.list:
        for f in manifest():
            print(f)
        return 0
    if a.control:
        return control()
    if a.stage:
        return stage(Path(a.stage))
    if a.verify_served:
        return verify_served(Path(a.verify_served))
    return check()


if __name__ == "__main__":
    sys.exit(main())
