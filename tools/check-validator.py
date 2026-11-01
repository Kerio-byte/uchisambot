#!/usr/bin/env python3
"""check-validator.py — посторонний валидатор HTML, который зовётся каждый прогон.

Повод (02.11.2026, блок 47). 01.11 в README появилась строка «валидаторы» с честной
припиской: это РАЗОВЫЙ аудит. Одиннадцать страниц прочитал `html-validate` 11.17.0,
нашёл 132 находки (123 `void-style` + 9 `aria-label-misuse`), ноль структурных — и
на этом всё. Прибором его не завели по двум названным причинам: `node_modules`
уехал бы в опубликованные байты, и README обещает «no build step».

Обе причины верны, и обе обходятся, не ломая ни одной:

  1) Валидатор ставится ВНЕ дерева публикации: путь задаётся переменной
     `LANDING_VALIDATOR_PREFIX` (по умолчанию — каталог кэша в домашнем
     каталоге пользователя, имя каталога `landing-validator`).
     Прибор это не обещает, а ПРОВЕРЯЕТ: если `node_modules`, `package.json` или
     `package-lock.json` появятся внутри дерева публикации — красное, потому что
     именно этого мы боялись.
  2) «No build step» — про страницу, а не про проверку. Без валидатора страница
     собирается и живёт как жила; проверка в этом случае печатает ПРОПУСК и код 3,
     то есть молчания нет — есть названная дыра в отчёте.

Что сторожит прибор, чего не сторожил разовый аудит:

  A. Версия валидатора закреплена: правила `html-validate:recommended` меняются
     между версиями, и «прогнали когда-то» не значит «правила те же». Другая
     версия — красное с обоими номерами.
  B. Снимок находок сверяется побайтно по счёту (файл + правило): находка
     ПРИБАВИЛАСЬ — красное с файлом, строкой и правилом; находка ИСЧЕЗЛА —
     тоже красное, но другим словом: снимок стар, его надо обновить, иначе он
     врёт в сторону «всё как было».
  C. Снимок не имеет права прятать структурный класс. Разрешены ровно два
     косметических правила, оба разобраны в README (`void-style`,
     `aria-label-misuse`). Появился `element-permitted-content`, `close-order`,
     `no-dup-id` и любой другой класс — красное: baseline не мешок, под который
     заметают настоящую ошибку разметки.
  D. Число страниц берётся из `publish-tree.manifest()` — единственного места, где
     перечислен сайт, а не из своего списка: разъехавшиеся списки уже один раз
     прятали страницу от сверки (см. докстринг `live-bytes.py`).

Чем прибор НЕ является (чтобы зелёное не читалось шире, чем оно есть): он не
исполняет JavaScript (валидатор видит разметку, а не поведение), не читает
md-двойники и llms.txt (это не HTML), не заменяет axe (правила доступности у
валидатора — подмножество чужих) и не спорит с двумя принятыми находками: 132
косметические записаны в снимок как принятые, а не вылечены. Отдельно замерено
02.11: в наборе `recommended` НЕТ класса «два элемента с одним id» — повтор id
ловит свой `check-markup`, а не посторонний валидатор, и ждать от него этого
нельзя.

  python3 tools/check-validator.py                # дерево против снимка
  python3 tools/check-validator.py --control      # шесть мутантов обязаны покраснеть
  python3 tools/check-validator.py --write-baseline  # переснять снимок (громко скажет, что записал)

Нет Node, нет пакета, нет сети на установку — ПРОПУСК и код 3, а не зелёное.
"""

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "tools" / "validator-baseline.json"
PREFIX = Path(__import__("os").environ.get(
    "LANDING_VALIDATOR_PREFIX", Path.home() / ".cache" / "landing-validator"))
VERSION = "11.17.0"
# Ровно два класса, разобранные в README: разметка одного смысла двумя способами
# и имя ролика, которое нельзя записать иначе. Всё остальное — не косметика.
ALLOWED = ("void-style", "aria-label-misuse")
INSTALL = f"npm i --prefix {PREFIX} html-validate@{VERSION}"
TREE_LEAKS = ("node_modules", "package.json", "package-lock.json")


