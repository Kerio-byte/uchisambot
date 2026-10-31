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
import signal
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
CONTROL = {"redirects-control", "visual-control", "links-control",
           "weight-control", "narrow-control", "internal-control",
           "publish-tree-control", "prices-control", "words-control"}

# Приборы, которые живут ВНЕ дерева (рядом со скиллом) и зовутся через tools/external.py.
# До 31.10.2026 они существовали только строкой «вне дерева, НЕ запускались (3)»: цены,
# слова страницы и «сколько ждать разбор» держали приборы, которых не звал ни один прогон.
EXTERNAL_REQUIRES = {
    "words": "landing-sweep.py",
    "words-control": "landing-sweep.py",
    "prices": "landing-price-parity.py",
    "prices-control": "landing-price-parity.py",
}

# Глаз читает блоки страницы по кадрам; кадры режет visual-420 (флаг --frames).
# Список блоков держится здесь и обязан совпадать с tools/visual-pass.py:SECTIONS.
EYE_LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
EYE_PAGES = "hero,contact,footer"

# Прибор, который прямо сейчас работает. Нужен не для красоты: прогон, убитый
# снаружи (у крона свой потолок времени), обязан назвать, на чём его застали, —
# иначе 900 секунд работы выглядят как «свип не запускали».
INFLIGHT = {"name": None, "t0": 0.0, "proc": None}


def kill_tree(proc, grace: float = 2.0):
    """Погасить прибор вместе с его детьми. Прибор стартует своей сессией
    процессов (start_new_session), поэтому одного p.kill() мало: браузер
    глаза живёт в той же группе, но не под ним — нужен killpg по группе."""
    if proc is None or proc.poll() is not None:
        return
    import signal as _sig
    for sig in (_sig.SIGTERM, _sig.SIGKILL):
        try:
            os.killpg(os.getpgid(proc.pid), sig)
        except (ProcessLookupError, PermissionError):
            return
        try:
            proc.wait(timeout=grace)
            return
        except subprocess.TimeoutExpired:
            continue

