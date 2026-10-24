#!/usr/bin/env python3
"""Плоский текст страницы для вычитки: одна строка на видимый блок, как статья.

    python3 tools/page-text.py index.html [--chars N]

Зачем переписан (24.10.2026). Прежняя версия снимала теги регуляркой, и это
давало три вещи, которых на странице нет:

  1. HTML-сущности оставались буквами. В подвале стоит `&middot;` между
     «Политикой» и «Условиями»; посетитель видит «·», а вычитка читала
     `&middot;` — то есть инструмент смыслового прохода показывал не символ,
     а его имя. Ни один гейт этого не видел: гейты читают собранную страницу
     своим кодом, где `html.unescape` уже был.

  2. Текст, которого посетитель не видит, попадал в чтение. `#contact-ok`,
     `#contact-err`, `#contact-err-busy` и кнопка остановки ролика лежат с
     атрибутом `hidden` до своей минуты; в выводе они стояли обычными
     предложениями, вклеенными в один абзац с вопросом «Есть вопрос или отзыв?».
     Читающий не мог отличить то, что видит посетитель, от того, что появится
     после отправки формы.

  3. Гранулярность была случайной. Регулярка брала САМЫЙ ВНЕШНИЙ блок и
     съедала вложенные: шапка с меню и переключателем языков выходила одной
     строкой на 300 знаков, а весь FAQ — одной строкой на 3 000. «По одной
     строке на блок» было неправдой там, где блок = `div`.

Теперь разбор идёт HTMLParser'ом: сущности раскрываются на входе, поддеревья с
`hidden`, `.sr-only` и `.hp` пропускаются, строку заканчивает КОНЕЦ блочного
тега (не начало), поэтому номер шага склеивается со своим заголовком
(«1 Открой бота»), а не висит отдельной строкой.

Чего этот инструмент НЕ умеет и не пытается: моделировать CSS. Кнопка
остановки ролика содержит оба слова («Пауза» и «Играть») и переключается
атрибутом `data-state` — в тексте будут оба; `display:none` из стилей не
разбирается. Содержимое `details` печатается всегда, в том числе закрытое:
смысловой проход должен читать ответы FAQ, а не только вопросы. Для «что
именно видно на экране» есть браузерные батареи, у них другой вопрос.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# конец этих тегов закрывает строку вывода
BLOCK = {
    "address", "article", "aside", "blockquote", "button", "dd", "details", "div",
    "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2",
    "h3", "h4", "h5", "h6", "header", "label", "legend", "li", "main", "nav", "ol",
    "p", "section", "summary", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
}
# поддеревья, которых на экране нет ни секунды
SKIP_TAG = {"script", "style", "svg", "template", "noscript", "head", "title"}
# классы, которыми контент убран с экрана (читает скринридер, не глаз)
SKIP_CLASS = {"sr-only", "hp"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}


class Flattener(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.buf: list[str] = []
        self.skip = 0
        self.stack: list[tuple[str, bool]] = []
        self.in_body = False

    # --- helpers
    def _flush(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf.clear()
        if len(text) >= 2:
            self.lines.append(text)

    @staticmethod
    def _hidden(attrs) -> bool:
        d = dict(attrs)
        if "hidden" in d:
            return True
        classes = set((d.get("class") or "").split())
        return bool(classes & SKIP_CLASS)

    # --- parser hooks
    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if tag == "br" and not self.skip:
                self._flush()
            return
        if tag == "body":
            self.in_body = True
        skipping = tag in SKIP_TAG or self._hidden(attrs)
        self.stack.append((tag, skipping))
        if skipping:
            self.skip += 1
        elif self.buf and not "".join(self.buf[-1:]).endswith(" "):
            # соседние элементы в разметке не разделены пробелом
            # («<span>1</span><h3>Открой бота</h3>», «…English</span><span>Русский…») — ставим свой
            self.buf.append(" ")

    def handle_startendtag(self, tag, attrs):
        if tag == "br" and not self.skip:
            self._flush()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        skipping = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                skipping = self.stack[i][1]
                del self.stack[i:]
                break
        if skipping and self.skip:
            self.skip -= 1
        if not self.skip and tag in BLOCK:
            self._flush()

    def handle_data(self, data):
        if self.in_body and not self.skip:
            self.buf.append(data)

    def close(self):
        super().close()
        self._flush()


def flatten(html: str) -> str:
    body = html.split("</head>", 1)[-1] if "</head>" in html else html
    p = Flattener()
    p.feed(body)
    p.close()
    return "\n".join(p.lines)


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
    text = flatten(path.read_text(encoding="utf-8"))
    if "--chars" in sys.argv:
        text = text[: int(sys.argv[sys.argv.index("--chars") + 1])]
    print(text)


if __name__ == "__main__":
    main()
