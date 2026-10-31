#!/usr/bin/env python3
"""check-source-labels.py — метка `start=` сверена с тем, кто её РАЗБИРАЕТ.

Повод (01.11.2026, двадцать второй блок). Двадцать один блок держал страницу, и метка
источника в ссылке на бота проверялась только на НАЛИЧИЕ: `ai-layer` смотрит, что
`start=` в ссылке есть, `links` — что адрес жив, `referral-parity` — что числа
приглашения сходятся с `payments.py`. А понимает ли метку адресат, не смотрел никто.

Между тем одну и ту же грамматику метки независимо держат ТРИ места:
  * `tools/build.py` — пишет метку в разметку (генератор);
  * `study-bot/bot/handlers.py` — `_LANDING_LABEL` решает, каким языком бот поздоровается
    (`landing_lang`, 23.10.2026: посетитель /hi/ с финским Telegram получал русское
    приветствие, потому что все девять страниц несли один `src_landing`);
  * `study-bot/scripts/source_stats.py` — `_land_re` раскладывает источники по языку
    страницы и месту кнопки в отчёте, который читает владелец.

Три копии одной грамматики расходятся молча. Стоит боту переименовать позицию
(`sticky` → `sticky_cta`) — страница цела, кнопка нажимается, человек приходит, а
`landing_lang()` возвращает None: язык первого экрана теряется, и в отчёте эта метка
проваливается мимо разреза «язык страницы», оставаясь только строкой в общем списке.
Стоит отчёту сузить регулярку — владелец видит девять языков нулями и не знает, что
метки врут. Обе поломки выглядят как «пока мало людей», а не как дефект.

Что проверяет эта батарея (только чтение; бот — чужой код, поэтому читается, но не
правится, путь переопределяется `LANDING_BOT` / `LANDING_BOT_SCRIPTS`)

1. Грамматика: набор позиций, который ПРИНИМАЕТ бот, равен набору, который понимает
   отчёт, равен набору, который страницы ВЫПУСКАЮТ. Сверка пробами, а не сравнением
   строк регулярки: проба — синтетическая метка, ответ — да/нет.
2. Девять страниц: ровно четыре ссылки на бота, четыре разные метки — базовая и три
   позиции; ни одной без метки и ни одной с чужой позицией.
3. Язык: каждая метка страницы разрешается `landing_lang()` ровно в ЯЗЫК ЭТОЙ страницы,
   и этот язык есть в `SUPPORTED` бота. Иначе страница обещает боту язык, которого он
   не знает.
4. Отчёт: каждая метка раскладывается отчётом в (язык этой страницы, позиция), позиции
   четырёх меток не схлопываются в одну — иначе «какая кнопка работает» не имеет ответа.
5. Старая метка `src_landing` (до 23.10) не осталась ни в одном файле дерева.
6. Уникальность: все метки дерева различаются — копипаст метки чужой страницы виден.
7. `llms.txt`: одна ссылка, метка с префиксом `src_`, не совпадает ни с одной меткой
   страницы (иначе трафик ИИ-слоя сливается с трафиком страницы в одном ведре) и НЕ
   разбирается как языковая — иначе посетитель из `llms.txt` получил бы первый экран
   языка, которого в файле нет.
8. 404: единственная метка `src_landing_404` нарочно не языковая (страницы нет — языка
   нет), но бот её всё равно записывает как источник: проверяется и то, и другое, чтобы
   правка с любой стороны уронила батарею.
9. Запись источника в боте на месте: `payload.startswith("src_")` +
   `storage.set_source(...)` + колонка `source` в таблице users. Метка без приёмника —
   украшение.
10. Девять md-двойников несут ОДНУ метку без языка (`src_llms`). Это не «зелено», это
    названный разрыв: двойник знает язык страницы, а боту его не говорит, потому что
    грамматика бота не знает токена «двойник» (`band|shots|sticky`), а метка страницы
    слила бы двойник с HTML-страницей в одном ведре. Разрыв проверяется как факт: если
    кто-то начнёт ставить двойникам РАЗНЫЕ метки — красный; если грамматика бота
    научится токену `md` — красный с указанием, что двойникам пора нести язык
    (`src_landing_<язык>_md`), и тогда разрыв закрывается правкой в дереве.

Код возврата: 0 — всё сходится; 1 — расхождение (правится метка или бот, но не проверка).

  python3 tools/check-source-labels.py
  python3 tools/check-source-labels.py --control
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
POSITIONS = ("band", "shots", "sticky")
# Пробы: реальные позиции плюс те, которых в дереве нет. Проба отвечает на вопрос
# «примет ли разбор эту метку», не заглядывая внутрь регулярки.
PROBES = POSITIONS + ("hero", "md", "footer", "top")
MD_LABEL = "src_llms"
NOT_FOUND_LABEL = "src_landing_404"

BOT = Path(os.environ.get("LANDING_BOT") or ROOT.parent.parent / "study-bot" / "bot")
BOT_SCRIPTS = Path(os.environ.get("LANDING_BOT_SCRIPTS") or BOT.parent / "scripts")

LINK_RE = re.compile(r"t\.me/UchiSamBot\?start=([A-Za-z0-9_\-]*)")


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"нет файла: {path} — метка осталась без адресата")
    return path.read_text(encoding="utf-8")


def bot_pattern(bot: Path) -> str:
    """Регулярка метки CTA из кода бота, как написана, а не как мы её помним."""
    src = read_text(bot / "handlers.py")
    m = re.search(r"_LANDING_LABEL\s*=\s*re\.compile\(\s*r?[\"']([^\"']+)[\"']", src)
    if not m:
        raise SystemExit("handlers.py: не нашёл _LANDING_LABEL — разбор метки исчез")
    return m.group(1)


def report_pattern(scripts: Path) -> str:
    """Регулярка разреза источников из отчёта владельцу (source_stats.py)."""
    src = read_text(scripts / "source_stats.py")
    m = re.search(r"_land_re\s*=\s*re\.compile\(\s*r?[\"']([^\"']+)[\"']", src)
    if not m:
        raise SystemExit("source_stats.py: не нашёл _land_re — отчёт перестал разбирать метки")
    return m.group(1)


def supported_langs(bot: Path) -> list[str]:
    src = read_text(bot / "i18n.py")
    consts = dict(re.findall(r"^(LANG_[A-Z]{2})\s*=\s*\"([a-z]{2})\"", src, re.M))
    m = re.search(r"^SUPPORTED\s*:[^=]*=\s*\(([^)]*)\)", src, re.M)
    if not m or not consts:
        raise SystemExit("i18n.py: не нашёл SUPPORTED — список языков бота неизвестен")
    names = re.findall(r"LANG_[A-Z]{2}", m.group(1))
    return [consts[n] for n in names if n in consts]


def accepted(pattern: str, label: str) -> bool:
    return re.fullmatch(pattern, label) is not None


def group_of(pattern: str, label: str) -> tuple[str, str] | None:
    """Как отчёт разложит метку: (язык, позиция) или None."""
    m = re.fullmatch(pattern, label)
    if not m:
        return None
    return m.group(1), (m.group(2) or "hero")


def page_labels(root: Path) -> dict[str, list[str]]:
    out = {}
    for lang in LANGS:
        path = root / ("index.html" if lang == "en" else f"{lang}/index.html")
        out[lang] = LINK_RE.findall(read_text(path))
    return out


def md_labels(root: Path) -> dict[str, list[str]]:
    out = {}
    for lang in LANGS:
        path = root / ("index.html.md" if lang == "en" else f"{lang}/index.html.md")
        out[lang] = LINK_RE.findall(read_text(path))
    return out


def run(root: Path, bot: Path, scripts: Path) -> tuple[list[tuple[str, bool, str]], list[str]]:
    """Возвращает (проверки для печати, провалы). root — дерево, bot/scripts — чужой код."""
    bp = bot_pattern(bot)
    rp = report_pattern(scripts)
    supported = supported_langs(bot)
    checks: list[tuple[str, bool, str]] = []
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))
        if not ok:
            fails.append(f"{name}: {detail}" if detail else name)

    # 1. Грамматика: что принимает бот, что понимает отчёт, что выпускают страницы.
    # Бот вправе знать БОЛЬШЕ дерева (расширение разбора — улучшение, а не дефект), но
    # дерево не вправе выпускать метку, которую бот не разберёт, а отчёт обязан понимать
    # ровно столько же, сколько бот: разъехавшиеся копии одной грамматики и есть дефект.
    bot_pos = [p for p in PROBES if accepted(bp, f"src_landing_en_{p}")]
    rep_pos = [p for p in PROBES if group_of(rp, f"landing_en_{p}")]
    check("грамматика/бот", set(POSITIONS) <= set(bot_pos),
          f"бот не разбирает позиции {sorted(set(POSITIONS) - set(bot_pos))} — страницы их выпускают")
    check("грамматика/отчёт", rep_pos == bot_pos,
          f"отчёт понимает позиции {rep_pos}, бот — {bot_pos}: копии грамматики разъехались")
    check("грамматика/язык", accepted(bp, "src_landing_en") and not accepted(bp, "src_landing_eng"),
          "язык в метке бота — ровно две строчные буквы")

    pages = page_labels(root)

    # 2-4. Девять страниц: четыре ссылки, четыре разные метки, язык и позиция совпадают.
    for lang in LANGS:
        labels = pages[lang]
        where = f"{lang}/index.html"
        check(f"{where}: ссылок", len(labels) == 4,
              f"ссылок на бота {len(labels)}, ожидалось 4 (герой, полоса, кадры, липкая)")
        check(f"{where}: метки разные", len(set(labels)) == len(labels),
              f"повтор метки: {labels}")
        for label in labels:
            if not label:
                check(f"{where}: пустая метка", False, "ссылка на бота без start=")
                continue
            m = re.fullmatch(bp, label)
            if not m:
                check(f"{where}: {label}", False,
                      "бот такую метку не разбирает — язык первого экрана потерян")
                continue
            check(f"{where}: {label} язык", m.group(1) == lang,
                  f"метка говорит {m.group(1)}, страница — {lang}")
            check(f"{where}: {label} в SUPPORTED", m.group(1) in supported,
                  f"языка {m.group(1)} бот не знает: {supported}")
            # Отчёт читает УЖЕ обрезанный источник (бот пишет payload[4:]), поэтому
            # регулярка отчёта ждёт «landing_…», без префикса src_.
            grp = group_of(rp, label[4:])
            check(f"{where}: {label} в отчёте", grp is not None and grp[0] == lang,
                  f"отчёт разложит в {grp}, а страница — {lang}")
        positions = sorted({g[1] for g in (group_of(rp, lb[4:]) for lb in labels) if g})
        check(f"{where}: позиции различимы", positions == sorted(["hero", *POSITIONS]),
              f"отчёт видит позиции {positions}")

    # 5. Старая метка не осталась в ОТДАВАЕМЫХ файлах. Шаблон index-src.html несёт её
    # нарочно (сборка подставляет язык), исторические отчёты в evidence — тоже история,
    # а не вёрстка: проверяется дерево, которое уходит посетителю.
    served = [root / ("index.html" if lang == "en" else f"{lang}/index.html") for lang in LANGS]
    served += [root / "404.html", root / "llms.txt"]
    served += [root / ("index.html.md" if lang == "en" else f"{lang}/index.html.md") for lang in LANGS]
    leftovers = []
    for path in served:
        text = read_text(path)
        if re.search(r"start=(src_landing)(?=[\"'&\s)]|$)", text):
            leftovers.append(str(path.relative_to(root)))
    check("старая метка src_landing", not leftovers, f"осталась в: {leftovers}")

    # 6. Уникальность меток входов: каждая страница и 404 — своя метка.
    # Двойники нарочно делят одну метку с llms.txt (разрыв ИИ-слоя, проверяется ниже),
    # поэтому в уникальность входов они не входят.
    all_labels = [lb for lbs in pages.values() for lb in lbs]
    all_labels += LINK_RE.findall(read_text(root / "404.html"))
    page_only = list(all_labels)
    dupes = sorted({lb for lb in all_labels if all_labels.count(lb) > 1})
    check("уникальность меток", not dupes, f"одна метка у разных входов: {dupes}")

    # 7. llms.txt: метка есть, не языковая, не совпадает со страницей.
    llms_file = read_text(root / "llms.txt")
    llms_labels = LINK_RE.findall(llms_file)
    check("llms.txt: одна ссылка на бота", len(llms_labels) == 1, f"нашёл {llms_labels}")
    if len(llms_labels) == 1:
        label = llms_labels[0]
        check("llms.txt: префикс src_", label.startswith("src_"),
              f"метка «{label}» не начинается с src_ — бот её не запишет")
        check("llms.txt: не языковая метка", not accepted(bp, label),
              "метка разбирается как язык страницы, которой в llms.txt нет")
        check("llms.txt: не метка страницы", label not in page_only,
              f"метка «{label}» уже занята страницей — трафик сольётся в одном ведре")

    # 8. 404: метка нарочно не языковая, но источник записывается.
    nf = LINK_RE.findall(read_text(root / "404.html"))
    check("404: одна ссылка", len(nf) == 1, f"нашёл {nf}")
    if len(nf) == 1:
        check("404: метка", nf[0] == NOT_FOUND_LABEL, f"метка «{nf[0]}» вместо {NOT_FOUND_LABEL}")
        check("404: не языковая", not accepted(bp, nf[0]),
              "404 не должен обещать язык — страницы нет")
        check("404: в общий разрез не попадает", group_of(rp, nf[0][4:]) is None,
              "отчёт разложит 404 как языковую страницу")

    # 9. Приёмник метки в боте на месте.
    handlers = read_text(bot / "handlers.py")
    storage = read_text(bot / "storage.py")
    check("бот: префикс src_", 'payload.startswith("src_")' in handlers,
          "бот перестал узнавать метки источника")
    check("бот: set_source", re.search(r"storage\.set_source\(\s*uid\s*,\s*payload\[4:\]\s*\)", handlers) is not None,
          "метка записывается не тем вызовом — источник потерян")
    check("бот: колонка source", re.search(r"\bsource\s+TEXT\b", storage) is not None,
          "в схеме users нет колонки source")

    # 10. Разрыв ИИ-слоя назван и проверен как факт.
    twins = md_labels(root)
    twin_labels = {lb for lbs in twins.values() for lb in lbs}
    check("двойники: одна и та же метка", twin_labels == {MD_LABEL},
          f"метки двойников: {sorted(twin_labels)} — тогда язык и вход не различить")
    check("двойники: метка не языковая", not accepted(bp, MD_LABEL),
          "метка двойников разбирается как язык страницы")
    if accepted(bp, "src_landing_en_md"):
        # Бот научился токену двойника — разрыв можно закрыть, и молчать об этом нельзя.
        for lang in LANGS:
            want = f"src_landing_{lang}_md"
            check(f"двойник {lang}: язык", set(twins[lang]) == {want},
                  f"бот понимает _md, а двойник несёт {sorted(set(twins[lang]))} — язык теряется")

    return checks, fails


def control() -> int:
    """Мутанты: чистая копия зелёная, каждый дефект краснеет своим сообщением."""
    tree_files = ["index.html", "404.html", "llms.txt"]
    for lang in LANGS:
        tree_files += ["index.html.md"] if lang == "en" else [f"{lang}/index.html", f"{lang}/index.html.md"]
    bot_files = ["handlers.py", "i18n.py", "storage.py"]
    script_files = ["source_stats.py"]

    def build_copy(dst: Path) -> tuple[Path, Path, Path]:
        root = dst / "tree"
        bot = dst / "bot"
        scripts = dst / "scripts"
        for rel in tree_files:
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, root / rel)
        for rel in bot_files:
            bot.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BOT / rel, bot / rel)
        for rel in script_files:
            scripts.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BOT_SCRIPTS / rel, scripts / rel)
        return root, bot, scripts

    results = []

    def expect(name: str, mutate, needle: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, bot, scripts = build_copy(Path(tmp))
            mutate(root, bot, scripts)
            _, fails = run(root, bot, scripts)
            hit = [f for f in fails if needle in f]
            results.append((name, bool(hit), fails[0] if not hit and fails else (hit[0] if hit else "ни одного провала")))

    def clean(root, bot, scripts):
        return

    def wrong_lang(root, bot, scripts):
        p = root / "ru/index.html"
        p.write_text(p.read_text(encoding="utf-8").replace("start=src_landing_ru", "start=src_landing_es"),
                     encoding="utf-8")

    def unknown_pos(root, bot, scripts):
        p = root / "es/index.html"
        p.write_text(p.read_text(encoding="utf-8").replace("start=src_landing_es_sticky",
                                                           "start=src_landing_es_footer"), encoding="utf-8")

    def bare_old(root, bot, scripts):
        p = root / "pt/index.html"
        p.write_text(p.read_text(encoding="utf-8").replace('start=src_landing_pt_shots"',
                                                           'start=src_landing"'), encoding="utf-8")

    def llms_collide(root, bot, scripts):
        p = root / "llms.txt"
        p.write_text(p.read_text(encoding="utf-8").replace("start=src_llms", "start=src_landing_en"),
                     encoding="utf-8")

    def bot_drift(root, bot, scripts):
        p = bot / "handlers.py"
        p.write_text(p.read_text(encoding="utf-8").replace("band|shots|sticky", "band|shots"),
                     encoding="utf-8")

    def report_drift(root, bot, scripts):
        p = scripts / "source_stats.py"
        p.write_text(p.read_text(encoding="utf-8").replace("(band|shots|sticky)", "(band|sticky)"),
                     encoding="utf-8")

    def twin_split(root, bot, scripts):
        p = root / "hi/index.html.md"
        p.write_text(p.read_text(encoding="utf-8").replace("start=src_llms", "start=src_md_hi"),
                     encoding="utf-8")

    def bot_learns_md(root, bot, scripts):
        # Бот научился токену двойника, а двойники остались без языка: разрыв закрыт
        # наполовину, и прибор обязан потребовать язык в метке двойника.
        p = bot / "handlers.py"
        p.write_text(p.read_text(encoding="utf-8").replace("band|shots|sticky", "band|shots|sticky|md"),
                     encoding="utf-8")

    print("== контроль прибора: копия дерева и копия чужого кода ==")
    expect("копия без правок", clean, "")
    expect("чужой язык в метке", wrong_lang, "язык")
    expect("неизвестная позиция", unknown_pos, "не разбирает")
    expect("старая метка src_landing", bare_old, "старая метка")
    expect("llms.txt слит со страницей", llms_collide, "llms.txt")
    expect("бот сузил грамматику", bot_drift, "грамматика")
    expect("отчёт сузил грамматику", report_drift, "грамматика")
    expect("двойник сломал единство метки", twin_split, "двойники")
    expect("бот научился _md, двойники без языка", bot_learns_md, "двойник")

    bad = 0
    for name, ok, detail in results:
        if name == "копия без правок":
            if ok:
                print(f"  FAIL {name}: мутация без правок обязана быть зелёной, а красна: {detail}")
                bad += 1
            else:
                print(f"  ok   {name}: зелёная")
            continue
        if ok:
            print(f"  ok   {name}: поймано — {detail}")
        else:
            print(f"  FAIL {name}: НЕ поймано ({detail})")
            bad += 1
    caught = len(results) - 1
    print(f"мутантов: {caught}  поймано: {caught - bad + (1 if bad and results[0][1] else 0)}")
    print("ALL PASS" if bad == 0 else f"ПРОВАЛОВ: {bad}")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", action="store_true", help="мутанты: прибор обязан поймать каждый класс")
    args = ap.parse_args()
    if args.control:
        return control()

    checks, fails = run(ROOT, BOT, BOT_SCRIPTS)
    print(f"бот: {BOT}")
    print(f"страниц: {len(LANGS)}  проверок: {len(checks)}  провалов: {len(fails)}")
    for name, ok, detail in checks:
        if not ok:
            print(f"  FAIL {name}" + (f" — {detail}" if detail else ""))
    if fails:
        return 1
    print("разрыв ИИ-слоя назван: девять двойников несут src_llms без языка "
          "(бот не знает токена двойника) — закрывается правкой бота, не страницы")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
