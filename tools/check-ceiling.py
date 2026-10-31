#!/usr/bin/env python3
"""Потолок прогона: прибор и его контроль.

31.10.2026, десятый блок. У свипа не было своей страховки: без --budget он шёл
столько, сколько нужно глазу, и потолок держал только крон — забыл крон, потолка
нет. Хуже: потолок не был потолком. Остаток проверялся только ДО прибора, поэтому
один длинный прибор (глаз — 395 с) перепрыгивал объявленный потолок в разы.

Пять ног, каждая — отдельное утверждение о поведении tools/check-all.py:
  default  без ключей и без среды: «потолок прогона: <DEFAULT> с (по умолчанию)», код 0
  cut      потолок 8 с: код 2, прибор назван, недоделанный помечен SKIP «не дочитан»,
           а не FAIL — исправный инструмент не виноват в том, что кончилось время
  journal  в журнале complete=false, budget=8, cut называет потолок, есть результат cut=budget
  open     --no-ceiling: потолка нет, код 0 — бесконечность по имени работает
  label    --budget 60: источник назван ключом, а не «по умолчанию»; иначе забытый
           ключ и явный ключ выглядят в отчёте одинаково

Контроль (--control) ломает КОПИЮ инструмента двумя мутантами и требует, чтобы
покраснела именно своя нога:
  мутант A: DEFAULT_CEILING = 0  -> обязана покраснеть нога default
  мутант B: вырезан предел прибора по остатку -> обязана покраснеть нога cut
Без контроля «потолок держится» ничего не доказывало бы: зелёными были бы обе
версии кода — и та, что обрезает, и та, что нет.

Вердикт в общем формате свипа: CHECKS: N, FAILED: M
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWEEP = ROOT / "tools" / "check-all.py"
EVIDENCE = ROOT / "evidence"
CUT_CEILING = 8
# Две батареи: build (0,6 с) успевает, site-technical (43 с) не успевает в 8 с
# и обязан быть снят пределом, а не досидеть до своего таймаута.
CUT_ONLY = "build,site-technical"


def run(sweep, args, env_extra=None):
    """Прогон инструмента в чистой среде: чужие LANDING_SWEEP_* не должны
    подменять проверяемое поведение."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("LANDING_SWEEP_")}
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, "-u", str(sweep)] + args, cwd=str(ROOT),
                       capture_output=True, text=True, env=env, timeout=600)
    return p.returncode, ((p.stdout or "") + (p.stderr or "")),


def out_of(res):
    return res[1]


def default_ceiling():
    m = re.search(r"^DEFAULT_CEILING\s*=\s*(\d+)", SWEEP.read_text(encoding="utf-8"), re.M)
    return int(m.group(1)) if m else None


def leg_default(sweep, checks):
    rc, out = run(sweep, ["--fast", "--only", "build"])
    want = f"потолок прогона: {default_ceiling()} с (по умолчанию)"
    ok = rc == 0 and want in out
    return checks, ok, (f"умолчание названо «{want}», код {rc}" if ok else
                        f"умолчание не названо: искали «{want}», код {rc}; "
                        f"первая строка «{out.splitlines()[0] if out.splitlines() else ''}»")


def leg_cut(sweep, checks, journal_before):
    rc, out = run(sweep, ["--fast", "--only", CUT_ONLY, "--json"],
                  {"LANDING_SWEEP_CEILING": str(CUT_CEILING)})
    new = sorted(set(p.name for p in EVIDENCE.glob("check-all-*.json")) - journal_before)
    named = re.search(r"СВИП НЕПОЛНЫЙ: (\d+) прибор", out)
    capped = re.search(r"SKIP (\S+).*потолок прогона кончился на этом приборе.*не дочитан", out)
    bad_fail = re.search(r"FAIL (\S+).*таймаут", out)
    ok = (rc == 2 and named and capped and not bad_fail)
    msg = (f"потолок {CUT_CEILING} с: код 2, прибор {capped.group(1) if capped else '?'} "
           f"снят пределом и помечен SKIP, не FAIL") if ok else (
        f"потолок {CUT_CEILING} с не держится: код {rc}, "
        f"«СВИП НЕПОЛНЫЙ» {'есть' if named else 'нет'}, "
        f"снятый пределом прибор {'назван' if capped else 'НЕ назван'}"
        + (f", исправный прибор обвинён таймаутом ({bad_fail.group(1)})" if bad_fail else ""))
    return checks, ok, msg, (new[0] if new else None), out


