#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Годно ли ОКРУЖЕНИЕ мерить страницу — один вопрос, один ответ (блок 71, 03.11.2026).

Зачем. Журнал полного регресса 03.11 (55 батарей, 23 провала) читался как 23 дефекта
страницы. На деле ни один из них не был дефектом: прогон шёл интерпретатором, у которого
нет PIL и нет сборок firefox/webkit, которых ждёт его playwright. Приборы падали в первую
секунду, а журнал складывал это в колонку «провал» — то есть красное приходило от
окружения и приписывалось странице. Такое красное опаснее зелёного: оно рождает привычку
не смотреть.

Что меряется: ЭТОТ интерпретатор и ЭТА машина, а не страница.
  1. python: путь и версия;
  2. PIL: импортируется ли (им меряют пиксели `landing-pixel-density` и родня);
  3. playwright: импортируется ли и КАКИЕ сборки браузеров он ждёт (browsers.json пакета);
  4. сборки на диске: есть ли ожидаемые каталоги в PLAYWRIGHT_BROWSERS_PATH или в кэше playwright по умолчанию.

Коды возврата:
  0 — окружение годно, всё названное найдено;
  2 — окружение НЕ годно. Слово «НЕ ПРОВЕРЕНО» печатается в первой строке вердикта,
      чтобы раннер свипа (`tools/check-all.py`, SKIP_RC) прочитал это как пропуск с
      причиной, а не как дефект страницы.

Чего прибор НЕ делает: не ставит браузеры и не чинит окружение. Он только называет, чего
нет, и каким интерпретатором это мерили бы.

Проверка самого прибора (контроль): `--control` подсовывает заведомо пустой каталог
браузеров и обязан покраснеть — иначе прибор зелёный всегда и ничего не стоит.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

BROWSER_NAMES = ("chromium", "firefox", "webkit")


def default_browsers_dir() -> Path:
    env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if env and env != "0":
        return Path(env).expanduser()
    return Path.home() / ".cache" / "ms-playwright"


def _probe_code() -> str:
    return (
        "import json, os, sys\n"
        "out = {'exe': sys.executable, 'ver': sys.version.split()[0]}\n"
        "try:\n"
        "    import PIL; out['pil'] = getattr(PIL, '__version__', '?')\n"
        "except Exception:\n"
        "    out['pil'] = None\n"
        "try:\n"
        "    import playwright\n"
        "    out['pw'] = 'yes'\n"
        "    p = os.path.join(os.path.dirname(playwright.__file__), 'driver', 'package', 'browsers.json')\n"
        "    d = json.load(open(p)) if os.path.exists(p) else {}\n"
        "    out['want'] = {b['name']: b.get('revision') for b in d.get('browsers', [])\n"
        "                   if b.get('name') in ('chromium', 'firefox', 'webkit')}\n"
        "except Exception:\n"
        "    out['pw'] = None\n"
        "    out['want'] = {}\n"
        "print(json.dumps(out))\n"
    )


def measure(python: str, browsers_dir: Path) -> dict:
    """Снимок окружения. Один и тот же код для прямого запуска и для свипа."""
    r = subprocess.run([python, "-c", _probe_code()], capture_output=True, text=True, timeout=120)
    try:
        data = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return dict(exe=python, ver="?", pil=None, pw=None, want={}, have={},
                    error=(r.stderr or r.stdout or "нет ответа").strip()[-200:])
    have = {}
    for name in BROWSER_NAMES:
        rev = data.get("want", {}).get(name)
        if not rev:
            continue
        # chromium ставится двумя каталогами: полный и headless-shell; годится любой.
        cands = [browsers_dir / f"{name}-{rev}"]
        if name == "chromium":
            cands.append(browsers_dir / f"chromium_headless_shell-{rev}")
        have[name] = next((str(c) for c in cands if c.is_dir()), None)
    data["have"] = have
    data["browsers_dir"] = str(browsers_dir)
    return data


def gaps(m: dict) -> list:
    """Чего не хватает. Пустой список — окружение годно."""
    out = []
    if not m.get("pil"):
        out.append("нет PIL (пиксельные приборы не могут работать)")
    if not m.get("pw"):
        out.append("нет playwright (браузерные приборы не могут работать)")
    else:
        for name in BROWSER_NAMES:
            if name in (m.get("want") or {}) and not (m.get("have") or {}).get(name):
                out.append(f"нет сборки {name} {m['want'][name]} в {m.get('browsers_dir')}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="годно ли окружение мерить лендинг")
    ap.add_argument("--python", default=sys.executable, help="какой интерпретатор проверять")
    ap.add_argument("--browsers", default=None, help="каталог сборок браузеров")
    ap.add_argument("--json", default=None, help="куда положить снимок")
    ap.add_argument("--control", action="store_true",
                    help="контроль прибора: пустой каталог браузеров обязан покраснеть")
    args = ap.parse_args()

    browsers = Path(args.browsers).expanduser() if args.browsers else default_browsers_dir()
    if args.control:
        browsers = Path("/nonexistent/control-empty-browsers")
    m = measure(args.python, browsers)
    miss = gaps(m)
    if args.json:
        Path(args.json).write_text(json.dumps(dict(measured=m, gaps=miss), ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    print(f"ENV exe={m.get('exe')} python={m.get('ver')} PIL={m.get('pil') or 'НЕТ'} "
          f"playwright={'да' if m.get('pw') else 'НЕТ'}")
    want = m.get("want") or {}
    for name in BROWSER_NAMES:
        if name in want:
            got = (m.get("have") or {}).get(name)
            print(f"ENV браузер {name} {want[name]}: {'есть' if got else 'НЕТ'}")
    print(f"ENV каталог сборок: {browsers}")
    if miss:
        print("НЕ ПРОВЕРЕНО: окружение не годно — " + "; ".join(miss))
        print(f"CHECKS: {len(BROWSER_NAMES) + 2}, FAILED: {len(miss)}")
        return 2
    print("ОКРУЖЕНИЕ ГОДНО: этим интерпретатором страницу мерить можно")
    print(f"CHECKS: {len(BROWSER_NAMES) + 2}, FAILED: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
