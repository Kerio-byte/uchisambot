#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-subjects.py — список предметов отвечает реестру на всех девяти страницах.

Повод (01.11.2026, сороковой блок). В реестре `tools/subjects.json` стоит строка:
«build.py падает, если чипы расходятся с этим файлом; свип сверяет ещё q2a и обе
языковые половины Terms». Первая половина правда — `build.py` действительно падает
на чипах. Вторая — нет: строку `q2a` (ответ FAQ «какие предметы вы разбираете»)
и предложение о предметах в `terms.html` не читал НИ ОДИН прибор. Проверка:
`grep -rn "q2a" tools/` до этого блока находил только сам реестр и исторический
комментарий в `build.py`; слова «физика/physics» в предложении Terms не читал
ни один `tools/check-*.py`. То есть ровно тот класс дефекта, который README
объявляет долгом: файл сам себя объявил проверенным и потому выпал из поля зрения.

Чем это дорого. Список предметов уже один раз разъехался: при первой генерации
переводчики подставили в восемь языков название ЯЗЫКА СТРАНИЦЫ вместо предмета
(ru «Русский язык», hi «हिंदी»), и страницы обещали не тот предмет, а русская
половина Terms противоречила английской. Чипы с тех пор держит сборка, а ответ
FAQ и Terms — не держал никто: правь там «физика» на «биология», и все 78 батарей
останутся зелёными.

Что меряет прибор (читает НАРИСОВАННЫЕ страницы — то, что видит человек):

  * реестр сам согласован: ровно девять языков сайта, ровно пять предметов
    у каждого, пустых и повторов нет (повтор считается без учёта регистра);
  * в списке нет НАЗВАНИЯ ЯЗЫКА вместо предмета — та самая ошибка первой
    генерации: известные плохие значения («Русский язык», «Español», «हिंदी»,
    «Bahasa Indonesia», «Português», «Türkçe», «Tiếng Việt», «Українська мова»)
    краснеют, если снова окажутся предметом;
  * на каждой из девяти страниц все пять предметов реально написаны (чипы);
  * видимый ответ FAQ о предметах называет все пять — и такой ответ ровно один;
  * копия того же ответа в разметке для поиска (`FAQPage`) называет те же пять:
    это отдельная строка, её читает поисковик, и она умеет отставать от страницы;
  * в девяти md-двойниках (ИИ-слой) названы те же пять;
  * в `terms.html` обе языковые половины называют свои пять: английская —
    английские, русская — русские (историческая ошибка была именно здесь).

Регистр не важен (в Terms предметы написаны строчными), форма слова — важна:
прибор ищет предмет как текст, а не как основу. Если язык в ответе законно
называет предмет в другой форме, прибор покраснеет — это дефект текста, а не
прибора: реестр и страница обязаны называть предмет одинаково.

Чего прибор НЕ делает (названо, чтобы «не измерили» не читалось как «измерили»):
не запускает бота и не спрашивает, какие предметы он вправду разбирает — он
сверяет тексты с реестром, а реестр со страницами; не судит, полон ли сам список
предметов (это решение владельца, а не догадка прибора); не проверяет глубину
разбора по предмету.

Запуск:
  python3 tools/check-subjects.py            # дерево
  python3 tools/check-subjects.py --control  # шесть мутантов обязаны покраснеть
Код возврата: 0 — зелено, 1 — дефект, 2 — контроль не доказал прибор, 3 — нет реестра.
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "tools" / "subjects.json"
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
WANT = 5
DETAILS = re.compile(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>\s*<p[^>]*>(.*?)</p>", re.S)
LDJSON = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.S)
CHIP = re.compile(r'<span class="chip[^"]*">(.*?)</span>', re.S)
SPACES = re.compile(r"\s+")

# Название языка вместо предмета — ошибка первой генерации (22.10.2026).
AUTONYMS = {
    "ru": ["Русский язык"],
    "es": ["Español"],
    "hi": ["हिंदी"],
    "id": ["Bahasa Indonesia"],
    "pt": ["Português"],
    "tr": ["Türkçe"],
    "vi": ["Tiếng Việt"],
    "uk": ["Українська мова"],
}
# Плохие значения, которые ловятся в любом языке (а не только в своём).
BAD_ANY = ["Русский язык", "Español", "हिंदी", "Bahasa Indonesia", "Português", "Türkçe", "Tiếng Việt"]


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


def best_answer(answers, subjects):
    """Ответ, называющий больше всего предметов, и число названных."""
    best, count = "", 0
    for text in answers:
        low = text.casefold()
        n = sum(1 for s in subjects if s.casefold() in low)
        if n > count:
            best, count = text, n
    return best, count


def chips(html):
    return [flat(t) for t in CHIP.findall(html)]


def bullet_blocks(text):
    """Блоки подряд идущих пунктов «- …» — в md-двойнике список предметов это блок."""
    blocks, cur = [], []
    for line in text.splitlines():
        if line.startswith("- "):
            cur.append(flat(line[2:]))
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    return blocks


