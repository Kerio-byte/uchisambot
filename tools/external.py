#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/external.py — приборы, которые живут ВНЕ этого дерева, но держат обещания
страницы: слова, цены и «сколько ждать разбор» (31.10.2026).

Повод. С 30.10 `check-all.py` знал про три внешних прибора ровно одно: их имена,
напечатанные строкой «вне дерева, НЕ запускались (3)». То есть обещания и цены держали
приборы, которые не звал ни один прогон, и «ИТОГО зелёное» о них не говорило ничего.
Строка была честной, но бесполезной: чтобы её покрасить, нужно было помнить три
команды с ключами.

Что теперь. Два механических прибора (слова страницы, цены) зовутся отсюда и попадают
в свип как обычные батареи, вместе со своими контролями: у цен он уже был (`--mutate`),
у слов его не было — теперь есть, и он проверяет не «код 1», а СВОЁ сообщение.

Почему не все три. `landing-answer-time.py` — живой замер «сколько ждать разбор»: он
тратит настоящие генерации бота и занимает очередь. В крон-свип такое ставить нельзя
(деньги тратятся без спроса). Он остаётся ручным, и свип называет его поимённо, а не
делает вид, что проверил.

Пути. Публичное дерево не имеет права называть наш софт и наши каталоги — поэтому
приборы ищутся ШАБЛОНОМ (как `landing-eye.py` в раннере), а не литералом. Если прибора
нет — это «НЕ НАЙДЕН» и код 3, а не зелёное: «не проверяли» не имеет права выглядеть
как «проверено».

Запуск:
  python3 tools/external.py --words             # слова девяти страниц против claims.json
  python3 tools/external.py --words-control     # контроль: сломанная страница обязана покраснеть
  python3 tools/external.py --prices            # цены страницы против prices.json и кода бота
  python3 tools/external.py --prices-control    # контроль: три мутанта цен, каждый своим сообщением
Код возврата: 0 — зелено, 1 — дефект, 2 — контроль не доказал прибор, 3 — прибора нет.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(tempfile.gettempdir())
CHECKS_RE = re.compile(r"CHECKS:\s*(\d+),\s*FAILED:\s*(\d+)")
FAILLINE_RE = re.compile(r"^FAIL\s", re.M)


def find_script(name):
    """Тот же принцип, что у поиска глаза в раннере: шаблон, а не наш путь в тексте."""
    env = os.environ.get("LANDING_TOOLS", "").strip()
    if env:
        p = Path(env) / name
        if p.is_file():
            return p
    for pat in (f"*/*/*/*/scripts/{name}", f"*/*/*/scripts/{name}", f"*/*/scripts/{name}"):
        for base in (Path.home(), Path.home() / "Projects"):
            if not base.is_dir():
                continue
            for p in base.glob(pat):
                return p
    return None


def need(name):
    p = find_script(name)
    if p is None:
        print(f"НЕ НАЙДЕН: {name} — прибор живёт вне дерева, не проверяли")
        raise SystemExit(3)
    return p


