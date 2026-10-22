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
- `tools/site.json` — single source of the site address (`base`, plus `previous`:
  older addresses of this site). Added 22 Oct 2026, before the move to an own
  domain: the address used to live in three independent places — a literal in
  `tools/build.py`, literals in `index-src.html` (canonical, `og:url`, JSON-LD,
  the contact form's `redirect`) and the hand-written `privacy.html`, `terms.html`
  and `robots.txt`. The build rewrote canonical/`og:url` with regexes but matched
  the form `redirect` against the template literal, so on a domain change the
  redirect would silently keep the **old** host: a visitor submits the form and
  lands on the previous site. Now the template carries a `{{BASE}}` token, the
  build substitutes it (and fails if a literal comes back), and the hand-written
  files are normalized on every build by replacing each address from `previous`.
  Moving to a domain is: set `base`, move the old value into `previous`, run
  `tools/build.py`. `landing-site-move-test.py` (stars-bots-ops skill) proves the
  move on a throwaway copy — canonical, `og:url`, `og:image`, the site address in
  the policy prose (EN and RU), the form `redirect` per language, `robots.txt`,
  `sitemap.xml`, `404.html`, `llms.txt` — 17 checks; and the sweep fails if any
  old address survives or a literal returns to the template. The build itself also
  audits its own output after writing (22 Oct 2026, added by the reviewer): if any
  file still carries a foreign `https://<host>/uchisambot/` address, it exits 1 and
  names the files — a half-done move cannot be committed even without the sweep.
- `tools/prices.json` — single source of the prices (`free_breakdowns`, `single`,
  `pack5` / `pack15` as `{size, price}`, `currency`): `tools/build.py` writes these
  numbers into the JSON-LD `Offer` nodes, and the QA sweep checks every language page
  against the same file (see the prices paragraph under "Editing"). Added 21 Oct 2026 — before that the
  JSON-LD numbers were literals inside `build.py` and the visible prices were strings
  in nine dictionaries, so a one-sided price edit could silently make the structured
  data and the page disagree.
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
- `demo/captions.py` — the **single source of every word burned into a video**
  (22 Oct 2026): the hero loop's two step captions are `how.s2t` and `shot3.alt`
  without the brand, the full demo's intro tagline is `foot.tag` and its outro
  promise is `hero.chip1`; the handful of video-only phrases (the "text or photo"
  tail, the two outro buttons) are listed in one table. `demo/captions.json` is
  the ledger: the strings actually baked, plus sha256 of each loop, its poster and
  each full demo. `demo/build-web-loop-langs.sh [lang …]` and
  `demo/build-full-demo.sh en|ru` ask that script for every line and re-stamp the
  ledger; the QA sweep fails when the dictionary, the ledger and the bytes
  disagree. `landing-sweep.py` checks the ledger, `landing-poster-frames.py`
  (stars-bots-ops) checks that a poster really is its loop's last frame.
- `fonts/` — self-hosted Manrope variable font (OFL, `LICENSE-OFL.txt`): latin,
  latin-ext, cyrillic, cyrillic-ext, vietnamese subsets (~64 KB total); preload +
  `font-display: swap`, system fallback. No CDN. Plus Noto Sans Devanagari (OFL,
  `LICENSE-OFL-NotoSansDevanagari.txt`, ~121 KB, `wght 400..800`) for the Hindi page
  only: Manrope has no Devanagari glyphs, so `/hi/` used to fall back to a system font
  with two weights — 800 and 600 rendered identically and 500 collapsed to 400. The
  file is scoped by `unicode-range` (`U+0900-097F` …), so the other eight languages
  never download it; it is deliberately not preloaded (the page text renders at once in
  the fallback, the webfont only upgrades the weights).
  Plus the three **switcher mini subsets** (22 Oct 2026) — `langs-cyrillic.woff2`
  (2.9 KB), `langs-vietnamese.woff2` (1.2 KB), `langs-devanagari.woff2` (4.9 KB) —
  declared as the family `UchiSam Langs` and carrying exactly the glyphs of the nine
  language names, so opening the language menu costs 4–9 KB instead of 127–141 KB.
  They are generated by `tools/make-lang-fonts.py` (fontTools; run once, assets are
  committed) and registered, byte count and sha256, in `tools/lang-fonts.json`, which
  `tools/build.py` refuses to ignore.
- `404.html` — own not-found page (added 21 Oct 2026): brand card, the nine
  language chips and the bot CTA, instead of GitHub Pages' generic English 404.
  Generated by `tools/build.py` (`page_404()`), **not** hand-edited; its URLs are
  absolute (`BASE + …`) on purpose — GitHub Pages serves this file for *any*
  unknown path, so a relative `href`/`src` would resolve against the broken URL
  and die. `noindex,follow`, absent from `sitemap.xml` (a 404 must not be indexed),
  not in the `lastmod` ledger. QA sweep fails on any relative URL inside it.

## Editing

1. Edit texts/styles in `index-src.html` (translations in `src/locales/*.json`);
   legal texts — directly in `privacy.html` / `terms.html`. Never type the site
   address into any of them: the template carries `{{BASE}}` and the value lives
   only in `tools/site.json` (the build refuses a literal in the template).
2. Run `python3 tools/build.py` — regenerates all 9 language pages, their markdown
   twins (`index.html.md`), the legal-page markdown twins (`privacy.html.md` /
   `terms.html.md` — converted from the legal pages' own `main` content), `404.html`,
   sitemap and llms.txt.
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
default) shapes the Devanagari conjuncts. Every caption line comes from
`demo/captions.py` (see Structure); a rebuild refreshes the language's poster and
re-stamps `demo/captions.json`, and the sweep fails if you forget either. The full
35 s demos are rebuilt the same way: `bash demo/build-full-demo.sh en|ru`.

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

Prices have one source, `tools/prices.json`. The build writes those numbers into the
JSON-LD `Offer` nodes, and the QA sweep re-reads the file to check all nine language
pages: the structured-data prices must equal the file, and the visible strings must
carry the same numbers — pack prices (`p2p` / `p3p`), pack sizes (`p2t` / `p3t`), the
free count (`p1t`), the single price (`price.fine`), and the per-breakdown figure and
discount percentage (`p2d` / `p3d`) computed from those same numbers. A price change
is therefore: `tools/prices.json` → the nine dictionaries → `bot/payments.py` (the
product) → rebuild. The cross-repo check `landing-price-parity.py` (stars-bots-ops
skill) compares the file with the bot's `Plan` tuples and `FREE_TRIALS`, because a bot
price change never rebuilds the site. The sweep also pins the JSON-LD shape (the four
node types and ten FAQ answers with non-empty text): a broken graph does not break the
page, search engines just drop the rich result silently.

The free limit is named in five dictionary keys, and since 22 Oct 2026 the sweep checks
all of them, not just `p1t`: `hero.chip1`, `cta.sub`, `q4a` and `meta.desc` must carry the
`free_breakdowns` number from `tools/prices.json` *and* be present on the built page. Before
that, a free-tier change updated `prices.json` and `p1t`, the sweep stayed green, and the
first screen could still promise the old number. The same pass ties the FAQ to itself: every
JSON-LD `Question`/`Answer` must equal the visible `<details>` text (HTML stripped, whitespace
normalised), because search engines only show marked-up answers that are visible on the page —
the two copies used to drift silently. `llms.txt`’s tagline is likewise pinned to the English
`meta.desc`, so the AI-facing layer cannot keep an outdated promise either.

Legal pages are hand-written and live outside the generator, so their numbers are checked
too (added 21 Oct 2026). The sweep parses both language sections of `terms.html` and
compares the free count and the three prices with `tools/prices.json`, the subject list
with the `subj.c1`…`subj.c5` chips of the matching dictionary, and the nine-language list;
the referral numbers must agree between the English and Russian halves, and
`landing-price-parity.py` compares them with the bot's `REFERRAL_BONUS` /
`REFERRAL_MAX_CREDITS`. This closed a real defect: the English section said “Subjects:
mathematics, **Russian language**, …” while the English page and its chips say “English” —
the legal text had been copied from the Russian half and nobody checked meaning, only
markup. Legal dates are a per-page ledger in the sweep: both language halves must name the
same day, that day must not be in the future, and a text change bumps that page's date
(Terms: 21 October 2026; Privacy unchanged at 17 October 2026).

Dictionaries are strictly parallel: every locale must carry exactly the key set of
`en.json`, values must be non-empty, and every `data-i18n` / `data-i18n-ph` key used in
`index-src.html` must exist in all nine dictionaries — `tools/build.py` refuses to build
otherwise (gate added 21 Oct 2026). Before it, a missing key was invisible: `rep_i18n`
keeps the English text from the template when the dictionary has no entry, so a forgotten
translation shipped as an English line on `/hi/` while the build and the sweep stayed
green (every check ran on key names it already knew, and a brand-new key was nobody's
expectation). `contact.ph_email` (`you@example.com`) is the single deliberate English
value — a format example, not copy; a long English value anywhere else fails the sweep
(`dict no EN copy`).

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

WCAG 2.2 AA extras — target size (2.5.8) and focus not obscured (2.4.11): a dedicated
battery, `landing-wcag22-targets.py` (43 checks), measures every non-inline pointer
target on all 11 pages at 390 and 1440 px and walks the tab order with real `Tab` presses
(no synthetic `focus()`, which would park each element mid-screen and hide the defect).
It found four gaps, all closed: the LaunchIgniter hero badge link was 212×22 px
(`min-height: 24px` on the link), the `.privacy-link` under the parents block was 23.2 px
tall (1 px vertical padding), the legal-page footer links were 19 px tall
(`display: inline-block; padding: 3px 0` → 29 px hit area), and on a phone the browser
scrolled a focused FAQ question flush to the bottom edge, where the 59 px sticky CTA bar
covered it completely (5 of 5 sample points landed on the bar). `scroll-padding-bottom:
calc(78px + env(safe-area-inset-bottom))` in the mobile media query reserves that room,
so the question now lands 19 px above the bar. Links inside a sentence keep the standard
inline exception; the anchor landings (`#how`, `#pricing`, …) are re-checked against the
63 px sticky header on top of the existing `scroll-padding-top: 84px`. Measured
failed-first: 31 of 43 checks failed before the fix, 0 after; each fix also has a static
marker in the sweep (the sweep is the running count — 1336 checks as of 21 Oct 2026).

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
screens), lazy-loaded official assets (all hotlinked from the platforms except the
Startup Fame one — see below), links open in a new tab with
`rel="noopener"`. Badge links point at the platform's product page where one exists
(Fazier: `fazier.com/launches/uchisambot-study-helper`; the hotlinked badge asset uses
the canonical single-slash path `fazier.com/api/v1/public/…`). `privacy.html` /
`terms.html` carry the required LiftOff + Startup Fame badges in the same style.

