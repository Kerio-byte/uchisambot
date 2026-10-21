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
- `img/` — logo (SVG), favicons, chat-shot mockups (WebP; `shot1-3.webp` = EN,
  `shotN-<lang>.webp` = each of the other eight languages, see "Chat shots" below),
  social preview cards (`og-<lang>.png`, 1200×630 — one per language, see "Social
  preview cards" below; `og.png` is the earlier English card, kept for already-shared
  links and the two legal pages), hero video posters (`demo-poster*.webp`).
- `tools/og-cards.py` — renders the per-language social preview cards from
  `src/locales/*.json` with Playwright/Chromium (one 1200×630 template: icon, name,
  `foot.tag` tagline, `f1t · f2t · f5t` feature line, `t.me/UchiSamBot`); see
  "Social preview cards" below.
- `tools/shots-gen/` — generator for the per-language chat-shot mockups
  (`gen_shots.py` + `mockup.html` + Inter subsets under `assets/fonts/`); see
  "Chat shots" below. EN/RU shots are frozen references — the generator renders
  the other seven languages.
- `demo/` — demo videos: full 35 s (EN/RU, H.264 720×1560 30 fps, compressed to
  ≤1 MiB / ≤1.5 MiB, direct-linked from `llms.txt` and external platforms) and
  web-optimized hero loops — one per language, each carrying step captions in the
  page language: `*-web.mp4` (EN) / `*-web-<lang>.mp4` for the other eight. Loop
  weight budgets (QA sweep): EN ≤768 KB, RU ≤900 KB, the seven others ≤512 KB.
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

Reproducible build: `tools/build.py` is deterministic — a second run on unchanged
sources leaves the worktree clean. `sitemap.xml`’s `<lastmod>` comes from a content
ledger, `tools/lastmod.json` (`{url: {sha, date}}`, sha256 of the page bytes): a date
only moves when that page’s content actually changes, so a plain rebuild no longer
rewrites all eleven dates to the build day and the date never claims an edit that did
not happen. Commit `tools/lastmod.json` with the generated pages; the QA sweep
re-hashes every page and fails when the ledger is stale (page edited without a
rebuild, or sitemap date ≠ ledger date).

Hero video (per-language loops): every language page plays its OWN 13 s loop with the
two step captions in the page language — `demo/uchiambot-demo-web.mp4` (EN, the kit
build) and `demo/uchiambot-demo-web-<lang>.mp4` for the other eight (RU rebuilt; the
seven es/pt/hi/id/tr/vi/uk loops added 17 Oct 2026), poster `img/demo-poster[-<lang>].webp`
(last frame of the loop). Captions are the site dictionary terms (`how.s2t` /
`shot3.alt` core), e.g. RU `2 · Отправь задачу — текстом или фото` / `3 · Пошаговый
разбор`, ES `2 · Envía tu tarea — texto o foto` / `3 · Desglose paso a paso`. RU:
rebuild with `demo/build-web-loop-ru.sh`; the other seven loops and the poster of any
language: `demo/build-web-loop-langs.sh [lang …]` — same zoompan/drawtext pipeline as
the kit build (13.0 s, 720×1560, x264 veryslow crf30; poster = frame 389 → 540×1170
WebP). Sources are the per-language chat-shot PNG renders from `tools/shots-gen` —
regenerate them first if the scratch workdir is gone (`gen_shots.py --langs …`). Two
deliberate render notes: the hi loop uses Noto Sans Devanagari Bold, whose glyph set
has no `·` (U+00B7), so its step separator is `.`; drawtext `text_shaping` (on by
default) shapes the Devanagari conjuncts.

Demo video weights: the eleven `demo/` files have soft budgets enforced by the QA sweep —
full `uchiambot-demo.mp4` ≤1 MiB, `uchiambot-demo-ru.mp4` ≤1.5 MiB, the nine hero loops:
EN ≤768 KB, RU ≤900 KB, the other seven ≤512 KB. Re-encode with x264 (`-crf`, preset
`veryslow`, H.264 High, 720×1560,
30 fps, `-movflags +faststart`) and keep the exact file names — external platforms and
`llms.txt` link these URLs directly.

