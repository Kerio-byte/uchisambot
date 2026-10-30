#!/usr/bin/env python3
"""check-weight.py — вес страницы и дисциплина тяжёлых файлов.

Повод (30.10.2026). Технический блок смотрел ссылки, шапки, числа и совпадение
живого сайта с деревом, но вес страницы не мерил никто с 22.10: HTML за десять
дней вырос с 45 до 114 КБ (работа над обещаниями), а на странице появился ролик
весом 450 КБ на язык. Пока вес не измеряется прибором, «страница стала тяжелее»
замечают только по жалобе живого человека. Здесь пять клауз:

  1) первый экран — сумма gzip(HTML) + то, что браузер тянет ДО прокрутки:
     <link rel=preload>, картинки без loading="lazy", постер ролика. Потолок
     осознанный: 130 КБ, при живых 100–112 КБ остаётся запас на мелкую правку,
     но не на «вставили фотографию на 800 КБ».

  2) HTML в gzip. Сырой HTML врёт: страница 114 КБ отдаётся как 36 КБ, потому что
     GitHub Pages жмёт на лету. Считается именно то, что едет по сети.

  3) нетерпеливые картинки. Всё, что ниже первого экрана, обязано иметь
     loading="lazy"; иначе телефон качает десять скриншотов, которых человек
     ещё не видел. Исключение одно — логотип в шапке.

  4) потолки на файл: ролик 600 КБ, картинка 150 КБ, шрифт 40 КБ. Это не «красиво»,
     это граница, за которой 3G-абонент в Индии закрывает вкладку.

  5) медиа принадлежит языку. У каждого языка свои постер и ролик (правило
     владельца 15.10). Страница не имеет права ссылаться на чужой файл — самая
     тихая поломка: перевели текст, а ролик оставили английский.

Отдельно, без провала: файлы img/, на которые никто не ссылается (мусор в
публикации; сегодня таких нет — проверка ловит будущий).

Запуск:
  python3 tools/check-weight.py            # меряет, печатает таблицу
  python3 tools/check-weight.py --control   # прибор обязан покраснеть: потолок 1 байт
"""
from __future__ import annotations

import gzip
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
PAGES = [(l, "index.html" if l == "en" else f"{l}/index.html") for l in LANGS]
LEGAL = [("privacy", "privacy.html"), ("terms", "terms.html")]

BUDGET = {
    "first_view": 130_000,   # байт на первом экране (gzip html + нетерпеливое)
    "html_gzip": 45_000,     # байт html в gzip
    "eager_img_bytes": 8_000,
    "eager_img_count": 2,
    "video": 600_000,        # петля героя: грузится по нажатию, но должна быть лёгкой
    "download": 1_500_000,   # полное демо из llms.txt: человек качает осознанно
    "image": 150_000,
    "font": 80_000,          # деванагари (70 КБ) честно больше латиницы (25 КБ)
}

TAG_IMG = re.compile(r"<img\b[^>]*>", re.I)
TAG_VIDEO = re.compile(r"<video\b[^>]*>", re.I)
TAG_PRELOAD = re.compile(r'<link\b[^>]*\brel="preload"[^>]*>', re.I)
ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')


def strip_noise(html: str) -> str:
    """Убрать комментарии и содержимое <script>: там встречаются примеры тегов
    (в index.html пять раз написан `<video>` внутри объяснения кода)."""
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)


def attrs(tag: str) -> dict:
    return {k.lower(): v for k, v in ATTR.findall(tag)}


def resolve(rel: str, base: Path) -> Path | None:
    u = rel.split("?")[0].split("#")[0]
    if not u or u.startswith(("http://", "https://", "//", "data:", "mailto:", "tel:")):
        return None
    p = (ROOT / u.lstrip("/")) if u.startswith("/") else (base / u)
    return p.resolve()


def first_view(page: Path, html: str) -> tuple[int, list[tuple[int, Path]]]:
    """Байты, которые браузер тянет до прокрутки. Возвращает (сумма, список)."""
    base = page.parent
    body = strip_noise(html)
    eager: list[tuple[int, Path]] = []
    for tag in TAG_PRELOAD.finditer(body):
        p = resolve(attrs(tag.group(0)).get("href", ""), base)
        if p and p.exists():
            eager.append((p.stat().st_size, p))
    for tag in TAG_IMG.finditer(body):
        a = attrs(tag.group(0))
        if a.get("loading") == "lazy":
            continue
        srcs = [a.get("src", "")]
        if a.get("srcset"):
            srcs += [part.strip().split(" ")[0] for part in a["srcset"].split(",")]
        for s in srcs:
            p = resolve(s, base)
            if p and p.exists():
                eager.append((p.stat().st_size, p))
    for tag in TAG_VIDEO.finditer(body):
        a = attrs(tag.group(0))
        p = resolve(a.get("poster", ""), base)
        if p and p.exists():
            eager.append((p.stat().st_size, p))
    seen, uniq = set(), []
    for size, p in eager:
        if p in seen:
            continue
        seen.add(p)
        uniq.append((size, p))
    return sum(s for s, _ in uniq), uniq