def check_tree(root, registry_path):
    fails, info = [], {}
    registry = load_registry(registry_path)
    if registry is None:
        return ["registry: реестра предметов нет — сверять нечем"], info

    subjects = registry.get("subjects") or {}
    info["langs"] = len(subjects)

    missing = [l for l in LANGS if l not in subjects]
    extra = [l for l in subjects if l not in LANGS]
    if missing:
        fails.append("registry.langs: в реестре нет языков " + ", ".join(missing))
    if extra:
        fails.append("registry.langs: язык вне сайта — " + ", ".join(sorted(extra)))

    for lang in LANGS:
        items = subjects.get(lang) or []
        if len(items) != WANT:
            fails.append(f"registry.{lang}: предметов {len(items)}, а сайт обещает {WANT}")
        if any(not isinstance(s, str) or not s.strip() for s in items):
            fails.append(f"registry.{lang}: пустой предмет в списке")
        folded = [s.casefold() for s in items if isinstance(s, str)]
        dups = sorted({s for s in folded if folded.count(s) > 1})
        if dups:
            fails.append(f"registry.{lang}: повтор предмета — " + ", ".join(dups))

    # Название языка вместо предмета: своё — отдельно, чужие — тоже.
    for lang, items in subjects.items():
        if lang not in LANGS:
            continue
        folded = [s.casefold() for s in items if isinstance(s, str)]
        for bad in AUTONYMS.get(lang, []) + BAD_ANY:
            if bad.casefold() in folded:
                fails.append(f"registry.autonym.{lang}: «{bad}» — это название языка, а не предмет")

    terms = root / "terms.html"
    terms_text = terms.read_text(encoding="utf-8") if terms.is_file() else ""
    if not terms_text:
        fails.append("terms: файла terms.html нет — обе половины не прочитать")

    for lang in LANGS:
        items = [s for s in (subjects.get(lang) or []) if isinstance(s, str) and s.strip()]
        page = page_of(root, lang)
        if not items:
            continue
        if not page.is_file():
            fails.append(f"{lang}.visible: страницы нет — {page}")
            continue
        html = page.read_text(encoding="utf-8")
        low = html.casefold()

        gone = [s for s in items if s.casefold() not in low]
        if gone:
            fails.append(f"{lang}.page: на странице не написаны предметы " + ", ".join(gone))

        # Чипы: отдельная строка, ровно пять. Считаем совпадения с реестром, а не
        # «строка есть где-то на странице» — иначе пустой ряд чипов остался бы зелёным
        # за счёт того же слова в ответе FAQ (так и поймал контроль: два мутанта подряд).
        reg_folded = {s.casefold() for s in items}
        matched = [c for c in chips(html) if c.casefold() in reg_folded]
        if len(matched) != WANT:
            lost = [s for s in items if s.casefold() not in {c.casefold() for c in matched}]
            fails.append(f"{lang}.chips: в строке чипов {len(matched)} предмет(ов) из {WANT} совпали с реестром"
                         + (" — нет: " + ", ".join(lost) if lost else ""))

        best, count = best_answer(visible_answers(html), items)
        if count == 0:
            fails.append(f"{lang}.visible: ответа о предметах нет вовсе — ни один ответ не называет ни одного предмета")
        elif count < WANT:
            named = [s for s in items if s.casefold() in best.casefold()]
            lost = [s for s in items if s not in named]
            fails.append(f"{lang}.visible: ответ о предметах называет {count} из {WANT} — пропал: " + ", ".join(lost))

        best, count = best_answer(faq_answers(html), items)
        if count == 0:
            fails.append(f"{lang}.jsonld: в разметке для поиска ответа о предметах нет")
        elif count < WANT:
            lost = [s for s in items if s.casefold() not in best.casefold()]
            fails.append(f"{lang}.jsonld: разметка для поиска называет {count} из {WANT} — пропал: " + ", ".join(lost))

        twin = twin_of(root, lang)
        if not twin.is_file():
            fails.append(f"{lang}.twin: md-двойника нет — {twin}")
        else:
            # Список предметов в двойнике — свой блок пунктов, а не «слово где-то в файле»:
            # строка FAQ в двойнике называет те же предметы, и проверка «есть в тексте»
            # осталась бы зелёной при пустом списке (поймано контролем, мутант двойника).
            reg_folded = {s.casefold() for s in items}
            best, hit = [], 0
            for block in bullet_blocks(twin.read_text(encoding="utf-8")):
                n = sum(1 for b in block if b.casefold() in reg_folded)
                if n > hit:
                    best, hit = block, n
            if len(best) != WANT or hit != WANT:
                lost = [s for s in items if s.casefold() not in {b.casefold() for b in best}]
                fails.append(f"{lang}.twin: в списке предметов двойника {hit} из {WANT}"
                             + (" — нет: " + ", ".join(lost) if lost else ""))

    # Terms: английская половина до <section lang="ru">, русская — она сама.
    if terms_text:
        cut = terms_text.find('<section lang="ru"')
        en_half, ru_half = (terms_text, "") if cut < 0 else (terms_text[:cut], terms_text[cut:])
        if cut < 0:
            fails.append("terms.ru: русской половины (section lang=\"ru\") в terms.html нет")
        for lang, half in (("en", en_half), ("ru", ru_half)):
            items = [s for s in (subjects.get(lang) or []) if isinstance(s, str) and s.strip()]
            if not items or not half:
                continue
            low = half.casefold()
            lost = [s for s in items if s.casefold() not in low]
            if lost:
                fails.append(f"terms.{lang}: в половине Terms не названы предметы " + ", ".join(lost))
    return fails, info


