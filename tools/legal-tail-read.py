#!/usr/bin/env python3
"""legal-tail-read.py — глаз читает НИЖНЮЮ часть правового документа (29.10.2026, 26-й блок).

Зачем: 25-й блок прочитал документы сверху и честно записал предел — глаз видел только
открытие. Хвост политики высотой 7 620 px не читал никто: страница, которая рисует
шапку и теряет подвал, остаётся зелёной по геометрии и невидимой для глаза.

Устройство (предохранители, чтобы не соврать в зелёное):
  1. опора берётся из файла В ПОРЯДКЕ ЧТЕНИЯ: последний нумерованный раздел вывода
     tools/page-text.py («9. Контакты», «13. Контакты»). Файл-порядок не равен порядку
     чтения: русская половина документа размечена <h3>, и «последний h2 файла» — это
     английское «9. Contact». Заголовок документа опорой быть не может: в хвосте его
     не видно, спрашивать его значило бы спрашивать память модели;
  2. подвал: нижняя полоса ссылок сверяется с последней строкой того же сглаживателя —
     это первое, что теряется, если страницу обрезает посредник;
  3. контроль: кадры одного документа, опора — заголовок ДРУГОГО; обязан покраснеть.
     Прибор, который запомнил строку и повторяет её, здесь позеленеет.

Прибор (landing-eye.py) не прописан путём: репозиторий публичный, серверных путей и имён
нашего софта в нём быть не должно (opsec свипа). Ищется по `--eye`, затем по переменной
окружения LANDING_EYE, затем по домашнему дереву скиллов.

Запуск:
  python3 tools/legal-tail-read.py --root . [--frames evidence/legal-tail-20261029]
                                     [--docs privacy,terms] [--out <json>] [--eye <путь>]
Код возврата: 0 — хвосты прочитаны и совпали с файлами; 1 — иначе (или прибор недоступен).
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.error
from pathlib import Path

EYE_ENV = "LANDING_EYE"
DOCS = {"privacy": "privacy.html", "terms": "terms.html"}

TAIL_PROMPT = """Ты — приёмщик вёрстки документа. Тебе дают ОДИН кадр: НИЖНЯЯ часть страницы правового документа (последние 1200 пикселей).
Это не лендинг: текст в одну колонку — норма.

Строго по формату, без рассуждений:
HEADLINE: <дословно заголовок раздела, который стоит НИЖЕ всех остальных на кадре; если заголовков нет -> ->
LINE: <дословно последняя строка обычного текста на кадре, над самой нижней полосой ссылок>
FOOTER: <дословно текст ссылок в самой нижней полосе кадра; если полосы нет -> ->
LANG: <язык текста>
DEFECTS: none
или
DEFECTS:
- <что именно: текст обрезан нижним краем, текст налезает на текст, текст не читается из-за контраста, подвал отсутствует, пустое место вместо конца документа>

