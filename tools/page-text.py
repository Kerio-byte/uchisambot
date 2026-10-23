#!/usr/bin/env python3
"""Плоский текст страницы для вычитки: теги сняты, скрипты/стили выброшены.

    python3 tools/page-text.py index.html [--chars N]

Печатает по одному блоку на строку, чтобы глазами читать как статью.
"""
import re
import sys
from pathlib import Path

BLOCK = re.compile(r"<(p|h1|h2|h3|h4|li|summary|figcaption|label|button|a|span|div)\b[^>]*>(.*?)</\1>", re.S)
DROP = re.compile(r"<(script|style|svg)\b.*?</\1>", re.S)
TAG = re.compile(r"<[^>]+>")


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
    limit = 0
    if "--chars" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--chars") + 1])
    html = path.read_text(encoding="utf-8")
    html = DROP.sub(" ", html)
    body = html.split("</head>", 1)[-1]
    seen = []
    for m in BLOCK.finditer(body):
        inner = TAG.sub(" ", m.group(2))
        text = re.sub(r"\s+", " ", inner).strip()
        if not text or len(text) < 2:
            continue
        seen.append(text)
    out = "\n".join(seen)
    print(out if not limit else out[:limit])


if __name__ == "__main__":
    main()
