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
  tracking. `python3 tools/build.py --check` renders the same 24 files into memory and
  compares them with the disk without writing a byte (23.10.2026); the sweep runs it, so
  a source edited without a rebuild is red instead of silently leaving the old page.
- `tools/page-text.py` — flattens a built page into its visible text, one block per line, so it
  can be read as an article rather than as markup (added 23.10.2026 for the meaning pass);
  read-only, not part of the build: `python3 tools/page-text.py ru/index.html`.
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
- `tools/subjects.json` — single source of the subject list (9 languages × 5 subjects:
  mathematics, **English**, physics, chemistry, history): `tools/build.py` refuses to
  build when a dictionary's `subj.c1`…`subj.c5` differ from it, and the sweep compares
  the chips, the FAQ sentence and both halves of `terms.html` with the same file. Added
  22 Oct 2026 after the list had been translated as «the language of this page» on eight
  pages (see "The subject list was translated into the wrong thing" below).
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
node types and every FAQ answer of the language dictionary, each with non-empty text): a broken graph does not break the
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
it stays hidden) — and also while the screenshot section's own button (`.shots-cta`)
is on screen, so two identical buttons never stand together. Safe-area aware via the
two-declaration pattern (`padding:6px 14px;`
fallback, then `calc(6px + env(safe-area-inset-bottom))`) — browsers without `env()`
support still get sane padding; modern browsers are unaffected (second declaration wins).
Markup + inline script live in `index-src.html`.

CTA tags: the hero button keeps `?start=src_landing`, the closing band button uses
`?start=src_landing_band`, the sticky bar `?start=src_landing_sticky`, the button after
the screenshots `?start=src_landing_shots` (the bot records the first touch per user and
accepts any `src_*` payload). The sweep pins all four — exactly one plain `src_landing`
link must remain (the hero).

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

## The privacy promise is now checked against the wiring, not just the dictionaries (22.10.2026)

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

## The screenshots ended and there was nothing to press (22.10.2026)

Round 2 of the landing board (15 Oct, `~/.hermes/rooms/landing-modern-20261015`) agreed on six
P0 items; five shipped. The sixth — *CTA after the screenshots* — did not, and nothing noticed,
because no gate had been written for a decision: every check named a block that already existed.
Measured before the fix at 1440 px: the shots section ended at y=3430 and the nearest button sat
at y=5259 — **1829 px with nothing to press**; on a phone the sticky bar covered that stretch, on
a desktop nothing did.

The button itself is one paragraph of markup and one line of CSS: `.shots-cta` under the rail,
centred, the dictionary's own `cta.btn` label (no new translations), its own tag
`?start=src_landing_shots` so the bot's stats can tell this point from hero/band/sticky. Height
55 px, width 199–244 px across the nine languages, 26 px below the captions on desktop and 6 px on
a phone — measured in all nine, not assumed.

**The second button created a third problem.** On a phone the sticky bar sits at the bottom, so
when the section's own button entered the viewport the reader saw two identical blue buttons
~100 px apart. The bar already hid itself at `#contact` and the footer; it now hides at
`.shots-cta` too — via its own IntersectionObserver with no bottom margin (threshold 0), because
the existing observer shrinks the viewport by 20 % and would have left the pair visible until the
button was already halfway up the screen. Behaviour, measured in en/ru/hi at 420×900: shown at
y=1400, hidden at the shots button, hidden at `#contact`, hidden at the footer.

**Three checks per language, 1674 → 1701**: the tag appears exactly once inside an anchor with
`rel="noopener"`; `.shots-cta` sits *after* the rail in the markup (so the button cannot drift
back down the page); its label is the dictionary's `cta.btn`. **Proven by mutation**
(`evidence/block-20261022-shots-cta.txt`): deleting the paragraph from `ru/index.html` failed
three checks — the two new ones plus the `lastmod` sha guard — and the file was restored
byte-exact. The full browser batteries after the change: a11y 68/0, viewports 94/0, sweep 1701/0.

**What the static gate cannot prove** is that the bar disappears at the right moment — that is
JavaScript and layout, so it stays in the browser batteries (`landing-a11y-extra.py`,
`landing-viewports-extra.py`). The sweep guarantees the button exists, is reachable and keeps its
tag; the browser runs guarantee the reader never sees two of them at once.

## The stylesheet said Manrope; the browser said Liberation Sans (22.10.2026)

Every font gate until today read *declarations*: the `@font-face` block exists, the file exists, the
sha matches, and every character of the page's text falls inside some declared `unicode-range`. All
true — and all silent when the file itself lacks a glyph. Then the browser quietly takes a system
font for that character: the sentence stays complete, the typeface under it changes. That is exactly
what had happened to the 404, where «हिन्दी» was painted by the system font because no Devanagari
face was declared at all; the sweep was green through it.

The new battery asks the browser what it actually used: CDP
`CSS.getPlatformFontsForNode` on every element that owns text, aggregated per family. Twelve
pages — nine languages, privacy, terms, 404 — **44,216 glyphs, zero painted by a system font**.
Per page: en 2934, ru 2942, es 3338, pt 3317, hi 2790, id 3204, tr 3050, vi 3209, uk 3080,
privacy 9624, terms 6381, 404 347.

**Proven by mutation, each restored byte-exact**: pointing the 404's Devanagari mini at a missing
file left 5 fallback glyphs (`Noto Sans Devanagari:'हिन्दी'`); pointing the RU page's Cyrillic face
at a missing file left 2288 (`Liberation Sans`, starting with «Перейти к содержимому» and
«Русский»); restored, the same run reported 2942/2942 and exit 0.

It is a battery, not a sweep check: ~4–6 s per page, because each text node costs a CDP call.
`stars-bots-ops/scripts/landing-glyph-fallback.py`, run in control passes.

**What it cannot prove**: that the files contain glyphs for text that does not exist yet. A new
language or a new sentence still needs the rebuild and the run; the check is a photograph, not a
promise. It also reports what this machine's Chromium chose — a different fallback font on another
OS would still be a fallback, which is the failure it is looking for.

## The form said "sent"; the mailbox was never asked (22.10.2026)

The live end-to-end test of the contact form ended with a 3xx from `api.web3forms.com` and the
line "the letter has been sent". A 3xx means *the service accepted the request* — it says nothing
about the letter. Between those two facts sits the delivery itself (free-plan quota, a spam
filter, a revoked access key, a changed recipient), and all of it breaks silently: the visitor
sees the confirmation, the site stays green, nobody ever gets the message.

**The loop was closed by hand first**: a real submit from the live site (ru), and two seconds
later the letter in the kerio inbox, both fields intact (`email`, `message` with the run's own
timestamp). Then a second run (uk) after the script change — same result.

**A second defect was hiding in the test itself.** The POST body is form-urlencoded, so the
`redirect` value travels with `%23contact-card` instead of `#contact-card`; the printout said
`redirect: False` on a form that worked. It is now a decoded check, `post carries redirect`
(10 → 11 live checks), so a real break cannot hide behind a false alarm.

**New tool — `landing-contact-delivery.py`**: searches the mailbox for the subject, keeps only
letters inside `--since-minutes`, and requires the run's own timestamp in the body *and* the test
address in the email field. Proven with a negative control: a fresh letter from an earlier run is
rejected (exit 1), so "a letter exists" cannot pass for "this letter arrived". Exit 2 means the
mailbox could not be checked at all — the run is then not a pass.

Numbers for the day: offline 468 checks / 0 failed across nine languages; live 10 / 0 in ru (before
the fix) and 11 / 0 in uk (after it); delivery confirmed twice. Evidence:
`evidence/block-20261022-contact-delivery.txt`.

**What it still cannot prove**: that a human reads the inbox and answers. Delivery is measured
now; answering is a process, not code.

## The bell rang in an empty room (22.10.2026)

Delivery was proven this evening; the *notification* that says «someone wrote» had been run once,
against an empty mailbox — and an empty mailbox is exactly what a broken check looks like. Two
ways to be silent, both live until now.

**1. «Could not check» read as «nothing new».** The helper returned stdout only. A dead token, a
network error or an unparseable answer produced an empty string, the script concluded «no letters»
and exited 0: the cron ledger says `ok`, the owner hears nothing, every enquiry waits unseen in
the inbox. Proven on the real error path — `--account nonexistent-account` prints to stderr and
returns 1 — the old code came back with `rc=0` and empty stdout.

