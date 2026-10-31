#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""controls-mutation.py — мутационный контроль приборов лендинга.

31.10.2026. Раннер печатал зелёное «ИТОГО», а у десяти приборов из девятнадцати
не было ни одного способа увидеть красное. Прибор, которого никогда не видели
красным, — это не проверка, а расписка: он может быть сломан ровно так, что
зелёный цвет ничего не значит (30.10 у locale-key-parity и placeholder-parity
вообще не было sys.exit — они возвращали 0 всегда).

Механика. Каждый прибор считает корнем репозитория папку своего файла
(`Path(__file__).parent.parent` или `os.chdir(dirname(dirname(abspath(__file__))))`).
Значит достаточно скопировать дерево, внести ОДИН известный дефект и запустить
прибор из копии: он обязан покраснеть и назвать именно этот дефект. Копия на
немутированном дереве обязана быть зелёной — иначе красное ничего не доказывает.

Требования к рецепту:
  * код возврата != 0 на мутанте;
  * ожидаемая подстрока в выводе (чтобы прибор не покраснел по посторонней причине);
  * код возврата == 0 на контроле без мутации;
  * мутация снимается при следующем запуске (работа только в копии).

Использование:
  python3 tools/controls-mutation.py            # все рецепты
  python3 tools/controls-mutation.py --only og  # подстрока имени рецепта
  python3 tools/controls-mutation.py --list
  python3 tools/controls-mutation.py --json     # доказательство в evidence/
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
COPY_EXCLUDE = {".git", ".shots-work", "evidence", "__pycache__", "node_modules"}


# ---------------------------------------------------------------- рецепты ----
def mut_internal_links(tree: Path) -> tuple[bool, str]:
    """Битая внутренняя ссылка: якорь, которого нет на целевой странице."""
    page = tree / "ru" / "index.html"
    html = page.read_text(encoding="utf-8")
    probe = 'zzz-probe-anchor-31oct'
    marker = "</body>"
    if marker not in html:
        return False, "на ru/index.html нет </body> — рецепт не применим"
    page.write_text(html.replace(marker, f'<a href="#{probe}">x</a>\n{marker}', 1),
                    encoding="utf-8")
    return True, f"в ru/index.html добавлена ссылка #{probe}"


def mut_site_technical(tree: Path) -> tuple[bool, str]:
    """Из шапки ru/index.html выпадает hreflang украинского языка."""
    page = tree / "ru" / "index.html"
    html = page.read_text(encoding="utf-8")
    start = html.find('<link rel="alternate" hreflang="uk"')
    if start < 0:
        return False, "в шапке ru/index.html нет <link hreflang=\"uk\"> — рецепт не применим"
    end = html.find(">", start) + 1
    page.write_text(html[:start] + html[end:], encoding="utf-8")
    return True, 'в шапке ru/index.html удалён <link hreflang="uk">'


def mut_locale_keys(tree: Path) -> tuple[bool, str]:
    """Ключ, который знает один язык и не знает страница: DEAD + UNEVEN."""
    loc = tree / "src" / "locales" / "en.json"
    data = json.loads(loc.read_text(encoding="utf-8"))
    data["zzz_dead_probe"] = "probe text that no page ever asks for"
    loc.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True, "в src/locales/en.json добавлен ключ zzz_dead_probe"


def mut_placeholders(tree: Path) -> tuple[bool, str]:
    """Плейсхолдер, протёкший на собранную страницу."""
    page = tree / "index.html"
    html = page.read_text(encoding="utf-8")
    marker = "</body>"
    if marker not in html:
        return False, "в index.html нет </body> — рецепт не применим"
    page.write_text(html.replace(marker, "<p>{zzz_probe_probe}</p>\n" + marker, 1),
                    encoding="utf-8")
    return True, "на index.html выведен литерал {zzz_probe_probe}"


def mut_og_cards(tree: Path) -> tuple[bool, str]:
    """Карточка og: на один язык подменена картинкой чужого размера."""
    cards = sorted((tree / "img").glob("og-*.png"))
    if not cards:
        return False, "в img нет карточек og-*.png — рецепт не применим"
    victim = next((c for c in cards if c.stem in ("og-ru", "og-en")), cards[0])
    icon = [i for i in sorted((tree / "img").rglob("*.png"))
            if not i.name.startswith("og-") and i.stat().st_size < 60_000]
    if not icon:
        return False, "нет маленькой png для подмены — рецепт не применим"
    shutil.copyfile(icon[0], victim)
    return True, f"img/{victim.name} заменена на {icon[0].relative_to(tree)} (чужой размер)"


