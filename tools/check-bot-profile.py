#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-bot-profile.py — тексты профиля бота отвечают словарям сайта.

Повод (01.11.2026, сорок первый блок). В `tools/bot-profile.json` стояло: «тексты
long восьми языков задуманы как совпадающие с meta.desc словарей сайта», и рядом
приёмка 01.11 записала долг: сверять это некому. Батарея `bot-profile` читает
ЖИВОГО бота против реестра, то есть ловит «бот отстал от реестра», но не ловит
«реестр отстал от сайта». Правка описания на странице оставляла профиль бота
врать молча, а профиль — первое, что видит человек, нажавший главную кнопку сайта.

Что меряет прибор (27 текстов × девять языков против того, что нарисовано):

  A. Реестр сам согласован: слот по умолчанию — `en` (язык сайта по умолчанию),
     три поля на месте, лимиты равны лимитам Telegram (long 512, short 120,
     name 64), у каждого поля ровно девять языков сайта, пустых текстов нет.
  B. Ни один текст не длиннее своего лимита — иначе Bot API отклонит запись
     целиком, и профиль останется старым, а реестр будет думать, что применён.
  C. long и name восьми НЕрукописных языков дословно равны `meta.desc` и
     `meta.title` своего словаря. Это и есть долг, названный приёмкой 01.11:
     сайт и профиль бота — один текст, а не два похожих.
  D. Рукописные тексты объявлены поимённо и с причиной; объявление не бывает
     мёртвым: если «рукописный» текст совпал со словарём, значит исключение
     ничего не скрывает и его пора снять.
  E. short называет число бесплатных разборов из `tools/prices.json` (2): это
     обещание, которое человек читает на t.me до первого сообщения.
  F. Нарисованные страницы несут тот же `meta.desc`/`meta.title`, что словари:
     реестр сверяется не с исходником сборки, а с тем, что отдано посетителю.
  G. Ни один текст не называет предметом НАЗВАНИЕ ЯЗЫКА СТРАНИЦЫ — та самая
     ошибка первой генерации (ru «Русский язык» вместо «Английский язык»).
     У рукописных текстов это не провал, а ДОЛГ: текст владельца не
     переписывается прибором, но прибор обязан называть его вслух каждый прогон.
  H. `_note` реестра называет этот прибор и обе батареи свипа — правило дерева
     «обещание проверки обязано называть прибор» проверяется машинно.

  python3 tools/check-bot-profile.py            # дерево
  python3 tools/check-bot-profile.py --control  # семь мутантов обязаны покраснеть