def run(cmd, timeout=600):
    p = subprocess.run([sys.executable, "-u"] + [str(c) for c in cmd],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def verdict(out):
    m = CHECKS_RE.findall(out)
    return (int(m[-1][0]), int(m[-1][1])) if m else (None, None)


def words():
    sweep = need("landing-sweep.py")
    rc, out = run([sweep, "--root", ".", "--json",
                   str(ROOT / "evidence" / f"words-{_stamp()}.json")], timeout=900)
    checks, failed = verdict(out)
    if checks is None:
        print("НЕ РАЗОБРАЛ вывод свипа слов — считать непроверенным")
        print("\n".join(out.splitlines()[-6:]))
        return 2
    print(f"CHECKS: {checks}, FAILED: {failed}")
    if failed:
        print("\n".join([ln for ln in out.splitlines() if FAILLINE_RE.match(ln)][:8]))
        return 1
    return 0


def words_control():
    """Сломанная страница обязана покраснеть и назвать СВОЙ язык.

    Мутант: копия дерева, у которой `ru/index.html` — заглушка. Требуется не «код 1»
    (на копии краснеют и проверки, которым нужен живой сайт), а красная строка с меткой
    [ru]: красный от чужой причины дефектом не считается.
    """
    sweep = need("landing-sweep.py")
    rc_live, out_live = run([sweep, "--root", "."], timeout=900)
    _, failed_live = verdict(out_live)
    if rc_live != 0 or failed_live != 0:
        print(f"НЕ ПОЙМАЛ: боевое дерево уже красное ({failed_live} провалов) — контролю нечего доказывать")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="words-control-", dir=str(SCRATCH)))
    try:
        for p in ROOT.iterdir():
            if p.name in (".git", "evidence", "__pycache__"):
                continue
            dst = tmp / p.name
            shutil.copytree(p, dst) if p.is_dir() else shutil.copy2(p, dst)
        (tmp / "ru" / "index.html").write_text(
            "<!doctype html><html><body><h1>stub</h1></body></html>\n", encoding="utf-8")
        rc_mut, out_mut = run([sweep, "--root", str(tmp)], timeout=900)
        checks, failed = verdict(out_mut)
        own = [ln for ln in out_mut.splitlines()
               if FAILLINE_RE.match(ln) and re.search(r"\[ru\]", ln)]
        if failed is None:
            print("НЕ ПОЙМАЛ: вывод мутанта не разобран")
            return 2
        if rc_mut == 0 or failed == 0 or not own:
            print(f"НЕ ПОЙМАЛ: мутант дал код {rc_mut}, провалов {failed}, "
                  f"своих [ru] — {len(own)}")
            return 2
        print(f"мутант: код {rc_mut}, провалов {failed}, своих [ru] {len(own)}; "
              f"первая — {own[0][:110]}")
        print("поймал 1 из 1")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def prices():
    parity = need("landing-price-parity.py")
    rc, out = run([parity, "--landing", "."], timeout=300)
    checks, failed = verdict(out)
    if checks is None:
        print("НЕ РАЗОБРАЛ вывод прибора цен — считать непроверенным")
        print("\n".join(out.splitlines()[-6:]))
        return 2
    print(f"CHECKS: {checks}, FAILED: {failed}")
    if failed:
        print("\n".join([ln for ln in out.splitlines() if "MISMATCH" in ln or "FAIL" in ln][:8]))
        return 1
    return 0


def prices_control():
    """Три мутанта по одному числу. Каждый обязан покраснеть РОВНО одним утверждением
    и назвать подменённое число — так требует сам прибор; здесь только счёт."""
    parity = need("landing-price-parity.py")
    caught, total = 0, 0
    for kind in ("bot", "site", "reftext"):
        total += 1
        rc, out = run([parity, "--landing", ".", "--mutate", kind], timeout=300)
        last = [ln for ln in out.splitlines() if ln.strip()][-1:] or [""]
        ok = rc == 0 and "поймано ровно одно" in out
        caught += 1 if ok else 0
        print(f"  {kind:8} {'поймал' if ok else 'НЕ ПОЙМАЛ'}: {last[0][:120]}")
    if caught != total:
        print(f"НЕ ПОЙМАЛ: {caught} из {total}")
        return 2
    print(f"поймал {caught} из {total}")
    return 0


def lang_leftovers():
    """Непереведённый английский на восьми языковых страницах.

    31.10.2026: прибор жил рядом со скиллом и его не звал ни один прогон. Девять
    языков — обещание страницы, а держал его прибор, которого свип не знал.
    """
    tool = need("landing-en-leftovers.py")
    rc, out = run([tool, "--root", "."], timeout=300)
    checks, failed = verdict(out)
    if checks is None:
        print("НЕ РАЗОБРАЛ вывод прибора непереведённого — считать непроверенным")
        print("\n".join(out.splitlines()[-6:]))
        return 2
    print(f"CHECKS: {checks}, FAILED: {failed}")
    if failed:
        print("\n".join([ln for ln in out.splitlines() if ln.strip()][-8:]))
        return 1
    return 0


