#!/usr/bin/env python3
"""ИИ-слой страницы: llms.txt и md-двойники — то, что читает ассистент, а не человек.

Зачем. Двадцать блоков держали HTML: разметку, ссылки, цены, доступность, форму,
JSON-LD. Рядом с каждой страницей с 22.10 лежит вторая её версия — `index.html.md`,
а в корне `llms.txt` со списком всех девяти. Этот слой читают не люди, а
ассистенты и агенты: они цитируют цену, ответ FAQ и обещание «первые 2 разбора
бесплатно» из markdown, а не из вёрстки. Проверял его только `build` — то есть
сборка сверялась сама с собой: файл собрался, значит цел.

Двойник может разойтись со страницей молча: секция на странице есть, в md её
нет; цена в карточке 120, в md 125; ответ FAQ переписали на странице, а
конвертер собрал из старого словаря. Глазу это не видно — md не открывают.

Что держит (классы, свой тег в отчёте):

  MISS  — двойник есть у каждой страницы, страница есть у каждого двойника.
  TITLE — первый заголовок двойника равен <title> своей страницы.
  SECT  — ни одна секция страницы не потеряна в двойнике и ни одна не выдумана.
  ORDER — порядок секций двойника тот же, что на странице: ИИ пересказывает
          страницу в том порядке, в каком её прочитал.
  PRICE — три карточки цен (название, сумма, пояснение) и строка про одиночный
          разбор лежат в двойнике дословно.
  FAQ   — каждый вопрос и КАЖДЫЙ ответ FAQ страницы есть в двойнике дословно,
          и наоборот: вопроса, которого нет на странице, в двойнике быть не
          может — ответ, которого нет на странице, ассистент процитирует как наш.
  MEDIA — двойник ссылается на ролик и кадры СВОЕГО языка и на те же файлы,
          что стоят на странице (EN-фолбэка у языка быть не должно).
  LINK  — каждая ссылка двойника ведёт на файл, который лежит в дереве, якорь
          существует, а ссылка на бота несёт метку источника (start=).
  LLMS  — llms.txt перечисляет все девять двойников, оба legal-двойника и
          ролики, и все его адреса резолвятся в файлы дерева.
  LEGAL — ни один заголовок privacy/terms не потерян при конвертации в md.

Ожидания берутся из дерева (страницы, их заголовки, карточки, FAQ) и из
llms.txt, а не из констант build.py: прибор обязан спорить со сборкой.

Запуск:
  python3 tools/check-ai-layer.py            # проверка дерева
  python3 tools/check-ai-layer.py --control  # сам прибор: девять мутантов
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
BASE = "https://kerio-byte.github.io/uchisambot/"
BOT_PREFIX = "https://t.me/UchiSamBot"

CODES = {
    "MISS": "двойник или страница отсутствует",
    "TITLE": "заголовок двойника не равен <title> страницы",
    "SECT": "состав секций разошёлся",
    "ORDER": "порядок секций разошёлся",
    "PRICE": "цена в двойнике не та, что в карточке",
    "FAQ": "вопрос или ответ FAQ разошёлся",
    "MEDIA": "ролик или кадры чужого языка / не те файлы",
    "LINK": "ссылка двойника никуда не ведёт",
    "LLMS": "llms.txt неполон или ведёт в пустоту",
    "LEGAL": "заголовок legal-страницы потерян в md",
}


def norm(s: str) -> str:
    """Текст для сравнения: без тегов, сущностей, лишних пробелов и markdown-выделения."""
    s = re.sub(r"<[^>]+>", "", s)
    s = unescape(s).replace("**", "").replace("__", "")
    return re.sub(r"\s+", " ", s).strip()


class _Page(HTMLParser):
    """Заголовки, <title> и id страницы — то, с чем сверяется двойник."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.heads: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.title = ""
        self._tag: str | None = None
        self._buf: list[str] = []
        self._in_title = False
        self._tbuf: list[str] = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id" and v:
                self.ids.add(v)
        if tag in ("h1", "h2", "h3"):
            self._tag, self._buf = tag, []
        elif tag == "title":
            self._in_title, self._tbuf = True, []

    def handle_endtag(self, tag):
        if self._tag == tag:
            self.heads.append((tag, norm("".join(self._buf))))
            self._tag = None
        elif tag == "title" and self._in_title:
            self.title = norm("".join(self._tbuf))
            self._in_title = False

    def handle_data(self, data):
        if self._tag:
            self._buf.append(data)
        if self._in_title:
            self._tbuf.append(data)


