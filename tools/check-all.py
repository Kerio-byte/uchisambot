#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-all.py — одна команда на все приборы этого дерева (30.10.2026).

Повод. В tools/ к 30.10 накопилось пятнадцать приборов, а способа позвать их
все разом не было: README перечислял одиннадцать строк, и «прогнал всё» держалось
на том, что человек вспомнил список. Четыре прибора в этот список не попали вовсе
(`check-internal`, `locale-key-parity`, `placeholder-parity`, `og-cards`), три
требуют неочевидных ключей (`claim-basis --json`, `legal-tail-read --root . --out …`,
`probe-anchors --sections`), а у `og-cards` рабочий режим — `--check`, и без него
прибор не проверяет, а рисует. Ровно этот класс дефекта дерево уже ловило дважды
(«прибор работал у того, кто помнил строку venv»). Здесь список живёт в коде, а не
в голове: имя, ключи, таймаут и ярус каждого прибора — в таблице BATTERIES ниже.

Ярусы (нужны, чтобы прогон влезал в блок и в крон):
  build   — пересборка страниц; проверяется ВОСПРОИЗВОДИМОСТЬ: два прогона подряд
            не меняют дерево. Сравниваются два снимка `git status`, а не «пусто
            после первого»: ровно в полночь sitemap.xml меняет lastmod, и проверка
            «дерево чисто» краснела бы от календаря, а не от сборки.
  offline — без сети: шапки, числа, внутренние ссылки, вес, паритеты ключей,
            placeholder'ов, реферала, OG-картинок, Deva-подмножества, профиля бота.
  live    — ходят в сеть и в бота: 116 внешних адресов, редиректы, живые языки,
            основание обещаний (адрес LLM, веса, служба, Linger).
  eye     — приборы, которым нужен `landing-eye.py` из дерева скилла (в публичном
            репозитории его нет). Если прибор не найден — SKIP с названной причиной,
            а не красное и не зелёное: «не проверяли» не имеет права выглядеть как
            «проверено».
  visual  — браузер: 420 px, десктоп, 320 px.

Питфоллы:
  • `build.py` пишет файлы; снимок `git status` берётся ДО и ПОСЛЕ второго прогона,
    иначе первый прогон после правки текста выглядел бы невоспроизводимым.
  • Приборы печатают много; в отчёте — только строка CHECKS/итога, а хвост лога
    (8 строк) показывается только у упавшего.
  • `landing-eye.py` ищется так же, как его ищут сами приборы: явный путь, затем
    LANDING_EYE, затем дерево скиллов. Один поиск — на весь прогон.
  • Код возврата 1 — вердикт прогона (есть упавшее), а не поломка прибора.

Запуск:
  python3 tools/check-all.py                # всё, что можно на этой машине
  python3 tools/check-all.py --offline      # без сети (быстро, для крона)
  python3 tools/check-all.py --fast         # сборка + offline, без браузера и сети
  python3 tools/check-all.py --only parity  # подмножество по подстроке имени
  python3 tools/check-all.py --strict       # SKIP считается провалом
Код возврата: 0 — всё зелёное (SKIP допустим), 1 — есть упавшее.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence"
CHECKS_RE = re.compile(r"CHECKS:\s*(\d+),\s*FAILED:\s*(\d+)")
TOTAL_RE = re.compile(r"^TOTAL\s+(\d+)$")
LEAK_RE = re.compile(r"^LEAKS\s+(\d+)$")
CAUGHT_RE = re.compile(r"поймал\s+(\d+)\s+из\s+(\d+)")
ADDR_RE = re.compile(r"адресов:\s*(\d+).*?мёртвых:\s*(\d+)")
EYE_RE = re.compile(r"ИТОГО:\s*языков\s*(\d+),\s*дефектов\s*(\d+)")

# Приборы-КОНТРОЛИ: они нарочно портят вход и обязаны ПОКРАСНЕТЬ. Их красный —
# это их зелёный. Первый полный прогон 30.10 покрасил visual-control, поймавший
# 18 из 18, — раннер считал цвет контроля как цвет страницы.
CONTROL = {"redirects-control", "visual-control", "links-control"}

# Глаз читает блоки страницы по кадрам; кадры режет visual-420 (флаг --frames).
# Список блоков держится здесь и обязан совпадать с tools/visual-pass.py:SECTIONS.
EYE_LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
EYE_PAGES = "hero,contact,footer"

