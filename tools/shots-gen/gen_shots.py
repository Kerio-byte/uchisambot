#!/usr/bin/env python3
"""Генератор языковых макетов чата для лендинга UchiSamBot (1080×2340, стиль Telegram).

Назначение: у КАЖДОГО языка — свои макеты (img/shot1..3-<lang>.webp). Шаг сборки
tools/build.py подставляет файл языка через shot_src(); генератор их создаёт.

Источники правды:
- Тексты интерфейса — из i18n бота (../..//..//study-bot/bot): welcome, task_received,
  task_type_1..3, answer, пункты меню. НЕ переписывать руками.
- Кернед-строки макетов (user2 — сообщение пользователя; body3 — пример разбора;
  приветствие/плейсхолдер панели ввода) — словарь CANNED ниже: у бота их нет
  (динамический ответ LLM), переводы выверены вручную при создании.
- Ассеты (шеврон, аватар, точки, статус-иконки, скрепка) — вырезаются из
  EN-эталона img/shot1.webp (единый стиль, см. extract_assets()).

Рендер: локальный Playwright/Chromium, viewport 1080×2340, dsf=1, шрифт Inter
(сабсеты локально в assets/fonts/, OFL). Эмодзи — системные (Noto Color Emoji),
деванагари — системный Noto Sans Devanagari.

Запуск:
  python3 tools/shots-gen/gen_shots.py --langs hi,uk          # только превью-PNG
  python3 tools/shots-gen/gen_shots.py --langs hi,uk --apply  # записать img/shotN-<lang>.webp
  python3 tools/shots-gen/gen_shots.py --langs en --calib     # EN-калибровка (в превью, не в img/)
  python3 tools/shots-gen/gen_shots.py --langs en,ru --apply --force-en --stamp  # перерисовать эталоны

Кнопки главного меню НЕ вписаны здесь списком (23.10.2026): порядок читается из
`menu_kb()` бота (`bot_menu.py`, разбор исходника). Пока список был ручным, бот
получил кнопку «Пригласить друга», а все девять макетов показывали шесть кнопок.

`--stamp` пишет реестр `tools/shots.json`: sha256 каждого макета и ровно те
строки, что нарисованы. Свип сверяет реестр с ботом и с байтами файлов, поэтому
«текст бота поправили, картинку не перерисовали» и «картинку подменили руками» —
провал, а не тишина.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent                    # .../promo/landing-20261012
# 23.10.2026: путь к боту можно переопределить (как LANDING_ROOT в свипе) — иначе прогон
# на копии дерева падал на чтении bot/handlers.py, и негативный контроль «фраза выпала из
# политики» приходилось проверять на живом сайте.
BOT_DIR = Path(os.environ.get("BOT_DIR", REPO.parent.parent / "study-bot"))   # .../stars-bots/study-bot
FONTS = HERE / "assets" / "fonts"
IMG = REPO / "img"
LEDGER = REPO / "tools" / "shots.json"

sys.path.insert(0, str(HERE))
import bot_menu  # noqa: E402

HANDLERS = BOT_DIR / "bot" / "handlers.py"
MENU_KEYS = bot_menu.menu_keys(HANDLERS)

# --- кернед-строки макетов (в боте их нет: это образец ответа и реплика юзера) ---
# en — для калибровки стиля (эталон img/shot1-3.webp: тексты совпадают с ними).
CANNED = {
    "en": {
        "header": "Study Helper",
        "ph": "Message",
        "user2": "Break down step by step: 3x − 7 = 14",
        "body3": (
            "1. Goal: leave x alone on one side.\n"
            "2. 3x − 7 = 14 → add 7 to both sides: 3x = 21.\n"
            "3. Divide both sides by 3: x = 7.\n"
            "4. Check: 3 × 7 − 7 = 14 ✓\n\n"
            "Example: for 2x = 10, divide both sides by 2 → x = 5.\n\n"
            "Key rule: whatever you do to one side, do the same to the other. "
            "You've almost solved it — just finish the last division."
        ),
    },
    # ru добавлен 23.10.2026: до этого RU-макет был «замороженным эталоном»,
    # и кнопку «Пригласить друга» в нём нельзя было дорисовать иначе как руками.
    "ru": {
        "header": "Учебный помощник",
        "ph": "Сообщение",
        "user2": "Разбери по шагам: 3x − 7 = 14",
        "body3": (
            "1. Цель: оставить x одного на одной стороне.\n"
            "2. 3x − 7 = 14 → прибавляем 7 к обеим сторонам: 3x = 21.\n"
            "3. Делим обе стороны на 3: x = 7.\n"
            "4. Проверка: 3 × 7 − 7 = 14 ✓\n\n"
            "Пример: если 2x = 10, делим обе стороны на 2 → x = 5.\n\n"
            "Главное правило: что делаешь с одной стороной, делай и с другой. "
            "Остался последний шаг — деление."
        ),
    },
    "es": {
        "header": "Ayudante de Estudio",
        "ph": "Mensaje",
        "user2": "Resuelve paso a paso: 3x − 7 = 14",
        "body3": (
            "1. Meta: dejar la x sola en un lado.\n"
            "2. 3x − 7 = 14 → suma 7 a los dos lados: 3x = 21.\n"
            "3. Divide los dos lados entre 3: x = 7.\n"
            "4. Comprueba: 3 × 7 − 7 = 14 ✓\n\n"
            "Ejemplo: si fuera 2x = 10, divides los dos lados entre 2 → x = 5.\n\n"
            "Regla clave: lo que hagas con un lado, hazlo también con el otro. "
            "Ya casi está — solo queda la última división."
        ),
    },
    "pt": {
        "header": "Assistente de Estudos",
        "ph": "Mensagem",
        "user2": "Resolva passo a passo: 3x − 7 = 14",
        "body3": (
            "1. Meta: deixar o x sozinho de um lado.\n"
            "2. 3x − 7 = 14 → some 7 aos dois lados: 3x = 21.\n"
            "3. Divida os dois lados por 3: x = 7.\n"
            "4. Confira: 3 × 7 − 7 = 14 ✓\n\n"
            "Exemplo: se fosse 2x = 10, você dividiria os dois lados por 2 → x = 5.\n\n"
            "Regra de ouro: o que você fizer com um lado, faça também com o outro. "
            "Está quase pronto — falta só a última divisão."
        ),
    },
    "hi": {
        "header": "स्टडी हेल्पर",
        "ph": "संदेश",
        "user2": "कदम-दर-कदम हल करें: 3x − 7 = 14",
        "body3": (
            "1. लक्ष्य: x को एक तरफ़ अकेला छोड़ना।\n"
            "2. 3x − 7 = 14 → दोनों तरफ़ 7 जोड़ें: 3x = 21।\n"
            "3. दोनों तरफ़ 3 से भाग दें: x = 7।\n"
            "4. जाँच: 3 × 7 − 7 = 14 ✓\n\n"
            "उदाहरण: अगर 2x = 10 हो, तो दोनों तरफ़ 2 से भाग दें → x = 5।\n\n"
            "मुख्य नियम: एक तरफ़ जो करें, वही दूसरी तरफ़ भी करें। "
            "बस आख़िरी भाग देना बाकी है।"
        ),
    },
    "id": {
        "header": "Study Helper",
        "ph": "Pesan",
        "user2": "Bahas langkah demi langkah: 3x − 7 = 14",
        "body3": (
            "1. Tujuan: sisakan x di satu sisi.\n"
            "2. 3x − 7 = 14 → tambahkan 7 ke kedua sisi: 3x = 21.\n"
            "3. Bagi kedua sisi dengan 3: x = 7.\n"
            "4. Periksa: 3 × 7 − 7 = 14 ✓\n\n"
            "Contoh: kalau 2x = 10, bagi kedua sisi dengan 2 → x = 5.\n\n"
            "Aturan kunci: apa pun yang kamu lakukan di satu sisi, lakukan juga di sisi lain. "
            "Tinggal satu pembagian terakhir."
        ),
    },
    "tr": {
        "header": "Ders Yardımcısı",
        "ph": "Mesaj",
        "user2": "Adım adım çöz: 3x − 7 = 14",
        "body3": (
            "1. Amaç: x'i bir tarafta yalnız bırakmak.\n"
            "2. 3x − 7 = 14 → iki tarafa da 7 ekle: 3x = 21.\n"
            "3. İki tarafı da 3'e böl: x = 7.\n"
            "4. Kontrol: 3 × 7 − 7 = 14 ✓\n\n"
            "Örnek: 2x = 10 olsaydı iki tarafı da 2'ye bölerdin → x = 5.\n\n"
            "Altın kural: bir tarafa ne yaparsan, diğer tarafa da aynısını yap. "
            "Geriye son bölme kaldı."
        ),
    },
    "vi": {
        "header": "Study Helper",
        "ph": "Tin nhắn",
        "user2": "Phân tích từng bước: 3x − 7 = 14",
        "body3": (
            "1. Mục tiêu: để x đứng một mình ở một vế.\n"
            "2. 3x − 7 = 14 → cộng 7 vào cả hai vế: 3x = 21.\n"
            "3. Chia cả hai vế cho 3: x = 7.\n"
            "4. Kiểm tra: 3 × 7 − 7 = 14 ✓\n\n"
            "Ví dụ: nếu là 2x = 10, chia cả hai vế cho 2 → x = 5.\n\n"
            "Quy tắc chính: làm gì với một vế thì làm đúng như vậy với vế kia. "
            "Chỉ còn phép chia cuối cùng."
        ),
    },
    "uk": {
        "header": "Навчальний помічник",
        "ph": "Повідомлення",
        "user2": "Розбери крок за кроком: 3x − 7 = 14",
        "body3": (
            "1. Мета: залишити x сам на одному боці.\n"
            "2. 3x − 7 = 14 → додай 7 до обох частин: 3x = 21.\n"
            "3. Поділи обидві частини на 3: x = 7.\n"
            "4. Перевірка: 3 × 7 − 7 = 14 ✓\n\n"
            "Приклад: якби було 2x = 10, ти б поділив обидві частини на 2 → x = 5.\n\n"
            "Головне правило: що робиш з однією частиною — роби й з іншою. "
            "Залишилося останнє ділення."
        ),
    },
}

# координаты вырезки ассетов из EN-эталона img/shot1.webp (замеры см. landing-qa)
ASSET_CROPS = {
    "avatar.png": (365, 137, 454, 228),
    "chevron.png": (42, 170, 61, 200),
    "dots.png": (969, 177, 1026, 189),
    "status.png": (844, 25, 996, 64),
    "clip.png": (56, 2231, 84, 2277),
}


def extract_assets(workdir: Path) -> None:
    """Вырезает ассеты из EN-эталона + копирует шрифты в рабочий каталог."""
    from PIL import Image

    src = Image.open(IMG / "shot1.webp").convert("RGB")
    adir = workdir / "assets"
    (adir / "fonts").mkdir(parents=True, exist_ok=True)
    for name, (x0, y0, x1, y1) in ASSET_CROPS.items():
        src.crop((x0, y0, x1, y1)).save(adir / name)
    for f in FONTS.glob("*.woff2"):
        shutil.copy(f, adir / "fonts" / f.name)


def load_i18n():
    sys.path.insert(0, str(BOT_DIR))
    from bot import i18n  # noqa: PLC0415
    return i18n


def build_shots(lang: str, i18n) -> dict:
    """Разметка сообщений для трёх кадров. Стиль согласован с EN-эталоном.

    Кнопки меню — из `MENU_KEYS` (порядок menu_kb() бота), не из литерала:
    бот добавил «Пригласить друга», генератор обязан это увидеть сам.
    """
    c = CANNED[lang]
    t = lambda k: i18n.t(lang, k)  # noqa: E731
    menu = [t(k) for k in MENU_KEYS]
    return {
        1: [
            ("user", "/start", "12:02"),
            ("bot", t("welcome"), "12:02"),
            ("kb", menu, None),
        ],
        2: [
            ("user", c["user2"], "12:04"),
            ("bot", t("task_received"), "12:04"),
            ("kb", [f"1. {t('task_type_1')}", f"2. {t('task_type_2')}", f"3. {t('task_type_3')}"], None),
        ],
        3: [
            ("bot", t("answer") + "\n\n" + c["body3"], "12:05"),
            ("kb", menu, None),
        ],
    }


def messages_html(msgs: list) -> str:
    out = []
    for kind, text, ts in msgs:
        if kind == "kb":
            rows = "".join(f'<div class="row">{html.escape(r)}</div>' for r in text)
            out.append(f'<div class="kb">{rows}</div>')
        else:
            ts_html = f'<div class="ts">{html.escape(ts)} ✓✓</div>' if kind == "user" \
                else f'<div class="ts">{html.escape(ts)}</div>'
            out.append(f'<div class="msg {kind}"><div class="body">{html.escape(text)}</div>{ts_html}</div>')
    return "".join(out)


def render_png(out_png: Path) -> None:
    """Рендер страницы (html рядом с out_png) в PNG через локальный Playwright/Chromium.

    Ретрай 3x: headless-скриншот иногда падает транзиентно (Protocol error
    Page.captureScreenshot) — повтор без изменения входных данных помогает.
    """
    import time

    from playwright.sync_api import sync_playwright

    last = None
    for attempt in range(3):
        try:
            with sync_playwright() as pw:
                b = pw.chromium.launch()
                pg = b.new_page(viewport={"width": 1080, "height": 2340}, device_scale_factor=1)
                pg.goto(out_png.with_suffix(".html").as_uri())
                pg.wait_for_function("document.fonts.status === 'loaded'", timeout=15000)
                pg.wait_for_timeout(120)
                pg.screenshot(path=str(out_png))
                b.close()
            return
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2)
    raise RuntimeError(f"render failed after 3 attempts: {last}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--langs", default="es,pt,hi,id,tr,vi,uk")
    ap.add_argument("--apply", action="store_true", help="записать webp в img/")
    ap.add_argument("--calib", action="store_true", help="разрешить en в превью (не пишет в img/)")
    ap.add_argument("--force", action="store_true", help="перезаписывать существующие webp")
    ap.add_argument("--force-en", action="store_true",
                    help="разрешить запись EN (эталон; нужен, когда меняется клавиатура)")
    ap.add_argument("--stamp", action="store_true", help="перештамповать реестр tools/shots.json")
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--workdir", default="/home/jar/.hermes/cache/scratch/shots-gen/work")
    args = ap.parse_args()

    from PIL import Image

    langs = [s.strip() for s in args.langs.split(",") if s.strip()]
    i18n = load_i18n()
    tpl = (HERE / "mockup.html").read_text(encoding="utf-8")
    work = Path(args.workdir)
    extract_assets(work)
    stats = []
    ledger_langs: dict[str, dict] = {}
    for lang in langs:
        if lang not in CANNED:
            print(f"{lang}: SKIP (нет CANNED-строк)")
            continue
        if lang == "en" and args.apply and not args.force_en:
            print("en: SKIP записи (эталон; --force-en, если менялась клавиатура)")
            continue
        ldir = work / lang
        ldir.mkdir(parents=True, exist_ok=True)
        if not (ldir / "assets").exists():
            (ldir / "assets").symlink_to(work / "assets")
        shots = build_shots(lang, i18n)
        c = CANNED[lang]
        shot_rows: dict[str, dict] = {}
        for n, msgs in shots.items():
            page = (tpl
                    .replace("{{LANG}}", lang)
                    .replace("{{SHOT}}", str(n))
                    .replace("{{NAME}}", html.escape(c["header"]))
                    .replace("{{PLACEHOLDER}}", html.escape(c["ph"]))
                    .replace("{{MESSAGES}}", messages_html(msgs)))
            (ldir / f"shot{n}.html").write_text(page, encoding="utf-8")
            png = ldir / f"shot{n}.png"
            render_png(png)
            line = f"{lang} shot{n}: png {png.stat().st_size // 1024} KiB -> "
            dst = IMG / (f"shot{n}.webp" if lang == "en" else f"shot{n}-{lang}.webp")
            if args.apply:
                if dst.exists() and not args.force:
                    line += f"{dst.name} EXISTS (skip; --force чтобы перезаписать)"
                else:
                    im = Image.open(png).convert("RGB")
                    im.save(dst, "WEBP", quality=args.quality, method=6)
                    line += f"{dst.name} {dst.stat().st_size // 1024} KiB"
            else:
                line += "(preview only)"
            if dst.exists():
                shot_rows[str(n)] = {"file": dst.name, "sha256": sha256(dst)}
            print(line)
            stats.append(line)
        drawn = {k: i18n.t(lang, k) for k in MENU_KEYS}
        drawn.update({
            "welcome": i18n.t(lang, "welcome"),
            "task_received": i18n.t(lang, "task_received"),
            "answer": i18n.t(lang, "answer"),
            "task_type_1": i18n.t(lang, "task_type_1"),
            "task_type_2": i18n.t(lang, "task_type_2"),
            "task_type_3": i18n.t(lang, "task_type_3"),
        })
        ledger_langs[lang] = {
            "texts": drawn,
            "canned": {k: c[k] for k in ("header", "ph", "user2", "body3")},
            "shots": shot_rows,
        }
    if args.stamp and args.apply:
        LEDGER.write_text(json.dumps({
            "note": ("Реестр макетов чата: sha256 каждого img/shotN[-<lang>].webp и ровно те "
                     "строки, что нарисованы (тексты бота + кернед-строки макета). Пишется "
                     "только генератором: python3 tools/shots-gen/gen_shots.py ... --apply --stamp. "
                     "Свип сверяет его с bot/ и с байтами файлов."),
            "menu_keys": list(MENU_KEYS),
            "langs": ledger_langs,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"реестр: {LEDGER.relative_to(REPO)} ({len(ledger_langs)} языков)")
    print("\nГотово:", len(stats), "кадров")


if __name__ == "__main__":
    main()
