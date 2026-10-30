#!/usr/bin/env python3
"""check-redirects.py — переходы, слэши и адрес страницы-дубля.

Повод (30.10.2026). Технический блок каждый запуск проверял руками: редирект
http→https, слэш после языка, поведение /index.html и что неизвестный адрес
отдаёт 404, а не 200. Ровно этот класс дефектов уже закрывали прибором —
одноразовые команды в терминале не переживают запуск и не падают, когда
ломаются. Здесь то же самое становится проверкой с контролем.

Что проверяется (десять клауз, все на живом сайте):

  1) http.upgrade — плоский http отдаёт 301 на https и НЕ отдаёт тело страницы.
     Если 200 — человек первый раз читает сайт по открытому каналу.
  2) root.slash — корень без слэша уходит 301 на корень со слэшем: иначе один
     и тот же текст живёт по двум адресам.
  3) lang.slash ×9 — /xx → 301 /xx/. Это то, что человек набирает руками
     и что приходит из чужих ссылок.
  4) lang.live ×9 — адрес со слэшем отвечает 200. Обещание «девять языков»
     проверяется здесь по-настоящему: не по файлу в дереве, а по ответу сети.
  5) same.host — ни один 301 не уводит на чужой хост (тихая подмена домена).
  6) probe.404 — неизвестный вложенный адрес отвечает 404, не 200.
  7) probe.404_page — тело этого ответа — своя страница 404 (в нём есть «404»
     и ссылка домой), а не пустота.
  8) canonical.self — canonical каждой страницы указывает на неё саму.
  9) index.html — /index.html отвечает 200, но canonical там — корень, а не
     «/index.html»: сервер на GitHub Pages редирект отдать не может, значит
     дубль обязан схлопываться каноническим адресом.
 10) hreflang.live — каждый адрес из hreflang (девять языков + x-default)
     отвечает 200. Список берётся со страницы, а не из головы.

Контроль (--control) гоняет тот же разбор по заведомо кривым ответам: плоский
http с 200, язык без слэша с 200, неизвестный адрес с 200, редирект на чужой
хост, canonical на /index.html. Прибор обязан покраснеть на всех пяти. Прибор,
который никогда не падал, ничего не проверяет.

  python3 tools/check-redirects.py             # живой сайт
  python3 tools/check-redirects.py --offline   # только дерево: canonical, hreflang, /en/
  python3 tools/check-redirects.py --control   # проверка самого прибора
  python3 tools/check-redirects.py --json      # доказательство в evidence/
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "tools" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"]
LANGS = ["en", "ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
UA = "UchiSamBot-landing-check/1.0 (+redirect surface)"
PROBE = "zz-nonexistent-probe-30-10/"
STEP_TIMEOUT = 20


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def url_for(lang: str) -> str:
    return BASE if lang == "en" else f"{BASE}{lang}/"


def page_path(lang: str) -> Path:
    return ROOT / "index.html" if lang == "en" else ROOT / lang / "index.html"


def fetch(url: str) -> dict:
    """Один ответ без перехода по редиректу. Возвращает status/location/body."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=STEP_TIMEOUT) as resp:
            body = resp.read(400_000)
            return {"status": resp.status, "location": resp.headers.get("Location", "") or "",
                    "body": body.decode("utf-8", "replace")}
    except urllib.error.HTTPError as err:
        try:
            body = err.read(400_000)
        except Exception:  # noqa: BLE001 — тело у 3xx бывает недоступно
            body = b""
        location = ""
        if err.headers is not None:
            location = err.headers.get("Location", "") or ""
        return {"status": err.code, "location": location,
                "body": body.decode("utf-8", "replace")}
    except Exception as err:  # noqa: BLE001 — сеть: считаем как «нет ответа»
        return {"status": 0, "location": "", "body": "", "error": str(err)[:120]}


def strip_slash(url: str) -> str:
    return url[:-1] if url.endswith("/") else url


def canonical_in(tree_path: Path) -> str:
    if not tree_path.is_file():
        return ""
    text = tree_path.read_text(encoding="utf-8", errors="replace")
    found = re.search(r'<link rel="canonical" href="([^"]+)"', text)
    return found.group(1) if found else ""


def hreflang_in(tree_path: Path) -> list[str]:
    if not tree_path.is_file():
        return []
    text = tree_path.read_text(encoding="utf-8", errors="replace")
    return re.findall(r'<link rel="alternate" hreflang="[^"]+" href="([^"]+)"', text)


