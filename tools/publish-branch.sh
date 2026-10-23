#!/bin/bash
# tools/publish-branch.sh — выложить ТОЛЬКО сайт, без мастерской.
#
# Зачем (23.10.2026). Сайт публикуется из корня ветки main, а в корне лежит вся
# мастерская: README.md с инженерным дневником (196 КБ), tools/, src/, demo/*.py,
# собранный шаблон index-src.html. GitHub Pages отдаёт всё это по прямым адресам
# (/README.md → 200). Пока источник публикации — корень main, убрать мастерскую
# нельзя; можно только не писать в неё адреса и пути (это делает свип).
#
# Настоящее разделение — отдельная ветка публикации: в ней лежат ровно те файлы,
# что перечисляет tools/publish-tree.py. Переключение источника — один клик в
# GitHub: Settings → Pages → Branch: gh-pages / (root). Скрипт его НЕ делает.
#
# Использование:
#   bash tools/publish-branch.sh --dry-run   # собрать дерево и проверить его локальным сервером
#   bash tools/publish-branch.sh             # создать/обновить ветку gh-pages и запушить в origin
#
# После переключения Pages на gh-pages сайт обновляется ТОЛЬКО этим скриптом:
# обычный push в main его не двигает. Отставшую публикацию ловит
# landing-live-bytes.py (сравнивает живой сайт с деревом).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
BRANCH="${BRANCH:-gh-pages}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

python3 "$HERE/publish-tree.py" --check
python3 "$HERE/publish-tree.py" --stage "$WORK/tree" >/dev/null
COUNT=$(find "$WORK/tree" -type f | wc -l)
echo "в дереве публикации: $COUNT файлов"

if [ "${1:-}" = "--dry-run" ] || [ "${1:-}" = "--serve" ]; then
  python3 "$HERE/publish-tree.py" --verify-served "$WORK/tree"
  exit 0
fi

cd "$WORK"
git init --quiet pub
cd pub
git remote add origin "$(git -C "$ROOT" remote get-url origin)"
git checkout --quiet --orphan "$BRANCH"
cp -a "$WORK/tree/." .
git add -A
git -c user.name="$(git -C "$ROOT" config user.name)" -c user.email="$(git -C "$ROOT" config user.email)" \
    commit --quiet -m "publish: only the site ($COUNT files), no workshop

Источник публикации: tools/publish-tree.py. Мастерская (tools/, src/,
demo/*.py|sh|json, README.md, index-src.html, evidence/) в ветку не попадает.
Обновлять сайт после переключения Pages: bash tools/publish-branch.sh"
git push --quiet --force origin "$BRANCH"
echo "ветка $BRANCH отправлена в origin ($(git remote get-url origin))"
echo "осталось одно действие владельца: Settings → Pages → Source: Deploy from a branch → $BRANCH / (root)"