Badge strip shape (22.10.2026): eight badges on a 1440 screen used to wrap 6+2 — the
two-badge second row sat centered under the first and the strip read as unfinished. The
strip is capped at `max-width:780px` (the four widest badges total 714 px, the fifth no
longer fits), so it forms two even rows of four; on a 420 screen it stays two per row.

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

Startup Fame badge: served from our own domain (22.10.2026): the platform's
`https://startupfa.me/badge?t=classic&theme=default` answers `HTTP 200` with a valid,
self-contained SVG (10 KB, text converted to paths, logo inlined as `data:`) — and
Chromium still refuses it with `net::ERR_BLOCKED_BY_ORB` on every page, and in a bare
`<img>` test outside the site, so the `onerror` fallback below silently hid the link and
every language page showed **7 platforms instead of 8**. `curl` sees 200, the browser sees
nothing: only a browser check catches this class of failure, a status-code audit never
will. The exact bytes now live at `img/badges/startupfa.svg` (10 258 bytes, sha256
`ef22f5c2…`), the link still points at `startupfa.me/s/-51`, and `tools/build.py` fails
the build (`audit_local_assets`) when any `src|href|poster="img/…"` reference has no file
on disk — so a missing local badge breaks CI instead of vanishing from the page. The sweep
pins the local path on all nine pages plus the file itself, and the browser smoke treats
it as the one badge that must stay visible and loaded while every platform host is blocked.

Badge failure fallback (21.10.2026): every badge but Startup Fame is a hotlink to the platform's own
asset, and those edges do throttle. A fresh 9-language × 2-viewport capture found at
least one badge request with `naturalWidth=0` in 5 of 18 renders; an 18-page browser
smoke run saw `startupfa.me` fail on 10 pages while a single request to the same URL
returned 200. A visitor on such a render saw the browser's broken-image glyph plus alt
text. Each of the nine external badges (one in the hero, eight in the footer) now
carries `onerror="(this.closest('a')||this).style.display='none'"`: an asset that
cannot load removes its own link from the strip and the remaining badges reflow.
Nothing changes when the asset loads. The QA sweep asserts the fallback on all nine
language pages, and the browser smoke blocks every badge host at the network layer and
requires 9 of 9 links hidden, 0 visible broken images and no horizontal overflow.

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
logo replacement hits exactly one `<img>` per page.

