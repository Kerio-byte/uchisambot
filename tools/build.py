#!/usr/bin/env python3
"""Генератор языковых страниц лендинга UchiSamBot (только статические файлы, без рантайма).

Источник:  index-src.html — страница с разметкой data-i18n (EN-тексты внутри, как база)
Словари:   src/locales/*.json (en, ru + es, pt, hi, id, tr, vi, uk)
Выход:     index.html (EN, корень) + <lang>/index.html для 8 языков (md-двойники
           index.html.md рядом с каждой страницей), md-двойники legal-страниц
           (privacy.html.md / terms.html.md — конвертация main-контента их html),
           404.html (одна страница на весь сайт), sitemap.xml + llms.txt
Запуск:    python3 tools/build.py     (правки контента: меняешь словарь → пересборка)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / "src" / "locales"
SITE_FILE = ROOT / "tools" / "site.json"


def load_site() -> tuple:
    """Единственный источник адреса сайта (22.10.2026).

    До этого адрес жил в трёх местах: литерал здесь, литералы в index-src.html
    (canonical, og:url, JSON-LD, redirect формы) и руками написанные privacy.html /
    terms.html / robots.txt. При переезде на свой домен build.py переписывал canonical
    и og:url регулярками, а строка redirect формы сравнивалась с литералом шаблона —
    совпадения не было, и посетитель после отправки формы уезжал на СТАРЫЙ адрес.
    Теперь адрес один: tools/site.json. Шаблон несёт токен {{BASE}}, руками
    написанные файлы нормализует сборка по списку previous (старые адреса сайта).
    """
    try:
        data = json.loads(SITE_FILE.read_text(encoding="utf-8"))
    except OSError as e:
        raise SystemExit(f"нет {SITE_FILE}: адрес сайта обязан быть в tools/site.json ({e})")
    base = str(data.get("base", ""))
    if not (base.startswith("https://") and base.endswith("/")):
        raise SystemExit(f"site.json: base должен быть https-адресом со слэшем на конце, получено {base!r}")
    prev = []
    for p in data.get("previous", []):
        p = str(p)
        if not (p.startswith("https://") and p.endswith("/")):
            raise SystemExit(f"site.json: previous-адрес должен быть https и со слэшем: {p!r}")
        if p != base:
            prev.append(p)
    return base, prev


BASE, PREV_BASES = load_site()
# Файлы, которые пишутся руками и потому не могут получить адрес из шаблона:
# их нормализует normalize_hand_written() при каждой сборке.
HAND_WRITTEN = ("privacy.html", "terms.html", "robots.txt")
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
PRICES_FILE = ROOT / "tools" / "prices.json"
# Ссылка на бота для ИИ-слоя (llms.txt + md-двойники страниц). Правило владельца:
# каждая ссылка на бота несёт метку источника (реестр меток ведётся вне этого репозитория);
# без метки переход из ИИ-канала падает в статистике в «(без метки)» и неразличим по площадкам.
BOT_LLMS = "https://t.me/UchiSamBot?start=src_llms"


def load_prices() -> dict:
    """Единственный источник цен (21.10.2026).

    До этого числа числа JSON-LD были литералами здесь, а видимые цены — строками в 9
    словарях: правка одной стороны оставляла вторую врать молча (поисковик показывал старую
    цену, человек — новую, и ни одна проверка этого не видела). Теперь JSON-LD собирается
    из этого файла, а свип сверяет с ним тексты всех языков.
    """
    p = json.loads(PRICES_FILE.read_text(encoding="utf-8"))
    assert isinstance(p.get("free_breakdowns"), int) and p["free_breakdowns"] >= 0, "prices: free_breakdowns"
    assert isinstance(p.get("single"), int) and p["single"] > 0, "prices: single"
    for name in ("pack5", "pack15"):
        pack = p.get(name) or {}
        assert isinstance(pack.get("size"), int) and pack["size"] > 1, f"prices: {name}.size"
        assert isinstance(pack.get("price"), int) and pack["price"] > 0, f"prices: {name}.price"
        assert pack["price"] < p["single"] * pack["size"], f"prices: {name} не выгоднее поштучной покупки"
    assert isinstance(p.get("currency"), str) and p["currency"], "prices: currency"
    return p


PRICES = load_prices()
SUBJECTS_FILE = ROOT / "tools" / "subjects.json"


def load_subjects() -> dict:
    """Единственный источник списка предметов (22.10.2026).

    До этого числа список жил только в девяти словарях (чипы subj.c1…c5 и строка q2a) и
    повторялся словами в обеих половинах terms.html. При первой генерации словарей (15.10)
    в восемь языков попало название языка самой страницы вместо предмета «English» (ru
    «Русский язык», es «Español», tr «Türkçe»), поэтому неделю страницы обещали не тот
    предмет, а русская половина Terms противоречила английской — и свип был зелёным,
    потому что сверял страницу с нею же. Теперь канон здесь; проверка ниже валит сборку,
    если чипы хоть одного языка разошлись.
    """
    data = json.loads(SUBJECTS_FILE.read_text(encoding="utf-8"))
    subjects = data.get("subjects") or {}
    assert set(subjects) == set(LANGS), f"subjects: набор языков {sorted(subjects)}"
    for lang, items in subjects.items():
        assert (isinstance(items, list) and len(items) == 5
                and all(isinstance(x, str) and x.strip() for x in items)), f"subjects: {lang}"
    return subjects


SUBJECTS = load_subjects()


def validate_subjects(dicts: dict) -> None:
    """Чипы страницы обязаны совпадать с каноном слово в слово (22.10.2026).

    Проверка намеренно жёсткая: список предметов — обещание продукта, одинаковое на всех
    девяти страницах. Правка чипа «по смыслу» (например, «English» → «Русский язык») — это
    уже другое обещание, и она должна идти через tools/subjects.json, а не мимо него.
    """
    problems = []
    for lang in LANGS:
        want = SUBJECTS[lang]
        got = [str(dicts[lang].get(f"subj.c{i}", "")).strip() for i in range(1, 6)]
        if got != want:
            diff = [f"subj.c{i + 1}: {g!r} != {w!r}" for i, (g, w) in enumerate(zip(got, want)) if g != w]
            problems.append(f"{lang}: " + "; ".join(diff))
    if problems:
        raise SystemExit("СПИСОК ПРЕДМЕТОВ РАСХОДИТСЯ с tools/subjects.json "
                         "(правь канон и словари вместе):\n  " + "\n  ".join(problems))


# Названия языков — БЕЗ флагов-эмодзи (21.10.2026): Windows не рисует региональные
# флаги (вместо них «GB»/«RU»-квадраты), а флаг — это страна, не язык (🇮🇳 для хинди,
# 🇧🇷 для португальского, 🇬🇧 для английского читаются как ошибка на мировом рынке).
# Страница 404 давно использует чистые названия — теперь один стиль на всём сайте.
LABELS = {
    "en": "English", "ru": "Русский", "es": "Español", "pt": "Português",
    "hi": "हिन्दी", "id": "Bahasa Indonesia", "tr": "Türkçe", "vi": "Tiếng Việt",
    "uk": "Українська",
}
# privacy.html и terms.html существуют только на английском и русском (решение совета 15.10).
# На остальных 7 языках подпись ссылки честно говорит, на каком языке откроется документ:
# иначе /hi/ обещает «गोपनीयता नीति पढ़ें», а показывает английский текст.
LEGAL_KEYS = {"parents.link", "foot.privacy", "foot.terms", "contact.privacy"}
LEGAL_SUFFIX = " (EN/RU)"


def legal_label(val, key: str, lang: str):
    """Подпись ссылки на юридический документ: добавляет язык, если перевода нет."""
    if val is not None and key in LEGAL_KEYS and lang not in ("en", "ru"):
        return val + LEGAL_SUFFIX
    return val


# Иконка «глобус» вместо эмодзи 🌐: эмодзи рисуется по-разному в каждой ОС (а на части
# систем подменяется цветным шрифтом), SVG наследует цвет текста и выглядит одинаково везде.
GLOBE_SVG = (
    '<svg class="globe" viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false">'
    '<circle cx="8" cy="8" r="6.4" fill="none" stroke="currentColor" stroke-width="1.4"/>'
    '<ellipse cx="8" cy="8" rx="2.9" ry="6.4" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    '<path d="M1.9 5.9h12.2M1.9 10.1h12.2" fill="none" stroke="currentColor" stroke-width="1.2"/>'
    '</svg>'
)

OG_LOCALE = {"en": "en_US", "ru": "ru_RU", "es": "es_ES", "pt": "pt_BR",
             "hi": "hi_IN", "id": "id_ID", "tr": "tr_TR", "vi": "vi_VN", "uk": "uk_UA"}
NO_TRANSLATE = ["UchiSamBot", "Telegram Stars", "Stars", "/lang", "you@example.com"]
# Подпись видео для скринридеров жила ЗДЕСЬ, таблицей на девять языков внутри генератора:
# её не видел ни один словарный гейт, поэтому «бот решает задачу по шагам» спокойно осталось
# в шести языках после того, как страница от этой фразы отказалась (24.10.2026). Теперь это
# обычный ключ словаря demo.alt, а шаблон несёт data-i18n-attr="aria-label:demo.alt".
# Бейджи (герой + футер): фрагмент src -> имя площадки. Альт = шаблон словаря
# badge.alt («отмечен на {name}»), подпись группы бейджей = badge.group.
# До 16.10 альты были захардкожены по-английски и лежали ОДИНАКОВО на всех 9
# страницах (утечка чужого языка для скринридеров); см. блок «бейджи».
FONT_SUBSETS = [
    ("cyrillic-ext", "U+0460-052F,U+1C80-1C8A,U+20B4,U+2DE0-2DFF,U+A640-A69F,U+FE2E-FE2F"),
    ("cyrillic", "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116"),
    ("vietnamese", "U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,"
                   "U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB"),
    ("latin-ext", "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,"
                  "U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C4,"
                  "U+2113,U+2C60-2C7F,U+A720-A7FF"),
    ("latin", "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,"
              "U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
]
# Мини-сабсеты переключателя языка: реестр генерирует tools/make-lang-fonts.py
# (там же отпечатки файлов). Шаблон объявляет их литералами — свип сверяет шаблон
# с этим реестром, чтобы объявленный unicode-range не разошёлся с содержимым файла.
LANG_FONTS_FILE = ROOT / "tools" / "lang-fonts.json"
try:
    LANG_FONTS = json.loads(LANG_FONTS_FILE.read_text(encoding="utf-8"))
except (OSError, ValueError) as e:
    raise SystemExit(f"нет/битый {LANG_FONTS_FILE}: мини-сабсеты переключателя без реестра ({e})")
for _k, _v in LANG_FONTS.items():
    _f = ROOT / _v["file"]
    if not _f.is_file():
        raise SystemExit(f"lang-fonts.json: {_v['file']} не существует — запусти tools/make-lang-fonts.py")
    if _f.stat().st_size != _v["bytes"]:
        raise SystemExit(f"lang-fonts.json: размер {_v['file']} разошёлся с реестром")
# Сабсет деванагари под текст сайта (26.10.2026). Реестр генерирует tools/subset-deva.py.
# Зачем: полный Noto Sans Devanagari — 121 192 Б — грузился на каждом заходе на /hi/
# (19 % веса первого экрана), хотя страница использует 57 кодпойнтов из ~660. Сабсет
# с тем же рисунком букв и всеми GSUB-фичами весит 70 КБ. Сборка читает реестр и
# падает, если тексту страницы нужен кодпойнт, которого в сабсете нет.
DEVA_FILE = ROOT / "tools" / "deva-subset.json"
try:
    DEVA = json.loads(DEVA_FILE.read_text(encoding="utf-8"))
except (OSError, ValueError) as e:
    raise SystemExit(f"нет/битый {DEVA_FILE}: сабсет деванагари без реестра ({e})")
_deva_f = ROOT / DEVA["file"]
if not _deva_f.is_file():
    raise SystemExit(f"deva-subset.json: {DEVA['file']} не существует — запусти tools/subset-deva.py")
if _deva_f.stat().st_size != DEVA["bytes"] or hashlib.sha256(_deva_f.read_bytes()).hexdigest() != DEVA["sha256"]:
    raise SystemExit(f"deva-subset.json: {DEVA['file']} разошёлся с реестром — пересобери tools/subset-deva.py")
if hashlib.sha256((ROOT / DEVA["source"]).read_bytes()).hexdigest() != DEVA["source_sha256"]:
    raise SystemExit("deva-subset.json: исходный шрифт изменился — пересобери tools/subset-deva.py")
DEVA_CHARS = DEVA["charters"]
# Письменность каждого языка: полный сабсет этой письменности объявляется только
# на его странице, мини-сабсет переключателя — наоборот, на всех ОСТАЛЬНЫХ.
OWN_SCRIPT = {"ru": "cyrillic", "uk": "cyrillic", "vi": "vietnamese", "hi": "devanagari"}
FULL_FACES = {
    "ru": ("cyrillic-ext", "cyrillic"),
    "uk": ("cyrillic-ext", "cyrillic"),
    "vi": ("vietnamese",),
    "hi": (),
}
LANGS_FAMILY = "UchiSam Langs"
NOTO_RANGE = ("U+0900-097F,U+1CD0-1CF4,U+1CF7-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,"
              "U+25CC,U+A830-A839,U+A8E0-A8FF,U+11B00-11B0A")
BADGE_ALTS = [
    # 23.10.2026: все значки лежат у нас (img/badges/), чужих адресов на страницах больше нет.
    # Старые адреса оставлены в образцах как второй вариант: так сборка понимает и архивную
    # страницу из git, и новый локальный файл, а не падает «совпадений 0» на пустом месте.
    # 25.10.2026: LaunchIgniter из списка убран вместе со значком в герое — площадка удалила
    # нашу страницу (200 + «Product Not Found»), ссылка вела в пустоту.
    (r"(?:https://fazier\.com/api/v1/|(?:\.\./)?img/badges/fazier\.svg)", "Fazier"),
    (r"(?:https://statics\.startupbase\.io/site/badges/|(?:\.\./)?img/badges/startupbase\.svg)", "StartupBase"),
    (r"(?:https://showmebest\.ai/badge/|(?:\.\./)?img/badges/showmebest\.webp)", "ShowMeBestAI"),
    (r"(?:https://lift-off\.sh/images/badges/badgeLaunched|(?:\.\./)?img/badges/liftoff-launched\.webp)", "LiftOff"),
    # 22.10.2026: значок Startup Fame отдаётся с нашего домена (ORB резал горячую ссылку),
    # поэтому здесь два варианта src: свой файл и старый чужой адрес.
    (r"(?:https://startupfa\.me/badge\?|(?:\.\./)?img/badges/startupfa\.svg)", "Startup Fame"),
    # 25.10.2026: OpenHunts Club убран вместе со значком — площадка не держит нашей страницы:
    # её карта сайта перечисляет 3 837 проектов, нашего среди них нет, а прямой адрес отвечает
    # 200 страницей «Project Not Found». Значок вёл на главную, и проверить обещание было нечем.
    (r"(?:https://auraplusplus\.com/images/badges/|(?:\.\./)?img/badges/auraplusplus\.svg)", "Aura++"),
]


def url_for(lang: str) -> str:
    return BASE if lang == "en" else f"{BASE}{lang}/"


# Ключи, у которых текст совпадает с английским НАМЕРЕННО (пример в поле — не перевод).
SAME_AS_EN_OK = {"contact.ph_email"}


def validate_dicts(out: dict) -> None:
    """Словари обязаны быть одинаковыми по набору ключей (21.10.2026).

    Зачем: `rep_i18n` при отсутствии ключа молча оставляет английский текст из
    шаблона — страница уезжает в свет с английской строкой, а сборка зелёная.
    Проверка ловит оба случая: (а) ключ добавили в en и забыли в другом языке,
    (б) в шаблоне новый data-i18n, которого нет ни в одном словаре.
    """
    en = set(out["en"])
    problems = []
    for lang in LANGS[1:]:
        missing = sorted(en - set(out[lang]))
        extra = sorted(set(out[lang]) - en)
        if missing:
            problems.append(f"{lang}: нет ключей {missing[:4]}{' …' if len(missing) > 4 else ''}")
        if extra:
            problems.append(f"{lang}: лишние ключи {extra[:4]}{' …' if len(extra) > 4 else ''}")
    if problems:
        raise SystemExit("СЛОВАРИ РАСХОДЯТСЯ по набору ключей "
                         "(добавь переводы в src/locales/*.json):\n  " + "\n  ".join(problems))
    for lang in LANGS:
        empty = sorted(k for k, v in out[lang].items() if not str(v).strip())
        if empty:
            raise SystemExit(f"{lang}: пустые значения в словаре: {empty}")
    # Мягкий сигнал (не валит сборку): ключ есть, но перевода нет — текст английский.
    for lang in LANGS[1:]:
        same = sorted(k for k in out[lang]
                      if k in out["en"] and out[lang][k] == out["en"][k]
                      and len(str(out[lang][k])) >= 12 and k not in SAME_AS_EN_OK)
        if same:
            print(f"  ВНИМАНИЕ {lang}: английский текст без перевода — {same}")


def load_dicts() -> dict:
    out = {}
    for lang in LANGS:
        out[lang] = json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
        assert len(out[lang]) >= 80, f"{lang}: мало ключей"
    validate_dicts(out)
    return out


def esc_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;")


def esc_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hreflang_block() -> str:
    lines = [f'<link rel="alternate" hreflang="{l}" href="{url_for(l)}">' for l in LANGS]
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}">')
    return "\n".join(lines)


def switcher_html(lang: str, aria: str) -> str:
    """Переключатель языка: реальные ссылки на /xx/, текущий язык — не ссылка.

    lang="" на каждом пункте — WCAG 3.1.2 (скринридер читает «हिन्दी» хинди, а не
    по правилам английского); так же сделана страница 404.
    """
    items = []
    for l in LANGS:
        if l == lang:
            # Текущий язык — span, а не <a href="#">: ссылка «в никуда» ломала клик
            # (прыжок наверх) и врала разметкой о переходе.
            items.append(f'<span class="on" aria-current="page" lang="{l}">{LABELS[l]}</span>')
        else:
            if lang == "en":
                href = "./" if l == "en" else f"{l}/"
            else:
                href = "../" if l == "en" else f"../{l}/"
            items.append(f'<a href="{href}" lang="{l}" hreflang="{l}">{LABELS[l]}</a>')
    return (
        f'<details class="lang-dd"><summary aria-label="{esc_attr(aria)}: {esc_attr(LABELS[lang])}">'
        + GLOBE_SVG + f'<span lang="{lang}">{LABELS[lang]}</span>'
        + '</summary><div class="lang-list">' + "".join(items) + "</div></details>"
    )


def faq_entities(d: dict, lang: str) -> list:
    """FAQ-разметка: вопросы q1..qN с ответами q1a..qNa (сколько есть в словаре)."""
    out, i = [], 1
    while f"q{i}" in d:
        assert f"q{i}a" in d, f"{lang}: нет ответа для вопроса q{i}"
        out.append({"@type": "Question", "name": d[f"q{i}"],
                    "acceptedAnswer": {"@type": "Answer", "text": d[f"q{i}a"]}})
        i += 1
    return out


def jsonld(d: dict, lang: str) -> str:
    graph = [
        {"@type": "Organization", "@id": BASE + "#org", "name": "UchiSamBot",
         "url": BASE, "logo": BASE + "img/logo-512.png", "sameAs": ["https://t.me/UchiSamBot"]},
        {"@type": "WebSite", "@id": BASE + "#website", "url": url_for(lang), "name": "UchiSamBot",
         "inLanguage": lang, "publisher": {"@id": BASE + "#org"}},
        {"@type": "SoftwareApplication", "@id": BASE + "#app", "name": "UchiSamBot (Study Helper)",
         "applicationCategory": "EducationalApplication", "operatingSystem": "Telegram",
         "url": "https://t.me/UchiSamBot", "inLanguage": LANGS,
         "description": d.get("meta.desc", ""),
         "offers": [
             {"@type": "Offer", "name": d["p1t"], "price": "0", "priceCurrency": PRICES["currency"]},
             {"@type": "Offer", "name": d["price.single"], "price": str(PRICES["single"]),
              "priceCurrency": PRICES["currency"]},
             {"@type": "Offer", "name": d["p2t"], "price": str(PRICES["pack5"]["price"]),
              "priceCurrency": PRICES["currency"]},
             {"@type": "Offer", "name": d["p3t"], "price": str(PRICES["pack15"]["price"]),
              "priceCurrency": PRICES["currency"]},
         ]},
        {"@type": "FAQPage", "@id": BASE + "#faq",
         "inLanguage": lang,
         "mainEntity": faq_entities(d, lang)},
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False)


def shot_src(n: str, lang: str) -> str:
    """Картинка языка, если файл есть; иначе — английская."""
    for cand in (f"shot{n}-{lang}.webp", f"shot{n}.webp"):
        if (ROOT / "img" / cand).exists():
            return cand
    return f"shot{n}.webp"


def normalized_hand_written() -> dict:
    """Нормализованный текст руками написанных файлов под текущий BASE — без записи.

    privacy.html / terms.html / robots.txt не генерируются из шаблона, но содержат
    абсолютные адреса сайта: canonical, og:url, og:image, twitter:image, describedby,
    ссылку на md-двойник, сам адрес сайта в тексте политики (EN и RU) и Sitemap в
    robots.txt. Без этого шага переезд на домен оставил бы canonical на старом хосте
    (страница снимает себя с индекса) и карту сайта по старому адресу.

    23.10.2026: раньше функция писала на диск прямо посреди сборки. Режиму --check
    нужно то же самое, но без единой записи, поэтому тексты возвращаются словарём,
    а пишет их main().
    """
    out = {}
    for name in HAND_WRITTEN:
        p = ROOT / name
        text = p.read_text(encoding="utf-8")
        new = text
        for old in PREV_BASES:
            new = new.replace(old, BASE)                                       # https://host/path/
            bare_old = old.split("://", 1)[1].rstrip("/")
            bare_new = BASE.split("://", 1)[1].rstrip("/")
            new = new.replace(bare_old, bare_new)   # host/path без схемы: текст политики «сайт (host/path)»
        left = [o for o in PREV_BASES
                if o in new or o.split("://", 1)[1].rstrip("/") in new]
        if left:
            raise SystemExit(f"{name}: остался старый адрес сайта {left} — уберите руками")
        out[name] = new
    return out


def font_css(lang: str) -> str:
    """CSS-блок шрифтов страницы (22.10.2026): состав зависит от письменности языка.

    Правило (и его проверяет свип):
      * мини-сабсеты переключателя (tools/lang-fonts.json) объявлены всегда, КРОМЕ
        письменности самой страницы — там полный сабсет уже грузится текстом, и
        название текущего языка в шапке берётся из него;
      * полные сабсеты Manrope — только латиница/latin-ext и письменность языка;
      * Noto Sans Devanagari — только /hi/ (118 КБ: другой текст её не требует).
    Так открытие переключателя стоит 4–9 КБ вместо 127–141 КБ, а на 404 (отдельная
    генерация) у «हिन्दी» впервые появляется свой шрифт.
    """
    own = OWN_SCRIPT.get(lang)
    parts = []
    for key, v in LANG_FONTS.items():
        if key == own:
            continue
        parts.append(
            f"@font-face{{font-family:'{LANGS_FAMILY}';font-style:normal;font-weight:200 800;"
            f"font-display:swap;src:url(\"{v['file']}\") format('woff2');"
            f"unicode-range:{v['range']}}}")
    full = set(FULL_FACES.get(lang, ())) | {"latin", "latin-ext"}
    for name, rng in FONT_SUBSETS:
        if name not in full:
            continue
        parts.append(
            f"@font-face{{font-family:'Manrope';font-style:normal;font-weight:200 800;"
            f"font-display:swap;src:url(\"fonts/manrope-{name}.woff2\") format('woff2');"
            f"unicode-range:{rng}}}")
    if lang == "hi":
        # 26.10.2026: не полный Noto (121 192 Б), а сабсет под текст сайта (69 960 Б).
        # Реестр — tools/deva-subset.json, генератор — tools/subset-deva.py. Сборка ниже
        # проверяет, что каждой букве страницы есть глиф в этом файле.
        parts.append(
            f"@font-face{{font-family:'Noto Sans Devanagari';font-style:normal;"
            f"font-weight:400 800;font-display:swap;"
            f"src:url(\"{DEVA['file']}\") format('woff2');"
            f"unicode-range:{NOTO_RANGE}}}")
    return "\n".join(parts)


def bake(src: str, lang: str, dicts: dict) -> str:
    d = dicts[lang]
    # 0) адрес сайта: шаблон несёт токен {{BASE}}, значение — только из tools/site.json
    #    (см. load_site: литерал в шаблоне раньше ломал redirect формы при переезде)
    out = src.replace("{{BASE}}", BASE)
    # 0а) шрифтовой блок: состав зависит от письменности языка (см. font_css)
    assert "{{FONTS}}" in out, "в шаблоне нет маркера {{FONTS}}"
    out = out.replace("{{FONTS}}", font_css(lang))

    # 1) тексты data-i18n и placeholders data-i18n-ph
    def rep_i18n(m: re.Match) -> str:
        key = m.group(2)
        val = legal_label(d.get(key), key, lang)
        tag = re.sub(r'\sdata-i18n="[\w.]+"', "", m.group(1))
        return tag + (esc_text(val) if val is not None else m.group(3)) + m.group(4)

    out = re.sub(
        r'(<[a-z][a-z0-9]*[^>]*\sdata-i18n="([\w.]+)"[^>]*>)(.*?)(</[a-z][a-z0-9]*>)',
        rep_i18n, out, flags=re.S,
    )

    def rep_ph(m: re.Match) -> str:
        key = m.group(2)
        val = d.get(key)
        tag = re.sub(r'\sdata-i18n-ph="[\w.]+"', "", m.group(1))
        if val is None:
            return tag
        if 'placeholder="' in tag:
            return re.sub(r'placeholder="[^"]*"', 'placeholder="' + esc_attr(val) + '"', tag)
        return tag + ' placeholder="' + esc_attr(val) + '"'

    out = re.sub(r'(<(?:input|textarea)[^>]*\sdata-i18n-ph="([\w.]+)"[^>]*>)', rep_ph, out)

    # 1б) подписи в АТРИБУТАХ (aria-label и подобные) — 22.10.2026: у кнопки остановки
    #     демо-видео две подписи (пауза и играть), и обе обязаны быть на языке страницы.
    #     Синтаксис: data-i18n-attr="aria-label:vbtn.pause;data-play-label:vbtn.play".
    #     Текстовый механизм выше такие подписи не видит, а класть их в DOM текстом
    #     нельзя: имя кнопки стало бы из двух строк сразу.
    def rep_attr(m: re.Match) -> str:
        tag = m.group(1) + m.group(3)
        for pair in m.group(2).split(";"):
            if ":" not in pair:
                continue
            attr, key = (x.strip() for x in pair.split(":", 1))
            val = d.get(key)
            if val is None:
                continue
            pat = rf'\s{re.escape(attr)}="[^"]*"'
            if re.search(pat, tag):
                tag = re.sub(pat, f' {attr}="{esc_attr(val)}"', tag, count=1)
            else:
                tag = tag[:-1].rstrip() + f' {attr}="{esc_attr(val)}">'
        return tag

    out = re.sub(r'(<[a-z][a-z0-9]*[^>]*?)\sdata-i18n-attr="([^"]+)"([^>]*>)', rep_attr, out)

    # 2) html lang, title, description
    out = re.sub(r'<html lang="[^"]*"', f'<html lang="{lang}"', out)
    out = re.sub(r"<title>.*?</title>", f"<title>{esc_text(d['meta.title'])}</title>", out, flags=re.S)
    out = re.sub(r'<meta name="description" content="[^"]*"',
                 f'<meta name="description" content="{esc_attr(d["meta.desc"])}"', out)

    # 3) canonical + hreflang + rel-ссылки ИИ-слоя (llms.txt v2): describedby -> llms.txt,
    #    alternate type=text/markdown -> md-двойник страницы (лежит рядом со страницей)
    out = re.sub(r'<link rel="canonical" href="[^"]*">',
                 f'<link rel="canonical" href="{url_for(lang)}">\n' + hreflang_block() + '\n'
                 + f'<link rel="describedby" href="{BASE}llms.txt">\n'
                 + f'<link rel="alternate" type="text/markdown" href="{url_for(lang)}index.html.md">',
                 out)

    # 4) OG / Twitter
    out = re.sub(r'<meta property="og:url" content="[^"]*">',
                 f'<meta property="og:url" content="{url_for(lang)}">', out)
    out = re.sub(r'<meta property="og:title" content="[^"]*">',
                 f'<meta property="og:title" content="{esc_attr(d["meta.title"])}">', out)
    out = re.sub(r'<meta property="og:description" content="[^"]*">',
                 f'<meta property="og:description" content="{esc_attr(d["meta.desc"])}">', out)
    out = re.sub(r'<meta property="og:locale" content="[^"]*">',
                 f'<meta property="og:locale" content="{OG_LOCALE[lang]}">', out)
    # alternates — все ОСТАЛЬНЫЕ языки (ogp.me: массив локалей; до 16.10 было жёстко ru_RU
    # на всех страницах, из-за чего на /ru/ локаль сама себе «альтернатива»)
    alt_lines = "\n".join(f'<meta property="og:locale:alternate" content="{OG_LOCALE[l]}">'
                          for l in LANGS if l != lang)
    out = re.sub(r'<meta property="og:locale:alternate" content="[^"]*">',
                 lambda _m: alt_lines, out)
    out = re.sub(r'<meta name="twitter:title" content="[^"]*">',
                 f'<meta name="twitter:title" content="{esc_attr(d["meta.title"])}">', out)
    out = re.sub(r'<meta name="twitter:description" content="[^"]*">',
                 f'<meta name="twitter:description" content="{esc_attr(d["meta.desc"])}">', out)
    # альты превью-картинки (og/twitter) — по языку (до 16.10 были статичные англ. на всех страницах)
    out = re.sub(r'<meta property="og:image:alt" content="[^"]*">',
                 f'<meta property="og:image:alt" content="{esc_attr(d["meta.title"])}">', out)
    out = re.sub(r'<meta name="twitter:image:alt" content="[^"]*">',
                 f'<meta name="twitter:image:alt" content="{esc_attr(d["meta.title"])}">', out)
    # картинка превью — своя на каждый язык (до 21.10 на всех 9 страницах был один английский
    # og.png: шаринг /hi/ показывал английскую карточку). Файлы собирает tools/og-cards.py;
    # старый og.png не перезаписывается — английская карточка называется og-en.png.
    og_img = BASE + "img/" + ("og-en.png" if lang == "en" else f"og-{lang}.png")
    out = re.sub(r'<meta property="og:image" content="[^"]*">',
                 f'<meta property="og:image" content="{og_img}">', out)
    out = re.sub(r'<meta name="twitter:image" content="[^"]*">',
                 f'<meta name="twitter:image" content="{og_img}">', out)

    # 5) JSON-LD: единственный источник — jsonld() ниже; в шаблоне только маркер
    #    (24.10.2026). Раньше шаблон нёс свою копию блока, и она отстала от словарей
    #    на четыре вопроса. Подстановка по маркеру падает громко, регулярка — молча
    #    (не совпала и всё), поэтому здесь assert, а не re.sub.
    assert "{{JSONLD}}" in out, "в шаблоне нет маркера {{JSONLD}} — структурированные данные некуда положить"
    out = out.replace("{{JSONLD}}", jsonld(d, lang))

    # 6) переключатель языка (aria-подпись — из словаря языка)
    out = re.sub(r'<div class="lang" role="group"[^>]*>.*?</div>',
                 switcher_html(lang, d["lang.aria"]), out, flags=re.S)

    # 7) JS-i18n в шаблоне больше нет (22.10.2026): мёртвый клиентский словарь удалён —
    #    вторая копия текстов расходилась с src/locales (ru: «первые 5 разборов»).
    #    Тексты запекаются сборкой, страница без JS показывает тот же язык.

    # 8) пути для подпапок
    if lang != "en":
        out = out.replace('src="img/', 'src="../img/').replace('href="img/', 'href="../img/')
        out = out.replace('poster="img/', 'poster="../img/')
        out = out.replace('src="demo/', 'src="../demo/')
        out = out.replace('href="privacy.html', 'href="../privacy.html')
        out = out.replace('href="terms.html', 'href="../terms.html')
        out = out.replace('href="index.html"', 'href="../"')
        if lang == "ru":
            # Двуязычные privacy/terms: с /ru/ ссылки ведут сразу к русскому разделу (spec: анкоры #ru)
            out = out.replace('href="../privacy.html"', 'href="../privacy.html#ru"')
            out = out.replace('href="../terms.html"', 'href="../terms.html#ru"')

    # 8а-2) форма: после отправки Web3Forms возврат на страницу того же языка (?sent=1#contact-card;
    # якорь на блок формы — по нему CSS показывает подтверждение и без JS)
    out = out.replace(BASE + "?sent=1#contact-card", url_for(lang) + "?sent=1#contact-card")

    # 8а-3) метка CTA несёт язык страницы (23.10.2026). До этого все девять страниц отдавали
    # боту один src_landing: первый экран выбирался по языку интерфейса Telegram (посетитель
    # /hi/ с Telegram на финском получал русское приветствие), а владелец не мог узнать,
    # какая языковая страница приводит людей. Кавычка в шаблоне не даёт спутать метку
    # с её продолжением (_band/_shots/_sticky), поэтому замены независимы.
    for _pos in ("band", "shots", "sticky"):
        _old = f'?start=src_landing_{_pos}"'
        assert out.count(_old) == 1, f"{lang}: метка {_old!r} встречается {out.count(_old)} раз"
        out = out.replace(_old, f'?start=src_landing_{lang}_{_pos}"')
    _old = '?start=src_landing"'
    assert out.count(_old) == 1, f"{lang}: метка {_old!r} встречается {out.count(_old)} раз"
    out = out.replace(_old, f'?start=src_landing_{lang}"')

    # 8b) шрифты: preload под письменность страницы, пути — для подпапок
    if lang in ("ru", "uk"):
        out = out.replace('href="fonts/manrope-latin.woff2"', 'href="fonts/manrope-cyrillic.woff2"')
    if lang != "en":
        out = out.replace('href="fonts/', 'href="../fonts/')
        out = out.replace('url("fonts/', 'url("../fonts/')

    # 9) скриншоты по языку
    prefix = "../img/" if lang != "en" else "img/"
    out = re.sub(r'src="(?:\.\./)?img/shot(\d)(?:-\w+)?\.webp"',
                 lambda m: f'src="{prefix}{shot_src(m.group(1), lang)}"', out)

    # 9c) альты скриншотов — по языку (до 16.10 оставались англ. на всех 9 страницах;
    #     атрибуты data-shot/data-alt-* были мертвы после отказа от JS-i18n и удалены)
    for _i in ("1", "2", "3"):
        out = re.sub(
            rf'(<img src="(?:\.\./)?img/shot{_i}(?:-\w+)?\.webp"[^>]*? alt=")[^"]*(")',
            lambda m, _i=_i: m.group(1) + esc_attr(d[f"shot{_i}.alt"]) + m.group(2),
            out)

    # 9e) альты бейджей + подпись группы бейджей — по языку (до 16.10 были англ. на всех
    #     9 страницах: бейдж героя + 7 бейджей футера). Шаблон — badge.alt словаря,
    #     имя площадки подставляется; каждое совпадение обязано быть ровно одно.
    tpl = d["badge.alt"]
    assert "{name}" in tpl, f"{lang}: badge.alt без {{name}}"
    for frag, nm in BADGE_ALTS:
        pat = re.compile(
            r'(<img src="' + frag + r'[^"]*"[^>]*?alt=")[^"]*(")')
        out, n = pat.subn(
            lambda m, _a=esc_attr(tpl.format(name=nm)): m.group(1) + _a + m.group(2), out)
        assert n == 1, f"{lang}: бейдж {nm} — совпадений {n}"

    # 9e2) бейдж-награда LiftOff "No. 1 of the Day" — отдельный альт по языку (выдан площадкой,
    #      ссылка та же; не «Featured on», поэтому не в BADGE_ALTS) — 21.10
    assert "badge.award" in d, f"{lang}: нет badge.award"
    pat_award = re.compile(
        r'(<img src="(?:https://lift-off\.sh/images/badges/day/|(?:\.\./)?img/badges/liftoff-day\.webp)[^"]*"[^>]*?alt=")[^"]*(")')
    out, n_award = pat_award.subn(
        lambda m: m.group(1) + esc_attr(d["badge.award"]) + m.group(2), out)
    assert n_award == 1, f"{lang}: бейдж-награда LiftOff — совпадений {n_award}"
    assert out.count('aria-label="Featured on"') == 1, f"{lang}: группа бейджей не однозначна"
    out = out.replace('aria-label="Featured on"',
                      f'aria-label="{esc_attr(d["badge.group"])}"')

    # 9f) альт логотипа — по языку (до 16.10 на всех 9 страницах стоял англ. «UchiSamBot logo»;
    #     на языковой странице img/logo.svg ровно один — header-логотип)
    out, _n_logo = re.subn(
        r'(<img src="(?:\.\./)?img/logo\.svg"[^>]*? alt=")[^"]*(")',
        lambda m: m.group(1) + esc_attr(d["logo.alt"]) + m.group(2),
        out)
    assert _n_logo == 1, f"{lang}: логотип — совпадений {_n_logo}"

    # 9b) hero-видео и постер: у КАЖДОГО языка своя версия лупа (свои ассеты; EN-фолбэк — только
    #     у EN). До 17.10 (хвост ПРОХОДА 2) свои ассеты были только у RU; остальные 7 языков
    #     получили свои ролики в demo/uchiambot-demo-web-<lang>.mp4 (build-web-loop-langs.sh)
    if lang != "en":
        out = out.replace("demo/uchiambot-demo-web.mp4", f"demo/uchiambot-demo-web-{lang}.mp4")
        out = out.replace("img/demo-poster.webp", f"img/demo-poster-{lang}.webp")
    # Подпись видео ставит общий механизм data-i18n-attr (ключ demo.alt) — отдельной
    # подстановки здесь больше нет: девять строк жили в таблице генератора мимо словарей.

    # 10) CSS переключателя (один раз)
    if ".lang-dd" not in src:
        out = out.replace(
            "</style>",
            ".lang-dd{position:relative;font-size:14px}"
            ".lang-dd summary{list-style:none;cursor:pointer;padding:6px 10px;border:1px solid var(--line);border-radius:999px;background:#fff}"
            ".lang-dd summary::-webkit-details-marker{display:none}"
            ".lang-list{position:absolute;right:0;top:110%;background:#fff;border:1px solid var(--line);border-radius:12px;padding:8px;display:flex;flex-direction:column;gap:2px;z-index:30;min-width:180px;box-shadow:var(--shadow)}"
            ".lang-list a{padding:6px 10px;border-radius:8px;color:var(--ink);white-space:nowrap}"
            ".lang-list a:hover{background:var(--brand-soft)}"
            ".lang-list a.on{font-weight:700;color:var(--brand)}"
            "</style>",
        )
    return out


def page_md(d: dict, lang: str) -> str:
    """Markdown-двойник страницы (llms.txt v2): index.html.md рядом со страницей.

    Содержимое — из того же словаря языка, что и страница (единый источник правды):
    описание, шаги, возможности, предметы, цены, родителям, FAQ, контакты и ссылки.
    """
    bot = BOT_LLMS
    page_url = url_for(lang)
    pp = BASE + "privacy.html" + ("#ru" if lang == "ru" else "")
    tt = BASE + "terms.html" + ("#ru" if lang == "ru" else "")
    # Демо-ролик языка: в md-двойнике ссылка на СВОЙ 13-секундный луп (у каждого языка
    # он свой, EN-фолбэка у md быть не должно — как и у страницы). До 22.10 ИИ-слой
    # знал только два полных ролика из llms.txt, поэтому на вопрос «покажи, как это
    # работает» по-хинди отдать было нечего.
    demo = BASE + "demo/uchiambot-demo-web" + ("" if lang == "en" else "-" + lang) + ".mp4"
    L = [f"# {d['meta.title']}", "", f"> {d['meta.desc']}", "", d["hero.sub"], "",
         f"[{d['hero.cta']}]({bot})", "", f"[{d['md.demo']}]({demo})", "",
         f"## {d['how.title']}", ""]
    i = 1
    while f"how.s{i}t" in d:
        L.append(f"{i}. **{d[f'how.s{i}t']}** — {d[f'how.s{i}d']}")
        i += 1
    L += ["", f"## {d['feat.title']}", ""]
    i = 1
    while f"f{i}t" in d:
        L.append(f"- **{d[f'f{i}t']}** — {d[f'f{i}d']}")
        i += 1
    L += ["", f"## {d['principle.title']}", "", d["principle.sub"],
          "", f"## {d['subj.title']}", ""]
    i = 1
    while f"subj.c{i}" in d:
        L.append(f"- {d[f'subj.c{i}']}")
        i += 1
    # «Живые чаты» (22.10.2026): секция страницы с тремя настоящими скриншотами
    # отсутствовала в двойнике ЦЕЛИКОМ — ни заголовка, ни подписи, ни кадров.
    # Агент, цитирующий страницу, не знал, что продукт показан на реальных
    # снимках, и не мог сказать, что на них видно. Каждый кадр — свой для языка
    # (shot_src), alt — из словаря (тот же, что на странице).
    L += ["", d["subj.note"], "", f"## {d['shots.title']}", "", d["shots.cap"], ""]
    for n in ("1", "2", "3"):
        L += [f"![{d[f'shot{n}.alt']}]({BASE}img/{shot_src(n, lang)})", ""]
    L += [f"## {d['price.title']}", "", d["price.note"], "",
          f"- **{d['p1t']} — {d['p1p']}**: {d['p1d']}",
          f"- **{d['p2t']} — {d['p2p']}**: {d['p2d']}",
          f"- **{d['p3t']} — {d['p3p']}**: {d['p3d']}",
          "", d["price.fine"], "", d["ref.text"], "", f"## {d['parents.title']}", ""]
    for b in ("b1", "b2", "b3", "b4"):
        L.append(f"- {d[f'parents.{b}']}")
    L += ["", f"## {d['faq.title']}", ""]
    i = 1
    while f"q{i}" in d:
        L += [f"### {d[f'q{i}']}", "", d[f"q{i}a"], ""]
        i += 1
    L += [f"## {d['contact.title']}", "", d["contact.sub"], "", d["contact.note"], "",
          f"- [{d['contact.btn']}]({page_url}#contact)",
          f"- [{legal_label(d['foot.privacy'], 'foot.privacy', lang)}]({pp})",
          f"- [{legal_label(d['foot.terms'], 'foot.terms', lang)}]({tt})", "",
          # Финальная полоса страницы. Без неё md-двойник заканчивался списком
          # документов: агент, цитирующий страницу, не доносил до читателя ни
          # призыва, ни главного оффера «первые 2 разбора бесплатно».
          f"## {d['cta.title']}", "", d["cta.sub"], "", f"[{d['cta.btn']}]({bot})", ""]
    return "\n".join(L)


class _LegalParser(HTMLParser):
    """Мини-конвертер main-контента privacy/terms в markdown.

    Структура этих страниц известна и контролируется: h1/h2/h3, p, ul>li, hr,
    прозрачный section, инлайн b/strong/em/i/a, br. Неожиданная разметка — ошибка
    сборки (лучше упасть, чем выпустить испорченный md).
    """

    INLINE = {"b": "**", "strong": "**", "em": "*", "i": "*"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.buf = []
        self.ul = None
        self.sub = None      # открытый инлайн: ("a", href, buf) | ("fmt", marker, buf)
        self.expect = None   # открытый контейнер: h1/h2/h3/p/li
        self.err = []

    def handle_data(self, data):
        if self.sub:
            self.sub[2].append(data)
        elif self.expect:
            self.buf.append(data)
        elif data.strip():
            self.err.append(f"текст вне блока: {data.strip()[:40]!r}")

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            return
        if tag == "hr":
            self.blocks.append("---")
            return
        if tag == "br":
            self.handle_data(" ")
            return
        if tag in ("h1", "h2", "h3", "p", "li"):
            if self.expect:
                self.err.append(f"вложенный <{tag}> внутри <{self.expect}>")
            self.expect = tag
            self.buf = []
            return
        if tag == "ul":
            if self.ul is not None:
                self.err.append("вложенный <ul>")
            self.ul = []
            return
        if tag == "a":
            if self.sub:
                self.err.append("вложенный инлайн <a>")
            self.sub = ("a", dict(attrs).get("href", ""), [])
            return
        if tag in self.INLINE:
            if self.sub:
                self.err.append(f"вложенный инлайн <{tag}>")
            self.sub = ("fmt", self.INLINE[tag], [])
            return
        self.err.append(f"неожиданный тег <{tag}>")

    def handle_endtag(self, tag):
        if tag in ("section", "hr", "br"):
            return
        if tag == "a" or tag in self.INLINE:
            if not self.sub:
                self.err.append(f"</{tag}> без открытия")
                return
            kind, val, buf = self.sub
            self.sub = None
            text = " ".join("".join(buf).split())
            self.buf.append(f"[{text}]({val})" if kind == "a" else f"{val}{text}{val}")
            return
        if tag in ("h1", "h2", "h3", "p", "li"):
            if self.expect != tag:
                self.err.append(f"</{tag}> не совпал с <{self.expect}>")
            text = " ".join("".join(self.buf).split())
            self.buf = []
            self.expect = None
            if tag == "li":
                if self.ul is None:
                    self.err.append("</li> вне <ul>")
                else:
                    self.ul.append(text)
            elif tag == "p":
                self.blocks.append(text)
            else:
                self.blocks.append({"h1": "# ", "h2": "## ", "h3": "### "}[tag] + text)
            return
        if tag == "ul":
            self.blocks.append("\n".join("- " + x for x in (self.ul or [])))
            self.ul = None
            return
        self.err.append(f"неожиданный </{tag}>")


def legal_md(src_text: str, name: str) -> str:
    """Markdown-двойник privacy/terms: main-контент (EN-часть + RU-секция) в markdown."""
    m = re.search(r'<main[^>]*id="main"[^>]*>(.*?)</main>', src_text, re.S)
    assert m, f"{name}: не найден main"
    p = _LegalParser()
    p.feed(m.group(1))
    p.close()
    assert not p.err, f"{name}: конвертер md: {p.err[:5]}"
    assert p.expect is None and p.sub is None and p.ul is None, f"{name}: незакрытые блоки"
    out = "\n\n".join(b for b in p.blocks if b) + "\n"
    assert out.startswith("# ") and "<" not in out and ">" not in out, f"{name}: плохой md"
    assert "\n---\n" in out, f"{name}: нет разделителя EN/RU"
    return out


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_lastmods() -> dict:
    """Прошлые штампы {url: {"sha", "date"}} из tools/lastmod.json.

    Зачем: lastmod в sitemap обязан означать «когда контент реально изменился».
    Раньше туда писался datetime.date.today() — сборка была НЕ воспроизводима
    (любой перезапуск менял sitemap) и дата врала при неизменном контенте.
    """
    try:
        data = json.loads((ROOT / "tools" / "lastmod.json").read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        return data
    except (OSError, ValueError, AssertionError):
        return {}


def stamp(prev: dict, url: str, content: str, today: str) -> dict:
    """Штамп страницы: дата остаётся прежней, пока байты контента те же."""
    sha = _sha256(content)
    old = prev.get(url) or {}
    date = old.get("date") if old.get("sha") == sha and old.get("date") else today
    return {"sha": sha, "date": date}


def sitemap(dates: dict) -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    # alternates: каждый язык + x-default (фолбэк для несовпавших языков; соответствует
    # hreflang x-default в шапках страниц и «Guidelines for all methods» Google)
    alts = "\n".join(
        [f'    <xhtml:link rel="alternate" hreflang="{x}" href="{url_for(x)}"/>' for x in LANGS]
        + [f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}"/>']
    )
    for lang in LANGS:
        url = url_for(lang)
        parts.append(f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{dates[url]}</lastmod>\n{alts}\n  </url>')
    for page in ("privacy.html", "terms.html"):
        url = BASE + page
        parts.append(f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{dates[url]}</lastmod>\n  </url>')
    parts.append("</urlset>\n")
    return "\n".join(parts)


def llms(dicts: dict) -> str:
    d = dicts["en"]
    lines = [
        "# UchiSamBot",
        "",
        "> " + d["meta.desc"],
        "",
        "Open the bot: " + BOT_LLMS,
        "",
        "## Pages",
        "",
    ]
    for lang in LANGS:
        lines.append(f'- [{LABELS[lang]}: {dicts[lang]["meta.title"]}]'
                     f'({url_for(lang)}index.html.md): landing page — features, how it works, pricing, FAQ.')
    lines += [
        f"- [Privacy Policy]({BASE}privacy.html.md): what data the bot handles, and how to have it deleted.",
        f"- [Terms of Service]({BASE}terms.html.md): pricing and usage rules.",
        "",
        "## Optional",
        "",
        f"- [Demo video (35 s, English)]({BASE}demo/uchiambot-demo.mp4)",
        f"- [Demo video (35 s, Russian)]({BASE}demo/uchiambot-demo-ru.mp4)",
        "",
        # Лупы героя: по одному на язык, 13 с, подписи шагов на языке страницы.
        # До 22.10 llms.txt знал только два полных ролика, и на «покажи по-хинди»
        # у агента не было ни одной ссылки, хотя файл лежал на сайте.
        "Hero loops (13 s, step captions in the page language):",
        "",
    ]
    for lang in LANGS:
        loop = "demo/uchiambot-demo-web" + ("" if lang == "en" else "-" + lang) + ".mp4"
        lines.append(f"- [{LABELS[lang]}]({BASE}{loop})")
    lines.append("")
    return "\n".join(lines)


def page_404() -> str:
    """Страница 404 (одна на весь сайт, EN + чипы языков).

    Зачем: без неё GitHub Pages отдаёт свою стандартную английскую заглушку на любой
    несуществующий адрес — посетитель уходит, а конверсия теряется. Своя 404 возвращает
    человека к языку и к боту.

    Все URL — АБСОЛЮТНЫЕ (BASE+...): 404 отдаётся по ЛЮБОМУ пути, поэтому относительные
    ссылки/ассеты считались бы от запрошенного адреса и ломались (стили, шрифты, ссылки).
    Никаких дат и случайных значений — сборка воспроизводима.
    """
    chips = []
    for lang in LANGS:
        label = LABELS[lang]  # чистое название языка, без флага
        # lang/hreflang — чтобы скринридер читал «Русский» по-русски (WCAG 3.1.2),
        # aria-current="true" — «текущий пункт набора» (это не текущая страница:
        # чип ведёт на главную другого языка, а не на эту 404).
        cur = ' aria-current="true"' if lang == "en" else ""
        chips.append(f'<li><a href="{url_for(lang)}" hreflang="{lang}" lang="{lang}"{cur}>'
                     f'{esc_text(label)}</a></li>')
    # Шрифты 404 (22.10.2026). До этого блока страница несла все пять сабсетов Manrope,
    # хотя её текст — английский: браузер скачивал cyrillic 14.2 + vietnamese 8.3 КБ
    # только чтобы нарисовать «Русский» и «Tiếng Việt» в чипах, а «हिन्दी» оставалось
    # БЕЗ шрифта (сабсета деванагари на странице не было) — единственная ссылка для
    # хинди-посетителя рисовалась системным шрифтом. Теперь: latin (текст) + три
    # мини-сабсета переключателя (tools/lang-fonts.json) — дешевле и без подмены.
    # Вес у всех трёх лиц ОДИН (200 800) намеренно: Chrome отбирает лицо внутри
    # семейства по style-дескрипторам и только потом смотрит unicode-range; разный
    # вес у одного лица ломает выбор по диапазону (проверено: сабсет деванагари
    # не запрашивался, пока у него стояло 400 800, хотя диапазон совпадал).
    lang_faces = "".join(
        f"@font-face{{font-family:'UchiSam Langs';font-style:normal;font-weight:200 800;"
        f"font-display:swap;src:url(\"{BASE}{v['file']}\") format('woff2');"
        f"unicode-range:{v['range']}}}\n"
        for v in LANG_FONTS.values()
    )
    faces = "".join(
        f"@font-face{{font-family:'Manrope';font-style:normal;font-weight:200 800;"
        f"font-display:swap;src:url(\"{BASE}fonts/manrope-{s}.woff2\") format('woff2');"
        f"unicode-range:{r}}}\n"
        for s, r in FONT_SUBSETS
        if s == "latin"          # на 404 нет ни кириллического, ни вьетнамского текста
    ) + lang_faces
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found — UchiSamBot</title>
<meta name="robots" content="noindex,follow">
<meta name="theme-color" content="#3D5AFE">
<link rel="icon" href="{BASE}img/logo.svg" type="image/svg+xml">
<link rel="icon" type="image/png" sizes="64x64" href="{BASE}img/icon-64.png">
<style>
/* Шрифты: latin для английского текста + три мини-сабсета переключателя
   (cyrillic/vietnamese/devanagari — ровно глифы девяти названий, см. tools/lang-fonts.json).
   Полные сабсеты по письменностям здесь не нужны: текста на них на 404 нет. */
{faces}:root{{--brand:#3D5AFE;--brand-deep:#2338A8;--brand-soft:#EAF0FF;--ink:#14203A;--muted:#50617F;--bg:#F7FAFF;--card:#fff;--line:#E3EAF7;--r:18px}}
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:var(--bg);color:var(--ink);
  font:16px/1.6 "UchiSam Langs","Manrope",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased}}
.card{{width:100%;max-width:620px;background:var(--card);border:1px solid var(--line);border-radius:var(--r);
  box-shadow:0 10px 30px rgba(30,60,140,.08);padding:32px}}
.brand{{display:flex;align-items:center;gap:10px;margin-bottom:20px;font-weight:800;letter-spacing:-.02em}}
.code{{font-size:64px;font-weight:800;letter-spacing:-.03em;line-height:1;color:var(--brand);margin:0 0 8px}}
h1{{font-size:clamp(22px,4.6vw,30px);line-height:1.25;letter-spacing:-.02em;margin:0 0 10px}}
p{{margin:0 0 20px;color:var(--muted)}}
.langs{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 24px;padding:0;list-style:none}}
.langs a{{display:inline-flex;align-items:center;min-height:44px;padding:8px 14px;border:1px solid var(--line);
  border-radius:999px;color:var(--ink);text-decoration:none;font-weight:600}}
.langs a:hover{{border-color:var(--brand);color:var(--brand)}}
.langs a[aria-current]{{background:var(--brand-soft);border-color:var(--brand);color:var(--brand-deep)}}
.acts{{display:flex;flex-wrap:wrap;align-items:center;gap:12px}}
.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:12px 20px;border-radius:12px;
  background:var(--brand);color:#fff;font-weight:700;text-decoration:none}}
.btn:hover{{background:#2F49D6}}
.alt{{font-weight:600;color:var(--ink)}}
footer{{margin-top:24px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:14px}}
footer a{{color:var(--muted)}}
:focus-visible{{outline:3px solid var(--brand);outline-offset:2px}}
@media (forced-colors:active){{.btn,.langs a{{border:1px solid}}}}
/* Бумага (25.10.2026): у .btn фон var(--brand), текст белый, а браузер печатает без фонов —
   кнопка «Open UchiSamBot in Telegram» выходила белым прямоугольником без надписи.
   Поля @page (25.10.2026, вечер): без них при пустых полях в диалоге печати текст ложится на
   кромку листа; 6 мм — как у политики и условий, один язык бумаги на весь сайт. */
@media print{{@page{{margin:6mm}}.btn{{background:#fff;color:#111;border:1px solid #44506A}}}}
</style>
</head>
<body>
<main class="card">
  <div class="brand"><img src="{BASE}img/logo.svg" alt="" width="34" height="34">UchiSamBot</div>
  <p class="code">404</p>
  <h1>This page doesn't exist</h1>
  <p>The link may be out of date, or the address has a typo. Pick your language — the site is the same in all nine.</p>
  <ul class="langs">
    {"".join(chips)}
  </ul>
  <div class="acts">
    <a class="btn" href="https://t.me/UchiSamBot?start=src_landing_404">Open UchiSamBot in Telegram</a>
    <a class="alt" href="{BASE}">Go to the home page</a>
  </div>
  <footer>UchiSamBot — step-by-step homework help in Telegram ·
    <a href="{BASE}privacy.html">Privacy</a> · <a href="{BASE}terms.html">Terms</a></footer>
</main>
</body>
</html>
"""


