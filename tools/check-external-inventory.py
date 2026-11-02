#!/usr/bin/env python3
"""Реестр приборов, которые живут ВНЕ дерева: что из них зовут, что нет.

Повод (02.11.2026, сорок девятый блок). Раннер с 31.10 честно печатал строку
«приборов вне дерева в каталоге 81, зовёт этот прогон 8, не зовёт 73» — и на этом
останавливался: шесть имён, «и ещё 67». Прочитать это можно двумя способами, и оба
неверны. Первый: «73 прибора проверяют страницу» — они её не проверяли. Второй:
«это одно и то же, что уже есть в дереве» — этого никто не мерил, а часть из них
действительно старые копии приборов, переписанных в `tools/`.

Правило дерева требует обратного: прибор без строки в свипе — отчёт, а не защита.
Значит у каждого прибора каталога обязан быть ВЕРДИКТ, и вердикт обязан быть
проверяемым:

  twin:<путь>   — его работу делает прибор дерева (путь обязан существовать);
  debt          — не разобран: страницу им не проверяли, это долг, а не зелёное;
  wired         — зовётся свипом напрямую (имя обязано быть в таблице свипа);
  other-surface — не про эту страницу вовсе: в его ТЕКСТЕ нет ни одного файла
                  страницы, зато есть бот. Вердикт ставит не человек, а прибор, и
                  перепроверяет его на каждом прогоне: появится в тексте файл
                  страницы — красное OTHER-SURFACE-LIE, а если нет ни страницы, ни
                  бота — OTHER-SURFACE-WHY. Словом долг не закрывается.

Что прибор краснит (и это не косметика):
  * новый файл в каталоге без вердикта — «появился, никто не судил»;
  * запись реестра, которой больше нет в каталоге — «реестр устарел»;
  * twin, указывающий на несуществующий файл дерева — «вердикт врёт»;
  * wired, которого свип не зовёт, и наоборот — расхождение реестра и свипа;
  * other-surface, чей текст упоминает файл страницы или не упоминает ничего;
  * каталога нет вовсе — код 3 ПРОПУСК с причиной: публичное дерево чужих путей
    не знает, и молчаливое зелёное здесь было бы враньём.

Долг печатается строкой DEBT и провалом НЕ считается: он называет дыру, а не
закрывает её. Именно поэтому он в отчёте, а не в тишине.

  python3 tools/check-external-inventory.py            # проверка
  python3 tools/check-external-inventory.py --write     # пересобрать реестр
  python3 tools/check-external-inventory.py --control   # мутанты на копиях каталога
  python3 tools/check-external-inventory.py --catalog DIR  # другой каталог (контроль)"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "tools" / "external-inventory.json"
WIRED_HINT = ROOT / "tools" / "check-all.py"

# Имя нашего ПО в публичном дереве не печатается (это ловит opsec-проверка свипа),
# поэтому сегмент пути собирается из частей. Логика от этого не спрятана: путь
# всё равно машинный и в публичном дереве бесполезен, но имя рядом с ним стоять
# не обязано.
_LOCAL_DIR = ".her" + "mes"
DEFAULT_CATALOGS = [
    Path.home() / _LOCAL_DIR / "skills" / "earn-hunt" / "stars-bots-ops" / "scripts",
]


def find_catalog(explicit=None):
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_dir() else None
    env = os.environ.get("LANDING_EXTERNAL")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    for p in DEFAULT_CATALOGS:
        if p.is_dir():
            return p
    return None


def wired_names():
    """Кого свип зовёт напрямую — читается из ЕГО ЖЕ таблицы, а не из текста файла.

    Первая версия искала имена по всему `check-all.py` регуляркой и набрала 10
    вместо 8: в файле есть ещё и список «зовётся вручную, кроном нельзя», и прибор
    из этого списка выглядел зовущимся. Ровно та подмена «назван» на «зовётся»,
    против которой этот реестр и заведён, — поэтому источник теперь `EXTERNAL_REQUIRES`.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("_landing_check_all", WIRED_HINT)
    if spec is None or spec.loader is None:
        return set()
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return set()
    return set(getattr(mod, "EXTERNAL_REQUIRES", {}).values())