Дефектом считается только видимое. НЕ дефект: узкая колонка, шрифт, цвет, длина документа, отсутствие того, чего в документе нет по замыслу.
Не выдумывай дефектов. Если всё цело — ровно `DEFECTS: none`.
"""


def find_eye(given: str = "") -> Path | None:
    """Прибор ищется, а не прописывается: публичный репозиторий не хранит серверных путей."""
    for cand in (given, os.environ.get(EYE_ENV, "")):
        if cand.strip():
            p = Path(cand).expanduser()
            return p if p.is_file() else None
    hits = sorted(Path.home().glob("*/skills/**/landing-eye.py"))
    return hits[0] if hits else None


def load_eye(path: Path):
    spec = importlib.util.spec_from_file_location("landing_eye", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"FAIL прибор не загружается: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def page_text(path: Path) -> list[str]:
    """Строки страницы в порядке чтения — вывод tools/page-text.py, без своих правил."""
    flat = path.parent / "tools" / "page-text.py"
    if not flat.is_file():
        return []
    proc = subprocess.run([sys.executable, str(flat), str(path)],
                          capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        return []
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def last_section_heading(lines: list[str]) -> str:
    numbered = [ln for ln in lines if re.match(r"^\d+\.\s*\S", ln)]
    return numbered[-1] if numbered else ""


def last_footer_line(lines: list[str]) -> str:
    return lines[-1] if lines else ""


def parse_footer(answer: str) -> str:
    m = re.search(r"^FOOTER:\s*(.*)$", answer, re.M)
    if not m:
        return ""
    val = m.group(1).strip()
    return "" if val in {"->", "—", "-", "none", "нет"} else val


def read_tail(eye_mod, frames: Path, doc: str) -> dict:
    path = frames.parent.parent / DOCS[doc]
    lines = page_text(path)
    expected = last_section_heading(lines)
    exp_footer = last_footer_line(lines)
    frame = frames / f"{doc}-d.png"
    row = {"doc": doc, "frame": frame.name, "expected_heading": expected, "seen_heading": "",
           "seen_line": "", "expected_footer": exp_footer, "seen_footer": "", "footer_ok": False,
           "footer_grounding": "", "lang": "", "defects": [], "grounded": False, "grounding": "",
           "parsed": False, "raw": "", "verdict": ""}
    if not expected:
        row["verdict"] = "UNGROUNDED"
        row["grounding"] = "в порядке чтения нет нумерованного раздела — сверять не с чем"
        return row
    if not frame.is_file():
        row["verdict"] = "FAIL"
        row["grounding"] = f"нет кадра {frame.name}"
        return row
    try:
        answer = eye_mod.ask(TAIL_PROMPT, [frame])
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        row["verdict"] = "UNAVAILABLE"
        row["grounding"] = f"глаз недоступен ({exc.__class__.__name__})"
        return row
    if not answer:
        row["verdict"] = "UNAVAILABLE"
        row["grounding"] = "глаз молчит (пустой ответ)"
        return row
    got = eye_mod.parse(answer)
    row.update({"seen_heading": got["headline"], "seen_line": got["line"], "lang": got["lang"],
                "defects": got["defects"], "parsed": got["parsed"], "raw": answer})
    if not got["parsed"]:
        row["verdict"] = "FAIL"
        row["grounding"] = "ответ вне формата"
        return row
    ok, why = eye_mod.headline_agrees(expected, got["headline"] or got["line"])
    row["grounded"], row["grounding"] = ok, why
    seen_footer = parse_footer(answer)
    row["seen_footer"] = seen_footer
    f_ok, f_why = (eye_mod.headline_agrees(exp_footer, seen_footer) if exp_footer
                   else (False, "нет опоры подвала"))
    row["footer_ok"], row["footer_grounding"] = f_ok, f_why
    if not ok:
        row["verdict"] = "UNGROUNDED"
    elif not f_ok:
        row["verdict"] = "FAIL"
        row["grounding"] = f"{why}; подвал не прочитан ({f_why})"
    elif got["defects"]:
        row["verdict"] = "DEFECT"
    else:
        row["verdict"] = "PASS"
    return row


def control(eye_mod, frames: Path, docs: list[str]) -> bool | None:
    """Чужой заголовок на этих кадрах обязан покраснеть."""
    a, b = docs[0], docs[1]
    expected = eye_mod.headline_of(frames.parent.parent / DOCS[a])
    frame = frames / f"{b}-d.png"
    if not expected or not frame.is_file():
        print("CONTROL: пропущен (нет заголовка или кадра)")
        return None
    try:
        answer = eye_mod.ask(TAIL_PROMPT, [frame])
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"CONTROL: модель недоступна ({exc.__class__.__name__})")
        return None
    got = eye_mod.parse(answer)
    ok, why = eye_mod.headline_agrees(expected, got["headline"] or got["line"])
    if ok:
        print(f"CONTROL FAIL: заголовок «{expected}» принят на хвосте {b} ({why})")
        return False
    print(f"CONTROL: заголовок «{expected}» отвергнут на хвосте {b} ({why})")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--frames", default="")
    ap.add_argument("--docs", default="privacy,terms")
    ap.add_argument("--out", default="")
    ap.add_argument("--eye", default="")
    ap.add_argument("--no-control", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    frames = root / args.frames if args.frames else (root / "evidence/legal-tail-20261029")
    if not frames.is_dir():
        print(f"FAIL кадров хвоста нет: {frames}")
        return 1
    docs = [d for d in args.docs.split(",") if d]
    unknown = [d for d in docs if d not in DOCS]
    if unknown:
        print(f"FAIL неизвестный документ: {', '.join(unknown)}")
        return 1
    eye_path = find_eye(args.eye)
    if eye_path is None:
        print(f"FAIL прибор не найден (--eye или {EYE_ENV})")
        return 1

    eye_mod = load_eye(eye_path)
    rows = [read_tail(eye_mod, frames, d) for d in docs]
    for r in rows:
        if r["verdict"] == "PASS":
            print(f"PASS {r['doc']}: хвост прочитан, «{r['seen_heading'][:40]}» — {r['grounding']}; "
                  f"подвал «{r['seen_footer'][:50]}» — {r['footer_grounding']}")
        elif r["verdict"] == "DEFECT":
            print(f"DEFECT {r['doc']}: {len(r['defects'])} шт.")
            for d in r["defects"]:
                print(f"   - {d}")
        else:
            print(f"{r['verdict']} {r['doc']}: {r['grounding']}")

    ctl = None if args.no_control or len(docs) < 2 else control(eye_mod, frames, docs)
    bad = sum(1 for r in rows if r["verdict"] != "PASS")
    summary = {"frames_dir": str(frames), "docs": docs, "checked": len(rows), "bad": bad,
               "control": ctl, "rows": rows}
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nИТОГО по хвостам: документов {len(rows)}, не прошло {bad}, контроль {ctl}")
    return 0 if bad == 0 and ctl is not False and rows else 1


if __name__ == "__main__":
    sys.exit(main())