def page_facts(html: str) -> dict:
    p = _Page()
    p.feed(html)
    h2 = [t for tag, t in p.heads if tag == "h2"]
    cards = []
    for m in re.finditer(
        r'<div class="card price[^"]*">\s*<h3>(.*?)</h3>\s*'
        r'<div class="amount">(.*?)</div>\s*<p>(.*?)</p>', html, re.S):
        cards.append(tuple(norm(x) for x in m.groups()))
    fine = re.search(r'<p class="price-fine">(.*?)</p>', html, re.S)
    faq_block = ""
    sec = re.search(r'<section[^>]*id="faq".*?</section>', html, re.S)
    if sec:
        faq_block = sec.group(0)
    faq = [(norm(q), norm(a)) for q, a in
           re.findall(r'<summary>(.*?)</summary>\s*<p>(.*?)</p>', faq_block, re.S)]
    shots = re.findall(r'src="((?:\.\./)?img/shot[^"]+)"', html)
    video = re.search(r'src="((?:\.\./)?demo/[^"]+\.mp4)"', html)
    return {"title": p.title, "h2": h2, "ids": p.ids, "cards": cards,
            "heads": p.heads,
            "fine": norm(fine.group(1)) if fine else "",
            "faq": faq, "shots": shots,
            "video": video.group(1) if video else ""}


def md_facts(md: str) -> dict:
    lines = md.splitlines()
    h1 = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), "")
    h2 = [ln[3:].strip() for ln in lines if ln.startswith("## ")]
    h3 = [ln[4:].strip() for ln in lines if ln.startswith("### ")]
    links = [(m.group(1), m.group(2)) for m in
             re.finditer(r"!?\[([^\]]*)\]\(([^)\s]+)\)", md)]
    imgs = [m.group(1) for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)\)", md)]
    return {"h1": norm(h1), "h2": [norm(x) for x in h2],
            "h3": [norm(x) for x in h3], "links": links, "imgs": imgs,
            "text": norm(md)}


def resolve(url: str, root: Path) -> Path | None:
    """Адрес двойника → путь в дереве. None, если адрес не наш."""
    if url.startswith(BASE):
        rel = url[len(BASE):]
    elif url.startswith("/"):
        rel = url[1:]
    elif "://" in url:
        return None
    else:
        rel = url
    rel = rel.split("#")[0].split("?")[0]
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return root / rel


