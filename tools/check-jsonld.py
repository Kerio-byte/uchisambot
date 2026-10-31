#!/usr/bin/env python3
"""JSON-LD: данные для машинного чтения, которых не видит ни один другой прибор.

Зачем. У дерева девятнадцать приборов, и ни один не читал `<script type=
"application/ld+json">`. Приборы держат разметку, ссылки, карту сайта, веса и
слова страницы — то есть то, что видит человек или краулер в HTML. JSON-LD
человек не видит вообще: его читают поисковик и ассистенты, и там же лежат цены,
язык страницы и одиннадцать пар «вопрос-ответ». Разъехавшаяся цена в этом блоке
не видна глазу, не видна свипу и не видна браузеру — она видна только в выдаче,
где рядом с сайтом стоит старая цифра. `tools/prices.json` с 21.10 обещает:
«свип сверяет с этим файлом JSON-LD» — не сверял никто.

Что держит (классы дефектов, свои теги в отчёте):

  LD    — синтаксис: блок есть, JSON парсится, @context схемы, у каждого узла
          есть @type и абсолютный @id, два узла не делят один @id.
  COVER — покрытие: на каждой странице-визитке ровно один блок и ровно четыре
          узла — Organization, WebSite, SoftwareApplication, FAQPage, по одному.
  IDENT — личность: WebSite.url равен canonical своей страницы, inLanguage равен
          <html lang>, publisher указывает на Organization из этого же блока,
          Organization.url — корень сайта, logo — файл, который лежит на диске,
          адрес приложения совпадает с кнопкой на самой странице.
  OFFER — цены: четыре предложения с ценами 0 / одиночный / пакет 5 / пакет 15
          против tools/prices.json, валюта из того же файла, цена — число
          строкой, и набор цен ОДИН на всех девяти языках (цена, разъехавшаяся
          по локалям, — отдельный класс брака).
  FAQ   — вопросы: у каждого есть ответ, ни один вопрос не повторяется, и текст
          каждого вопроса И ответа реально виден на странице (разметка обещает
          поисковику то, чего на странице нет, — это повод для санкций, а не
          мелочь вёрстки).
  LEAK  — в данных нет плейсхолдеров {…}, TODO, lorem, локальных путей,
          localhost и http:// (схема данных обязана быть https).

Почему ожидания выводятся из дерева, а не из констант build.py: база сайта
берётся из canonical корня, языки — из каталогов с index.html, <html lang> — со
страницы. Прибор обязан спорить со сборкой, а не повторять её.

Запуск:
  python3 tools/check-jsonld.py            # проверка дерева
  python3 tools/check-jsonld.py --control  # сам прибор: восемь мутантов
Код возврата: 0 — чисто, 1 — есть провал (у контроля — не поймал своего мутанта).
"""
import argparse
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TWO = re.compile(r"^[a-z]{2}$")
HTMLLANG = re.compile(r'<html[^>]*\blang="([^"]*)"', re.I)
CANON = re.compile(r'<link[^>]*rel="canonical"[^>]*href="([^"]*)"', re.I)
BLOCK = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
# Адрес кнопки «открыть бота» на самой странице — с ним сверяется url приложения.
TG_HREF = re.compile(r'href="(https://t\.me/[A-Za-z0-9_]+)(?:[^"]*)?"')
LEAKS = [
    (re.compile(r"\{[A-Za-z0-9_.\-]{1,30}\}"), "плейсхолдер {…}"),
    (re.compile(r"\bTODO\b|\bFIXME\b", re.I), "TODO/FIXME"),
    (re.compile(r"lorem\s+ipsum", re.I), "рыба"),
    (re.compile(r"/home/|localhost|\b127\.0\.0\.1\b"), "локальный путь или адрес"),
    (re.compile(r"http://"), "не-https адрес"),
]


class Probe:
    def __init__(self) -> None:
        self.checks = 0
        self.problems: list[str] = []

    def ok(self, cond: bool, msg: str) -> bool:
        self.checks += 1
        if not cond:
            self.problems.append(msg)
        return bool(cond)


