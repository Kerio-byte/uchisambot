#!/usr/bin/env python3
"""check-lang-fonts.py — шрифты переключателя языка сверены с НАЗВАНИЯМИ языков.

Повод (01.11.2026, двадцать четвёртый блок). Переключатель показывает девять названий
своими письменностями: «Русский», «Українська», «हिन्दी», «Tiếng Việt». Полные сабсеты
по письменностям тянуть ради девяти слов — 127–141 КБ, поэтому с 22.10 рядом лежат три
мини-шрифта (`fonts/langs-*.woff2`), собранные ровно под эти слова, с УЗКИМ
`unicode-range`. Реестр — `tools/lang-fonts.json`, генератор — `tools/make-lang-fonts.py`,
вставка в страницы — `tools/build.py`.

Что было не проверено. `build.py` в комментарии (строка 189) обещает: «Шаблон объявляет
их литералами — свип сверяет шаблон с этим реестром». Свип не сверял: ни один прибор в
`tools/check-*.py` не читает `lang-fonts.json` и не знает семейства `UchiSam Langs`.
Проверка жила только в голове генератора, который печатает `missing=` при пересборке, —
а пересборку никто не делает: шрифты лежат в git как ассеты.

Почему это дефект, а не пробел в отчётности. Переименуй язык в `LABELS` (स्क्रिप्ट:
«हिन्दी» → «हिंदी», «Tiếng Việt» → «Tiếng Việt Nam») и не пересобери шрифты — на
страницах ДРУГИХ языков новая буква не попадает ни в один `unicode-range`, браузер
берёт её из системного шрифта, и одно слово в переключателе рисуется чужой гарнитурой.
Это ровно тот дефект, который 22.10 чинили на 404 («हिन्दी» без шрифта). Второй класс:
`range` в реестре называет кодпойнт, которого в файле нет (пересобрали шрифт, забыли
реестр) — браузер отдаёт этот символ объявленному лицу и получает пустой прямоугольник.
Обе поломки выглядят как «нормально, просто шрифт другой».

Что проверяется (только чтение; `build.py` разбирается как текст, не импортируется —
импорт запускает сборку)

1. Реестр полон: три мини-сабсета (cyrillic, vietnamese, devanagari), у каждого
   file/range/names/bytes/sha256/source.
2. Файлы на диске: существуют, размер и sha256 совпадают с реестром (сборка сверяет
   только размер — правка байтов внутри файла того же размера проходила молча).
3. Девять названий из `LABELS` против покрытия: на КАЖДОЙ из девяти страниц и на 404
   каждый символ каждого названия попадает в `unicode-range` хотя бы одного лица,
   объявленного этой страницей. Иначе символ рисует системный шрифт.
4. Реестр не отстал от названий: набор кодпойнтов в `names` равен набору кодпойнтов
   названий, отнесённых к этой письменности. Переименовали язык — красное с буквой.
5. `range` точен: ровно кодпойнты `names` (без пробела), без фантомов и без пропусков.
   Фантомный кодпойнт «крадёт» символ у текста страницы и отдаёт его лицу, где глифа нет.
6. Вставка в собранные страницы: у каждого лица `font-weight:200 800` (Chrome выбирает
   лицо внутри семейства по дескрипторам и только потом по диапазону — разный вес ломает
   выбор), `font-display:swap`, адрес файла из реестра, диапазон дословно из реестра.
7. Правило веса: мини-сабсет СВОЕЙ письменности на своей странице не объявляется
   (там уже грузится полный текст), на 404 объявлены все три.

Контроль — семь мутантов на копии дерева, каждый обязан покраснеть своим сообщением.
`--deep` дополнительно читает cmap файлов, если в питоне есть fontTools (в кроне его нет:
логика 3–5 ловит отсутствующий глиф и без cmap, потому что генератор пишет `range` по cmap).
"""
import argparse
import ast
import hashlib
import json
import re
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = Path("tools/lang-fonts.json")
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
FAMILY = "UchiSam Langs"
SCRIPTS = ["cyrillic", "vietnamese", "devanagari"]


# --- разбор генератора без импорта -------------------------------------------