"""

import argparse
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
TELEGRAM = {"long": 512, "short": 120, "name": 64}
INSTRUMENT = "tools/check-bot-profile.py"
BATTERIES = ("bot-profile-texts", "bot-profile-texts-control")
# Известные плохие значения: название ЯЗЫКА вместо предмета. Список тот же, что
# у check-subjects.py, — здесь он про профиль бота, а не про страницы.
AUTONYMS = {
    "ru": ["русский язык", "русский"],
    "uk": ["українська мова", "українська"],
    "es": ["español"],
    "pt": ["português"],
    "hi": ["हिंदी"],
    "id": ["bahasa indonesia"],
    "tr": ["türkçe"],
    "vi": ["tiếng việt"],
    "en": ["russian"],
}


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def meta_of_page(text: str) -> tuple[str, str]:
    desc = re.search(r'<meta name="description" content="([^"]*)"', text)
    title = re.search(r"<title>(.*?)</title>", text, re.S)
    return (html.unescape(desc.group(1)) if desc else "",
            html.unescape(title.group(1)) if title else "")


def page_of(lang: str) -> Path:
    return ROOT / "index.html" if lang == "en" else ROOT / lang / "index.html"


def scan(root: Path) -> tuple[int, list[str], list[str]]:
    checks, bad, debt = 0, [], []
    reg = json.loads((root / "tools" / "bot-profile.json").read_text(encoding="utf-8"))
    locales = {l: json.loads((root / "src" / "locales" / f"{l}.json").read_text(encoding="utf-8"))
               for l in LANGS}
    prices = json.loads((root / "tools" / "prices.json").read_text(encoding="utf-8"))
    free = str(prices.get("free_breakdowns"))

    checks += 1
    if reg.get("default") != "en":
        bad.append(f"реестр: слот по умолчанию '{reg.get('default')}', а язык сайта по умолчанию — en")

    for field in ("long", "short", "name"):
        node = reg.get(field)
        checks += 1
        if not isinstance(node, dict):
            bad.append(f"реестр: поля {field} нет")
            continue
        checks += 1
        if node.get("limit") != TELEGRAM[field]:
            bad.append(f"{field}: лимит {node.get('limit')} вместо лимита Telegram {TELEGRAM[field]}")
        texts = node.get("texts") or {}
        checks += 1
        if set(texts) != set(LANGS):
            bad.append(f"{field}: языки {sorted(set(LANGS) - set(texts))} пропущены, "
                       f"{sorted(set(texts) - set(LANGS))} лишние")
        handwritten = node.get("handwritten") or {}
        for lang, text in sorted(texts.items()):
            checks += 1
            if not str(text).strip():
                bad.append(f"{field}/{lang}: пустой текст — Bot API отклонит запись")
            elif len(text) > TELEGRAM[field]:
                bad.append(f"{field}/{lang}: {len(text)} знаков при лимите {TELEGRAM[field]}")
            checks += 1
            if field == "short" and free and free not in str(text):
                bad.append(f"short/{lang}: не называет число бесплатных разборов ({free}) из prices.json")
            checks += 1
            if field == "long":
                want = locales[lang].get("meta.desc", "")
                if lang in handwritten:
                    if str(text) == want:
                        bad.append(f"long/{lang}: объявлен рукописным, но совпал с meta.desc — "
                                   f"исключение мёртвое, сними объявление")
                elif str(text) != want:
                    bad.append(f"long/{lang}: профиль бота разошёлся с meta.desc словаря "
                               f"(реестр {len(str(text))} знаков, сайт {len(want)})")
            if field == "name":
                want = locales[lang].get("meta.title", "")
                if lang in handwritten:
                    if str(text) == want:
                        bad.append(f"name/{lang}: объявлен рукописным, но совпал с meta.title — "
                                   f"исключение мёртвое, сними объявление")
                elif str(text) != want:
                    bad.append(f"name/{lang}: имя бота разошлось с meta.title словаря")
            # G. Название языка вместо предмета.
            low = str(text).lower()
            hits = [t for t in AUTONYMS.get(lang, []) if t in low]
            checks += 1
            if hits:
                where = f"{field}/{lang}"
                subjects = ", ".join(json.loads((root / "tools" / "subjects.json")
                                                .read_text(encoding="utf-8"))["subjects"][lang])
                if lang in handwritten:
                    debt.append(f"{where}: называет предметом '{hits[0]}', которого нет в каноне "
                                f"({subjects}). Текст рукописный — не переписывается прибором")
                else:
                    bad.append(f"{where}: называет предметом '{hits[0]}', которого нет в каноне "
                               f"({subjects})")
        for lang in sorted(handwritten):
            checks += 1
            if lang not in LANGS:
                bad.append(f"{field}: рукописным объявлен неизвестный язык '{lang}'")
            elif not str(handwritten[lang]).strip():
                bad.append(f"{field}/{lang}: рукописный без причины — исключение без объяснения")

    # F. Нарисованные страницы против словарей.
    for lang in LANGS:
        page = page_of(lang) if root == ROOT else (
            root / "index.html" if lang == "en" else root / lang / "index.html")
        checks += 1
        if not page.exists():
            bad.append(f"{lang}: нет нарисованной страницы {page.name}")
            continue
        desc, title = meta_of_page(page.read_text(encoding="utf-8", errors="replace"))
        checks += 1
        if desc != locales[lang].get("meta.desc", ""):
            bad.append(f"{lang}/index.html: meta description на странице ≠ meta.desc словаря")
        checks += 1
        if title != locales[lang].get("meta.title", ""):
            bad.append(f"{lang}/index.html: <title> на странице ≠ meta.title словаря")

    # H. Правило дерева: обещание проверки называет прибор.
    checks += 1
    note = str(reg.get("_note", ""))
    if INSTRUMENT not in note or not all(b in note for b in BATTERIES):
        bad.append(f"реестр: _note не называет прибор {INSTRUMENT} и батареи {', '.join(BATTERIES)} — "
                   f"это обещание, а не проверка")

    return checks, bad, debt


def control(tmp: Path) -> int:
    clean = tmp / "clean"
    shutil.copytree(ROOT, clean, ignore=shutil.ignore_patterns(
        ".git", "evidence", "node_modules", ".shots-work", "__pycache__"))
    checks, bad, debt = scan(clean)
    if bad:
        print("КОНТРОЛЬ СЛОМАН: чистая копия не зелёная:")
        for line in bad:
            print("  ", line)
        return 1
    mut = tmp / "mut"
    shutil.copytree(clean, mut)
    reg_path = mut / "tools" / "bot-profile.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    reg["long"]["texts"]["es"] += " Extra."
    reg["short"]["texts"]["hi"] = reg["short"]["texts"]["hi"].replace("2", "3", 1)
    reg["name"]["texts"]["tr"] += "!"
    reg["long"]["limit"] = 1024
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    hi = mut / "hi" / "index.html"
    hi.write_text(hi.read_text(encoding="utf-8").replace(
        "</title>", " (mutant)</title>", 1), encoding="utf-8")
    uk = mut / "tools" / "bot-profile.json"
    reg2 = json.loads(uk.read_text(encoding="utf-8"))
    reg2["short"]["texts"]["id"] = reg2["short"]["texts"]["id"] + " Bahasa Indonesia."
    uk.write_text(json.dumps(reg2, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    note_reg = mut / "tools" / "bot-profile.json"
    reg3 = json.loads(note_reg.read_text(encoding="utf-8"))
    reg3["_note"] = note_reg and reg3["_note"].replace(INSTRUMENT, "какой-то прибор")
    note_reg.write_text(json.dumps(reg3, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _c, bad, _d = scan(mut)
    expect = ["long/es: профиль бота разошёлся с meta.desc",
              "short/hi: не называет число бесплатных разборов",
              "name/tr: имя бота разошлось",
              "long: лимит 1024",
              "hi/index.html: <title> на странице",
              "short/id: называет предметом 'bahasa indonesia'",
              "_note не называет прибор"]
    caught = sum(1 for e in expect if any(e in line for line in bad))
    for line in bad:
        print("  поймано:", line)
    print(f"КОНТРОЛЬ: чистая копия зелёная, мутант поймал {caught}/{len(expect)}")
    return 0 if caught == len(expect) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="профиль бота против словарей сайта")
    ap.add_argument("--control", action="store_true", help="семь мутантов обязаны покраснеть")
    a = ap.parse_args()
    if a.control:
        with tempfile.TemporaryDirectory() as td:
            return control(Path(td))
    checks, bad, debt = scan(ROOT)
    for line in bad:
        print("  КРАСНО:", line)
    for line in debt:
        print("  ДОЛГ (решает владелец):", line)
    print(f"CHECKS: {checks}")
    print(f"FAILED: {len(bad)}")
    print(f"DEBT: {len(debt)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