def manifest_pages() -> list[str]:
    """Страницы для валидатора — из списка публикации, а не из своего перечня."""
    spec = importlib.util.spec_from_file_location("publish_tree", ROOT / "tools" / "publish-tree.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("tools/publish-tree.py не читается")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [f for f in mod.manifest() if f.endswith(".html")]


def binary() -> Path:
    return PREFIX / "node_modules" / ".bin" / "html-validate"


def version_of(binp: Path) -> str:
    out = subprocess.run([str(binp), "--version"], capture_output=True, text=True, timeout=60)
    text = (out.stdout or "") + (out.stderr or "")
    return text.strip().splitlines()[-1].replace("html-validate-", "") if text.strip() else "?"


def leaks() -> list[str]:
    """Причина, по которой аудит не стал прибором: пакеты внутри публикуемого дерева."""
    bad = []
    for name in TREE_LEAKS:
        for p in ROOT.rglob(name):
            rel = p.relative_to(ROOT).as_posix()
            if ".git" in rel.split("/") or "evidence" in rel.split("/"):
                continue
            bad.append(rel)
    return sorted(bad)


def run(binp: Path, pages: list[str], root: Path | None = None) -> tuple[dict, list[str]]:
    """Находки по (файл, правило) плюс поимённый список для сообщений.

    Вывод валидатора пишется в ФАЙЛ, а не в пайп. Это не стиль: html-validate на
    pipe отдаёт обрезанный JSON (замер 02.11: 54 050 байт, строка рвётся на
    середине ответа, `json.decoder` падает на «Unterminated string»). Причина —
    Node теряет асинхронный буфер на выходе процесса; в файл тот же прогон пишет
    все 132 находки целиком. Ошибка коварная: она выглядит как «валидатор сломался»,
    а не как «прибор не умеет его читать».
    """
    base = root or ROOT
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as fh:
        outf = Path(fh.name)
    try:
        with open(outf, "w", encoding="utf-8") as fout:
            out = subprocess.run([str(binp), "--formatter", "json"] + pages, cwd=str(base),
                                 stdout=fout, stderr=subprocess.PIPE, text=True, timeout=300)
        text = outf.read_text(encoding="utf-8")
    finally:
        outf.unlink(missing_ok=True)
    if not text.strip().startswith("["):
        raise RuntimeError(text[:400] + (out.stderr or "")[:400])
    counts, named = Counter(), []
    for f in json.loads(text):
        rel = Path(f.get("filePath", "?")).resolve().relative_to(base.resolve()).as_posix()
        for m in f.get("messages", []):
            rule = m.get("ruleId") or "?"
            counts[(rel, rule)] += 1
            named.append(f"{rel}:{m.get('line', '?')} {rule}: {m.get('message', '')[:70]}")
    return dict(counts), named


def snapshot(counts: dict) -> dict:
    per: dict[str, dict[str, int]] = {}
    for (rel, rule), n in sorted(counts.items()):
        per.setdefault(rel, {})[rule] = n
    return {"validator": f"html-validate@{VERSION}", "allowed_rules": list(ALLOWED),
            "measured_on": "11 published pages, tree of 02.11.2026", "findings": per}


def compare(counts: dict, base: dict) -> tuple[int, list[str]]:
    """Счёт против снимка в ОБЕ стороны. Возвращает (проверок, красных)."""
    checks, bad = 0, []
    want = {(rel, rule): n for rel, rules in base.get("findings", {}).items()
            for rule, n in rules.items()}
    for key in sorted(set(want) | set(counts)):
        rel, rule = key
        checks += 1
        got, was = counts.get(key, 0), want.get(key, 0)
        if got > was:
            bad.append(f"новая находка {rel} / {rule}: было {was}, стало {got} — "
                       f"это не косметика, пока её не разобрали")
        elif got < was:
            bad.append(f"снимок стар {rel} / {rule}: записано {was}, найдено {got} — "
                       f"обнови tools/validator-baseline.json")
    return checks, bad


def guard_tree() -> list[str]:
    return [f"{rel}: пакет внутри публикуемого дерева — ровно та причина, по которой "
            f"аудит не стал прибором" for rel in leaks()]


def guard_baseline(base: dict) -> list[str]:
    bad = []
    if base.get("validator") != f"html-validate@{VERSION}":
        bad.append(f"снимок снят прибором {base.get('validator')}, а стоит {VERSION}: "
                   f"правила по умолчанию могли поменяться")
    for rule in base.get("allowed_rules", []):
        if rule not in ALLOWED:
            bad.append(f"снимок объявил разрешённым правило '{rule}' — разрешены только "
                       f"{', '.join(ALLOWED)}: структурную ошибку прятать нельзя")
    for rule in {r for rules in base.get("findings", {}).values() for r in rules}:
        if rule not in ALLOWED:
            bad.append(f"в снимок записано правило '{rule}' — не косметика, чинить разметку")
    return bad


def check(root_pages: list[str] | None = None) -> tuple[int, list[str]]:
    binp = binary()
    pages = root_pages if root_pages is not None else manifest_pages()
    counts, _named = run(binp, pages)
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    checks, bad = compare(counts, base)
    checks += len(pages)
    bad += guard_tree() + guard_baseline(base)
    return checks, bad


def write_baseline() -> int:
    counts, named = run(binary(), manifest_pages())
    base = snapshot(counts)
    structural = [r for r in {x[1] for x in counts} if r not in ALLOWED]
    if structural:
        print(f"ОТКАЗ: снимок не пишется, пока в дереве есть не косметика: {structural}")
        for line in named[:10]:
            print("  ", line)
        return 1
    BASELINE.write_text(json.dumps(base, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    total = sum(counts.values())
    print(f"СНИМОК ЗАПИСАН: {len(base['findings'])} файлов, {total} находок, "
          f"правила {sorted({x[1] for x in counts})}")
    print("Проверь глазами, что новых находок нет: снимок — это принятое, а не прощённое.")
    return 0


def control() -> int:
    binp = binary()
    tmp = Path(tempfile.mkdtemp(prefix="validator-control-"))
    try:
        clean = tmp / "clean"
        shutil.copytree(ROOT, clean, ignore=shutil.ignore_patterns(
            ".git", "evidence", "tools", "src", "node_modules", ".shots-work", "*~"))
        pages = [p for p in manifest_pages() if (clean / p).exists()]
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        counts, _ = run(binp, pages, clean)
        _c, bad = compare(counts, base)
        if bad:
            print("КОНТРОЛЬ СЛОМАН: чистая копия не совпала со снимком:")
            for line in bad:
                print("  ", line)
            return 1
        mutants = [
            ("void-style", "ru/index.html", lambda t: t.replace("</body>", "<br /></body>", 1),
             "новая находка ru/index.html / void-style"),
            ("close-order", "index.html", lambda t: t.replace("</section>", "", 1),
             "новая находка index.html /"),
            # Повтор атрибута на одном элементе: браузер молча возьмёт последний.
            # Именно `no-dup-attr`, а не `no-dup-id`: замер 02.11 показал, что в
            # наборе по умолчанию класса «два элемента с одним id» НЕТ вовсе —
            # повтор id сторожит свой `check-markup`, и это записано в README.
            ("dup-attr", "es/index.html", _dup_attr, "новая находка es/index.html /"),
            ("leak", None, None, "пакет внутри публикуемого дерева"),
            ("baseline-структурное", None, None, "не косметика"),
            ("baseline-версия", None, None, "правила по умолчанию могли поменяться"),
        ]
        caught, summary = 0, []
        for name, rel, mut, expect in mutants:
            mut_root = tmp / f"m-{name}"
            shutil.copytree(clean, mut_root)
            if name == "leak":
                (mut_root / "node_modules" / "x").mkdir(parents=True)
                hits = _guard_in(mut_root)
            elif name.startswith("baseline"):
                bent = json.loads(json.dumps(base))
                if name == "baseline-структурное":
                    bent["findings"].setdefault("index.html", {})["close-order"] = 1
                else:
                    bent["validator"] = "html-validate@9.9.9"
                hits = guard_baseline(bent)
            else:
                page = mut_root / rel
                page.write_text(mut(page.read_text(encoding="utf-8")), encoding="utf-8")
                got, _ = run(binp, pages, mut_root)
                _c, hits = compare(got, base)
            ok = any(expect in h for h in hits)
            caught += 1 if ok else 0
            summary.append(f"{name}: {'поймал' if ok else 'НЕ ПОЙМАЛ'}")
        print("КОНТРОЛЬ:", "; ".join(summary))
        print(f"поймал {caught} из {len(mutants)}")
        return 0 if caught == len(mutants) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _dup_attr(text: str) -> str:
    """Два одинаковых атрибута на одном элементе: браузер молча возьмёт последний."""
    return text.replace("<body>", '<body class="a" class="b">', 1)


def _guard_in(root: Path) -> list[str]:
    bad = []
    for name in TREE_LEAKS:
        for p in root.rglob(name):
            rel = p.relative_to(root).as_posix()
            if ".git" in rel.split("/") or "evidence" in rel.split("/"):
                continue
            bad.append(f"{rel}: пакет внутри публикуемого дерева — ровно та причина, по которой "
                       f"аудит не стал прибором")
    return sorted(bad)


def main() -> int:
    ap = argparse.ArgumentParser(description="посторонний валидатор HTML против снимка находок")
    ap.add_argument("--control", action="store_true", help="шесть мутантов обязаны покраснеть")
    ap.add_argument("--write-baseline", action="store_true", help="переснять снимок находок")
    a = ap.parse_args()
    binp = binary()
    if not binp.exists():
        print(f"ПРОПУСК: html-validate не установлен вне дерева ({PREFIX}) — разметку "
              f"посторонним валидатором не читали. Поставить: {INSTALL}")
        return 3
    got = version_of(binp)
    if got != VERSION:
        print(f"КРАСНО: стоит html-validate {got}, а снимок и прибор говорят про {VERSION} — "
              f"правила по умолчанию могли поменяться")
        return 1
    if a.write_baseline:
        return write_baseline()
    if a.control:
        return control()
    checks, bad = check()
    for line in bad:
        print("  КРАСНО:", line)
    print(f"CHECKS: {checks}, FAILED: {len(bad)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