**2. De-duplication rested on the UNREAD flag.** A letter is composed, then marked read. When
`gmail modify` fails (a 500, a revoked scope) the flag stays, and the same letter is announced
again on the next tick: three ticks, three notifications for one letter, twelve an hour.

**Now**: `call()` returns `(rc, stdout, stderr)`, and any failure — including an answer that is
not JSON — ends in a fixed sentence on stderr plus exit code 1. For a `no_agent` cron that is not
silence: the scheduler delivers script failures (*«a silently broken watchdog is the worst-case
outcome»*) and withholds repeats of the same signature for `cron.failure_repeat_alert_hours` —
which is why the first sentence is constant and the changing detail follows it. Announced ids are
kept in `~/.hermes/state/contact-inbox-state.json`, so UNREAD is a convenience again instead of the
memory. A letter that cannot be read is still announced, with its id and «текст прочитать не
удалось»; more than ten in one tick are summarised as «и ещё N»; the notification carries the
letter's local time.

**Numbers**: new regression `stars-bots-ops/scripts/contact-inbox-regress.py` — 13 checks, no
mailbox and no network, exit 0. Mutation: control 0, delete the id write → 1, swallow the search
`rc` → 1, so the test does tell the two behaviours apart. Live: a real letter from tonight marked
unread again — notification with its time (22.10 19:15), the author's address and the full text;
the second and third runs silent; the state file holds exactly that one id. Site control:
sweep 1701 / 0.

**What it still cannot prove**: that the owner answers, and that the Web3Forms monthly quota is not
exhausted — when the free plan runs out the submission never becomes a letter, and from our side
that is invisible.

## The subject list was translated into the wrong thing (22.10.2026)

Every page lists five subjects: mathematics, **English**, physics, chemistry, history. On eight of
the nine pages the second one was not English — it was the page's own language: «Русский язык» in
Russian, «Español», «Português», «हिंदी», «Bahasa Indonesia», «Türkçe», «Tiếng Việt», «Українська
мова». A Russian parent read that the bot covers Russian-language homework; a Hindi reader, Hindi.
The product covers English as a subject, and it said so only on the English page.

The list lives in two places per dictionary — the chips (`subj.c2`) and the FAQ sentence (`q2a`) —
and once more, in words, in the Russian half of `terms.html`. Both halves of the legal page are
supposed to describe the same product; they described two: *Subjects: mathematics, English…*
against *Предметы: математика, русский язык…*.

**Where it came from**: the first dictionary generation on 15 Oct (commit `2a3aee4`), where the
translator took the word for the school subject and rendered it as the language of the page.
`git log -S'"subj.c2"'` returns exactly one commit — the file's creation — so this was a
translation artefact, not a later decision.

**Why every gate stayed green.** The sweep had two checks for the legal list — "terms subjects EN
== en chips" and "terms subjects RU == ru chips" — and both compared the legal page with chips of
*the same page*. When the chips were wrong on eight pages, the document agreed with them, and the
comparison passed. On 21 Oct the English half of Terms was fixed by hand (it had been copied from
the Russian half); that fixed one symptom and left the cause: the Russian half kept «русский язык»
and eight pages kept their own. This is the same class as the earlier prices and og-card drifts:
a shop window checked against its own reflection.

**Now**: `tools/subjects.json` is the single source (nine languages × five subjects), `build.py`
refuses to write a page whose chips differ from it, and 21 new sweep checks compare the canonical
list with the chips of every language, the FAQ sentence, and both legal halves. Numbers: 1701 →
1722 checks, 0 failed; the canonical list is also the only place where "English" is spelled out,
so changing it is a deliberate act with a diff.

**Proven by mutation, each restored byte-exact**: `ru` `subj.c2` back to «Русский язык» — the build
exits 1 with `ru: subj.c2: 'Русский язык' != 'Английский язык'`, and the sweep fails 2 checks on
the same data; `ru` `q2a` with the second subject removed — 1 sweep failure
(`faq q2a has all five subjects | Английский язык`); the Russian `terms.html` list reverted — 3
failures (the page sha in the lastmod ledger, Terms vs chips, Terms vs the canonical file).

**Also fixed in the same pass**: the Russian half of Terms §7 read «Пожалуйста, не: используйте
бота…» — a colon that broke the sentence in two and left the imperative without its verb. The
document date moved 21 → 22 October 2026 in both halves, because the text really changed.

**Checked in a browser, not only in the sweep**: `viewports-extra` 94 checks / 0 at 320–1440 px,
the visual pass over nine languages at 420 and 1440 px reports 0 problems, and the longer chips
(«Английский язык», «Англійська мова», «Bahasa Inggris») were looked at in the crops: on a 420 px
phone the Russian block wraps 2 + 3 across two lines, no chip clips its text.

**What it cannot prove**: that "English" is the right subject for this product. The gate keeps the
list identical everywhere and makes a change deliberate; it cannot know whether the bot is good at
English essays. Nor does it check the grammar of the FAQ sentence — only that each of the five
subjects appears in it.

## Consumer law on the page: cancelling a purchase, and the rights behind the policy (22.10.2026)

**The Terms never mentioned cancelling a purchase.** `terms.html` had twelve sections and not
one word about refusal — and the owner's rule ("no refunds promised") had been implemented in
the sweep as a blanket ban on the words *refund* / «возврат» anywhere in the legal pages. So the
page could not say the one thing consumer law requires it to say. Under Directive 2011/83/EU,
Article 16(m) (EUR-Lex, CELEX 32011L0083, read from the Publications Office copy), a consumer in
the EU/EEA has 14 days to withdraw, and that right disappears for digital content only when
performance began with the consumer's **prior express consent** *and* an acknowledgement that
the right is lost. Silence is not consent: Terms that say nothing leave the 14-day right alive,
whatever our own policy says.

**What the page says now.** `terms.html` §5 "Cancelling a purchase and refunds" / «Отказ от
покупки и возврат звёзд» — five paragraphs in both halves: the right exists for EU/EEA
consumers; it ends at delivery only if we asked before delivery and the buyer confirmed; where
that confirmation was not given, the right remains; delivery starts when the first breakdown of
the pack is generated; a purchase that does not work as described gets delivered or fixed, or
the Stars for the undelivered breakdowns come back (the remedy Directive (EU) 2019/770 gives for
digital content that does not conform — bring into conformity, price reduction, termination); and
Stars for breakdowns already delivered are not returned on a change of mind. Sections 5–12 were
renumbered 6–13 in both halves, so the new §5 sits where a buyer looks for it: right after the
prices. The document date stays 22 October 2026 — same day, and the text really changed.

