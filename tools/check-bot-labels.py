#!/usr/bin/env python3
"""check-bot-labels.py — слышит ли бот те метки, которые обещает страница.

Повод (01.11.2026, блок 25). У ссылок на бота две работы, и до этого прибора ни одну
из них не сторожил ни один прибор. Грамматику меток держит бот
(`study-bot/bot/handlers.py`, `_LANDING_LABEL`), а пишет метки страница — и разъезжались
они молча: у бота одна правда, у лендинга другая, сверять некому.

Что нашлось, когда сверили:

  1) Метка ИИ-слоя `src_llms` ботом НЕ слышится: `landing_lang()` возвращает None, язык
     берётся из интерфейса Telegram. Это осознанный компромисс, а не забытая строка
     (см. комментарий у `BOT_LLMS` в build.py): документ llms.txt английский, но человек,
     пришедший по ссылке из ИИ, чаще хочет свой язык интерфейса, а не английский.
     Цена — ИИ-переход виден в источнике, но не в выборе языка.
  2) Языковые метки страниц (`src_landing_<код>[_band|_shots|_sticky]`) обязаны совпадать
     с языком страницы: опечатка в коде языка отправляет русского на испанскую страницу,
     и это не видно ни сборке, ни свипу.

Проверки прибора:

  A. Метка ИИ-слоя одна на весь слой: ровно она стоит в llms.txt и во всех десяти
     md-двойниках. Разъехалась — ИИ-трафик считается по-разному, и это не заметит никто.
  B. Каждая метка страницы разбирается грамматикой бота (иначе бот молча её выбросит)
     и код в ней равен языку файла.
  C. Метка без языка (`src_landing_404`) допустима ТОЛЬКО на странице 404: там языка
     нет по устройству, и падение в язык Telegram — решение, а не авария.
  D. Если бот когда-нибудь научится метке ИИ-слоя, прибор скажет об этом вслух: тогда
     источник и язык можно свести в одну метку, и молчать об этом нельзя.

Грамматика берётся из кода бота, а не переписана сюда: копия разъехалась бы молча.
Если код бота недоступен, прибор НЕ притворяется зелёным — печатает ПРОПУСК и код 3.

  python3 tools/check-bot-labels.py             # дерево + код бота
  python3 tools/check-bot-labels.py --control   # четыре мутанта обязаны покраснеть
"""

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
BUCKET = "src_llms"
# Код бота лежит рядом, в соседнем проекте: путь считается от этого файла, а не пишется
# литералом — свип справедливо запрещает серверные пути в том, что отдаётся наружу.
BOT_HANDLERS = Path(os.environ.get(
    "LANDING_BOT_HANDLERS", ROOT.parents[1] / "study-bot" / "bot" / "handlers.py"))
LINK = re.compile(r"t\.me/UchiSamBot\?start=([A-Za-z0-9_]+)")
NOLANG = re.compile(r"^src_landing_(\d+)$")


def bot_grammar() -> re.Pattern:
    """Грамматика меток из кода бота — единственный источник правды."""
    text = BOT_HANDLERS.read_text(encoding="utf-8")
    m = re.search(r'_LANDING_LABEL\s*=\s*re\.compile\(r"([^"]+)"\)', text)
    if not m:
        raise SystemExit(f"ПРОПУСК: в {BOT_HANDLERS} не нашёл _LANDING_LABEL")
    return re.compile(m.group(1))


def lang_of_file(rel: str) -> str | None:
    """Язык файла по его месту в дереве; None — файл языка не знает."""
    parts = rel.split("/")
    if len(parts) == 1:
        return "en" if parts[0] in ("index.html", "index.html.md") else None
    if len(parts) == 2 and parts[1] in ("index.html", "index.html.md"):
        return parts[0] if parts[0] in LANGS else None
    return None


def tree_files(root: Path) -> list[str]:
    out = [p.relative_to(root).as_posix() for p in root.rglob("*")
           if p.is_file() and (p.name.endswith(".html") or p.name.endswith(".md")
                               or p.name == "llms.txt")
           and p.name != "index-src.html"          # шаблон: в нём макроподстановки, а не метки
           and ".shots-work" not in p.as_posix() and "evidence" not in p.as_posix()]
    return sorted(out)