# name, argv (после `python3`), tier, timeout, что именно проверяет
BATTERIES = [
    ("build",            ["tools/build.py"],                                   "build",  180, "пересборка страниц и sitemap"),
    ("site-technical",   ["tools/check-site-technical.py"],                     "offline",180, "шапки девяти языков, числа в словарях"),
    ("internal-links",   ["tools/check-internal.py"],                           "offline",180, "внутренние ссылки и якоря на 12 страницах"),
    ("locale-keys",      ["tools/locale-key-parity.py"],                        "offline",180, "ключи словарей: нет мёртвых и разъехавшихся"),
    ("placeholders",     ["tools/placeholder-parity.py"],                       "offline",180, "плейсхолдеры и незакрытые фигурные скобки"),
    ("deva-subset",      ["tools/subset-deva.py", "--check"],                   "offline",120, "Deva-подмножество шрифта против реестра"),
    ("og-cards",         ["tools/og-cards.py", "--check"],                      "offline",120, "карточки og: 1200x630 на девять языков"),
    ("bot-profile",      ["tools/apply-bot-profile.py", "--check"],             "offline",120, "профиль бота против bot-profile.json"),
    ("weight",           ["tools/check-weight.py"],                             "offline",180, "вес первого экрана, ленивость, потолки"),
    ("referral-parity",  ["tools/referral-parity.py"],                          "offline",120, "реферальные числа страницы против кода бота"),
    ("links",            ["tools/check-links.py"],                              "live",   420, "116 внешних адресов"),
    ("links-control",    ["tools/check-links.py", "--control"],                 "offline",120, "сам прибор: обязан разложить семь известных ответов по классам"),
    ("redirects",        ["tools/check-redirects.py"],                          "live",   240, "http→https, слэши, /index.html, 404, canonical"),
    ("redirects-control",["tools/check-redirects.py", "--control"],             "live",   240, "сам прибор: обязан краснеть на пяти кривых ответах"),
    ("claim-basis",      ["tools/claim-basis.py"],                              "live",   240, "адрес LLM, веса, служба, Linger, девять языков"),
    ("visual-420",       ["tools/visual-pass.py", "--frames"],                  "visual", 600, "420 px и десктоп: вылезание, обрезка, кнопки, кадры по блокам"),
    ("visual-control",   ["tools/visual-pass.py", "--control"],                 "visual", 300, "сам прибор: обязан поймать блок шире окна"),
    ("narrow-320",       ["tools/probe-narrow.py"],                             "visual", 600, "320 px на девяти языках"),
    ("eye-pages",        ["landing-eye.py"],                                    "eye",    900, "глаз читает блоки всех девяти языков по кадрам visual-420"),
    ("eye-anchors",      ["tools/probe-anchors.py"],                            "eye",    300, "опоры блоков под глаз"),
    ("eye-legal-tail",   ["tools/legal-tail-read.py", "--root", "."],           "eye",    300, "нижняя часть privacy/terms глазами"),
]

# приборы, у которых есть --offline; в режиме --offline он им и передаётся
OFFLINE_FLAG = {"site-technical", "links", "claim-basis"}


def find_eye():
    """Тот же путь поиска, что у probe-anchors.py и legal-tail-read.py."""
    env = os.environ.get("LANDING_EYE", "").strip()
    if env and Path(env).is_file():
        return Path(env)
    # Дерево скиллов ищется ШАБЛОНОМ, а не именем каталога: публичный репозиторий
    # не имеет права называть наш софт и наши пути (клауза opsec свипа ловит имя
    # в тексте и валит коммит — так и поймала первую версию этой строки 30.10).
    for pat in ("*/*/*/*/scripts/landing-eye.py", "*/*/*/scripts/landing-eye.py",
                "*/*/scripts/landing-eye.py"):
        for base in (Path.home(), Path.home() / "Projects"):
            if not base.is_dir():
                continue
            for p in base.glob(pat):
                return p
    return None


def git_status():
    out = subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT),
                         capture_output=True, text=True)
    return out.stdout.strip()