**The policy listed rights as a possibility.** `privacy.html` §5 said "depending on your country,
you may also have the right to access or correct" — two rights out of six, no complaint route, no
word about transfers. Now §5 "Your rights and deletion" / «Ваши права и удаление» names access,
rectification, erasure, restriction, objection and portability, withdrawal of consent, the
one-month answer time, and the complaint route (Finland's Data Protection Ombudsman's Office,
tietosuoja.fi, or the authority in the reader's own country). §2 states the legal bases
(contract / legitimate interest / consent / legal obligation). §3 gains the transfers paragraph
and §4 now names the website processors instead of claiming that data goes to Telegram and the
authorities only: Telegram keeps data in data centres in several countries and, for EU or UK
sign-ups, in the Netherlands (telegram.org/privacy); GitHub (USA) relies on the EU–US Data
Privacy Framework and on the standard contractual clauses (docs.github.com); Web3Forms operates
from India and states that EEA transfers run under the standard contractual clauses of its data
processing agreement (web3forms.com/privacy). "Last updated" moved 21 → 22 October 2026 in both
halves.

**Gates instead of good intentions.** The sweep gained 40 checks (1722 → 1762): five required
phrases per language in the withdrawal section, the 1..13 numbering intact in both halves, a ban
on absolute phrasings ("money-back guarantee", «гарантируем возврат», «по первому требованию»),
the refund words allowed **only** inside §5 (a count comparison against that section, not an
allowlist), the nine rights phrases in both halves, transfers and legal bases present, and §4
naming both website processors. The blanket refund ban still covers the landing pages, the
AI-facing twins, the policy and the nine dictionaries; Terms left that loop on purpose and got the
two precise gates above instead, because a legal section has to be able to use the word.

**Proven by mutation, each restored byte-exact** (sha256 checked after every run): `14 days from
the payment to cancel the purchase` shortened to "14 days from the payment" — 2 sweep failures;
the Russian fallback sentence replaced by «Подтверждение не требуется.» — 2; a right deleted from
§5 of the English policy — 2; §4 reduced to "(b)" so GitHub and Web3Forms vanish from the sharing
paragraph — 2; the word "refunds" put back into the FAQ of `index-src.html` — the old blanket gate
still bites (1 failure, `['index-src.html:refund']`). 1762 checks / 0 failures after the restores.

**Checked in a browser, not only in the sweep**: `landing-nu-validate.py` — privacy and terms 0
findings (81 known-false messages across the nine language pages, unchanged); a fresh 16-check
eye pass at 420 and 1440 px on both documents: no horizontal overflow, no paragraph wider than its
box, the §5 heading present and not clipped, the self-hosted font actually applied. Section
screenshots in both languages at both widths: `evidence/legal-20261022/`.

**What it cannot prove**: the Terms now describe the rule, but the bot still sends the invoice
straight from the "pay" button with no consent step (`bot/handlers.py`, `cb_pay` → `send_invoice`)
— so for an EU buyer the 14-day right is still alive today, and the page says so honestly instead
of pretending otherwise. Making the exception real is a bot change: one confirmation before the
invoice, worded exactly as the consent the Terms describe. Also unverified: whether "the operator
of UchiSamBot" is enough as the controller's identity — a name and an address for complaints are
missing, and publishing them is the owner's decision (the phone number is off-limits by his rule).

## The demo video played on; nothing on the page could stop it (22.10.2026)

**What was found.** The hero demo is a 13-second loop that starts by itself
(`autoplay muted loop`) and there is no control of any kind: no `controls` attribute, no
button, no way to stop it short of closing the tab. WCAG 2.2.2 *Pause, Stop, Hide*
(Level A) asks exactly for that — moving content that starts on its own, runs longer than
five seconds and sits next to other content must offer a pause, stop or hide mechanism.
The site's accessibility line ("axe-core, 0 violations across 11 pages") never contradicted
this, because axe cannot test 2.2.2: it is a manual criterion, so the gap survived every
earlier pass, including the visual one. Reduced-motion and Save-Data visitors were already
served the poster; everyone else had a loop they could not switch off.

**What is on the page now.** A 44×44 round button in the top-right corner of the phone
frame, inside the video's rounded corner, dark plate with a white icon. It is written into
the markup as `hidden` and un-hidden by the script, because a button that cannot work
without JavaScript is a dead control. The name of the button is the action, not the state:
"Pause the demo video" while it plays, "Play the demo video" after a stop, and the icon
swaps with it (`data-state="pause|play"`). Both strings live in the nine dictionaries —
`vbtn.pause` / `vbtn.play` — and reach the attribute through a new build mechanism,
`data-i18n-attr="aria-label:vbtn.pause;data-play-label:vbtn.play"`: attribute labels are now
translated by the same pass that bakes body text, an unknown key fails the build, and a
page that still carries an `data-i18n-attr` marker is refused (`build.py`, checks at the top
and after each page). Two DOM labels inside the button would have been simpler and wrong:
the accessible name would read both at once.

**The behaviour, not just the button.** The loop pauses when it leaves the viewport and when
the tab goes to the background — a phone should not decode a video nobody sees — and resumes
on return only if the visitor never stopped it themselves; a manual stop outranks our resume
logic. With `prefers-reduced-motion: reduce` or Save-Data the video still does not start at
all, the button offers "play", and a deliberate press starts it: the visitor's choice beats
the system setting, the system setting beats our autoplay. This replaced the earlier block
that only removed `autoplay`/`loop` for those visitors and left everyone else with no
control.

**Gates instead of good intentions.** The sweep grew by 81 checks (1762 → 1843): per
language, the button exists and sits inside `.phone-frame`, it is `hidden` at load, both
labels equal that language's dictionary, the two labels differ, the pause label is not the
English one on a non-English page, the CSS carries 44×44, and the script is wired
(`getElementById('video-toggle')` + `visibilitychange`). Static gates prove the parts are
present, not that the mechanism works — so the block adds a browser battery,
`landing-video-motion.py` (363 checks): nine languages × two widths (420 / 1440 px) for
size, position inside the video, dictionary labels, autoplay, click-to-stop with the label
and `data-state` flipping, Enter from the keyboard resuming, off-screen stop and return
resume, 320 px reflow with the button still on screen; then a `prefers-reduced-motion`
context per language (no autoplay, offers play, the press really plays) and one user-intent
scenario in English (stop → scroll away → return → still stopped; start → scroll away →
return → resumes).

**Proven by mutation on the built page, each restored byte-exact** (sha256 of `index.html`
compared before and after the whole run): the button deleted from the markup — 17 battery
failures; the click handler renamed to a no-op — 9; the IntersectionObserver block removed —
2 (`off-screen pauses` on both widths); both labels made identical — 6. The first negative
control also exposed a defect in the battery itself: a missing button made `page.click` wait
30 s and crash instead of recording a failure; the harness now checks the button's
existence first and reports one honest "interactions" failure.

**Numbers on the finished build.** `tools/build.py` rc=0, nine pages plus 404 (EN 55 498
characters / 59 456 bytes — 4 340 bytes more than the previous page for the CSS, markup and
script); sweep 1843 checks / 0 failures;
`landing-a11y-extra.py` 68/0 (the button joins the tab order and the skip-link walk without
breaking the cycle), `landing-wcag22-targets.py` 43/0 (44 px target), `landing-env-prefs.py`
45/0, axe 0 violations on 12 pages, `landing-cross-engine.py` 36 runs / 0 problems in WebKit
and Firefox (IntersectionObserver, `visibilitychange` and `media.play()` behave the same),
`landing-cwv.py` 69/0, `landing-contact-e2e.py` 468/0, `landing-visual-pass.py` PROBLEMS 0
on nine languages × two widths. Eyes: hero screenshots at 420 and 1440 px in
`evidence/video-motion-20261022/` and `evidence/visual-20261022e/` — the button sits in the
empty right side of the chat header, covers no text, and the mock keeps its proportions.

**What it cannot prove.** That the top-right corner is the *most* tasteful place for the
control — the owner's eye decides that, and moving it is a one-line CSS change; and that
every browser will autoplay: iOS Low Power Mode never starts a video, so the button then
shows "play" from the first second, which is the honest state rather than a bug.

## Without JavaScript the demo kept playing and the pause button did nothing (23.10.2026)

**What was found.** The stop button from the previous block ships in the markup as
`hidden` and is un-hidden by its script, so that a visitor without JavaScript never sees a
control that cannot work. The comment said so; the browser disagreed. The stylesheet set
`.video-toggle{display:grid}`, and an author `display` rule beats the user-agent rule
`[hidden]{display:none}` — so the button was painted on the frame at first paint, before any
script ran. On top of that the `<video>` carried `autoplay` in the markup: with scripting
disabled (or with the script blocked, or after an error earlier in the page) the 13-second
loop started anyway, while the button that was supposed to stop it did nothing — and the
`prefers-reduced-motion` promise, which is kept by the script removing the attribute, was
ignored too. Nothing caught this because every gate, every battery and every screenshot ran
with JavaScript on.

**What is on the page now.** `autoplay` is gone from the markup: motion starts only inside
the script that owns the stop control, and only after that control has been found
(`if (!reduce && !save) play();` sits after the `btn` lookup, so a page without the button
never moves). Without JavaScript the visitor sees the poster — a still frame of the same
demo, in their language — and no button at all. The CSS now hides the control by default and
shows it through `.video-toggle:not([hidden]){display:grid}`, so `hidden` means hidden and
the script is the only thing that can reveal it. Behaviour with JavaScript is unchanged:
muted loop, pause on click and on Enter, stop when off-screen or in a background tab,
reduced-motion and Save-Data visitors get the poster and can still press play.

**Gates.** The sweep grew by 27 checks (1843 → 1870), three per language: the `<video>` tag
carries no `autoplay`, the start line under the preference gate is present, and the CSS
`display:none` + `:not([hidden])` pair exists. Static gates cannot see whether the page
actually moves, so the browser battery `landing-video-motion.py` grew from 363 to 408
checks: nine languages in a context with scripting disabled — two screenshots of the video
frame 0.9 s apart must be pixel-identical (PIL `ImageChops`, byte compare as fallback), the
toggle must not be visible, the poster attribute must be there, the page text must still be
readable (the reveal animation hides nothing without `.js`), and — the general form of the
same defect — every element that still carries `hidden` in a script-less page must compute
to `display:none`, not just the one button. `landing-browser-smoke.py` also gained a
JS-on check of that invariant (18 page/width runs), for elements that stay hidden after the
scripts have run.

**Proven by running the new battery against the previous page** (`git show HEAD:index.html`
into a throwaway copy of the site): 48 checks, 3 failures — exactly "кадр стоит" (the frames
differed), "кнопки «пауза» не видно" (visible) and "все элементы с hidden скрыты без
скрипта" (named `video-toggle`). Same battery on the fixed page: 408/0. The negative
control is the reason to trust the new checks: before the fix they fail, in the exact way a
visitor would have seen it.

**Numbers on the finished build.** `tools/build.py` rc=0, EN 56 599 characters / 60 883
bytes (+1 427 bytes for the comments and the CSS pair); sweep 1870/0;
`landing-video-motion.py` 408/0 in 116 s; `landing-env-prefs.py` 45/0 (its control check
used to assert that the `autoplay` attribute exists — it now asserts the opposite and that
the video started without the harness's nudge, `triedPlay=false`, i.e. the page's own script
did it); `landing-a11y-extra.py` 68/0; `landing-wcag22-targets.py` 43/0;
`landing-axe-audit.py` 0 violations on 12 pages; `landing-cwv.py` 69/0 (LCP/CLS unchanged:
the poster is still the LCP element and it is still preloaded); `landing-cross-engine.py`
36 runs / 0 problems in WebKit and Firefox; `landing-render-check.py` ALL OK including its
own `no-js /ru/: visible: True` probe; `landing-price-parity.py` 9/0;
`landing-links-audit.py` 11 pages / 0; `landing-en-leftovers.py` 0; `landing-fonts.py` 39/0;
`landing-poster-frames.py` 9 posters / 0; Nu validator: no real findings;
`landing-visual-pass.py` PROBLEMS 0 on nine languages × two widths;
`landing-browser-smoke.py` 18 runs / 0 (with the new `hidden` check); `landing-contact-e2e.py`
468/0; `landing-viewports-extra.py` 94/0 under throttling; `landing-glyph-fallback.py` 12
pages / 0 substituted glyphs; `landing-external-links.py` 0 broken links.

**What it cannot prove.** That every browser will start a muted video from a script: iOS Low
Power Mode never does, and some privacy extensions block media outright. In those cases the
hero stays a still poster with a "play" button — the honest state, and the same one the
previous block accepted. Nor that a visitor without JavaScript prefers a still frame to the
demo: the frame is the only thing a script-less page can show without moving.

## The last thing the page asked of other people's servers (23.10.2026)

Eight of the nine launch badges on every page were hotlinks: `fazier.com`,
`statics.startupbase.io`, `showmebest.ai`, `lift-off.sh` (twice), `cdn.openhunts.com`,
`auraplusplus.com`, and — the worst place for it — `launchigniter.com` in the hero, above the
fold. On top of that the `<head>` carried `preconnect` to LaunchIgniter (an early TCP+TLS
handshake, before anything is drawn) and seven `dns-prefetch` hints. So opening any of the
nine language pages, or either legal page, told eight companies the visitor's IP address and
that the visit came from our site — before the visitor clicked anything. The privacy policy
said so, honestly, in both languages; that honesty was the defect's receipt.

The failure mode was also real, not theoretical: on 21 Oct Chrome refused the Startup Fame
badge as ORB (`ERR_BLOCKED_BY_ORB`), the `onerror` handler hid the link, and the page showed
seven platforms out of eight — silently.

**What changed.** The platforms' own badge art is now stored in `img/badges/` and served from
our origin: nine files, 148 KB in total — the same bytes the page used to pull from those
servers, now from our own connection, and every one byte-identical to what the platform serves
(no re-encoding — a brand mark is not the place to save a kilobyte). All badge URLs, and every
`preconnect`/`dns-prefetch` hint to a third party, are gone; the only external host left in the
markup is `api.web3forms.com`, and only because the contact form posts there. `privacy.html`
(two languages) and its markdown twin now say the truth in the other direction: the pictures are
ours, no request leaves for the platforms, and a click is what takes you to them.

**Why not the smaller files.** Rasterising the badges to 2x WebP was measured first: 148 KB →
34 KB. It was rejected — the re-encoded LiftOff award showed a pale band across the top and
softer text next to the original in a side-by-side crop. All nine badges are `loading="lazy"`
below the fold anyway, and the bytes now come from the same origin over the same connection
instead of eight separate TLS handshakes. A hundred kilobytes are not worth shipping a worse
copy of someone else's logo.

**What the gates learned** (`landing-sweep.py`, 1875 checks, 0 failures):
- no third-party image host on any page (9 languages + privacy + terms + 404);
- every referenced badge file exists and is really an image — SVG must start with `<` and
  contain `<svg`, WebP must carry `RIFF….WEBP`, so a saved HTML error page cannot pass as art;
- the set of badge files on the pages equals the set on disk, and the counts are pinned
  (9 on the landing page: hero + footer, 3 on each legal page);
- the privacy policy states it in English and in Russian, and so does `privacy.html.md`;
- no `preconnect` anywhere, and `dns-prefetch` only to `api.web3forms.com`.

**Checked after the change.** Build reproducible (a second `tools/build.py` leaves `git status`
clean); sweep 1875/0; `landing-links-audit.py` 11 pages / 0; Nu validator: no real findings;
`landing-visual-pass.py` PROBLEMS 0 across nine languages × 420/1440, with the footer strip at
4+4 badges on desktop and 2×4 on mobile as before; the badge strip and the hero badge were
inspected at 2x in Chromium and compared against the live hotlinked page — identical geometry
(212×55) and identical art. The local page now makes zero third-party requests on load; the
live GitHub Pages copy is checked after the push by `landing-live-bytes.py` and
`landing-live-assets.py`.

**What it cannot prove.** That a platform will not change its badge art tomorrow: our copy then
stays as it is, which is the point of owning it, and refreshing it is a one-file download. That
a badge is legible at 46 CSS pixels on every display — verified at 2x here, not on a real phone.
And the Web3Forms monthly limit is still invisible from our side (unchanged, it is outside the
code).

## The language menu could be opened and never dismissed (23.10.2026)

The nine-language switcher is a native `<details>`: it opens on click, on Enter and on Space — and
then it stayed open. Escape did nothing; a click anywhere else on the page did nothing. On a 420 px
screen the open list of nine languages covers the first screen, and the only way back was to hit
the same 44-px summary again, the smallest target in the header. Measured before the fix in
Chromium, WebKit and Firefox at 420 px: `open` was still true after Escape and after an outside
click, and focus stayed on the language link.

**Why no gate caught it.** The keyboard battery proved that the menu OPENS via Enter, that it holds
nine entries and that Tab reaches a link inside it — the opening half of the control. No check
asked whether it closes. A gate that tests only the half a control does first will approve a trap.

**What changed.** One standalone `<script>` block at the end of `index-src.html` (~1.5 KB raw,
+0.6 KB gzipped per page): Escape closes the menu and puts focus back on the summary, as the
disclosure pattern requires; any click outside closes it without moving focus. It is a separate
IIFE on purpose — the contact-form script begins with `if (!form …) return`, which would have
skipped anything appended to it. With JavaScript off nothing changes: `<details>` still opens and
closes by its own summary.

**What the gates learned**
- `landing-a11y-extra.py`: focus is first placed on a language LINK (not on the summary, where the
  focus-return assertion would pass for free), then Escape must leave `open=false` with focus on the
  summary, and a click on the page heading must leave `open=false`. Before: 6 failures (3 × ru,
  3 × hi); after: 78 checks, 0 failures.
- `landing-cross-engine.py`: the same three assertions now run inside every WebKit and Firefox run,
  because key handling and click-outside differ per engine (18 mobile runs, 0 problems).

**A second defect found by the same pass: a gate that had been red since the badges moved.**
`landing-browser-smoke.py` still simulated "the platforms' servers are unreachable" and expected the
eight hotlinked badges to hide via `onerror`. Since 23.10 all nine badges are served from
`img/badges/`, so that scenario measured `external images 0` and reported a failure on every run — a
permanently red check. Permanently red is worse than absent: it trains everyone to skim the output,
and the next real failure hides behind it. It now tests what can actually break: abort all nine
badge files → every link hides, no broken icon is left and the layout keeps its width; abort one
file → exactly that link hides and the other eight stay visible and loaded (so the per-image
`onerror` works, not a CSS rule that would hide the whole strip).

**Checked after the change.** Build reproducible (a second `tools/build.py` leaves `git status`
clean apart from the lastmod ledger it rewrites from content hashes); sweep 1875/0;
`landing-links-audit.py` 11 pages / 0; `landing-browser-smoke.py` 18/18 runs with both badge
scenarios (9/9 hidden; 1 hidden + 8 intact); `landing-a11y-extra.py` 78/0; cross-engine 18 mobile
runs in WebKit and Firefox, 0 problems.

**What it cannot prove.** That a hardware-keyboard Escape reaches `keydown` the same way on a phone
when the menu was opened by touch — the engines here are emulated, not a real device. Nor that a
visitor expects an outside click to close this particular list: it is the only navigation of its
kind on the page, and the stake is one extra tap, not a lost sale.

## In landscape the language menu stopped at the sixth language (23.10.2026)

The switcher's list is a fixed height on a touch device: nine rows of 44 px, 2 px gaps, 16 px
padding, 2 px border — 430 px. In portrait that fits any phone. In landscape it does not, and the
list is `position:absolute` inside the sticky header, so there was nothing to scroll: the list
continued past the bottom edge and stayed there. Measured with touch emulation, menu open, before
the fix:

- 844×390 (phone landscape): the list ran from y=61 to y=491 on a 390 px screen. Vietnamese sat at
  392–436 and Ukrainian at 438–482 — two of the nine languages were entirely outside the screen,
  and `scrollHeight` equalled `clientHeight` (428/428), so dragging brought nothing back.
- 568×320 (small phone, landscape): four of the nine were below the edge.
- With the sticky "Open in Telegram" bar up (its `z-index:40` outranks the header's stacking
  context), the list's bottom at 491 lay under a bar whose top was 331 — off-screen *and* covered.
- Portrait was clean from 320 to 1280 px wide: zero findings. The 320 px reflow pass cannot see
  this, because it varies the width; the defect lived in the height.

**Why no gate caught it.** The keyboard battery proved the menu opens with Enter, holds nine
entries and — since the block above — closes on Escape and an outside click. The smoke run proves
the header renders and no script throws. Nothing asked whether every entry can be *reached* when
the screen is shorter than the list: "the control works" and "all of the control is on the screen"
are different questions.

**What changed**, in three layers of decreasing dependence:

1. A CSS ceiling — `max-height:calc(100vh - 132px)` (`100dvh` behind `@supports`),
   `overflow-y:auto`, `overscroll-behavior:contain`, `scroll-snap-type:y proximity`,
   `scrollbar-width:thin`. 132 px = header 63 + gap 8 + sticky bar 57 + slack. Without JavaScript
   the list scrolls now, but the ceiling slices the sixth row through a letter.
2. The menu script measures that ceiling in **whole rows** against the real space left above the
   sticky bar, so the cut lands on a row boundary: 6 rows (292 px) at 844×390, 5 rows (246 px) at
   568×320, and 5 rows when the bar is up — its top at 331 against a list bottom of 307.
3. The same script adds a `more` class while something is left below and draws an **inset** bottom
   shadow (inset keeps the drop shadow; a `mask-image` fade would have clipped it away), removed
   at the end of the list and recomputed on open, on scroll and on resize/rotation. The inline fit
   costs 4.3 KB raw and 1.5 KB gzipped per page.

**What the gates learned.** `landing-a11y-extra.py` gained section E — 26 checks in an 844×390
touch context: nine entries; the list fits or scrolls; the `more` hint is present exactly while
the list overflows and gone at its end; the last language is reachable and hittable under the
pointer after scrolling; focus on the last language scrolls it into view; the open list clears the
sticky bar; no page errors. 104 checks in total, 0 failed.

The gate was proved to bite, not just to pass: the same battery run against a copy of the site with
the old CSS (`LANDING_ROOT=…`) reports **13 failures** — `list bottom=491 vh=390 canScroll=False`,
`'Українська' rect=438..482 vh=390 hit=none`, `list bottom=491 bar top=331` — one set per language
plus the sticky-bar check. Red before, green after.

**Checked after the change.** Build reproducible (a second `tools/build.py` leaves the worktree
byte-identical — same diff hash); sweep 1875/0; smoke 18/18 runs, 0 problems; cross-engine WebKit +
Firefox, 18 mobile runs, 0 problems; screenshots at 844×390 and 568×320 read at 2x — the list ends
on a row boundary, no sliced glyph, and the shadow reads as "more below".

**What it cannot prove.** That a real phone's landscape viewport equals 390 px — `100dvh` follows
the browser toolbars, and no emulator models those exactly. That a visitor takes an inset shadow
for "scroll" when the scrollbar itself is invisible on a phone. That six rows beat nine on a 320 px
screen: the choice was to keep every language one scroll away instead of building a second,
two-column layout that exists only in landscape. And the geometry was measured in Chromium with
touch emulation; WebKit and Firefox get the same CSS, but their scrollbars, snapping and `dvh`
handling are their own — the cross-engine run proves the page, not this geometry.

## The menu's geometry was proven in one engine and shipped to all of them (23.10.2026)

The previous block made the language list stop on a whole row and scroll, and proved it with 26
checks in Chromium. Its own closing paragraph named the hole: "the cross-engine run proves the
page, not this geometry." Visitors do not arrive in desktop Chromium. On iOS every browser,
including Telegram's in-app one, is WKWebView (WebKit); on Android it is Chromium but a different
viewport, and Firefox is a real minority on both. The geometry had never been measured in either
of the other two engines.

**What was measured.** `landing-cross-engine.py` gained a landscape section: four phone-landscape
viewports (844×390, 915×412, 667×375, 568×320), three languages that stress the list (ru, vi, hi),
two engines — 24 runs. Each run keeps the page scrolled, so the sticky "Open in Telegram" bar is up
(its 57 px is the worst case for vertical room) and opens the menu from the sticky header there.
Per run: nine entries; the list either fits the screen or really scrolls (`scrollHeight >
clientHeight`); the `more` shadow is present exactly while the list overflows and gone at its end;
the last language, after scrolling, is inside the viewport and hit-testable at its own centre; the
list bottom and the last row clear the sticky bar; no page errors.

**Result on the shipped pages: 24 runs, 0 problems.** The inline fit script computes the same
ceiling in both engines, to the pixel: 292 px = 6 rows at 915×412, 246 px = 5 rows at 844×390,
200 px = 4 rows at 667×375, 154 px = 3 rows at 568×320, with `scrollHeight` 428 against client
heights of 290 / 244 / 198 / 152. So all nine languages stay one scroll away in WebKit and Gecko
too, and the hint appears and disappears with the overflow in both.

**The gate was proved to bite.** The same section run against the pre-fix build (`git archive
8db0889`) fails 24 of 24 runs with five distinct signatures: `list bottom=491 vh=390`,
`list bottom=491 under sticky bar top=261`, `last language 'Українська' not in view: 438..482
vh=390`, `not hittable`, `last entry bottom=482 under bar top=261`. That is the defect the previous
block fixed, now caught by the engines that actually ship on phones.

**Two ways the new gate lied before it told the truth.** The first version read the `more` class in
the same JS task that set `scrollTop = scrollHeight`; the class is recomputed by the `scroll`
handler, which runs after that task, so 12 of 12 runs "failed" on a correct page — the scroll and
the read are now separate calls with a 300 ms pause. The second version scrolled the page back to
the top before opening the menu, which hides the sticky bar: the overlap check then measured
nothing at all. The page now stays scrolled, and every row records whether the bar was really up
(`bar=up/down`), so a future change that suppresses the bar cannot make that check pass by
accident. At 915 px wide the bar legitimately does not appear (desktop threshold) — the row says
`bar=down` and the run passes.

**Checked after the change.** The site's own files are untouched by this block, so the build was
re-run to prove it: `tools/build.py` leaves `git status` empty. Sweep 1875 / 0. Full cross-engine
battery with the new section: **60 runs, 0 problems, 428.6 s** (36 page runs as before plus the 24
menu runs, about 120 s more). Live parity on Pages: 24 published files (nine pages, their markdown
twins, privacy, terms, 404, sitemap, robots, llms) byte-identical to the local build. Both mirrors
at the same commit.

**What it cannot prove.** That an emulated 390 px landscape equals a real iPhone's visual viewport:
iOS toolbars move and `100dvh` follows them, and no emulator models the address-bar animation.
That GeckoView (Firefox on Android) behaves like the desktop Firefox used here. That a finger's
momentum scroll and snapping inside the list feel the same as a programmatic `scrollTop` jump — the
gate asserts reachability, not feel. And that three visible rows out of nine, at 568×320 with the
bar up, is the right trade: the alternative, a two-column list that exists only in landscape, was
declined twice now.

## The page was confident; the small print was honest (23.10.2026)

Ten FAQ answers covered cheating, subjects, languages, payment, installation, Stars, timing, failure
and the difference from a general chatbot. None of them said the obvious thing: the explanations are
generated by AI and can be wrong. The Terms did — §9, "Accuracy disclaimer" — and the marketer's
round-1 note asked for the same sentence on the page. The sentence never arrived. A parent deciding
whether to pay reads the FAQ, not the Terms; and the JSON-LD `FAQPage`, the copy search engines and
AI assistants quote, carried the same ten confident answers.

**What was added.** An eleventh question at the end of the FAQ, in all nine dictionaries — "Can the
answers be wrong?": *The explanations are generated by AI, so a mistake is possible. Every step is
shown, so you can check the reasoning against your textbook or with a teacher. If an answer looks
wrong, send it to us through the form — we read every message.* It promises no refund and no
accuracy; it tells the reader what to do with a wrong answer. Because `tools/build.py` builds the
`FAQPage` from the same dictionary, the structured data carries it too, and the markdown twins — the
AI-facing layer — picked it up without a second edit.

**Why the end, not the second slot.** Inserting it after "Is this cheating?" would renumber q2…q10
in nine dictionaries; every gate that names q9a (the contact channel) or q10a (the third-party-AI
claim) would silently start checking a different answer. At the end it costs nothing: the last thing
the reader sees before "Stuck on a problem right now?" is the honest limit, and the CTA follows it.

**The sentence is backed by a running mechanism, not a promise.** "We read every message" is the
only claim in the answer that depends on us rather than on the reader; the landing inbox is read by
the `обращения-лендинга` cron (every 10 minutes, `contact-inbox-check.py`), which is how a letter
reaches a human. If that cron dies, the sentence becomes exactly the class of promise this project
keeps removing — it is named here so a later block checks the cron, not only the page.

**Four gates that counted to ten.** `landing-sweep.py`, `landing-browser-smoke.py`,
`landing-cross-engine.py` and `landing-live-assets.py` each held the FAQ size as a literal. Adding a
question meant editing the dictionaries *and* four test scripts, and the first run after the change
proved it the hard way: all 60 cross-engine runs reported `ISSUES` on a correct page, and the live
check would have called nine pages wrong. All four now count the `qN` keys in the language
dictionary — the single source of the texts — and the sweep's JSON-LD check compares the answer
count with that same number instead of a second literal.

**Checked after the change.** `tools/build.py` rc=0 and `git status` shows only the intended files
(9 dictionaries, 9 pages, 9 twins, the template, the lastmod ledger, this file). Sweep 1875 / 0. Browser smoke
18 runs (nine languages × desktop and mobile), 0 problems. axe 12 pages, 0 violations. WCAG 2.2
targets 43 / 0. Contact end-to-end 468 / 0. Glyph coverage 12 pages, 0 characters painted by a
system font — the new Hindi, Portuguese, Indonesian and Vietnamese sentences are covered by the
fonts already shipped. Cross-engine 60 runs / 0.

**What it cannot prove.** That my Hindi and Vietnamese read like a native wrote them: no native
speaker reviewed them; the wording follows the register the dictionaries already use (आप, bạn) and
the sentence structure of the English. That the inbox cron stays alive — see above. And that an
eleventh answer gets read at all: length is not attention.

## The policy changed; its own date did not (23.10.2026)

At 02:33 on 23 October, §7 of the privacy policy was rewritten: the eight launch badges moved from
the platforms' servers to ours, and the sentence a reader relies on changed from "the platform sees
your IP address and that the request came from our site" to "opening a page sends no request to
those platforms at all". The page was edited, committed, deployed — and still said "Last updated:
22 October 2026". Nothing else on the site tells a reader that the data-sharing disclosure changed;
the date is the only thing that does.

**Why no gate looked there.** The sweep did check legal dates — against a hand-written ledger:
`LEGAL_DATES = {"privacy.html": ("22 October 2026", "22 октября 2026"), …}`. That is a copy of the
date, not a fact about the file. The copy goes stale exactly on the day it matters: the text changes,
the ledger does not, and the run prints `FAILED: 0`. The same class as the badge gate that had been
red since the files moved and the FAQ counter that was a literal — a gate reading a second copy of
the truth instead of the truth.

**What replaced it.** The date now has to equal the day the *visible text* of the page last changed,
read from git. `_legal_last_text_change()` walks the file's commits from newest to oldest, extracts
`<main>` from each revision, strips the two date lines, and returns the date of the first commit
whose text differs from the previous one. Stripping the date lines is what keeps the check from
chasing its own tail: without it, bumping the date would count as a text change and every document
would keep dating itself to the day it was last dated. Two more checks hold the twin and the two
language halves: the `.md` file must carry the same day in English and Russian, and the two halves
must name one day that is not in the future. The ledger is gone; the sweep is 1881 checks (+6).

**Terms was not bumped, deliberately.** `terms.html` also changed on 23 October — but only in the
`<head>` (`dns-prefetch` links removed) and in the footer (badge images now local). Its visible text
did not change by a word, so its date stays 22 October. A gate that demanded a bump for that would
demand a lie in the other direction, and would be switched off within a week — the same lesson as
the always-red badge gate. The check compares text, not mtime and not the commit list.

**The working tree counts as today.** The project's order is build → sweep → commit. If the check
read only committed history, an honest edit would turn the sweep red *before* the commit and force
the order to be broken. So when the working tree's text differs from `HEAD`, the required date is
today. Verified by mutation: with yesterday's date left on an edited page, the run fails with
`история 23 October 2026 (рабочее дерево (не закоммичено))`.

**Checked.** Build rc=0; the build touched three files (privacy.html, its markdown twin, the lastmod
ledger), a second build is byte-identical, and this README is the fourth file in the commit. Sweep
1881 / 0. Links 11 pages / 0. Nu validator exit 0 (only the known parser gaps on
`overscroll-behavior`, `dvh` and four-argument `rgb`). Browser smoke 18 runs (nine languages ×
desktop and mobile) / 0. Negative controls: the pre-fix page fails the new check
(`страница 22 October 2026 / история 23 October 2026 (c25662a6)`), a stale `.md` twin fails one
check, a drifted Russian half fails four; every mutation was restored and verified by sha256.

**What it cannot prove.** That the date equals the day a reader could first see the change: it is
the day of the commit, and Pages deploys minutes later — the same day, unless the commit lands just
before midnight. That the machine's clock is right: the page and the history are stamped by the same
clock, so a wrong clock writes the same wrong day twice and this gate agrees with both. That an
uncommitted edit kept for a week keeps its first day — it does not; every run dates it to today,
which is honest but not a history. And that a date makes a policy compliant: it records when the
words changed, not whether they are sufficient.

## The validator was reported green for five hours while returning an error (23.10.2026)

At 05:13 the language menu got its height ceiling: `max-height:calc(100vh - 132px)`,
`calc(100dvh - 132px)` behind `@supports`, `overscroll-behavior:contain`, and an inset shadow for
the "more below" hint. Every run of `landing-nu-validate.py` since then exited **1** — four
findings on each of the nine language pages: `overscroll-behavior doesn't exist`,
`height: Unknown dimension` (`100dvh`), `max-height: Parse Error` (`calc(100dvh - 132px)`), and
`box-shadow: rgb(20, 40, 90, 0.30) is an incorrect operator` — and the section above this one,
written the same night, states "Nu validator exit 0 (only the known parser gaps on
`overscroll-behavior`, `dvh` and four-argument `rgb`)".

