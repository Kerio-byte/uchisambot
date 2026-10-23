#!/bin/bash
# tools/publish-branch.sh — выложить ТОЛЬКО сайт, без мастерской.
#
# Зачем (23.10.2026). Сайт публиковался из корня ветки main, а в корне лежит вся
# мастерская: README.md с инженерным дневником (196 КБ), tools/, src/, demo/*.py,
# собранный шаблон index-src.html, кадры evidence/. GitHub Pages отдаёт всё это по
# прямым адресам (/README.md → 200): дневник, схема базы и устройства бота были
# открыты любому, кто угадает имя файла. Пока источник публикации — корень main,
# убрать мастерскую нельзя; можно только не писать в неё адреса и пути (это делает свип).
#
# Что сделано 24.10.2026. Источник публикации переключён на ветку gh-pages (в ней
# ровно те файлы, что перечисляет tools/publish-tree.py: 115 файлов, 10.7 МБ).
# Переключение — одноразовое действие в настройках репозитория, сделано через API:
#   gh api -X PUT repos/<owner>/<repo>/pages \
#          -f 'source[branch]=gh-pages' -f 'source[path]=/' -f 'build_type=legacy'
# Обратно (если понадобится): -f 'source[branch]=main'.
#
# С этого дня сайт двигает ТОЛЬКО этот скрипт: обычный push в main ветку gh-pages не
# трогает, и мир продолжает видеть вчерашнюю сборку. Отставшую публикацию ловят две
# проверки свипа («публикация: …»: мастерская не отдаётся, живой сайт = сборка) и
# landing-live-bytes.py (полное сравнение дерева).
#
# Использование:
#   bash tools/publish-branch.sh --dry-run   # собрать дерево и проверить его локальным сервером
#   bash tools/publish-branch.sh             # обновить ветку gh-pages во всех зеркалах
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
git checkout --quiet --orphan "$BRANCH"
cp -a "$WORK/tree/." .
git add -A
git -c user.name="$(git -C "$ROOT" config user.name)" -c user.email="$(git -C "$ROOT" config user.email)" \
    commit --quiet -m "publish: only the site ($COUNT files), no workshop

Источник публикации: tools/publish-tree.py. Мастерская (tools/, src/,
demo/*.py|sh|json, README.md, index-src.html, evidence/) в ветку не попадает.
Правки страниц сайта выкладываются ТОЛЬКО этим скриптом."

# Оба зеркала: GitHub отдаёт сайт, Forgejo хранит резерв. Падение одного зеркала не
# должно отменять уже сделанный push в другое — поэтому предупреждение, а не выход.
# Адрес берётся у основного репозитория: во временном (одноразовом) своих remote нет.
for R in $(git -C "$ROOT" remote); do
  URL=$(git -C "$ROOT" remote get-url "$R")
  git remote remove "$R" 2>/dev/null || true
  git remote add "$R" "$URL"
  if git push --quiet --force "$R" "$BRANCH" 2>/dev/null; then
    echo "ветка $BRANCH -> $R ($URL)"
  else
    echo "ВНИМАНИЕ: $R не принял ветку $BRANCH — проверить доступ"
  fi
done

# Проверка источника публикации. Молчаливый провал этого шага — самый дорогой:
# ветка gh-pages обновлена, а сайт по-прежнему отдаётся из main, и правки не видны.
if command -v gh >/dev/null 2>&1; then
  SLUG=$(git -C "$ROOT" remote get-url origin | sed -E 's#^.*github\.com[:/]##; s#\.git$##')
  SRC=$(gh api "repos/$SLUG/pages" --jq '.source.branch + .source.path' 2>/dev/null || true)
  if [ -z "$SRC" ]; then
    echo "ВНИМАНИЕ: настройки Pages у $SLUG не прочитались — проверить глазами"
  elif [ "$SRC" != "$BRANCH/" ]; then
    echo "ВНИМАНИЕ: Pages отдаёт из '$SRC', а не из '$BRANCH/'. Ветка обновлена, но мир"
    echo "          увидит её только после переключения источника публикации."
    exit 1
  else
    echo "источник публикации: $BRANCH/ — совпадает"
  fi
fi