Page weight: the QA sweep also enforces a per-language budget — the page plus every
local asset it references (chat shots, hero loop, posters, fonts) must stay ≤1.25 MiB
(measured worst case ~1.1 MiB). External links and third-party-hosted badge assets are
checked by a separate network-bound audit (`landing-external-links.py` in the
stars-bots-ops skill scripts) during site passes — not part of the headless sweep,
because third-party sites can be slow or timeout.

Keep `meta.desc` at ≤160 characters per language: the same string feeds
`meta description`, `og:description`, `twitter:description` and the JSON-LD
description, and longer text gets truncated in search results.

Typography: Manrope variable, self-hosted in `fonts/` (5 subsets). Pages preload the
subset matching the language (latin by default, cyrillic for `/ru/` and `/uk/`);
`privacy.html` / `terms.html` load fonts from the same folder.

Headline scale: `h1` runs `clamp(30px, 5.4vw, 56px)` at weight 800, letter-spacing −.03em
(desktop cap 56px — council round-1 typographic scale); section heads and cards keep the
existing clamp steps.

Surfaces (de-SaaS tail, council round 1): flat `#F7FAFF` page background (the former top
radial tint is gone), flat brand buttons (hover = tone shift `#2F49D8` + 1px lift, no glow),
exactly two shadow tokens (`--shadow`, `--shadow-2`) and a four-value radius scale
(12 / 18 / 24 / 999 — tokens `--sky`/`--tg` removed).

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

CTA tags: the hero button keeps `?start=src_landing`, the closing band button uses
`?start=src_landing_band`, the sticky bar `?start=src_landing_sticky` (the bot records
the first touch per user and accepts any `src_*` payload). The sweep pins all three —
exactly one plain `src_landing` link must remain (the hero).

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

Screenshots rail: on viewports ≤860px the three cards form a horizontal scroll-snap rail
(each card ≈86% wide with the next one peeking; `scroll-snap-type: x mandatory`, hidden
scrollbar) — the section no longer stacks into ~2600 px of vertical scroll on phones. On
desktop the grid is `1.2fr 1fr 1fr`, so the first card reads larger (council round-1 fix).

Section numbers: the six main sections (How it works … FAQ) carry a decorative `01`–`06`
kicker above the headline (`.sec-num`, small brand-blue). It is a plain `aria-hidden`
`<p>` outside the `H2` — the numbers never enter the heading text (SEO requirement,
council round 1) and stay out of the markdown twins.

Chat shots (per-language mockups): every language page shows its OWN chat mockups —
`shot1-3.webp` (EN) and `shotN-<lang>.webp` for ru, es, pt, hi, id, tr, vi, uk. The
`shot_src()` step in `tools/build.py` picks the language file, falling back to EN only
if a file is missing (a missing file is a defect — the QA sweep fails any language page
that falls back). The shots are Telegram-style chat mockups (1080×2340, flat colours),
generated by `tools/shots-gen/gen_shots.py`: text comes from the bot's own i18n
(`../study-bot/bot/i18n.py` — single source of truth; the mockup-only canned lines —
the user's request, the sample answer, the input-bar placeholder — live in the
generator's `CANNED` dict), rendering is local Playwright/Chromium with the Inter font
(OFL subsets in `tools/shots-gen/assets/fonts/`; emoji from the system font, Devanagari
falls back to Noto Sans Devanagari), and the shared chrome (avatar, chevron, three-dot
menu, status icons, paperclip) is cropped from the frozen EN shot at render time.

Regenerate (after bot-text or mockup changes):

```bash
python3 tools/shots-gen/gen_shots.py --langs es,pt,hi,id,tr,vi,uk            # preview PNGs
python3 tools/shots-gen/gen_shots.py --langs es,pt,hi,id,tr,vi,uk --apply  # write img/
```

EN/RU shots are reference images — do not overwrite them; `--langs en --calib` renders
an EN calibration build into the work dir only (it must stay visually identical to
`img/shot1-3.webp`, which is how the template was tuned).

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
it does not know yet) and the `scroll-snap-*` properties in media contexts / pairs
(validator parser bug, proven by a minimal-HTML bisect on 17 Oct — see
`landing-qa.md`, "Сверка с решениями совета") — all intentional progressive
enhancements.