def scan(root: Path) -> list[dict]:
    bad: list[dict] = []
    checks = 0

    def fail(code: str, where: str, msg: str) -> None:
        bad.append({"code": code, "where": where, "msg": msg})

    facts = {}
    for lang in LANGS:
        d = root if lang == "en" else root / lang
        page_p, md_p = d / "index.html", d / "index.html.md"
        checks += 1
        if not page_p.exists() or not md_p.exists():
            fail("MISS", lang, f"нет {'страницы' if not page_p.exists() else 'двойника'}")
            continue
        page = page_facts(page_p.read_text(encoding="utf-8"))
        md = md_facts(md_p.read_text(encoding="utf-8"))
        facts[lang] = (page, md)

        checks += 1
        if md["h1"] != page["title"]:
            fail("TITLE", lang, f"двойник «{md['h1'][:70]}» ≠ <title> «{page['title'][:70]}»")

        checks += 1
        lost = [h for h in page["h2"] if h not in md["h2"]]
        extra = [h for h in md["h2"] if h not in page["h2"]]
        if lost or extra:
            fail("SECT", lang, f"потеряно {lost} выдумано {extra}".strip())
        elif md["h2"] != page["h2"]:
            i = next(i for i, (a, b) in enumerate(zip(page["h2"], md["h2"])) if a != b)
            fail("ORDER", lang, f"позиция {i + 1}: страница «{page['h2'][i][:40]}», "
                                f"двойник «{md['h2'][i][:40]}»")

        checks += 1
        miss = [c for c in page["cards"]
                if f"{c[0]} — {c[1]}" not in md["text"] or c[2] not in md["text"]]
        if page["fine"] and page["fine"] not in md["text"]:
            miss.append(("строка про одиночный разбор", page["fine"][:40], ""))
        if miss:
            fail("PRICE", lang, f"нет в двойнике: {[m[0] for m in miss]}")

        checks += 1
        if not page["faq"]:
            fail("FAQ", lang, "на странице не найден FAQ — прибору нечего сверять")
        for q, a in page["faq"]:
            if q not in md["h3"]:
                fail("FAQ", lang, f"вопроса нет в двойнике: «{q[:50]}»")
            elif a not in md["text"]:
                fail("FAQ", lang, f"ответ разошёлся: «{q[:50]}»")
        page_q = {q for q, _ in page["faq"]}
        for q in md["h3"]:
            if q not in page_q:
                fail("FAQ", lang, f"вопрос есть в двойнике, но не на странице: «{q[:50]}»")

        checks += 1
        demo = [u for _, u in md["links"] if "demo/" in u and u.endswith(".mp4")]
        want = page["video"].split("/")[-1]
        if not demo:
            fail("MEDIA", lang, "в двойнике нет ссылки на ролик")
        elif demo[0].split("/")[-1] != want:
            fail("MEDIA", lang, f"ролик двойника {demo[0].split('/')[-1]} ≠ страницы {want}")
        md_shots = [u.split("/")[-1] for u in md["imgs"] if "/img/shot" in u]
        page_shots = [u.split("/")[-1] for u in page["shots"]]
        if md_shots != page_shots:
            fail("MEDIA", lang, f"кадры двойника {md_shots} ≠ страницы {page_shots}")

        checks += 1
        for text, url in md["links"]:
            if url.startswith(BOT_PREFIX):
                checks += 1
                if "start=" not in url:
                    fail("LINK", lang, f"ссылка на бота без метки источника: {url}")
                continue
            target = resolve(url, root)
            if target is None:
                fail("LINK", lang, f"чужой адрес в ИИ-слое: {url}")
                continue
            checks += 1
            if not target.exists():
                fail("LINK", lang, f"нет файла: {url}")
        ids_cache = {lang: facts[lang][0]["ids"]}

        def ids_of(path: Path) -> set[str]:
            key = str(path)
            if key not in ids_cache:
                ids_cache[key] = (page_facts(path.read_text(encoding="utf-8"))["ids"]
                                  if path.exists() else set())
            return ids_cache[key]

        for text, url in md["links"]:
            if "#" not in url:
                continue
            frag = url.split("#", 1)[1]
            if not frag:
                continue
            checks += 1
            if "://" in url and not url.startswith(BASE):
                continue
            tgt = resolve(url, root)
            if tgt is not None and frag not in ids_of(tgt):
                fail("LINK", lang, f"якоря #{frag} нет в {tgt.name}")

    # llms.txt
    llms_p = root / "llms.txt"
    checks += 1
    if not llms_p.exists():
        fail("LLMS", "llms.txt", "файла нет")
    else:
        llms = llms_p.read_text(encoding="utf-8")
        for lang in LANGS:
            checks += 1
            url = BASE + ("index.html.md" if lang == "en" else f"{lang}/index.html.md")
            n = llms.count(url)
            if n != 1:
                fail("LLMS", lang, f"двойник в llms.txt упомянут {n} раз(а), нужно 1")
            else:
                t = resolve(url, root)
                if t is None or not t.exists():
                    fail("LLMS", lang, f"двойник не собран: {url}")
        for name in ("privacy.html.md", "terms.html.md"):
            checks += 1
            if llms.count(BASE + name) != 1:
                fail("LLMS", name, "legal-двойник не упомянут ровно один раз")
        bot_urls = re.findall(re.escape(BOT_PREFIX) + r'[^\s)\]>]*', llms)
        checks += 1
        if not bot_urls:
            fail("LLMS", "bot", "в llms.txt нет ссылки на бота")
        elif not any("start=" in u for u in bot_urls):
            fail("LLMS", "bot", "ссылка на бота без метки источника (start=)")
        for url in [u for _, u in re.findall(r"\[([^\]]*)\]\(([^)\s]+)\)", llms)]:
            if not url.startswith(("http://", "https://")):
                continue
            if url.startswith(BOT_PREFIX):
                continue
            checks += 1
            t = resolve(url, root)
            if t is None:
                fail("LLMS", "чужой", f"посторонний адрес: {url}")
            elif not t.exists():
                fail("LLMS", "llms.txt", f"нет файла: {url}")

    # legal-двойники
    for name in ("privacy", "terms"):
        hp, mp = root / f"{name}.html", root / f"{name}.html.md"
        checks += 1
        if not hp.exists() or not mp.exists():
            fail("MISS", name, "нет страницы или двойника")
            continue
        page = page_facts(hp.read_text(encoding="utf-8"))
        md = md_facts(mp.read_text(encoding="utf-8"))
        checks += 1
        lost = [t for tag, t in page["heads"] if tag in ("h2", "h3")
                and t not in md["h2"] + md["h3"]]
        if lost:
            fail("LEGAL", name, f"заголовков нет в md: {lost[:4]}")

    return [{"checks": checks, "bad": bad}]


