#!/usr/bin/env python3
"""Генератор языковых страниц лендинга UchiSamBot (только статические файлы, без рантайма).

Источник:  index-src.html — страница с разметкой data-i18n (EN-тексты внутри, как база)
Словари:   src/locales/*.json (en, ru + es, pt, hi, id, tr, vi, uk)
Выход:     index.html (EN, корень) + <lang>/index.html для 8 языков + sitemap.xml + llms.txt
Запуск:    python3 tools/build.py     (правки контента: меняешь словарь → пересборка)
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / "src" / "locales"
BASE = "https://kerio-byte.github.io/uchisambot/"
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
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


def url_for(lang: str) -> str:
    return BASE if lang == "en" else f"{BASE}{lang}/"


def load_dicts() -> dict:
    out = {}
    for lang in LANGS:
        out[lang] = json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
        assert len(out[lang]) >= 80, f"{lang}: мало ключей"
    return out


def esc_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;")


def esc_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hreflang_block() -> str:
    lines = [f'<link rel="alternate" hreflang="{l}" href="{url_for(l)}">' for l in LANGS]
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}">')
    return "\n".join(lines)


def switcher_html(lang: str) -> str:
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
        '<details class="lang-dd"><summary aria-label="Language">🌐 '
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
             {"@type": "Offer", "name": d["p1t"], "price": "0", "priceCurrency": "XTR"},
             {"@type": "Offer", "name": d["price.single"], "price": "30", "priceCurrency": "XTR"},
             {"@type": "Offer", "name": d["p2t"], "price": "120", "priceCurrency": "XTR"},
             {"@type": "Offer", "name": d["p3t"], "price": "300", "priceCurrency": "XTR"},
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

    # 3) canonical + hreflang
    out = re.sub(r'<link rel="canonical" href="[^"]*">',
                 f'<link rel="canonical" href="{url_for(lang)}">\n' + hreflang_block(), out)

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

    # 5) JSON-LD
    out = re.sub(r'<script type="application/ld\+json">.*?</script>', jsonld(d, lang), out, flags=re.S)

    # 6) переключатель языка
    out = re.sub(r'<div class="lang" role="group"[^>]*>.*?</div>', switcher_html(lang), out, flags=re.S)

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

    # 8а-2) форма: после отправки Web3Forms возврат на страницу того же языка (?sent=1#contact)
    out = out.replace(BASE + "?sent=1#contact", url_for(lang) + "?sent=1#contact")

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

    # 9b) hero-видео: у RU своя версия (у каждого языка свои ассеты; остальным — EN-фолбэк)
    if lang == "ru":
        out = out.replace("demo/uchiambot-demo-web.mp4", "demo/uchiambot-demo-web-ru.mp4")
        out = out.replace("img/demo-poster.webp", "img/demo-poster-ru.webp")
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


def sitemap() -> str:
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    # alternates: каждый язык + x-default (фолбэк для несовпавших языков; соответствует
    # hreflang x-default в шапках страниц и «Guidelines for all methods» Google)
    alts = "\n".join(
        [f'    <xhtml:link rel="alternate" hreflang="{x}" href="{url_for(x)}"/>' for x in LANGS]
        + [f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}"/>']
    )
    today = datetime.date.today().isoformat()
    for lang in LANGS:
        parts.append(f'  <url>\n    <loc>{url_for(lang)}</loc>\n    <lastmod>{today}</lastmod>\n{alts}\n  </url>')
    for page in ("privacy.html", "terms.html"):
        parts.append(f'  <url>\n    <loc>{BASE}{page}</loc>\n    <lastmod>{today}</lastmod>\n  </url>')
    parts.append("</urlset>\n")
    return "\n".join(parts)


def llms(dicts: dict) -> str:
    d = dicts["en"]
    lines = [
        "# UchiSamBot",
        "",
        "> " + d["meta.desc"],
        "",
        "Open the bot: https://t.me/UchiSamBot",
        "",
        "## Pages",
        "",
    ]
    for lang in LANGS:
        lines.append(f'- [{LABELS[lang]}: {dicts[lang]["meta.title"]}]({url_for(lang)})')
    lines += [
        f"- [Privacy Policy]({BASE}privacy.html)",
        f"- [Terms of Service]({BASE}terms.html)",
        "",
        "## Optional",
        "",
        f"- [Demo video (35 s, English)]({BASE}demo/uchiambot-demo.mp4)",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    dicts = load_dicts()
    src = (ROOT / "index-src.html").read_text(encoding="utf-8")
    assert "data-i18n" in src and "var I18N" in src, "источник не похож на index-src.html"

    for lang in LANGS:
        page = bake(src, lang, dicts)
        assert 'data-i18n="' not in page, f"{lang}: остались незапечённые ключи"
        assert "data-i18n-ph=" not in page, f"{lang}: остались placeholder-ключи"
        assert "var I18N" not in page, f"{lang}: не вырезан JS-i18n"
        outdir = ROOT if lang == "en" else ROOT / lang
        outdir.mkdir(exist_ok=True)
        (outdir / "index.html").write_text(page, encoding="utf-8")
        print(f"{lang}: {outdir / 'index.html'} ({len(page)} символов, {len(page.encode('utf-8'))} байт)")

    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (ROOT / "llms.txt").write_text(llms(dicts), encoding="utf-8")
    print("sitemap.xml + llms.txt обновлены")


if __name__ == "__main__":
    main()