def run_battery(name, argv, tier, timeout, what, offline, eye):
    cmd = [sys.executable, "-u"] + argv
    if offline and name in OFFLINE_FLAG:
        cmd.append("--offline")
    if tier == "eye":
        if not eye:
            return dict(name=name, tier=tier, status="SKIP", checks="-", secs=0.0,
                        why="прибор landing-eye.py не найден (публичное дерево его не хранит)",
                        tail=[])
        if name == "eye-pages":
            # Глаз не лежит в дереве, поэтому его зовут напрямую, а не флагом --eye.
            # Кадры к этому моменту уже нарезал visual-420 (ярус visual идёт выше).
            cmd = [sys.executable, "-u", str(eye), "--root", ".",
                   "--frames", f"evidence/visual-{time.strftime('%Y%m%d')}",
                   "--sections", EYE_PAGES, "--langs", ",".join(EYE_LANGS)]
        else:
            cmd += ["--eye", str(eye)]
        if name == "eye-legal-tail":
            EVIDENCE.mkdir(exist_ok=True)
            cmd += ["--out", str(EVIDENCE / f"legal-tail-{time.strftime('%Y%m%d')}.json")]
        if name == "eye-pages":
            # 31.10.2026: прибор звали без --out, и 395 секунд работы глаза существовали
            # только строкой в отчёте раннера. «Дефектов 0» через месяц нечем проверить.
            EVIDENCE.mkdir(exist_ok=True)
            cmd += ["--out", str(EVIDENCE / f"eye-pages-{time.strftime('%Y%m%d')}.json")]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                           timeout=timeout)
        rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        secs = round(time.time() - t0, 1)
        raw = e.stdout or e.stderr or ""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", "replace")
        return dict(name=name, tier=tier, status="FAIL", checks="-", secs=secs,
                    why=f"таймаут {timeout} с", tail=tail_of(raw))
    secs = round(time.time() - t0, 1)
    m = CHECKS_RE.search(out)
    checks = f"{m.group(1)}/{m.group(2)}" if m else "-"
    if not m:
        t = TOTAL_RE.search(out)
        l = LEAK_RE.search(out)
        c = CAUGHT_RE.search(out)
        a = ADDR_RE.search(out)
        e = EYE_RE.search(out)
        if c:
            checks = f"поймал {c.group(1)}/{c.group(2)}"
        elif a:
            checks = f"{a.group(1)}/мёртвых {a.group(2)}"
        elif e:
            checks = f"{e.group(1)} языков/бед {e.group(2)}"
        elif t and l:
            checks = f"{t.group(1)} живых"
        elif t:
            checks = f"{t.group(1)}"
    if name in CONTROL:
        c = CAUGHT_RE.search(out)
        if c:
            checks = f"поймал {c.group(1)}/{c.group(2)}"
        else:
            n = len(re.findall(r"поймал:", out))
            checks = f"поймал {n}"
        # У обоих контролей вердикт в ТЕКСТЕ, а код возврата 0 и на успехе, и на
        # провале: `check-redirects.py --control` печатает «прибор падает там, где
        # должен», `visual-pass.py --control` — «поймал N из N». Судить по коду
        # здесь нельзя (первый прогон 30.10 покрасил оба исправных контроля, второй
        # — позеленел бы на слепом). Поэтому читается вердикт, а код ловит только падение.
        caught = CAUGHT_RE.search(out)
        verdict_ok = False
        if caught:
            verdict_ok = int(caught.group(1)) == int(caught.group(2)) and int(caught.group(2)) > 0
        if "прибор падает там, где должен" in out:
            verdict_ok = True
        if "НЕ ПОЙМАЛ" in out or "не поймал" in out:
            verdict_ok = False
        if rc != 0 or not verdict_ok:
            return dict(name=name, tier=tier, status="FAIL", checks=checks, secs=secs,
                        why="контроль не доказал прибор" if rc == 0 else "контроль упал сам",
                        tail=tail_of(out))
        return dict(name=name, tier=tier, status="ok", checks=checks, secs=secs,
                    why="", tail=[])
    bad = rc != 0
    if m and int(m.group(2)):
        bad = True
    return dict(name=name, tier=tier, status="FAIL" if bad else "ok", checks=checks,
                secs=secs, why="" if not bad else first_failure_line(out),
                tail=tail_of(out) if bad else [])


def first_failure_line(out):
    for line in out.splitlines():
        low = line.lower()
        if "fail" in low or "провал" in low or "красн" in low or "traceback" in low:
            return line.strip()[:200]
    return ""


def tail_of(out, n=8):
    lines = [l for l in out.splitlines() if l.strip()]
    return lines[-n:]


