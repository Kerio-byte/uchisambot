#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-answer-time.py — обещание «сколько ждать разбор» отвечает реестру замеров.

Повод (01.11.2026, тридцать девятый блок). На девяти страницах и в их разметке для
поиска стоит самое нагруженное обещание лендинга: «обычно 5–60 секунд, если сервер
занят — до двух минут». У этого обещания есть реестр — `tools/answer-time.json`:
он хранит и числа (`typical_raw`, `ceiling_seconds`), и локализованную фразу потолка
для каждого языка (`ceiling_phrase`, снятую с живых ответов бота), и сами замеры
(`sessions`: дата, вид задачи, секунды, модель).

И до сегодняшнего дня этот реестр не читал ни один прибор. Свип звал 76 батарей,
`answer-time` среди них не было; слова страницы сверял `external.py --words` с
`claims.json`, а там этого обещания нет вовсе. То есть число, которое школьник
видит первым делом, держалось на честном слове: правь «5–60» на «5–30» в девяти
словарях — все приборы останутся зелёными. В самом реестре при этом стояла строка
«свип сверяет тексты с claims и каждый замер с потолком ceiling» — то есть реестр
обещал проверку, которой не было. Это тот же класс дефекта, что тридцать второй
блок у цен: обещание без владельца.

Что меряет прибор (читает НАРИСОВАННЫЕ страницы — то, что видит человек):

  * реестр сам согласован: цифры из `typical_raw` равны `typical`, потолок не ниже
    верхней границы обычного, фразы потолка есть ровно у девяти языков сайта;
  * на каждой из девяти страниц ровно один ответ FAQ называет фразу потолка И
    содержит обычный диапазон (пропавшее или подменённое число — дефект);
  * в разметке для поиска (`FAQPage`) тот же ответ называет оба числа: это копия,
    которую читает поисковик и ассистент, и она живёт отдельной строкой;
  * в девяти md-двойниках (ИИ-слой) названы те же два числа;
  * каждый замер в `sessions` не выше потолка (иначе страница обещает быстрее, чем
    бот отвечает), и оба вида задачи — текст и фото — измерены хотя бы раз: фото
    это и есть главный сценарий («пришли фото задачи»).

Чего прибор НЕ делает (названо, чтобы «не измерили» не читалось как «измерили»):
не запускает генерации бота (это `landing-answer-time.py`, ручной замер: он занимает
очередь и тратит настоящие разборы), не проверяет свежесть замера календарём
(возраст печатается числом, но не краснеет: порог «свежо» — решение владельца, а не
догадка прибора) и не судит, честен ли сам замер — он читает то, что записано.

Запуск:
  python3 tools/check-answer-time.py            # дерево
  python3 tools/check-answer-time.py --control  # пять мутантов обязаны покраснеть
