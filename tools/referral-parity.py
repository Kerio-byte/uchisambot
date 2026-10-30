#!/usr/bin/env python3
"""referral-parity.py — сверка обещания «пригласи друга» с кодом бота.

Повод (30.10.2026). Блок ref.text в девяти языках обещал три вещи сразу:
  * событие — «когда он РЕШИТ первую задачу» (en solve their first task, ru решит
    первую задачу, tr çözünce, hi हल करेंगे …);
  * величину — «ещё один бесплатный разбор»;
  * потолок — «всего не больше 20 бонусных разборов».

Потолок и величина в боте есть и совпадали: REFERRAL_BONUS=1, REFERRAL_MAX_CREDITS=20
(study-bot/bot/payments.py), начисление — storage.credit_referral(). А события «друг
решил» в продукте НЕТ вовсе: credit_referral_on_first_solve() вызывается в handlers.py
после того, как бот выдал другу ПЕРВЫЙ РАЗБОР (mark_task(..., "solved") — это отметка
о том, что ответил бот, а не о том, что ученик что-то решил). То есть страница,
которая девять раз обещает «бот не решает за тебя», в блоке приглашения называла
событием «друг решил». Слово вернулось в пятой форме — не в обещании продукта, а в
условии бонуса, и реестр claims.json его не видел, потому что ref.text там не значился.

Что проверяет эта батарея
-------------------------
1. Потолок: единственное число в ref.text равно REFERRAL_MAX_CREDITS (все 9 языков).
2. Величина: REFERRAL_BONUS == 1 — иначе фраза «ещё один» становится ложью, и это
   красный, а не повод править текст молча.
3. Событие: в ref.text нет глаголов «решает/решит/solves/çözer/मिल …» — событие
   описано как «получит первый разбор» (единица продукта), а не как «решил задачу».
4. Код бота вообще на месте: payments.py и handlers.py читаются, функция начисления
   вызывается после выдачи разбора.

Код возврата: 0 — всё сходится; 1 — расхождение (тогда правится страница или бот,
но не проверка).

  python3 tools/referral-parity.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
# Бот лежит рядом с лендингом в том же рабочем дереве (../../study-bot/bot). Путь
# строится от файла, а не пишется строкой: репозиторий публичный, и опseк-батарея
# свипа краснеет на любой абсолютный путь сервера в тексте. Переопределяется
# переменной LANDING_BOT, если дерево когда-нибудь разъедется.
BOT = Path(os.environ.get("LANDING_BOT") or ROOT.parent.parent / "study-bot" / "bot")

# Глаголы «решил», которыми нельзя описывать событие бонуса: продукт такого события
# не наблюдает, а страница в остальных блоках обещает ровно обратное.
FORBID = {
    "en": r"(?i)\b(solve|solves|solved|solving)\b",
    "ru": r"(?i)\b(решит|решает|решил|решила)\b",
    "uk": r"(?i)\b(розв['’]яже|розв['’]язує|вирішить|вирішує)\b",
    "es": r"(?i)\b(resuelva|resuelve|resolverá|resolvió)\b",
    "pt": r"(?i)\b(resolva|resolve|resolver|resolverá|resolveu)\b",
    "hi": r"(?i)(हल कर|समाधान कर)",
    "id": r"(?i)(menyelesaikan|selesaikan|selesai)",
    "tr": r"(?i)\b(çözer|çözünce|çözdü|çözmesi)\b",
    "vi": r"(?i)\b(giải)\b",
}


def bot_constants() -> tuple[int, int]:
    src = (BOT / "payments.py").read_text(encoding="utf-8")
    def grab(name: str) -> int:
        m = re.search(rf"^{name}\s*=\s*(\d+)", src, re.M)
        if not m:
            raise SystemExit(f"payments.py: не нашёл {name} — обещание осталось без основания")
        return int(m.group(1))
    return grab("REFERRAL_BONUS"), grab("REFERRAL_MAX_CREDITS")


def main() -> int:
    bonus, cap = bot_constants()
    handlers = (BOT / "handlers.py").read_text(encoding="utf-8")
    trigger_ok = bool(re.search(r"credit_referral_on_first_solve\(message\.bot, storage, uid\)", handlers))
    after_answer = handlers.find('mark_task(\n            task_id, "solved"') < handlers.find("credit_referral_on_first_solve(message.bot")

    fails = []
    print(f"бот: REFERRAL_BONUS={bonus}  REFERRAL_MAX_CREDITS={cap}")
    if bonus != 1:
        fails.append(f"REFERRAL_BONUS={bonus}: фраза «ещё один» стала ложью")
    if not trigger_ok:
        fails.append("handlers.py: вызова credit_referral_on_first_solve больше нет — событие бонуса изменилось")
    if trigger_ok and not after_answer:
        fails.append("handlers.py: начисление стоит ДО выдачи разбора — событие бонуса изменилось")

    for lang in LANGS:
        data = json.loads((ROOT / "src" / "locales" / f"{lang}.json").read_text(encoding="utf-8"))
        text = data.get("ref.text", "")
        where = f"{lang} ref.text"
        if not text:
            fails.append(f"{where}: ключа нет")
            continue
        nums = re.findall(r"\d+", text)
        if not nums:
            fails.append(f"{where}: нет числа бонусного потолка")
        elif any(int(n) != cap for n in nums):
            fails.append(f"{where}: числа {nums} != потолку бота {cap}")
        m = re.search(FORBID[lang], text)
        if m:
            fails.append(f"{where}: событие описано как «{m.group(0)}», а продукт его не наблюдает")

    print(f"языков: {len(LANGS)}  провалов: {len(fails)}")
    for f in fails:
        print("  FAIL " + f)
    if fails:
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
