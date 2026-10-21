#!/usr/bin/env python3
"""Локализованные карточки превью (og:image) для лендинга UchiSamBot.

Один шаблон 1200x630 на все 9 языков: иконка слева, справа — название, подзаголовок
(foot.tag), строка возможностей (f1t · f2t · f5t) и ссылка t.me/UchiSamBot.
Тексты берутся ТОЛЬКО из src/locales/<lang>.json (уже выверенные переводы страницы) —
новых переводов скрипт не придумывает.

Почему: до 21.10.2026 у всех девяти языков был один английский og.png — при отправке
ссылки на /es/ или /hi/ в Telegram превью показывало английский текст (нарушение
правила владельца «у каждого языка свои картинки»). Старый og.png НЕ перезаписывается:
новые файлы называются og-<lang>.png, английская карточка — og-en.png.

Запуск:  python3 tools/og-cards.py [--langs es,pt] [--check]
Выход:   img/og-<lang>.png (1200x630) + tools/og-cards.lock.json (реестр отпечатков:
         текста словаря и самого PNG — свип сверяет его и ловит «карточка устарела»)
--check  только измерить существующие файлы (размер, разрешение, совпадение с реестром),
         ничего не рендерить.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from html import escape as html_escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOCALES = ROOT / "src" / "locales"
FONTS = ROOT / "fonts"
IMG = ROOT / "img"
LOCK = ROOT / "tools" / "og-cards.lock.json"
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]

W, H = 1200, 630

TEMPLATE = """<!doctype html>
<html lang="{lang}">
<meta charset="utf-8">
<style>
@font-face{{font-family:'Manrope';font-style:normal;font-weight:200 800;font-display:block;
  src:url("{fonts}/manrope-cyrillic-ext.woff2") format('woff2');unicode-range:U+0460-052F,U+1C80-1C8A,U+20B4,U+2DE0-2DFF,U+A640-A69F,U+FE2E-FE2F}}
@font-face{{font-family:'Manrope';font-style:normal;font-weight:200 800;font-display:block;
  src:url("{fonts}/manrope-cyrillic.woff2") format('woff2');unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:'Manrope';font-style:normal;font-weight:200 800;font-display:block;
  src:url("{fonts}/manrope-vietnamese.woff2") format('woff2');unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB}}
@font-face{{font-family:'Manrope';font-style:normal;font-weight:200 800;font-display:block;
  src:url("{fonts}/manrope-latin-ext.woff2") format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C4,U+2113,U+2C60-2C7F,U+A720-A7FF}}
@font-face{{font-family:'Manrope';font-style:normal;font-weight:200 800;font-display:block;
  src:url("{fonts}/manrope-latin.woff2") format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px}}
