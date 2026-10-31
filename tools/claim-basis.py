#!/usr/bin/env python3
"""Основание обещаний страницы в живом продукте, а не в словах.

    python3 tools/claim-basis.py [--bot-dir DIR] [--offline]

Зачем. Тридцать заходов смыслового прохода проверяли, что страница говорит то,
что обещает, и что обещания не противоречат друг другу. Но два обещания живут
не в тексте, а в железе:

  1. «Работает круглосуточно / в любое время дня» — держится на том, что бот
     запущен и переживёт перезагрузку сервера.
  2. «Вся ИИ-обработка идёт на нашей собственной инфраструктуре — задачи не
     передаются сторонним ИИ-сервисам» — держится на адресе, по которому бот
     ходит за разбором.

Оба проверялись глазами один раз и ни одним прибором. Прибор читает:

  - .env бота: только LLM_BASE_URL / LLM_MODEL / LLM_PROVIDER, значения
    секретов не печатаются и в JSON не попадают;
  - адрес LLM: хост обязан быть петлёй (127.0.0.1 / localhost / ::1), иначе
    задачи уходят наружу и обещание ложное;
  - GET <base>/v1/models: имена моделей должны быть локальными путями к весам
    (.gguf), а не именами чужих моделей — так видно, что считает свой сервер;
  - код бота: ни одного адреса сторонних ИИ-сервисов;
  - служба: study-bot.service у менеджера пользователя — active, enabled,
    Linger=yes (иначе после перезагрузки без входа в систему бот не поднимется);
  - bot/i18n.py: кортеж SUPPORTED — третье обещание «девять языков» тоже живёт
    не в вёрстке: страница обещает столько языков, на скольких реально говорит
    бот, и каждая языковая страница обязана звать бота СВОИМ кодом
    (src_landing_hi с /hi/), иначе человек читал хинди и слышит чужой язык.

--offline пропускает сетевой запрос к LLM (остальное проверяется).

Код возврата: 0 — все проверки прошли, 1 — есть провал, 2 — прибор не смог.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOT = ROOT.parents[1] / "study-bot"
LOOPBACK = {"127.0.0.1", "localhost", "::1", "[::1]"}

# Девять языков страницы. Список живёт здесь, чтобы прибор замечал не только
# «бот разучился», но и «страница завела десятый язык, а бот его не знает».
EXPECTED_LANGS = ("en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk")

# Адреса сторонних ИИ-сервисов. Ищем в коде бота: обещание «не передаём»
# ломается не текстом, а одной строкой import/URL.
FOREIGN = (
    "api.openai.com", "openrouter.ai", "api.anthropic.com", "generativelanguage.googleapis.com",
    "api.deepseek.com", "api.mistral.ai", "huggingface.co", "api.replicate.com",
    "api.together.xyz", "api.groq.com", "api.x.ai", "api.cohere.ai",
)

rows: list[dict] = []


def check(name: str, ok: bool, detail: str) -> None:
    rows.append({"check": name, "ok": bool(ok), "detail": detail})


def read_env(bot: Path) -> dict[str, str]:
    """Только три ключа маршрута LLM. Секреты не читаются вообще."""
    want = {"LLM_BASE_URL", "LLM_MODEL", "LLM_PROVIDER"}
    out: dict[str, str] = {}
    env = bot / ".env"
    if not env.is_file():
        return out
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        if key.strip() in want:
            out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def host_of(url: str) -> str:
    m = re.match(r"^[a-z]+://([^/:]+)", url.strip(), re.I)
    return (m.group(1) if m else "").lower()


def models(base: str) -> list[str]:
    with urllib.request.urlopen(base.rstrip("/") + "/models", timeout=8) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    out = []
    for m in data.get("data") or data.get("models") or []:
        name = m.get("id") or m.get("name") or m.get("model") or ""
        if name:
            out.append(str(name))
    return out


def main_pid(unit: str) -> int:
    try:
        p = subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value", unit],
                           capture_output=True, text=True, timeout=10)
        return int((p.stdout or "0").strip() or 0)
    except (ValueError, OSError):
        return 0


def proc_env(pid: int) -> dict[str, str]:
    """Маршрут LLM из ЖИВОГО процесса, а не из файла.

    .env можно переписать после запуска службы: файл будет говорить одно,
    а бот продолжит работать с тем, что получил при старте. Секреты не читаются.
    """
    out: dict[str, str] = {}
    try:
        data = Path(f"/proc/{pid}/environ").read_bytes()
    except OSError:
        return out
    for item in data.split(b"\0"):
        key, sep, val = item.decode("utf-8", "replace").partition("=")
        if sep and key in {"LLM_BASE_URL", "LLM_MODEL", "LLM_PROVIDER"}:
            out[key] = val.strip()
    return out


def listeners(port: int) -> list[int]:
    """Кто слушает порт: pid из ss. Пусто — никто или прав не хватило."""
    try:
        p = subprocess.run(["ss", "-ltnp", f"sport = :{port}"], capture_output=True, text=True, timeout=10)
    except OSError:
        return []
    pids: list[int] = []
    for x in re.findall(r"pid=(\d+)", p.stdout):
        if int(x) not in pids:
            pids.append(int(x))
    return pids


def routes_of(pid: int) -> list[tuple[int, str]]:
    """Карта --route <слушает>:<куда>:... из командной строки прокси."""
    try:
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        return []
    return [(int(a), b) for a, b in re.findall(r"--route\s+(\d+):([^:\s]+):", cmd)]


def walk_chain(url: str, hops: int = 2) -> tuple[list[str], str]:
    """Первый прыжок — адрес из настройки, дальше — по карте --route прокси.

    Петля на входе ничего не доказывает: прокси на 127.0.0.1 может отправлять
    запрос на чужой адрес, и обещание «задачи не уходят наружу» станет ложным
    при зелёном llm.loopback. Возвращает (прыжки, приговор); пустой приговор — чисто.
    """
    steps: list[str] = []
    m = re.search(r":(\d+)", url)
    if not m:
        return steps, "в адресе нет порта — цепочку не пройти"
    port = int(m.group(1))
    for _ in range(hops):
        pids = listeners(port)
        if not pids:
            steps.append(f"{port}: слушателя нет")
            return steps, f"порт {port} никто не слушает"
        pid = pids[0]
        rs = routes_of(pid)
        if not rs:
            steps.append(f"{port}: процесс {pid} без --route, сам сервер")
            return steps, ""
        nxt = [b for a, b in rs if a == port]
        if not nxt:
            steps.append(f"{port}: у процесса {pid} нет маршрута этого порта")
            return steps, f"порт {port} слушает прокси, но куда он ведёт, не сказано"
        if not nxt[0].isdigit():
            steps.append(f"{port} -> {nxt[0]}")
            return steps, f"прокси ведёт на {nxt[0]} — это не петля"
        steps.append(f"{port} -> {nxt[0]}")
        port = int(nxt[0])
    return steps, ""


def unit_state(unit: str) -> tuple[str, str, str]:
    def sc(*args: str) -> str:
        try:
            p = subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, timeout=10)
            return p.stdout.strip()
        except Exception:
            return ""

    return sc("is-active", unit), sc("is-enabled", unit), sc("show", "-p", "NRestarts", "--value", unit)


def linger() -> str:
    try:
        p = subprocess.run(["loginctl", "show-user", Path.home().name, "-p", "Linger", "--value"],
                           capture_output=True, text=True, timeout=10)
        return p.stdout.strip()
    except Exception:
        return ""


def page_codes(root: Path) -> list[str]:
    """Языки, которые страница обещает: hreflang в шапке главной."""
    html = (root / "index.html").read_text(encoding="utf-8", errors="replace")
    codes = re.findall(r'hreflang="([a-z]{2})"', html)
    seen: list[str] = []
    for c in codes:
        if c not in seen:
            seen.append(c)
    return seen


def bot_languages(bot: Path) -> list[str]:
    """Языки, на которых бот реально говорит: кортеж SUPPORTED из bot/i18n.py.

    Читаем файл, а не импортируем модуль: прибор не должен тянуть зависимости
    бота (telegram, httpx) и не должен ничего запускать в его процессе.
    """
    src = bot / "bot" / "i18n.py"
    text = src.read_text(encoding="utf-8", errors="replace")
    consts = dict(re.findall(r'^(LANG_[A-Z]+)\s*=\s*"([a-z]{2})"', text, re.M))
    m = re.search(r"^SUPPORTED[^=\n]*=\s*\(([^)]*)\)", text, re.M | re.S)
    if not m:
        return []
    names = re.findall(r"LANG_[A-Z]+", m.group(1))
    return [consts[n] for n in names if n in consts]


def own_cta_missing(root: Path, codes: list[str]) -> list[str]:
    """Страница языка обязана звать бота СВОИМ кодом, иначе человек с /hi/
    попадает в приветствие на другом языке."""
    missing = []
    for code in codes:
        page = root / "index.html" if code == "en" else root / code / "index.html"
        if not page.is_file():
            missing.append(f"{code}: нет страницы")
            continue
        if f"src_landing_{code}" not in page.read_text(encoding="utf-8", errors="replace"):
            missing.append(f"{code}: нет src_landing_{code}")
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot-dir", default=str(DEFAULT_BOT))
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--control", action="store_true", help="мутанты маршрута: чужой прыжок обязан покраснеть")
    args = ap.parse_args()
    bot = Path(args.bot_dir).expanduser().resolve()

    # 0. Контроль прибора: правила разбора обязаны краснеть на чужих значениях
    if args.control:
        foreign = re.findall(r"--route\s+(\d+):([^:\s]+):", "--route 8080:1.1.1.1:3000")
        own = re.findall(r"--route\s+(\d+):([^:\s]+):", "--route 8080:9080:3000")
        check("control.route_foreign", bool(foreign) and not foreign[0][1].isdigit(),
              f"чужой маршрут разобран как {foreign[0][1] if foreign else 'НЕ РАЗОБРАН'} — обязан считаться не-петлёй")
        check("control.route_local", bool(own) and own[0][1].isdigit(),
              f"свой маршрут разобран как {own[0][1] if own else 'НЕ РАЗОБРАН'} — обязан считаться петлёй")
        cloud = host_of("https://api.openai.com/v1")
        check("control.host_foreign", cloud == "api.openai.com" and cloud not in LOOPBACK,
              f"хост чужого адреса разобран как {cloud or '?'} — обязан быть снаружи")

    # 1. Маршрут LLM
    env = read_env(bot)
    base = env.get("LLM_BASE_URL", "")
    model = env.get("LLM_MODEL", "")
    check("llm.env", bool(base), f".env бота: LLM_BASE_URL задан={bool(base)}, LLM_MODEL={model or '—'}, "
                                 f"LLM_PROVIDER={env.get('LLM_PROVIDER') or '—'}")
    if base:
        h = host_of(base)
        check("llm.loopback", h in LOOPBACK,
              f"адрес разбора: {h or '?'} — «{'своя инфраструктура' if h in LOOPBACK else 'НАРУЖУ, обещание ложное'}»")

    # 2. Кто на том конце
    if base and not args.offline:
        t0 = time.time()
        try:
            names = models(base)
            local = [n for n in names if n.lower().endswith(".gguf") or n.startswith("/")]
            check("llm.weights_local", bool(local),
                  f"/v1/models ответил за {time.time() - t0:.1f} с: {len(names)} модел.; локальные веса: "
                  f"{', '.join(Path(n).name for n in local) or 'НЕ НАЙДЕНЫ'}")
        except (urllib.error.URLError, OSError, ValueError) as exc:
            check("llm.weights_local", False, f"/v1/models не ответил: {type(exc).__name__}: {exc}")

    # 2b. Живой процесс и цепочка прокси: файл может говорить одно, работать другое
    if base:
        pid = main_pid("study-bot")
        live = proc_env(pid) if pid else {}
        if not live:
            check("llm.running", False,
                  f"MainPID={pid or '?'}: окружение процесса не прочитать — чем бот работает на самом деле, не доказано")
        else:
            same = (host_of(live.get("LLM_BASE_URL", "")) == host_of(base)
                    and live.get("LLM_MODEL", "") == model)
            check("llm.running", same,
                  f"процесс {pid}: {live.get('LLM_PROVIDER') or '—'} {host_of(live.get('LLM_BASE_URL', '')) or '?'}, "
                  f"модель {live.get('LLM_MODEL') or '—'}"
                  + ("" if same else f" — РАСХОДИТСЯ с .env ({host_of(base) or '?'}, {model or '—'})"))
    if base and host_of(base) in LOOPBACK and not args.offline:
        steps, verdict = walk_chain(base)
        check("llm.chain", not verdict,
              "цепочка: " + " -> ".join(steps) + ("" if not verdict else f" — {verdict}"))

    # 3. Код бота: чужие адреса
    hits: list[str] = []
    for py in sorted((bot / "bot").glob("*.py")):
        text = py.read_text(encoding="utf-8", errors="replace")
        for host in FOREIGN:
            if host in text:
                hits.append(f"{py.name}:{host}")
    check("llm.no_foreign", not hits, "сторонние ИИ-адреса в коде бота: " + (", ".join(hits) or "нет"))

    # 4. Круглосуточно: служба, автозапуск, работа без входа в систему
    state, enabled, restarts = unit_state("study-bot")
    ling = linger()
    check("uptime.active", state == "active", f"study-bot.service: {state or 'нет ответа'}, NRestarts={restarts or '?'}")
    check("uptime.enabled", enabled in ("enabled", "enabled-runtime", "static"), f"автозапуск: {enabled or '?'}")
    check("uptime.linger", ling == "yes", f"Linger={ling or '?'} — {'работает без входа в систему' if ling == 'yes' else 'после перезагрузки без входа бот не поднимется'}")

    # 5. Девять языков: страница обещает столько, на скольких говорит бот
    pages = page_codes(ROOT)
    speaks = bot_languages(bot)
    check("langs.pages", len(pages) == 9 and set(pages) == set(EXPECTED_LANGS),
          f"страница обещает {len(pages)} язык(ов): {', '.join(pages) or '—'}")
    if speaks:
        mute = [c for c in pages if c not in speaks]
        check("langs.supported", not mute,
              f"бот говорит на {len(speaks)}: {', '.join(speaks)}"
              + (f"; ОБЕЩАНЫ, А БОТ НЕ ГОВОРИТ: {', '.join(mute)}" if mute else ""))
    else:
        check("langs.supported", False, f"не нашёл SUPPORTED в {bot / 'bot' / 'i18n.py'}")
    quiet = own_cta_missing(ROOT, pages)
    check("langs.own_cta", not quiet, "метка языка на своей странице: " + (", ".join(quiet) or "у всех девяти своя"))

    failed = [r for r in rows if not r["ok"]]
    for r in rows:
        print(f"  [{'ok  ' if r['ok'] else 'FAIL'}] {r['check']}: {r['detail']}")
    print(f"CHECKS: {len(rows)}, FAILED: {len(failed)}")

    if "--json" in sys.argv:
        outp = ROOT / "evidence" / f"claim-basis-{time.strftime('%Y%m%dT%H%M%S')}.json"
        outp.parent.mkdir(exist_ok=True)
        outp.write_text(json.dumps({"rows": rows, "bot_dir": str(bot)}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"evidence: {outp}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