User environment preferences: the hero video and the reveal animation respect
`prefers-reduced-motion: reduce` (poster instead of the loop, every `.rv` visible from
the start, `scroll-behavior: auto`, no sticky-bar transition) and
`navigator.connection.saveData` (same video fallback; the reveal intentionally stays on).
Windows high-contrast mode (`forced-colors: active`) drops author backgrounds, so a small
media rule restores a 1 px border on the interactive nodes that would otherwise render as
plain text: `.btn` (hero, band, sticky), the contact submit (its `border:0` comes from
`.contact button.btn`, so that higher-specificity selector is repeated inside the rule)
and the language-switcher summary. The light design does not react to
`prefers-color-scheme` (delta-checked under a dark system preference; no `color-scheme`
declaration). Covered by `landing-env-prefs.py` (45 checks, forced-colors screenshots
included) and by the sweep's `fc btn border` marker on every language page.

Footer: one centered "Featured on" strip of official launch-platform badges — Fazier,
StartupBase, ShowMeBestAI, LiftOff, Startup Fame, OpenHunts Club, Aura++ (LaunchIgniter
badge sits in the hero, as its platform requires). Uniform 46 px height (40 px on small
screens), lazy-loaded hotlinked official assets, links open in a new tab with
`rel="noopener"`. Badge links point at the platform's product page where one exists
(Fazier: `fazier.com/launches/uchisambot-study-helper`; the hotlinked badge asset uses
the canonical single-slash path `fazier.com/api/v1/public/…`). `privacy.html` /
`terms.html` carry the required LiftOff + Startup Fame badges in the same style.

Earned award badge (21.10.2026): on 19 Oct 2026 LiftOff placed UchiSamBot (Study Helper)
#1 in its daily competition and issued a proof badge for it. It is the platform's own
asset, hotlinked like the rest — `/images/badges/day/badge1DayLight.webp`, 360×120 — and
sits next to the LiftOff launch badge in the same strip, on the nine language pages and on
both legal pages. Because it is not a "Featured on" badge it gets its own dictionary line,
`badge.award` ("No. 1 of the Day on LiftOff" / "Продукт дня №1 на LiftOff" …): `tools/build.py`
bakes it per language and asserts exactly one match per page, and the sweep pins the asset
path, the localised alt and the do-follow link on every page. The link stays a plain
`rel="noopener"` (no `nofollow` / `sponsored` / `ugc`): `lift-off.sh/legal/badge-policy`
requires a crawlable do-follow link and forbids self-made "earned proof" badges or custom
variants, so nothing here is drawn, re-typeset or recoloured locally.

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

Social preview cards (`og:image`): every language page points at its OWN 1200×630
card, `img/og-<lang>.png` (`og-en.png` for the root page). Until 21 Oct 2026 all nine
pages shared one English `og.png`, so a link to `/hi/` or `/es/` shared in Telegram or
WhatsApp previewed with English text — the same gap the screenshots and hero loops had
before their per-language pass. The cards are rendered from the same dictionaries:

    python3 tools/og-cards.py              # all nine
    python3 tools/og-cards.py --langs ru,es
    python3 tools/og-cards.py --check      # only verify size/resolution of existing files

The renderer also writes `tools/og-cards.lock.json` — a fingerprint of the four
dictionary strings that go on each card plus a SHA-256 of the PNG. Cards are committed
artifacts and the build never re-renders them, so editing a locale string would
otherwise leave a stale picture behind; the QA sweep compares the lock against the
current dictionaries and the file on disk and fails with "og card text in sync" until
the card is re-rendered (`--check` reports the same drift).

One template (light-blue gradient, app icon, name, `foot.tag` tagline,
`f1t · f2t · f5t` feature line, `t.me/UchiSamBot`). The tagline auto-shrinks to fit the
column; the feature line may wrap only BETWEEN features (each is a `nowrap` segment) —
a plain wrap broke Russian as "Задачи с / фото" and Spanish as "Tareas con / foto".
`hi` falls back to the system Noto Sans Devanagari (Manrope has no Devanagari subset);
the rendered conjuncts and matras were reviewed on the produced PNG. The old `og.png`
is never overwritten — already-shared links and the two legal pages keep it. The build
bakes the per-language absolute URL into both `og:image` and `twitter:image`, and the
QA sweep asserts per language that the page points at its own file, that the file
exists on disk, and that no page still references `og.png`.

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
This form is the site's single support channel: the FAQ answer about failed
breakdowns, privacy and terms all point visitors here — no page promises an in-bot
message-to-team path (the bot's Help button only shows payment guidance), and the
sweep fails any page that references one.

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