def lang_leftovers_control():
    """Мутант — фраза-пустышка на каждом из восьми языков (EN не в счёте).

    Требуется не «код 0», а итоговая строка контроля и восемь поймавших языков:
    прибор, поймавший фразу на одном языке, девяти языков не держит.
    """
    tool = need("landing-en-leftovers.py")
    rc, out = run([tool, "--root", ".", "--mutate", "all"], timeout=600)
    caught = [ln for ln in out.splitlines()
              if re.match(r"\s*(ru|es|pt|hi|id|tr|vi|uk)\s*:", ln)]
    marker = "фраза поймана на каждом из восьми" in out
    if rc != 0 or not marker or len(caught) < 8:
        print(f"НЕ ПОЙМАЛ: код {rc}, языков {len(caught)} из 8, "
              f"итоговой строки контроля {'есть' if marker else 'нет'}")
        print("\n".join(out.splitlines()[-6:]))
        return 2
    print(f"мутант: поймано языков {len(caught)} из 8, EN не в счёте")
    print("поймал 1 из 1")
    return 0


PAGE_EXTRAS = [
    ("landing-axe-audit.py", ["--root", "."], "axe-core по двенадцати страницам"),
    ("landing-a11y-extra.py", ["--root", "."], "остаточная доступность: роли, порядок обхода, озвучка"),
    ("landing-badge-rows.py", [], "полоса значков площадок по ширинам и языкам"),
]


def page_extras():
    """Три прибора вне дерева, которые держат ту же страницу, но не звались никем.

    31.10.2026, шестнадцатый блок. Раннер честно печатал «зовёт 3, не зовёт 78»,
    и в этих 78 лежали ровно те приборы, что читают ЭТУ страницу: axe-core,
    остаточная доступность, полоса значков. Красное в них не увидел бы никто,
    пока кто-нибудь не вспомнил бы про них руками. Теперь они зовутся прогоном.
    """
    total = fail = 0
    missing = []
    for name, extra, what in PAGE_EXTRAS:
        p = find_script(name)
        if p is None:
            missing.append(name)
            print(f"НЕ НАЙДЕН: {name} — не проверяли")
            continue
        rc, out = run([p] + extra, timeout=420)
        checks, failed = verdict(out)
        if checks is None or failed is None:
            print(f"{name}: вывод без CHECKS — считать непроверенным (код {rc})")
            print("\n".join(out.splitlines()[-4:]))
            return 2
        total += checks
        fail += failed
        print(f"{name}: {checks}/{failed} — {what}" + ("" if rc == 0 else f" (код {rc})"))
        if failed:
            print("\n".join([ln for ln in out.splitlines() if FAILLINE_RE.match(ln)][:6]))
        elif rc != 0:
            fail += 1
    print(f"CHECKS: {total}, FAILED: {fail}")
    if missing:
        print("не проверяли: " + ", ".join(missing))
        return 3
    return 1 if fail else 0


def _stamp():
    import time
    return time.strftime("%Y%m%d-%H%M%S")


def main():
    ap = argparse.ArgumentParser(description="внешние приборы лендинга одной командой")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--words", action="store_true", help="слова страницы против claims.json")
    g.add_argument("--words-control", dest="words_control", action="store_true",
                   help="контроль: сломанная страница обязана покраснеть своим сообщением")
    g.add_argument("--prices", action="store_true", help="цены страницы против кода бота")
    g.add_argument("--prices-control", dest="prices_control", action="store_true",
                   help="контроль: три мутанта цен обязаны покраснеть")
    g.add_argument("--lang-leftovers", dest="lang_leftovers", action="store_true",
                   help="непереведённый английский на восьми языковых страницах")
    g.add_argument("--lang-leftovers-control", dest="lang_leftovers_control",
                   action="store_true",
                   help="контроль: фраза-пустышка обязана быть поймана на каждом из восьми языков")
    g.add_argument("--page-extras", dest="page_extras", action="store_true",
                   help="три прибора вне дерева, читающие страницу: axe-core, "
                        "остаточная доступность, полоса значков")
    a = ap.parse_args()
    if a.words:
        return words()
    if a.words_control:
        return words_control()
    if a.prices:
        return prices()
    if a.prices_control:
        return prices_control()
    if a.lang_leftovers:
        return lang_leftovers()
    if a.lang_leftovers_control:
        return lang_leftovers_control()
    if a.page_extras:
        return page_extras()
    return 3


if __name__ == "__main__":
    sys.exit(main())
