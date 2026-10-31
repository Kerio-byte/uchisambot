#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/check-form.py — контракт формы связи на девяти языках.

Повод (31.10.2026, девятнадцатый блок). Форма — единственный канал, которым
посетитель может написать нам. Ни один прибор её не читал: check-markup смотрит
дерево тегов и id, a11y — подписи и цели нажатия, third-party — что браузер
сходил только к Web3Forms. Сам контракт отправки не проверял никто:

  1) ключ доступа. Он лежит в разметке девяти страниц копией. Опечатка в одной
     копии не видна ничем: страница цела, кнопка нажимается, Web3Forms отвечает
     отказом, а человек читает «попробуйте ещё раз» — и его письмо не приходит
     НИКОГДА. Молчащий канал хуже закрытого: закрытый видно.
  2) subject. Это не украшение: по нему почтовый сторож на kerio отбирает наши
     письма из ящика. Разъехавшийся subject — письмо приходит и не разбирается.
  3) redirect. Он обязан вести на ТУ ЖЕ языковую страницу: копия с английским
     адресом уводит испанца на английскую страницу, то есть после отправки
     человек теряет свой язык.
  4) приманка botcheck обязана быть и обязана быть спрятана. Видимая приманка —
     галочка, которую честный человек не тронет, но и робот не тронет; а
     неспрятанная ловит людей.
  5) обещания в текстах отказов. Страница говорит: «твой текст всё ещё в поле».
     Это обещание проверяемо браузером и до 31.10 не проверялось ничем: очистка
     поля при отказе выглядела бы как забота о чистоте формы.

Что делает прибор. Два слоя:
  A) разметка девяти страниц: action/method, access_key (формат UUID и ОДНО
     значение на всех), subject, from_name, redirect по языку, приманка и её
     стиль, обязательность полей, потолок maxlength против предела Web3Forms
     (3000), подписи полей, три баннера (ок / отказ / занято);
  B) поведение в Chromium: подмена ответа Web3Forms на четырёх сценариях —
     успех, отказ (success:false), обрыв сети, 429 — и проверка того, что
     обещано: успех прячет форму и показывает «спасибо»; отказ показывает
     ошибку и НЕ теряет текст; 429 говорит «занято»; кнопка возвращается.

Контроль (--control): копия дерева, нетронутая копия обязана быть зелёной,
затем семь мутантов, каждый обязан покраснеть СВОИМ сообщением: чужой ключ на
одной странице, чужой subject, redirect на другой язык, снятая приманка,
снятый required, maxlength 5000, очистка поля при отказе (мутант в JS —
единственный, кого видит только браузерный слой).

Запуск:
  python3 tools/check-form.py                 # разметка + браузер
  python3 tools/check-form.py --no-browser    # только разметка (быстро)
  python3 tools/check-form.py --control       # сам прибор: семь мутантов
  python3 tools/check-form.py --control --no-browser   # только разметка

