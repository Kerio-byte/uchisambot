#!/usr/bin/env python3
"""check-sitemap.py — sitemap.xml как данные, а не как файл.

Read-only. Пять классов:
  1) COVER — набор <loc> против дерева: пропавшая страница, лишний адрес, дубль;
  2) FILE  — каждый <loc> указывает на существующий файл (каталог -> index.html);
  3) ALTS  — у каждой языковой страницы ровно свой набор alternate (все языки +
     x-default), все href — среди <loc>, и набор одинаков у всех страниц;
  4) DATE  — lastmod: формат YYYY-MM-DD, не из будущего, совпадает с реестром
     tools/lastmod.json (и в реестре нет адресов, которых нет в sitemap);
  5) PAGE  — страница по адресу сама называет себя canonical и объявляет тот же
     набор alternate, что и sitemap.

До 31.10.2026 sitemap проверялся только двумя способами: «живые байты == байты
в дереве» (`check-site-technical.py`) и обходом всех адресов из него
(`check-links.py`). Оба смотрят на то, что в sitemap ЕСТЬ. Ни один прибор не
видел ПРОПУСК: страница на диске лежит, в sitemap её нет — прогон зелёный, и
поисковик о ней не узнает. Никто не видел и lastmod, который врёт: сборка
верит `tools/lastmod.json`, а правится реестр руками — дата «контент изменился»
могла стоять над неизменной страницей, и это было неотличимо от правды.

Ожидание выводится из дерева, а не из констант `build.py`: язык по умолчанию —
из `<html lang>` корня, языки — из каталогов с `index.html`, прочие страницы —
корневые `.html` кроме `index.html` и `404.html` (странице ошибки в sitemap не
место). Поэтому прибор спорит со сборкой, а не повторяет её.

  python3 tools/check-sitemap.py
  python3 tools/check-sitemap.py --control    # сам прибор: обязан покраснеть
  python3 tools/check-sitemap.py --root DIR   # проверять копию дерева
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = Path("tools") / "lastmod.json"

TWO = re.compile(r"^[a-z]{2}$")
BLOCK = re.compile(r"<url>(.*?)</url>", re.S)
LOC = re.compile(r"<loc>([^<]+)</loc>")
LASTMOD = re.compile(r"<lastmod>([^<]*)</lastmod>")
XALT = re.compile(r'<xhtml:link\s+rel="alternate"\s+hreflang="([^"]+)"\s+href="([^"]+)"\s*/?>')
CANON = re.compile(r'<link rel="canonical" href="([^"]+)"')
ALT = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"')
HTMLLANG = re.compile(r'<html[^>]*\blang="([^"]+)"')
STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA = re.compile(r"^[0-9a-f]{64}$")


class Probe:
    """Счётчик проверок и список проблем: класс всегда первым словом."""

    def __init__(self) -> None:
        self.checks = 0
        self.problems: list[str] = []

    def ok(self, cond: bool, msg: str) -> bool:
        self.checks += 1
        if not cond:
            self.problems.append(msg)
        return cond


def text_of(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def shape(root: Path) -> dict:
    """Что дерево обещает: база, язык по умолчанию, языки, прочие страницы."""
    head = text_of(root / "index.html")
    m = HTMLLANG.search(head)
    default = (m.group(1).strip().lower() if m else "")
    base = ""
    c = CANON.search(head)
    if c:
        base = c.group(1).strip()
    langs = sorted(d.name for d in root.iterdir()
                   if d.is_dir() and TWO.match(d.name) and (d / "index.html").exists())
    # Корневой .html — страница сайта, кроме страницы ошибки и того, что
    # robots.txt запрещает читать: `index-src.html` — исходник мастерской,
    # его в sitemap не зовут (31.10.2026 прибор честно на этом покраснел).
    shut = disallowed(root)
    others = sorted(p.name for p in root.iterdir()
                    if p.is_file() and p.suffix == ".html"
                    and p.name not in ("index.html", "404.html")
                    and p.name not in shut)
    return {"base": base, "default": default, "langs": langs, "others": others,
            "shut": shut}


def disallowed(root: Path) -> set[str]:
    """Корневые имена файлов, которые robots.txt велит краулеру не читать."""
    shut: set[str] = set()
    for line in text_of(root / "robots.txt").splitlines():
        line = line.strip()
        if not line.lower().startswith("disallow:"):
            continue
        path = line.split(":", 1)[1].strip()
        rest = path.lstrip("/")
        if rest and "*" not in rest and "/" not in rest:
            shut.add(rest)
    return shut


def url_for(shape_: dict, code: str) -> str:
    base = shape_["base"]
    return base if code == shape_["default"] else f"{base}{code}/"


def path_of(root: Path, base: str, loc: str) -> Path | None:
    if not loc.startswith(base):
        return None
    rest = loc[len(base):]
    if ".." in rest or rest.startswith("//"):
        return None
    if rest == "":
        return root / "index.html"
    if rest.endswith("/"):
        return root / rest / "index.html"
    return root / rest


def parse(text: str) -> list[dict]:
    out = []
    for block in BLOCK.findall(text):
        loc = LOC.search(block)
        lm = LASTMOD.search(block)
        out.append({
            "loc": loc.group(1).strip() if loc else "",
            "lastmod": lm.group(1).strip() if lm else "",
            "alts": [(h.strip(), u.strip()) for h, u in XALT.findall(block)],
        })
    return out


def registry(root: Path) -> dict:
    try:
        data = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def scan(root: Path) -> dict:
    p = Probe()
    sh = shape(root)
    today = date.today()
    stext = text_of(root / "sitemap.xml")
    reg = registry(root)

    if not stext:
        p.ok(False, "FILE sitemap.xml отсутствует или пуст")
        return {"c": {"checks": p.checks, "fails": 1}, "problems": p.problems}
    if not sh["base"] or not sh["default"]:
        p.ok(False, "COVER не удалось прочитать базу/язык из корневой страницы")
        return {"c": {"checks": p.checks, "fails": 1}, "problems": p.problems}

    entries = parse(stext)
    locs = [e["loc"] for e in entries]
    lang_urls = [url_for(sh, c) for c in [sh["default"]] + sh["langs"]]
    expected = lang_urls + [f"{sh['base']}{o}" for o in sh["others"]]

    # 1) COVER — набор адресов
    p.ok(len(entries) > 0, "COVER sitemap без единого <url>")
    for u in expected:
        p.ok(u in locs, f"COVER нет адреса {u} (страница на диске есть)")
    for u in locs:
        p.ok(u in expected, f"COVER лишний адрес {u} (страницы нет в дереве)")
    dupes = {u for u in locs if locs.count(u) > 1}
    p.ok(not dupes, f"COVER дубли адресов: {', '.join(sorted(dupes))}")
    # Адрес, который robots.txt запрещает читать, в sitemap звать нельзя:
    # краулер получит запрет на то, что ему только что предложили.
    for u in locs:
        rel = u[len(sh["base"]):] if u.startswith(sh["base"]) else u
        p.ok(rel not in sh["shut"],
             f"COVER {u}: robots.txt запрещает читать этот адрес")

    # 2) FILE — каждый адрес ведёт на файл
    for e in entries:
        f = path_of(root, sh["base"], e["loc"])
        p.ok(f is not None and f.is_file(),
             f"FILE {e['loc']}: файла нет по адресу ({f.name if f else 'вне базы'})")

    # 3) ALTS — alternate у языковых страниц
    codes = [sh["default"]] + sh["langs"]
    want = {c: url_for(sh, c) for c in codes}
    want["x-default"] = sh["base"]
    seen_sets: dict[str, str] = {}
    for e in entries:
        alts = dict(e["alts"])
        if e["loc"] in lang_urls:
            p.ok(set(alts) == set(want),
                 f"ALTS {e['loc']}: набор alternate {sorted(alts)} вместо {sorted(want)}")
            for code, href in sorted(alts.items()):
                p.ok(want.get(code) == href,
                     f"ALTS {e['loc']}: {code} -> {href}, ждали {want.get(code, '—')}")
                p.ok(href in locs, f"ALTS {e['loc']}: {code} -> {href}, адреса нет среди <loc>")
            seen_sets[e["loc"]] = json.dumps(sorted(alts.items()), ensure_ascii=False)
            p.ok(len(e["alts"]) == len(alts),
                 f"ALTS {e['loc']}: повтор языка в alternate")
        else:
            p.ok(not alts, f"ALTS {e['loc']}: alternate у непереводимой страницы")
    p.ok(len(set(seen_sets.values())) <= 1,
         "ALTS наборы alternate разъезжаются между языковыми страницами")

    # 4) DATE — lastmod и реестр
    for e in entries:
        lm = e["lastmod"]
        if not p.ok(bool(STAMP.match(lm)), f"DATE {e['loc']}: lastmod «{lm}» не YYYY-MM-DD"):
            continue
        try:
            d = date.fromisoformat(lm)
        except ValueError:
            p.ok(False, f"DATE {e['loc']}: lastmod «{lm}» не дата")
            continue
        p.ok(d <= today, f"DATE {e['loc']}: lastmod {lm} из будущего (сегодня {today})")
        rec = reg.get(e["loc"]) or {}
        p.ok(rec.get("date") == lm,
             f"DATE {e['loc']}: lastmod {lm}, а реестр {rec.get('date', '—')}")
        p.ok(bool(SHA.match(str(rec.get("sha", "")))),
             f"DATE {e['loc']}: в реестре нет отпечатка sha")
    for u in reg:
        p.ok(u in locs, f"DATE реестр помнит {u}, а в sitemap его нет")

    # 5) PAGE — страница сама называет себя
    for e in entries:
        f = path_of(root, sh["base"], e["loc"])
        if f is None or not f.is_file():
            continue
        page = text_of(f)
        cm = CANON.search(page)
        p.ok(cm is not None and cm.group(1).strip() == e["loc"],
             f"PAGE {e['loc']}: canonical "
             f"{(cm.group(1).strip() if cm else '—')}")
        if e["loc"] in lang_urls:
            own = dict(ALT.findall(page))
            p.ok(own == dict(e["alts"]),
                 f"PAGE {e['loc']}: alternate страницы расходятся с sitemap")

    return {"c": {"checks": p.checks, "fails": len(p.problems),
                  "urls": len(entries), "langs": len(lang_urls)},
            "problems": p.problems}


def report(res: dict) -> int:
    c = res["c"]
    if "urls" in c:
        print(f"адресов: {c['urls']}  языковых: {c['langs']}  проверок: {c['checks']}")
    for prob in res["problems"][:25]:
        print("  " + prob)
    if len(res["problems"]) > 25:
        print(f"  ... ещё {len(res['problems']) - 25}")
    print(f"CHECKS: {c['checks']}, FAILED: {c['fails']}")
    return 1 if c["fails"] else 0


# ---- контроль прибора: шесть мутантов на копии дерева -----------------------

def _copy_tree(src: Path, dst: Path) -> None:
    # robots.txt обязателен: shape() по нему решает, какие страницы вообще
    # считаются страницами сайта. Без него копия «забыла» бы запрет.
    files = [Path("sitemap.xml"), Path("index.html"), Path("robots.txt"),
             Path(REGISTRY)]
    sh = shape(src)
    files += [Path(o) for o in sh["others"]]
    files += [Path(c) / "index.html" for c in sh["langs"]]
    for rel in files:
        srcf = src / rel
        if srcf.is_file():
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(srcf, dst / rel)


def _rewrite(site: Path, loc: str, fn) -> None:
    path = site / "sitemap.xml"
    text = text_of(path)

    def rep(m: re.Match) -> str:
        block = m.group(0)
        return fn(block) if f"<loc>{loc}</loc>" in block else block

    path.write_text(BLOCK.sub(rep, text), encoding="utf-8")


def control() -> int:
    sh = shape(ROOT)
    base = sh["base"]
    root_url = url_for(sh, sh["default"])
    lang = sh["langs"][-1]
    lang_url = url_for(sh, lang)
    victim = url_for(sh, sh["langs"][0])

    def fresh() -> Path:
        d = Path(tempfile.mkdtemp(prefix="sitemap-ctl-"))
        _copy_tree(ROOT, d)
        return d

    caught: list[tuple[str, bool]] = []

    def leg(name: str, tag: str, mutate) -> None:
        site = fresh()
        try:
            mutate(site)
            probs = scan(site)["problems"]
            caught.append((name, any(x.startswith(tag) for x in probs)))
        finally:
            shutil.rmtree(site, ignore_errors=True)

    leg("пропавший адрес", "COVER",
        lambda s: _rewrite(s, lang_url, lambda b: ""))
    leg("адрес без файла", "FILE",
        lambda s: _rewrite(s, victim, lambda b: b.replace(victim, f"{base}hh/")))
    leg("урезанный alternate", "ALTS",
        lambda s: _rewrite(s, root_url, lambda b: re.sub(
            r'\n\s*<xhtml:link[^\n]*hreflang="uk"[^\n]*', "", b)))
    leg("lastmod из будущего", "DATE",
        lambda s: _rewrite(s, victim, lambda b: LASTMOD.sub(
            "<lastmod>2099-12-31</lastmod>", b)))
    leg("реестр разошёлся", "DATE",
        _stale_registry(root_url, victim))
    leg("чужой canonical", "PAGE",
        _foreign_canonical(victim, lang_url))
    # База берётся из canonical корня, а не из самого sitemap: иначе прибор
    # сверял бы sitemap сам с собой и старый домен прошёл бы зелёным.
    leg("старый домен", "COVER",
        lambda s: (s / "sitemap.xml").write_text(
            text_of(s / "sitemap.xml").replace(base, "https://old.example.com/"),
            encoding="utf-8"))

    good = sum(1 for _, ok in caught if ok)
    print("КОНТРОЛЬ: " + "  ".join(f"{n} — {'поймал' if ok else 'ПРОСМОТРЕЛ'}"
                                   for n, ok in caught))
    print(f"поймал {good} из {len(caught)}")
    return 0 if good == len(caught) else 1


def _stale_registry(root_url: str, victim: str):
    def mutate(site: Path) -> None:
        path = site / REGISTRY
        data = json.loads(path.read_text(encoding="utf-8"))
        if victim in data:
            data[victim]["date"] = "2026-01-01"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return mutate


def _foreign_canonical(loc_url: str, other_url: str):
    def mutate(site: Path) -> None:
        sh = shape(site)
        f = path_of(site, sh["base"], loc_url)
        if f is None or not f.is_file():
            return
        page = text_of(f)
        f.write_text(page.replace(f'<link rel="canonical" href="{loc_url}">',
                                  f'<link rel="canonical" href="{other_url}">', 1),
                     encoding="utf-8")
    return mutate


def main() -> int:
    ap = argparse.ArgumentParser(
        description="sitemap.xml: покрытие, файлы, alternate, lastmod, canonical")
    ap.add_argument("--control", action="store_true",
                    help="проверить сам прибор на шести выдумках")
    ap.add_argument("--root", default=str(ROOT),
                    help="корень для проверки (по умолчанию — каталог репозитория)")
    args = ap.parse_args()
    if args.control:
        return control()
    return report(scan(Path(args.root).resolve()))


if __name__ == "__main__":
    sys.exit(main())