**All four are the validator's gaps, not the page's.** The bundled `vnu.jar` predates `dvh` and
`overscroll-behavior`; worse, its CSS parser rewrote the source's valid `rgba(20,40,90,.30)` into
four-argument `rgb()` and then rejected its own rewrite. A browser accepts every one of them —
which is exactly why the fix could not be "believe the validator" or "delete the CSS".

**Why nobody saw it.** The gate was read as `python3 landing-nu-validate.py | tail -6`: that prints
the exit code of `tail`, and the line that carries the verdict (`=== РЕАЛЬНЫЕ НАХОДКИ ===` and the
findings under it) sat below the cut. The report then quoted the exit code from memory of the last
time it had been green. A gate whose result is read from a truncated screen, with a document next
to it asserting the good state, is not a measurement — it is the appearance of one. Same family as
the badge gate that had been red since the files moved.

**What replaced it.** `KNOWN_FP_PAIRS` — the message fragment *and* a mandatory fragment of the
`extract` must both match. Anything less is a real finding: `Unknown dimension` without `100dvh`,
`max-height` without `dvh`, `incorrect operator` without `var(--shadow-2)`, and `overscroll-behavior`
with any other value all still fail. Verified with ten synthetic messages: the four genuine parser
gaps pass as known, six look-alikes (a broken `height:100foo`, a broken `calc` with no `dvh`, a
different shadow, a different `overscroll-behavior` value, an ordinary `color` error, an HTML error)
stay real.

