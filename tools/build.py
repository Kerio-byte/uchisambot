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
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / "src" / "locales"
BASE = "https://kerio-byte.github.io/uchisambot/"
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
PRICES_FILE = ROOT / "tools" / "prices.json"
# Ссылка на бота для ИИ-слоя (llms.txt + md-двойники страниц). Правило владельца:
# каждая ссылка на бота несёт метку источника (реестр — ~/.hermes/state/money/link-tags.md);
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
LABELS = {
    "en": "🇬🇧 English", "ru": "🇷🇺 Русский", "es": "🇪🇸 Español", "pt": "🇧🇷 Português",
    "hi": "🇮🇳 हिन्दी", "id": "🇮🇩 Bahasa Indonesia", "tr": "🇹🇷 Türkçe", "vi": "🇻🇳 Tiếng Việt",
    "uk": "🇺🇦 Українська",
}
OG_LOCALE = {"en": "en_US", "ru": "ru_RU", "es": "es_ES", "pt": "pt_BR",
             "hi": "hi_IN", "id": "id_ID", "tr": "tr_TR", "vi": "vi_VN", "uk": "uk_UA"}
NO_TRANSLATE = ["UchiSamBot", "Telegram Stars", "Stars", "/lang", "you@example.com"]
VIDEO_ALT = {
    "en": "Demo: the bot breaks down a task step by step.",
    "ru": "Демонстрация: бот разбирает задачу по шагам.",
    "es": "Demostración: el bot resuelve una tarea paso a paso.",
    "pt": "Demonstração: o bot resolve uma tarefa passo a passo.",
    "hi": "डेमो: बॉट समस्या को चरण-दर-चरण हल करता है।",
    "id": "Demo: bot menyelesaikan tugas langkah demi langkah.",
    "tr": "Demo: bot bir soruyu adım adım çözüyor.",
    "vi": "Bản demo: bot giải bài từng bước.",
    "uk": "Демонстрація: бот розбирає задачу крок за кроком.",
}
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
BADGE_ALTS = [
    ("launchigniter.com/api/badge/", "LaunchIgniter"),
    ("fazier.com/api/v1/", "Fazier"),
    ("statics.startupbase.io/site/badges/", "StartupBase"),
    ("showmebest.ai/badge/", "ShowMeBestAI"),
    ("lift-off.sh/images/badges/badgeLaunched", "LiftOff"),
    ("startupfa.me/badge?", "Startup Fame"),
    ("cdn.openhunts.com/badges/", "OpenHunts Club"),
    ("auraplusplus.com/images/badges/", "Aura++"),
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
    links = []
    for l in LANGS:
        if l == lang:
            links.append(f'<a href="#" aria-current="page" class="on">{LABELS[l]}</a>')
        else:
            if lang == "en":
                href = "./" if l == "en" else f"{l}/"
            else:
                href = "../" if l == "en" else f"../{l}/"
            links.append(f'<a href="{href}">{LABELS[l]}</a>')
    return (
        f'<details class="lang-dd"><summary aria-label="{esc_attr(aria)}">🌐 '
        + LABELS[lang].split(" ", 1)[1]
        + '</summary><div class="lang-list">' + "".join(links) + "</div></details>"
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
    return '<script type="application/ld+json">\n' + json.dumps(
        {"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) + "\n</script>"


def shot_src(n: str, lang: str) -> str:
    """Картинка языка, если файл есть; иначе — английская."""
    for cand in (f"shot{n}-{lang}.webp", f"shot{n}.webp"):
        if (ROOT / "img" / cand).exists():
            return cand
    return f"shot{n}.webp"


def bake(src: str, lang: str, dicts: dict) -> str:
    d = dicts[lang]
    out = src

    # 1) тексты data-i18n и placeholders data-i18n-ph
    def rep_i18n(m: re.Match) -> str:
        key = m.group(2)
        val = d.get(key)
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

    # 5) JSON-LD
    out = re.sub(r'<script type="application/ld\+json">.*?</script>', jsonld(d, lang), out, flags=re.S)

    # 6) переключатель языка (aria-подпись — из словаря языка)
    out = re.sub(r'<div class="lang" role="group"[^>]*>.*?</div>',
                 switcher_html(lang, d["lang.aria"]), out, flags=re.S)

    # 7) вырезать JS-i18n (тексты уже запечены)
    out = re.sub(r'<script>\s*\nvar I18N = \{.*?\n\}\)\(\);\n</script>\n', "", out, flags=re.S)

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
            r'(<img src="https://' + re.escape(frag) + r'[^"]*"[^>]*?alt=")[^"]*(")')
        out, n = pat.subn(
            lambda m, _a=esc_attr(tpl.format(name=nm)): m.group(1) + _a + m.group(2), out)
        assert n == 1, f"{lang}: бейдж {nm} — совпадений {n}"

    # 9e2) бейдж-награда LiftOff "No. 1 of the Day" — отдельный альт по языку (выдан площадкой,
    #      ссылка та же; не «Featured on», поэтому не в BADGE_ALTS) — 21.10
    assert "badge.award" in d, f"{lang}: нет badge.award"
    pat_award = re.compile(
        r'(<img src="https://lift-off\.sh/images/badges/day/[^"]*"[^>]*?alt=")[^"]*(")')
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
    out = out.replace(VIDEO_ALT["en"], VIDEO_ALT[lang])

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
    L = [f"# {d['meta.title']}", "", f"> {d['meta.desc']}", "", d["hero.sub"], "",
         f"[{d['hero.cta']}]({bot})", "", f"## {d['how.title']}", ""]
    i = 1
    while f"how.s{i}t" in d:
        L.append(f"{i}. **{d[f'how.s{i}t']}** — {d[f'how.s{i}d']}")
        i += 1
    L += ["", f"## {d['feat.title']}", ""]
    i = 1
    while f"f{i}t" in d:
        L.append(f"- **{d[f'f{i}t']}** — {d[f'f{i}d']}")
        i += 1
    L += ["", f"**{d['principle.title']}** {d['principle.sub']}",
          "", f"## {d['subj.title']}", ""]
    i = 1
    while f"subj.c{i}" in d:
        L.append(f"- {d[f'subj.c{i}']}")
        i += 1
    L += ["", d["subj.note"], "", f"## {d['price.title']}", "", d["price.note"], "",
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
          f"- [{d['foot.privacy']}]({pp})",
          f"- [{d['foot.terms']}]({tt})", ""]
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
    ]
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
        label = LABELS[lang].split(" ", 1)[1]  # без эмодзи-флага
        # lang/hreflang — чтобы скринридер читал «Русский» по-русски (WCAG 3.1.2),
        # aria-current="true" — «текущий пункт набора» (это не текущая страница:
        # чип ведёт на главную другого языка, а не на эту 404).
        cur = ' aria-current="true"' if lang == "en" else ""
        chips.append(f'<li><a href="{url_for(lang)}" hreflang="{lang}" lang="{lang}"{cur}>'
                     f'{esc_text(label)}</a></li>')
    faces = "".join(
        f'@font-face{{font-family:\'Manrope\';font-style:normal;font-weight:200 800;'
        f'font-display:swap;src:url("{BASE}fonts/manrope-{s}.woff2") format(\'woff2\');'
        f'unicode-range:{r}}}\n'
        for s, r in FONT_SUBSETS
    )
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
/* Manrope (variable, self-hosted, OFL) — те же 5 сабсетов, что и на основных страницах */
{faces}:root{{--brand:#3D5AFE;--brand-deep:#2338A8;--brand-soft:#EAF0FF;--ink:#14203A;--muted:#50617F;--bg:#F7FAFF;--card:#fff;--line:#E3EAF7;--r:18px}}
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:var(--bg);color:var(--ink);
  font:16px/1.6 "Manrope",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased}}
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


def main() -> None:
    dicts = load_dicts()
    src = (ROOT / "index-src.html").read_text(encoding="utf-8")
    assert "data-i18n" in src and "var I18N" in src, "источник не похож на index-src.html"
    # Ключи шаблона обязаны иметь перевод в КАЖДОМ языке: иначе rep_i18n молча
    # оставит английский текст шаблона (см. validate_dicts).
    tmpl_keys = set(re.findall(r'data-i18n(?:-ph)?="([\w.]+)"', src))
    uncovered = sorted(k for k in tmpl_keys if any(k not in dicts[l] for l in LANGS))
    assert not uncovered, f"в шаблоне ключи без перевода: {uncovered}"
    today = datetime.date.today().isoformat()
    prev = load_lastmods()
    stamps: dict = {}

    for lang in LANGS:
        page = bake(src, lang, dicts)
        assert 'data-i18n="' not in page, f"{lang}: остались незапечённые ключи"
        assert "data-i18n-ph=" not in page, f"{lang}: остались placeholder-ключи"
        assert "var I18N" not in page, f"{lang}: не вырезан JS-i18n"
        outdir = ROOT if lang == "en" else ROOT / lang
        outdir.mkdir(exist_ok=True)
        (outdir / "index.html").write_text(page, encoding="utf-8")
        print(f"{lang}: {outdir / 'index.html'} ({len(page)} символов, {len(page.encode('utf-8'))} байт)")
        md = page_md(dicts[lang], lang)
        assert md.startswith("# ") and "data-i18n" not in md, f"{lang}: плохой md-двойник"
        (outdir / "index.html.md").write_text(md, encoding="utf-8")
        print(f"{lang}: {outdir / 'index.html.md'} ({len(md.encode('utf-8'))} байт)")
        stamps[url_for(lang)] = stamp(prev, url_for(lang), page, today)

    for name in ("privacy.html", "terms.html"):
        raw = (ROOT / name).read_text(encoding="utf-8")
        md = legal_md(raw, name)
        (ROOT / (name + ".md")).write_text(md, encoding="utf-8")
        print(f"{name}.md ({len(md.encode('utf-8'))} байт)")
        stamps[BASE + name] = stamp(prev, BASE + name, raw, today)

    # 404 (21.10): своя страница вместо стандартной заглушки GitHub Pages.
    # В sitemap НЕ идёт (её не индексируют), в lastmod-реестр не попадает.
    p404 = page_404()
    assert p404.count('<a href="' + BASE) >= 10, "404: не все ссылки абсолютные"
    (ROOT / "404.html").write_text(p404, encoding="utf-8")
    print(f"404.html ({len(p404.encode('utf-8'))} байт)")

    (ROOT / "sitemap.xml").write_text(sitemap({u: s["date"] for u, s in stamps.items()}), encoding="utf-8")
    (ROOT / "tools" / "lastmod.json").write_text(
        json.dumps(stamps, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "llms.txt").write_text(llms(dicts), encoding="utf-8")
    fresh = sum(1 for u, s in stamps.items() if s["date"] == today)
    print(f"sitemap.xml (lastmod: изменено сегодня {fresh} из {len(stamps)}) + llms.txt + tools/lastmod.json")


if __name__ == "__main__":
    main()