def text_of(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def disallowed(root: Path) -> set:
    shut: set = set()
    for line in text_of(root / "robots.txt").splitlines():
        line = line.strip()
        if not line.lower().startswith("disallow:"):
            continue
        rest = line.split(":", 1)[1].strip().lstrip("/")
        if rest and "*" not in rest and "/" not in rest:
            shut.add(rest)
    return shut


def pages(root: Path) -> list:
    out: list = []
    shut = disallowed(root)
    if (root / "index.html").is_file():
        out.append(root / "index.html")
    out += sorted(p / "index.html" for p in root.iterdir()
                  if p.is_dir() and TWO.match(p.name) and (p / "index.html").is_file())
    out += sorted(p for p in root.iterdir()
                  if p.is_file() and p.suffix == ".html"
                  and p.name not in ("index.html", "404.html") and p.name not in shut)
    return out


def cards(root: Path) -> list:
    """Страницы-визитки: корень и языки. У них JSON-LD обязан быть."""
    out = [root / "index.html"] if (root / "index.html").is_file() else []
    out += sorted(p / "index.html" for p in root.iterdir()
                  if p.is_dir() and TWO.match(p.name) and (p / "index.html").is_file())
    return [p for p in out if p.is_file()]


def visible(text: str) -> str:
    body = re.sub(r"<script.*?</script>", " ", text, flags=re.S)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()


def norm(s) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(s or ""))).strip()


def rel_of(page: Path, root: Path) -> str:
    return str(page.relative_to(root))


def site_base(root: Path) -> str:
    """База сайта — из canonical корня, а не из констант сборки."""
    m = CANON.search(text_of(root / "index.html"))
    base = (m.group(1).strip() if m else "")
    if base and not base.endswith("/"):
        base += "/"
    return base


def prices(root: Path) -> dict:
    try:
        return json.loads(text_of(root / "tools" / "prices.json") or "{}")
    except json.JSONDecodeError:
        return {}


def expected_prices(p: dict) -> list:
    out = [0.0]
    for k in ("single",):
        if isinstance(p.get(k), (int, float)):
            out.append(float(p[k]))
    for k in ("pack5", "pack15"):
        v = p.get(k)
        if isinstance(v, dict) and isinstance(v.get("price"), (int, float)):
            out.append(float(v["price"]))
    return sorted(out)


def block_json(text: str) -> tuple:
    """(список узлов, список ошибок разбора) по всем блокам страницы."""
    nodes, bad = [], []
    for raw in BLOCK.findall(text):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            bad.append(f"JSON не разбирается: {e.msg} (строка {e.lineno})")
            continue
        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            nodes += [n for n in data["@graph"] if isinstance(n, dict)]
            bad += ([] if data.get("@context") else ["нет @context у блока с @graph"])
        elif isinstance(data, dict):
            nodes.append(data)
        elif isinstance(data, list):
            nodes += [n for n in data if isinstance(n, dict)]
        else:
            bad.append("блок не объект и не список")
    return nodes, bad


def one(nodes: list, typ: str):
    for n in nodes:
        t = n.get("@type")
        if t == typ or (isinstance(t, list) and typ in t):
            return n
    return None


def url_file(base: str, url: str) -> str:
    r = url[len(base):] if url.startswith(base) else ""
    if r == "" or r.endswith("/"):
        r += "index.html"
    return r