def audit_site_address(pages: dict | None = None) -> None:
    """После сборки: чужого адреса сайта не осталось ни в одном файле (22.10.2026).

    Зачем отдельно от load_site: сборка приводит к текущему адресу только те файлы,
    что перечислены в previous. Если адрес сменили, а старый в previous не внесли,
    нормализация молча ничего не делает — и страницы уезжают в свет со старым
    canonical/og:url, то есть сами себя выкидывают из поиска. Свип это ловит, но
    ловит ПОСЛЕ сборки; здесь сборка падает сама (код 1), называет файлы и не даёт
    закоммитить половинчатый переезд.

    23.10.2026: pages — содержимое в памяти (режим --check проверяет то, что будет
    записано, а не то, что уже лежит). Без словаря функция читает файлы с диска.
    """
    pat = re.compile(r"https://([A-Za-z0-9.-]+)/uchisambot/")
    files = ["index.html", "index.html.md", "privacy.html", "privacy.html.md",
             "terms.html", "terms.html.md", "sitemap.xml", "robots.txt",
             "llms.txt", "404.html"]
    files += [f"{lang}/index.html" for lang in LANGS[1:]]
    files += [f"{lang}/index.html.md" for lang in LANGS[1:]]
    bad = set()
    for name in files:
        if pages is not None:
            if name not in pages:
                continue
            text = pages[name]
        else:
            p = ROOT / name
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8")
        for host in pat.findall(text):
            url = f"https://{host}/uchisambot/"
            if url != BASE:
                bad.add(f"{name}: {url}")
    if bad:
        raise SystemExit(
            "СБОРКА ОТМЕНЕНА: в файлах остался чужой адрес сайта — переезд сделан наполовину.\n"
            "  Либо верни старый адрес в previous в tools/site.json, либо почини нормализацию:\n  "
            + "\n  ".join(sorted(bad)[:10]))