def report(res: list[dict]) -> int:
    r = res[0]
    bad = r["bad"]
    by: dict[str, list[dict]] = {}
    for b in bad:
        by.setdefault(b["code"], []).append(b)
    for code, desc in CODES.items():
        got = by.get(code, [])
        print(f"{code:5} {desc:52} {'OK' if not got else str(len(got)) + ' пробл.'}")
    for b in bad[:30]:
        print(f"  [{b['code']}] {b['where']}: {b['msg']}")
    if len(bad) > 30:
        print(f"  … и ещё {len(bad) - 30}")
    print(f"ИТОГ: {r['checks']} проверок, {len(bad)} проблем")
    return 0 if not bad else 1


def _setup(tmp: Path) -> Path:
    """Копия того, что прибор читает, плюс пустышки вместо медиа: контроль
    проверяет резолв ссылок, а не байты роликов (байты держит live-bytes)."""
    base = tmp / "base"
    base.mkdir(parents=True)
    for name in ("llms.txt", "privacy.html", "privacy.html.md", "terms.html", "terms.html.md"):
        shutil.copy2(ROOT / name, base / name)
    shutil.copy2(ROOT / "index.html", base / "index.html")
    shutil.copy2(ROOT / "index.html.md", base / "index.html.md")
    for lang in LANGS[1:]:
        (base / lang).mkdir()
        shutil.copy2(ROOT / lang / "index.html", base / lang / "index.html")
        shutil.copy2(ROOT / lang / "index.html.md", base / lang / "index.html.md")
    # пустышки для всех наших целей — кроме тех, что уже скопированы
    for p in list(base.rglob("*.md")) + [base / "llms.txt"]:
        txt = p.read_text(encoding="utf-8")
        for url in re.findall(r"\]\(([^)\s]+)\)", txt):
            if url.startswith(BOT_PREFIX) or "://" in url and not url.startswith(BASE):
                continue
            t = resolve(url, base)
            if t and not t.exists():
                t.parent.mkdir(parents=True, exist_ok=True)
                t.write_bytes(b"")
    return base