def scan(root: Path, grammar: re.Pattern) -> tuple[int, list[str], int]:
    checks, bad, _n = 0, [], 0
    bucket_seen: dict[str, str] = {}
    for rel in tree_files(root):
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        want = lang_of_file(rel)
        labels = LINK.findall(text)
        is_ai = rel == "llms.txt" or rel.endswith(".html.md")
        if not is_ai and want and not labels:
            checks += 1
            bad.append(f"{rel}: ни одной ссылки на бота с меткой — молчание не обещание")
        for label in labels:
            checks += 1
            if is_ai:
                bucket_seen[rel] = label
                if label != BUCKET:
                    if rel == "llms.txt":
                        bad.append(f"llms.txt: верхняя ссылка ведёт не в метку ИИ-слоя ({label})")
                    else:
                        bad.append(f"{rel}: метка ИИ-слоя разъехалась — {label} вместо {BUCKET}")
                continue
            m = grammar.fullmatch(label)
            if not m:
                if NOLANG.fullmatch(label) and rel == "404.html":
                    continue
                bad.append(f"{rel}: бот не слышит метку '{label}' (даст язык Telegram)")
                continue
            code = m.group(1)
            if want and code != want:
                bad.append(f"{rel}: язык файла {want}, а метка ведёт в {code} ('{label}')")
    if not bucket_seen:
        checks += 1
        bad.append("ИИ-слой: нет ни одной ссылки на бота — обещание агента проверять не на чем")
    checks += 1
    if bucket_seen and len(set(bucket_seen.values())) > 1:
        bad.append(f"ИИ-слой: метки разъехались по файлам — {sorted(set(bucket_seen.values()))}")
    return checks, bad, len(bucket_seen)


def control(tmp: Path) -> int:
    clean = tmp / "clean"
    shutil.copytree(ROOT, clean, ignore=shutil.ignore_patterns(
        ".git", "evidence", "tools", "src", "node_modules", ".shots-work"))
    grammar = bot_grammar()
    if scan(clean, grammar)[1]:
        print("КОНТРОЛЬ СЛОМАН: чистая копия не зелёная:")
        for line in scan(clean, grammar)[1]:
            print("  ", line)
        return 1
    mut = tmp / "mut"
    shutil.copytree(clean, mut)
    ru = mut / "ru" / "index.html"
    ru.write_text(ru.read_text(encoding="utf-8").replace(
        "start=src_landing_ru", "start=src_landing_es", 1), encoding="utf-8")
    uk = mut / "uk" / "index.html"
    uk.write_text(uk.read_text(encoding="utf-8").replace(
        "start=src_landing_uk", "start=src_landing", 1), encoding="utf-8")
    llms = mut / "llms.txt"
    llms.write_text(llms.read_text(encoding="utf-8").replace(
        f"start={BUCKET}", "start=src_landing_en", 1), encoding="utf-8")
    hi = mut / "hi" / "index.html.md"
    hi.write_text(hi.read_text(encoding="utf-8").replace(
        f"start={BUCKET}", "start=src_landing_hi", 1), encoding="utf-8")
    _c, bad, _n = scan(mut, grammar)
    expect = ["язык файла ru, а метка ведёт в es",
              "бот не слышит метку 'src_landing'",
              "llms.txt: верхняя ссылка ведёт не в метку ИИ-слоя",
              "hi/index.html.md: метка ИИ-слоя разъехалась"]
    caught = sum(1 for e in expect if any(e in line for line in bad))
    for line in bad:
        print("  поймано:", line)
    print(f"КОНТРОЛЬ: чистая копия зелёная, мутант поймал {caught}/4")
    return 0 if caught == 4 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="метки ссылок на бота против грамматики бота")
    ap.add_argument("--control", action="store_true", help="четыре мутанта обязаны покраснеть")
    a = ap.parse_args()
    if not BOT_HANDLERS.exists():
        print(f"ПРОПУСК: код бота недоступен ({BOT_HANDLERS}) — метки не сверены с ботом")
        return 3
    if a.control:
        with tempfile.TemporaryDirectory() as td:
            return control(Path(td))
    grammar = bot_grammar()
    checks, bad, files = scan(ROOT, grammar)
    for line in bad:
        print("  КРАСНО:", line)
    if grammar.fullmatch(BUCKET):
        print("  ВНИМАНИЕ: бот научился метке ИИ-слоя — источник и язык можно свести в одну метку")
    print(f"CHECKS: {checks}")
    print(f"FAILED: {len(bad)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