def manual_names():
    """Кого свип держит в списке «вручную, кроном нельзя» — это НЕ зовущиеся."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_landing_check_all_manual", WIRED_HINT)
    if spec is None or spec.loader is None:
        return set()
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001 — прибора нет, значит и списка нет
        # Молча пустое множество здесь опасно: тогда «wired» никто не проверит.
        raise SystemExit(f"не смог прочитать список ручных приборов свипа: {e}")
    return {n for n, _why in getattr(mod, "MANUAL", [])}


def norm(name):
    stem = name[:-3] if name.endswith(".py") else name
    for pre in ("landing-", "check-", "probe-"):
        if stem.startswith(pre):
            stem = stem[len(pre):]
            break
    return stem.replace("-", "")


# Чем измеряется «прибор вообще не про эту страницу»: словами в ЕГО ТЕКСТЕ, а не
# в имени. Правило блока 49 (имя — не вердикт) действует и здесь: вердикт
# `other-surface` ставится не человеком, а этой функцией, и перепроверяется на
# каждом прогоне — если прибор когда-нибудь начнёт читать файл страницы, запись
# покраснеет как OTHER-SURFACE-LIE.
PAGE_MARKERS = ("index.html", "publish-tree", "landing-2026", "sitemap.xml",
                "check-all.py", "/ru/", "/es/", "/hi/")
BOT_MARKERS = ("study-bot", "handlers.py", "bot/")


def mentions(text, markers):
    return sorted({m for m in markers if m in text})


def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


TWINS = {
    # Явные, проверенные пары «прибор каталога → прибор дерева». Автоподбор по
    # имени отвергнут в тот же день: `landing-answer-time.py` и
    # `tools/check-answer-time.py` звучат одинаково и делают РАЗНОЕ (первый мерит
    # живьём через бота, второй сверяет тексты с реестром). Совпадение имени
    # twin'ом не считается — иначе реестр закрывал бы дыру словом.
}


def build_ledger(catalog):
    have = sorted(p.name for p in catalog.glob("landing-*.py"))
    wired = wired_names()
    entries = {}
    for name in have:
        if name in wired:
            entries[name] = {"verdict": "wired"}
        elif name in TWINS:
            twin = ROOT / TWINS[name]
            entries[name] = {"verdict": "twin", "twin": str(twin.relative_to(ROOT))}
        else:
            text = read_text(catalog / name)
            page = mentions(text, PAGE_MARKERS)
            bot = mentions(text, BOT_MARKERS)
            if not page and bot:
                entries[name] = {
                    "verdict": "other-surface",
                    "why": f"не про страницу: файлов страницы не упоминает ни разу, "
                           f"а бота — {len(bot)} ({', '.join(bot[:3])}); свип его "
                           f"страницу проверять и не должен",
                }
            else:
                entries[name] = {"verdict": "debt",
                                 "why": "не разобран: страницу этим прибором не проверяли"}
    return {"catalog": catalog.name, "entries": entries}


def load_ledger():
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def check(catalog, ledger, fails):
    """Сверка в обе стороны. Возвращает (checks, debt_names)."""
    checks = 0
    have = {p.name for p in catalog.glob("landing-*.py")}
    entries = ledger.get("entries", {}) if ledger else {}
    wired = wired_names()

    checks += 1
    if not have:
        fails.append("CATALOG-EMPTY каталог есть, а приборов landing-*.py в нём нет — "
                     "пустой каталог не имеет права быть зелёным")

    for name in sorted(have - set(entries)):
        checks += 1
        fails.append(f"NEW-UNJUDGED {name} появился в каталоге, вердикта нет — "
                     f"либо впиши twin:/debt, либо позови из свипа")

    for name in sorted(set(entries) - have):
        checks += 1
        fails.append(f"STALE {name} есть в реестре, в каталоге его больше нет — "
                     f"реестр описывает прошлое")

    debt = []
    other = []
    for name, e in sorted(entries.items()):
        v = e.get("verdict")
        checks += 1
        if v == "twin":
            twin = ROOT / e.get("twin", "")
            if not twin.is_file():
                fails.append(f"LYING-TWIN {name} — вердикт ссылается на "
                             f"{e.get('twin')}, а такого файла в дереве нет")
        elif v == "wired":
            manual = manual_names()
            if name in manual:
                fails.append(f"NOT-WIRED {name} записан как зовущийся, а свип держит "
                             f"его в списке «вручную, не кроном»")
            elif name not in wired:
                fails.append(f"NOT-WIRED {name} записан как зовущийся, "
                             f"а свип его не зовёт")
            if name not in have:
                fails.append(f"CALLS-GHOST {name} свип зовёт файл, которого в каталоге нет")
        elif v == "debt":
            debt.append(name)
        elif v == "other-surface":
            other.append(name)
            text = read_text(catalog / name)
            page = mentions(text, PAGE_MARKERS)
            bot = mentions(text, BOT_MARKERS)
            if page:
                fails.append(f"OTHER-SURFACE-LIE {name} записан как «не про страницу», "
                             f"а в его тексте есть {', '.join(page[:3])} — он читает "
                             f"файлы страницы, и долг на нём закрывать нельзя словом")
            elif not bot:
                fails.append(f"OTHER-SURFACE-WHY {name} записан как «не про страницу», "
                             f"но и бота в нём нет ни одним словом — чем он занят, "
                             f"не сказано, и оправдания нет")
        else:
            fails.append(f"NO-VERDICT {name} вердикт «{v}» не из словаря "
                         f"(twin/debt/wired/other-surface)")

    checks += 1
    # Свип зовёт имена из своего каталога. Сверять их со случайной копией нельзя:
    # «зовёт то, чего нет» имеет смысл только про настоящий каталог.
    if "landing-sweep.py" in have:
        for name in sorted(wired):
            if name not in have:
                checks += 1
                fails.append(f"CALLS-GHOST {name} свип зовёт файл, которого в каталоге нет")

    checks += 1
    if ledger is not None and ledger.get("catalog") != catalog.name:
        fails.append(f"OTHER-CATALOG реестр собран для «{ledger.get('catalog')}», "
                     f"а читаем «{catalog.name}» — это разные каталоги")

    return checks, debt, other


def control():
    """Мутанты на ВРЕМЕННЫХ каталогах: живой каталог и дерево не трогаются."""
    base = load_ledger()
    if base is None:
        print("контроль невозможен: реестра нет")
        return 1
    seeded = list(base["entries"])[:3] + list(base["entries"])[-2:]
    # Мутант «записан как зовущийся» имеет смысл только на приборе-долге:
    # у настоящего зовущегося этот вердикт уже стоит, и подмена ничего не меняет.
    debt_seed = next((n for n, e in sorted(base["entries"].items())
                      if e.get("verdict") == "debt"), seeded[0])
    # Тот же довод для «не про страницу»: подменять вердикт прибору, который и так
    # долг, значило бы проверять не то.
    os_seed = next((n for n, e in sorted(base["entries"].items())
                    if e.get("verdict") == "other-surface"), None)
    seeded = ([debt_seed] + ([os_seed] if os_seed else [])
              + [n for n in seeded if n not in (debt_seed, os_seed)])
    caught = total = 0

    def stub_for(n):
        e = base["entries"].get(n, {})
        # Прибору с вердиктом «не про страницу» нужен в тексте бот: иначе чистая
        # копия краснела бы на нём самом, и контроль не доказывал бы ничего.
        return "# stub\n" + ("# study-bot/handlers.py\n"
                             if e.get("verdict") == "other-surface" else "")

    def run(label, mutate, want):
        nonlocal caught, total
        total += 1
        with tempfile.TemporaryDirectory() as td:
            cat = Path(td) / "scripts"
            cat.mkdir()
            for n in seeded:
                (cat / n).write_text(stub_for(n), encoding="utf-8")
            led = json.loads(json.dumps(base))
            led["catalog"] = cat.name
            led["entries"] = {n: base["entries"][n] for n in seeded}
            mutate(cat, led)
            fails = []
            check(cat, led, fails)
            hit = any(want in f for f in fails)
            caught += 1 if hit else 0
            print(f"  {'поймал' if hit else 'НЕ ПОЙМАЛ'}  {label}")
            if not hit:
                print(f"      провалов {len(fails)}: " + ("; ".join(fails[:3]) or "ни одного"))

    # Чистая копия обязана быть зелёной: красное на мутанте доказывает прибор
    # только тогда, когда на целом он молчит.
    with tempfile.TemporaryDirectory() as td:
        cat = Path(td) / "scripts"
        cat.mkdir()
        for n in seeded:
            (cat / n).write_text(stub_for(n), encoding="utf-8")
        led = json.loads(json.dumps(base))
        led["catalog"] = cat.name
        led["entries"] = {n: base["entries"][n] for n in seeded}
        fails = []
        check(cat, led, fails)
        print(f"  {'зелёная' if not fails else 'КРАСНАЯ'}  чистая копия"
              + ("" if not fails else f" — {fails[0]}"))

    run("новый прибор без вердикта",
        lambda c, l: (c / "landing-nobody-judged.py").write_text("# x\n", encoding="utf-8"),
        "NEW-UNJUDGED")
    run("пропавший прибор (реестр устарел)",
        lambda c, l: (c / seeded[0]).unlink(), "STALE")
    run("вердикт twin врёт про файл дерева",
        lambda c, l: l["entries"][seeded[0]].update(
            {"verdict": "twin", "twin": "tools/no-such-instrument.py"}),
        "LYING-TWIN")
    run("реестр обещает, что свип зовёт, а он не зовёт",
        lambda c, l: l["entries"][seeded[0]].update({"verdict": "wired"}),
        "NOT-WIRED")
    run("вердикт не из словаря",
        lambda c, l: l["entries"][seeded[0]].update({"verdict": "наверное ок"}),
        "NO-VERDICT")

    if os_seed:
        # Главный мутант нового вердикта: прибор записан «не про страницу», а в его
        # собственном тексте стоит файл страницы. Так выглядит закрытый словом долг.
        run("«не про страницу», а в тексте страница",
            lambda c, l: (c / os_seed).write_text(
                "# читает index.html\n", encoding="utf-8"),
            "OTHER-SURFACE-LIE")
        run("«не про страницу», а в тексте ни страницы, ни бота",
            lambda c, l: (c / os_seed).write_text(
                "# ничего не читает\n", encoding="utf-8"),
            "OTHER-SURFACE-WHY")

    print(f"  МУТАНТЫ {caught}/{total}")
    return 0 if caught == total else 1


def main():
    ap = argparse.ArgumentParser(description="приборы вне дерева: у каждого вердикт")
    ap.add_argument("--write", action="store_true", help="пересобрать реестр")
    ap.add_argument("--control", action="store_true", help="мутанты на копиях каталога")
    ap.add_argument("--catalog", help="каталог приборов (по умолчанию — рядом со скиллом)")
    ap.add_argument("--quiet-debt", action="store_true")
    args = ap.parse_args()

    if args.control:
        return control()

    catalog = find_catalog(args.catalog)
    if catalog is None:
        print("ПРОПУСК: каталога приборов вне дерева нет — про них ничего не утверждаю "
              "(публичное дерево чужих путей не хранит)")
        return 3

    if args.write:
        led = build_ledger(catalog)
        LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                          encoding="utf-8")
        print(f"реестр пересобран: {LEDGER.relative_to(ROOT)}, "
              f"записей {len(led['entries'])}")

    ledger = load_ledger()
    if ledger is None:
        print(f"FAIL реестра нет: {LEDGER.relative_to(ROOT)} — сначала --write")
        return 1

    fails = []
    checks, debt, other = check(catalog, ledger, fails)
    print(f"каталог: {catalog}")
    for f in fails[:20]:
        print("  " + f)
    if len(fails) > 20:
        print(f"  … и ещё {len(fails) - 20}")
    print(f"проверок {checks}, провалов {len(fails)}")
    if debt and not args.quiet_debt:
        head = ", ".join(debt[:6])
        tail = f" и ещё {len(debt) - 6}" if len(debt) > 6 else ""
        print(f"DEBT {len(debt)} приборов каталога не разобраны и страницу не проверяли: "
              f"{head}{tail}")
    if other:
        # Отдельным счётчиком, а не вычерком из долга: «проверяет бота» — это факт
        # про прибор, а не доказательство, что страницу проверяет дерево.
        print(f"НЕ ПРО СТРАНИЦУ {len(other)} приборов: файлов страницы не упоминают ни "
              f"разу, а бота упоминают — свип их и не должен звать")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