def audit_local_assets() -> None:
    """Каждый локальный ассет, на который ссылается собранная страница, обязан быть на диске.

    22.10.2026: значок Startup Fame отдавался площадкой, но Chrome резал его как ORB, и
    ссылка молча пряталась — на всех девяти страницах висело 7 площадок из 8, и никто
    этого не видел ни в сборке, ни в свипе. Теперь такой значок лежит у нас; чтобы файл
    не потерялся при чистке img/, сборка падает, если ссылка ведёт в пустоту. Ссылки на
    чужие домены (http/https//) не проверяются — их живость ловит браузерный аудит.
    """
    pat = re.compile(r'(?:src|href|poster)="((?:\.\./)?img/[^"]+)"')
    pages = ["index.html", "404.html", "privacy.html", "terms.html"]
    pages += [f"{lang}/index.html" for lang in LANGS[1:]]
    bad = []
    for name in pages:
        p = ROOT / name
        if not p.exists():
            continue
        for ref in pat.findall(p.read_text(encoding="utf-8")):
            rel = ref[3:] if ref.startswith("../") else ref
            if not (ROOT / rel).is_file():
                bad.append(f"{name}: {ref}")
    if bad:
        raise SystemExit("СБОРКА ОТМЕНЕНА: ссылка на локальный файл, которого нет на диске:\n  "
                         + "\n  ".join(sorted(set(bad))[:12]))


