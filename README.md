# UchiSamBot — landing page

Static landing page for **UchiSamBot**, a Telegram study helper: a student sends a photo of a task
and gets a step-by-step explanation back in the chat.

- **Live site:** published from the `gh-pages` branch.
- **Languages:** en, ru, es, pt, hi, id, tr, vi, uk.
- **Stack:** hand-written HTML and CSS, no framework and no build step for the page itself.
- **Contact:** the form on the page.

## Проверка

Сборка и проверки — из корня репозитория, без внешних сервисов:

```
python3 tools/build.py                    # пересобрать страницы и sitemap (идемпотентно)
python3 tools/check-site-technical.py     # шапки девяти языков, числа в словарях, живой сайт против дерева
python3 tools/check-links.py              # внешние адреса; реестр — tools/links-last-seen.json
python3 tools/check-weight.py             # вес страницы, ленивость картинок, потолки
python3 tools/visual-pass.py              # 420 px и десктоп: вылезание, обрезка, кнопки; снимки в evidence/
python3 tools/visual-pass.py --control    # проверка самого прибора: обязан поймать блок шире окна
```

`check-site-technical.py --offline` и `check-links.py --offline` работают без сети.
Снимки и JSON-доказательства лежат в `evidence/` и в репозиторий не попадают.

## Licence

Content and design: all rights reserved. Badge images in `img/badges/` belong to the respective
directory sites.