def lang_media_fails(body: str, lang: str, base: Path) -> list[str]:
    """Клауза 5: страница языка не ссылается на медиа другого языка."""
    out = []
    for r in re.findall(r'(?:src|poster)="([^"]+)"', body):
        p = resolve(r, base)
        if p is None or not p.exists():
            continue
        name = p.name
        if "/demo/" not in str(p) and "demo-poster" not in name:
            continue
        for other in LANGS:
            if other == lang:
                continue
            if re.search(rf"-{other}(?:-[\w]+)?\.(?:mp4|webp|png)$", name):
                out.append(f"{lang}: ссылается на чужой файл языка {other}: {name}")
    return out


def main(argv: list[str]) -> int:
    control = "--control" in argv
    budget = dict(BUDGET)
    if control:
        budget["first_view"] = 1  # прибор обязан это увидеть
    fails: list[str] = []
    rows = []


    for lang, rel in PAGES + [(n, p) for n, p in LEGAL]:
        path = ROOT / rel
        html = path.read_text(encoding="utf-8")
        raw = len(html.encode("utf-8"))
        gz = len(gzip.compress(html.encode("utf-8"), 9))
        fv, eager = first_view(path, html)
        rows.append((lang, raw, gz, fv, len(eager)))

        if lang in LANGS and gz > budget["html_gzip"]:
            fails.append(f"{lang}: html {gz} Б gzip > {budget['html_gzip']}")
        if fv > budget["first_view"]:
            top = ", ".join(f"{p.relative_to(ROOT)} {s}" for s, p in sorted(eager, reverse=True)[:3])
            fails.append(f"{lang}: первый экран {fv} Б > {budget['first_view']} Б ({top})")

        body = strip_noise(html)
        imgs = [attrs(m.group(0)) for m in TAG_IMG.finditer(body)]
        eager_imgs = [a for a in imgs if a.get("loading") != "lazy"]
        eager_bytes = 0
        for a in eager_imgs:
            p = resolve(a.get("src", ""), path.parent)
            if p is not None and p.exists():
                eager_bytes += p.stat().st_size
        if len(eager_imgs) > budget["eager_img_count"]:
            fails.append(f"{lang}: {len(eager_imgs)} картинок без loading=lazy "
                         f"(> {budget['eager_img_count']})")
        if eager_bytes > budget["eager_img_bytes"]:
            fails.append(f"{lang}: нетерпеливые картинки {eager_bytes} Б > {budget['eager_img_bytes']}")

        # 5) медиа принадлежит языку
        if lang in LANGS:
            fails.extend(lang_media_fails(body, lang, path.parent))

    # потолки на файл. Потолок — про то, что браузер обязан скачать, чтобы страница
    # показалась; полное демо (1 МБ), которое человек качает по своей воле из llms.txt,
    # в этот потолок не входит — у него отдельная, более широкая граница.
    embedded = set()
    for lang, rel in PAGES:
        body = strip_noise((ROOT / rel).read_text(encoding="utf-8"))
        for m in re.finditer(r'<(?:video|source)\b[^>]*\bsrc="([^"]+)"', body, re.I):
            p = resolve(m.group(1), (ROOT / rel).parent)
            if p:
                embedded.add(p)
    for p in sorted(ROOT.glob("demo/*.mp4")):
        limit = budget["video"] if p.resolve() in embedded else budget["download"]
        if p.stat().st_size > limit:
            fails.append(f"ролик {p.relative_to(ROOT)} {p.stat().st_size} Б > {limit}")
    for pattern, limit, kind in (("img/*.webp", budget["image"], "картинка"),
                                 ("img/*.png", budget["image"], "картинка"),
                                 ("fonts/*.woff2", budget["font"], "шрифт")):
        for p in sorted(ROOT.glob(pattern)):
            if p.stat().st_size > limit:
                fails.append(f"{kind} {p.relative_to(ROOT)} {p.stat().st_size} Б > {limit}")

    print(f"{'page':9} {'html':>7} {'gz':>6} {'1-й экран':>10} {'файлов':>7}")
    for lang, raw, gz, fv, n in rows:
        print(f"{lang:9} {raw:7} {gz:6} {fv:10} {n:7}")

    used = set()
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".html", ".md", ".xml", ".txt", ".json", ".css", ".js") \
                and ".git" not in p.parts:
            used.add(p)
    blob = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in used)
    orphans = [p for p in (ROOT / "img").rglob("*") if p.is_file() and p.name not in blob]
    if orphans:
        print("\nмусор в img/ (никто не ссылается):")
        for p in orphans:
            print(f"  {p.stat().st_size:7} {p.relative_to(ROOT)}")
        fails.append(f"img/: {len(orphans)} файлов без ссылок")

    if control:
        ok = any("первый экран" in f for f in fails)
        probe = ('<video poster="img/demo-poster-uk.webp">'
                 '<source src="demo/uchiambot-demo-web-uk.mp4"></video>')
        caught_lang = bool(lang_media_fails(probe, "ru", ROOT))
        print(f"\nКОНТРОЛЬ: вес — {'поймал' if ok else 'НЕ ПОЙМАЛ'}; "
              f"чужой язык — {'поймал' if caught_lang else 'НЕ ПОЙМАЛ'}")
        return 0 if (ok and caught_lang) else 1

    if fails:
        print(f"\nПРОВАЛЕНО: {len(fails)}")
        for f in fails[:20]:
            print("  - " + f)
        return 1
    print("\nЧИСТО: вес, ленивость, потолки и язык медиа — все клаузы пройдены")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