def judge(records: dict[str, dict], tree_canonicals: dict[str, str],
          hreflang: list[str]) -> list[tuple[bool, str, str]]:
    """Чистая логика: записи ответов → приговоры. Без сети, чтобы её можно было
    прогнать по выдуманным ответам в контроле."""
    out: list[tuple[bool, str, str]] = []
    host = urllib.parse.urlsplit(BASE).netloc
    http_base = BASE.replace("https://", "http://", 1)

    def rec(url: str) -> dict:
        return records.get(url, {"status": 0, "location": "", "body": ""})

    # 1) плоский http обязан уводить на https
    r = rec(http_base)
    ok = r.get("status") in (301, 302, 307, 308) and r.get("location", "").startswith("https://")
    out.append((ok, "http.upgrade", f"{http_base} -> {r.get('status')} {r.get('location') or '—'}"))

    # 2) корень без слэша
    root_ns = strip_slash(BASE)
    r = rec(root_ns)
    ok = r.get("status") in (301, 308) and r.get("location", "") == BASE
    out.append((ok, "root.slash", f"{root_ns} -> {r.get('status')} {r.get('location') or '—'}"))

    # 3-4) каждый язык: без слэша 301 на со слэшем, со слэшем 200
    for lang in LANGS:
        target = url_for(lang)
        r = rec(strip_slash(target))
        ok = r.get("status") in (301, 302, 307, 308) and r.get("location", "") == target
        out.append((ok, f"lang.slash {lang}", f"{strip_slash(target)} -> {r.get('status')} "
                                                   f"{r.get('location') or '—'}"))
    for lang in LANGS:
        target = url_for(lang)
        r = rec(target)
        ok = r.get("status") == 200 and len(r.get("body", "")) > 2000
        out.append((ok, f"lang.live {lang}", f"{target} -> {r.get('status')}, "
                                             f"{len(r.get('body', ''))} байт тела"))

    # 5) ни один 301 не уводит на чужой хост
    foreign = [f"{u} -> {d.get('location')}" for u, d in records.items()
               if d.get("status") in (301, 302, 307, 308)
               and urllib.parse.urlsplit(d.get("location", "")).netloc not in ("", host)]
    out.append((not foreign, "same.host", "; ".join(foreign) or "все переходы внутри своего хоста"))

    # 6-7) неизвестный адрес: 404 и своя страница
    probe = BASE + PROBE
    r = rec(probe)
    out.append((r.get("status") == 404, "probe.404", f"{probe} -> {r.get('status')}"))
    body = r.get("body", "")
    home_ref = 'href="/uchisambot/"' in body or f'href="{BASE}"' in body
    out.append(("404" in body and home_ref, "probe.404_page",
                f"{len(body)} байт, «404»={'да' if '404' in body else 'НЕТ'}, "
                f"ссылка домой={'да' if home_ref else 'НЕТ'}"))

    # 8) canonical каждой страницы — на неё саму
    for lang in LANGS:
        want = url_for(lang)
        got = tree_canonicals.get(lang, "")
        out.append((got == want, f"canonical.self {lang}", f"{got or 'нет'} (ждали {want})"))

    # 9) /index.html: 200, но canonical — корень
    idx = BASE + "index.html"
    r = rec(idx)
    got = tree_canonicals.get("__index__", "")
    out.append((r.get("status") == 200 and got == BASE,
                "index.html", f"{idx} -> {r.get('status')}, canonical={got or 'нет'}"))

    # 10) hreflang: каждый адрес отвечает 200
    missing = [u for u in hreflang if rec(u).get("status") != 200]
    out.append((not missing, "hreflang.live",
                "; ".join(missing) if missing else f"все {len(hreflang)} адресов из hreflang живы"))
    return out


def tree_side() -> tuple[dict[str, str], list[str]]:
    canonicals = {lang: canonical_in(page_path(lang)) for lang in LANGS}
    canonicals["__index__"] = canonical_in(ROOT / "index.html")
    return canonicals, hreflang_in(ROOT / "index.html")