# name, argv (после `python3`), tier, timeout, что именно проверяет
BATTERIES = [
    ("build",            ["tools/build.py"],                                   "build",  180, "пересборка страниц и sitemap"),
    ("site-technical",   ["tools/check-site-technical.py"],                     "offline",180, "шапки девяти языков, числа в словарях"),
    ("internal-links",   ["tools/check-internal.py"],                           "offline",180, "внутренние ссылки, якоря и своё имущество (src/poster) на 12 страницах"),
    ("internal-control", ["tools/check-internal.py", "--control"],               "offline",120, "сам прибор: обязан поймать битый файл, якорь, src и пропавшую страницу"),
    ("publish-tree",     ["tools/publish-tree.py", "--check"],                  "offline",180, "список публикации: полнота, границы мастерской, ссылки, читатели"),
    ("publish-tree-control", ["tools/publish-tree.py", "--control"],            "offline",240, "сам прибор: пять мутантов обязаны покраснеть, каждый своим сообщением"),
    ("locale-keys",      ["tools/locale-key-parity.py"],                        "offline",180, "ключи словарей: нет мёртвых и разъехавшихся"),
    ("placeholders",     ["tools/placeholder-parity.py"],                       "offline",180, "плейсхолдеры и незакрытые фигурные скобки"),
    ("deva-subset",      ["tools/subset-deva.py", "--check"],                   "offline",120, "Deva-подмножество шрифта против реестра"),
    ("og-cards",         ["tools/og-cards.py", "--check"],                      "offline",120, "карточки og: 1200x630 на девять языков"),
    ("bot-profile",      ["tools/apply-bot-profile.py", "--check"],             "offline",120, "профиль бота против bot-profile.json"),
    ("sigterm-control",  ["tools/check-sigterm.py"],                            "offline",300, "сам прибор: SIGTERM раннеру гасит ребёнка, мутант без kill_tree обязан оставить сироту"),
    ("weight",           ["tools/check-weight.py"],                             "offline",180, "вес первого экрана, ленивость, потолки"),
    ("weight-control",   ["tools/check-weight.py", "--control"],                 "offline",180, "сам прибор: обязан увидеть потолок 1 байт и чужой язык в медиа"),
    ("referral-parity",  ["tools/referral-parity.py"],                          "offline",120, "реферальные числа страницы против кода бота"),
    ("links",            ["tools/check-links.py"],                              "live",   420, "116 внешних адресов"),
    ("live-bytes",       ["tools/live-bytes.py"],                                "live",   240, "живой сайт против дерева: байт в байт, 16 файлов"),
    ("live-bytes-control", ["tools/live-bytes.py", "--control"],                 "live",   240, "сам прибор: один испорченный байт обязан покраснеть именно им"),
    ("links-control",    ["tools/check-links.py", "--control"],                 "offline",120, "сам прибор: обязан разложить семь известных ответов по классам"),
    ("controls-mutation",["tools/controls-mutation.py"],                        "offline",300, "сам прибор: пять инструментов обязаны покраснеть на своих дефектах"),
    ("redirects",        ["tools/check-redirects.py"],                          "live",   240, "http→https, слэши, /index.html, 404, canonical"),
    ("redirects-control",["tools/check-redirects.py", "--control"],             "live",   240, "сам прибор: обязан краснеть на пяти кривых ответах"),
    ("claim-basis",      ["tools/claim-basis.py"],                              "live",   240, "адрес LLM, веса, служба, Linger, девять языков"),
    ("words",            ["tools/external.py", "--words"],                     "external",900, "слова девяти страниц против claims.json (прибор вне дерева)"),
    ("words-control",    ["tools/external.py", "--words-control"],             "external",900, "сам прибор: сломанная страница обязана покраснеть своим [ru]"),
    ("prices",           ["tools/external.py", "--prices"],                    "external",300, "цены страницы против prices.json и кода бота"),
    ("prices-control",   ["tools/external.py", "--prices-control"],            "external",600, "сам прибор: три мутанта цен обязаны покраснеть"),
    ("visual-420",       ["tools/visual-pass.py", "--frames"],                  "visual", 600, "420 px и десктоп: вылезание, обрезка, кнопки, кадры по блокам"),
    ("visual-control",   ["tools/visual-pass.py", "--control"],                 "visual", 300, "сам прибор: обязан поймать блок шире окна"),
    ("narrow-320",       ["tools/probe-narrow.py"],                             "visual", 600, "320 px на девяти языках"),
    ("narrow-control",   ["tools/probe-narrow.py", "--control"],                 "visual", 600, "сам прибор: обязан поймать блок 600 px в окне 320"),
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


def find_external(script):
    """Тот же шаблонный поиск, что у глаза: публичное дерево не называет наших путей."""
    env = os.environ.get("LANDING_TOOLS", "").strip()
    if env and (Path(env) / script).is_file():
        return Path(env) / script
    for pat in (f"*/*/*/*/scripts/{script}", f"*/*/*/scripts/{script}",
                f"*/*/scripts/{script}"):
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
    INFLIGHT["name"], INFLIGHT["t0"] = name, t0
    # 31.10.2026: прибор — отдельная сессия процессов. Иначе SIGTERM раннеру
    # оставлял живым его ребёнка (браузер глаза, обход ссылок), а запись
    # «прогон прерван» рядом с живым сиротой — ложь: следующий прогон
    # подерётся с ним за тот же каталог evidence.
    try:
        p = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True,
                             start_new_session=True)
        INFLIGHT["proc"] = p
        out, err = p.communicate(timeout=timeout)
        rc, out = p.returncode, (out or "") + (err or "")
    except subprocess.TimeoutExpired as e:
        secs = round(time.time() - t0, 1)
        kill_tree(INFLIGHT.get("proc"))
        raw = e.stdout or e.stderr or ""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", "replace")
        return dict(name=name, tier=tier, status="FAIL", checks="-", secs=secs,
                    why=f"таймаут {timeout} с", tail=tail_of(raw))
    finally:
        INFLIGHT["proc"] = None
    secs = round(time.time() - t0, 1)
    # ПОСЛЕДНЕЕ совпадение, а не первое: прибор-мутация печатает вывод своего
    # мутанта как улику, и там есть своя строка «CHECKS: …, FAILED: 1». 31.10
    # раннер взял её за вердикт и покрасил исправный `controls-mutation`.
    matches = CHECKS_RE.findall(out)
    m = matches[-1] if matches else None
    checks = f"{m[0]}/{m[1]}" if m else "-"
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
            n = len(re.findall(r"(?:ПОЙМАЛ|поймал)", out)) - len(re.findall(r"(?:НЕ ПОЙМАЛ|не поймал)", out))
            checks = f"поймал {max(n, 0)}"
        # У контролей вердикт в ТЕКСТЕ, а код возврата бывает 0 и на успехе, и на
        # провале: `check-redirects.py --control` печатает «прибор падает там, где
        # должен», `visual-pass.py --control` — «поймал N из N». Судить по коду
        # здесь нельзя (первый прогон 30.10 покрасил оба исправных контроля, второй
        # — позеленел бы на слепом). Поэтому читается вердикт, а код ловит только падение.
        #
        # 31.10: у `check-weight.py --control` и `probe-narrow.py --control` третий
        # формат — «КОНТРОЛЬ: вес — поймал; чужой язык — поймал» и «КОНТРОЛЬ: ПОЙМАЛ»
        # / «ПРОСМОТРЕЛ», то есть без числа пойманных. Без этой ветки оба исправных
        # контроля читались бы как «не доказал прибор» и красили прогон.
        caught = CAUGHT_RE.search(out)
        verdict_ok = False
        if caught:
            verdict_ok = int(caught.group(1)) == int(caught.group(2)) and int(caught.group(2)) > 0
        elif re.search(r"ПОЙМАЛ|поймал", out):
            # Беcчисловой вердикт (weight, narrow) — но только когда «поймал N из M»
            # не печаталось: иначе «поймал 5 из 7» перебивалось бы этим словом.
            verdict_ok = True
        if "прибор падает там, где должен" in out:
            verdict_ok = True
        if re.search(r"НЕ ПОЙМАЛ|не поймал|ПРОСМОТРЕЛ|просмотрел", out):
            verdict_ok = False
        if rc != 0 or not verdict_ok:
            return dict(name=name, tier=tier, status="FAIL", checks=checks, secs=secs,
                        why="контроль не доказал прибор" if rc == 0 else "контроль упал сам",
                        tail=tail_of(out))
        return dict(name=name, tier=tier, status="ok", checks=checks, secs=secs,
                    why="", tail=[])
    bad = rc != 0
    if m and int(m[1]):
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


