#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Картинки для форм сторонних площадок — 4 карточки 1920×1080 (16:9).

Зачем отдельный генератор (24.10.2026). В `submission-kit/` лежали четыре PNG от
15.10.2026: их загружают файлом в формы PeerPush / OpenHunts / LaunchIgniter и в
галерею Product Hunt. На них было написано «First 5 breakdowns free» — бот даёт
ДВЕ (FREE_TRIALS = 2, tools/prices.json, страница говорит «First 2» в пяти
местах) — и «Works in Russian and English / One bot, two languages», хотя бот и
сайт отвечают на девяти. Меню бота рисовалось шестью кнопками (с 23.10 их семь).
Проверить это было нечем: файлы лежат ВНЕ публикуемого дерева, свип видел только
«четыре файла вне страниц, оставлены осознанно».

Что делает. Собирает четыре карточки из ТЕХ ЖЕ картинок, что показывает страница
(img/shot1..3.webp + scenes/shot4.webp), а подписи берёт из словаря страницы
(src/locales/en.json) и справочников (tools/prices.json — число бесплатных
разборов, LABELS в tools/build.py — названия девяти языков). Руками не пишется
ни одна строка: правишь словарь — перегенерируешь.

Рядом кладёт `submission-kit/manifest.json`: sha256 картинок, ровно нарисованные
строки, число бесплатных разборов и языков, sha256 входов. Проверка (`--check`,
её же зовёт свип) краснеет, если: байты не совпали с манифестом; манифест
разошёлся с prices.json или словарём; входы новее манифеста («текст поправили,
картинку не перерисовали»); размер не 1920×1080; в манифесте/README остались
старые обещания («First 5», «two languages», «Russian and English»).

Запуск:
  python3 tools/submission-kit.py            # собрать и записать в submission-kit/
  python3 tools/submission-kit.py --check    # только сверить, ничего не писать
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "submission-kit"
MANIFEST = KIT / "manifest.json"
LOCALES = ROOT / "src" / "locales"
PRICES = ROOT / "tools" / "prices.json"
BUILD = ROOT / "tools" / "build.py"
FONTS = ROOT / "fonts"
INTER = ROOT / "tools" / "shots-gen" / "assets" / "fonts"

# 15.10.2026 — эти файлы уезжали в формы; порядок и смысл кадров сохранён.
PAGES = {
    "1": ROOT / "img" / "shot1.webp",
    "2": ROOT / "img" / "shot2.webp",
    "3": ROOT / "img" / "shot3.webp",
    "4": ROOT / "tools" / "shots-gen" / "scenes" / "shot4.webp",
}
OUT = {f"screen{i}.png": i for i in "1234"}

STALE = ("First 5", "5 breakdowns", "five free", "two languages",
         "Russian and English")

