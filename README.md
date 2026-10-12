# UchiSamBot — landing page

Static landing page for **@UchiSamBot** (Study Helper) — a Telegram bot that
breaks down school homework step by step, explains topics in simple words,
checks solutions and makes flashcards.

Live: https://kerio-byte.github.io/uchisambot/

## Structure

- `index.html` — the entire page: layout, styles and the EN/RU language toggle.
  No build step, no dependencies, no tracking.
- `img/` — logo (SVG), favicons, app screenshots (WebP) and the social preview
  image (`og.png`).

## Editing

Edit `index.html` directly and push to `main`; GitHub Pages serves the site
from the repository root. When editing texts, update both language dictionaries
(`I18N.en` / `I18N.ru`) and the matching `data-i18n` attributes.