def scan(root: Path) -> dict:
    pr = Probe()
    base = site_base(root)
    pr.ok(bool(base), "LD корень: у index.html нет canonical — база сайта неизвестна")
    price = prices(root)
    want_prices = expected_prices(price)
    currency = str(price.get("currency") or "")
    pr.ok(bool(want_prices) and bool(currency),
          "OFFER tools/prices.json не прочитан или пуст — цены сверять не с чем")

    root_lang = ""
    m = HTMLLANG.search(text_of(root / "index.html"))
    if m and m.group(1):
        root_lang = m.group(1)
    langs = [root_lang] if root_lang else []
    langs += sorted(p.name for p in root.iterdir()
                    if p.is_dir() and TWO.match(p.name) and (p / "index.html").is_file())

    offer_sets: dict = {}
    for page in cards(root):
        rel = rel_of(page, root)
        text = text_of(page)
        nodes, bad = block_json(text)
        for b in bad:
            pr.ok(False, f"LD [{rel}] {b}")
        pr.ok(bool(BLOCK.findall(text)), f"LD [{rel}] нет блока application/ld+json")
        pr.ok(len(BLOCK.findall(text)) == 1,
              f"LD [{rel}] блоков {len(BLOCK.findall(text))}, ожидался один")
        for n in nodes:
            pr.ok(bool(n.get("@type")), f"LD [{rel}] узел без @type")
            pr.ok(bool(n.get("@id")), f"LD [{rel}] узел {n.get('@type')} без @id")
            pr.ok(str(n.get("@id", "")).startswith("http"),
                  f"LD [{rel}] @id не абсолютный у {n.get('@type')}: {n.get('@id')}")
        ids = [n.get("@id") for n in nodes if n.get("@id")]
        for i in ids:
            pr.ok(ids.count(i) == 1, f"LD [{rel}] @id повторяется: {i}")

        # ---- COVER ----
        pr.ok(len(nodes) == 4, f"COVER [{rel}] узлов {len(nodes)}, ожидалось 4")
        for typ in ("Organization", "WebSite", "SoftwareApplication", "FAQPage"):
            pr.ok(sum(1 for n in nodes if n.get("@type") == typ) == 1,
                  f"COVER [{rel}] узла {typ} нет или он не один")

        # ---- IDENT ----
        site = one(nodes, "WebSite") or {}
        org = one(nodes, "Organization") or {}
        app = one(nodes, "SoftwareApplication") or {}
        canon = (CANON.search(text).group(1).strip() if CANON.search(text) else "")
        pr.ok(canon.startswith(base), f"IDENT [{rel}] canonical вне сайта: {canon!r}")
        pr.ok(site.get("url") == canon,
              f"IDENT [{rel}] WebSite.url {site.get('url')!r} ≠ canonical {canon!r}")
        hl = (HTMLLANG.search(text).group(1) if HTMLLANG.search(text) else "")
        pr.ok(site.get("inLanguage") == hl,
              f"IDENT [{rel}] WebSite.inLanguage {site.get('inLanguage')!r} ≠ <html lang> {hl!r}")
        faq = one(nodes, "FAQPage") or {}
        pr.ok(faq.get("inLanguage") == hl,
              f"IDENT [{rel}] FAQPage.inLanguage {faq.get('inLanguage')!r} ≠ {hl!r}")
        app_langs = app.get("inLanguage")
        app_langs = sorted(app_langs) if isinstance(app_langs, list) else app_langs
        pr.ok(app_langs == sorted(langs),
              f"IDENT [{rel}] SoftwareApplication.inLanguage {app.get('inLanguage')!r} ≠ языки сайта {langs!r}")
        pub = site.get("publisher")
        pub_id = pub.get("@id") if isinstance(pub, dict) else (pub or "")
        pr.ok(pub_id == org.get("@id"),
              f"IDENT [{rel}] publisher {pub_id!r} не указывает на Organization {org.get('@id')!r}")
        pr.ok(org.get("url") == base,
              f"IDENT [{rel}] Organization.url {org.get('url')!r} ≠ корень {base!r}")
        logo = str(org.get("logo") or "")
        pr.ok(logo.startswith(base) and (root / url_file(base, logo)).is_file(),
              f"IDENT [{rel}] logo {logo!r} — файла нет на диске")
        cta = set(TG_HREF.findall(text))
        pr.ok(bool(cta), f"IDENT [{rel}] на странице нет ни одной кнопки t.me — сверять app.url не с чем")
        pr.ok(str(app.get("url") or "") in cta,
              f"IDENT [{rel}] app.url {app.get('url')!r} не совпадает с кнопкой страницы {sorted(cta)!r}")

        # ---- OFFER ----
        offers = app.get("offers")
        offers = offers if isinstance(offers, list) else ([offers] if isinstance(offers, dict) else [])
        pr.ok(len(offers) == 4, f"OFFER [{rel}] предложений {len(offers)}, ожидалось 4")
        got = []
        for off in offers:
            if not isinstance(off, dict):
                pr.ok(False, f"OFFER [{rel}] предложение не объект: {off!r}")
                continue
            pr.ok(off.get("@type") == "Offer", f"OFFER [{rel}] @type {off.get('@type')!r} вместо Offer")
            pr.ok(bool(norm(off.get("name"))), f"OFFER [{rel}] предложение без названия")
            raw = off.get("price")
            pr.ok(isinstance(raw, str) and re.fullmatch(r"\d+(\.\d{1,2})?", str(raw)) is not None,
                  f"OFFER [{rel}] цена не число строкой: {raw!r}")
            pr.ok(off.get("priceCurrency") == currency,
                  f"OFFER [{rel}] валюта {off.get('priceCurrency')!r} ≠ {currency!r} из prices.json")
            try:
                got.append(float(raw))
            except (TypeError, ValueError):
                pass
        pr.ok(sorted(got) == want_prices,
              f"OFFER [{rel}] цены {sorted(got)} ≠ {want_prices} из prices.json")
        pr.ok(len(set(got)) == len(got), f"OFFER [{rel}] две цены совпадают: {sorted(got)}")
        offer_sets[rel] = sorted(got)

        # ---- FAQ ----
        ent = faq.get("mainEntity")
        ent = ent if isinstance(ent, list) else []
        pr.ok(bool(ent), f"FAQ [{rel}] mainEntity пуст")
        vis = visible(text)
        names: list = []
        for item in ent:
            if not isinstance(item, dict):
                pr.ok(False, f"FAQ [{rel}] вопрос не объект: {item!r}")
                continue
            pr.ok(item.get("@type") == "Question", f"FAQ [{rel}] @type {item.get('@type')!r} вместо Question")
            q = norm(item.get("name"))
            ans = item.get("acceptedAnswer")
            ans = ans if isinstance(ans, dict) else {}
            a = norm(ans.get("text"))
            pr.ok(bool(q), f"FAQ [{rel}] вопрос без текста")
            pr.ok(ans.get("@type") == "Answer", f"FAQ [{rel}] ответ без @type Answer у «{q[:40]}»")
            pr.ok(len(a) >= 20, f"FAQ [{rel}] ответ короче 20 знаков у «{q[:40]}»")
            pr.ok(q and q in vis, f"FAQ [{rel}] вопрос {q[:60]!r} не виден на странице")
            pr.ok(a and a in vis, f"FAQ [{rel}] ответ к «{q[:40]}» не виден на странице")
            names.append(q)
        for q in names:
            pr.ok(names.count(q) == 1, f"FAQ [{rel}] вопрос повторяется: {q[:60]!r}")

        # ---- LEAK ----
        raw_block = " ".join(BLOCK.findall(text))
        for rx, what in LEAKS:
            m = rx.search(raw_block)
            pr.ok(m is None, f"LEAK [{rel}] в JSON-LD {what}: {m.group(0) if m else ''}")

    # цены обязаны быть одни и те же на всех языках
    uniq = {tuple(v) for v in offer_sets.values()}
    pr.ok(len(uniq) <= 1,
          f"OFFER цены разъехались по языкам: { {k: v for k, v in offer_sets.items()} }")

    # страницы без визитки (privacy, terms): блока может не быть, но если есть — он обязан быть чистым
    for page in pages(root):
        if page in cards(root):
            continue
        rel = rel_of(page, root)
        nodes, bad = block_json(text_of(page))
        for b in bad:
            pr.ok(False, f"LD [{rel}] {b}")
        for n in nodes:
            pr.ok(bool(n.get("@type")) and bool(n.get("@id")),
                  f"LD [{rel}] узел без @type или @id")

    return {"c": {"checks": pr.checks, "fails": len(pr.problems),
                  "pages": len(cards(root)), "langs": len(langs)},
            "problems": pr.problems, "offers": offer_sets}