**And the page's side is now proven in a browser, not read off the CSS.** `landing-a11y-extra.py`
grew a no-JavaScript pass (section E2, four checks on `ru`, `hi`, `en` at 844x390): computed
`max-height` equals screen minus 132 px (258 px), the open list is cut by it, it still scrolls
(428 > 256 px), and `overscrollBehaviorY` computes to `contain`. Without JavaScript on purpose: with
the script running, `fit()` re-caps the list to whole rows (292 px at that height), so the CSS
declaration is no longer visible in the computed value — the first version of this check demanded
258 px with JS on and failed for that reason alone. Easier to notice in the diff than in the
running site: the check was wrong, not the page.

**Checked.** Negative control: removing `max-height`, the `@supports` ceiling and
`overscroll-behavior` from the built `index.html`, `ru/`, `hi/` produced 16 failures (four per
language in E2, four in the JS path); `clientHeight` became 428 px on a 390 px screen and the list
stopped scrolling. Files restored with `git checkout --`, sha256 equal to the `tools/lastmod.json`
ledger (f29abfe0 / 15d186a3 / 726fc693), working tree clean. Then: build rc=0 and byte-identical on
a second run; sweep 1881 / 0; Nu 126 known gaps / 0 findings / **rc=0**; a11y-extra 124 / 0 (was
104); render-check ALL OK; links 11 pages / 0; axe 12 pages / 0; smoke 18 runs / 0; video-motion
408 / 0; viewports 94 / 0; price parity 9 / 0; posters 9 / 0; English leftovers 0; live assets and
external links clean.