def build_reproducible():
    """Два прогона подряд не меняют дерево; сравниваются два снимка git status."""
    t0 = time.time()
    p1 = subprocess.run([sys.executable, "tools/build.py"], cwd=str(ROOT),
                        capture_output=True, text=True)
    if p1.returncode != 0:
        return dict(name="build", tier="build", status="FAIL", checks="-",
                    secs=round(time.time()-t0, 1), why="сборка упала",
                    tail=tail_of((p1.stdout or "") + (p1.stderr or "")))
    first = git_status()
    p2 = subprocess.run([sys.executable, "tools/build.py"], cwd=str(ROOT),
                        capture_output=True, text=True)
    second = git_status()
    secs = round(time.time() - t0, 1)
    if p2.returncode != 0:
        return dict(name="build", tier="build", status="FAIL", checks="-", secs=secs,
                    why="второй прогон сборки упал", tail=tail_of(p2.stderr))
    if first != second:
        changed = sorted(set(second.splitlines()) - set(first.splitlines())) or ["(снимки разошлись)"]
        return dict(name="build", tier="build", status="FAIL", checks="-", secs=secs,
                    why="сборка невоспроизводима: второй прогон изменил дерево",
                    tail=changed[:8])
    return dict(name="build", tier="build", status="ok",
                checks="2 прогона", secs=secs, why="", tail=[])


# Приборы, которые живут вне этого дерева (рядом со скиллом stars-bots-ops) и поэтому
# в ИТОГО не попадают. Молчать о них нельзя: «ИТОГО ok 19» читается как «всё проверено»,
# а обещания и цены держат ровно эти три прибора. 30.10.2026 нашлось: раннер их не знал,
# и зелёный итог ничего не говорил о ценах, о времени разбора и о словах страницы.
EXTERNAL = [
    ("landing-sweep.py", "слова страницы против claims.json, три тысячи проверок на девяти языках",
     "python3 $SKILL/landing-sweep.py --root . --json out.json"),
    ("landing-price-parity.py", "цены страницы против prices.json и bot/payments.py",
     "python3 $SKILL/landing-price-parity.py --landing ."),
    ("landing-answer-time.py", "«сколько ждать разбор» живым замером через venv бота",
     "python3 $SKILL/landing-answer-time.py --write"),
]


def main():
    ap = argparse.ArgumentParser(description="все приборы лендинга одной командой")
    ap.add_argument("--offline", action="store_true", help="только ярусы build и offline")
    ap.add_argument("--fast", action="store_true", help="сборка + offline (без браузера и сети)")
    ap.add_argument("--only", default="", help="подстрока имени прибора")
    ap.add_argument("--strict", action="store_true", help="SKIP считать провалом")
    ap.add_argument("--json", action="store_true", help="положить журнал в evidence/")
    ap.add_argument("--list", action="store_true", help="напечатать таблицу приборов и выйти")
    args = ap.parse_args()

    if args.list:
        for n, a, t, to, w in BATTERIES:
            print(f"{n:18} {t:8} {to:4} с  {' '.join(a):45} {w}")
        return 0

    only_offline = args.offline or args.fast
    eye = find_eye() if not only_offline else None
    results = []
    for name, argv, tier, timeout, what in BATTERIES:
        if args.only and args.only not in name:
            continue
        if only_offline and tier not in ("build", "offline"):
            results.append(dict(name=name, tier=tier, status="SKIP", checks="-",
                                secs=0.0, why="режим без сети и браузера", tail=[]))
            continue
        if tier == "build":
            r = build_reproducible()
        else:
            r = run_battery(name, argv, tier, timeout, what, args.offline, eye)
        r["what"] = what
        results.append(r)
        line = f"  {r['status']:4} {r['name']:18} {r['checks']:>10}  {r['secs']:6.1f} с  {r['why']}"
        print(line.rstrip())
        for t in r["tail"]:
            print(f"       | {t}")

    bad = [r for r in results if r["status"] == "FAIL"]
    skipped = [r for r in results if r["status"] == "SKIP"]
    print()
    print(f"ИТОГО: приборов {len(results)}, ok {len(results)-len(bad)-len(skipped)}, "
          f"fail {len(bad)}, skip {len(skipped)}")
    if skipped:
        print("не проверяли: " + ", ".join(f"{r['name']} ({r['why']})" for r in skipped))
    if bad:
        print("упало: " + ", ".join(r["name"] for r in bad))
    print(f"вне дерева, НЕ запускались ({len(EXTERNAL)}): "
          + ", ".join(n for n, _, _ in EXTERNAL))
    print("  зелёный ИТОГО выше — это дерево, а не обещания и цены; "
          "их держат приборы выше, их зовут отдельно")

    if args.json:
        EVIDENCE.mkdir(exist_ok=True)
        out = EVIDENCE / f"check-all-{time.strftime('%Y%m%d-%H%M%S')}.json"
        out.write_text(json.dumps(dict(when=time.strftime("%Y-%m-%dT%H:%M:%S"),
                                       offline=bool(only_offline),
                                       results=results), ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print(f"журнал: {out}")

    if bad:
        return 1
    if args.strict and skipped:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