Код возврата: 0 — зелено, 1 — дефект, 2 — контроль не доказал прибор,
3 — браузерного слоя нет (не проверяли — это не зелено).
"""
from __future__ import annotations

import argparse
import http.server
import json
import re
import shutil
import socketserver
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["ru", "es", "pt", "hi", "id", "tr", "vi", "uk"]
EXTRA = ["privacy.html", "terms.html", "404.html"]
FORM_ACTION = "https://api.web3forms.com/submit"
MAXLEN_CAP = 3000          # предел Web3Forms на поле message
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
FORM_RE = re.compile(r"<form\b[^>]*id=\"contact-form\"[^>]*>(.*?)</form>", re.S)
INPUT_RE = re.compile(r"<(input|textarea|button)\b([^>]*)>", re.S)


def base_url(root: Path) -> str:
    """Адрес живого сайта берём из tools/site.json, а не пишем литералом."""
    p = root / "tools" / "site.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))["base"]
    except Exception:
        return "https://kerio-byte.github.io/uchisambot/"


def pages(root: Path) -> list[tuple[str, Path]]:
    out = [("en", root / "index.html")]
    out += [(l, root / l / "index.html") for l in LANGS]
    return out


def prefix(lang: str) -> str:
    return "" if lang == "en" else f"{lang}/"


def attr(attrs: str, name: str) -> str | None:
    m = re.search(r"\b" + name + r"=\"([^\"]*)\"", attrs)
    return m.group(1) if m else None


def flag(attrs: str, name: str) -> bool:
    """Булевы атрибуты пишутся без значения: required, disabled, hidden."""
    return re.search(r"(?<![\w-])" + name + r"(?![\w-])", attrs) is not None


def fields(form_html: str) -> dict[str, str]:
    """name → все атрибуты тега. Для hidden берём value, для полей — весь набор."""
    out: dict[str, str] = {}
    for _tag, attrs in INPUT_RE.findall(form_html):
        n = attr(attrs, "name")
        if n:
            out[n] = attrs
    return out


def scan_markup(root: Path) -> dict:
    res = {"checks": 0, "fails": [], "pages": 0}
    fails = res["fails"]

    def check(tag: str, ok: bool, where: str, msg: str) -> None:
        res["checks"] += 1
        if not ok:
            fails.append(f"{tag} [{where}] {msg}")

    base = base_url(root)
    keys: dict[str, str] = {}
    subj: dict[str, str] = {}
    fromn: dict[str, str] = {}

    for lang, path in pages(root):
        where = lang
        if not path.is_file():
            check("FORM", False, where, f"страницы нет: {path.relative_to(root)}")
            continue
        res["pages"] += 1
        page = path.read_text(encoding="utf-8", errors="replace")

        # 1) одна форма и она наша
        n_forms = len(re.findall(r"<form\b", page))
        m = FORM_RE.search(page)
        check("FORM", n_forms == 1 and m is not None, where,
              f"форм на странице {n_forms}, форма contact-form "
              f"{'есть' if m else 'не найдена'}")
        if not m:
            continue
        tag_attrs = page[m.start():m.start(1)]
        body = m.group(1)

        # 2) адрес и метод: без них не работает путь без JS
        act = attr(tag_attrs, "action")
        meth = (attr(tag_attrs, "method") or "").upper()
        check("ACT", act == FORM_ACTION and meth == "POST", where,
              f"action={act!r} method={meth!r} (нужно {FORM_ACTION} + POST)")

        f = fields(body)

        # 3) ключ доступа: формат
        k = attr(f.get("access_key", ""), "value") or ""
        check("KEY", bool(UUID_RE.match(k)), where,
              f"access_key {k!r} не похож на ключ Web3Forms")
        keys[lang] = k

        # 4) subject и from_name: маршрут письма и подпись
        subj[lang] = attr(f.get("subject", ""), "value") or ""
        fromn[lang] = attr(f.get("from_name", ""), "value") or ""

        # 5) redirect: та же языковая страница, тот же якорь
        want = f"{base}{prefix(lang)}?sent=1#contact-card"
        got = attr(f.get("redirect", ""), "value") or ""
        check("REDIR", got == want, where, f"redirect={got!r}, нужно {want!r}")

        # 6) приманка: есть и спрятана
        hp = "botcheck" in f
        hidden_css = ".contact .hp{display:none" in page.replace(" !important", "")
        check("HP", hp and hidden_css, where,
              f"приманка botcheck {'есть' if hp else 'НЕТ'}, "
              f"стиль .hp {'прячет' if hidden_css else 'НЕ прячет'}")

        # 7) обязательные поля и их типы
        em = f.get("email", "")
        ms = f.get("message", "")
        ok_req = (attr(em, "type") == "email" and flag(em, "required")
                  and flag(ms, "required"))
        check("REQ", ok_req, where,
              "email обязан быть type=email + required, message — required")

        # 8) потолок длины против предела Web3Forms
        ml = attr(ms, "maxlength")
        ok_ml = ml is not None and ml.isdigit() and 0 < int(ml) <= MAXLEN_CAP
        check("LIMIT", ok_ml, where,
              f"maxlength={ml!r}: больше {MAXLEN_CAP} Web3Forms обрежет молча")

        # 9) подписи привязаны к полям (скринридер, не только глаз)
        for field in ("cf-email", "cf-msg"):
            check("LABEL", f'for="{field}"' in page and f'id="{field}"' in body, where,
                  f"нет label[for={field}] рядом с полем")

        # 10) кнопка отправки и три баннера-обещания
        check("BANNER", 'type="submit"' in body, where, "нет кнопки type=submit")
        for bid in ("contact-ok", "contact-err", "contact-err-busy"):
            check("BANNER", f'id="{bid}"' in page, where, f"нет баннера #{bid}")
        check("BANNER", 'role="alert"' in page and 'id="contact-err"' in page, where,
              "баннер отказа без role=alert — скринридер его не объявит")

        # 11) обещание стоит рядом с формой: ссылка на политику в той же карточке.
        # Человек, который уже пишет нам адрес, обязан видеть, что мы с ним сделаем.
        note = re.search(r'<p class="contact-note">(.*?)</p>', page, re.S)
        check("NOTE", note is not None and "privacy.html" in note.group(1), where,
              "рядом с формой нет ссылки на политику конфиденциальности")

    # ---- сквозные: одна и та же форма на девяти страницах ------------------
    def same(name: str, data: dict[str, str], tag: str) -> None:
        vals = {v for v in data.values() if v}
        ok = len(vals) == 1 and all(data.values())
        res["checks"] += 1
        if not ok:
            detail = ", ".join(f"{k}={v!r}" for k, v in data.items() if v !=
                               (list(vals)[0] if vals else None))
            fails.append(f"{tag} значения разъехались: {detail or 'пусто'}")

    same("access_key", keys, "KEYID")
    same("subject", subj, "SUBJ")
    same("from_name", fromn, "FROM")
    res["checks"] += 1
    if subj and not any(subj.values()):
        fails.append("SUBJ subject пустой — письма нечем маршрутизировать")

    # ---- форма не должна стоять там, где нет карточки подтверждения -------
    for name in EXTRA:
        p = root / name
        if not p.is_file():
            continue
        page = p.read_text(encoding="utf-8", errors="replace")
        res["checks"] += 1
        if "<form" in page and 'id="contact-card"' not in page:
            fails.append(f"FORM [{name}] форма без карточки подтверждения: "
                         f"после отправки человеку нечего показать")

    return res


# ---- слой B: поведение в браузере -----------------------------------------
def serve(root: Path):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(root), **kw)

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def scan_behavior(root: Path) -> dict:
    res = {"checks": 0, "fails": []}
    fails = res["fails"]
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        res["nobrowser"] = True
        return res

    httpd, port = serve(root)
    ok_headers = {
        "access-control-allow-origin": "*",
        "access-control-allow-headers": "*",
        "access-control-allow-methods": "POST, OPTIONS",
    }
    try:
        with sync_playwright() as p:
            br = p.chromium.launch(args=["--no-sandbox"])

            def run_case(lang: str, mode: str, width: int = 420) -> dict:
                ctx = br.new_context(viewport={"width": width, "height": 900})
                pg = ctx.new_page()
                seen = {"body": None}

                def route(r):
                    if r.request.method == "OPTIONS":
                        return r.fulfill(status=204, headers=ok_headers, body="")
                    seen["body"] = r.request.post_data
                    if mode == "abort":
                        return r.abort()
                    if mode == "ok":
                        return r.fulfill(status=200, headers={**ok_headers,
                                                              "content-type": "application/json"},
                                         body=json.dumps({"success": True}))
                    if mode == "refuse":
                        return r.fulfill(status=200, headers={**ok_headers,
                                                              "content-type": "application/json"},
                                         body=json.dumps({"success": False,
                                                          "message": "Invalid Access Key"}))
                    return r.fulfill(status=429, headers={**ok_headers,
                                                          "content-type": "application/json"},
                                     body=json.dumps({"success": False, "message": "busy"}))

                pg.route("**/api.web3forms.com/**", route)
                pg.goto(f"http://127.0.0.1:{port}/{prefix(lang)}", wait_until="load")
                pg.fill("#cf-email", "visitor@example.com")
                pg.fill("#cf-msg", "Текст, который обязан выжить при отказе")
                pg.click("#contact-form button[type=submit]")
                pg.wait_for_timeout(900)
                state = pg.evaluate("""() => {
                    const q = s => document.querySelector(s);
                    const vis = el => !!el && !el.hidden &&
                        getComputedStyle(el).display !== 'none';
                    const over = (el) => el ? el.scrollWidth - el.clientWidth : 0;
                    return {
                        ok: vis(q('#contact-ok')),
                        err: vis(q('#contact-err')),
                        busy: vis(q('#contact-err-busy')),
                        form: q('#contact-form') ? getComputedStyle(q('#contact-form')).display : 'gone',
                        text: (q('#cf-msg') || {}).value || '',
                        btn: q('#contact-form button[type=submit]')
                             ? !q('#contact-form button[type=submit]').disabled : false,
                        // глаз смотрит на кадр, прибор — на числа: длинный текст
                        // отказа на 420 и 320 px не имеет права вылезти за экран
                        // и не имеет права быть обрезанным внутри своего блока.
                        over_page: Math.max(0, document.documentElement.scrollWidth
                                               - window.innerWidth),
                        clipped: Math.max(over(q('#contact-ok')), over(q('#contact-err')),
                                          over(q('#contact-err-busy'))),
                    };
                }""")
                state["body"] = seen["body"]
                ctx.close()
                return state

            def check(tag: str, ok: bool, msg: str) -> None:
                res["checks"] += 1
                if not ok:
                    fails.append(f"{tag} {msg}")

            lang = "ru"
            # успех: подтверждение вместо формы, текст полю больше не нужен
            s = run_case(lang, "ok")
            check("BODY", bool(s["body"]), "браузер не отправил POST на Web3Forms")
            if s["body"]:
                try:
                    sent = json.loads(s["body"])
                except Exception:
                    sent = {}
                check("BODY", bool(UUID_RE.match(str(sent.get("access_key", "")))),
                      f"в теле ушёл ключ {sent.get('access_key')!r}")
                check("BODY", sent.get("email") == "visitor@example.com"
                      and sent.get("message", "").startswith("Текст"),
                      "в теле ушли не те поля: письмо придёт пустым боту защиты")
                check("BODY", sent.get("redirect") is None,
                      "поле redirect ушло в JSON: ответ придёт HTML-страницей")
            check("OK", s["ok"] and s["form"] == "none",
                  f"после успеха: спасибо={s['ok']}, форма display={s['form']}")

            # отказ: ошибка есть, текст НЕ потерян, кнопка снова живая
            s = run_case(lang, "refuse")
            check("ERR", s["err"] and not s["ok"] and not s["busy"],
                  f"на success:false баннеры: отказ={s['err']} спасибо={s['ok']} "
                  f"занято={s['busy']}")
            check("TEXT", s["text"].startswith("Текст"),
                  f"при отказе текст пропал из поля: {s['text']!r}")
            check("RETRY", s["btn"], "кнопка осталась disabled после отказа")

            # визуал числом: длинный текст отказа на узком экране
            for width in (420, 320):
                s = run_case(lang, "refuse", width=width)
                check("VIEW", s["over_page"] == 0,
                      f"{width}px: страница шире окна на {s['over_page']} px в состоянии отказа")
                check("VIEW", s["clipped"] <= 1,
                      f"{width}px: текст отказа обрезан внутри блока на {s['clipped']} px")

            # обрыв сети: тот же отказ, тот же текст
            s = run_case(lang, "abort")
            check("NET", s["err"] and not s["ok"], "обрыв сети не показал отказ")
            check("TEXT", s["text"].startswith("Текст"),
                  f"при обрыве сети текст пропал из поля: {s['text']!r}")

            # 429: «занято», а не общий отказ; текст на месте
            s = run_case(lang, "busy")
            check("BUSY", s["busy"] and not s["ok"],
                  f"на 429 показан не «занято»: занято={s['busy']} отказ={s['err']}")
            check("TEXT", s["text"].startswith("Текст"),
                  f"на 429 текст пропал из поля: {s['text']!r}")

            br.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    return res


def scan(root: Path, browser: bool = True) -> dict:
    res = scan_markup(root)
    if browser:
        b = scan_behavior(root)
        res["checks"] += b["checks"]
        res["fails"] += b["fails"]
        if b.get("nobrowser"):
            res["nobrowser"] = True
    return res


# ---- контроль: семь мутантов на копии дерева -------------------------------
IGNORE = shutil.ignore_patterns(".git", "evidence", ".shots-work", "tools", "src",
                                "docs", "submission-kit", "__pycache__")


def control(browser: bool = True) -> int:
    def fresh() -> Path:
        d = Path(tempfile.mkdtemp(prefix="form-ctl-"))
        shutil.copytree(ROOT, d, ignore=IGNORE, dirs_exist_ok=True)
        return d

    caught: list[tuple[str, bool]] = []

    def leg(name: str, tag: str, mutate, use_browser: bool = False) -> None:
        # Разметочные мутанты проверяются разметкой: гонять браузер на каждого —
        # четыре лишних запуска Chromium на мутант, и контроль не влезает в бюджет.
        site = fresh()
        try:
            mutate(site)
            probs = scan(site, browser=use_browser and browser)["fails"]
            caught.append((name, any(x.startswith(tag) for x in probs)))
        finally:
            shutil.rmtree(site, ignore_errors=True)

    def edit_page(lang: str, fn) -> None:
        def mutate(site: Path) -> None:
            f = site / (("index.html") if lang == "en" else f"{lang}/index.html")
            t = f.read_text(encoding="utf-8")
            f.write_text(fn(t), encoding="utf-8")
        return mutate

    # нетронутая копия обязана быть зелёной — иначе красное ниже ничего не доказывает
    site = fresh()
    try:
        clean = scan(site, browser=False)["fails"]
    finally:
        shutil.rmtree(site, ignore_errors=True)
    print(f"КОНТРОЛЬ: нетронутая копия — {'зелёная' if not clean else 'КРАСНАЯ: ' + clean[0]}")

    leg("чужой ключ на одной странице", "KEYID",
        edit_page("es", lambda t: t.replace(
            "f3eafc0c-996f-4090-aff4-63c993612a2c",
            "00000000-1111-2222-3333-444444444444")))
    leg("чужой subject", "SUBJ",
        edit_page("tr", lambda t: t.replace(
            'name="subject" value="UchiSamBot contact form"',
            'name="subject" value="Contact"', 1)))
    leg("redirect на другой язык", "REDIR",
        edit_page("pt", lambda t: t.replace("/pt/?sent=1#contact-card",
                                            "/?sent=1#contact-card")))
    leg("снятая приманка", "HP",
        edit_page("hi", lambda t: re.sub(
            r'\s*<input type="checkbox" name="botcheck"[^>]*>', "", t)))
    leg("снятый required у message", "REQ",
        edit_page("id", lambda t: t.replace(
            '<textarea id="cf-msg" name="message" rows="4" required',
            '<textarea id="cf-msg" name="message" rows="4"', 1)))
    leg("maxlength выше предела", "LIMIT",
        edit_page("vi", lambda t: t.replace('maxlength="3000"', 'maxlength="5000"', 1)))
    if browser:
        # единственный мутант, которого не видит разметка: очистка поля при отказе
        def wipe(site: Path) -> None:
            f = site / "ru" / "index.html"
            t = f.read_text(encoding="utf-8")
            t = t.replace("  function showError(which){",
                          "  function showError(which){\n    form.reset();", 1)
            f.write_text(t, encoding="utf-8")
        leg("очистка поля при отказе", "TEXT", wipe, use_browser=True)

    good = sum(1 for _, ok in caught if ok)
    print("  " + "\n  ".join(f"{n} — {'поймал' if ok else 'ПРОСМОТРЕЛ'}"
                             for n, ok in caught))
    print(f"поймал {good} из {len(caught)}")
    return 0 if good == len(caught) and not clean else 1


def report(res: dict) -> int:
    if res.get("nobrowser"):
        print("БРАУЗЕРНОГО СЛОЯ НЕТ: playwright не установлен — проверена только разметка")
    print(f"страниц с формой: {res.get('pages', 0)}")
    for prob in res["fails"][:25]:
        print("  " + prob)
    if len(res["fails"]) > 25:
        print(f"  ... ещё {len(res['fails']) - 25}")
    print(f"CHECKS: {res['checks']}, FAILED: {len(res['fails'])}")
    if res.get("nobrowser"):
        return 3
    return 1 if res["fails"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="контракт формы связи: разметка девяти страниц и поведение в браузере")
    ap.add_argument("--control", action="store_true", help="проверить сам прибор")
    ap.add_argument("--no-browser", action="store_true", help="только разметка")
    ap.add_argument("--root", default=str(ROOT), help="корень дерева для проверки")
    args = ap.parse_args()
    if args.control:
        return control(browser=not args.no_browser)
    return report(scan(Path(args.root).resolve(), browser=not args.no_browser))


if __name__ == "__main__":
    sys.exit(main())
