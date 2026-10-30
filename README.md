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
python3 tools/probe-narrow.py             # 320 px (узкий iPhone SE): вылезание и обрезка на девяти языках
python3 tools/claim-basis.py              # основание обещаний в живом продукте: адрес LLM, веса, служба, Linger, девять языков
python3 tools/legal-tail-read.py --root . --out evidence/legal-tail-$(date +%Y%m%d).json
                                          # нижняя часть privacy/terms глазами: последний раздел и подвал
python3 tools/probe-anchors.py --sections faq,contact
                                          # опоры, против которых глаз сверяет кадр, без вызова модели
```

`legal-tail-read.py` и `probe-anchors.py` работают только вместе с прибором `landing-eye.py`,
который лежит вне этого дерева (публичный репозиторий серверных путей не хранит). Оба ищут его
одинаково: `--eye PATH`, затем переменная `LANDING_EYE`, затем домашнее дерево скиллов.
30.10.2026 у обоих был один и тот же дефект: `probe-anchors.py` жил только по явному пути и из
дерева всегда выходил кодом 1, а `legal-tail-read.py` звал `headline_agrees` — имя, которое прибор
потерял при переписывании 29.10, — и падал в `AttributeError` на каждом запуске, то есть хвост
правовых документов после переписывания не читал никто. Теперь имя сверки спрашивается у прибора
(`headline_agrees`, иначе `agrees`), и оба прибора дают код 0 на чистом дереве.

Смысл обещаний сверяется реестрами, а не глазами. Три прибора живут рядом со скиллом
`earn-hunt/stars-bots-ops/scripts` (они ходят в соседний репозиторий бота, поэтому лежат
не в этом дереве):

```
landing-sweep.py         # слова страницы против tools/claims.json: 3046 проверок на девяти языках
landing-price-parity.py  # цены страницы против tools/prices.json и против bot/payments.py (XTR, паки, реферал)
landing-answer-time.py   # «сколько ждать разбор»: живой замер production-путём бота против tools/answer-time.json
```

`landing-answer-time.py` сам переходит в `venv` бота: замер идёт через `bot.handlers`, а он тянет
aiogram, и под системным python прибор раньше падал голым traceback вместо замера. Замер пишется
в реестр ключом `--write` (сессия: дата, модель, состояние очереди GPU до/после, секунды по задачам).

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