def _first_diff(have: str, want: str) -> str:
    """Короткое описание первого расхождения двух текстов (для отчёта --check)."""
    hl, wl = have.splitlines(), want.splitlines()
    for i, (a, b) in enumerate(zip(hl, wl), 1):
        if a != b:
            return f"строка {i}: на диске «{a.strip()[:70]}», сборка «{b.strip()[:70]}»"
    return (f"диск {len(have.encode('utf-8'))} Б / сборка {len(want.encode('utf-8'))} Б, "
            f"строк {len(hl)} / {len(wl)}")


def compare_outputs(outputs: dict) -> list:
    """Расхождения «что лежит на диске» против «что даёт свежая сборка» (23.10.2026).

    Зачем: свип проверял собранные файлы на внутреннюю согласованность и сверял
    sha страницы с реестром lastmod — то есть ловил РУЧНУЮ правку готовой страницы.
    Обратный случай он не видел: правку ИСТОЧНИКА (index-src.html, src/locales,
    prices.json) без пересборки. Тогда на диске остаётся старая, внутренне
    согласованная страница, реестр с ней согласен, свип зелёный — а сайт говорит
    не то, что написано в словарях. Сборка детерминирована (lastmod держит дату,
    пока байты те же), поэтому «свежая сборка == диск» — проверяемое утверждение.
    """
    bad = []
    for name in sorted(outputs):
        want = outputs[name]
        p = ROOT / name
        if not p.is_file():
            bad.append(f"НЕТ ФАЙЛА    {name}")
            continue
        have = p.read_text(encoding="utf-8")
        if have != want:
            bad.append(f"РАСХОЖДЕНИЕ  {name}: {_first_diff(have, want)}")
    return bad