Language switcher (21 Oct 2026): every entry now carries its own `lang`/`hreflang`, so
«Русский» is pronounced as Russian on an English page (WCAG 3.1.2 — the same rule the
404 chips got earlier that day). The summary `aria-label` ends with the current
language name (`lang.aria` + `": English"`), because `aria-label` overrides the
visible text and used to say only "Language". Three more fixes rode along: the flag
emoji are gone (Windows has no flag glyphs and draws bare `GB`/`RU` boxes, and a flag
is a country, not a language — 🇮🇳 for Hindi, 🇧🇷 for Portuguese, 🇬🇧 for English all
read wrong on a page sold worldwide); the summary shows an inline SVG globe instead,
and the nine entries use native names exactly like the 404 chips. The current language
is a `<span aria-current="page">`, not an `<a href="#">` that jumped to the top and
claimed to be a link. Nothing else moved: section offsets and page height are
unchanged at 1280, 768 and 420 px.

Legal pages exist in English and Russian only, so on the other seven languages every
link to them ends with "(EN/RU)" — one rule in `legal_label()` covering
`parents.link`, `foot.privacy`, `foot.terms` and `contact.privacy` — and the pages
themselves open with a two-line notice naming the sections that exist. Until 21 Oct
2026 `/hi/` promised «गोपनीयता नीति पढ़ें» ("read the privacy policy") and delivered
English text. The suffix is repeated in the `.md` twins. `privacy.html` / `terms.html`
keep the English wording, like their badges — bilingual EN-first pages.

Connections: the head warms up the third-party origins the pages actually use —
`preconnect` to `launchigniter.com` (the hero badge is the only eager external image)
and `dns-prefetch` to the seven footer badge hosts plus the form API
(`api.web3forms.com`). Footer badge assets are lazy, so a full preconnect there would
only burn sockets — DNS warm-up is the right level. `privacy.html` / `terms.html`
carry `dns-prefetch` for their two badge hosts.

The largest contentful paint on every page is the hero `<video>`'s poster, so the head
preloads that image (`<link rel="preload" href="img/demo-poster.webp" as="image"
type="image/webp">`; the build rewrites the href per language exactly like the `poster`
attribute, and the QA sweep fails if a page preloads another language's poster or a file
that does not exist). Measured on the Core Web Vitals battery (`landing-cwv.py`,
Lighthouse-mobile profile: 390×844, DPR 2, CPU ×4, Slow 4G) it is worth 40–70 ms of LCP
with no second download — the media element reuses the preloaded response, and the
battery asserts exactly one poster request per page. Current numbers, all nine
languages: LCP 912–1256 ms, CLS 0.000, `video` as the LCP element above the fold, first
FAQ tap → painted frame 7–18 ms. TBT is reported for information only: on a static page
without a JS runtime the single long task is the initial parse/style of the HTML, so the
Lighthouse TBT threshold does not describe this page.

Contact form: `#contact` posts straight to Web3Forms — no Telegram step. After a
successful submit Web3Forms returns the visitor to the **same language page**
(`?sent=1&t=<token>#contact-card`, rewritten per language by the build), where the
form is replaced by a localized confirmation message baked into the page (one
string per language, no JS dictionary).

The confirmation is tied to the submission, not to the URL: on `submit` the page
mints a random token, keeps it in `sessionStorage` and appends it to the redirect
field. A `?sent=1` URL with a foreign or missing token — a copied "thank you" link,
another tab, an old bookmark — gets the form back and **no** false "we received your
message". After a genuine return the address is stripped to the plain page, so the
address bar never keeps a shareable "thanks" link. The page also stays on the form
card: clearing the query and the anchor makes the browser jump to the top, so the
card is scrolled back into place before focus lands on the message.

