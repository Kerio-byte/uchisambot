# UchiSamBot — landing page

Static landing page for **@UchiSamBot** (Study Helper) — a Telegram bot that
breaks down school homework step by step, explains topics in simple words,
checks solutions and makes flashcards.

Live: https://kerio-byte.github.io/uchisambot/

## Structure

- `index-src.html` — source template with `data-i18n` keys (EN texts inside).
- `src/locales/*.json` — text dictionaries for 9 languages (en, ru, es, pt, hi, id, tr, vi, uk).
- `tools/build.py` — static site generator (stdlib only): bakes the template into
  `index.html` (EN) + `ru/`, `es/`, `pt/`, `hi/`, `id/`, `tr/`, `vi/`, `uk/` pages, plus
  `sitemap.xml` and `llms.txt`. No runtime, no dependencies, no tracking.
- `img/` — logo (SVG), favicons, app screenshots (WebP, EN + RU variants), social
  preview image (`og.png`), hero video posters (`demo-poster*.webp`).
- `demo/` — demo videos: full 35 s (EN/RU) and web-optimized hero loops (`*-web.mp4`).
- `fonts/` — self-hosted Manrope variable font (OFL, `LICENSE-OFL.txt`): latin,
  latin-ext, cyrillic, cyrillic-ext, vietnamese subsets (~64 KB total); preload +
  `font-display: swap`, system fallback. No CDN.

## Editing

1. Edit texts/styles in `index-src.html` (translations in `src/locales/*.json`).
2. Run `python3 tools/build.py` — regenerates all 9 language pages, sitemap and llms.txt.
3. Commit the template + locales + generated pages together and push to `main`;
   GitHub Pages serves the site from the repository root.

Hero video: `demo/uchiambot-demo-web.mp4` (EN) / `demo/uchiambot-demo-web-ru.mp4` (RU),
poster `img/demo-poster.webp` / `img/demo-poster-ru.webp`.

Typography: Manrope variable, self-hosted in `fonts/` (5 subsets). Pages preload the
subset matching the language (latin by default, cyrillic for `/ru/` and `/uk/`);
`privacy.html` / `terms.html` load fonts from the same folder.

Sticky CTA (mobile only, viewport ≤860px): fixed bottom bar with the main Telegram
button (`?start=src_landing_sticky`). Appears after ~700px of scroll, hides when the
contact form (`#contact`) or the footer is in view (IntersectionObserver; without JS
it stays hidden). Safe-area aware. Markup + inline script live in `index-src.html`.
