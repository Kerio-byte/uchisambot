"""Главное меню бота как источник правды для макетов чата (23.10.2026).

Зачем: макеты `img/shot1..3-<lang>.webp` рисуют инлайн-клавиатуру, которую
человек видит сразу после /start. Пока список кнопок был вписан в генератор
руками, бот успел получить кнопку «Пригласить друга» — и все девять
скриншотов продолжали показывать шесть кнопок. Каждый гейт был зелёным:
файлы на месте, размеры верные, alt-тексты из словаря. Никто не спрашивал
у бота, какие кнопки он на самом деле показывает.

Теперь порядок кнопок читается из `menu_kb()` в `bot/handlers.py` разбором
исходника (ast, только stdlib): генератор рисует ровно то, что бот отдаёт.

Запуск отдельно (для проверки руками): `python3 bot_menu.py <handlers.py>`.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

FUNCTION = "menu_kb"


class _Calls(ast.NodeVisitor):
    """Собирает аргументы вызовов `t(lang, "<key>")` в порядке исходника."""

    def __init__(self) -> None:
        self.keys: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 (ast API)
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id == "t" and len(node.args) >= 2:
            arg = node.args[1]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                self.keys.append(arg.value)
        self.generic_visit(node)


def menu_keys(handlers_path: str | Path) -> tuple[str, ...]:
    """Ключи словаря в порядке кнопок menu_kb(); исключение — если функции нет."""
    path = Path(handlers_path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    func = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == FUNCTION),
        None,
    )
    if func is None:
        raise ValueError(f"{FUNCTION}() не найдена в {path}")
    collector = _Calls()
    collector.visit(func)
    keys = tuple(collector.keys)
    if not keys:
        raise ValueError(f"{FUNCTION}() не содержит вызовов t(lang, key) — {path}")
    return keys


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("bot/handlers.py")
    print("\n".join(menu_keys(target)))
