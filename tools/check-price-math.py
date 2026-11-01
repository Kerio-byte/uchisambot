#!/usr/bin/env python3
"""check-price-math.py — числа «за разбор» и «выгода %» на карточках тарифов верны.

Повод (01.11.2026, тридцать второй блок). На карточках тарифов стоят не только цены,
но и два ЧИСЛА, которых нет ни в одном реестре: сколько стоит один разбор в пакете и
сколько процентов экономит пакет. Их выводит из цен человек, руками, в девяти словарях.

`tools/prices.json` хранит только то, что бот берёт деньгами: 30 / 120 за 5 / 300 за 15.
Прибор `prices` сверяет с ним видимые строки цен и код бота — то есть 120 и 300. А «24
звезды за разбор» и «выгода 20%» не сверяет никто: они не в реестре, их нечем сравнить,
и после правки цены в словарях они остаются прежними. Страница при этом продолжает
обещать скидку, которой уже нет: 120 звёзд за 5 разборов — это 24 за разбор ровно
потому, что 120/5=24; если пакет станет 150, «24 за разбор» и «выгода 20%» превратятся
в ложь, а все нынешние приборы останутся зелёными.

Что меряет этот прибор (читает НАРИСОВАННЫЕ страницы, а не словари — то, что видит
человек, а не то, что задумано):

  * карточек тарифов ровно три, и в каждой цене стоит число из `prices.json`;
  * цена пакета делится на размер пакета без остатка, и «за разбор» на странице равно
    этому частному (иначе страница называет цену, которой бот не возьмёт);
  * «выгода N%» равна (одиночная − за разбор) / одиночная, округлённой вниз или по
    правилам арифметики (обе записи допустимы: 33% и 33% — одно и то же число);
  * бесплатных разборов в заголовке столько же, сколько `free_breakdowns`;
  * строка `price-fine` называет одиночную цену.

Чего прибор НЕ делает (названо, чтобы «не измерили» не читалось как «измерили и хорошо»):
не проверяет валюту и слово «звёзды» (это решение продукта: в семи языках стоит
«Stars», в ru и hi переведено) и не сверяет проценты с кодом бота — скидку бот не
считает, её пишет страница.

Запуск:
  python3 tools/check-price-math.py              # девять страниц этого дерева
  python3 tools/check-price-math.py --root DIR   # то же на копии дерева
  python3 tools/check-price-math.py --control    # проверка самого прибора: пять мутантов
  python3 tools/check-price-math.py --json       # машинный вывод
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
CARD_RE = r'<div class="card price[^"]*">'
TAG_RE = re.compile(r"<[^>]+>")
NUM_RE = re.compile(r"\d+")


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub("", s)).strip()


def page_of(root: Path, lang: str) -> Path:
    return root / "index.html" if lang == "en" else root / lang / "index.html"


def cards_of(html: str) -> list[dict]:
    parts = re.split(CARD_RE, html)
    out = []
    for chunk in parts[1:]:
        chunk = chunk.split('<p class="price-fine"')[0]
        h3 = re.search(r"<h3[^>]*>(.*?)</h3>", chunk, re.S)
        amt = re.search(r'<div class="amount"[^>]*>(.*?)</div>', chunk, re.S)
        par = re.search(r"<p[^>]*>(.*?)</p>", chunk, re.S)
        out.append({
            "title": clean(h3.group(1)) if h3 else "",
            "amount": clean(amt.group(1)) if amt else "",
            "line": clean(par.group(1)) if par else "",
        })
    return out


def percent_of(text: str) -> int | None:
    m = re.search(r"(?:(\d+)\s*%|%\s*(\d+))", text)
    if not m:
        return None
    return int(m.group(1) or m.group(2))


def check_page(root: Path, lang: str, prices: dict) -> tuple[list[str], dict]:
    bad: list[str] = []
    path = page_of(root, lang)
    if not path.exists():
        return [f"{lang:2}: страницы нет ({path.name})"], {}
    html = path.read_text(encoding="utf-8", errors="replace")
    cards = cards_of(html)
    if len(cards) != 3:
        bad.append(f"{lang:2}: карточек тарифов {len(cards)}, а не 3 — считать нечего")
        return bad, {}

    single = int(prices["single"])
    free = int(prices["free_breakdowns"])
    packs = {}
    for name in ("pack5", "pack15"):
        p = prices[name]
        packs[int(p["price"])] = (name, int(p["size"]))

    stat = {"free": None, "packs": {}}
    seen_pack = 0
    for i, card in enumerate(cards, 1):
        nums = [int(n) for n in NUM_RE.findall(card["amount"])]
        if not nums:
            got = [int(n) for n in NUM_RE.findall(card["title"])]
            stat["free"] = got[0] if got else None
            if not got:
                bad.append(f"{lang:2}: в заголовке бесплатной карточки нет числа — "
                           f"обещание «{free} бесплатно» не названо")
            elif got[0] != free:
                bad.append(f"{lang:2}: бесплатных разборов на карточке {got[0]}, "
                           f"а в prices.json {free}")
            continue

        seen_pack += 1
        price = nums[0]
        if price not in packs:
            bad.append(f"{lang:2}: на карточке цена {price}, которой нет в prices.json "
                       f"(там {sorted(packs)}) — сверять не с чем")
            continue
        name, size = packs[price]
        if price % size:
            bad.append(f"{lang:2}: {name} — {price} не делится на {size} без остатка, "
                       f"а страница называет цену «за разбор» целым числом")
            continue
        per = price // size
        exact = (single - per) / single * 100
        allowed = {int(exact), int(round(exact))}

        got_per = None
        line_nums = [int(n) for n in NUM_RE.findall(card["line"])]
        if line_nums:
            got_per = line_nums[0]
        if got_per is None:
            bad.append(f"{lang:2}: {name} — в строке «{card['line']}» нет цены за разбор")
        elif got_per != per:
            bad.append(f"{lang:2}: {name} — на странице {got_per} за разбор, "
                       f"а {price}/{size} = {per}")

        got_save = percent_of(card["line"])
        if got_save is None:
            bad.append(f"{lang:2}: {name} — в строке «{card['line']}» нет выгоды в процентах")
        elif got_save not in allowed:
            bad.append(f"{lang:2}: {name} — выгода на странице {got_save}%, "
                       f"а ({single}-{per})/{single} = {exact:.2f}% (допустимо "
                       f"{'/'.join(str(a) for a in sorted(allowed))}%)")

        stat["packs"][name] = {"price": price, "per": got_per, "save": got_save}

    if seen_pack != 2:
        bad.append(f"{lang:2}: карточек с ценой пакета {seen_pack}, а не 2")

    fine = re.search(r'<p class="price-fine"[^>]*>(.*?)</p>', html, re.S)
    if not fine:
        bad.append(f"{lang:2}: строки price-fine нет — одиночная цена не названа")
    else:
        fine_nums = [int(n) for n in NUM_RE.findall(clean(fine.group(1)))]
        if single not in fine_nums:
            bad.append(f"{lang:2}: price-fine «{clean(fine.group(1))}» не называет "
                       f"одиночную цену {single}")
    return bad, stat


def load_prices(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# Слова «бесплатно» на каждом языке — по ним ищется фраза-обещание в ИИ-слое.
FREE_WORDS = {
    "en": ("free",),
    "ru": ("бесплатн",),
    "es": ("gratis",),
    "pt": ("grátis", "gratis"),
    "hi": ("मुफ़्त",),
    "id": ("gratis",),
    "tr": ("ücretsiz",),
    "vi": ("miễn phí",),
    "uk": ("безкоштовн",),
}


def ai_twins(root: Path) -> list[tuple[Path, str]]:
    """Файлы ИИ-слоя: llms.txt и десять md-двойников — с языком каждого."""
    out = [(root / "llms.txt", "en"), (root / "index.html.md", "en")]
    out += [(root / lang / "index.html.md", lang) for lang in LANGS if lang != "en"]
    return out


def check_ai_layer(root: Path, prices: dict) -> list[str]:
    """Тот же обещанный счёт бесплатных разборов — в файлах, которые читают ИИ.

    Дырка 01.11.2026 (блок 33): price-math читает НАРИСОВАННЫЕ страницы, а llms.txt
    и десять md-двойников называют то же число словами и цифрой — и никем не сверялись.
    Меняешь free_breakdowns в prices.json: девять карточек обновятся, а файл для ИИ
    продолжит обещать прежнее число, и ассистент процитирует его человеку.
    Правило: первое слово «бесплатно» в файле, ближайшее число ПЕРЕД ним (40 знаков)
    обязано равняться free_breakdowns. Нет числа — находка: обещание не названо.
    """
    bad: list[str] = []
    free = int(prices["free_breakdowns"])
    for path, lang in ai_twins(root):
        name = path.relative_to(root) if path.is_relative_to(root) else path.name
        if not path.is_file():
            bad.append(f"ИИ {name}: файла нет — обещание «{free} бесплатно» не проверить")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        low = text.lower()
        pos = min((low.find(w) for w in FREE_WORDS[lang] if low.find(w) >= 0), default=-1)
        if pos < 0:
            bad.append(f"ИИ {name}: слова «бесплатно» нет — обещание не названо")
            continue
        window = text[max(0, pos - 40):pos]
        nums = re.findall(r"\d+", window)
        if not nums:
            bad.append(f"ИИ {name}: перед «бесплатно» нет числа — обещание «{free}» не названо")
            continue
        got = int(nums[-1])
        if got != free:
            bad.append(f"ИИ {name}: «{got} бесплатно», а в prices.json {free}")
    return bad


def check_tree(root: Path, prices_path: Path) -> tuple[list[str], dict]:
    prices = load_prices(prices_path)
    bad: list[str] = []
    stats = {}
    for lang in LANGS:
        b, s = check_page(root, lang, prices)
        bad += b
        if s:
            stats[lang] = s
    bad += check_ai_layer(root, prices)
    return bad, stats


def control() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="price-math-"))
    caught: list[str] = []
    try:
        base = tmp / "base"
        for lang in LANGS:
            src = page_of(ROOT, lang)
            dst = page_of(base, lang)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
        shutil.copy(ROOT / "tools" / "prices.json", base / "prices.json")
        for src, _ in ai_twins(ROOT):
            dst = base / src.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
        prices_path = base / "prices.json"

        bad, _ = check_tree(base, prices_path)
        if bad:
            print("  контроль: чистая копия не зелёная — прибор врёт сам по себе:")
            for line in bad[:5]:
                print("   ", line)
            return 1
        print("  контроль: чистая копия зелёная")

        def run(name: str, mutate, marker: str, count: int = 1) -> None:
            d = tmp / re.sub(r"\W+", "-", name)
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(base, d)
            mutate(d)
            bad, _ = check_tree(d, d / "prices.json")
            hit = [x for x in bad if marker in x]
            if len(hit) >= count:
                caught.append(name)
                print(f"  поймал: {name} — {hit[0]}")
            else:
                print(f"  НЕ ПОЙМАЛ: {name} (находок {len(bad)}, из них с «{marker}» {len(hit)})")

        def edit_page(d: Path, lang: str, old: str, new: str, count: int = 1) -> None:
            p = page_of(d, lang)
            s = p.read_text(encoding="utf-8")
            if s.count(old) < count:
                raise SystemExit(f"мутант не поставить: {old!r} нет на {lang}")
            p.write_text(s.replace(old, new, count), encoding="utf-8")

        def per_item(d: Path) -> None:
            edit_page(d, "ru", "24 звезды за разбор", "25 звёзд за разбор")

        def save_pct(d: Path) -> None:
            edit_page(d, "tr", "%33 tasarruf", "%30 tasarruf")

        def free_count(d: Path) -> None:
            edit_page(d, "uk", "Перші 2 розбори</h3>", "Перші 3 розбори</h3>")

        def no_fine(d: Path) -> None:
            edit_page(d, "es", "30 Stars.", "35 Stars.")

        def price_changed(d: Path) -> None:
            p = d / "prices.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["pack15"]["price"] = 360
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        def free_ai(d: Path) -> None:
            p = d / "llms.txt"
            s = p.read_text(encoding="utf-8")
            if "First 2 breakdowns free" not in s:
                raise SystemExit("мутант не поставить: в llms.txt нет английского обещания")
            p.write_text(s.replace("First 2 breakdowns free", "First 3 breakdowns free", 1),
                         encoding="utf-8")

        run("цена за разбор разошлась", per_item, "ru")
        run("процент выгоды разошёлся", save_pct, "tr")
        run("бесплатных разборов больше", free_count, "uk")
        run("строка одиночной цены пропала", no_fine, "es")
        run("файл для ИИ обещает другое число", free_ai, "llms.txt")
        run("пакет подорожал, страница нет", price_changed, "нет в prices.json", count=len(LANGS))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = 6
    print(f"МУТАНТЫ {len(caught)}/{total}")
    return 0 if len(caught) == total else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="тарифы: числа «за разбор» и «выгода %» верны")
    ap.add_argument("--root", default="", help="дерево со страницами (по умолчанию это)")
    ap.add_argument("--prices", default="", help="реестр цен (по умолчанию tools/prices.json)")
    ap.add_argument("--control", action="store_true", help="проверка самого прибора: пять мутантов")
    ap.add_argument("--json", action="store_true", help="машинный вывод")
    a = ap.parse_args()

    if a.control:
        return control()

    root = Path(a.root).resolve() if a.root else ROOT
    prices_path = Path(a.prices).resolve() if a.prices else ROOT / "tools" / "prices.json"
    bad, stats = check_tree(root, prices_path)
    if a.json:
        print(json.dumps({"findings": bad, "stats": stats, "langs": len(LANGS)}, ensure_ascii=False))
        return 1 if bad else 0
    for lang in LANGS:
        s = stats.get(lang) or {}
        packs = s.get("packs") or {}
        bits = [f"{packs[k]['price']}->{packs[k]['per']} ({packs[k]['save']}%)"
                for k in ("pack5", "pack15") if k in packs]
        print(f"  {lang:2} {' '.join(bits) or '?':28} бесплатно {s.get('free')}")
    if bad:
        print(f"НАХОДОК {len(bad)}:")
        for line in bad:
            print("  FAIL", line)
        return 1
    print(f"ТАРИФЫ: {len(LANGS)} языков, находок 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