**What it cannot prove.** That `vnu.jar` is the right judge for CSS at all — it is not, and keeping
a whitelist is a permanent tax: every new CSS feature costs a pair here, and a careless pair would
hide a real error. The no-JS pass covers three languages at one viewport, 844x390 — the short-screen
case the ceiling exists for, not all nine languages and not a tall screen. And that a green battery
means the site is good: it means the things this battery measures are still true.

## The promise that depended on a cron nobody watched (23.10.2026)

The eleventh answer, added three hours earlier the same day, ends with a sentence the reader has no
way to check: "If an answer looks wrong, send it to us through the form — we read every message."
Every other claim on the page is about the reader's own experience; this one is about us, and the
mechanism behind it is a `no_agent` cron job named `обращения-лендинга`: every ten minutes
`contact-inbox-check.py` asks the mailbox for `from:web3forms.com subject:"UchiSamBot contact form"
is:unread`, and turns anything it finds into a Telegram message to the owner. The page was
documented as promising that, and the README said in as many words that a later block should check
the cron and not only the page.

**Why nothing caught it.** The failure signature of this channel is silence, and silence is also the
normal answer: a cron that is paused, deleted, or whose sender filter matches nothing returns "no
messages" twenty-four times an hour and never fails. Hermes reports a job that errors; it does not
report a job that is gone from `jobs.json` — a file this machine has already had to rebuild once
(a `.corrupt-20260916` copy sits next to it). Nothing in the page's battery reads that file.