def read_consts(root: Path) -> dict:
    """LABELS / FONT_SUBSETS / OWN_SCRIPT из build.py как данные, без запуска сборки."""
    src = (root / "tools" / "build.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    want = {"LABELS", "FONT_SUBSETS", "OWN_SCRIPT"}
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in want:
                out[target.id] = ast.literal_eval(node.value)
    missing = want - set(out)
    if missing:
        raise SystemExit(f"build.py: не нашёл {sorted(missing)} — разбор констант устарел")
    return out


def page_files(root: Path) -> dict:
    """lang -> файл страницы (en в корне, остальные в своих папках)."""
    files = {}
    for lang in LANGS:
        p = root / ("index.html" if lang == "en" else f"{lang}/index.html")
        files[lang] = p
    files["404"] = root / "404.html"
    return files


# --- unicode-range ------------------------------------------------------------

def parse_range(text: str) -> set:
    cps = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"U\+([0-9A-Fa-f]+)(?:-([0-9A-Fa-f]+))?", part)
        if not m:
            raise ValueError(f"битый unicode-range: {part!r}")
        lo = int(m.group(1), 16)
        hi = int(m.group(2), 16) if m.group(2) else lo
        cps |= set(range(lo, hi + 1))
    return cps


def script_of(ch: str, ranges: dict) -> str:
    """Письменность символа: по имени в Unicode, а не по диапазонам (иначе круг)."""
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return "unknown"
    if name.startswith("CYRILLIC"):
        return "cyrillic"
    if name.startswith("DEVANAGARI"):
        return "devanagari"
    if "LATIN" in name:
        # вьетнамский — латиница с диакритикой вне ASCII; базовая латиница названий
        # («Tiếng») рисуется Manrope, поэтому письменностью считаем только надстрочные
        return "vietnamese" if ord(ch) > 0xFF else "latin"
    return "other"


# --- лица собранной страницы --------------------------------------------------

FACE_RE = re.compile(
    r"@font-face\{font-family:'(?P<fam>[^']+)';font-style:(?P<style>[^;]+);"
    r"font-weight:(?P<weight>[^;]+);font-display:(?P<display>[^;]+);"
    r"src:url\(\"(?P<url>[^\"]+)\"\) format\('woff2'\);unicode-range:(?P<range>[^}]+)\}")


def faces_of(html: str) -> list:
    return [m.groupdict() for m in FACE_RE.finditer(html)]


# --- проверки -----------------------------------------------------------------