Код возврата: 0 — зелено, 1 — дефект, 2 — контроль не доказал прибор, 3 — нет реестра.
"""
import argparse
import datetime as dt
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "tools" / "answer-time.json"
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
DETAILS = re.compile(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>\s*<p[^>]*>(.*?)</p>", re.S)
LDJSON = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.S)
NUM = re.compile(r"\d+")
SPACES = re.compile(r"\s+")


def flat(s):
    return SPACES.sub(" ", s or "").strip()


def page_of(root, lang):
    return root / "index.html" if lang == "en" else root / lang / "index.html"


def twin_of(root, lang):
    return root / "index.html.md" if lang == "en" else root / lang / "index.html.md"


def visible_answers(html):
    return [flat(a) for _q, a in DETAILS.findall(html)]


def faq_answers(html):
    """Тексты ответов из FAQPage — той копии, которую читает поисковик."""
    out = []
    for block in LDJSON.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        for node in nodes if isinstance(nodes, list) else [nodes]:
            if not isinstance(node, dict) or node.get("@type") != "FAQPage":
                continue
            for item in node.get("mainEntity", []) or []:
                answer = item.get("acceptedAnswer") or {}
                text = answer.get("text") if isinstance(answer, dict) else None
                if text:
                    out.append(flat(text))
    return out


def load_registry(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def check_tree(root, registry_path):
    fails, info = [], {}
    registry = load_registry(registry_path)
    if registry is None:
        return ["registry: реестра замеров нет — обещание ничем не держится"], info

    claims = registry.get("claims", {})
    typical_raw = claims.get("typical_raw", "")
    typical = claims.get("typical") or [int(n) for n in NUM.findall(typical_raw)][:2]
    ceiling = claims.get("ceiling")
    phrases = claims.get("ceiling_phrase") or {}
    info["typical_raw"], info["ceiling"] = typical_raw, ceiling

    if not typical_raw or not NUM.search(typical_raw):
        fails.append("registry.typical_raw: в реестре нет обычного диапазона — сверять нечем")
    elif [int(n) for n in NUM.findall(typical_raw)] != list(typical):
        fails.append(f"registry.typical: «{typical_raw}» не совпадает с {typical}")
    if not isinstance(ceiling, int) or not isinstance(typical, list) or len(typical) < 2:
        fails.append("registry.ceiling: потолок не задан числом или обычный диапазон не пара")
    elif ceiling < typical[1]:
        fails.append(f"registry.ceiling: потолок {ceiling} с ниже верхней границы обычного {typical[1]} с")

    missing = [l for l in LANGS if not phrases.get(l)]
    if missing:
        fails.append("registry.ceiling_phrase: фразы потолка нет у языков " + ", ".join(missing))
    extra = [l for l in phrases if l not in LANGS]
    if extra:
        fails.append("registry.ceiling_phrase: фраза у языка вне сайта — " + ", ".join(sorted(extra)))

    for lang in LANGS:
        phrase, raw = phrases.get(lang, ""), typical_raw
        page = page_of(root, lang)
        if not page.is_file():
            fails.append(f"{lang}.visible: страницы нет — {page}")
            continue
        html = page.read_text(encoding="utf-8")
        answers = [a for a in visible_answers(html) if phrase and phrase in a]
        if phrase and len(answers) != 1:
            fails.append(f"{lang}.visible: ответов с фразой «{phrase}» на странице {len(answers)}, ждали 1")
        elif answers and raw not in answers[0]:
            fails.append(f"{lang}.visible: ответ про ожидание не называет «{raw}» — {answers[0][:90]}")

        ld = [a for a in faq_answers(html) if phrase and phrase in a]
        if phrase and len(ld) != 1:
            fails.append(f"{lang}.jsonld: ответов FAQPage с фразой «{phrase}» {len(ld)}, ждали 1")
        elif ld and raw not in ld[0]:
            fails.append(f"{lang}.jsonld: разметка для поиска не называет «{raw}» — {ld[0][:90]}")

        twin = twin_of(root, lang)
        if not twin.is_file():
            fails.append(f"{lang}.twin: md-двойника нет — {twin}")
            continue
        text = flat(twin.read_text(encoding="utf-8"))
        for need, what in ((raw, "обычный диапазон"), (phrase, "фразу потолка")):
            if need and need not in text:
                fails.append(f"{lang}.twin: двойник не называет {what} «{need}»")

    sessions = registry.get("sessions") or []
    if not sessions:
        fails.append("sessions: замеров нет вовсе — обещание не на чем")
    kinds, newest = {}, {}
    for index, session in enumerate(sessions, 1):
        raw_date = session.get("date")
        day = str(raw_date or "")[:10]
        stamp = f"{day or '#' + str(index)} ({session.get('model', 'модель не названа')})"
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            fails.append(f"session {raw_date!r}: дата не в виде ГГГГ-ММ-ДД")
        elif dt.date.fromisoformat(day) > dt.date.today():
            fails.append(f"session {day}: дата замера в будущем")
        by_kind = {}
        for row in session.get("rows") or []:
            kind, secs = row.get("kind"), row.get("seconds")
            if not isinstance(secs, (int, float)):
                fails.append(f"session {stamp}/{kind}: секунды не числом — {secs!r}")
                continue
            if isinstance(ceiling, int) and secs > ceiling:
                fails.append(f"session {stamp}/{kind}: {secs} с выше потолка {ceiling} с — страница обещает быстрее, чем бот отвечает")
            by_kind.setdefault(kind, []).append(secs)
            kinds.setdefault(kind, []).append((day, secs))
        # сводка сессии — то, что читает человек; строки — то, что было на самом деле.
        for kind in ("text", "photo"):
            summary = session.get(kind) or {}
            got = by_kind.get(kind, [])
            if "n" in summary and summary.get("n") != len(got):
                fails.append(f"session {stamp}/{kind}: сводка говорит n={summary.get('n')}, строк {len(got)}")
            if got and summary.get("max") is not None and abs(float(summary["max"]) - max(got)) > 0.05:
                fails.append(f"session {stamp}/{kind}: сводка max={summary.get('max')}, а в строках до {max(got)} с")
        newest[stamp] = sorted(by_kind)
    for kind in ("text", "photo"):
        if not kinds.get(kind):
            fails.append(f"sessions.{kind}: вид задачи «{kind}» не измерен ни разу — обещание про него висит в воздухе")
    last_stamp = sorted(newest)[-1] if newest else ""
    if last_stamp and "photo" not in newest[last_stamp]:
        info["photo_gap"] = last_stamp

    ages = {}
    for kind, rows in kinds.items():
        rows.sort()
        last = rows[-1][0]
        try:
            ages[kind] = (dt.date.today() - dt.date.fromisoformat(last)).days
        except (ValueError, TypeError):
            ages[kind] = None
    info["ages"], info["kinds"] = ages, {k: len(v) for k, v in kinds.items()}
    return fails, info


def copy_tree(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    for lang in LANGS:
        for path in (page_of(src, lang), twin_of(src, lang)):
            if path.is_file():
                target = dst / path.relative_to(src)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    reg = dst / "tools" / "answer-time.json"
    reg.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / "tools" / "answer-time.json", reg)


def control():
    src = ROOT
    results = []

    def run(name, mutate, marker):
        tmp = Path(tempfile.mkdtemp(prefix="ans-"))
        try:
            copy_tree(src, tmp)
            mutate(tmp)
            fails, _info = check_tree(tmp, tmp / "tools" / "answer-time.json")
            caught = [f for f in fails if marker in f]
            ok = bool(caught)
            results.append((name, ok, caught[0] if caught else (fails[0] if fails else "ничего не покраснело")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def edit(path, old, new):
        text = path.read_text(encoding="utf-8")
        assert old in text, f"мутант не нашёл {old!r} в {path.name}"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def edit_visible(path, old, new):
        """Правит только видимый ответ FAQ, не трогая его копию в разметке для поиска."""
        text = path.read_text(encoding="utf-8")
        hits = [m for m in DETAILS.finditer(text) if old in m.group(2)]
        assert len(hits) == 1, f"мутант нашёл {len(hits)} видимых ответов с {old!r} в {path.name}"
        body = hits[0].group(2).replace(old, new, 1)
        path.write_text(text[:hits[0].start(2)] + body + text[hits[0].end(2):], encoding="utf-8")

    def m_number_only_visible(d):
        """Число обычного диапазона поправлено на странице — двойники и разметка целы."""
        edit_visible(page_of(d, "en"), "5–60", "5–30")

    def m_ceiling_phrase(d):
        """Локализованная фраза потолка подменена на другой срок (ru)."""
        edit_visible(page_of(d, "ru"), "до двух минут", "до пяти минут")

    def m_jsonld(d):
        """Разметка для поиска отстала от страницы: правим только блок FAQPage."""
        p = page_of(d, "en")
        text = p.read_text(encoding="utf-8")
        out, changed = [], 0
        for block in LDJSON.finditer(text):
            body = block.group(1)
            if '"FAQPage"' in body and "up to two minutes" in body:
                body, changed = body.replace("up to two minutes", "up to five minutes"), changed + 1
            out.append(text[:block.start(1)] + body + text[block.end(1):])
            text = out[-1]
        assert changed == 1, f"мутант разметки нашёл {changed} блок(ов)"
        p.write_text(text, encoding="utf-8")

    def m_session(d):
        """Замер выше потолка: бот ответил за 180 с, страница обещает 120."""
        reg_path = d / "tools" / "answer-time.json"
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        data["sessions"][0]["rows"][0]["seconds"] = 180
        reg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def m_twin(d):
        """md-двойник живёт отдельной строкой и отстал от страницы."""
        edit(twin_of(d, "pt"), "5–60", "5–30")

    def m_summary(d):
        """Сводка сессии приукрашена: в строках 17.8 с, а сводка называет 3.0 с."""
        reg_path = d / "tools" / "answer-time.json"
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        data["sessions"][0]["text"]["max"] = 3.0
        reg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    run("страница: число подменено", m_number_only_visible, "en.visible")
    run("страница: фраза потолка подменена", m_ceiling_phrase, "ru.visible")
    run("разметка для поиска отстала", m_jsonld, "en.jsonld")
    run("замер выше потолка", m_session, "выше потолка")
    run("md-двойник отстал", m_twin, "pt.twin")
    run("сводка сессии приукрашена", m_summary, "сводка max")

    print("контроль прибора (шесть мутантов, каждый своим сообщением):")
    for name, ok, message in results:
        print(("  ok   " if ok else "  FAIL ") + f"{name}: {message[:110]}")
    passed = sum(1 for _n, ok, _m in results if ok)
    print(f"КОНТРОЛЬ: мутантов {len(results)}, поймано {passed}")
    return 0 if passed == len(results) else 2


def main():
    ap = argparse.ArgumentParser(description="обещание «сколько ждать разбор» против реестра замеров")
    ap.add_argument("--control", action="store_true", help="пять мутантов обязаны покраснеть, каждый своим сообщением")
    args = ap.parse_args()
    if args.control:
        return control()

    fails, info = check_tree(ROOT, REGISTRY)
    registry = load_registry(REGISTRY) or {}
    sessions = registry.get("sessions") or []
    rows = sum(len(s.get("rows") or []) for s in sessions)
    total = 3 + len(LANGS) * 3 + len(sessions) + rows + 2 + 4 * len(sessions)

    for fail in fails:
        print("FAIL " + fail)
    ages = info.get("ages") or {}
    age_line = ", ".join(f"{k} {v} дн." for k, v in ages.items() if v is not None)
    print(f"замеры: строк {rows} в {len(sessions)} сессиях; "
          f"возраст последнего: {age_line or 'нет'}; обычный {info.get('typical_raw')}, потолок {info.get('ceiling')} с")
    if info.get("photo_gap"):
        print(f"НЕ ИЗМЕРЕНО (названо, чтобы не читалось как измеренное): фото на текущей модели — "
              f"последняя сессия {info['photo_gap']} фото не мерила; потолок для фото держится на прошлой модели")
    print(f"CHECKS: {total}, FAILED: {len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