def main() -> None:
    check = "--check" in sys.argv[1:]
    dicts = load_dicts()
    validate_subjects(dicts)
    hand = normalized_hand_written()
    changed = [n for n in HAND_WRITTEN if (ROOT / n).read_text(encoding="utf-8") != hand[n]]
    src = (ROOT / "index-src.html").read_text(encoding="utf-8")
    assert "data-i18n" in src, "источник не похож на index-src.html"
    # 22.10.2026: в шаблоне НЕ должно быть второй копии текстов. Старый клиентский
    # словарь I18N вырезался здесь и жил отдельной жизнью — разошёлся по деньгам
    # (ru cta.sub обещал 5 бесплатных разборов вместо 2). Вернуть его нельзя.
    assert "var I18N" not in src, ("index-src.html снова несёт JS-словарь I18N: "
                                   "вторая копия текстов запрещена, правь src/locales")
    assert BASE not in src, ("index-src.html содержит литерал адреса сайта — "
                             "в шаблоне должен быть только токен {{BASE}}")
    # Ключи шаблона обязаны иметь перевод в КАЖДОМ языке: иначе rep_i18n молча
    # оставит английский текст шаблона (см. validate_dicts).
    tmpl_keys = set(re.findall(r'data-i18n(?:-ph)?="([\w.]+)"', src))
    # 22.10.2026: подписи в атрибутах (data-i18n-attr) — тоже ключи словаря, иначе
    # перевод кнопки молча останется английским (та же болезнь, что у data-i18n).
    for _spec in re.findall(r'data-i18n-attr="([^"]+)"', src):
        for _pair in _spec.split(";"):
            if ":" in _pair:
                tmpl_keys.add(_pair.split(":", 1)[1].strip())
    uncovered = sorted(k for k in tmpl_keys if any(k not in dicts[l] for l in LANGS))
    assert not uncovered, f"в шаблоне ключи без перевода: {uncovered}"
    today = datetime.date.today().isoformat()
    prev = load_lastmods()
    stamps: dict = {}
    out: dict = {}          # полный набор файлов, которые сборка обязана положить на диск

    for lang in LANGS:
        page = bake(src, lang, dicts)
        assert 'data-i18n="' not in page, f"{lang}: остались незапечённые ключи"
        assert "data-i18n-ph=" not in page, f"{lang}: остались placeholder-ключи"
        assert "data-i18n-attr=" not in page, f"{lang}: остались непереведённые атрибуты"
        assert "{{BASE}}" not in page, f"{lang}: токен адреса сайта не заменён"
        assert "var I18N" not in page, f"{lang}: не вырезан JS-i18n"
        # Деванагари (26.10.2026): каждая буква деванагари на ЛЮБОЙ странице (в шапке
        # стоит «हिन्दी») обязана быть в сабсете, иначе браузер молча нарисует её
        # системным шрифтом — другой рисунок букв посреди слова.
        _deva_used = {ch for ch in page if "\u0900" <= ch <= "\u097f"}
        _deva_missing = sorted(ch for ch in _deva_used if ch not in DEVA_CHARS)
        if _deva_missing:
            raise SystemExit(
                f"{lang}: в тексте деванагари {[(c, f'U+{ord(c):04X}') for c in _deva_missing]}, "
                f"а в сабсете их нет — запусти python3 tools/subset-deva.py")
        rel = "index.html" if lang == "en" else f"{lang}/index.html"
        out[rel] = page
        md = page_md(dicts[lang], lang)
        assert md.startswith("# ") and "data-i18n" not in md, f"{lang}: плохой md-двойник"
        out[rel + ".md"] = md
        stamps[url_for(lang)] = stamp(prev, url_for(lang), page, today)

    for name in ("privacy.html", "terms.html"):
        md = legal_md(hand[name], name)
        out[name + ".md"] = md
        stamps[BASE + name] = stamp(prev, BASE + name, hand[name], today)

    # 404 (21.10): своя страница вместо стандартной заглушки GitHub Pages.
    # В sitemap НЕ идёт (её не индексируют), в lastmod-реестр не попадает.
    p404 = page_404()
    assert p404.count('<a href="' + BASE) >= 10, "404: не все ссылки абсолютные"
    out["404.html"] = p404

    out["sitemap.xml"] = sitemap({u: s["date"] for u, s in stamps.items()})
    out["tools/lastmod.json"] = json.dumps(stamps, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    out["llms.txt"] = llms(dicts)
    for name in changed:
        out[name] = hand[name]

    # Аудит адреса — по тому, что сборка собирается положить, а не по старому диску.
    audit_site_address({**{n: hand[n] for n in HAND_WRITTEN}, **out})

    if check:
        bad = compare_outputs(out)
        if bad:
            print("СВЕРКА НЕ ПРОЙДЕНА: на диске не то, что даёт свежая сборка — "
                  "правь источники и запусти tools/build.py")
            for line in bad:
                print("  " + line)
            raise SystemExit(1)
        print(f"СВЕРКА ПРОЙДЕНА: {len(out)} файлов совпадают со свежей сборкой")
        return

    if changed:
        print(f"адрес сайта нормализован в: {', '.join(changed)}")
    for name, text in out.items():
        p = ROOT / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    for lang in LANGS:
        rel = "index.html" if lang == "en" else f"{lang}/index.html"
        page = out[rel]
        print(f"{lang}: {ROOT / rel} ({len(page)} символов, {len(page.encode('utf-8'))} байт)")
        print(f"{lang}: {ROOT / (rel + '.md')} ({len(out[rel + '.md'].encode('utf-8'))} байт)")
    for name in ("privacy.html", "terms.html"):
        print(f"{name}.md ({len(out[name + '.md'].encode('utf-8'))} байт)")
    print(f"404.html ({len(out['404.html'].encode('utf-8'))} байт)")
    fresh = sum(1 for u, s in stamps.items() if s["date"] == today)
    print(f"sitemap.xml (lastmod: изменено сегодня {fresh} из {len(stamps)}) + llms.txt + tools/lastmod.json")
    audit_local_assets()


if __name__ == "__main__":
    main()