def leg_journal(checks, name):
    if not name:
        return checks, False, "журнала нет — нечего читать (нога cut не записала файл)"
    j = json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
    cut = str(j.get("cut") or "")
    has_cut_row = any(r.get("cut") == "budget" for r in j.get("results", []))
    ok = (j.get("complete") is False and j.get("budget") == CUT_CEILING
          and "потолок" in cut and has_cut_row)
    return checks, ok, (f"журнал {name}: complete=false, budget={j.get('budget')}, "
                        f"cut называет потолок, строка cut=budget есть") if ok else (
        f"журнал {name} не подтверждает обрыв: complete={j.get('complete')}, "
        f"budget={j.get('budget')}, cut=«{cut[:60]}», строка cut=budget "
        f"{'есть' if has_cut_row else 'нет'}")


def leg_open(sweep, checks):
    rc, out = run(sweep, ["--fast", "--only", "build", "--no-ceiling"])
    ok = rc == 0 and "потолок прогона: нет (снят ключом --no-ceiling)" in out \
        and "СВИП НЕПОЛНЫЙ" not in out
    return checks, ok, ("--no-ceiling: потолка нет, код 0 — бесконечность только по имени"
                        if ok else f"--no-ceiling не работает как обещано: код {rc}")


def leg_label(sweep, checks):
    rc, out = run(sweep, ["--fast", "--only", "build", "--budget", "60"])
    ok = rc == 0 and "потолок прогона: 60 с (задан ключом --budget)" in out
    return checks, ok, ("явный --budget назван своим источником, не «по умолчанию»"
                        if ok else f"источник потолка не различается: код {rc}, "
                                    f"первая строка «{out.splitlines()[0] if out.splitlines() else ''}»")


def control(checks):
    """Мутанты — на копии инструмента, не на живом файле."""
    work = ROOT / ".shots-work" / "ceiling-control"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    src = SWEEP.read_text(encoding="utf-8")

    mutants = [
        ("A: DEFAULT_CEILING = 0 (потолка по умолчанию нет)", "default",
         re.sub(r"^DEFAULT_CEILING\s*=\s*\d+", "DEFAULT_CEILING = 0", src, count=1, flags=re.M)),
        ("B: предел прибора по остатку вырезан", "cut",
         src.replace("            if left < timeout:\n"
                     "                eff_timeout, capped = max(1, int(left)), True",
                     "            if False:\n"
                     "                eff_timeout, capped = max(1, int(left)), True", 1)),
    ]
    for title, expected_leg, text in mutants:
        checks += 1
        if text == src:
            print(f"  FAIL мутация не наложилась: {title} — прибор не знает, "
                  f"что именно он ломает")
            return checks, False
        mfile = work / f"mutant-{expected_leg}.py"
        mfile.write_text(text, encoding="utf-8")
        # Мутант живёт рядом с настоящим tools/: путь ROOT считается от файла,
        # поэтому копия кладётся в tools/ на время прогона.
        shadow = ROOT / "tools" / f"_mutant-ceiling-{expected_leg}.py"
        shutil.copyfile(mfile, shadow)
        try:
            if expected_leg == "default":
                c2, ok, why = leg_default(shadow, 0)
            else:
                before = set(p.name for p in EVIDENCE.glob("check-all-*.json"))
                c2, ok, why, _, _ = leg_cut(shadow, 0, before)
        finally:
            shadow.unlink(missing_ok=True)
        if ok:
            print(f"  FAIL мутант пережил проверку: {title} — «{why}»")
            return checks, False
        print(f"  ok   мутант поймала нога {expected_leg}: {title}")
    return checks, True


def main():
    checks = failed = 0
    journal_before = set(p.name for p in EVIDENCE.glob("check-all-*.json"))

    for fn in (leg_default,):
        checks += 1
        c, ok, why = fn(SWEEP, checks)
        failed += 0 if ok else 1
        print(f"  {'ok  ' if ok else 'FAIL'} {fn.__name__[4:]:9} {why}")

    checks += 1
    c, ok, why, jname, out = leg_cut(SWEEP, checks, journal_before)
    failed += 0 if ok else 1
    print(f"  {'ok  ' if ok else 'FAIL'} cut       {why}")

    checks += 1
    c, ok, why = leg_journal(checks, jname)
    failed += 0 if ok else 1
    print(f"  {'ok  ' if ok else 'FAIL'} journal   {why}")

    for fn in (leg_open, leg_label):
        checks += 1
        c, ok, why = fn(SWEEP, checks)
        failed += 0 if ok else 1
        print(f"  {'ok  ' if ok else 'FAIL'} {fn.__name__[4:]:9} {why}")

    if "--control" in sys.argv:
        c, ok = control(checks)
        checks = c
        failed += 0 if ok else 1

    print(f"CHECKS: {checks}, FAILED: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