def control() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ai-layer-"))
    try:
        base = _setup(tmp)
        clean = scan(base)[0]["bad"]
        print(f"чистая копия: {len(clean)} проблем" + ("" if not clean else f" — {clean[0]}"))

        def mutate(name: str, code: str, fn, label: str | None = None) -> tuple[str, bool]:
            m = tmp / ("mut-" + code + "-" + str(len(list(tmp.iterdir()))))
            shutil.copytree(base, m)
            p = m / name
            txt = p.read_text(encoding="utf-8")
            new = fn(txt)
            if new == txt:
                print(f"  мутант «{code}» не применился — проверь шаблон")
                return code, False
            p.write_text(new, encoding="utf-8")
            got = {b["code"] for b in scan(m)[0]["bad"]}
            return label or code, code in got

        def drop_price(t: str) -> str:
            return t.replace("120 Stars", "125 Stars", 1)

        def drop_sect(t: str) -> str:
            return re.sub(r"\n## [^\n]+\n", "\n", t, count=1)

        def swap_two(t: str) -> str:
            lines = t.splitlines()
            idx = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
            if len(idx) < 2:
                return t
            a, b = idx[0], idx[1]
            lines[a], lines[b] = lines[b], lines[a]
            return "\n".join(lines) + "\n"

        def en_media(t: str) -> str:
            return re.sub(r"-es\.mp4", ".mp4", t, count=1)

        def break_link(t: str) -> str:
            return t.replace("](https://kerio-byte.github.io/uchisambot/privacy.html",
                             "](https://kerio-byte.github.io/uchisambot/privacy-gone.html", 1)

        def break_faq(t: str) -> str:
            m = re.search(r"^### .+$", t, re.M)
            if not m:
                return t
            return t[:m.end()] + " подмена" + t[m.end():]

        def drop_llms(t: str) -> str:
            return re.sub(r"\n- \[Українська[^\n]*\n", "\n", t, count=1)

        def phantom_faq(t: str) -> str:
            return t + "\n### Чи можна скасувати покупку?\n\nНі.\n"

        def drop_legal(t: str) -> str:
            return re.sub(r"\n## [^\n]+\n", "\n", t, count=1)

        caught = [
            mutate("index.html.md", "PRICE", drop_price),
            mutate("es/index.html.md", "SECT", drop_sect),
            mutate("id/index.html.md", "ORDER", swap_two),
            mutate("es/index.html.md", "MEDIA", en_media),
            mutate("vi/index.html.md", "LINK", break_link),
            mutate("tr/index.html.md", "FAQ", break_faq),
            mutate("llms.txt", "LLMS", drop_llms),
            mutate("uk/index.html.md", "FAQ", phantom_faq, "FAQ-фантом"),
            mutate("privacy.html.md", "LEGAL", drop_legal),
        ]
        ok = sum(1 for _, hit in caught if hit)
        print("КОНТРОЛЬ: " + "  ".join(f"{c} — {'поймал' if h else 'ПРОСМОТРЕЛ'}"
                                       for c, h in caught))
        print(f"поймал {ok} из {len(caught)}")
        green = 0 if not clean else 1
        return 0 if ok == len(caught) and not clean else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="ИИ-слой: llms.txt и md-двойники против страниц")
    ap.add_argument("--control", action="store_true", help="проверить сам прибор на девяти мутантах")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", metavar="PATH", help="машинный отчёт в файл")
    args = ap.parse_args()
    if args.control:
        return control()
    res = scan(Path(args.root).resolve())
    if args.json:
        p = Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report(res)


if __name__ == "__main__":
    sys.exit(main())
