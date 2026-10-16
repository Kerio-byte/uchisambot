# UchiSamBot — landing page

Static landing page for **@UchiSamBot** (Study Helper) — a Telegram bot that
breaks down school homework step by step, explains topics in simple words,
checks solutions and makes flashcards.

Live: https://kerio-byte.github.io/uchisambot/

## Structure

- `index-src.html` — source template with `data-i18n` keys (EN texts inside).
- `src/locales/*.json` — text dictionaries for 9 languages (en, ru, es, pt, hi, id, tr, vi, uk).
- `tools/build.py` — static site generator (stdlib only): bakes the template into
  `index.html` (EN) + `ru/`, `es/`, `pt/`, `hi/`, `id/`, `tr/`, `vi/`, `uk/` pages and their
  markdown twins (`index.html.md` next to each page), and converts the `main`
  content of the legal pages into their markdown twins (`privacy.html.md` /
  `terms.html.md`), plus
  `sitemap.xml` and `llms.txt`; every language page carries its own `og:locale`
  plus `og:locale:alternate` for the other eight languages (social-preview locale
  linking), and the sitemap mirrors the hreflang set per URL — all nine languages
  plus `x-default` pointing at the English root. No runtime, no dependencies, no
  tracking.
- `img/` — logo (SVG), favicons, app screenshots (WebP, EN + RU variants), social
  preview image (`og.png`), hero video posters (`demo-poster*.webp`).
- `demo/` — demo videos: full 35 s (EN/RU, H.264 720×1560 30 fps, compressed to
  ≤1 MiB / ≤1.5 MiB, direct-linked from `llms.txt` and external platforms) and
  web-optimized hero loops (`*-web.mp4`, ≤768 KB / ≤900 KB).
- `fonts/` — self-hosted Manrope variable font (OFL, `LICENSE-OFL.txt`): latin,
  latin-ext, cyrillic, cyrillic-ext, vietnamese subsets (~64 KB total); preload +
  `font-display: swap`, system fallback. No CDN.

## Editing

1. Edit texts/styles in `index-src.html` (translations in `src/locales/*.json`);
   legal texts — directly in `privacy.html` / `terms.html`.
2. Run `python3 tools/build.py` — regenerates all 9 language pages, their markdown
   twins (`index.html.md`), the legal-page markdown twins (`privacy.html.md` /
   `terms.html.md` — converted from the legal pages' own `main` content), sitemap
   and llms.txt.
3. Commit the template + locales + generated pages together and push to `main`;
   GitHub Pages serves the site from the repository root.

Hero video: `demo/uchiambot-demo-web.mp4` (EN) / `demo/uchiambot-demo-web-ru.mp4` (RU),
poster `img/demo-poster.webp` / `img/demo-poster-ru.webp`.

Demo video weights: the four `demo/` files have soft budgets enforced by the QA sweep —
full `uchiambot-demo.mp4` ≤1 MiB, `uchiambot-demo-ru.mp4` ≤1.5 MiB, web loops ≤768 KB
and ≤900 KB. Re-encode with x264 (`-crf`, preset `veryslow`, H.264 High, 720×1560,
30 fps, `-movflags +faststart`) and keep the exact file names — external platforms and
`llms.txt` link these URLs directly.

Keep `meta.desc` at ≤160 characters per language: the same string feeds
`meta description`, `og:description`, `twitter:description` and the JSON-LD
description, and longer text gets truncated in search results.

Typography: Manrope variable, self-hosted in `fonts/` (5 subsets). Pages preload the
subset matching the language (latin by default, cyrillic for `/ru/` and `/uk/`);
`privacy.html` / `terms.html` load fonts from the same folder.

Favicons: every page (landing, privacy, terms) declares `img/logo.svg` (SVG, for
browsers that support it), `img/icon-64.png` (PNG, 64×64 — the format Google
Search's favicon pipeline supports; SVG is not in its format list) and
`img/icon-180.png` (iOS touch icon).

Sticky CTA (mobile only, viewport ≤860px): fixed bottom bar with the main Telegram
button (`?start=src_landing_sticky`). Appears after ~700px of scroll, hides when the
contact form (`#contact`) or the footer is in view (IntersectionObserver; without JS
it stays hidden). Safe-area aware via the two-declaration pattern (`padding:6px 14px;`
fallback, then `calc(6px + env(safe-area-inset-bottom))`) — browsers without `env()`
support still get sane padding; modern browsers are unaffected (second declaration wins).
Markup + inline script live in `index-src.html`.

Micro-interactions: keyboard focus ring (`:focus-visible`, 2px brand, offset — everywhere
interactive), press feedback on buttons (`:active`), smooth FAQ open/close (~180 ms via
`::details-content` + `interpolate-size`; browsers without support get the old instant
toggle), opacity-only scroll reveal (IntersectionObserver adds `rv-in` to `.rv` elements;
disabled under `prefers-reduced-motion`; without JS everything stays visible), small
transition polish on nav/lang/FAQ-summary hovers, and `scroll-padding-top: 84px` so
anchor jumps clear the sticky header. Smooth scrolling is turned off under
`prefers-reduced-motion`.

Screenshots: each of the three chat shots in the "Real chats" section carries a small
caption naming the how-it-works step it shows (the `how.s1t`-`how.s3t` texts), baked
into all 9 language pages. The shots' `alt` texts are localised per language (dictionary
keys `shot1.alt`-`shot3.alt`); `og:image:alt` / `twitter:image:alt` reuse the page title,
and the JSON-LD `Offer` names reuse the pricing texts (`p1t`, `price.single`, `p2t`, `p3t`).

Contrast (WCAG AA): the closing CTA band is a solid ink plate (`#0E1526`) — white
headline 18:1, `#EAF0FF` body line 15.9:1, white Telegram button 5.1:1; the footer
secondary lines use `#5C6E90` (4.9:1 on the page background instead of the former
`#8194B4` at 2.9:1).

Accessibility: each page is a single `<main id="main">` landmark (header and footer
sit outside it; the mobile sticky CTA bar lives inside `main`). Every page opens with
a keyboard skip link (`.skip` → `#main`, label localised through the `a11y.skip`
dictionary key) that slides in at the top-left on focus; the `main:focus` outline is
suppressed because the skip jump itself is the cue. Audited with axe-core
(WCAG 2.0-2.2 A/AA + best practice): 0 violations across all 11 pages. The W3C Nu
validator reports only `interpolate-size` / `transition:allow-discrete` (modern CSS
it does not know yet) — both are intentional progressive enhancements.

Footer: one centered "Featured on" strip of official launch-platform badges — Fazier,
StartupBase, ShowMeBestAI, LiftOff, Startup Fame, OpenHunts Club, Aura++ (LaunchIgniter
badge sits in the hero, as its platform requires). Uniform 46 px height (40 px on small
screens), lazy-loaded hotlinked official assets, links open in a new tab with
`rel="noopener"`. `privacy.html` / `terms.html` carry the required LiftOff + Startup
Fame badges in the same style.

Badge accessibility / layout-shift: badge `alt` texts are localised per language — the
`badge.alt` dictionary template ("Featured on {name}" / "Отмечен на {name}" …) is baked
with the platform name, and the strip's group label comes from `badge.group`; the
`privacy.html` / `terms.html` badges use the English wording. Every badge (and every
other `img` on the site) declares both `width` and `height`, and those values must keep
the asset's **true aspect ratio** — measured from the served file (`naturalWidth` /
`naturalHeight` in a browser), not copied from embed snippets: with a one-sided or
wrong ratio the browser reserves the wrong slot before the lazy image loads and the
strip visibly jumps (measured up to ~53 px per badge before the fix; now the reserved
width equals the final width). The CSS `height:46px;width:auto` rule keeps rendering
unchanged — the attributes only affect the pre-load reservation. Hover `title`s on
badge links were dropped: they duplicated the alt text in English on every language
page.

