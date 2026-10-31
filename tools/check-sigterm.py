#!/usr/bin/env python3
"""Контроль обработчика SIGTERM в tools/check-all.py.

Повод (31.10.2026, девятый блок). В прошлом блоке осталась строка, которую
нечем было закрыть: «обработчик SIGTERM в коде есть, но в этом прогоне не
подтверждён — сигнал, посланный обёртке bash, до python не доходит». Значит,
неизвестно было и второе: раннер, убитый снаружи, гасит ли своего ребёнка
(обход 116 ссылок, браузер глаза) или уходит через os._exit и оставляет
сироту, который потом пишет в тот же каталог evidence.

Прибор делает две руки:
  живая   — настоящий check-all.py, SIGTERM ПРЯМОМУ pid раннера, сразу как
            только у него появился ребёнок. Требует: код 2, журнал с
            complete=false, в cut назван сигнал и прибор, ребёнок мёртв;
  мутант  — копия check-all.py без вызова kill_tree в обработчике. Требует,
            чтобы ребёнок ОСТАЛСЯ ЖИВ: иначе «сирот нет» — не проверка, а
            совпадение, и прибор зелёный у обеих версий кода.

Вердикт в общем формате свипа: CHECKS: N, FAILED: M

    python3 tools/check-sigterm.py
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence"
BATTERY = "links"          # 15 с сети: ребёнок успевает пожить под сигналом
MUTANT_DIR = ROOT / ".sig-mutant"


def children_of(pid: int) -> list:
    """Дети процесса по /proc — без внешних утилит и без гонки с pgrep."""
    kids = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            stat = Path(f"/proc/{entry}/stat").read_text()
            # поле 4 — ppid; имя процесса (поле 2) может содержать пробелы,
            # поэтому режем по последней скобке
            ppid = int(stat.rsplit(")", 1)[1].split()[1])
        except (OSError, IndexError, ValueError):
            continue
        if ppid == pid:
            kids.append(int(entry))
    return kids


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def kill_group(pid: int):
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except (OSError, TypeError):
        pass


def journals() -> set:
    return set(EVIDENCE.glob("check-all-*.json"))


def arm(label: str, script: Path) -> dict:
    """Одна рука: запустить раннер, дождаться ребёнка, ударить SIGTERM."""
    before = journals()
    log = EVIDENCE / f"{label}.log"
    log.parent.mkdir(exist_ok=True)
    with log.open("w") as fh:
        p = subprocess.Popen([sys.executable, "-u", str(script), "--json",
                              "--budget", "600", "--only", BATTERY],
                             cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT,
                             start_new_session=True)
        kid, t0 = None, time.time()
        while time.time() - t0 < 30:
            kids = children_of(p.pid)
            if kids:
                kid = kids[0]
                break
            if p.poll() is not None:
                break
            time.sleep(0.2)
        if not kid:
            p.kill()
            return dict(label=label, ok=False, kid=None,
                        why="ребёнок не появился за 30 с — проверять нечего")
        p.send_signal(signal.SIGTERM)          # прямо в python, не в обёртку
        p.wait(timeout=30)
        rc = p.returncode
        time.sleep(4)
        kid_alive = alive(kid)
        new = journals() - before

    out = dict(label=label, rc=rc, kid=kid, kid_alive=kid_alive,
               journal=new.pop() if new else None, why=None)
    return out


def main() -> int:
    EVIDENCE.mkdir(exist_ok=True)
    checks = failed = 0
    problems = []

    # --- рука 1: живой раннер -------------------------------------------
    a = arm("siglive", ROOT / "tools" / "check-all.py")
    checks += 5
    j = {}
    if a.get("journal"):
        try:
            j = json.loads(Path(a["journal"]).read_text())
        except (OSError, ValueError):
            j = {}
    for ok, name in [
        (a.get("rc") == 2, "код возврата 2 (прогон прерван, а не «полный»)"),
        (bool(j), "журнал записан"),
        (j.get("complete") is False, "complete=false"),
        (bool(j.get("cut")) and "сигналом 15" in str(j.get("cut")),
         "в cut назван сигнал 15"),
        (j.get("in_flight") == BATTERY and a.get("kid_alive") is False,
         f"прибор назван ({BATTERY}), ребёнок погашен"),
    ]:
        if ok:
            print(f"  ok   {name}")
        else:
            failed += 1
            print(f"  FAIL {name}  <- {a}")
            problems.append(name)

    # --- рука 2: мутант без kill_tree -----------------------------------
    MUTANT_DIR.mkdir(exist_ok=True)
    src = (ROOT / "tools" / "check-all.py").read_text()
    mutant = MUTANT_DIR / "check-all-mutant.py"
    patched, n = re.subn(
        r'(cut\["battery"\] = INFLIGHT\["name"\]\n(?:\s*#[^\n]*\n)*)(\s*)'
        r'kill_tree\(INFLIGHT\.get\("proc"\)\)',
        r'\1\2pass  # мутант: ребёнка не гасим',
        src, count=1, flags=re.M)

    if n != 1:
        print(f"  FAIL мутация не наложилась (совпадений {n}) — прибор не знает, "
              f"что ломать")
        kill_group(a.get("kid") or 0)
        shutil.rmtree(MUTANT_DIR, ignore_errors=True)
        print(f"CHECKS: {checks + 1}, FAILED: {failed + 1}")
        return 1
    mutant.write_text(patched)

    b = arm("sigmutant", mutant)
    checks += 1
    if b.get("kid_alive") is True:
        print(f"  ok   контроль: без kill_tree ребёнок живёт (прибор умеет "
              f"краснеть), код {b.get('rc')}")
    else:
        failed += 1
        print(f"  FAIL контроль: без kill_tree ребёнок тоже умер — «сирот нет» "
              f"ничего не доказывает  <- {b}")
        problems.append("контроль не краснеет")
    kill_group(b.get("kid") or 0)
    shutil.rmtree(MUTANT_DIR, ignore_errors=True)
    for f in EVIDENCE.glob("sig*.log"):
        f.unlink(missing_ok=True)

    print(f"CHECKS: {checks}, FAILED: {failed}")
    if failed:
        print("упало: " + ", ".join(problems))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
