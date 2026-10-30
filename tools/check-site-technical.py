#!/usr/bin/env python3
"""check-site-technical.py — три проверки, которых до 30.10.2026 не было в репозитории.

Повод. 30.10.2026 технический блок прогонялся руками, одноразовыми скриптами в
каталоге вне репозитория: сверка живого сайта с деревом, шапки девяти страниц
(canonical / hreflang / og:url) и чисел в девяти словарях. Результат был чистый,
но проверки жили один запуск: следующий прогон начал бы с нуля и с теми же
руками. Здесь они сложены в один прибор.

Что проверяется:

  1) шапка каждого языка — <html lang> совпадает с кодом языка; canonical и
     og:url указывают ровно на канонический адрес этой страницы (EN живёт в
     корне, остальные — в <code>/); набор hreflang — девять языков плюс
     x-default, каждый адрес верный. Классическая поломка — перепутанный
     hreflang после добавления языка: поисковик склеивает две страницы в одну.

  2) числа в словарях — для каждого ключа с цифрами в src/locales/*.json набор
     чисел обязан совпадать с английским. Цена «30 звёзд» в одном языке и «50»
     в другом невидима ни одной из существующих проверок: locale-key-parity
     смотрит только наличие ключа, placeholder-parity — только {подстановки}.

  3) живой сайт против дерева — побайтовая сверка девяти страниц, юридических
     страниц, 404, sitemap, llms.txt, robots.txt. Ловит «закоммитили, но не
     выложили»: правка обещания лежит в репозитории, а человек читает старую.

Запуск:
  python3 tools/check-site-technical.py              # всё, включая сеть
  python3 tools/check-site-technical.py --offline    # только диск (быстро)

Read-only. Возврат 0 — чисто, 1 — есть расхождения (печатаются с именем класса).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NUM = re.compile(r"\d+(?:[.,]\d)?")


def pages() -> list[tuple[str, str]]:
    """(код языка, путь от корня сайта), EN первым."""
    out = [("en", "index.html")]
    for p in sorted(glob.glob(str(ROOT / "src" / "locales" / "*.json"))):
        code = Path(p).stem
        if code != "en":
            out.append((code, f"{code}/index.html"))
    return out


def base() -> str:
    try:
        return json.loads((ROOT / "tools" / "site.json").read_text("utf-8"))["base"]
    except Exception:
        return ""


def canonical_for(code: str, site: str) -> str:
    return site if code == "en" else f"{site}{code}/"


def one(pat: str, text: str) -> str | None:
    m = re.search(pat, text, re.I | re.S)
    return m.group(1).strip() if m else None


def check_head(site: str) -> list[str]:
    codes = [c for c, _ in pages()]
    bad: list[str] = []
    for code, path in pages():
        html = (ROOT / path).read_text("utf-8")
        head = html[: html.find("</head>")] if "</head>" in html else html
        lang = one(r'<html[^>]*\blang="([^"]*)"', head)
        if lang != code:
            bad.append(f"HEAD lang {path}: <html lang={lang}> вместо {code}")
        want = canonical_for(code, site)
        canon = one(r'<link[^>]+rel="canonical"[^>]+href="([^"]*)"', head)
        if canon != want:
            bad.append(f"HEAD canonical {path}: {canon} вместо {want}")
        ogurl = one(r'<meta[^>]+property="og:url"[^>]+content="([^"]*)"', head)
        if ogurl != want:
            bad.append(f"HEAD og:url {path}: {ogurl} вместо {want}")
        alts = dict(re.findall(
            r'<link[^>]+rel="alternate"[^>]+hreflang="([^"]+)"[^>]+href="([^"]+)"',
            head, re.I))
        if not alts:
            alts = dict(re.findall(
                r'<link[^>]+hreflang="([^"]+)"[^>]+rel="alternate"[^>]+href="([^"]+)"',
                head, re.I))
        for c in codes:
            if c not in alts:
                bad.append(f"HEAD hreflang {path}: нет языка {c}")
            elif alts[c] != canonical_for(c, site):
                bad.append(f"HEAD hreflang {path}: {c} -> {alts[c]}"
                           f" вместо {canonical_for(c, site)}")
        if alts.get("x-default") != site:
            bad.append(f"HEAD hreflang {path}: x-default={alts.get('x-default')}"
                       f" вместо {site}")
        for extra in sorted(set(alts) - set(codes) - {"x-default"}):
            bad.append(f"HEAD hreflang {path}: лишний язык {extra}")
    return bad


def check_numbers() -> list[str]:
    locs = {Path(p).stem: json.loads(Path(p).read_text("utf-8"))
            for p in sorted(glob.glob(str(ROOT / "src" / "locales" / "*.json")))}
    bad: list[str] = []
    keys = sorted(set().union(*[set(d) for d in locs.values()]))
    for k in keys:
        got = {lang: sorted(NUM.findall(d[k])) for lang, d in locs.items()
               if isinstance(d.get(k), str) and NUM.search(d[k])}
        if not got:
            continue
        if "en" not in got:
            bad.append(f"NUM {k}: числа есть в {sorted(got)}, в английском нет")
            continue
        ref = got["en"]
        for lang, val in sorted(got.items()):
            if val != ref:
                bad.append(f"NUM {k} [{lang}]: {val} вместо en={ref}")
    return bad


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_live(site: str) -> list[str]:
    if not site:
        return ["LIVE: tools/site.json без base — сверять не с чем"]
    files = [p for _, p in pages()] + ["privacy.html", "terms.html", "404.html",
                                       "sitemap.xml", "llms.txt", "robots.txt"]
    bad: list[str] = []
    for f in files:
        url = site + f
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "check-site-technical"})
            with urllib.request.urlopen(req, timeout=30) as r:
                live = r.read()
        except Exception as e:  # noqa: BLE001
            bad.append(f"LIVE {f}: не открылся — {e}")
            continue
        disk = (ROOT / f).read_bytes()
        if sha(live) != sha(disk):
            bad.append(f"LIVE {f}: живой {len(live)} б, в дереве {len(disk)} б —"
                       f" выложено не то, что в репозитории")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="без сети: только диск")
    args = ap.parse_args()

    os.chdir(ROOT)
    site = base()
    problems: list[str] = []
    problems += check_head(site)
    problems += check_numbers()
    if not args.offline:
        problems += check_live(site)

    checks = len(pages()) * 3 + len(pages()) * 2 + 3
    if problems:
        for p in problems:
            print("FAIL", p)
        print(f"\nПРОБЛЕМ: {len(problems)}")
        return 1
    print(f"шапка: {len(pages())} страниц, canonical/hreflang/og:url — чисто")
    print("числа: все ключи с цифрами согласны с английским")
    if not args.offline:
        print("живой сайт: побайтово совпадает с деревом")
    print(f"CHECKS: {checks}, FAILED: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
