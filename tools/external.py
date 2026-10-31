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
  python3 tools/external.py --third-party       # сеть: браузер обязан сходить только к нам
  python3 tools/external.py --third-party-control  # контроль: шесть мутантов, каждый своим сообщением
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


def run(cmd, timeout=600, env=None):
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run([sys.executable, "-u"] + [str(c) for c in cmd],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=timeout,
                       env=e)
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


def engines():
    """Страница в WebKit и Firefox: два движка, которых у прогона не было ни одного.

    31.10.2026, семнадцатый блок. Сорок восемь батарей читали эту страницу в Chromium:
    его запускает visual-420, его запускают a11y и css, его запускает глаз. Ни одна
    не спрашивала WebKit. А люди приходят в основном из встроенного браузера Telegram:
    на iPhone это WKWebView — WebKit, не Chromium. Дефект этого класса невидим сразу
    с двух сторон: в Chromium его нет вовсе (правило раскладки, которого движок не
    знает, просто выбрасывается), а глазом он выглядит как замысел — слово легло на
    1-2 px шире, шапка на телефоне разъехалась, ряд языков сломался на две строки.
    """
    tool = need("landing-cross-engine.py")
    # Порт у прибора вбит числом (8244). Второй такой же прогон рядом — это не дефект
    # страницы, но stack trace читается как дефект, а «красное от чужой причины»
    # дефектом не считается. Поэтому занятый порт называется вслух и уходит кодом 3:
    # не проверяли ≠ проверено.
    import socket as _sock
    with _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM) as s:
        s.setsockopt(_sock.SOL_SOCKET, _sock.SO_REUSEADDR, 1)
        if s.connect_ex(("127.0.0.1", 8244)) == 0:
            print("порт 8244 занят: страницу прямо сейчас читает другой прогон — "
                  "кросс-движок не проверяли")
            return 3
    rc, out = run([tool], timeout=1500, env={"LANDING_ROOT": str(ROOT)})
    checks, failed = verdict(out)
    if checks is None or failed is None:
        print("НЕ РАЗОБРАЛ вывод кросс-движка — считать непроверенным")
        print("\n".join(out.splitlines()[-6:]))
        return 2
    print(f"движки: прогонов {checks}, проблем {failed}, код {rc}")
    print(f"CHECKS: {checks}, FAILED: {failed}")
    if failed:
        print("\n".join([ln for ln in out.splitlines() if ln.strip().startswith("[")]
                        [:8]) or "\n".join(out.splitlines()[-8:]))
        return 1
    return 0 if rc == 0 else 1


def engines_control():
    """Мутант: дефект ширины, посаженный в КОПИЮ дерева, обязан покраснеть и назвать ru.

    Два требования, а не одно. Первое: прибор умеет краснеть — это доказывает его
    собственный `--control`, где клауза считается по clientWidth, а не по innerWidth
    (вторая на том же дефекте слепа, и это печатается числом). Второе: прибор читает
    то дерево, которое ему назвали. Если он молча берёт живой репозиторий по вбитому
    в него пути, дефект в копии не покраснеет — и «зелено» будет значить «смотрел не
    туда». Поэтому копия, а не живое дерево: у копии и дефект, и ответ.
    """
    tool = need("landing-cross-engine.py")
    rc_c, out_c = run([tool, "--control"], timeout=300, env={"LANDING_ROOT": str(ROOT)})
    caught = "КОНТРОЛЬ ПОЙМАЛ" in out_c
    clause = [ln.strip() for ln in out_c.splitlines() if ln.strip().startswith(("новая клауза", "КОНТРОЛЬ"))]
    if rc_c != 0 or not caught:
        print(f"НЕ ПОЙМАЛ: собственный контроль прибора дал код {rc_c}, строки: {clause[:2]}")
        return 2
    print(f"своя клауза: {clause[1] if len(clause) > 1 else clause[0]}")

    tmp = Path(tempfile.mkdtemp(prefix="engines-control-", dir=str(SCRATCH)))
    try:
        for p in ROOT.iterdir():
            if p.name in (".git", "evidence", "__pycache__", ".shots-work"):
                continue
            dst = tmp / p.name
            shutil.copytree(p, dst) if p.is_dir() else shutil.copy2(p, dst)
        page = tmp / "ru" / "index.html"
        html = page.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"<body[^>]*>", html, re.I)
        if not m:
            print("НЕ ПОЙМАЛ: в копии ru/index.html нет <body> — дефект некуда посадить")
            return 2
        wide = '<div id="ctl-wide" style="width:700px;height:4px;background:#000"></div>'
        page.write_text(html[:m.end()] + wide + html[m.end():], encoding="utf-8")

        rc_m, out_m = run([tool, "--shorts"], timeout=900, env={"LANDING_ROOT": str(tmp)})
        checks_m, failed_m = verdict(out_m)
        own = [ln for ln in out_m.splitlines() if re.match(r"\s*\[[a-z]+/[a-z]+/ru\]", ln)]
        if failed_m is None:
            print("НЕ ПОЙМАЛ: вывод мутанта не разобран")
            print("\n".join(out_m.splitlines()[-6:]))
            return 2
        if rc_m == 0 or failed_m < 1 or not own:
            print(f"НЕ ПОЙМАЛ: мутант дал код {rc_m}, проблем {failed_m}, своих [*/ru] — {len(own)}")
            return 2
        print(f"мутант: код {rc_m}, проблем {failed_m}, своих [*/ru] {len(own)}; первая — {own[0].strip()[:110]}")
        print("поймал 1 из 1")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def third_party():
    """Политика конфиденциальности обещает: «ни одного запроса на чужой сервер».

    31.10.2026, восемнадцатый блок. Обещание проверялось РАЗМЕТКОЙ: свип слов ищет
    адреса в src/poster/url(). Но разметка — не сеть. Шрифт приезжает по url() из
    соседнего CSS, пиксель аналитики — из вставки, которую регулярка не поймала,
    кука ставится скриптом, в котором адреса нет вовсе. Прибор, который открывает
    страницу браузером и записывает ВСЕ запросы, лежал в каталоге с 24.10 и не
    звался никем — то есть единственное обещание политики, которое можно проверить
    машинно, держалось на том, что кто-то вспомнит команду.
    """
    tool = need("landing-third-party.py")
    rc, out = run([tool], timeout=600)
    checks, failed = verdict(out)
    if checks is None or failed is None:
        print("НЕ РАЗОБРАЛ вывод прибора третьих сторон — считать непроверенным")
        print("\n".join(out.splitlines()[-6:]))
        return 2
    print(f"CHECKS: {checks}, FAILED: {failed}")
    if failed:
        print("\n".join([ln for ln in out.splitlines() if FAILLINE_RE.match(ln)][:8]))
        return 1
    print("\n".join([ln for ln in out.splitlines() if "no foreign host" in ln][:2]))
    return 0 if rc == 0 else 1