**What the mailbox actually holds.** The live audit finds nine letters from Web3Forms: seven form
submissions (15.10, four on 21.10, two on 22.10) and two service letters (the welcome message and
the verification code). The cron's ledger `~/.hermes/state/contact-inbox-state.json` knows one of
the seven — the 22.10 16:15 submission, the last one — because the ledger was introduced on 22.10;
the other six predate it, were read at the time, and still carry no `UNREAD` label. The two service
letters are not submissions and are ignored by the subject filter, correctly.

**The hole nobody had looked at.** Gmail's search excludes SPAM and TRASH unless the query says
`in:anywhere`. The cron does not say it — and it should not, a submission in spam is not something
to announce as a message to read — but that means a submission that lands in spam is invisible to
the cron forever, while the page keeps promising it was read. The audit therefore searches
`in:anywhere` and treats any submission in SPAM or TRASH as a loss, whatever else is true.

**Two gates, in different places, for different questions.** The sweep now asks whether the
machinery is alive: exactly one job whose `script` ends in `contact-inbox-check.py`, enabled and
`scheduled`, `no_agent` (a model in the loop is a different mechanism), interval no coarser than
thirty minutes, last run no older than sixty, last status `ok` with `failure_streak` 0. On a machine
that has no `~/.hermes/cron/jobs.json` — a clone, another host — it prints one check whose name says
`SKIP`, not a green claim it cannot support. `landing-inbox-canary.py` asks the other question, about
the crate rather than the machinery: every submission in the mailbox must be in the ledger, or in
flight (unread and younger than sixty minutes), or older than the baseline — the date of the earliest
ledger id still present in the mailbox. Anything else is printed by id and date as `ПОТЕРЯ`. A
missing token, a missing ledger, or a ledger with no id that still exists in the mailbox exits 2:
"cannot check" is not "clean".

**Controls, because a gate that has never failed is a guess.** A fake `jobs.json` with the job
paused, a 120-minute interval, `no_agent` false and a three-day-old failed run turns five checks red;
the same sweep on a home without `jobs.json` runs 1882 checks and passes with the SKIP visible; a
ledger that has forgotten the six pre-ledger submissions prints six losses and exits 1; an empty
ledger exits 2. Sweep went from 1881 to 1887 checks, all passing.

**What it cannot prove.** That a human opened the letter — the ledger proves the notification was
sent, not that it was read; only the owner's word does that. That Web3Forms keeps the sender domain
`notify+<id>@web3forms.com`; if it changes, the canary's own search goes empty and the first line it
prints is "not found", which is the alarm, not a proof of health. That a letter already in spam will
be rescued: the canary reports it, nobody moves it. And the sixty-minute in-flight window is a
choice, not a law — a letter that arrives while the scheduler is paused will be called lost, which is
the safe direction to be wrong in.

## The page was right about itself and silent about its sources (23.10.2026)

**What was found.** The sweep had two ways to notice a stale page, and both read the page. It
checked that the shipped HTML is internally consistent (prices, subject list, keys, addresses, md
twins, `llms.txt`), and it compared each page's sha256 with the `tools/lastmod.json` ledger, so a
hand-edited `index.html` could not hide. Neither question is "is this file what the sources
produce". A build that was never run leaves the previous page in place: internally consistent, its
sha still matching the ledger, every gate green — and the site saying what the dictionaries no
longer say. The wrong direction is the likelier one, because the sources are what people edit: one
line in `src/locales/*.json`, a price in `prices.json`, a block in `index-src.html`, committed with
the rebuild forgotten. The build bakes those sources into nine pages, nine markdown twins, two
legal twins, `404.html`, `sitemap.xml`, `llms.txt` and the ledger — twenty-four of the files a
visitor or a crawler ever sees. Two copies of one truth is a failure this site has already paid
for twice: the JavaScript `I18N` dictionary that drifted to "5 free breakdowns", and the site
address that lived in three places.

**What changed.** `tools/build.py` now renders the whole site into memory, into one dictionary of
the 24 files it owns, and `--check` compares that dictionary with the disk byte for byte, printing
the first differing line and exiting 1; it writes nothing — the run leaves `git status` empty,
which is how it was proved. Two functions had to stop writing to allow it: the legal-page address
normalisation returns its texts instead of rewriting `privacy.html` / `terms.html` / `robots.txt`
in the middle of the build, and the post-build address audit now accepts the in-memory pages, so
`--check` audits what the build *would* ship rather than what is already there. Default behaviour
is unchanged: a plain `python3 tools/build.py` writes the same files with the same report.

**The gate, and the gate over the gate.** The sweep runs `--check` and gained two checks (1887 →
1889). The second one exists because a comparison can pass over an empty list: the build must also
say how many files it compared, and the number must be at least 24. When `--check` honestly fails
it prints no count, so the count check stays silent then — one defect, one red line, not two.