CSS = """
@font-face{font-family:'Kit Latin';font-weight:100 900;font-display:block;
  src:url('__INTER_LATIN__') format('woff2');}
@font-face{font-family:'Kit Latin';font-weight:100 900;font-display:block;
  src:url('__INTER_LATIN_EXT__') format('woff2');
  unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C4,U+2113,U+2C60-2C7F,U+A720-A7FF;}
@font-face{font-family:'Kit Latin';font-weight:100 900;font-display:block;
  src:url('__INTER_VI__') format('woff2');
  unicode-range:U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+1EA0-1EF9,U+20AB;}
@font-face{font-family:'Kit Cyr';font-weight:200 800;font-display:block;
  src:url('__LANGS_CYR__') format('woff2');unicode-range:__RANGE_CYR__;}
@font-face{font-family:'Kit Dev';font-weight:200 800;font-display:block;
  src:url('__LANGS_DEV__') format('woff2');unicode-range:__RANGE_DEV__;}
@font-face{font-family:'Kit Viet';font-weight:200 800;font-display:block;
  src:url('__LANGS_VI__') format('woff2');unicode-range:__RANGE_VI__;}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden}
body{background:#F7FAFF;color:#14203A;
  font-family:'Kit Viet','Kit Cyr','Kit Dev','Kit Latin',sans-serif;
  -webkit-font-smoothing:antialiased}
.stage{position:relative;width:1920px;height:1080px;overflow:hidden;
  background:linear-gradient(122deg,#FFFFFF 0%,#F7FAFF 46%,#EAF0FF 100%)}
.glow{position:absolute;right:-220px;top:-260px;width:1080px;height:1080px;border-radius:50%;
  background:radial-gradient(circle at 50% 50%,rgba(61,90,254,.20) 0%,rgba(61,90,254,0) 62%)}
.glow2{position:absolute;left:-260px;bottom:-420px;width:900px;height:900px;border-radius:50%;
  background:radial-gradient(circle at 50% 50%,rgba(79,195,247,.18) 0%,rgba(79,195,247,0) 64%)}
.left{position:absolute;left:120px;top:96px;width:1080px}
.brand{display:flex;align-items:center;gap:18px;margin-bottom:56px}
.brand img{width:70px;height:70px;display:block}
.brand span{font-size:44px;font-weight:800;letter-spacing:-.5px}
h1{font-size:80px;line-height:1.06;letter-spacing:-2.2px;font-weight:800;max-width:1020px}
.sub{margin-top:30px;font-size:33px;line-height:1.45;color:#50617F;max-width:980px}
.chips{display:flex;flex-wrap:wrap;gap:14px;margin-top:40px}
.chip{display:inline-flex;align-items:center;gap:12px;font-size:26px;font-weight:700;
  color:#2338A8;background:#FFFFFF;border:1px solid #D8E2F5;border-radius:999px;padding:14px 26px}
.chip i{width:12px;height:12px;border-radius:50%;background:#3D5AFE;display:block}
.foot{position:absolute;left:120px;bottom:88px;display:flex;align-items:center;gap:16px}
.tg{width:44px;height:44px;border-radius:50%;background:#3D5AFE;color:#fff;font-weight:800;
  font-size:24px;display:flex;align-items:center;justify-content:center}
.foot b{font-size:32px;font-weight:800;letter-spacing:-.3px;color:#3D5AFE}
.foot em{font-style:normal;font-size:26px;color:#7A8AA6;margin-left:6px}
.shot{position:absolute;left:1338px;top:40px;width:462px;height:1000px;
  border-radius:46px;overflow:hidden;background:#fff;
  box-shadow:0 40px 90px rgba(20,40,100,.20),0 4px 14px rgba(20,40,100,.10);
  border:1px solid #E3EAF7}
.shot img{width:462px;height:1000px;display:block;object-fit:cover;object-position:top center}
"""

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>__TITLE__</title>
<style>__CSS__</style></head>
<body><div class="stage">
  <div class="glow"></div><div class="glow2"></div>
  <div class="left">
    <div class="brand"><img src="__LOGO__" alt=""><span>UchiSamBot</span></div>
    <h1>__H1__</h1>
    __SUB__
    __CHIPS__
  </div>
  <div class="foot"><div class="tg">T</div><b>t.me/UchiSamBot</b><em>__FOOT__</em></div>
  <div class="shot"><img src="__SHOT__" alt=""></div>
</div></body></html>
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def data_uri(path: Path) -> str:
    """Файл внутрь HTML как data:. Внешние file:// не грузятся: страница
    собирается через set_content (origin about:blank), и Chromium молча
    оставляет <img> пустым — 24.10.2026 это дало белый «телефон» и битую
    иконку при идеально зелёной геометрии."""
    mime = {".woff2": "font/woff2", ".svg": "image/svg+xml", ".webp": "image/webp",
            ".png": "image/png"}[path.suffix]
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def labels() -> dict[str, str]:
    """Названия языков — из tools/build.py (LABELS), не из рукописи."""
    src = BUILD.read_text(encoding="utf-8")
    m = re.search(r"^LABELS = \{(.*?)^\}", src, re.S | re.M)
    if not m:
        raise SystemExit("LABELS не найден в tools/build.py — генератор не гадает")
    return dict(re.findall(r'"([a-z]{2})":\s*"([^"]+)"', m.group(1)))