def third_party_control():
    """Шесть мутантов обязаны покраснеть, каждый своим сообщением.

    Красное на мутанте ничего не доказывает, если копия красна сама по себе: поэтому
    прибор сначала гоняет копию без правок и требует ноль провалов, и только потом
    сажает шесть дефектов. Обёртка судит по «поймал N из M», а не по последней строке
    CHECKS: каждый мутант печатает свой итог, и последний по счёту — всегда красный.
    """
    tool = need("landing-third-party.py")
    rc, out = run([tool, "--control"], timeout=600)
    m = re.search(r"поймал\s+(\d+)\s+из\s+(\d+)", out)
    pristine = re.search(r"копия без правок: CHECKS:\s*(\d+), FAILED:\s*(\d+)", out)
    if not m or not pristine:
        print(f"НЕ РАЗОБРАЛ контроль третьих сторон (код {rc})")
        print("\n".join(out.splitlines()[-6:]))
        return 2
    caught, total = int(m.group(1)), int(m.group(2))
    if pristine.group(2) != "0":
        print(f"НЕ ДОКАЗАНО: нетронутая копия красная ({pristine.group(2)} провалов)")
        return 2
    print(f"контроль: копия без правок {pristine.group(1)} проверок — 0 провалов; "
          f"мутантов поймано {caught} из {total}")
    for ln in out.splitlines():
        if ln.startswith("поймал ["):
            print("  " + ln)
    if rc != 0 or caught != total:
        print(f"НЕ ПОЙМАЛ: код {rc}, поймано {caught} из {total}")
        return 2
    print(f"CHECKS: {caught}, FAILED: 0")
    return 0


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
    g.add_argument("--engines", action="store_true",
                   help="кросс-движок: страница в WebKit и Firefox, а не только в Chromium")
    g.add_argument("--engines-control", dest="engines_control", action="store_true",
                   help="контроль: своя клауза ширины + дефект в КОПИИ дерева обязан покраснеть и назвать ru")
    g.add_argument("--third-party", dest="third_party", action="store_true",
                   help="сеть: браузер обязан сходить только к нам (обещание политики)")
    g.add_argument("--third-party-control", dest="third_party_control", action="store_true",
                   help="контроль: шесть мутантов (чужой хост, 404, JS, кука, storage, POST) "
                        "обязаны покраснеть каждый своим сообщением")
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
    if a.engines:
        return engines()
    if a.engines_control:
        return engines_control()
    if a.third_party:
        return third_party()
    if a.third_party_control:
        return third_party_control()
    return 3


if __name__ == "__main__":
    sys.exit(main())