body{{
  background:linear-gradient(180deg,#E7F1FE 0%,#E1EEFE 55%,#DAE9FE 100%);
  font-family:'Manrope','Noto Sans Devanagari',-apple-system,'Segoe UI',Roboto,sans-serif;
  color:#14203A;display:flex;align-items:center;gap:78px;padding:0 64px 0 88px;
  -webkit-font-smoothing:antialiased;
}}
.icon{{width:220px;height:220px;flex:0 0 220px;display:block}}
.txt{{display:flex;flex-direction:column;align-items:flex-start;min-width:0}}
.name{{font-size:72px;font-weight:800;letter-spacing:-.02em;line-height:1.06}}
.tag{{font-size:38px;font-weight:700;color:#3C5AFE;line-height:1.2;margin-top:18px}}
.fit{{max-width:100%;white-space:nowrap}}
.desc{{font-size:28px;font-weight:500;color:#4A5974;line-height:1.3;margin-top:26px;
  max-width:780px}}
.desc .seg{{display:inline-block;white-space:nowrap}}
.desc .seg + .seg{{margin-left:.6em}}
.desc .seg:not(:last-child)::after{{content:"·";margin-left:.6em;color:#93A3BB}}
.link{{font-size:28px;font-weight:800;color:#229ED9;margin-top:42px;letter-spacing:.01em}}
</style>
<body>
  <img class="icon" src="{icon}" alt="">
  <div class="txt">
    <div class="name">UchiSamBot</div>
    <div class="tag fit" id="tag">{tag}</div>
    <div class="desc" id="desc">{desc}</div>
    <div class="link">t.me/UchiSamBot</div>
  </div>
<script>
// Подгонка: сначала уменьшаем кегль, если строка не влезает в колонку; для desc
// допускаем перенос на 2 строки, но не больше.
window.__fit = () => {{
  const box = document.querySelector('.txt');
  const avail = {W} - 88 - 220 - 78 - 64; // ширина текстовой колонки
  const tag = document.getElementById('tag');
  let size = 38;
  while (tag.scrollWidth > avail && size > 24) {{
    size -= 1; tag.style.fontSize = size + 'px';
  }}
  const desc = document.getElementById('desc');
  desc.style.maxWidth = avail + 'px';
  let ds = 28;
  while (desc.scrollHeight > 2 * Math.round(ds * 1.3) + 2 && ds > 20) {{
    ds -= 1; desc.style.fontSize = ds + 'px';
  }}
  return {{avail, tagSize: size, descSize: ds,
           tagW: tag.scrollWidth, descH: desc.scrollHeight,
           blockH: document.querySelector('.txt').getBoundingClientRect().height}};
}};
</script>
</body>
</html>
"""


def text_sha(lang: str) -> str:
    """Отпечаток текста карточки — ровно те четыре строки, что попадают на картинку."""
    d = json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
    s = "\x1f".join(str(d[k]) for k in ("foot.tag", "f1t", "f2t", "f5t"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def write_lock(langs: list[str]) -> None:
    """Реестр для свипа: text_sha + img_sha.

    Зачем: карточки — готовые PNG в git, сборка их не перерисовывает. Если завтра
    поправить строку в src/locales, картинка останется старой и превью в Telegram
    будет врать. Реестр делает такой дрейф машинно-видимым.
    """
    try:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        if not isinstance(lock, dict):
            lock = {}
    except Exception:
        lock = {}
    for lang in langs:
        p = IMG / f"og-{lang}.png"
        lock[lang] = {"text_sha": text_sha(lang), "img_sha": file_sha(p), "bytes": p.stat().st_size}
    LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"реестр: tools/og-cards.lock.json ({len(langs)} языков)")


def strings(lang: str) -> tuple[str, str]:
    """Подзаголовок и HTML-строка возможностей.

    Каждая возможность — отдельный неразрывный сегмент: перенос разрешён только МЕЖДУ
    возможностями, поэтому предлог не отрывается от своего слова (в ru/es обычный
    перенос рвал «Задачи с / фото»).
    """
    d = json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
    tag = html_escape(d["foot.tag"])
    segs = "\n".join(f'<span class="seg">{html_escape(d[k])}</span>' for k in ("f1t", "f2t", "f5t"))
    return tag, segs


def render(langs: list[str]) -> int:
    from playwright.sync_api import sync_playwright

    IMG.mkdir(exist_ok=True)
    meta = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for lang in langs:
            tag, desc = strings(lang)
            html = TEMPLATE.format(lang=lang, fonts=FONTS.as_uri(), icon=(IMG / "logo-512.png").as_uri(),
                                   tag=tag, desc=desc, W=W, H=H)
            tmp = Path(tempfile.mkdtemp(prefix="ogcard-")) / f"{lang}.html"
            tmp.write_text(html, encoding="utf-8")
            page.goto(tmp.as_uri())
            page.wait_for_function("document.fonts.status === 'loaded'", timeout=20000)
            page.wait_for_timeout(150)
            m = page.evaluate("window.__fit()")
            shot = IMG / f"og-{lang}.png"
            try:
                page.screenshot(path=str(shot))
            except Exception:
                # редкий сбой композитора headless при точном совпадении вьюпорта и тела
                page.wait_for_timeout(400)
                page.screenshot(path=str(shot), clip={"x": 0, "y": 0, "width": W, "height": H})
            meta[lang] = m
            print(f"{lang}: tag {m['tagSize']}px/{m['tagW']}px  desc {m['descSize']}px/{m['descH']}px  "
                  f"block {m['blockH']:.0f}px -> img/og-{lang}.png "
                  f"{(IMG / f'og-{lang}.png').stat().st_size} B")
        browser.close()
    if any(m["tagW"] > m["avail"] for m in meta.values()):
        print("ОШИБКА: подзаголовок не влез даже на минимальном кегле", file=sys.stderr)
        return 1
    if any(m["descH"] > 2 * (m["descSize"] * 1.3) + 2 for m in meta.values()):
        print("ОШИБКА: описание заняло больше двух строк", file=sys.stderr)
        return 1
    write_lock(langs)
    return 0


def check() -> int:
    from PIL import Image

    bad = 0
    for lang in LANGS:
        p = IMG / f"og-{lang}.png"
        if not p.exists():
            print(f"НЕТ   {p.name}")
            bad += 1
            continue
        with Image.open(p) as im:
            size = im.size
        ok = size == (W, H) and p.stat().st_size > 15000
        try:
            lock = json.loads(LOCK.read_text(encoding="utf-8"))
            ent = lock.get(lang) or {}
            lock_ok = ent.get("text_sha") == text_sha(lang) and ent.get("img_sha") == file_sha(p)
        except Exception:
            lock_ok = False
        ok = ok and lock_ok
        print(f"{'OK   ' if ok else 'ПЛОХО'} {p.name} {size[0]}x{size[1]} {p.stat().st_size} B"
              + ("" if lock_ok else "  ДРЕЙФ: карточка не совпадает с текстом словаря — перерендерить"))
        bad += 0 if ok else 1
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="", help="через запятую; по умолчанию все 9")
    ap.add_argument("--check", action="store_true", help="только проверить готовые файлы")
    a = ap.parse_args()
    if a.check:
        return check()
    langs = [x.strip() for x in a.langs.split(",") if x.strip()] or LANGS
    unknown = [x for x in langs if x not in LANGS]
    if unknown:
        print(f"неизвестные языки: {unknown}", file=sys.stderr)
        return 2
    return render(langs)


if __name__ == "__main__":
    raise SystemExit(main())