def sources() -> dict[str, Path]:
    src = {"src/locales/en.json": LOCALES / "en.json", "tools/prices.json": PRICES,
           "tools/build.py": BUILD}
    for i, p in PAGES.items():
        src[f"card{i}"] = p
    for name in ("langs-cyrillic.woff2", "langs-devanagari.woff2", "langs-vietnamese.woff2"):
        src[f"fonts/{name}"] = FONTS / name
    return src


def cards() -> list[dict]:
    d = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    price = json.loads(PRICES.read_text(encoding="utf-8"))
    lab = labels()
    names = list(lab.values())
    free = price["free_breakdowns"]
    if str(free) not in d["hero.chip1"]:
        raise SystemExit(f"словарь обещает не {free} бесплатных разбора: {d['hero.chip1']!r}")
    if len(names) != 9:
        raise SystemExit(f"названий языков {len(names)}, а должно быть 9: {names}")
    rows = [
        {"i": "1", "title": d["hero.title"], "sub": d["hero.sub"],
         "chips": [d["hero.chip1"], d["hero.chip3"]]},
        {"i": "2", "title": d["how.s2t"], "sub": d["how.s2d"], "chips": []},
        {"i": "3", "title": d["how.s3t"], "sub": d["how.s3d"], "chips": []},
        {"i": "4", "title": d["hero.chip3"], "sub": " · ".join(names), "chips": []},
    ]
    for r in rows:
        # Подвал — тоже строка словаря (foot.tag), а не «free to start» из головы:
        # на этих карточках не должно быть ни одного обещания, которого нет на сайте.
        r["foot"] = d["foot.tag"]
    return rows


def build_html(card: dict) -> str:
    ranges = json.loads((ROOT / "tools" / "lang-fonts.json").read_text(encoding="utf-8"))
    css = (CSS
           .replace("__INTER_LATIN__", data_uri(INTER / "inter-latin.woff2"))
           .replace("__INTER_LATIN_EXT__", data_uri(INTER / "inter-latin-ext.woff2"))
           .replace("__INTER_VI__", data_uri(INTER / "inter-vietnamese.woff2"))
           .replace("__LANGS_CYR__", data_uri(FONTS / "langs-cyrillic.woff2"))
           .replace("__LANGS_DEV__", data_uri(FONTS / "langs-devanagari.woff2"))
           .replace("__LANGS_VI__", data_uri(FONTS / "langs-vietnamese.woff2"))
           .replace("__RANGE_CYR__", ranges["cyrillic"]["range"])
           .replace("__RANGE_DEV__", ranges["devanagari"]["range"])
           .replace("__RANGE_VI__", ranges["vietnamese"]["range"]))
    chips = ""
    if card["chips"]:
        chips = ('<div class="chips">'
                 + "".join(f'<span class="chip"><i></i>{esc(c)}</span>' for c in card["chips"])
                 + "</div>")
    return (HTML
            .replace("__TITLE__", esc(card["title"]))
            .replace("__CSS__", css)
            .replace("__LOGO__", data_uri(ROOT / "img" / "logo.svg"))
            .replace("__H1__", esc(card["title"]))
            .replace("__SUB__", f'<p class="sub">{esc(card["sub"])}</p>' if card["sub"] else "")
            .replace("__CHIPS__", chips)
            .replace("__FOOT__", esc(card["foot"]))
            .replace("__SHOT__", data_uri(PAGES[card["i"]])))