RECIPES = [
    dict(name="internal-links", tool="tools/check-internal.py", args=[],
         mutate=mut_internal_links, expect="нет якоря"),
    dict(name="site-technical", tool="tools/check-site-technical.py", args=["--offline"],
         mutate=mut_site_technical, expect="нет языка uk"),
    dict(name="locale-keys", tool="tools/locale-key-parity.py", args=[],
         mutate=mut_locale_keys, expect="UNEVEN"),
    dict(name="placeholders", tool="tools/placeholder-parity.py", args=[],
         mutate=mut_placeholders, expect="zzz_probe_probe"),
    dict(name="og-cards", tool="tools/og-cards.py", args=["--check"],
         mutate=mut_og_cards, expect="ДРЕЙФ"),
]


# ---------------------------------------------------------------- механика ---
def copy_tree(dst: Path) -> None:
    def ignore(dir_path, names):
        return [n for n in names if n in COPY_EXCLUDE]
    shutil.copytree(ROOT, dst, ignore=ignore, symlinks=True)


def run(tool: str, args: list[str], where: Path) -> tuple[int, str, float]:
    t0 = time.time()
    proc = subprocess.run([sys.executable, tool, *args], cwd=str(where),
                          capture_output=True, text=True, timeout=600)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out, time.time() - t0


def last_relevant(out: str, expect: str, height: int = 6) -> list[str]:
    lines = [l.rstrip() for l in out.splitlines() if l.strip()]
    hits = [l for l in lines if expect and expect in l]
    tail = lines[-height:]
    picked = hits[:3] + [l for l in tail if l not in hits[:3]]
    return picked[:8]


def check_recipe(r: dict) -> dict:
    name = r["name"]
    result: dict[str, Any] = dict(name=name, tool=r["tool"], ok=False, reason="",
                                  seconds=0.0, mutation="", control_rc=None,
                                  mutant_rc=None, evidence=[])
    base = Path(tempfile.mkdtemp(prefix=f"ctrl-{name}-"))
    try:
        clean = base / "clean"
        copy_tree(clean)
        rc, out, dt = run(r["tool"], r["args"], clean)
        result["control_rc"] = rc
        result["seconds"] += dt
        if rc != 0:
            result["reason"] = ("прибор краснеет на НЕмутированном дереве — "
                                "красное на мутанте ничего не докажет")
            result["evidence"] = last_relevant(out, "", 8)
            return result

        mutant = base / "mutant"
        shutil.copytree(clean, mutant, symlinks=True)
        applied, note = r["mutate"](mutant)
        result["mutation"] = note
        if not applied:
            result["reason"] = note
            return result

        rc, out, dt = run(r["tool"], r["args"], mutant)
        result["mutant_rc"] = rc
        result["seconds"] += dt
        expect = r["expect"]
        if rc == 0:
            result["reason"] = "зелёный на мутанте: дефект не назван"
        elif expect and expect not in out:
            result["reason"] = f"покраснел, но не назвал дефект (ждали «{expect}»)"
        else:
            result["ok"] = True
            result["reason"] = "покраснел и назвал дефект"
        result["evidence"] = last_relevant(out, expect)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="мутационный контроль приборов: каждый обязан быть увиден красным")
    ap.add_argument("--only", default="", help="подстрока имени рецепта")
    ap.add_argument("--list", action="store_true", help="напечатать рецепты и выйти")
    ap.add_argument("--json", action="store_true", help="доказательство в evidence/")
    a = ap.parse_args()

    picked = [r for r in RECIPES if a.only.lower() in r["name"].lower()]
    if not picked:
        print(f"нет рецептов под «{a.only}»; есть: "
              + ", ".join(r["name"] for r in RECIPES))
        return 2
    if a.list:
        for r in RECIPES:
            print(f"  {r['name']:<16} {r['tool']:<32} ждём: {r['expect'] or '(любой красный)'}")
        return 0

    print(f"рецептов: {len(picked)}  корень: {ROOT}")
    bad = 0
    rows = []
    for r in picked:
        res = check_recipe(r)
        rows.append(res)
        flag = "ok  " if res["ok"] else "FAIL"
        print(f"  {flag} {res['name']:<16} контроль:{res['control_rc']} "
              f"мутант:{res['mutant_rc']} {res['seconds']:.1f} с — {res['reason']}")
        for line in res["evidence"][:4]:
            print(f"         | {line[:150]}")
        if not res["ok"]:
            bad += 1
    print(f"ИТОГО рецептов: {len(rows)}  недоказанных: {bad}")

    if a.json:
        out = ROOT / "evidence" / "controls-mutation.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(
            {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "recipes": rows},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"журнал: {out.relative_to(ROOT)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
