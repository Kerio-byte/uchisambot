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
python3 tools/check-redirects.py          # переходы http→https, слэши языков, /index.html, 404
python3 tools/check-redirects.py --control  # проверка самого прибора: обязан покраснеть на кривых ответах
python3 tools/check-redirects.py --offline  # без сети: canonical, hreflang, отсутствие ссылок на /en/
python3 tools/visual-pass.py              # 420 px и десктоп: вылезание, обрезка, кнопки; снимки в evidence/
python3 tools/visual-pass.py --control    # проверка самого прибора: обязан поймать блок шире окна
python3 tools/claim-basis.py              # основание обещаний в живом продукте: адрес LLM, веса, служба, Linger, девять языков
```

`tools/check-redirects.py` держит адресную поверхность: плоский http обязан уводить на https,
`/xx` — на `/xx/`, неизвестный вложенный адрес — отдавать 404 со своей страницей, canonical каждой
страницы — указывать на неё саму, а `/index.html` — схлопываться в корень каноническим адресом
(GitHub Pages редирект отдать не может). Список языков берётся из hreflang живой страницы, а не из
головы. `--control` подаёт прибору пять заведомо кривых ответов и требует, чтобы он покраснел на
всех пяти.

`tools/claim-basis.py` смотрит за пределы страницы: читает маршрут LLM из `.env` бота
(три ключа, секреты не печатаются), требует петлевой адрес и локальные веса в ответе
`/v1/models`, ищет в коде бота адреса сторонних ИИ-сервисов и проверяет, что
`study-bot.service` у менеджера пользователя `active`, `enabled` и `Linger=yes`.
`--offline` пропускает сетевой запрос к модели, `--json` кладёт доказательство в `evidence/`.
Обещания «круглосуточно», «своя инфраструктура» и «девять языков» держатся на этих десяти
проверках, а не на словах. Языковая часть читает кортеж `SUPPORTED` в `bot/i18n.py`:
страница не имеет права обещать язык, на котором бот не говорит, и каждая языковая
страница обязана звать бота своим кодом (`src_landing_hi` с `/hi/`). Прибор проверен
контролем: с бота, у которого отнят `uk`, он краснеет.

`check-site-technical.py --offline` и `check-links.py --offline` работают без сети.
Снимки и JSON-доказательства лежат в `evidence/` и в репозиторий не попадают.

## Licence

Content and design: all rights reserved. Badge images in `img/badges/` belong to the respective
directory sites.