def render(verbose: bool = True) -> None:
    from playwright.sync_api import sync_playwright

    cs = cards()
    written: dict[str, dict] = {}
    ocr_dump: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        for card in cs:
            pg.set_content(build_html(card), wait_until="load")
            pg.wait_for_timeout(350)   # шрифты и картинка
            box = pg.evaluate("""() => {
                const d = document.documentElement;
                const imgs = [...document.images].map(i => [i.currentSrc.slice(0, 14), i.naturalWidth]);
                const r = [...document.querySelectorAll('.left,.foot,.shot')]
                    .map(e => e.getBoundingClientRect());
                return {sw: d.scrollWidth, sh: d.scrollHeight,
                        right: Math.max(...r.map(b => b.right)),
                        bottom: Math.max(...r.map(b => b.bottom)),
                        imgs, fonts: document.fonts.status};
            }""")
            if box["sw"] > 1920 or box["sh"] > 1080 or box["right"] > 1920.5 or box["bottom"] > 1080.5:
                raise SystemExit(f"карточка {card['i']} не влезла в 1920×1080: {box}")
            empty = [i for i, w in box["imgs"] if not w]
            if empty or len(box["imgs"]) != 2:
                raise SystemExit(f"карточка {card['i']}: картинки не загрузились {box['imgs']}")
            out = KIT / f"screen{card['i']}.png"
            pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
            ocr = subprocess.run(["tesseract", str(out), "-", "-l", "eng+rus"],
                                 capture_output=True, text=True).stdout
            ocr_dump.append(f"--- {out.name}\n{ocr.strip()}")
            if verbose:
                print(f"нарисовано {out.name} ({out.stat().st_size} байт)")
            written[out.name] = {"card": card["i"], "sha256": sha(out),
                                 "source": f"card{card['i']}",
                                 "title": card["title"], "sub": card["sub"],
                                 "chips": card["chips"], "foot": card["foot"]}
        b.close()

    # --- то, что реально видно в пикселях (OCR), а не то, что мы думали, что нарисовали
    price = json.loads(PRICES.read_text(encoding="utf-8"))
    names = list(labels().values())
    whole = "\n".join(ocr_dump)
    low = whole.lower()
    problems = []

    # 1) Покрытие глифов — ДО пикселей: каждый символ каждого названия обязан попасть
    #    в unicode-range одного из объявленных шрифтов. Иначе браузер нарисует «тофу»
    #    (пустые прямоугольники), а OCR с eng+rus этого не заметит.
    ranges = json.loads((ROOT / "tools" / "lang-fonts.json").read_text(encoding="utf-8"))
    covered = set("".join(chr(c) for c in range(0x20, 0x250)))   # латиница + диакритика
    for k in ("cyrillic", "devanagari", "vietnamese"):
        covered |= set(ranges[k]["names"])
    missing = sorted({ch for n in names for ch in n if ch not in covered})
    if missing:
        problems.append("шрифт не нарисует буквы: " + " ".join(missing))

    # 2) OCR: цифра бесплатных разборов на карточке 1 и «languages» на карточке 4
    m = re.search(r"(\d+)\s*breakdowns?\s*free", ocr_dump[0], re.I)
    if not m or int(m.group(1)) != price["free_breakdowns"]:
        problems.append(f"OCR на карточке 1 прочитал не «{price['free_breakdowns']} "
                        f"breakdowns free»: {m.group(0) if m else 'нет строки'}")
    if "language" not in ocr_dump[3].lower():
        problems.append("OCR на карточке 4 не прочитал слово languages")
    for bad in ("5 breakdowns", "two languages", "russian and english"):
        if bad in low:
            problems.append(f"OCR прочитал старое обещание: {bad!r}")
    ascii_names = ["engli", "portu", "bahas", "turk", "tien"]
    if len([s for s in ascii_names if s in low]) < 3:
        problems.append("OCR не нашёл хотя бы три названия языков")
    if problems:
        raise SystemExit("картинки нарисованы, но прочитать их не вышло: " + "; ".join(problems))

    manifest = {
        "note": "Пишется только tools/submission-kit.py. Картинки для форм сторонних "
                "площадок: подписи берутся из src/locales/en.json, число бесплатных "
                "разборов — из tools/prices.json, названия языков — из LABELS "
                "tools/build.py. Свип сверяет байты с этим файлом и манифест с "
                "источниками (см. «submission-kit» в landing-sweep.py).",
        "generated": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "canvas": [1920, 1080],
        "claims": {"free_breakdowns": price["free_breakdowns"], "languages": len(names)},
        "cards": written,
        "sources": {k: sha(v) for k, v in sources().items()},
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    if verbose:
        print(f"манифест: {MANIFEST.relative_to(ROOT)} — 4 карточки, "
              f"{price['free_breakdowns']} бесплатных, {len(names)} языков")


def check() -> list[tuple[str, bool, str]]:
    """Возвращает [(имя проверки, ок, подробность)]. Зовётся свипом и --check."""
    out: list[tuple[str, bool, str]] = []
    price = json.loads(PRICES.read_text(encoding="utf-8"))
    names = list(labels().values())
    have_png = sorted(p.name for p in KIT.glob("*.png"))
    out.append(("kit: четыре картинки на месте",
                have_png == sorted(OUT), ", ".join(have_png)))
    if not MANIFEST.is_file():
        out.append(("kit: манифест существует", False, "нет submission-kit/manifest.json"))
        return out
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out.append(("kit: манифест существует", True, m.get("generated", "")))
    bad = []
    for name in sorted(OUT):
        f = KIT / name
        if not f.is_file():
            bad.append(f"{name}: нет файла")
            continue
        head = f.open("rb").read(33)
        w = int.from_bytes(head[16:20], "big")
        h = int.from_bytes(head[20:24], "big")
        if (w, h) != (1920, 1080):
            bad.append(f"{name}: {w}×{h}, а нужно 1920×1080")
        want = m.get("cards", {}).get(name, {}).get("sha256")
        if want != sha(f):
            bad.append(f"{name}: байты не те, что в манифесте")
    out.append(("kit: каждая картинка 1920×1080 и совпадает с манифестом",
                not bad, "; ".join(bad)[:240] or "4/4"))
    out.append(("kit: манифест обещает столько же бесплатных разборов, сколько prices.json",
                m.get("claims", {}).get("free_breakdowns") == price["free_breakdowns"],
                f"манифест {m.get('claims', {}).get('free_breakdowns')}, "
                f"prices.json {price['free_breakdowns']}"))
    out.append(("kit: манифест обещает столько же языков, сколько LABELS",
                m.get("claims", {}).get("languages") == len(names),
                f"манифест {m.get('claims', {}).get('languages')}, LABELS {len(names)}"))
    stale_src = [k for k, v in sources().items() if m.get("sources", {}).get(k) != sha(v)]
    out.append(("kit: входы не новее манифеста (иначе «текст поправили, картинку нет»)",
                not stale_src,
                ("перерисовать: " + ", ".join(stale_src))[:240] if stale_src
                else f"{len(sources())} входов совпали"))
    drawn = {name: m["cards"][name].get("chips", []) for name in m.get("cards", {})}
    blob = json.dumps(m, ensure_ascii=False) + " " + " ".join(
        p.read_text(encoding="utf-8") for p in KIT.glob("*.md"))
    hits = [s for s in STALE if s.lower() in blob.lower()]
    out.append(("kit: ни в манифесте, ни в README нет старых обещаний",
                not hits, ", ".join(hits) or "чисто"))
    return out


def main(argv: list[str]) -> int:
    if "--check" in argv:
        rows = check()
        fails = [r for r in rows if not r[1]]
        for name, ok, detail in rows:
            print(("OK   " if ok else "FAIL ") + name + (f" | {detail}" if detail else ""))
        print(f"CHECKS: {len(rows)}, FAILED: {len(fails)}")
        return 1 if fails else 0
    render()
    rows = check()
    fails = [r for r in rows if not r[1]]
    for name, ok, detail in rows:
        print(("OK   " if ok else "FAIL ") + name + (f" | {detail}" if detail else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