The confirmation survives **without JavaScript** too: the redirect anchor points at
the form card, and `#contact-card:target:not(.stale)` CSS reveals the message
(`:target` + descendant selector, so it works in every browser — an earlier
`:has()` variant was rejected by the Nu validator's CSS parser). Two rules learned
the hard way: the form is **not** hidden in that state (a forwarded URL must not
lock a visitor out of the only support channel), and the message sits **above** the
form, so it is read before the fields, not after the button.
This form is the site's single support channel: the FAQ answer about failed
breakdowns, privacy and terms all point visitors here — no page promises an in-bot
message-to-team path (the bot's Help button only shows payment guidance), and the
sweep fails any page that references one.

The path is verified end to end, not just in markup: `landing-contact-e2e.py`
(default: 468 offline checks across nine languages — fields, labels, autocomplete,
honeypot out of the tab order, native validation, the token minted on submit, the
own/foreign `?sent=1` states, the bare `#contact-card` link, landing position and
reveal, and the no-JS state) and `--live`, which submits one real message through a
**real Chrome over CDP** and asserts a 3xx from Web3Forms, that the redirect kept
the token, the return to the same language page, the localized confirmation, a
cleaned address and focus on the message. Do not try this with headless browsers or
a server-side POST: `api.web3forms.com` sits behind Cloudflare and answers 403 "Just
a moment", so an automated probe proves nothing about real visitors.

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

The bot link in the AI layer carries its own source tag. `llms.txt` (the
`Open the bot` line) and the `Open in Telegram` line of every markdown twin point
to `https://t.me/UchiSamBot?start=src_llms` — the constant `BOT_LLMS` in
`tools/build.py`. The page keeps its three landing tags (`src_landing`,
`src_landing_band`, `src_landing_sticky`); the AI layer is a separate channel, and
without its own tag a reader who arrives from an AI answer lands in the bot's
statistics as "(no tag)" and cannot be told apart from any other untagged source.
The QA sweep checks the tag in all nine twins and in `llms.txt` and fails if the
bare link comes back.

Privacy policy vs the site's real data flows (21.10.2026): the policy named
GitHub Pages and Web3Forms only, while every page loads nine hotlinked badge
images from eight launch platforms — the visitor's browser asks each platform for
the picture, so that platform sees the visitor's IP address and the site it came
from — and the contact form keeps a token in `sessionStorage`, which the policy
never mentioned. Section 7 of `privacy.html` (EN and RU) now lists the eight
platforms with their domains, says what the platform sees and that the rest is
covered by its own policy, states that the site itself sets no cookies and runs
no analytics, advertising or third-party scripts, and explains the session token;
"Last updated" moved to 21 October 2026 in both language parts. The sweep now ties
the policy to the fact instead of to a wish: a `BADGE_PLATFORMS` registry, every
external image host on the nine language pages plus the two legal pages and
`404.html` must be registered *and* named in the policy, the registry may not list
a platform that has left the pages (a stale promise), no remote `<script src>` or
stylesheet, no `document.cookie` / `localStorage`, the only `sessionStorage` key is
`ucs_sent`, and both new paragraphs must survive into `privacy.html.md` — 18
checks, 1309 → 1327. Seven mutations (a platform label without its domain, an
injected third-party script, a cookie write, a renamed session key, a removed
token sentence, "may set cookies", an unmapped badge host) each fail the sweep and
leave the file restored afterwards. Screenshots at 420 and 1440 px in EN and RU
(`evidence/privacy-disclosure-20261021/`) and the measured layout show no
horizontal overflow, 16 px text and a document exactly as wide as the viewport.

## One copy of the texts, and no refund promises (22.10.2026)

**A second copy of the texts is gone.** The template carried a client-side dictionary
(`var I18N`, 99 English and 104 Russian strings) for the old two-language switcher —
dead code, which the build stripped from every page. Dead did not mean harmless: the
copy had drifted. Its Russian `cta.sub` still promised **five** free breakdowns while
the pages, the dictionaries and the bot said **two**, and its `shots.cap` still said
"screenshots in Russian and English" long after every language got its own shots. A
price promise was sitting in code nobody looked at, one revert away from the live page.
The block is deleted (template −13.7 KB; the build output is byte-identical, which is
the proof it was dead), `tools/build.py` refuses a template that carries `var I18N`
again, and the sweep fails if the dictionary returns to the template or appears on any
page. Texts now live in exactly one place: `src/locales/*.json`.

**The "no refunds" rule has a guard.** Since 16 Oct (owner) no surface promises money
back — the bot's own texts were cleaned that day. On the site the rule was kept by
memory only: nothing in the sweep looked for the word. The sweep now fails on any
refund phrase in nine languages across every surface — the eleven pages, their markdown
twins, `privacy.html` / `terms.html` (both twins), `404.html`, `llms.txt`, the template
and the nine dictionaries. Current state: zero mentions. Strict by design: if the legal
texts ever need an explicit "no refunds are provided", that file:phrase pair goes into
`REFUND_ALLOW` in the sweep consciously — the guard must not be weakened silently.

Both guards were proven by mutation, not by a green run alone: injecting «Возврат средств
по запросу» into the Russian `q9a` fails with `ru/index.html:возврат`,
`ru/index.html.md:возврат`, `src/locales/ru.json:возврат`; putting `var I18N` back into
the template fails the sweep and the build. Sweep 1394 → **1397 checks**.

**Copy fixes in two languages.** Turkish `cta.sub` said "Bot'a gönder" — an apostrophe
before a case suffix belongs to proper nouns only, so it is now "Bota gönder" (the
product name keeps its apostrophe: `UchiSamBot'a`). Ukrainian used the ASCII apostrophe
in two strings (`Дев'ять`, `розв'язаннях`) while the rest of the file uses `’` — the
same word root appeared with two different marks on one page; both now use `’`.

**The dead switcher's markup followed the dictionary.** The same template still carried
the old two-language switcher — two buttons (`lang-en`, `lang-ru`) and five CSS rules
(`.lang`, `.lang button`, `.lang button.on`, plus `.lang button` in the 44 px touch-target
rule and its padding rule inside `@media(pointer:coarse)`). The build replaces that block
with the nine-language `<details class="lang-dd">` dropdown, so no visitor ever saw them;
their only handler was the dictionary that is now gone. Buttons and rules removed (pages
365 bytes lighter each, nine pages); the empty `div` stays as the build's replacement
anchor with the reason written inside it, so the note ships nowhere. A template that still
shows a working switcher invites someone to wire it up again — now it shows none. The two
media-query rules surfaced only after a second look at the built page (`grep -F "lang
button"` on the output, not on the source): a first pass that trusts its own grep on the
template will miss rules that hide inside shared selector lists.

## Claims against the product (22.10.2026)

Every earlier gate compared the shop window with itself: dictionaries against
dictionaries, prices against `prices.json`, prices against `bot/payments.py`. The
promises themselves — nine languages, five abilities — were never compared with
what the bot actually does. This pass did that, and it found the window ahead of
the product.

**Status: both issues below are FIXED (22 Oct, 03:13, main session).** The answer
language was rewritten to a per-locale map (`ANSWER_LANG`: English + native name,
directive as the last prompt line) and `study-bot.service` was restarted with it;
measured through the same `:8080` queue afterwards — hi/es/uk/tr/vi answer in their
own language. The "endpoint answered nothing" case was not a wedged proxy: the TTS
server was pinned to GPU 0 and held 2.2 GB, leaving ~2.4 GB free against the queue's
3 GB reserve, so `wait_vram()` stalled every request. The TTS unit now runs on GPU 1
(`CUDA_VISIBLE_DEVICES=1`), the queue answers in ~0.9 s, and both bot fixes are
committed (`7a98389`, `e3d67ff`). The paragraphs below are the original findings,
kept as history.

> УСТАРЕВШЕЕ (на момент блока 22.10, до фикса): «Answer language» и «Product
> reachability» ниже описывают СОСТОЯНИЕ ДО исправления.

**Answer language.** `bot/handlers.py` (`build_prompt`) writes the response
language as `'русский' if lang == LANG_RU else 'english'`, so seven of the nine
languages get English answers even though the visitor picked their language and
the system prompt asks for the language of the request. Measured on the live
model with the bot's exact prompt (thinking off, temperature 0.2): a Spanish,
Hindi and Vietnamese task each came back in English under the current line, and
in Spanish, Hindi and Vietnamese once the language was named. The model can do
it; the prompt forbids it. Five lines in the bot fix it — recorded with the
measurement in `evidence/block-20261022-claims-vs-product.txt`. It is not done
here: this block's working folder is the landing alone, and the bot fix needs
`study-bot.service` restarted, which cron is not allowed to do.

**Product reachability.** At the same hour the bot's endpoint
(`http://[адрес]:8080/v1`, the `gpu-queue-[GPU]` proxy in front of
llama-server) answered nothing at all: five requests between 02:41 and 02:57,
waits of 15 to 130 seconds, not one byte back, while the model behind it on
`[локальный порт]` answered the same request in 1.2 s. The bot has no second provider, so a
visitor waits out `LLM_TIMEOUT=120` and gets an error. One command restores it
(`systemctl restart gpu-queue-[GPU].service`, `Restart=always`); cron is barred
from touching services.

**Two gates added** so neither class slips again, 1392 → 1394 checks:

- *Numbers in translations.* Prices, "first 2 breakdowns", "9 languages" and pack
  sizes live in the nine dictionaries as text, so a translator writing "3" made
  one page promise what the other eight deny. Every key's set of numbers must now
  match English (Devanagari and Arabic-Indic digits are normalized — `२` is not a
  defect). 0 mismatches across 113 keys × 8 languages.
- *Site languages = bot languages.* The council's rule was checked by hand once;
  the sweep now reads `SUPPORTED` from `bot/i18n.py` (expanding the `LANG_*`
  constants) and fails if the two sets differ.

Both were proven by mutation: `hero.chip1` 2 → 3 in Spanish fails with
`es:hero.chip1`; dropping `uk` from the bot's tuple fails with `bot 8 vs site 9`;
restored, the sweep is 1394 checks, 0 failed. This is a documentation-and-gates
pass — the site's own markup did not change, so the build output is byte-identical.

## The badge strip is gated, not just printed (22.10.2026)

The three fixes of that morning (the Startup Fame badge moved to our domain, the footer
strip laid out 4+4, the privacy text about it) landed at 07:02–07:18 — **after** the last
full battery, which ran at 05:59. Nothing had re-checked accessibility, cross-engine or
timing against the pages that actually ship, so this pass ran the whole battery on that
commit: sweep 1408 → **1426 checks, 0 failed**; render-check ALL OK (9 languages, 4 render
probes, no console errors); browser smoke 18/18; axe-core 0 violations on all 12 pages;
a11y-extra 68/0; WCAG 2.2 target size and focus 43/0; environment preferences 45/0 (dark,
forced colors, reduced motion, WebKit); throttled viewports 85/0; contact end-to-end
468/0; cross-engine 36 runs in 308 s with 0 problems; Core Web Vitals 69/0 (LCP 204–332 ms,
CLS 0–0.006); Nu validator 0 real findings; links and external hosts 0 broken; price
parity and the English-leftover scan clean. `tools/build.py` re-run leaves `git status`
empty, so the build is still byte-reproducible.

Then the visual pass was re-shot after those fixes (`evidence/visual-20261022b`): 9
languages × 420/1440 px, eight sections each, 8/8 badges on every page, rows `[4,4]` on the
desktop and `[2,2,2,2]` on the phone, heights 46/40 px, no overflow, no clipped text, no
JS errors. The band and the footer were also looked at directly — English desktop and Hindi
mobile (the smallest type and the longest strings): even rows, nothing cropped, Devanagari
renders, contrast holds.

**The tool was blind to the defect the owner named.** `landing-visual-pass.py` printed
`rows=` and never asserted it, so a 6+2 strip — the exact thing the owner called unfinished
— passed with `PROBLEMS 0`. It now derives the expected rows from the design (`ceil(n / 4)`
desktop, `ceil(n / 2)` mobile), requires rows to be even, no row wider than the design, and
equal badge heights, and it exits non-zero on any problem (a verdict that only exists in a
log stops nothing). Proven by mutation: with the strip narrowed to 620 px it fails with
`badge rows 3 != 2 ([3,3,2], 4/row)` and exit 1; restored, 0 problems and exit 0.

A second defect surfaced in the same pass: three pages reported **7/8 badges** while the
rest reported 8/8 at the same minute. A fixed 1800 ms wait after scrolling was racing the
platforms' CDNs — the probe read `naturalWidth` before the image had answered, and on a
retry the same pages loaded 8/8 within 1.8 s. The pass now waits for `img.complete` on
every badge, reloads once to tell a transient miss from a broken asset, and names the
missing file instead of just a count. Those seven assets are hotlinked by the platforms'
terms, so a single CDN miss hides that link (`onerror`) rather than breaking the page —
distinguishing "not yet" from "broken" is the whole point of the wait.

Static markers went into the sweep as well (2 × 9 languages), because a CSS regression
must fail without a browser: `.foot-badges{… max-width:780px … flex-wrap:wrap}` and the
mobile `.foot-badges{gap:10px 14px}`. Narrowing the style to 620 px in the built page makes
the sweep report exactly two failures — the new marker and the existing "page edited without
a rebuild" guard — and restoring it returns 1426/0.

The site's markup is unchanged by this pass: it is verification and gates only.

## The AI-facing layer is the same page, so it is gated too (22.10.2026)

The site has a second copy of itself: `llms.txt` and one `index.html.md` per language,
served as `text/markdown` — the layer an AI assistant reads when someone asks it about
the bot. Everything else on the page was gated to death; this layer had three checks
(the file exists, it starts with the H1, it carries the `src_llms` bot tag) and had
quietly fallen behind the page:

- the final band — "Stuck on a problem right now? … the first 2 breakdowns are free" —
  was missing from all nine twins, so an agent quoting the page ended on a list of legal
  documents instead of the offer;
- none of the nine twins linked the language's own demo video, and `llms.txt` named only
  the two full 35 s videos, although the site has a 13 s loop in each of the nine
  languages. Asked "show me how it works" in Hindi, an agent had nothing to point at;
- nothing looked inside the twins at all: HTML leftovers, the price lines and the demo
  link were unverified.

Fixed in the generator, not in the output (the output is rebuilt every time): `page_md()`
now writes the demo link under the first bot link and the final CTA after the contact
links, and `llms()` lists the nine loops. One new dictionary key, `md.demo` — the link
text in that language ("Демо-видео (13 с, по-русски)", "डेमो वीडियो (13 सेकंड, हिन्दी में)" …).

Five gates, 1426 → 1473 checks. Per language: no HTML tags or entities in the twin; the
final CTA heading, its sub-line and the bot tag; the three price lines exactly as
generated; the twin's **own** loop (the English loop must not appear on the other eight);
the localised link text. Globally: `llms.txt` names all nine loops and every `demo/*.mp4`
it links exists on disk — a link to a missing file is worse than no link.

Proven by five mutations, each caught by exactly its gate: deleting the Hindi demo link,
renaming the Russian CTA heading, stripping `300 Stars` from the Spanish price line,
deleting the Hindi loop from `llms.txt`, pointing a loop at a missing file
(`evidence/block-20261022-ai-layer-mutations.txt`). The first version of the price gate
compared the *title* ("Paquete de 15 desgloses") and stayed green when the number was
removed — the same "it is printed, therefore it is checked" mistake as the badge rows; it
now compares the full generated lines.

The HTML did not change — the commit touches only the nine twins, `llms.txt`, the nine
dictionaries and `build.py` — so the accessibility, cross-engine and timing batteries of
the previous pass stay valid for this commit; the sweep, link audit, price parity and the
English-leftover scan were re-run (1473/0, 0, 0, 0).


## The language switcher had no font plan (22.10.2026)

**What was measured.** Nine language names, three scripts beyond Latin — Cyrillic,
Vietnamese, Devanagari. The stylesheet declared every full subset on every page and let
`unicode-range` keep downloads down. That works while the names are hidden, and stops
working the moment the `<details>` switcher opens: the browser then needs all nine names
and fetches every full subset it does not already have. Summed font bytes in real Chrome,
menu closed then opened (`landing-fonts.py`):

| page | opening the menu, before | after |
|---|---|---|
| en, es, pt, id, tr | +140.8 KB (cyrillic 14.2 + vietnamese 8.3 + devanagari 118.4) | +9.0 KB |
| ru, uk | +126.7 KB | +6.1 KB |
| vi | +132.5 KB | +7.8 KB |
| hi | +22.5 KB | +4.1 KB |

**The 404 was not just expensive — it was broken.** `page_404()` declared the five Manrope
subsets and no Devanagari at all, so the «हिन्दी» chip — the one link a Hindi visitor needs
on a dead end — was drawn by whatever Indic font the device happened to have, and by
nothing at all on a device without one. The page also downloaded 22.5 KB of Cyrillic and
Vietnamese subsets for the other two names.

**The fix: three mini subsets, and full subsets only where the text needs them.**
`tools/make-lang-fonts.py` (fontTools, run once, assets committed) cuts
`langs-cyrillic.woff2` (2.9 KB), `langs-vietnamese.woff2` (1.2 KB) and
`langs-devanagari.woff2` (4.9 KB) — exactly the glyphs of «Русский», «Українська»,
«Tiếng Việt», «हिन्दी» — declares them as the family `UchiSam Langs` with a `unicode-range`
equal to the glyphs the file really contains, and puts that family first in the body stack.
`tools/build.py` emits the full subsets per language: `cyrillic` + `cyrillic-ext` on /ru/
and /uk/ only, `vietnamese` on /vi/ only, `Noto Sans Devanagari` (118 KB) on /hi/ only,
latin and latin-ext everywhere. The mini subset for the page's **own** script is
deliberately not declared — the full subset is already there for the body text and serves
the name in the header too. The 404 declares the three minis plus the latin full subset:
33.2 KB of fonts instead of 46.7, and the Hindi chip finally has a face of its own.

**A Chrome detail worth writing down.** Declaring the three mini faces with different
`font-weight` descriptors (`400 800` on the Devanagari one, `200 800` on the others)
silently disables range-based selection: Chrome picks one face per family by style
descriptors first and only then looks at `unicode-range`. The Devanagari subset was never
requested and the word kept falling back. Equal descriptors on every face of the family
fixed it — found by network capture and `document.fonts`, then pinned by a gate that fails
when the descriptors inside `UchiSam Langs` diverge.

**Gates: 1474 → 1544 checks**, plus a new browser battery `landing-fonts.py` (39 checks:
closed page ≤160 KB of fonts, opening the menu ≤12 KB, no foreign full subset on open,
404 ≤40 KB with the Devanagari mini and without the 118 KB Noto, no console errors).
Per page the sweep now checks: the mini family is declared with the right face count and
one weight descriptor, it sits first in the stack, the Manrope full subsets equal the
page's script, Noto appears only on /hi/, the registry bytes and sha256 match — and the
gate that would have caught the 404: **every non-emoji character of the visible text must
fall inside a declared `unicode-range`**, otherwise the system font draws it.

Six mutations, each caught by its own gate (`evidence/block-20261022-switcher-fonts-mutations.txt`):
the 404 without the Devanagari mini (two gates fire), a divergent weight descriptor, the
full Cyrillic subset back on /en/, a Devanagari range without `U+0939`, one byte appended to
a mini file, and Noto declared on the 404. Control run afterwards: 1544/0.

**The change is invisible where it should be.** Full-page screenshots of all nine languages
at 420 px, old build against new, differ by **0 pixels**; on the 404 the difference is
confined to the chip row (`evidence/fontdiff/`). The mini renders «हिन्दी» within a pixel
of the full Noto at 40 px — same outlines, the shaping features `half`/`pres`/`cjct` survive
subsetting. Timing did not move (mobile LCP 0.9–1.3 s, CLS ≤0.002 — 69/0), the W3C validator
reports no real findings, and the link audit stays at 0 problems.

## The AI copy was missing a whole section, not just a line (22.10.2026)

**What was found.** The page has ten sections; each of the nine markdown twins had eight.
The missing one was "Real chats with the bot" — the page's only proof that the product is
real: three screenshots in the reader's own language, each with a localised alt and a
caption. None of it reached the AI layer: no heading, no caption, no frames. The principle
band ("Not just answers…") was present as a bold paragraph although the page marks it as
an `H2`, so the twin's structure did not match the page either.

**Why no gate saw it.** Every AI-layer gate named a block it already knew — the final CTA,
the three price lines, the language's own demo loop. A section that was never written is
not a wrong value, so no value check could fail: nothing looked at the *set* of sections.
The same lesson as the badge rows and the price title — a gate that only verifies what the
author remembered cannot see what the author forgot.

**Fixed in the generator.** `page_md()` writes the principle band as a heading (matching the
page) and the shots section after the subjects: the caption plus
`![alt](BASE img/shotN-<lang>.webp)` for the three frames, picked by `shot_src()` exactly
like the page — so the Hindi twin points at the Hindi screenshots, not the English ones.

**Gates: 1544 → 1571, three per language.** All ten section headings are present in the
twin (one list, used for both copies — a new section on the page now has to be answered for
in the twin); the caption is the dictionary line exactly and each alt opens its image; the
three image files are the language's own (the English `shotN.webp` may not appear on the
other eight). A missing image is still caught by the existing global "every BASE link in
the AI layer resolves" check, so no duplicate gate was added for it.

**Proven by five mutations**, each caught by exactly its gate
(`evidence/block-20261022-ai-sections-mutations.txt`): deleting the heading from the
English twin; pointing a Russian image at the English file; putting the English caption on
the Spanish twin; dropping one Hindi alt; pointing the Ukrainian twin at a missing image.
The first version of the caption gate used a substring test and stayed green when the
caption was merely appended to — it now compares the whole line. Control run afterwards:
1571/0, link audit 11 pages / 0 problems.

The HTML did not change: the commit touches the nine twins and `build.py`, so the browser
batteries of the previous pass remain valid for it.

## The font change was never re-checked by the batteries — so they ran (22.10.2026)

The switcher-font commit (10:47) is the one commit of the day that changed CSS and
`@font-face` on all ten pages and on the 404. The full browser battery — axe, the
accessibility extras, WCAG 2.2 targets, reduced-motion/contrast preferences, viewports,
cross-engine, timing — last ran at 05:59–08:29, **before** it. The two AI-layer commits
that followed touched no markup, so nothing asked for a re-run and none happened: the one
change that could move the rendering was the one nobody measured after.

So the whole battery was re-run on HEAD `3870b5e`. Every suite passed except one, and the
failure was in the test, not the page:

| suite | result |
|---|---|
| QA sweep / links / price parity / English leftovers | 1571-0 / 11 pages 0 / 9-0 / 0 |
| W3C validator, live bytes, 404 probe | 0 real findings, 26/26 identical, own 404 |
| render-check, browser smoke | ALL OK, 18 runs / 0 |
| axe, a11y extras, WCAG 2.2, system preferences | 12 pages / 0, 68/0, 43/0, 45/0 |
| viewports, Core Web Vitals, font budgets, cross-engine | 91/0, 69/0, 39/0, 36/0 |

**The stale gate.** `landing-viewports-extra.py` asserted that the first family of the body
stack is Manrope. The font pass put the switcher mini family first — which is the whole
point of that pass — so the 404 check failed three times while the page rendered exactly
right (the Latin text measures 281 px in Manrope against 284.59 px in the system fallback,
and the mini subsets are loaded). The gate was a copy of the CSS, not of the behaviour: a
font *name* read out of the stylesheet also stays "right" when the woff2 file 404s.

It now checks what the page must do, in three steps — the stack starts with
`UchiSam Langs` and then Manrope; both families are actually loaded
(`document.fonts.check`); and the text is *drawn* in Manrope, by comparing the rendered
width of a probe string in the body with its width set in Manrope (≤0.05 px apart) and
with the system fallback. 85 → 91 checks. The width probe is what makes it real: with
`manrope-latin.woff2` pointing at a missing file the body measures 284.59 px, and with the
family not declared at all Chromium reports a synthesised 263.06 px.

Three mutations, each caught by its own gate and only by it
(`evidence/regress4-20261022/404-font-mutations.txt`): dropping the mini family from the
stack (3 × *own font stack*); `system-ui` first (9 × stack + loaded + drawn); a missing
Manrope file (6 × loaded + drawn). The page was restored byte-exact after each, control run
91/0.

**No site file changed in this pass** — the commit touches the skill's battery script,
this README and the evidence. The reproducible build was re-run anyway: `tools/build.py`
followed by an empty `git status`.

The lesson is narrower than "re-run the tests": a gate that names a value from the
stylesheet fails for the right reason at the wrong moment, and the fix is to name the
property the value was standing for — here *which font the pixels come from* — not to
update the literal.

## The promises were translated, but nothing checked the meaning (22.10.2026)

The meaning pass had gates for the things that can be counted — the number of free
breakdowns and the prices against `tools/prices.json`, the FAQ count, a single H1, the
refund wording on every surface — and no gate at all for the three sentences that carry
legal weight. A translator could delete "tasks are not sent to third-party AI services"
in one language and the page would keep promising what the privacy policy no longer
guarantees: the text still had the right structure, the right keys and the right numbers.

**What the read found.** The copy of the nine dictionaries is in good shape: 114 keys in
each, no empty values, no English left behind except brand names (`Telegram Stars`, `FAQ`,
the placeholder `you@example.com`), number sets identical to English (already gated),
`हल` / `pembahasan` / `çözüm` / `phân tích` used for *breakdown* consistently. One real
defect, and it was in Vietnamese: the FAQ answer to "what if the breakdown fails" said
*chúng tôi* at the start of the sentence and *chúng mình* at the end — two different
first-person plurals for "we" in one line, the second one appearing nowhere else in the
114 strings. Now `chúng tôi` throughout; the page, its JSON-LD `FAQPage` twin and the
markdown twin were rebuilt together, so the three faces of the answer still match.

The localized media were checked as media, not as file names: the nine hero loops and the
three screenshots per language have distinct hashes (no English copy posing as a
translation), and a frame from the Hindi and Vietnamese loops shows the bot answering in
those languages with only the step number and `@UchiSamBot` in Latin.

**The gate.** Four anchors per language, 36 checks, in the QA sweep
(`landing-sweep.py`): the parents block must still say the service runs on *our own server
in the European Union (Finland)*, both the parents block and the FAQ must still say tasks
are *not sent to third-party AI services*, and the Stars answer must still say there is
*no subscription and no auto-renewal*. The anchors are substrings in the language of the
page, not translations of an English phrase: weakening one is a deliberate act that has to
travel with a change to the policy, which is exactly what the gate is for. The sweep went
1571 → 1607 checks.

Three mutations, each caught (`evidence/regress5-20261022/claim-mut-*.txt`): dropping
"сторонним ИИ-сервисам" from the Russian parents block (1 fail, the new gate), turning
"Sin suscripción" into "Con suscripción mensual" in Spanish (2 fails — the new gate and the
older premium-note gate), removing Finland from the Vietnamese server sentence (1 fail).
Every file was restored byte-exact and the control run is 1607/0.

**Battery after the rebuild:** sweep 1607/0, links 11 pages/0, English leftovers 0, price
parity 9/0, W3C validator 0 real findings, render-check ALL OK, viewports 94/0, axe 12
pages/0, accessibility extras 68/0, WCAG 2.2 targets 43/0, system preferences 45/0, fonts
39/0, build reproducible (`tools/build.py` then only the four expected files in
`git status`). The Vietnamese page was also photographed — the page sections at 420 px and
1440 px, and the changed FAQ answer with the accordion open at 420 px: no overflow, no
clipped text, and the changed sentence is the only difference.

The lesson: structure gates prove that a page has ten questions, not that the tenth answer
still tells the truth. Where a sentence is a promise, the promise itself is the assertion.

## The video promised five; the page promised two (22.10.2026)

Every text pass so far gated the *page*. The videos were left out of every gate because
their text is pixels, and pixels are not in the dictionary — so nobody compared the two.
Reading the nine hero loops and the two 35 s demos frame by frame found three real defects
and one structural hole:

- **The full demos' outro promised "5 free step-by-step solutions"** while the product
  gives two (`FREE_TRIALS = 2`), `tools/prices.json` says two and the page says two in five
  places. The video is linked from `llms.txt` and from every launch platform, so the most
  visible asset was the one making the wrong promise.
- **The Russian "demo-ru" was captioned in English**: Russian screenshots under English
  captions ("2 · Send any task — text or photo", "3 · Step-by-step explanations",
  "4 · Works in Russian and English") and an English intro/outro. The file name and the
  language of the page that links it disagreed with the language of the video.
- **The English hero loop had drifted from the page**: it said "Send any task" where the
  page's step is "Send a task", and "Step-by-step explanations" where the same screenshot's
  alt text and 17 other strings say "breakdown" — a second word for one thing, in the
  flagship language, in the first screen.
- **The Russian page's poster was an English frame.** `demo-poster-ru.webp` still showed
  "3 · Step-by-step explanations" (made on 15 Oct, before the RU loop was re-cut on 17 Oct):
  the poster is what a visitor sees before pressing play and what `save-data` users see
  instead of the video, so the Russian page opened with an English caption.

**The structural fix.** Captions are no longer written in the build scripts. `demo/captions.py`
derives every line from `src/locales/<lang>.json`: the loop's step-2 caption is `how.s2t`,
its step-3 caption is `shot3.alt` without the brand (`from`/`от`/`de`/`do`/`से`/`dari`/
`'tan`/`từ`/`від`, and the label is capitalised when the brand led the phrase, as in Hindi
and Turkish); the full demo's intro tagline is `foot.tag` and its outro promise is
`hero.chip1`. Only four phrases per language are video-only (the "text or photo" tail, the
two outro buttons, the intro/outro scene labels) and they live in one table in that file,
not scattered through shell scripts.

`demo/captions.json` is the ledger: the exact strings baked, plus sha256 and byte count of
each loop, its poster and each full demo. A rebuild always re-stamps it, so "the dictionary
changed but the video did not" and "the loop was re-cut but the poster was forgotten" are
both failures. The sweep went 1607 → 1660 checks: 36 for the nine loops (two captions, loop
bytes, poster bytes each), 14 for the two full demos (four captions, intro tagline, outro
promise, file bytes), 3 for the build scripts (they must call `captions.py` and must not
carry a literal `drawtext … text='…'`).

**A second pair of eyes for the posters.** The ledger proves the poster is the file that was
built with the loop, but not that it depicts the loop's last frame — a poster rendered from
the wrong loop by the same recipe would still be stamped. `landing-poster-frames.py`
(stars-bots-ops) extracts frame 389 of each loop, scales it to 540×1170 and compares it with
the poster by RMSE. Calibration on all nine: a fresh poster scores 0.0102–0.0110; the stale
Russian one scored 0.0431 and the English poster with the old wording 0.0324. The threshold
is 0.02, which separates the two classes with room on both sides.

**Rebuilt:** the EN loop (701 KB → 365 KB, captions now "Send a task" / "Step-by-step
breakdown"), its poster, the RU page poster (re-cut from the RU loop, 52 KB), and both full
demos — EN 991 KB → 916 KB (crf32), RU 1.34 MB → 1.30 MB (crf33), now in Russian throughout
with "Первые 2 разбора бесплатно". Quality was measured against the files they replace, not
assumed: zoomed crops of the chat text are indistinguishable at normal viewing distance.
The full-demo pipeline renders its zoompan at 1440×3120 instead of the kit's 2160×4680 —
the 3× variant segfaulted ffmpeg 6.1.1 on this box after two minutes of encoding, twice.

**Six mutations, each caught and each restored byte-exact** (`evidence/regress6-20261022/`):
a changed `how.s2t` in Spanish (loop caption gate), the old Russian poster put back (ledger
gate: 1 fail; poster tool: RMSE 0.04311), a literal caption slipped into the build script
(script gate), a changed free-tier promise in `hero.chip1` + `prices.json` (full-demo promise
gate, plus the four older free-count gates), a ledger that still described the old wording
(2 fails, loop and full demo), the old full demo put back under the same name (bytes gate).
Control after every restore: 1660/0, posters 9/0.

**Battery after the rebuild:** sweep 1660/0, poster frames 9/0 (worst 0.01097), links 11
pages/0, English leftovers 0, price parity 9/0, W3C validator 0 real findings, render-check
ALL OK, axe 12 pages/0, accessibility extras 68/0, WCAG 2.2 targets 43/0, fonts 39/0, build
reproducible. The English page was photographed at 420 and 1440 px after the swap: the new
poster renders, nothing is cut or overflowing.

The lesson: a promise that lives in pixels has to be asserted from the pixels' own source.
Deriving the strings from the dictionary closes the gap at the only place where it opens — the
moment of encoding — and the ledger makes the next rebuild prove it.

## The privacy promise was checked against the dictionaries, not the wiring (22.10.2026)

Every language says it twice — in the parents block and in the FAQ: "Your tasks also stay on our
own server — they are not sent to third-party AI services." The privacy policy says it a third
time and adds "not used to train third-party models". Three surfaces, nine languages — and until
this pass every one of those checks compared the shop window with itself: dictionary against
dictionary, policy against the policy file. Not one of them looked at where the bot actually sends
a task. That promise lives in `study-bot/.env`, not in `src/locales/`: point `LLM_BASE_URL` at a
cloud address and the page lies while the sweep stays green.

**Six checks on the wiring and eight on the legal text; 1660 → 1674.**

Read from `.env`, and only these four keys: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`,
`LLM_TIMEOUT`. `BOT_TOKEN` and `LLM_API_KEY` are never read and never printed — a failing check
prints the scheme and the host, never the URL, so a key in a query string cannot reach a log. The
endpoint must be loopback or private (`[адрес]`, `::1`, `localhost`, `10/8`, `172.16/12`,
`192.168/16`); a DNS name the gate cannot resolve offline fails closed, and adding one's own name
is a single line in `_OWN_HOSTS`. The systemd unit is read too, because it can override the file:
`EnvironmentFile=` must point at the same `.env`, `Environment=` is merged with the precedence
systemd uses (the later one wins), and an override that disagrees with the file is a failure in its
own right — two sources of truth is exactly what bit the site address that same morning. A scan of
`bot/*.py` for eleven known inference hosts (OpenAI, Anthropic, Gemini, Groq, Mistral, DeepSeek,
OpenRouter, Together, Fireworks, Perplexity, HF inference) closes the other door: a provider baked
into code instead of configured.

The legal text: three statements × two languages in `privacy.html`, plus the same three in
`privacy.html.md` (the twin is what AI clients read). Until now the sweep looked at the policy for
canonical, `og:`, one H1 and the badge strip — an edit that softened the AI paragraph, or a
rebuild that dropped it, would have passed.

**Proven by mutation, each restored byte-exact** (`evidence/block-20261022-claim-infra.txt`):
`LLM_BASE_URL` → `api.openai.com` (1 fail: "endpoint is ours, not a third party"); an
`Environment=LLM_BASE_URL=https://api.anthropic.com/v1` line appended to the unit (2 fails: the
endpoint and the override); a file in `bot/` naming `api.groq.com` (1 fail: the code scan);
`LLM_BASE_URL` → `192.168.1.50` (0 fails — a private LAN box is still "our infrastructure", and a
gate that cries wolf gets switched off); "not sent to third-party AI services" → "handled with
care" in `privacy.html` (1 fail, plus the `lastmod` sha check, which watches every page edit); the
Russian training sentence softened in `privacy.html.md` (1 fail). After every restore: sha256
equal, `git status` clean, sweep 1674/0.

**Where the promise stands today**, measured rather than assumed: `LLM_PROVIDER=local`,
`LLM_BASE_URL=http://[адрес]:8080/v1`, the queue in front of it routes `8080 → 9080` on this box,
no third-party host in the bot code, and a chat probe through that same queue answered
("работает") — the endpoint the page promises is the endpoint that answers.

**What the gate cannot prove**, and why the wording does not need it to: "our own infrastructure"
is a statement about ownership, not geography — a private IP on a rented cloud VM would pass. The
gate catches the realistic failure (someone switches the provider to a cloud API and forgets the
page), not every possible lie.