Screen-reader labels: the header logo `alt` and the language-switcher summary
`aria-label` are localised via the `logo.alt` / `lang.aria` dictionary keys on all
nine language pages (both were the same English string on every page before, so a
screen reader on `/ru/`, `/hi/`, `/es/` … announced English). The build asserts the
logo replacement hits exactly one `<img>` per page. `privacy.html` / `terms.html`
keep the English wording, like their badges — bilingual EN-first pages.

Connections: the head warms up the third-party origins the pages actually use —
`preconnect` to `launchigniter.com` (the hero badge is the only eager external image)
and `dns-prefetch` to the seven footer badge hosts plus the form API
(`api.web3forms.com`). Footer badge assets are lazy, so a full preconnect there would
only burn sockets — DNS warm-up is the right level. `privacy.html` / `terms.html`
carry `dns-prefetch` for their two badge hosts.

Contact form: `#contact` posts straight to Web3Forms — no Telegram step. After a
successful submit Web3Forms returns the visitor to the **same language page**
(`?sent=1#contact`, rewritten per language by the build), where the form is replaced
by a localized confirmation message that is baked into the page (one string per
language, no JS dictionary; without JS the visitor simply keeps seeing the form).

Privacy / terms: bilingual single pages (EN, then the Russian section marked
`id="ru"`). Each page keeps exactly one `H1` (the English title): the Russian
section title is an `H2` styled like the page title (`.pg-ttl`), and its
numbered sections are `H3` — one clean heading outline per page. Links from
`/ru/` carry the `#ru` anchor, so Russian visitors land directly on the Russian
text; links from the other languages open the page top (EN). Both pages carry a
self-canonical URL and a full social-preview set — `og` and `twitter` title,
description, the shared `img/og.png` (1200×630, image alt = page title) — so
shared links get a proper preview card. The hashes are added by `tools/build.py`.

AI layer (llms.txt v2): every page has a clean markdown twin next to it —
`index.html.md` / `ru/index.html.md` … for the nine language pages (generated from
the locale dictionaries by `tools/build.py`) and `privacy.html.md` /
`terms.html.md` for the legal pages (converted from the `main` content of the
hand-written HTML, their single source of truth; a strict converter — unexpected
markup fails the build). Each page declares two link relations in the head:
`rel="describedby"` → `llms.txt` (the site-wide overview, which lists all eleven
markdown twins and the demo videos) and `rel="alternate" type="text/markdown"` →
that page's markdown twin. The links in `llms.txt` point to the markdown
versions — the convention of llms.txt v2 (llmstxt.org): markdown twin at the page
URL + `.md`.