# Приборы, которые в свип НЕ встают по устройству, а не по забывчивости. Молчать о них
# нельзя: «ИТОГО ok 19» читается как «всё проверено» — поэтому они называются поимённо
# с причиной. 31.10.2026: два из трёх прежних «вне дерева» переехали в батареи
# (words, prices через tools/external.py); остался замер, который тратит генерации.
MANUAL = [
    ("landing-answer-time.py",
     "живой замер «сколько ждать разбор»: тратит настоящие генерации бота и занимает его "
     "очередь — зовётся вручную, не кроном"),
]


def main():
    ap = argparse.ArgumentParser(description="все приборы лендинга одной командой")
    ap.add_argument("--offline", action="store_true", help="только ярусы build и offline")
    ap.add_argument("--fast", action="store_true", help="сборка + offline (без браузера и сети)")
    ap.add_argument("--only", default="", help="подстрока имени прибора")
    ap.add_argument("--strict", action="store_true", help="SKIP считать провалом")
    ap.add_argument("--json", action="store_true", help="положить журнал в evidence/")
    ap.add_argument("--budget", type=int,
                    default=int(os.environ.get("LANDING_SWEEP_BUDGET", "0") or 0),
                    help="секунд на весь прогон: остаток называется поимённо, прогон "
                         "не притворяется полным (0 — без потолка; то же в "
                         "LANDING_SWEEP_BUDGET)")
    ap.add_argument("--list", action="store_true", help="напечатать таблицу приборов и выйти")
    args = ap.parse_args()

    if args.list:
        for n, a, t, to, w in BATTERIES:
            print(f"{n:18} {t:8} {to:4} с  {' '.join(a):45} {w}")
        return 0

    only_offline = args.offline or args.fast
    eye = find_eye() if not only_offline else None
    results = []
    t_start = time.time()
    cut: dict = {"why": None, "battery": None}
    journal = (EVIDENCE / f"check-all-{time.strftime('%Y%m%d-%H%M%S')}.json") if args.json else None

    def write_journal(complete):
        """Журнал пишется после каждого прибора, а не одним куском в конце:
        прогон, убитый снаружи, обязан оставить файл, в котором видно, сколько
        успели проверить и на чём именно его застали."""
        if not journal:
            return
        EVIDENCE.mkdir(exist_ok=True)
        journal.write_text(json.dumps(
            dict(when=time.strftime("%Y-%m-%dT%H:%M:%S"), offline=bool(only_offline),
                 complete=bool(complete), elapsed=round(time.time() - t_start, 1),
                 cut=cut["why"], in_flight=cut["battery"], results=results),
            ensure_ascii=False, indent=1), encoding="utf-8")

    def on_signal(signum, frame):
        cut["why"] = f"прервано сигналом {signum} (внешний потолок времени)"
        cut["battery"] = INFLIGHT["name"]
        # Ребёнок прибора гасится ДО записи журнала: иначе «прервано» стоит
        # рядом с живым сиротой, который дописывает в тот же каталог evidence.
        kill_tree(INFLIGHT.get("proc"))
        write_journal(complete=False)
        bad = [r for r in results if r["status"] == "FAIL"]
        print(f"\nИТОГО: ПРЕРВАНО сигналом {signum} на приборе {INFLIGHT['name']} "
              f"после {len(results)} приборов, упало {len(bad)}. "
              f"Ребёнок прибора погашен. "
              f"Это не полный прогон: {journal or 'журнал не заказан (--json)'}")
        sys.stdout.flush()
        os._exit(2)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    for name, argv, tier, timeout, what in BATTERIES:
        if args.only:
            # 31.10.2026: --only links ловил и internal-links — прогон «одного
            # прибора» тихо включал чужой. Точное имя прибора старше подстроки.
            if args.only in {b[0] for b in BATTERIES}:
                if name != args.only:
                    continue
            elif args.only not in name:
                continue
        if args.budget:
            left = args.budget - (time.time() - t_start)
            if left < 30:
                why = (f"бюджет прогона {args.budget} с исчерпан, осталось "
                       f"{max(0, int(left))} с — прибор не запускался")
                cut["why"] = why
                cut["battery"] = name
                results.append(dict(name=name, tier=tier, status="SKIP", checks="-",
                                    secs=0.0, why=why, tail=[], what=what))
                print(f"  SKIP {name:18} {'-':>10}  {0.0:6.1f} с  {why}")
                write_journal(complete=False)
                continue
        if only_offline and tier not in ("build", "offline"):
            why = {"visual": "режим без браузера",
                   "live": "режим без сети",
                   "eye": "режим без браузера и сети",
                   "external": "внешние приборы ходят в сеть — не в этом режиме",
                   }.get(tier, "режим без сети и браузера")
            results.append(dict(name=name, tier=tier, status="SKIP", checks="-",
                                secs=0.0, why=why, tail=[]))
            continue
        if tier == "external":
            req = EXTERNAL_REQUIRES.get(name)
            if req and not find_external(req):
                r = dict(name=name, tier=tier, status="SKIP", checks="-", secs=0.0,
                         why=f"прибор вне дерева не найден ({req})", tail=[], what=what)
                results.append(r)
                print(f"  {r['status']:4} {name:18} {'-':>10}  {0.0:6.1f} с  {r['why']}")
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
        write_journal(complete=False)

    bad = [r for r in results if r["status"] == "FAIL"]
    skipped = [r for r in results if r["status"] == "SKIP"]
    print()
    print(f"ИТОГО: приборов {len(results)}, ok {len(results)-len(bad)-len(skipped)}, "
          f"fail {len(bad)}, skip {len(skipped)}")
    if skipped:
        # Причина у бюджетных пропусков одна на тридцать приборов — печатать её
        # тридцать раз значит спрятать имена в стене текста. Группируем.
        by_why: dict = {}
        for r in skipped:
            by_why.setdefault(r["why"], []).append(r["name"])
        print("не проверяли: " + "; ".join(
            f"{', '.join(names)} ({why})" for why, names in by_why.items()))
    cut_off = [r for r in skipped if r["why"] and "бюджет прогона" in r["why"]]
    if cut_off:
        print(f"СВИП НЕПОЛНЫЙ: {len(cut_off)} приборов не запускались — бюджет "
              f"{args.budget} с кончился на {round(time.time() - t_start, 1)} с: "
              + ", ".join(r["name"] for r in cut_off))
    if bad:
        print("упало: " + ", ".join(r["name"] for r in bad))
    print(f"вне свипа по устройству ({len(MANUAL)}): "
          + "; ".join(f"{n} — {why}" for n, why in MANUAL))
    print("  остальные приборы обещаний и цен зовутся этим же прогоном (words, prices "
          "и их контроли); зелёный ИТОГО выше — про них тоже")

    write_journal(complete=not cut["why"])
    if journal:
        print(f"журнал: {journal}")

    if bad:
        return 1
    if cut_off:
        # 31.10.2026: зелёное «ИТОГО» при неполном прогоне — тот же обман, что
        # прибор без контроля. Бюджет кончился — прогон не проверен, код 2.
        return 2
    if args.strict and skipped:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