def run(root: Path) -> tuple:
    checks = []
    fails = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        if not ok:
            fails.append((name, detail))

    reg_path = root / REGISTRY
    if not reg_path.is_file():
        check("реестр на месте", False, str(reg_path))
        return checks, fails
    reg = json.loads(reg_path.read_text(encoding="utf-8"))

    check("реестр: три мини-сабсета", sorted(reg) == sorted(SCRIPTS),
          f"в реестре {sorted(reg)}")
    for key in SCRIPTS:
        v = reg.get(key) or {}
        for field in ("file", "range", "names", "bytes", "sha256", "source"):
            check(f"{key}: поле {field}", field in v, "нет поля")
        if not v.get("file"):
            continue
        f = root / v["file"]
        check(f"{key}: файл существует", f.is_file(), v.get("file", ""))
        if not f.is_file():
            continue
        data = f.read_bytes()
        check(f"{key}: размер = реестр", len(data) == v["bytes"],
              f"файл {len(data)}, реестр {v['bytes']}")
        check(f"{key}: sha256 = реестр", hashlib.sha256(data).hexdigest() == v["sha256"],
              "содержимое файла разошлось с реестром при том же размере")

    consts = read_consts(root)
    labels = consts["LABELS"]
    subsets = dict(consts["FONT_SUBSETS"])
    own = consts["OWN_SCRIPT"]
    check("LABELS: девять языков", sorted(labels) == sorted(LANGS), f"{sorted(labels)}")

    # 3–5: названия против диапазонов
    micro = {}
    for key in SCRIPTS:
        v = reg.get(key) or {}
        try:
            micro[key] = parse_range(v.get("range", ""))
        except ValueError as e:
            check(f"{key}: range разбирается", False, str(e))
            micro[key] = set()
        else:
            check(f"{key}: range разбирается", True)

    latin_cps = set()
    for name in ("latin", "latin-ext"):
        try:
            latin_cps |= parse_range(subsets.get(name, ""))
        except ValueError:
            pass

    for key in SCRIPTS:
        names = (reg.get(key) or {}).get("names", "")
        # мини-лицо объявляет ровно те символы названий, которых НЕТ в латинском лице:
        # латиница названия («Tiếng») приходит из Manrope, и объявлять её здесь — значит
        # отбирать символы у текста страницы ради лица, где их нет.
        want = {ord(ch) for ch in names if ch != " " and ord(ch) not in latin_cps}
        check(f"{key}: range = кодпойнты names", micro[key] == want,
              "фантом: " + ", ".join(f"U+{c:04X}" for c in sorted(micro[key] - want)) if micro[key] - want
              else "пропуск: " + ", ".join(f"U+{c:04X}" for c in sorted(want - micro[key])))
        # отнесение названий к письменности — по Unicode, независимо от диапазонов
        expected = "".join(ch for ch in "".join(labels.values())
                           if ch != " " and script_of(ch, micro) == key
                           and ord(ch) not in latin_cps)
        all_label_chars = {ch for ch in "".join(labels.values()) if ch != " "}
        check(f"{key}: в names нет буквы, которой нет в названиях",
              set(names) <= all_label_chars,
              f"лишние: {sorted(set(names) - all_label_chars)}")
        check(f"{key}: names собраны из LABELS",
              {ch for ch in names if ord(ch) not in latin_cps} == set(expected),
              f"в реестре {sorted({ch for ch in names if ord(ch) not in latin_cps})}, "
              f"из LABELS {sorted(set(expected))}")

    pages = page_files(root)
    built = {}
    for tag, p in pages.items():
        check(f"страница {tag} существует", p.is_file(), str(p))
        if p.is_file():
            built[tag] = p.read_text(encoding="utf-8")

    # 3: покрытие каждого символа названия на каждой странице
    for tag, html in built.items():
        lang = None if tag == "404" else tag
        declared = []
        for face in faces_of(html):
            try:
                declared.append((face, parse_range(face["range"])))
            except ValueError as e:
                check(f"{tag}: range лица разбирается", False, f"{face['fam']}: {e}")
        covered = set()
        for _, cps in declared:
            covered |= cps
        for lkey, text in labels.items():
            for ch in text:
                if ch == " ":
                    continue
                check(f"{tag}: «{text}» — {ch}",
                      ord(ch) in covered,
                      f"U+{ord(ch):04X} {unicodedata.name(ch, '?')} не входит ни в один "
                      f"unicode-range этой страницы — символ нарисует системный шрифт")
        # 7: вес лица покрывает веса, которыми страница реально пишет
        used = {400} | {int(w) for w in re.findall(
            r"font-weight:\s*(\d{3})", re.sub(r"@font-face\{[^}]*\}", "", html))}
        micro_faces = [f for f in faces_of(html) if f["fam"] == FAMILY]
        full_faces = [f for f in faces_of(html) if f["fam"] != FAMILY]
        for f in faces_of(html):
            lo, hi = _weight_span(f["weight"])
            check(f"{tag}: вес {f['weight']} покрывает {min(used)}–{max(used)}",
                  lo is not None and lo <= min(used) and hi >= max(used),
                  f"лицо {f['fam']} объявлено {f['weight']}, а страница пишет "
                  f"{sorted(used)} — непокрытый вес уйдёт в системный шрифт")
            check(f"{tag}: display swap", f["display"] == "swap", f["display"])
        for f in micro_faces:
            check(f"{tag}: мини-лицо переключателя {f['weight']}",
                  f["weight"].replace(" ", "") == "200800",
                  "у лиц одного семейства вес обязан совпадать: Chrome выбирает лицо по "
                  "дескрипторам и только потом по диапазону")
        if lang is not None:
            mine = own.get(lang)
            for key in SCRIPTS:
                f = _face_for(micro_faces, reg.get(key, {}).get("file", ""))
                if key == mine:
                    check(f"{tag}: микро-лицо своей письменности не объявлено", f is None,
                          "своя письменность грузится полным сабсетом — мини-лицо лишние килобайты")
                else:
                    check(f"{tag}: лицо {key} объявлено", f is not None, "нет лица переключателя")
                    if f:
                        check(f"{tag}: {key} range = реестр",
                              f["range"].strip() == reg[key]["range"].strip(), "диапазон разошёлся")
                        check(f"{tag}: {key} адрес", reg[key]["file"] in f["url"], f["url"])
        else:  # 404: все три, полных сабсетов письменностей нет
            for key in SCRIPTS:
                check(f"404: лицо {key} объявлено",
                      _face_for(micro_faces, reg.get(key, {}).get("file", "")) is not None, "нет лица")
            check("404: полных сабсетов письменностей нет",
                  not [f for f in full_faces if "cyrillic" in f["url"] or "vietnamese" in f["url"]],
                  "404 снова тянет полные сабсеты")

    return checks, fails


def _in_latin(ch: str, subsets: dict) -> bool:
    try:
        return ord(ch) in parse_range(subsets.get("latin", ""))
    except ValueError:
        return False


def _face_for(faces: list, url: str):
    for f in faces:
        if url and url in f["url"]:
            return f
    return None


def _weight_span(text: str):
    nums = re.findall(r"\d+", text)
    if not nums:
        return None, None
    return int(nums[0]), int(nums[-1])