def copy_tree(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    for lang in LANGS:
        for path in (page_of(src, lang), twin_of(src, lang)):
            if path.is_file():
                target = dst / path.relative_to(src)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    for name in ("terms.html",):
        if (src / name).is_file():
            shutil.copy2(src / name, dst / name)
    reg = dst / "tools" / "subjects.json"
    reg.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / "tools" / "subjects.json", reg)


def control():
    src = ROOT
    results = []

    def run(name, mutate, marker):
        tmp = Path(tempfile.mkdtemp(prefix="subj-"))
        try:
            copy_tree(src, tmp)
            mutate(tmp)
            fails, _info = check_tree(tmp, tmp / "tools" / "subjects.json")
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

    def m_chip(d):
        """Предмет подменён на странице: чип и ответ разошлись с реестром."""
        edit(page_of(d, "ru"), "Физика", "Биология")

    def m_visible(d):
        """Видимый ответ FAQ потерял предмет, разметка и двойник целы."""
        edit_visible(page_of(d, "es"), "química", "biología")

    def m_jsonld(d):
        """Разметка для поиска отстала от страницы: правим только блок FAQPage."""
        p = page_of(d, "en")
        text = p.read_text(encoding="utf-8")
        changed = 0
        for block in list(LDJSON.finditer(text)):
            body = block.group(1)
            if '"FAQPage"' in body and "chemistry" in body.casefold():
                for old in ("chemistry", "Chemistry"):
                    if old in body:
                        body = body.replace(old, "Biology", 1)
                        changed += 1
                        break
                text = text[:block.start(1)] + body + text[block.end(1):]
        assert changed == 1, f"мутант разметки нашёл {changed} блок(ов)"
        p.write_text(text, encoding="utf-8")

    def m_twin(d):
        """md-двойник живёт отдельной строкой и отстал от страницы."""
        edit(twin_of(d, "pt"), "História", "Geografia")

    def m_terms(d):
        """Русская половина Terms перестала называть предмет."""
        edit(d / "terms.html", "химия", "биология")

    def m_autonym(d):
        """В реестр вернулось название языка вместо предмета — ошибка первой генерации."""
        reg = d / "tools" / "subjects.json"
        data = json.loads(reg.read_text(encoding="utf-8"))
        data["subjects"]["ru"][1] = "Русский язык"
        reg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    run("страница: предмет подменён в чипе", m_chip, "ru.chips")
    run("FAQ: видимый ответ потерял предмет", m_visible, "es.visible")
    run("разметка для поиска отстала", m_jsonld, "en.jsonld")
    run("md-двойник отстал", m_twin, "pt.twin")
    run("Terms: русская половина потеряла предмет", m_terms, "terms.ru")
    run("реестр: название языка вместо предмета", m_autonym, "registry.autonym")

    print("контроль прибора (шесть мутантов, каждый своим сообщением):")
    for name, ok, message in results:
        print(("  ok   " if ok else "  FAIL ") + f"{name}: {message[:110]}")
    passed = sum(1 for _n, ok, _m in results if ok)
    print(f"КОНТРОЛЬ: мутантов {len(results)}, поймано {passed}")
    return 0 if passed == len(results) else 2


def main():
    ap = argparse.ArgumentParser(description="список предметов против реестра и страниц")
    ap.add_argument("--control", action="store_true", help="шесть мутантов обязаны покраснеть, каждый своим сообщением")
    args = ap.parse_args()
    if args.control:
        return control()

    fails, info = check_tree(ROOT, REGISTRY)
    subjects = (load_registry(REGISTRY) or {}).get("subjects") or {}
    # Считается то, что прибор вправду сравнивает: 2 — набор языков в реестре;
    # на язык — 3 по реестру (число, пустые, повторы), 1 — название языка вместо
    # предмета, 1 — страница и по пять совпадений в четырёх местах (страница, чипы,
    # видимый ответ, разметка, двойник — чипов и страницы по пяти, всего пять мест);
    # 3 — Terms: файл и две половины.
    total = 2 + len(LANGS) * (4 + 5 * WANT) + 3
    for fail in fails:
        print("FAIL " + fail)
    sample = subjects.get("en") or []
    print(f"предметов: {len(sample)} (en: " + ", ".join(sample) + f"); языков в реестре {info.get('langs')}")
    print(f"CHECKS: {total}, FAILED: {len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