**Controls, each restored byte-exact and verified with `sha256sum -c`.** `hero.chip3` edited in
`src/locales/en.json` and not rebuilt — `--check` exits 1 naming `index.html` line 336
(«9 languages» on disk, «9 languages now» in the build) and the ledger's sha; the same edit run
through the sweep fails exactly one check. A line appended to the built `index.html` — caught as
size and line count. `ru/index.html.md` moved away — `НЕТ ФАЙЛА`. A date changed in
`tools/lastmod.json` — `sitemap.xml` line 5. And the count guard proved separately: with
`--check` edited to print a count-less `СВЕРКА ПРОЙДЕНА`, the sweep fails the second check alone.

**Checked after the change.** Full build: tree unchanged. Sweep 1889 / 0. Live parity on Pages
re-run: 26 published files byte-identical (`landing-live-bytes.py`), external links 0 problems.
Both mirrors at the same commit.

**What it cannot prove.** That the committed state is the deployed one — Pages publishes
separately, and `landing-live-bytes.py` is the gate for that, not this one. That the sources
themselves are right: it proves the site is what the dictionaries say, not that the dictionaries
say the truth. That the next block remembers to run the sweep: this is a checker, not a git hook,
and a commit that skips it turns the next run red instead of blocking the push. And that the build
is deterministic on a different Python: file order comes from explicit lists and the ledger from
`json.dumps(sort_keys=True)`, but no test pins the interpreter version.

## The shop window had no light, and every gate was reading the shop (23.10.2026)

**What was found.** Nine pages, and on each of them the one action that matters — a link to
`@UchiSamBot`, tagged `src_landing`, `_band`, `_shots`, `_sticky`, `_404`. The sweep had plenty to
say about those links: the tag, the label, the `rel`, the target. It had already learned to compare
the privacy promise with the bot's `.env` and with the unit file, and that no third-party AI host
appears in the bot's code. What none of it asked is whether the thing behind the link is running.
`study-bot.service` could be stopped, crash-looped, or never come back from a reboot, and the sweep
would print 1889 green checks over a shop with the lights off. The class is the one this site has
already paid for twice: the promise compared with a text, never with the live mechanism — the cron
behind "we read every message" (22.10), the queue that answered nothing for sixteen minutes (22.10),
and now the process behind the button.

**What changed.** Four checks in `landing-sweep.py`, all deterministic, none of them spending GPU
time: the user unit is `active`/`running`; its `MainPID` exists as a process; the `LLM_BASE_URL` of
that **running process** — read from `/proc/<pid>/environ`, not from the `.env` that can be edited
and left un-restarted — resolves to loopback or a private address; and the model endpoint behind it
answers `GET /models`. The last one is a probe, not a generation: measured while an 823-token answer
was being generated at 27 t/s, `/models` still returned in 0.01 s, so a busy queue cannot turn the
gate red. Eight seconds is the ceiling for a wedged queue, and red there is the defect. Values are
never printed — only scheme and host, the same discipline as the `claim↔infra` block. One defect
still means one red line: when the service is not running, the three dependent checks are not
executed at all, so a stopped bot prints one failure and the count drops to 1890 instead of four.

**Controls, run from byte-identical copies of the sweep in the scratch directory.** A unit name
that does not exist — `FAIL promise: the bot behind every button is running | inactive/dead pid=0`,
1890 checks, one red. The expectation flipped to a cloud host — `FAIL … the running bot points at
our own endpoint | scheme=http host=[адрес] from /proc`, which also proves the check reads the
process and not the file. `_svc_state` disabled, as on a clone without systemd — 1890 checks,
0 failed, with a check whose *name* says `SKIP` rather than a green claim it cannot support. The
probe pointed at a closed port — `FAIL … the model behind the bot answers | http://[адрес]:9/v1/models
-> URLError за 0.00 с`. The real sweep then ran three times in a row: 1893 checks, 0 failed, three
times.

**Checked after the change.** `tools/build.py --check`: 24 files identical to a fresh build, so the
site itself did not move. Live parity on Pages: 26 published files byte-identical, the 404 probe
still serving our own page. External links: 12 targets, 0 problems, including the four `t.me` tags.

**What it cannot prove.** That the bot's *answers* are any good — `/models` proves the door is open,
not the quality of the breakdown; that Telegram itself still delivers updates (the `t.me` link check
covers a banned bot, this gate does not); that the service stays up between runs — this is a
watchman, not a supervisor; and nothing at all on a host without a local model and without systemd,
where all four checks announce themselves as `SKIP`.

## The letter was announced once, and nobody asked whether it was answered (23.10.2026)

**What was found.** The form says "we will reply to your email"; the eleventh answer in the
FAQ says "we read every message". The mechanism was one cron: every ten minutes it looks for
a new enquiry, sends the owner a single Telegram message, marks the letter read, and writes
its id into the state file's `seen` list. After that, silence. Delivery was watched from five
sides — the form posts, the mailbox receives, the marker matches, the canary fires when the
box goes quiet — and not one check asked the only question the page actually promises:
*was it answered?* A message that arrives at midnight can be missed, and nothing in the system
would ever mention that letter again. The class is the one this repository keeps paying for:
the promise is compared with the notification, never with the outcome.

**What changed.** `contact-inbox-check.py` now keeps a `pending` list. An announced letter
enters it with its address and the letter's own date; twenty-four hours without a reply and the
digest carries a reminder, then one a day, three in total, after which the letter is left alone
and stays in the mailbox. "Answered" is not a guess: `gmail search 'in:sent to:"<address>"'`
in the same kerio mailbox, and only messages dated not earlier than the enquiry — an older
correspondence with the same person is not an answer. There are three verdicts, not two:
*yes* takes the letter off the chase, *no* raises the reminder, and *could not check* (expired
token, no network, unparsable reply) says so in words, leaves the counter alone, and keeps the
letter pending; guessing is forbidden in both directions. A failure in the chase does not
muffle the channel — new letters are still announced in that same tick. Reminders ride in one
digest message rather than one message per letter (owner, 21.10), at most five answer-checks
per tick to spare the Gmail quota, at most fifty letters remembered.

**The regression harness was eight scenarios; it is seventeen.** A fake mailbox, no network:
reminder one, reminder two, silence after the third, "the reply went out" clearing the letter,
old correspondence not counting as a reply, a broken answer-check staying honest and not
swallowing the new letter announced in the same tick, a fresh letter not being chased, the
announced letter landing in `pending` with its address and date, and an unreadable address
getting one warning and then silence. `python3 contact-inbox-regress.py` → exit 0, 35 checks
green, 0 failed.

**Controls.** Two mutations of the production script, each a refusal the harness had to catch.
With `CHASE_AFTER_H = 1000000` — the chase switched off — 12 checks go red, including both
reminders and the clearing by reply. With the found sent-message no longer counting as an
answer — the eyes blinded — 2 go red, exactly the two that describe the reply. So the harness
bites on "switched off" and on "blind", not merely on a missing word. A third control checked
the wiring rather than the behaviour: with the harness's last line replaced by `sys.exit(1)`
while it still printed `ИТОГ: ВСЁ ЧИСТО`, the sweep printed `FAIL … | ИТОГ: ВСЁ ЧИСТО` — a gate
that matched the words of a green run would have passed a failing harness, which is exactly
this morning's validator mistake; the check reads the exit code. Then, against the real
mailbox and read-only: an address the mailbox wrote to a year ago answers *yes*, the same
address with a thirty-day cutoff answers *no* (every letter is older than the cutoff), an
address that never existed answers *no*; and a dry run of the cron itself on a copy of the
state file exits 0, prints nothing (no new letters), and migrates the state to the new schema.

**In the sweep.** One new check, `promise: an enquiry nobody answered is chased`, runs the
harness and requires exit 0 — behaviour, not the presence of words, which is the lesson of the
validator that stayed green for five hours while returning an error. On a clone without the
harness the check announces itself as `SKIP` rather than passing silently. 1893 → 1894 checks,
0 failed.

**What it cannot prove.** That the owner will reply — the chase makes silence visible, it does
not answer for a person; that the reply left from this mailbox — an answer sent from another
account or a phone is invisible, and the letter will be chased three times (noise, not loss);
that the reminder is instant — it rides the ten-minute tick; that a letter written after the
third reminder will be noticed — it will not; that only real enquiries arrive — a spam letter
gets its three reminders too.