# --- контроль -----------------------------------------------------------------

def _copy_tree(dst: Path) -> None:
    shutil.copy2(ROOT / "tools" / "build.py", dst / "tools" / "build.py")
    shutil.copy2(ROOT / REGISTRY, dst / REGISTRY)
    for p in (ROOT / "fonts").glob("langs-*.woff2"):
        shutil.copy2(p, dst / "fonts" / p.name)
    for tag, p in page_files(ROOT).items():
        rel = p.relative_to(ROOT)
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst / rel)


def control() -> int:
    results = []

    def expect(name, mutate, needle=""):
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td)
            (dst / "tools").mkdir()
            (dst / "fonts").mkdir()
            _copy_tree(dst)
            mutate(dst)
            checks, fails = run(dst)
            red = [f for f in fails if needle in (f[0] + " " + f[1])]
            results.append((name, bool(red), red[0][1][:140] if red else "зелено"))

    expect("копия без правок", lambda d: None)

    def rename_lang(d):
        p = d / "tools" / "build.py"
        s = p.read_text(encoding="utf-8")
        p.write_text(s.replace('"ru": "Русский"', '"ru": "Русский язык"'), encoding="utf-8")
    expect("название языка переименовано без пересборки шрифтов", rename_lang, "язык")

    def drop_cp(d):
        p = d / REGISTRY
        reg = json.loads(p.read_text(encoding="utf-8"))
        reg["cyrillic"]["range"] = ",".join(
            x for x in reg["cyrillic"]["range"].split(",") if x != "U+0457")
        p.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    expect("из диапазона выпал кодпойнт «ї»", drop_cp, "пропуск")

    def phantom(d):
        p = d / REGISTRY
        reg = json.loads(p.read_text(encoding="utf-8"))
        reg["vietnamese"]["range"] += ",U+1EC0"
        p.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    expect("диапазон объявил фантомный кодпойнт", phantom, "фантом")

    def bad_sha(d):
        p = d / REGISTRY
        reg = json.loads(p.read_text(encoding="utf-8"))
        reg["devanagari"]["sha256"] = "0" * 64
        p.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    expect("отпечаток файла разошёлся с реестром", bad_sha, "sha256")

    def stale_names(d):
        p = d / REGISTRY
        reg = json.loads(p.read_text(encoding="utf-8"))
        reg["cyrillic"]["names"] = "РусскийУкраїнськаП"
        reg["cyrillic"]["range"] += ",U+041F"
        p.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    expect("реестр имён отстал от LABELS", stale_names, "names собраны")

    def wrong_weight(d):
        p = d / "ru" / "index.html"
        p.write_text(p.read_text(encoding="utf-8").replace("font-weight:200 800", "font-weight:400 800",
                                                          1), encoding="utf-8")
    expect("у лица разный вес", wrong_weight, "вес")

    def own_face(d):
        p = d / "ru" / "index.html"
        s = p.read_text(encoding="utf-8")
        reg = json.loads((d / REGISTRY).read_text(encoding="utf-8"))
        v = reg["cyrillic"]
        face = (f"@font-face{{font-family:'{FAMILY}';font-style:normal;font-weight:200 800;"
                f"font-display:swap;src:url(\"{v['file']}\") format('woff2');"
                f"unicode-range:{v['range']}}}")
        p.write_text(s.replace("</style>", face + "</style>", 1), encoding="utf-8")
    expect("мини-лицо своей письменности вернулось на свою страницу", own_face, "своей письменности")

    bad = 0
    for name, ok, detail in results:
        if name == "копия без правок":
            if ok:
                print(f"  FAIL {name}: копия без правок обязана быть зелёной, а красна: {detail}")
                bad += 1
            else:
                print(f"  ok   {name}: зелёная")
            continue
        if ok:
            print(f"  ok   {name}: поймано — {detail}")
        else:
            print(f"  FAIL {name}: НЕ поймано ({detail})")
            bad += 1
    total = len(results) - 1
    caught = total - bad
    print(f"мутантов: {total}  поймал {caught} из {total}")
    print("ALL PASS" if bad == 0 else f"ПРОВАЛОВ: {bad}")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="шрифты переключателя языка сверены с названиями")
    ap.add_argument("--control", action="store_true", help="семь мутантов: прибор обязан поймать каждый")
    args = ap.parse_args()
    if args.control:
        return control()
    checks, fails = run(ROOT)
    print(f"проверок: {len(checks)}  провалов: {len(fails)}")
    for name, detail in fails:
        print(f"  FAIL {name}" + (f" — {detail}" if detail else ""))
    if fails:
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