def offline_judge(canonicals: dict[str, str], hreflang: list[str]) -> list[tuple[bool, str, str]]:
    out: list[tuple[bool, str, str]] = []
    for lang in LANGS:
        want = url_for(lang)
        got = canonicals.get(lang, "")
        out.append((got == want, f"canonical.self {lang}", f"{got or 'нет'} (ждали {want})"))
    out.append((canonicals.get("__index__") == BASE, "index.html",
                f"canonical={canonicals.get('__index__') or 'нет'} (ждали {BASE})"))
    local = {u for u in hreflang if u.startswith(BASE)}
    missing = [u for u in hreflang if u not in local and not u.startswith("https://")]
    out.append((len(hreflang) == len(LANGS) + 1 and not missing, "hreflang.count",
                f"{len(hreflang)} адресов (ждали {len(LANGS) + 1})"))
    # ссылок на /en/ быть не должно: английский живёт в корне
    offenders = []
    for lang in LANGS:
        text = page_path(lang).read_text(encoding="utf-8", errors="replace")
        if f'href="{BASE}en/"' in text:
            offenders.append(str(page_path(lang).relative_to(ROOT)))
    out.append((not offenders, "no_en_dir", "; ".join(offenders) or "ссылок на /en/ нет"))
    return out


def live_judge() -> list[tuple[bool, str, str]]:
    canonicals, hreflang = tree_side()
    urls = [BASE.replace("https://", "http://", 1), strip_slash(BASE), BASE + PROBE, BASE + "index.html"]
    for lang in LANGS:
        urls += [strip_slash(url_for(lang)), url_for(lang)]
    urls += [u for u in hreflang if u.startswith("http")]
    seen, records = set(), {}
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        records[url] = fetch(url)
        time.sleep(0.05)
    return judge(records, canonicals, hreflang)


def control() -> int:
    canonicals, hreflang = tree_side()
    clean_records = {}
    host_base = BASE
    clean_records[host_base.replace("https://", "http://", 1)] = {
        "status": 301, "location": host_base, "body": ""}
    clean_records[strip_slash(host_base)] = {"status": 301, "location": host_base, "body": ""}
    for lang in LANGS:
        clean_records[strip_slash(url_for(lang))] = {
            "status": 301, "location": url_for(lang), "body": ""}
        clean_records[url_for(lang)] = {"status": 200, "location": "", "body": "<html>x" * 900}
    clean_records[host_base + PROBE] = {
        "status": 404, "location": "", "body": f'<h1>404</h1><a href="/uchisambot/">домой</a>'}
    clean_records[host_base + "index.html"] = {"status": 200, "location": "", "body": "<html>ok"}
    good = judge(clean_records, canonicals, hreflang)
    good_fails = [n for ok, n, _ in good if not ok]

    broken = dict(clean_records)
    broken[host_base.replace("https://", "http://", 1)] = {
        "status": 200, "location": "", "body": "<html>plain</html>"}
    broken[strip_slash(url_for("ru"))] = {"status": 200, "location": "", "body": "<html>x" * 900}
    broken[host_base + PROBE] = {"status": 200, "location": "", "body": "<html>404</html>"}
    broken[strip_slash(url_for("uk"))] = {
        "status": 301, "location": "https://example.com/uchisambot/uk/", "body": ""}
    bad_canon = dict(canonicals)
    bad_canon["__index__"] = host_base + "index.html"
    bad = judge(broken, bad_canon, hreflang)
    bad_fails = {n for ok, n, _ in bad if not ok}

    must_catch = {"http.upgrade", "lang.slash ru", "probe.404", "same.host", "index.html"}
    missed = must_catch - bad_fails
    print(f"контроль: чистый набор — провалов {len(good_fails)} (ждали 0)")
    for name in sorted(good_fails):
        print(f"  ложная тревога: {name}")
    print(f"контроль: кривой набор — поймано {len(bad_fails)} из {len(must_catch)} обязательных")
    for name in sorted(bad_fails):
        print(f"  поймал: {name}")
    ok = not good_fails and not missed
    print("КОНТРОЛЬ: " + ("прибор падает там, где должен, и молчит там, где чисто"
                          if ok else f"НЕ ГОДЕН, пропустил: {sorted(missed)}"))
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--control" in argv:
        return control()
    if "--offline" in argv:
        canonicals, hreflang = tree_side()
        rows = offline_judge(canonicals, hreflang)
        mode = "offline"
    else:
        rows = live_judge()
        mode = "live"
    failed = [(n, d) for ok, n, d in rows if not ok]
    for ok, name, detail in rows:
        print(f"{'ok  ' if ok else 'FAIL'} {name:22s} {detail}")
    total = len(rows)
    print(f"CHECKS: {total}, FAILED: {len(failed)}")
    if "--json" in argv:
        evidence = ROOT / "evidence"
        evidence.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M")
        path = evidence / f"redirects-{stamp}-{mode}.json"
        path.write_text(json.dumps({"mode": mode, "base": BASE, "checks": total,
                                    "failed": len(failed),
                                    "rows": [{"ok": o, "name": n, "detail": d} for o, n, d in rows]},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"evidence: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