def report(res: dict) -> int:
    c = res["c"]
    print(f"страниц: {c['pages']}  языков: {c['langs']}  проверок: {c['checks']}")
    for prob in res["problems"][:30]:
        print("  " + prob)
    if len(res["problems"]) > 30:
        print(f"  ... ещё {len(res['problems']) - 30}")
    print(f"CHECKS: {c['checks']}, FAILED: {c['fails']}")
    return 1 if c["fails"] else 0


# ---- контроль прибора: восемь мутантов на копии дерева --------------------

def _copy(root: Path, dst: Path) -> None:
    for f in cards(root):
        t = dst / f.relative_to(root)
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, t)
    (dst / "tools").mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "tools" / "prices.json", dst / "tools" / "prices.json")
    (dst / "robots.txt").write_text(text_of(root / "robots.txt"), encoding="utf-8")


def control(root: Path) -> int:
    caught: list = []
    src = cards(root)[0]
    original = text_of(src)

    def leg(name: str, tag: str, fn) -> None:
        d = Path(tempfile.mkdtemp(prefix="jsonld-ctl-"))
        try:
            _copy(root, d)
            page = d / src.relative_to(root)
            new = fn(original)
            if new == original:
                raise SystemExit(f"контроль: мутант «{name}» не поставился — шаблон не совпал")
            page.write_text(new, encoding="utf-8")
            probs = scan(d)["problems"]
            caught.append((name, any(x.startswith(tag) for x in probs)))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def sub_once(a: str, b: str):
        def f(text: str) -> str:
            return text.replace(a, b, 1)
        return f

    def wrong_currency(text: str) -> str:
        m = re.search(r'"priceCurrency":\s*"([A-Z]{3})"', text)
        return text.replace(m.group(1), "USD", 1) if m else text
    def q_invisible(text: str) -> str:
        i = text.find('"FAQPage"')
        m = re.search(r'"name":\s*"([^"]{8,})"', text[i:]) if i >= 0 else None
        if not m:
            return text
        return text[:i + m.start(1)] + "Вопрос, которого нет на странице" + text[i + m.end(1):]

    def drop_org(text: str) -> str:
        return text.replace('"@type": "Organization"', '"@type": "NotAnOrganization"', 1)

    def dangling(text: str) -> str:
        m = re.search(r'"@id":\s*"([^"]*#org)"', text)
        return text.replace(m.group(1), m.group(1).replace("#org", "#nobody"), 1) if m else text

    leg("битый JSON", "LD", sub_once('"@context": "https://schema.org"',
                                     '"@context": "https://schema.org",,,'))
    leg("цена разошлась с prices.json", "OFFER", sub_once('"price": "30"', '"price": "35"'))
    leg("чужой язык страницы", "IDENT", sub_once('"inLanguage": "en"', '"inLanguage": "de"'))
    leg("WebSite.url не canonical", "IDENT", _webs_url)
    leg("вопрос не виден на странице", "FAQ", q_invisible)
    leg("висячий publisher", "IDENT", dangling)
    leg("нет узла Organization", "COVER", drop_org)
    leg("чужая валюта", "OFFER", wrong_currency)

    good = sum(1 for _, ok in caught if ok)
    print("КОНТРОЛЬ: " + "  ".join(f"{n} — {'поймал' if ok else 'ПРОСМОТРЕЛ'}"
                                   for n, ok in caught))
    print(f"поймал {good} из {len(caught)}")
    return 0 if good == len(caught) else 1


def _webs_url(text: str) -> str:
    """WebSite.url увести на чужую страницу: правим второе вхождение url корня."""
    m = re.search(r'"@type": "WebSite".{0,400}?"url": "([^"]+)"', text, re.S)
    if not m:
        return text
    return text[:m.start(1)] + m.group(1).rstrip("/") + "/ru/" + text[m.end(1):]


def main() -> int:
    ap = argparse.ArgumentParser(description="JSON-LD: синтаксис, покрытие, личность, цены, вопросы, утечки")
    ap.add_argument("--control", action="store_true", help="проверить сам прибор на восьми мутантах")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", metavar="PATH", help="машинный отчёт в файл")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if args.control:
        return control(root)
    res = scan(root)
    if args.json:
        p = Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report(res)


if __name__ == "__main__":
    sys.exit(main())
