#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Поставить профилю бота ИМЯ и ДВА ОПИСАНИЯ на девяти языках сайта (28.10.2026).

ЗАЧЕМ. Всё, что видит посетитель после главной кнопки сайта, живёт в трёх полях Telegram,
и у каждого СВОЙ лимит и СВОЁ место на экране:
  • name  (setMyName,             ≤64)  — имя бота: заголовок страницы t.me и строка в списке чатов;
  • long  (setMyDescription,      ≤512) — текст в пустом чате до первого сообщения;
  • short (setMyShortDescription, ≤120) — «About»: именно его показывает страница t.me.
Пока имя стояло одно на весь мир («Учебный помощник»), посетитель из Турции или Бразилии
видел кириллицу первым, что о боте узнавал. Telegram умеет держать КАЖДОЕ из трёх полей
на каждый язык (`language_code`), и это не использовалось.

ИСТОЧНИК — ТОЛЬКО РЕЕСТР tools/bot-profile.json (как site.json для адреса, subjects.json для
предметов). Руками в Telegram профиль не правится: правка текста = правка реестра, этот
скрипт, затем батарея `landing-bot-profile.py` сверяет ЖИВУЮ страницу и ЖИВОЙ Bot API.

Слот без language_code — для всех языков, которых в профиле нет; его текст берётся из
слота `default` реестра (там английский — язык сайта по умолчанию).

Токен читается из study-bot/.env (`BOT_ENV` переопределяет путь) и НИКОГДА не печатается.
Пишет только в Telegram; в репозиторий не пишет ничего.

ЗАПУСК:
  python3 tools/apply-bot-profile.py            # поставить всё и проверить чтением
  python3 tools/apply-bot-profile.py --check    # только прочитать и сверить с реестром
  python3 tools/apply-bot-profile.py --only name
Коды: 0 — всё сошлось, 1 — расхождения, 2 — нет токена/сети (не «зелено», а «не проверено»).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

LANDING = Path(__file__).resolve().parent.parent
PROFILE = LANDING / "tools" / "bot-profile.json"
# Путь по умолчанию — ОТНОСИТЕЛЬНО репозитория (рядом лежит каталог бота), без адресов
# сервера: файл лежит в публичном репозитории. Другое место — переменной BOT_ENV.
DEFAULT_ENV = LANDING.parent.parent / "study-bot" / ".env"
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]

# Поле реестра → (метод записи, метод чтения, ключ в ответе, лимит по умолчанию)
FIELDS = {
    "name": ("setMyName", "getMyName", "name", 64),
    "long": ("setMyDescription", "getMyDescription", "description", 512),
    "short": ("setMyShortDescription", "getMyShortDescription", "short_description", 120),
}


def token() -> str:
    env = Path(os.environ.get("BOT_ENV", str(DEFAULT_ENV)))
    if not env.exists():
        raise SystemExit(f"нет файла с токеном: {env}")
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("BOT_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"нет BOT_TOKEN в {env}")


def api(tok: str, method: str, **params) -> dict:
    url = f"https://api.telegram.org/bot{tok}/{method}"
    data = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:  # ошибка Telegram — тоже ответ, а не падение
        try:
            return json.loads(exc.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            return {"ok": False, "error_code": exc.code, "description": f"HTTP {exc.code}"}
    except Exception as exc:  # noqa: BLE001 — нет сети: это код 2, а не «не сошлось»
        return {"ok": False, "error_code": 0, "description": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="name,long,short", help="name,long,short (через запятую)")
    ap.add_argument("--check", action="store_true", help="только прочитать и сверить с реестром")
    args = ap.parse_args()

    reg = json.loads(PROFILE.read_text(encoding="utf-8"))
    default_lang = reg.get("default", "en")
    tok = token()

    me = api(tok, "getMe")
    if not me.get("ok"):
        print(f"НЕ ПРОВЕРЕНО: Bot API не ответил — {me.get('description')}")
        return 2
    print(f"бот @{(me.get('result') or {}).get('username')}")

    bad: list[str] = []
    for key in [k.strip() for k in args.only.split(",") if k.strip()]:
        if key not in FIELDS:
            raise SystemExit(f"неизвестное поле: {key}")
        setter, getter, field, lim_default = FIELDS[key]
        block = reg.get(key) or {}
        texts = block.get("texts") or {}
        lim = int(block.get("limit", lim_default))
        if not texts:
            bad.append(f"{key}: в реестре нет текстов")
            print(f"\n== {key}: в реестре нет текстов — пропуск")
            continue

        now = (api(tok, getter).get("result") or {}).get(field, "")
        print(f"\n== {key} (лимит {lim}); слот по умолчанию сейчас: {len(now)} симв. {now[:70]!r}")

        # «Слот по умолчанию» и «слот en» — РАЗНЫЕ поля Telegram, и это выяснилось на живом
        # боте: имя стояло в слоте по умолчанию, а getMyName(language_code="en") отдавал
        # пустоту, то есть реестр называл девять слотов, а на боте было восемь и дефолт.
        # Поэтому пишутся ОБА: сначала слот по умолчанию (для языков без своей версии),
        # затем каждый из девяти языков — своим слотом, включая язык по умолчанию.
        plan: list[tuple[str | None, str, str]] = [(None, default_lang, texts.get(default_lang, ""))]
        plan += [(l, l, texts.get(l, "")) for l in LANGS]

        for code, lang, text in plan:
            mark = " (слот по умолчанию)" if code is None else ""
            if not text:
                bad.append(f"{key}/{code or 'default'}: пусто в реестре")
                print(f"НЕТ {str(code):4s} пусто в реестре")
                continue
            if len(text) > lim:
                bad.append(f"{key}/{code or 'default'}: {len(text)} > {lim}")
                print(f"ДЛИННО {str(code):4s} {len(text)}")
                continue
            if args.check:
                continue
            res = api(tok, setter, **{field: text, "language_code": code})
            if res.get("ok"):
                print(f"SET {str(code):4s} {len(text):4d}{mark}")
            else:
                bad.append(f"{key}/{code or 'default'}: {res.get('error_code')} {res.get('description')}")
                print(f"BAD {str(code):4s} {res.get('error_code')} {res.get('description')}")

        print(f"ЧТЕНИЕ ОБРАТНО ({key}):")
        for code, lang, want in plan:
            res = api(tok, getter, language_code=code)
            got = (res.get("result") or {}).get(field, "")
            same = got == want
            if not same:
                bad.append(f"{key}/{code or 'default'}: чтение разошлось")
            print(f"{'OK ' if same else 'НЕТ'} {str(code):4s} {len(got):4d} {got[:52]!r}")

    print(f"\nрасхождений: {len(bad)}")
    for b in bad:
        print("  ", b)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
