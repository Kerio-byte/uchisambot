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
- `tools/page-text.py` — flattens a built page into the text a visitor can read, one block per
  line, so it can be read as an article rather than as markup (added 23.10.2026 for the meaning
  pass, rewritten 24.10.2026 on `HTMLParser`: entities decoded, `hidden`/`.sr-only`/`.hp` subtrees
  skipped, a line ends where a block ends); read-only, not part of the build:
  `python3 tools/page-text.py ru/index.html`. Its output is what five sweep checks read.
- `tools/publish-tree.py` — the one list of what counts as the site (109 files), and `--check`
  for it: every listed file exists, no page links into the workshop, every internal reference
  points at a listed file. Added 23.10.2026 after the measurement that GitHub Pages was serving
  154 files — `/README.md` included. `--verify-served DIR` serves a staged tree and asks for every
  address (83 of them) to prove a switch of the publish source would not break anything.
- `tools/publish-branch.sh` — stages that list into the `gh-pages` branch (or checks it with
  `--dry-run`), pushes it to every mirror, and then reads the Pages setting back. Since 24 Oct 2026
  GitHub Pages serves this site **from `gh-pages` /(root)**, not from `main` / — so the workshop
  (this notebook, the generator, the dictionaries, the proof frames) is no longer reachable at
  `/README.md`, `/tools/…`. The switch was one API call, recorded in the script's header; the price
  is that **page edits reach the world only through this script** — a push to `main` no longer moves
  the site, and two sweep checks ("публикация: …") fail when the live site lags the tree or starts
  serving the workshop again.
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
- `tools/answer-time.json` — the number the page gives for waiting (23.10.2026). `claims` holds
  what all nine pages say (the range `5–60`, the 120-second ceiling and the ceiling phrase in each
  language); `sessions` holds what was measured on the production path — date, model, GPU queue
  state before and after, every task's seconds — written by `landing-answer-time.py`
  (`stars-bots-ops` skill), never by hand. The sweep ties the nine `q8a` answers to `claims` and
  fails when any recorded session exceeds the ceiling, when one of the two kinds of session (idle,
  busy) is missing, or when the newest is older than thirty days (see "The page counted seconds on
  a card it never looked at" below).
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
  "Chat shots" below. All nine languages are drawn by it (EN and RU were frozen
  captures until 23.10.2026, when the bot's seventh menu button had to reach
  them). The keyboard is not a list in the generator: `tools/shots-gen/bot_menu.py`
  reads `menu_kb()` from `bot/handlers.py`, and `tools/shots.json` is the ledger
  (sha256 of every webp + the exact strings drawn, written by `--apply --stamp`),
  which the QA sweep checks against the bot's own texts.
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
  the ledger: the strings actually baked, plus sha256 of each loop, its poster,
  each full demo, and (since 24 Oct 2026) of the two page screenshots each loop is
  cut from. `demo/build-web-loop-langs.sh [lang …]` and
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
   then publish the site tree to the `gh-pages` branch — GitHub Pages serves the
   site from `gh-pages` /(root) since 24 Oct 2026, so a push to `main` alone no
   longer changes what visitors see: `bash tools/publish-branch.sh` stages the
   publish list (`tools/publish-tree.py`), pushes it to every mirror and reads the
   Pages setting back.

Reproducible build: `tools/build.py` is deterministic — a second run on unchanged
sources leaves the worktree clean. `sitemap.xml`’s `<lastmod>` comes from a content
ledger, `tools/lastmod.json` (`{url: {sha, date}}`, sha256 of the page bytes): a date
only moves when that page’s content actually changes, so a plain rebuild no longer
rewrites all eleven dates to the build day and the date never claims an edit that did
not happen. Commit `tools/lastmod.json` with the generated pages; the QA sweep
re-hashes every page and fails when the ledger is stale (page edited without a
rebuild, or sitemap date ≠ ledger date).

Hero video (per-language loops): every language page plays its OWN 13 s loop with the
two step captions in the page language — `demo/uchiambot-demo-web.mp4` (EN) and
`demo/uchiambot-demo-web-<lang>.mp4` for the other eight (RU rebuilt; the
seven es/pt/hi/id/tr/vi/uk loops added 17 Oct 2026), poster `img/demo-poster[-<lang>].webp`
(last frame of the loop). Captions are the site dictionary terms (`how.s2t` /
`shot3.alt` core), e.g. RU `2 · Отправь задачу — текстом или фото` / `3 · Пошаговый
разбор`, ES `2 · Envía tu tarea — texto o foto` / `3 · Desglose paso a paso`. RU:
rebuild with `demo/build-web-loop-ru.sh`; any language (and its poster):
`demo/build-web-loop-langs.sh [lang …]` — same zoompan/drawtext pipeline as the
kit build (13.0 s, 720×1560, x264 veryslow crf30; poster = frame 389 → 540×1170
WebP). **Sources are the page's own screenshots** (24 Oct 2026): `img/shot2[-<lang>].webp`
and `img/shot3[-<lang>].webp` — the exact files the page displays, so a loop cannot
show a bot the page does not show; rebuilding needs no render run and no external
catalogue. Two deliberate render notes: the hi loop uses Noto Sans Devanagari Bold,
whose glyph set has no `·` (U+00B7), so its step separator is `.`; drawtext
`text_shaping` (on by default) shapes the Devanagari conjuncts. Every caption line
comes from `demo/captions.py` (see Structure); a rebuild refreshes the language's
poster and re-stamps `demo/captions.json` (loop bytes, poster bytes, **and the sha256
of both source screenshots**), and the sweep fails if you forget either — a redrawn
screenshot with an old loop is red, not silent. The full 35 s demos are rebuilt the
same way (`bash demo/build-full-demo.sh en|ru`): their scenes 1–3 are those same page
screenshots, and scene 4 (the language switch) is drawn by the shots generator into
`tools/shots-gen/scenes/shot4[-ru].webp` from the bot's own `LANG_TITLES` — nine rows, the
same list the bot answers with.

> УСТАРЕВШЕЕ (до 24.10.2026, блок g): «scene 4 (the language switch) has no page equivalent
> and still comes from `submission-kit-20261014`» — на той картинке было два языка
> («Русский / English») при девяти в боте. Кадр переехал в генератор, каталог больше не
> участвует; список публикации остался 109 файлов, потому что `scenes/` страница не
> показывает (см. раздел «Кадр 4 полного демо» в журнале).

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

CTA tags (23.10.2026): every label is built from the page's own language code —
`?start=src_landing_<code>` for the hero button, `..._band` for the closing band,
`..._sticky` for the sticky bar, `..._shots` for the button after the screenshots
(`en` → `src_landing_en`, `/hi/` → `src_landing_hi_band`). The bot records the first
touch per user, accepts any `src_*` payload, and reads the code back: a visitor who
arrives from `/hi/` is greeted in Hindi even if their Telegram interface is in another
language. The 404 page keeps its single language-neutral `src_landing_404`. The sweep
pins all four per page (4 × 9 = 36 labels, none foreign), and
`landing-page-lang.py` checks the page side and the bot side together.

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
(the bot's own i18n module — single source of truth; the mockup-only canned lines —
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
`tools/build.py`. The page keeps its four landing tags, each with the page's own
language code (23.10.2026: `src_landing_<code>`, `..._band`, `..._sticky`,
`..._shots`); the AI layer is a separate channel, and
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
directive as the last prompt line) and the bot's own service was restarted with it;
measured through the same local queue afterwards — hi/es/uk/tr/vi answer in their
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
the bot service restarted, which cron is not allowed to do.

**Product reachability.** At the same hour the bot's endpoint
(our own loopback queue, with the local inference server behind it) answered
nothing at all: five requests between 02:41 and 02:57,
waits of 15 to 130 seconds, not one byte back, while the model itself
answered the same request in 1.2 s. The bot has no second provider, so a
visitor waits out `LLM_TIMEOUT=120` and gets an error. One command restores it
(one restart on the host, `Restart=always`); cron is barred
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
a task. That promise lives in the bot's config, not in `src/locales/`: point the model endpoint setting at a
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
`LLM_BASE_URL` → a private LAN address (0 fails — a box on our own LAN is still "our infrastructure", and a
gate that cries wolf gets switched off); "not sent to third-party AI services" → "handled with
care" in `privacy.html` (1 fail, plus the `lastmod` sha check, which watches every page edit); the
Russian training sentence softened in `privacy.html.md` (1 fail). After every restore: sha256
equal, `git status` clean, sweep 1674/0.

**Where the promise stands today**, measured rather than assumed: `LLM_PROVIDER=local`,
`LLM_BASE_URL` = the loopback queue, which routes two ports on this box —
no third-party host in the bot code, and a chat probe through that same queue answered
("работает") — the endpoint the page promises is the endpoint that answers.

**What the gate cannot prove**, and why the wording does not need it to: "our own infrastructure"
is a statement about ownership, not geography — a private IP on a rented cloud VM would pass. The
gate catches the realistic failure (someone switches the provider to a cloud API and forgets the
page), not every possible lie.

## The screenshots ended and there was nothing to press (22.10.2026)

Round 2 of the landing board (15 Oct, its room folder lives outside this repo) agreed on six
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
kept in the inbox cron's own state file (outside this repo), so UNREAD is a convenience again instead of the
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
messages" twenty-four times an hour and never fails. The job scheduler reports a task that errors; it does not
report a job that is gone from `jobs.json` — a file this machine has already had to rebuild once
(a `.corrupt-20260916` copy sits next to it). Nothing in the page's battery reads that file.

**What the mailbox actually holds.** The live audit finds nine letters from Web3Forms: seven form
submissions (15.10, four on 21.10, two on 22.10) and two service letters (the welcome message and
the verification code). The cron's ledger — the same state file — knows one of
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
that has no scheduler job file — a clone, another host — it prints one check whose name says
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
the bot service could be stopped, crash-looped, or never come back from a reboot, and the sweep
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
probe pointed at a closed port — `FAIL … the model behind the bot answers | http://<loopback>:<closed port>/v1/models
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

## The page promised the last step would be the student's; on a photo the bot took it (23.10.2026)

**What was found.** All nine FAQ pages say the bot "stops one step before the answer so you
finish it yourself", and a feature card adds "Not just answers". Nothing measured it. The only
test that goes near the photo path (`tests/smoke.py`, section 9) feeds a fake JPEG — four bytes
of a JPEG header — to a mock provider and asserts that the answer contains the word "фото"; it
cannot fail for the reason the page cares about and never touches a model. Sent through the
production path instead (`build_prompt` plus the bot's own provider — the code a student's
message takes), thirteen tasks — seven typed, six photographs of a textbook page — the typed
path kept the rule seven times out of seven, and the photo path broke it once in five answers:
"Решите уравнение: x/3 + 4 = 9" came back ending "Получаем: x = 15". The sixth photo never came
back at all: at 120.2 seconds the bot's own timeout turned it into "the service is overloaded".

**The rule now ends the answer.** A prohibition alone did not hold on the fractional equation:
with "do not name the final answer" added as the last instruction before the language line, the
model still wrote the value — in one of seven typed tasks and one of six photos. What holds is a
required shape: the last line of a breakdown is a question to the student, with no equals sign.
Six runs of the same fractional task — three typed, three photographed — all ended "умножь сам —
что у тебя получилось?" and stopped at "x = 5 * 3". The instruction sits last but one, before
the language line, in the position that proved itself for the answer-language rule on 22.10,
and only for task types 2 and 3; type 1 explains a topic and gets no such line.

**A mechanism, not hope.** The prompt is a request; the retry is the mechanism.
`names_final_answer()` looks for a ready value — a lone variable and a finished number
(`x = 15`) — and deliberately not for a coefficient (`3x = 21`) or an expression (`x = 5 * 3`).
When it finds one, `generate_breakdown()` regenerates the breakdown once with a corrective
instruction. If the second attempt fails too, the first answer is sent: a breakdown that names
the answer is a flaw, an error message is a lost student. Both calls live in one function so the
live battery exercises exactly what a student gets, not a copy of it.

**Numbers.** Typed path, before the change: 7 tasks, 7 clean, 6.7–40.5 s. Photo path, before:
6 tasks, 5 answered, 1 of those named the answer, 1 died at the 120 s timeout, 34.7–78.8 s.
With the hard rule alone: 13 tasks, 2 violations (both the fractional equation, typed and
photo). With the required ending: 13 tasks, 1 violation (the same photo), and the weak case
repeated seven times — six on that exact equation plus one control — came back clean every
time. With the retry, measured while another tenant held the GPU: 13 tasks, 11 clean; one
photo was answered with the value because its retry timed out, one photo timed out before any
answer. The typed path was 7/7 throughout.

**One more thing the measurement found.** `solve_task` gave photo breakdowns forty-five extra
seconds (`wait_for`), but the provider carried its own 120-second limit and cut the request
first: the timeout landed at exactly 121.0 s while the outer budget was 165. The provider is
now built with `LLM_TIMEOUT + 60`, so the outer, per-type budget is the one that governs.

**In the sweep.** One new check, `prompt contract: the last step is left to the student`: it
runs the bot's own `build_prompt` through the bot's virtualenv for all nine languages and three
task types and requires the rule to be the last instruction before the language line for types
2 and 3 — and absent for type 1. 1894 → 1895 checks, 0 failed. A negative control (the rule
removed from the builder) turns it red — `FAILED: 1` — while the rest of the sweep stays green.
The behavioural proof is the live battery `landing-stop-rule.py` (13 tasks, 10–60 seconds
each); it needs the GPU, so it stays out of the sweep and runs per block.

**What it cannot prove.** That every formulation ends well — thirteen tasks are a sample, and
the failing case was found by reading output, not by a gate; that the retry always repairs a
violated answer — it is one attempt, and the first answer is kept when it fails; that the
detector is exact — a word problem writing "x = 5 apples" triggers an unnecessary retry (cost,
not harm); that the model's arithmetic is right; that the answer arrives inside the promised
minute.

**Left open: the minute the page promises.** The same photo tasks took 35–120 s during this
block and 10–16 s an hour later. The model is not the reason: the inference server reported 2.5 s of
work (1,323 prompt tokens at 650 tokens/s, 17 tokens out at 35 tokens/s) for a request that
took 50.7 s end to end; the rest was spent waiting in the single-slot GPU queue behind another
tenant (a shared agent service, 40,000–60,000-token prompts). While that queue is shared,
"usually in 10–60 seconds" is true on an idle GPU and false on a busy one, and a photo task can
reach the timeout — the student then reads "service overloaded". A priority lane for the bot,
or moving agent traffic off this GPU, changes shared infrastructure: it is the owner's call,
not a silent change in a cron block.

**State.** The fix is committed and tested (31 unit tests, the smoke run, the live battery); the
running process still executes the previous code until the service is restarted, and cron blocks
service restarts by policy — that one command belongs to the owner.

## The page counted seconds on a card it never looked at (23.10.2026)

**What was found.** The previous block ended with an open item: "the answer arrives inside the
promised minute" could not be proven. The promise itself was the reason. All nine pages answer
"how long does a breakdown take?" with one number — **10–60 seconds** — and nothing measured it:
no gate, no ledger, no test. Two measurements of the *same* production path (`generate_breakdown`
plus the bot's provider, the code a student's message takes) disagree with it in both directions.
On an idle card, three typed tasks and three photographs of a textbook page came back in 4.6–17.8 s
and 7.8–23.8 s — the page over-promised the floor by a factor of two. With the card shared
(agent crons through the shared service, the previous block's numbers), photographs took 34.7–78.8 s and one
task died at the 120 s timeout — the page under-promised the ceiling by more than a minute. A
number that is wrong both ways is a guess, and the student who sends a photo is the one who
measures it.

**What changed.** `q8a` in all nine dictionaries now names the measured range and the ceiling:
*5–60 seconds*, and *"if the server is busy, it can take up to two minutes"*. The bot's own
"⏳ working on it" line says the same thing in nine languages (`bot/i18n.py`, `bot/i18n_extra.py`)
— that line is what a student reads while waiting, so it was the other half of the same promise;
it deploys with the restart the previous block left for the owner.

**The number now has an owner.** `tools/answer-time.json` is a ledger in the same shape as
`prices.json`, `subjects.json` and `demo/captions.json`: `claims` — what the page says (the range,
the 120-second ceiling, and the ceiling phrase per language, because a check across nine languages
cannot match a Russian sentence against an English one); `sessions` — what was measured: date,
model, queue state before and after, and every task's seconds. `landing-answer-time.py` (in the
`stars-bots-ops` skill) runs the production path, appends a session with `--write`, and exits 1
when a task fails or the slowest one exceeds the ceiling. `--contend N` starts N filler generations
in the same queue first, so "a busy server" is reproducible instead of remembered.

**In the sweep.** Thirteen new checks (1,895 → 1,908, 0 failed): the ledger must name a range and a
ceiling that agree with each other; each of the nine `q8a` must contain both the range string and
its own language's ceiling phrase; no recorded session may exceed the ceiling or carry a
violation; there must be at least one idle session and one busy one; the newest session may not be
older than thirty days — a stale measurement is a claim nobody checked, and the sweep says so
instead of letting the number age quietly.

**Numbers.** Idle session (16:23, GPU 0 at 0 %, 20,284 MiB resident): typed `n=3` 4.6/6.7/17.8 s
(p50 6.7), photo `n=3` 7.8/11.3/23.8 s (p50 11.3), no errors. Contended session (16:29, two
600-token fillers fired into the same endpoint first): the first typed task waited **41.5 s**
behind them, the rest ran 6.6–12.9 s; `busy: true` is recorded with the queue state, not with a
feeling. The page's ceiling, 120 s, is deliberately below the bot's own hard photo budget
(`LLM_TIMEOUT` 120 + 45 = 165 s): the ledger fails the sweep at 120 because past two minutes the
page is already wrong, whatever the system is still willing to wait for.

**Controls, each restored byte-exact (`sha256sum -c`).** (1) `ru.json` edited back to "10–60" —
two red lines, `[ru] время разбора` and the older `translated numbers == EN` — plus `[build]`,
because the source was not rebuilt; that is the old gate doing its job. (2) A session's `text.max`
set to 150 — `ни один замер не вышел за потолок страницы`, naming the date and `150.0 > 120`.
(3) Both sessions marked `busy: false` — `есть замер и на свободной, и на занятой карте` names
"сессий 2, из них под нагрузкой 0". Every other check stayed green through all three.

**Checked after the change.** Sweep 1,908 / 0. The FAQ answer — the longest line on the page — at
420 px in RU, HI and EN: opened on its own (the language menu is a `<details>` too, and opening
every `<details>` on the page screenshots the menu over the text — the first attempt did exactly
that), the answer is 378 px wide inside a 420 px viewport, no horizontal scroll, no clipping, the
new sentence wraps by words. `landing-render-check.py`, the a11y battery (124 checks) and the
viewport battery (94 checks) re-run green; the bot's 31 unit tests pass with the new `processing`
strings.

**What it cannot prove.** That the GPU queue behaves tomorrow as it did at 16:23 and 16:29 — the
session records the queue state precisely because the number is a property of the card, not of the
page; that three plus three tasks are a distribution rather than a sample; that 120 s covers every
load — the hard budget is 165 s, and past it the student gets the "try again in a few minutes"
answer that `q9a` already describes; that the model's arithmetic is right (other batteries); and
that the running bot already says the new sentence — it does not, until the service is restarted.

## The page knew the visitor's language; the bot never heard it (23.10.2026)

**What was found.** Two defects with one root: the landing speaks nine languages, the bot chose its
first screen from the Telegram interface language only, and nothing carried the page's language
across the boundary.

1. All nine pages sent the same labels (`?start=src_landing`, `_band`, `_shots`, `_sticky`). The bot
   computed `lang` as the Telegram language code, falling back to `default_lang` — `ru`. A visitor
   reading `/hi/` with Telegram in Finnish or English was greeted in Russian or English, and had to
   find `/lang` before he could read anything. Meanwhile `q3a` in all nine dictionaries promises
   "nine languages... switch any time with `/lang`" — the page sells a choice the first screen
   ignores.
2. The choice was not merely ignored, it was overwritten. `storage.ensure_user()` updates `lang`
   whenever a value is passed in, and `cmd_start` passed the Telegram-derived value into `_track()`
   on every `/start`. A student who had picked Spanish with `/lang` and whose Telegram is in English
   was silently moved back to English the next time he pressed Start. Measured, not reasoned: a
   seeded user with `lang="es"` and Telegram `en` came out of `cmd_start` with `en` in the database.

**What changed.** `tools/build.py` writes the page's own code into all four CTA labels — 36 labels,
four per page (`src_landing_<code>`, `..._band`, `..._shots`, `..._sticky`); the 404 page keeps its
single neutral `src_landing_404`. The bot reads the code back through `landing_lang()`
(`bot/handlers.py`): a **new** user gets the language of the page he came from — it beats the
Telegram interface, because it is the language he was just reading; a **returning** user gets the
language he saved with `/lang` — neither Telegram nor the label may overwrite it. The first touch is
still recorded once per user, so `source` now reads `landing_hi_band` instead of `landing`, and
`scripts/source_stats.py` groups the report by page language and by button position (the script
takes `--db` so the report can be tested without the live database). Before this, all nine
languages collapsed into one row: "which language page brings people" had no answer in the data,
only in opinion.

**In the sweep.** Ten new checks (1,908 → 1,918): each page must carry exactly four labels, all with
its own code and none foreign — the three older checks that pinned `src_landing_sticky`, `_band` and
`_shots` now expect the language — plus one global check that runs `landing-page-lang.py` over both
sides at once: the 36 labels on disk and `bot.handlers.landing_lang` over all nine codes and over
the old or foreign labels (`src_landing`, `src_landing_404`, `src_llms`, `src_landing_zz` → `None`).
The bot's tests grew 31 → 39: the new user's greeting, both fallbacks, the returning user's saved
choice, the label never rewriting it, and the report grouping.

**Controls, each restored byte-exact (`sha256sum -c`).** (1) The old language rule put back into
`cmd_start`: three tests red with the exact difference — a `/hi/` visitor stored as `en`, a
returning `es` user moved to `en`, a page label rewriting a stored `ru` to `vi`; the other five
stayed green. (2) One page's hero label reverted to the bare `src_landing`: five red lines, naming
the page and the label list (`[hi] cta labels carry the page language`), the band check, the
`lastmod`/sha guard, the new global battery and the build comparison — a hand-edited page cannot
pass as a built one. (3) The same page break through `landing-page-lang.py` alone:
`FAIL hi: метки ['src_landing', 'src_landing_hi_band', ...]`.

**Checked after the change.** Sweep 1,918 / 0; the link audit 0 problems over 11 pages, listing the
new labels; `landing-render-check.py` ALL OK with no JS errors; the bot's 39 tests pass. Nothing
visible changed on the page — only query strings — so no new screenshots were needed.

**What it cannot prove.** That anyone has arrived from each page yet: the bot's database holds four
accounts and none of them tagged; the grouped report will have rows only when a real visitor comes
from a page. That links already shared with the old bare label change behaviour — they do not: the
old label maps to `None` and the bot falls back to Telegram exactly as before, so the change is
forward-only. And that the running bot already greets in the page language: it does not, until the
service is restarted — the same standing item the previous two blocks left for the owner.

## The price screen asked the buyer to fill in the blanks (23.10.2026)

**What was found.** Three defects, one root: the words about money were typed by hand and no test
ever rendered the screen a person sees.

1. The path from the menu to paying (`plans:buy`) called `t(lang, "plan_info")` **without the
   values**. Formatting raised, `t()` returned the template unchanged, and a buyer in all nine
   languages read `1️⃣ One breakdown — {single} ⭐️ ({single_tasks} task)`. A correct renderer,
   `plans_text()`, sat three functions above and was used only by the other branch.
2. The invitation in all nine dictionaries promised the friend **five** free breakdowns while
   `FREE_TRIALS` is 2 — and every language page on this site says two.
3. The plan labels lived as two strings, `title_ru` / `title_en`, so seven languages saw an
   English name in the plan button and in the **Telegram invoice itself**, on the screen where
   the decision to pay is made. The price screen also carried a hand-typed dollar estimate
   (`30 stars ≈ $0.4–0.6`) and hand-typed discount percentages.

**What changed.** `handlers.plans_text()` is the single renderer, at module level: prices come
from `payments.PLANS`, and both discount percentages are **computed** from those prices (20 and 33
are arithmetic now, not text). The `plans:buy` branch sends one screen with three buttons instead
of three copies of a raw template. `i18n.PLAN_TITLES` holds the three plan names in nine languages
with `plan_title(lang, plan_id)`, used by both the button and the invoice title (Telegram's
32-character limit is asserted); the `title_ru`/`title_en` fields are gone from `payments.Plan`.
The friend's free tier is a `{free}` placeholder filled with `FREE_TRIALS`, and the Russian and
Ukrainian sentences were rewritten so no grammatical case is bound to the number. `t()` no longer
stays silent: a missing substitution is logged as a warning — that silence is exactly what hid
this defect for three blocks.

**In the sweep.** One check (1,918 → 1,919) runs `landing-bot-money.py`, a new battery that
renders the three money screens with the bot's own code in all nine languages: no raw
placeholders, the real prices and computed discounts, the real free tier with no stray "5", plan
titles present and within the invoice limit, no English title outside English, and an AST guard
that forbids `t(…, "plan_info")` without arguments and any return of `title_ru`/`title_en`. The
bot's own suite grew 39 → 97: `tests/test_money_screens.py` (58 checks) plus the old pricing test
rewritten to render through `plans_text()` instead of assembling the arguments by hand — which is
why it had stayed green while the screen was broken.

**Controls, each restored byte-exact (`sha256sum -c`).** (1) The argument-less call put back into
`plans:buy`: the battery prints `FAIL handlers.py: t(lang, 'plan_info') без подстановок` and the
AST guard test turns red, 96 others green. (2) A "5" put back into the Spanish invitation: two
battery lines naming `es`, two red tests. (3) The Turkish 5-pack label replaced with the English
one: `FAIL tr/pack5: английское название тарифа`, one red test.

**Checked after the change.** Bot tests 97 passed; `landing-bot-money.py` ALL OK (9 languages, no
placeholders, prices 30/120/300, discounts 20 %/33 %, `FREE_TRIALS` 2); the sweep 1,919 / 0; the
price parity 9 checks / 0 mismatches; and the three screens printed for all nine languages and
read as an article — the numbers are there, the braces are not.

**What it cannot prove.** That the live bot already speaks this way: the service has been running
since 22 Oct and still serves the old code — restarting it from a cron run is refused by the
approval policy, so the one command stays with the owner. And that anyone will pay: the database
holds four accounts and no purchase; the money screen has only stopped lying.

## The phones on the page were 45% thinner than the files (23.10.2026)

**What was found.** The three chat mockups in "Real chats with the bot" — the section that exists
to show the product is real — were drawn with a **fixed height and a squeezed width** on all nine
language pages, at every screen size. Each file is a phone screen, 1080×2340 (ratio 0.462). On the
page it was drawn at:

| viewport | box | ratio | deviation |
|---|---|---|---|
| 390 mobile | 298×1170 | 0.254 | −45% |
| 1280 desktop, first column | 369×1170 | 0.315 | −32% |
| 1280 desktop, other two | 308×1170 | 0.263 | −43% |

Fifty-four images (3 shots × 9 languages × 2 viewports) were out of proportion. The detail that
makes it a defect rather than a taste: the avatar in the chat header is 89×91 px in the file
(a circle), so on the page it was an ellipse 24.6×45.5 px, and every letter in every bubble was
1.8× taller than wide.

**Why it survived nine days of passes.** The sweep knew two things about these images: that each
`<img>` **has** width/height attributes (a layout-shift guard from 16.10) and that the first shot's
column is wider (`grid-template-columns:1.2fr 1fr 1fr`). Neither compares the box on screen with
the file. And the unequal columns were *only* viable because all three frames were 1170 px tall:
the layout and the distortion propped each other up, so the sweep was asserting the symptom.
Eyes saw "a phone", not "a phone 1.8× too tall" — a narrow phone still looks like a phone.

**The cause in one line.** The stylesheet had `img{max-width:100%;display:block}` and no
`height:auto`. The `width`/`height` *attributes* are CSS presentational hints, not just metadata:
with `width:100%` from CSS and `height:1170px` from the attribute, the browser keeps 1170 px of
height and, since `object-fit` defaults to `fill`, stretches the file into that box. Measured, not
argued: an element screenshot (298×1171) compared with the same webp resampled into the same box
gave a mean channel difference of 7.6/255 — the rendering *is* the stretch.

**What changed.** `height:auto` in the global img rule (`img{max-width:100%;display:block;height:auto}`)
— the attributes still reserve the space, which is why the layout-shift numbers did not move
(CLS ≤ 0.1, `landing-cwv.py` 69/0). `.shots` became `repeat(3,1fr)`: with honest proportions the
1.2fr first column stood 130 px taller than its neighbours and the row read as a staircase, while
the three frames are one and the same 1080×2340 file. After the change: 390 → 298×642,
420 → 323×698, 1280 and 1440 → 328×708, all three equal, ratio 0.463 against the file's 0.462.

**In the sweep and in the battery.** Two static checks (1,919 → 1,928): `shots equal columns` and
`img height auto` — the second one exists because this whole class of defect starts with an img
rule that sets a width and forgets the height. The real measurement moved to where layout lives:
`landing-visual-pass.py` now records, for **every** image on the page, the drawn box against the
file's own proportions and fails above 2% (fractional px tolerance). It runs for all nine languages
at 420 and 1440, so the shots, the badges and the hero badge are all covered.

**Controls.** (1) Negative: `height:auto` removed from a throwaway copy of the tree, rebuilt —
`landing-visual-pass.py` prints 54 problems and exits 1 (`image squashed shot1.webp dev=-40.1%
box=323x1170`); the repo itself was never touched, the copy stays in scratch. (2) The CSS comment
first spelled the tag as `<img>`; the sweep's `img dims all` check matched that literal and went
red — the comment was reworded. Both are reminders the gates read raw text: worth knowing before
writing prose next to markup.

**Checked after the change.** Sweep 1,928 / 0. `landing-visual-pass.py` PROBLEMS 0 (18 page loads,
badges 8/8 on every page, rows 2 mobile / 4 desktop). Links 11 pages / 0 problems; render-check ALL
OK; a11y-extra 124 / 0; viewports-extra 94 / 0; axe 12 pages / 0 violations; wcag22 43 / 0; cwv
69 / 0; cross-engine 60 / 0 (WebKit + Firefox, mobile / desktop / three landscape sizes);
browser smoke 18 / 0. Images out of proportion across the whole site: 54 → **0 of 252**
(9 language pages + privacy + terms + 404, at 390 and 1280), and 0 of 234 **on the live site**
(9 pages × 420 and 1440, after the push).

**What it cannot prove.** That the conversations in those mockups match what the live bot says
today: the service still runs the code it started on 22 Oct, and restarting it from a cron run is
refused by the approval policy — that one command stays with the owner. And that the even row is
the look the owner wants: the first frame no longer dominates; getting the accent back means
cropping the chat text at the sides, which is worse than a flat row, so the flat row is the default
and one word from the owner turns it back.

## The headline said what the product is, and forgot what it does and where it lives (23.10.2026)

**What was found.** `<title>` is the only string a person reads before deciding to click: the browser
tab, the search result, and the **bold first line of a Telegram link preview**. Nine pages carried
nine different headlines, and two of them carried the whole message:

| lang | chars | title |
|---|---|---|
| en | 51 | UchiSamBot — Step-by-Step Homework Help in Telegram |
| ru | 56 | UchiSamBot — разбор домашних заданий по шагам в Telegram |
| es | 47 | UchiSamBot — Ayudante de estudio para escolares |
| pt | 46 | UchiSamBot — Assistente de estudos para alunos |
| hi | 50 | UchiSamBot — स्कूली बच्चों के लिए पढ़ाई में मददगार |
| id | 48 | UchiSamBot — Asisten belajar untuk siswa sekolah |
| tr | 50 | UchiSamBot — okul öğrencileri için ders yardımcısı |
| vi | 40 | UchiSamBot — Trợ lý học tập cho học sinh |
| uk | 45 | UchiSamBot — навчальний помічник для школярів |

Seven of the nine said what the product *is* (a study helper, for school students) and neither what
makes it different (**step by step — not a ready answer**) nor where it lives (**Telegram**). The
description immediately below each of those titles said both correctly: `Bot de Telegram que
desglosa las tareas paso a paso…`, `Telegram बॉट, जो होमवर्क को स्टेप-बाय-स्टेप हल करता है…`. So the
weak line was exactly the one printed largest, and the fine print underneath was doing the selling.

**Why nothing caught it.** Every gate asked whether the title *is there* — `title` (the dictionary
string appears in the page), `og:title`, `twitter:title`, `og:image:alt`, `md twin h1`. All five are
"the same string in five places" checks, and all five passed on a headline that described the
product as a category rather than as a promise. Nothing compared the title with the description
written by the same translator one line below, and nothing knew that "the place where the product
lives" is part of the message.

**What changed.** Seven `meta.title` strings, each built from that language's own words — no new
terms were introduced, every phrase is lifted from the same language's `meta.desc` or `hero.sub`:

| lang | chars | new title |
|---|---|---|
| es | 43 | UchiSamBot — Tareas paso a paso en Telegram |
| pt | 46 | UchiSamBot — Tarefas passo a passo no Telegram |
| hi | 56 | UchiSamBot — होमवर्क का स्टेप-बाय-स्टेप हल, Telegram में |
| id | 48 | UchiSamBot — PR langkah demi langkah di Telegram |
| tr | 47 | UchiSamBot — adım adım ödev çözümü, Telegram'da |
| vi | 51 | UchiSamBot — Bài tập về nhà từng bước trên Telegram |
| uk | 50 | UchiSamBot — домашні завдання покроково в Telegram |

Lengths now 43–56 (were 40–51) — the spread narrowed and nobody exceeds 65 characters.
`tools/build.py` rebuilt 7 pages, 7 markdown twins, `llms.txt` and `tools/lastmod.json`; the diff is
23 files, 63 insertions and 63 deletions, and `--check` confirms disk equals a fresh build. The
preview cards (`img/og-*.png`) were **not** re-rendered on purpose: they are drawn from `foot.tag`
and `f1t/f2t/f5t`, which do not include the title, so `tools/og-cards.lock.json` stayed valid.

**In the sweep (1,928 → 1,973 checks).** Three checks per page — `title names Telegram`, `title
names the brand`, `title <= 65 chars` — plus one global `brand mentions == EN (8 langs)`: the number
of times the product is named must match English for every key. Numbers were already compared
(`translated numbers == EN`); the name was not, so a translator could write "Uchi-бот" or drop the
name from a sentence and every gate stayed green.

**The blind spot next door: glyphs burned into pixels.** Looking for what else nothing checks, the
video captions turned out to be drawn with a font the page never uses — `DejaVuSans-Bold.ttf` for
eight languages, `NotoSansDevanagari-Bold.ttf` for Hindi. FreeType gets one file and renders a
missing character as `.notdef`, an empty box: the mp4 stays valid, the ledger still matches by
sha256, every gate stays green, and the frame shows a rectangle. Nothing asked the font what it can
spell. Today the answer is clean — 0 missing codepoints across all 29 baked strings (18 loop
captions, 11 full-demo lines) — so the defect does not exist; the blind spot did. The sweep now
reads the font's own `cmap` with a stdlib parser (`scripts/font_cmap.py`, formats 4, 6 and 12,
because the sweep has no fontTools and should not grow one), and that parser was cross-checked
against fontTools on both files: the maps agree to the last codepoint (DejaVu 5,935 / 5,935, Noto
Devanagari 272 / 272, zero differences either way).

**Controls.** A throwaway copy of the tree (`scratch/neg-231026a`) with four breaks — the Spanish
title put back to its old wording, `2` turned into `3` in the Vietnamese description, the brand
erased from `id.hero.sub`, and the Devanagari letter `स` appended to an English caption. The sweep on
that copy exits 1 and fails exactly as intended: `title names Telegram` (es), `translated numbers ==
EN` (vi), `brand mentions == EN (id:hero.sub)`, and `burned captions have every glyph | U+0938 'स'
нет в DejaVuSans-Bold.ttf`. To make that possible without touching the live tree, the sweep's root is
now overridable with `LANDING_ROOT`.

**Checked after the change.** Sweep 1,973 / 0. Links 11 pages / 0 problems; render-check ALL OK;
`landing-visual-pass.py` PROBLEMS 0 (18 page loads, 9 languages × 420/1440); cwv 69 / 0; a11y-extra
124 / 0; wcag22 43 / 0; axe 12 pages / 0 violations; cross-engine 60 / 0 (WebKit + Firefox, mobile,
desktop and three landscape sizes); Nu validator: no real findings; external links: 0 problems.

**What it cannot prove.** That these are the headlines the owner wants — the formula is the default
(translation was already even, only the shape of the line changed). That the live bot answers with
the new code: the user-unit for the bot started on 22 Oct 03:13:50, while the commits of
23 Oct (15:38 the last step stays with the student, 16:33 the waiting line, 17:23 the greeting
language, 18:10 the price screen) are not in that process, and restarting a service from a cron run
is refused by the approval policy — one command stays with the owner. And that the 35-second demo
should change: its closing frame says "Works in Russian and English" while the page promises nine
languages. That is an understatement, not a lie, but it is inconsistent; re-cutting two videos is
the owner's call, not a default worth taking.

## The bot showed seven menu buttons; every mockup drew six (23.10.2026)

**What was found.** The screenshot section calls its three chat images "Real screenshots — the bot
works in 9 languages". All nine languages showed the same main keyboard, and it did not exist:

| drawn in all 27 images | bot's `/start` keyboard (`menu_kb()`) |
|---|---|
| Free examples, Break down a problem, Check my solution, Summary & flashcards, Pricing, Help | the same six **plus "Invite a friend"** between Pricing and Help |

`menu_kb()` has carried the seventh button since the bot's first commit (15 Oct 22:33), so the
window was wrong from the day the mockups were installed. It also contradicted the page's own
referral paragraph ("Invite a friend — when they solve their first task, you get one more free
breakdown"): the page advertised a button its own screenshot left out.

**Why nothing caught it.** The generator (`tools/shots-gen/gen_shots.py`) kept the menu as a
hand-written list of six dictionary keys; everything else in a mockup already came from the bot.
The gates asked whether the file exists, is 1080×2340, is referenced with a width/height pair and a
dictionary alt — none asked the bot what it puts on the keyboard. Seven languages were rendered on
17 Oct from that list; EN and RU were frozen captures of an older screen, so the same six buttons
were baked in twice.

**What changed.**

- `tools/shots-gen/bot_menu.py` (new, stdlib ast only) reads `menu_kb()` from `bot/handlers.py` and
  returns the key order; the generator draws exactly those buttons. A new bot button is picked up by
  the next regeneration, and a forgotten regeneration is red instead of silent.
- All nine mockups redrawn through the one pipeline — 27 files. EN and RU are no longer frozen
  references: RU needed a sample answer added to the generator's `CANNED` table (the same sample
  task as the other eight languages, translated; no dictionary on the site changed), EN already had
  one for calibration. The keyboard now has seven rows in every language; the mockup is 1793 px tall
  at the last row against an input bar at 2170 px, so nothing is clipped.
- `tools/shots.json` (new) is the ledger: sha256 of every webp, the menu order, and the exact strings
  drawn (bot texts + canned sample). It is written only by
  `gen_shots.py … --apply --stamp`, so a picture cannot be replaced or outrun by an edit silently.
- The sweep grew 1,973 → 2,031 checks: menu order = `menu_kb()`, every drawn bot string = the bot's
  current text (read from `i18n.py` / `i18n_extra.py` with ast, no import), canned strings = the
  generator's `CANNED`, and every file's bytes = the ledger.
- No page HTML changed: the files keep their names and 1080×2340 geometry, and the pages still ask
  for 540×1170. `tools/build.py --check` reports 24 files equal to a fresh build. The 27 images grew
  1.72 MB → 1.90 MB in total (the seventh row, ~7 KB per file); every language page stays inside the
  1.25 MiB page budget.

**Controls.** A throwaway copy of the tree (`scratch/neg-shots-231026b`, `LANDING_ROOT`): removing
`invite` from the ledger's menu list fails `shots: menu = bot menu_kb()`; changing one recorded
Spanish string fails `shot texts = bot`; copying the Ukrainian file over `shot1-es.webp` fails
`shot1 bytes = ledger`. Three breaks, three red checks, nothing else moved.

**Checked after the change.** Sweep 2,031 / 0. Links 11 pages / 0 problems. Render-check ALL OK
(JS errors none). Visual pass PROBLEMS 0 — 18 page loads, 9 languages × 420/1440, screenshots in
`evidence/visual-20261023`; the desktop shots section of `/` now reads the seventh row
("Invite a friend"), confirmed by OCR of the rendered page, not of the asset.

**What it cannot prove.** That seven is the right number tomorrow — the gate follows `menu_kb()`,
so it proves agreement, not judgement. That the *other* screens (price list, language menu) match
the bot: the mockups are the first screen only. And that the owner prefers the regenerated EN/RU
images to the old captures — they are now the same pipeline as the other seven (default taken:
uniformity over frozen references).

## The policy listed six things; the bot kept fifty-one columns (23.10.2026)

**What was found.** `privacy.html` §1 named six categories of data: the Telegram user ID with
the interface language, the content sent to the bot, technical processing records, purchase
records, and referral links. The bot's database wrote more than that:

| stored, not named in §1 | where |
|---|---|
| the public @username, Telegram Premium status | `users.username`, `users.premium` |
| the language the visitor's own Telegram app is set to | `users.tg_lang` |
| the tag of the link that brought the visitor (`src_landing_*`) | `users.source` |
| photo present, bio length, username present, account language, an age read from the bio, six bio words (school / student / parent / exam / tutor / English), shared group chats, the kind of “last seen”, whether a phone number is shown | `profiles.*` (13 columns, keyed by `user_id`) |

The cron `профили-бота` has been filling that table daily at 08:30 since 15 Oct; at the time of
the check it held four rows for five users. So §1 was not merely incomplete: it said “we do not
ask for or store your name” while the public name was stored, and §2 called its statistics
“aggregated, de-identified” while the profile row sits next to a `user_id`. The policy also
described the footer as the eight badge pictures only — three plain text links
(realisticai.io, aitooltrek.com, basedtools.ai) were not named anywhere.

**Why nothing caught it.** Every privacy battery compared the policy with the site: the rights
list, the legal bases, the processors, the badges, the cookies. None compared it with the bot.
The policy was checked against itself, so it could stay true to its own wording and false to the
machine. The `profiles` table made this worse by existing in two places — `bot/storage.py` and
`scripts/profile_collect.py` — neither of which the site ever read.

**What changed.**

- §1, both halves: nine bullets. New: the app's own language (used once, on the first visit);
  @username and Premium (“Telegram shows both publicly… we never ask for your real name”); the
  arrival tag (“a word about a place, not about you”); and the profile observations, field by
  field — with the limits spelled out: never the bio text, only that a phone is shown, the kind
  of “last seen”, read as totals, never published, never shown to other users, never used for
  advertising.
- §1 closing paragraph: “your name” → “your real name”, plus one sentence that these
  observations come from what Telegram shows publicly, not from messages.
- §2: the purpose is now “understand who uses the bot … read as totals rather than one person at
  a time”, with “no decision about you is taken automatically from them”; the legitimate-interest
  clause says “statistics about the service as a whole” instead of “aggregated statistics”.
- §5: the profile observations are kept while the account exists and are deleted with the rest.
- §7: the three footer text links are named, with the same sentence as the badges — nothing is
  sent until a visitor clicks.
- The sweep grew 2,031 → 2,045 checks. New battery: the sweep reads the bot's schema (both files,
  stdlib regex, no import) and requires every column of `users`, `tasks`, `purchases`,
  `referrals`, `profiles`, `contacts` — 51 columns — to have a phrase in the EN half **and** a
  phrase in the RU half of the policy. A column the bot writes but the map does not know is red;
  a map entry the bot no longer writes is red; a phrase that fell out of the text is red. Plus
  “real name, not name”, the deletion sentence, and: every external host linked from any of the
  nine pages must be named in the policy in both halves.
- One source for the bot's address: `BOT_ROOT` in the sweep and `BOT_DIR` in `gen_shots.py`
  replace three literals — which is what let the negative controls run on a copy of the tree
  instead of on the live site.

**Controls.** A throwaway copy of the tree (`scratch/negpriv2-222734`, `LANDING_ROOT` +
`BOT_ROOT`): 2,044 / 0 before any break. Then four breaks, four red lines, nothing else moved:
(a) the RU bullet “Ваш @username” → “Ваш ник” fails `privacy names every field the bot writes:
users | username[ru]`; (b) “настоящее имя” → “имя” fails `privacy says 'real name' while storing
@username`; (c) a `phone` column added to `users` and `school_name` to `profiles` in a copy of
the bot fails `covers every column the bot writes | [('users','phone'), ('profiles','school_name')]`;
(d) removing the three-links sentence from the EN half fails `privacy names every external site
the page links to [en] | aitooltrek.com, basedtools.ai, realisticai.io`.

**Checked after the change.** Sweep 2,045 / 0. Links 11 pages / 0 problems. Render-check ALL OK,
JS errors none. Visual pass PROBLEMS 0 — 18 page loads, 9 languages × 420/1440. cwv 69 / 0.
a11y-extra 124 / 0. wcag22 43 / 0. axe 12 pages / 0 violations. Cross-engine 60 / 0 (WebKit +
Firefox; mobile, desktop and three landscape sizes; 426 s). Nu validator: no real findings, the
privacy page itself 0 messages. External links: 0 problems — the three newly named directories
answer 200. The legal page measured by eye at 420 and 1440, both halves: horizontal overflow 0,
the nine-bullet list wraps cleanly, nothing clipped.

**What it cannot prove.** That this is the lawful basis: “legitimate interest, statistics about
the service as a whole” is now stated, but whether it holds for observations taken from minors'
public profiles is a lawyer's judgement, not a gate's. That a user ever sees this notice: the bot
has no link to the policy in `/start` or the menu, so the notice still reaches only visitors of
the site — that is a bot-side block, not this one. That the rows already collected are wanted: if
the owner would rather not keep “last seen” and Premium at all, dropping two columns is a one-line
change, and the gate will demand the policy follow it. And that the three text links belong in the
footer — they are named now, which is the honest minimum, not a judgement about keeping them.

## The shop was open; the workshop had no door (23.10.2026)

**What was found.** GitHub Pages publishes the repository root, and the root holds both the site
and the machinery that builds it. Measured, not inferred: 154 files are committed, and the pages
are served beside them — `/README.md` returned 200 with byte-for-byte the file on disk (196 KB —
this notebook), `/tools/build.py` 73 KB, `/index-src.html` the unbuilt template with `{{BASE}}`
still inside and English only, a locale dictionary, `demo/captions.py`, `tools/shots.json`, even
`.gitignore` and two early evidence copies that were committed before the ignore rule. Directory
listings are off and no page links to any of them, but a path guessed once is a path forever.

What the notebook carried while it was public is the part that matters: a private LAN address, two
loopback endpoints with ports, four home-directory paths, the name of the software that runs the
work, and the systemd unit whose name ends in a GPU model. The owner's rule of 23 Oct — public
surfaces are neutral: no paths, no addresses, no tool names — was being broken by the file that
keeps the record of the project obeying it.

**Why nothing caught it.** Every battery reads the pages. The page is what gets checked: its links,
its texts, its colours, its claims, its weight. The files beside it were in nobody's scope, and the
one file that mentioned them, `robots.txt`, said `Allow: /`.

**And robots.txt was not read anyway.** A crawler asks the *host root* for `/robots.txt`. On this
project site that is `https://kerio-byte.github.io/robots.txt`, which answers 404; our rules live at
`/uchisambot/robots.txt` and nothing fetches them. Eleven AI-crawler groups had been maintained
there since 21 Oct — well-formed, ineffective. The live-assets battery asked whether the file
existed, and it did. The rules become live the day the site has its own domain; until then the only
protection that works is not publishing the file at all.

**What changed.**

- Redaction of the published text — nine places in this notebook, four in the tooling. The LAN
  address, the loopback endpoints, the home paths, the software names and the GPU-bearing unit name
  are gone; each sentence still makes its point ("a box on our own LAN is still our
  infrastructure", "one restart on the host"). `demo/build-full-demo.sh` and
  `build-web-loop-langs.sh` now take their kit path from `$ROOT` instead of an absolute home path;
  `gen_shots.py` renders into `.shots-work/` inside the repo (gitignored) instead of a
  home-directory cache.
- `robots.txt` rewritten: the workshop is disallowed in *both* groups — `*` and the AI group (RFC
  9309 gives a robot the most specific group, so rules written only under `*` would not bind
  GPTBot). Eight paths: `/README.md`, `/index-src.html`, `/src/`, `/tools/`, `/evidence/`,
  `/demo/*.py`, `/demo/*.sh`, `/demo/*.json`. The file now says in its own comment that today it is
  not consulted.
- `tools/publish-tree.py` — one explicit list of what a site is: 115 files, 10.7 MB (nine pages and
  their md twins, the legal pages, 404, sitemap, robots, llms, the IndexNow key, `img/`, `fonts/`,
  the eleven videos). `--check` fails when a listed file is missing, when a page links into the
  workshop, or when a referenced file is not in the list; 39 files are named as the workshop and
  left out.
- `tools/publish-branch.sh` — `--dry-run` stages that tree and asks a local server for every address
  in it (83 addresses, 0 errors); without the flag it writes the tree to a `gh-pages` branch and
  pushes it. Switching Pages to that branch is one click in the repository settings, and it is the
  owner's click, not a cron's.
- The sweep: 2045 → 2049. Four checks — the published text carries no private address, loopback
  endpoint, home path, software name or GPU model; the publish list is complete and workshop-free;
  the list names its own size; `robots.txt` disallows the workshop in *every* group, not only in
  `*`.

**Controls.** A throwaway copy of the tree, three breaks, three red lines, nothing else moved:
(a) a private LAN address written into the copy's README fails `что отдаёт сайт… |
README.md:11 частный IP`; (b) one `Disallow: /tools/` removed from the AI group fails `robots:
мастерская закрыта в каждой группе | GPTBot,… нет /tools/`; (c) `img/logo.svg` deleted fails
`состав публикации… | ссылка на файл вне публикации: img/logo.svg`. The copy showed three
environmental failures of its own (no git history, no bot tree), which is why its count reads 1993,
not 2049.

The first run of that control also caught the check itself, which is the reason it exists. The copy
lives inside another git repository (the agent's working directory), so `git -C <copy> ls-files`
answered with *that* repository's list, every file of the copy looked untracked, and the text scan
went quiet — green without reading a single line. One comparison fixed it (the repository root must
be the tree root); after that the control produced the three lines above. A gate that decides what
to read from a command's silence is one `cd` away from being a gate that reads nothing.

**Checked after the change.** Sweep 2049 / 0. Build `--check`: 24 files match. Publish list: 115
files, 513 internal references, every one inside the list. Publish tree served locally: 83
addresses, 0 errors. Links 11 pages / 0 problems. Render-check ALL OK, JS errors none.
Nu-validator: no real findings. External links: 11 pages, 0 problems. Visual pass: 18 loads, 0
problems.

**What it cannot prove.** That the workshop is unreachable — it is not: `/README.md` and
`/tools/build.py` still answer 200, and the rules that say otherwise sit in a file crawlers do not
fetch. What works is the branch switch (prepared and tested, one click) or a private repository
(paid; Pages from a private repo is not free). That no crawler has taken the notebook already: we
can log our own requests, not Google's, and the notebook has been public as long as the repository
has. That the redaction found every identifier: the gate knows the patterns it was given; a hostname
or an account id would pass unnoticed until somebody adds the pattern. And that the owner wants this
notebook public at all — the redaction assumes yes, because it is the record of the work, and
deletes nothing.

## The workshop had no door; now it has no address (24.10.2026)

**The gap.** The previous entry ended with an admission: `/README.md` and `/tools/build.py` still
answered 200, and the rules that said otherwise sat in a file crawlers do not fetch. The publication
source was the **root of `main`**, where the pages live next to the workshop — this notebook (196 KB,
with the database schema, the payment flow, the cron schedule), the generator, the nine dictionaries,
the assembled template and the proof frames. Redaction can take the names out of the text; it cannot
take the text off the site. Every gate we had read files in the working tree, and all of them were
green on a site that served the workshop.

**What changed.**

- Publication source: `main` / → **`gh-pages` /**, one call —
  `gh api -X PUT repos/Kerio-byte/uchisambot/pages -f 'source[branch]=gh-pages' -f 'source[path]=/' -f 'build_type=legacy'`.
  The branch had been staged by `tools/publish-branch.sh` from `tools/publish-tree.py`: 115 files,
  10.7 MB, 83 addresses answered by a local server with 0 errors before the switch. `main` keeps the
  whole workshop; nothing was deleted, and nothing in the diary was cut to make the site publishable.
- `tools/publish-branch.sh` now pushes that branch to **every** remote (GitHub serves it, [приватное зеркало]
  keeps the copy) and then reads the Pages setting back: if the site is still served from `main`, the
  script says so and exits 1. The silent failure of this change is "the branch is fresh, the world
  sees yesterday", so the script asks the setting instead of assuming it.
- The sweep: 2049 → 2051. Two checks now ask the **site**, not the files: (1) six workshop addresses
  — the diary, the generator, a dictionary, the template, a proof frame, a demo script — must answer
  404; (2) `index.html` and `sitemap.xml` in the live root must be byte-identical to the built ones,
  otherwise the publish branch lagged a commit. Network silence is red, not a skip: the sweep already
  needs the network for the bot's model probe, and quiet is not the same as fine.
- `robots.txt` keeps its eight `Disallow` lines. They no longer protect anything — those addresses
  are 404 — but they are the second lock on the same door and cost nothing.

**Controls.** A throwaway copy of the tree served by a local test server the way the old Pages did
(everything at the root): the six addresses answered 200 and the gate reddened, naming all six. That
control also caught the gate: its sixth probe was `demo/gen_shots.py`, which does not exist in the
tree, so its 404 had proven a typo and not a policy. The list now refuses a path that is absent from
the working tree, and the red line names it. Second control: one comment appended to a copy's
`index.html` while the staged tree was still being served — the freshness gate reddened with both
hashes (`живой 3a5ae810, в дереве 68299359`).

**Checked after the change.** Live: `/` byte-identical to the built `index.html`
(`sha256 3a5ae810…`), nine language pages 200, `privacy.html`, `terms.html`, `404.html`,
`sitemap.xml`, `robots.txt`, `llms.txt`, `index.html.md`, the logo, a badge, two videos — 200; an
unknown address returns our own 404 page ("Page not found — UchiSamBot"); `README.md`,
`tools/build.py`, `src/locales/en.json`, `index-src.html`, `evidence/…png`, `demo/captions.py` — 404.
Sweep 2051 / 0. Build `--check`: 24 files match. Publish list: 115 files, 513 internal references,
all inside the list. The GitHub build that followed the switch reports `built`, no error.

**What it cannot prove.** That nothing was copied before today: the notebook was public from the
first commit of this repository until this switch, and the only copies we know of are the ones in
git history. That the redaction was complete while it was public. That the setting stays: one
settings change reopens every address at once, which is why the gate asks the site and not the
setting. And that page edits will reach the world by themselves — they will not: from now on the
build → sweep → commit → `publish-branch.sh` order is the only way a change becomes visible, and a
forgotten last step is exactly what the freshness check is for.

## The policy said no other servers; only the markup was ever asked (24.10.2026)

**The gap.** The privacy policy makes the site's strongest factual claim — opening a page sends no
request to anyone but us, and the only exception (`api.web3forms.com`) happens when a person presses
Send. Three checks stood behind it, all reading attributes: `<img src>` with an absolute address,
`<script src>`, `<link rel="stylesheet" href="https://…">`, plus the `preconnect`/`dns-prefetch`
hints added on 23.10. A browser is asked for more than that. Fonts arrive through `url()` inside
`@font-face`, the hero asks for a `poster` and a `<source>`, `<link rel="preload">` and `srcset`
fetch files before a pixel is painted, and none of those shapes was in any gate. So a font moving to
a CDN — one edit, no visible change on the page — would have left the policy asserting something
untrue, with every check green. And nothing at all looked at the wire: an address assembled in
script (`atob` plus `new Image().src`) is invisible to every regex ever written.

**What changed.** Two gates of different natures, because neither one is enough.

- `landing-sweep.py` now enumerates every address a browser **must** load — `img/source/video src`,
  `poster`, `srcset`, `script src`, `iframe`, `object`/`embed`, `link[stylesheet|preload|icon|
  apple-touch-icon|manifest]` and `url()` in CSS — and requires each one to resolve to our own host.
  Relatives pass, `data:` passes, everything else has to be `kerio-byte.github.io`. 258 load-bearing
  addresses across the twelve pages; +21 checks (9 language pages + all 12 files) → **2072 checks**.
- New battery `landing-third-party.py` — 12 pages in Chromium, 9 assertions each (**108 checks**):
  the document answers 200 and actually pulls assets; every request went to our host; no failed
  request; no response ≥ 400; no JavaScript error; opening a page makes no non-GET call (beacons
  post); no cookie is set; and storage holds only the one key the policy names (`ucs_sent`).
  It prints `CHECKS: N, FAILED: 0` and exits non-zero otherwise, like the rest of the family.

**Controls.** A hardlinked copy of the tree (`cp -al`; every edited file is replaced — `unlink` then
write — or the hardlink would truncate the real page), served locally, run through the sweep with
`LANDING_ROOT` and through the battery with `--base`.

- Foreign font only, in `es/index.html`: the old gate set stayed green — `privacy no third-party
  assets` and `no third-party image hosts` did not notice a `url()` at all — while the two new checks
  answered `css url()->https://fonts.gstatic.com/s/manrope/manrope-latin.woff2` and the sweep exited 1.
- Runtime beacon only (`atob` + `new Image().src` to `evil-example.com`): the sweep reported **zero**
  failures naming it, which is the point — static reading cannot see an address that does not exist
  as text. The battery named `evil-example.com` on both "no foreign host" and "no failed request".
- The battery's first version counted hosts on **responses**. The beacon's domain does not exist, so
  there was no response and "no foreign host" stayed green — the leak was caught only one line lower,
  as a failed request. Hosts are now counted on `request` events. The control above is from the fixed
  version; the bug is recorded because the control is what found it.

**Checked after the change.** Sweep 2072 / 0. `tools/build.py --check`: 24 files match, so nothing in
the shipped HTML moved. Battery 108 / 0 on the live site: 12 pages, 6–19 requests each, one host —
`kerio-byte.github.io`. The static enumeration finds 258 addresses and 0 foreign ones.

**What it cannot prove.** That the visitor's browser behaves like ours: an extension, a hosts file or
a DNS filter can block a request in one browser and not in another, and the battery records what one
Chromium did. That a click cannot reach a third party — `a href` and `form action` are deliberately
out of scope (they carry no request until a person acts). And that the storage line stays honest in
both directions: it compares against the single key the policy names, so a future feature that adds
a second key must add it to the policy first, and the check will say so.

## The form said "sent" and had nothing to say when it was not (24.10.2026)

**The gap.** The contact form is the only support channel on the site, and its happy path was gated
end to end: nine languages, native POST → Web3Forms → mailbox → return to `?sent=1`, the letter
read back from the inbox. Its failure path was gated by nothing, and — measured, not assumed — did
not exist. A probe that made the endpoint fail three ways found the same shape every time: a broken
connection left the visitor on `chrome-error://chromewebdata/`; HTTP 500 left them on
`api.web3forms.com/submit` reading "Internal Server Error"; 429 left them reading "Too Many
Requests". In all three the site was gone from the screen, the typed text was gone with it, nobody
said the message had not been sent, and nothing on our side recorded that a person had tried. Nine
languages became the browser's or the API's English.

The same probe turned up the other end of the same promise. The page tells the visitor "we read
every message" (q11a, nine languages). The only mechanism behind that sentence was a watcher
searching the mailbox every ten minutes — and its query had no `in:spam`. The first letter I sent
through the new path (from a local copy of the page, not the live site) arrived, and Gmail filed it
under SPAM: the watcher answered "No messages found" while the site had already told the sender "we
received your message". The same letter sent later from the live origin landed in the inbox — so the
classification follows the referrer, not the new code, and it can go either way. The blind spot is the
query, not the sender.

**What changed.**

- **The form sends without leaving the page.** `fetch` with `Content-Type`/`Accept: application/json`,
  the documented Web3Forms AJAX contract. Success requires an explicit `success: true`; status alone
  is not enough, because the API answers 200 with `success:false` when it refuses (invalid key, quota,
  spam filter). The visitor never navigates, so the site stays on screen in every outcome.
- **Failure speaks, in the page's language, and keeps the text.** Two new lines above the form —
  a general one and a "form is busy" one for 429/5xx — with `role="alert"` and a programmatic focus
  so a screen reader announces it. The textarea keeps its contents, the button comes back enabled,
  and a `busy` guard makes a double click one letter, not two. Three keys × nine languages.
- **The old path survives.** The native POST, the `?sent=1` return and the CSS `:target`
  confirmation stay for browsers without `fetch` and for readers without JavaScript. The token logic
  that proves "this confirmation is yours" was not touched.
- **The watcher now looks in spam** (`in:inbox OR in:spam`) and says so in the notification: a letter
  that Gmail filed as spam is announced as such instead of being silently invisible. The canary that
  guards this promise had the same class of hole from the other side: it treated *any* spam letter as
  a loss, which was right while the watcher could not see spam and became wrong the moment it could.
  It now asks the ledger: a spam letter the watcher recorded is accounted for, with a printed warning
  that delivery is shaky; a spam letter nobody recorded is still a loss. Both directions were run
  (control below).
- **Gates.** `landing-contact-e2e.py` grew a failure section: five outcomes per language (network
  abort, 500, 429, `success:false` at HTTP 200, and success), judged by what a person sees — URL
  unchanged, the right line visible with the right words, text kept, button restored, focus on the
  message, exactly one POST per submit. 150 → **910 checks**, 9 languages, 135 s.
  `landing-sweep.py` checks the same in the files it ships: the two lines baked and hidden, their
  order above the form, the alert roles, the colour rule, the sending label, the JSON path, the
  `success === true` test, and that no `form.reset()` can appear in the handler.
  **2051 → 2172 checks.**
- **A fresh check for the watcher** in the sweep: the inbox script must search spam, or the sentence
  "we read every message" is again a promise without a mechanism.

**Controls.** Three hardlinked copies of the tree (`cp -al`; every edited file replaced, not edited in
place, or the hardlink would cut the real page), served locally, battery run against each with
`LANDING_ROOT`.

- The old behaviour (`canAjax = false`): ten red lines, and the detail column still names the old
  wounds — `chrome-error://chromewebdata/` for the abort, `https://api.web3forms.com/submit` for 500
  and 429.
- Sending works but any answer counts as success (`if (true)` instead of `success === true`): nine
  red lines on 500/429/refused — the silent lie is caught.
- Failure that clears the form (`form.reset()` in the error handler): four red lines, "текст не
  потерян".
- The first version of the failure section crashed with a traceback instead of reporting, because the
  page it was judging had navigated away and its DOM was gone. Rewritten: one defect, one red line.
- The canary, both directions, on the real mailbox: a temporary ledger without the test letter →
  `FAILED 1`, "в леджере её нет — письмо потеряно"; the real ledger → `FAILED 0` plus
  "пришла в СПАМ — сторож её увидел, но доставка шаткая". Losing a letter is still red; a letter
  in spam is not a gate failure once it is on the record.

**Checked after the change.** Sweep 2172 / 0 on the live tree. `tools/build.py --check`: 24 files
match. Battery 910 / 0 across nine languages. Real Chrome (CDP), real endpoint: the JSON POST from a
foreign origin is allowed (CORS answered, body readable), a refusal arrives as `400 {"success":false}`,
and a real submit returned `200 {"success":true,"message":"Form submitted successfully!"}`. Delivery
was confirmed in the mailbox, not by the answer: from the live page, letter `1a16b585a63e481b` (stamp
03:38:32) arrived in the inbox with the stamp and the reply-to address intact; an earlier one sent from
a local copy of the page arrived in spam — which is how the watcher's blind spot was found. Live run of
the battery against the published site: 13 / 0. Live page sha256 equals the built `index.html`.

**Eyes on it.** Six screenshots (ru/hi/en × 420 px and 1280 px) of the failure state and four of the
success state, in `evidence/visual-20261024-form/`. They found what no gate would have: the browser's
default focus ring drew a thick black box around the message. Replaced with a ring in the message's
own colour (green for sent, red for not sent), and the rule is now gated, so the box cannot come back.

**What it cannot prove.** That Gmail will keep filing these letters as spam, or stop. That the JSON
contract stays as documented — the live check would catch a change, but only when it runs. That an
extension on the visitor's machine cannot block the `fetch`: then the person sees "not sent", resends,
and we may get two letters instead of none — the failure is duplicated, not amplified. That the spam
folder will be emptied by a human: the watcher now says the letter is in spam, but nothing moves it
into the inbox, and deliverability itself is a reputation question no gate can answer. That a browser
without `fetch` gets the same honesty: it navigates away on failure exactly as before, because without
script there is nowhere to stay.

And a note for the next reader: the refund-promise gate reddened on this very block, on the word
"возврат" in two of my code comments ("return to the page", not "refund"). The comments were reworded
rather than the gate widened — it is a blunt rule on purpose, and it is alive.

## The page said «ты», and the one box where it asked you to write said «вы» (24.10.2026)

**The gap.** For most of its length the landing speaks to the reader in one voice. The principle
band: "чтобы ты мог самостоятельно решить похожую задачу". Three FAQ answers: "где ты застрял",
"последний шаг делаешь ты сам". Step four of the how-to, the referral line. Then, for every line of
the contact block, it switched to «вы»: "Ваш e-mail", "Ваше сообщение", "Используем ваш e-mail
только чтобы ответить на обращение", "Спасибо! Мы получили ваше сообщение и ответим на указанный
e-mail", "Напишите нам … ответим на вашу почту", "Проверьте связь и попробуйте ещё раз". Eight
lines, and the switch lands exactly where the page asks a person to write to us and where it answers
them — the moment the reader is asked to trust a stranger with an address.

Ukrainian the same, eight lines. Turkish had the switch in the other direction and inside a single
screen: the FAQ says "Birkaç dakika sonra yeniden dene — aşağıdaki formdan bize yaz", and the form
directly under it said "Bize yazın … size e-postayla yanıt veririz". Politeness in Turkish is a
suffix, so it was smeared across every label — adresiniz, mesajınız, metniniz, deneyin,
çocuğunuzun — twelve lines, none of which a pronoun search would find. Indonesian held "kamu/mu"
across the page and said "Anda" in the parents line and in both failure lines — the two lines
written the night before, the ones a person reads when something has already gone wrong.

Measured across all nine dictionaries, not assumed: es 24 informal keys and 0 formal (where "su/sus"
is "his/her", not an address), pt 24 and 0, hi 21 on आप, vi 22 on bạn — four languages were already
single-voice. So this was three and a half, not nine.

**Why no gate saw it.** Every text gate compares the page with its dictionary: printed == dictionary.
A page that contradicts itself satisfies both sides. Which voice the page uses had never been written
down anywhere — it was an intention, not a fact.

**What changed.** 33 strings in four dictionaries, in one direction: the page's dominant voice,
informal. ru and uk: eight lines each, from "Ваш e-mail" to "Твой e-mail", "Спасибо! Мы получили
твоё сообщение", "Проверь связь и попробуй ещё раз", "Напиши нам … ответим на твою почту". tr:
twelve, from "Bize yazın … size" to "Bize yaz … sana", "E-posta adresin", "Mesajın", "E-postanı
yalnızca bu mesaja yanıt vermek için kullanırız", "Bağlantını kontrol edip yeniden dene". id: three,
"teks kamu masih ada di kolom" twice and "data anakmu".

One line was not rewritten but made impersonal. The parents block's subtitle said "как мы бережём
данные вашего ребёнка" — the only line on the page that speaks about a child to a parent, and the
one place where the age of the reader is genuinely unknown. It now reads "как мы бережём данные
детей" in ru and uk; impersonality costs nothing and cannot be wrong. The owner can reverse the
direction in a word, but reversing means rewriting these 33 strings plus the ones that were already
informal.

**The gate is a registry, not a rule in code.** `tools/voice.json`: per language the chosen voice, the
words that carry it (must), the words of the other voice (forbidden), and how many keys must carry
the chosen voice (min_keys). English is in the registry explicitly, as "no distinction" — a
forgotten language cannot pass as a clean one. Two sweep checks per language and one on the registry,
2172 → 2189: no foreign voice anywhere in the dictionary; and the page and the contact block speak
one voice — the must-words appear in `min_keys` keys and in at least one `contact.*` key, because a
page that stopped addressing the reader at all would otherwise pass silently.

Word boundaries are built per script. Devanagari does not tokenise — `[^\W\d_]+` splits "आपका" into
"आपक", "स" — so a tokenizer would have made the Hindi check quietly vacuous while still counting as a
check.

**The gate found a second defect on the way.** Publishing moved to the `gh-pages` branch yesterday,
and the freshness check guarding it compared `/index.html` and `/sitemap.xml`, on the reasoning that
"one word changes both". Four dictionaries changed and the sweep printed ALL PASS while live
ru/uk/tr/id were a build behind: a change in ru.json does not touch the English root, and sitemap.xml
only moves when a date moves. The check now fetches all fifteen files the site serves — nine pages,
privacy, terms, 404, sitemap, llms.txt, robots.txt — and compares bytes. Before publishing it named
exactly the four stale pages; after publishing, all fifteen match.

**Controls.** Three full copies of the tree (real copies, not hardlinks: the build writes in place),
each broken one way and rebuilt so the build check stayed clean.

- "Используем ваш e-mail…" restored in ru `contact.note` → red, naming `contact.note`;
- every ты-form stripped from the ru dictionary → red on "страница и блок формы одной формы":
  0 keys of the 5 needed, 0 in the form;
- "E-posta adresiniz" restored in tr → red for tr, naming `contact.l_email`.

The first version of the second control was worthless and said so by staying green: substring
replacement without word boundaries turned "ответы" into "отвечеловек" and left the capitalised
"Твой"/"Твоё" untouched, so seven must-keys survived. Rewritten with boundaries and both cases: 0
keys, one red line.

One measurement worth recording: a copy of the tree living outside `~/Projects/stars-bots/promo`
reports 2133 checks instead of 2189, because some checks build paths from the parent directory
(the neighbouring study-bot). A copy placed next to it reports 2189 / 0 — so the difference is a
property of where the copy sits, not of the change.

**Checked after the change.** `tools/build.py --check`: 24 files match. Sweep 2189 / 0. The freshness
check proved itself in the right order: red on exactly four pages before publishing, green after.
axe 0 violations on 12 pages; a11y-extra 124 / 0; wcag22 targets 43 / 0; env-prefs 45 / 0; viewports
94 / 0; fonts 39 / 0; cwv 69 / 0; cross-engine 60 runs / 0 problems; third-party 108 / 0; en-leftovers
0; Nu validator clean; external links 0 problems; live-assets clean; the contact battery 910 / 0
across nine languages. Logs in `evidence/battery-20261024c/`.

**Eyes on it.** Four languages (ru, uk, tr, id) at 420 px and 1440 px in
`evidence/visual-20261024c-voice/`: PROBLEMS 0, no overflow, badges 8/8 in two rows on desktop and
four on mobile, and the block read in each language — one voice, nothing clipped. The Turkish
suffixes were checked on the screen, because that is the only place they are visible.

**What it cannot prove.** That informal is the right voice for a page parents also read — the page
was already informal in seven lines, but this is a taste call, reversible in a word. That the
forbidden lists are complete for Turkish, where politeness lives in suffixes: only the listed forms
are gated, and a new polite form would slip through. That no legal page contradicts the landing:
privacy and terms speak «вы» in Russian on purpose and sit outside the registry. And that a reader
notices at all — someone who came for homework help may never register the change; the point is that
the page no longer reads like two companies.

## Step 3 said the bot does the homework; the same page said it does not (24.10.2026)

The third step of the how-it-works block is the one a parent reads as "so what does my child get",
and in all nine languages it said the bot **solves** the task: «Бот решает по шагам», "The bot solves
it step by step", «El bot lo resuelve», «O bot resolve», «बॉट हर स्टेप में हल करता है», «Bot
menyelesaikannya», «Bot adım adım çözer», «Bot giải từng bước», «Бот розв'язує крок за кроком». A few
answers further down the same dictionary the FAQ answers "Is this cheating? No" and promises that for
solutions the bot **stops one step before the answer**; the band under the features says "Not just
answers"; the bot's own greeting says "I teach — I don't do your homework for you". So the page
sold the one thing it spends a whole FAQ answer denying. Turkish was the worst: the hero subtitle,
the step title and the step description all said «çözer» / «çözüm» — a reader could finish the hero
convinced the bot does the homework.

**The fix is one verb per language, taken from the page's own word for the thing.** EN "breaks it
down", RU «разбирает» (the bot's own verb: «разбираю задачи по шагам»), UK «розбирає», ES
«desglosa» (as in the hero), PT «percorre a solução», HI «समझाता है और हर कदम का कारण बताता है»,
ID «membahasnya» (as in the hero), TR «çözümü adım adım gösterir», VI «trình bày lời giải», plus one
hero line in Turkish: «ödevini adım adım çözmene yardımcı olur» — helps you solve it, not solves it.
**The unit's name stays.** A breakdown is «разбор» / "breakdown" / «desglose» / «çözüm» / «हल»
because that is what the bot itself calls it in the menu and in the price list; renaming the unit is
a product decision, not a copy edit, and a page that renames the thing the bot sells is worse than a
page that uses the product's word.

**The gate.** `tools/claims.json` — the same shape as `voice.json`: `no_solve_claim` lists the keys
that must not claim the bot does the work (`how.s3d`, `hero.sub`) and, per language, the verb forms
that are forbidden; `last_step` requires the answer to q10a to keep its "one step before the answer"
phrase, so the contradiction cannot be "fixed" by deleting the promise instead of the claim. The
sweep gained 18 checks (2193 → 2211): registry readable, registry names its keys, registry covers
all nine languages, every pattern compiles, and two checks per language. Reading the registry is not
enough — a missing language or an uncompilable pattern would make the gate blind while green.

**Controls.** Five mutations in five copies of the tree, each rebuilt so the build check stayed
clean, each red with its own line:

- ru `how.s3d` back to «Бот решает по шагам…» → red `claim: step 3 does not promise a solution`,
  naming `how.s3d: «\bрешает\b»`;
- tr `hero.sub` back to «…adım adım çözer…» → red for tr, naming `hero.sub: «\bçözer\b»`;
- en `q10a` with the last-step phrase cut → red `claim: the last step stays with the student`;
- tr dropped from the registry's `forbid` → red `claims registry covers nine languages`, printing
  which eight are left;
- a broken regex (`[незакрытый`) → red `claims registry patterns compile`.

The fifth control found a defect in the gate itself: the first version compiled patterns inside the
check but still fed the raw strings to `re.search`, so an uncompilable pattern killed the sweep with
a traceback instead of producing a red line — the run was non-zero, but 2,200 checks never ran and
nothing named the problem. Patterns are now compiled once, and the per-language loop only ever sees
compiled objects.

**Checked after the change.** `tools/build.py` rewrote the nine pages and their nine md twins, then
`--check` matched all 24 files. Sweep 2211 / 0. Nu validator: 126 messages,
all known-false trailing slashes, 0 real findings. en-leftovers 0. The visual pass over all nine
languages at 420 px and 1440 px: PROBLEMS 0, badges 8/8 in two rows on desktop and four on mobile,
no overflow outside the shots slider, no clipped text. The how-it-works block was photographed separately for
every language (`evidence/visual-20261024d-claim/how/`) and measured card by card: no `line-clamp`,
no clipped description, no card changing the row height. Published with `tools/publish-branch.sh`
(115 files, both mirrors, source read back as `gh-pages/`); `landing-live-bytes.py` then compared
the live site with the tree: 26 files, 26 match.

**What it cannot prove.** That a reader ever took "solves" for a promise — the sentence also says
"explains every move", and plenty of education products word it that way. That the new verb is the
best one: it is a phrasing choice, reversible per language in one word. That the Turkish page is now
consistent — its FAQ still says «bot soruyu çözerken cevaptan bir adım önce durur», and the bot's own
Turkish greeting says «soruları adım adım çözüyorum»; those live in the bot, not on the landing, and
changing them is a product decision. And that the unit's name («çözüm», «हल») does not carry the same
"it does the homework" reading all by itself — that is the question the wording change cannot answer.

**Files.** `src/locales/{en,ru,uk,es,pt,hi,id,tr,vi}.json` (one key each, tr two), `tools/claims.json`
(new), `tools/lastmod.json`, the nine rebuilt pages and their md twins, `README.md`, the skill
`stars-bots-ops`: `references/landing-qa.md` (section 24.10), `scripts/landing-sweep.py` (+18).

## The page Google reads had no gate, and its copy in the template was four answers behind (24.10.2026)

**What was found.** The sweep is the gate every block runs, and every check in it asks the
visitor's page: texts, prices, fonts, links, alt text, the form, the videos. `grep -c 'ld+json'`
over `landing-sweep.py` returned **0** — the structured data produced by `tools/build.py` was never
examined there, on any of the nine pages. One other script did look: `landing-live-assets.py`
compares the live FAQ text to the live page, loosely (`a in b or b in a`), and asks nothing about
the offers, the language fields, how many blocks a page carries, or the template. And the template
`index-src.html` carried a **second, hand-written copy of the same block**: 2,891 bytes of
`Organization` / `WebSite` / `SoftwareApplication` / `FAQPage` that the build replaced wholesale on
every run. Invisible on the site — and therefore invisible to everyone, including the people
editing it. It had drifted to **7 questions out of 11**, said `"inLanguage": ["en","ru"]` on a
nine-language site, and held the prices as text.

**The same file had drifted in three more places.** The inline English inside a `data-i18n`
element is the fallback `rep_i18n` returns when a dictionary key is missing — and three of them no
longer matched `src/locales/en.json`: `how.s3d` still said **"The bot solves it step by step and
explains every move"** (the claim two commits above this one removed from the page), `shots.cap`
still said "Real screenshots" (the honest wording is "this is what a breakdown looks like"), and
`q8a` still promised "10–60 seconds" where the page now says 5–60 with a two-minute ceiling. None
of that was visible, because the build always overrides it. All of it was one missing key away
from shipping on nine pages in English.

**The fix is one source and one marker.** `index-src.html` now holds
`<script type="application/ld+json">{{JSONLD}}</script>`; `jsonld()` returns the payload only, and
`bake()` **asserts** the marker is present instead of running a `re.sub` that would simply not match
and leave the old copy in place — silent substitution was the actual defect, the stale copy was its
symptom. The template fell from 71,840 to 69,081 bytes. The three inline defaults now say what the
dictionary says.

**The gate: 66 new checks (2211 → 2277).** Per language, seven: exactly one `ld+json` block; it
parses; the four node types appear once each; `inLanguage` on `WebSite` and `FAQPage` is the page's
language and `SoftwareApplication` lists all nine; the offers' prices and currency equal
`tools/prices.json`; the number of `mainEntity` questions equals the `<details class="rv">` items a
visitor opens; and every question and answer equals the visible text of that item. Globally, three:
the template carries no payload, the marker is present, and the template's built-in English — 105
element texts, 2 field placeholders, 2 attribute labels — equals `en.json`. That last one is the
check that would have caught "solves" two commits ago.

**Controls: eight mutations, each red with its own line** — inline text back to "The bot solves it";
the payload put back into the template; `pack5` repriced 120 → 125; the `ld+json` tag broken on the
Russian page; one FAQ item deleted from the Ukrainian page; `"inLanguage": "tr"` → `"en"` on the
Turkish page; the JSON broken on the English page; one visible answer rewritten. Each run was the
full sweep on the real tree; every file was restored from a snapshot afterwards and its sha256
compared before the next control. A second harness ran the same eight against isolated copies to
prove the checks fail on their own evidence, not on some neighbouring gate going red first.

**Checked after the change.** `tools/build.py --check`: 24 files match a fresh build. The nine
pages, the md twin, `sitemap.xml`, `llms.txt` and `404.html` are **byte-identical** before and
after — this block changed what the source says, not what the visitor sees, and the sha256 list is
the proof. Sweep 2277 / 0. The nine pages still carry one `<script type="application/ld+json">`
each; `privacy.html`, `terms.html` and `404.html` carry none, by design.

**What it cannot prove.** That a crawler will do anything with this markup: Google limited FAQ rich
results in 2023 to authoritative government and health sites, so the FAQ block is more likely to be
read as context than rendered as a widget. That `XTR` is accepted as a price currency by every
consumer of the file — it is Telegram's code for Stars, not a national currency. That the markup is
*complete* for rich results: there is no `aggregateRating`, because the product has no ratings yet
and inventing them would be the one lie this whole file is built to prevent. That the FAQ text was
unwatched before: `landing-live-assets.py` compared it on the live site, loosely — what was
unwatched is everything else, and the whole of it inside the sweep. And that the template copy would
ever have shipped: today the build always wins — the point is that nobody was checking, and a
`re.sub` that stops matching fails silently by design.

**Files.** `index-src.html` (payload → `{{JSONLD}}`, three inline defaults), `tools/build.py`
(`jsonld()` returns the payload; `bake()` asserts the marker), the skill `stars-bots-ops`:
`scripts/landing-sweep.py` (+66), `references/landing-qa.md` (section 24.10). No page, no image and
no dictionary value changed.

## The publish list checked itself, and six files rode along (24.10.2026)

**What was found.** `tools/publish-tree.py` is the one place that decides what the world
gets. Its `--check` asked four questions — every listed file exists, no workshop file is
listed, every internal link lands inside the list, no page points at the workshop — and it
answered them with one sentence that sounded stronger than it was: «список полон, лишнего
нет». "Nothing extra" compared the list **with itself**. The manifest walks all of `img/`
and `fonts/` with `rglob`, so anything dropped into those two folders becomes the site by
being there, and nothing ever asked whether a page wanted it.

Six files were riding along. `img/screen1.png` … `screen4.png` — four 1920×1080
screenshots, 1,104,464 bytes, committed on 15 October (f77ed94) for **uploading into other
people's forms** (PeerPush, OpenHunts, LaunchIgniter, the Product Hunt gallery), not for
the site: no page, no md twin, no `llms.txt` and no `sitemap.xml` names them. And
`img/shot4.webp` + `img/shot4-ru.webp` (57,496 bytes) — the fourth frame of the old "Real
chats" rail, which has had three frames since the redesign; the EN/RU pair that was never
re-cut when the other seven languages got their own. All six answered **200** on the live
site this morning, 1.11 MB of them. The screenshot set also predates the seven-button menu
(23.10), so the site was publishing pictures of an interface it no longer has.

There was a quieter reason nobody noticed: `landing-live-assets.py` had already classified
the same six as "kept — осознанно оставлены вне сайта", one hand-written reason each. The
file was honest about them being off-page and never asked the next question — off-page
means unpublished, or it means shipped.

**The fix is one folder and one honest list.** The four screenshots moved to
`submission-kit/` with a five-line README saying they are uploaded as files, never linked
by URL; the folder sits outside the manifest's walk. The two old frames are deleted, as the
fourth frame is gone from the page. Publication went from **115 files / 10.7 MB to 109
files / 9.6 MB**, and the six addresses now answer 404.

**The gate: a fifth check.** Every published file must be **named** by some published text
(html/md/txt/xml). Named is enough — a font lives in `url(...)`, a poster in `poster=`, an
og card in `og:image`; the only question is whether anybody asks for the file. Four files
are named by nobody and published on purpose, and they are listed in `PUBLIC_UNLINKED` with
a reason each: `.nojekyll` (the Pages flag), the IndexNow key (read at its address, never
linked), `robots.txt` (a crawler's convention) and `404.html` (served by the host for
unknown paths). The sweep gained one check that reads the new count line `без читателя: N`
and fails if it is not 0 **or if the line disappears** — a gate that watches the gate,
because the failure mode here was silence, not a red line.

**Controls: three mutations on the real tree, each restored byte-exact.** A stray
`img/zzz-control.png` → red, named with its size; the *same* file with one line added to
`llms.txt` → green, which proves the criterion is "has a reader" and not "is new"; a stray
`fonts/zzz-control.woff2` → red. After the restores `llms.txt` matched its snapshot sha256
and the check printed 0.

**Checked after the change.** `tools/build.py --check`: 24 files identical to a fresh build
— this block changed what ships, not what anyone reads. Sweep **2278 / 0**, one more check
than yesterday. `landing-live-bytes.py` after publishing: 26 / 26. The six removed
addresses: 404 from the live site. PeerPush's public page was read before deleting: its
gallery is served from `static.peerpush.com`, not from our host, and the workshop notes for
the other platforms record uploads, not links.

**What it cannot prove.** That "named somewhere" equals "needed": one stale sentence would
keep a file alive forever — the check is a floor, not a review. That no third party
hotlinks the six removed URLs: PeerPush was verified, the rest are recorded as uploads, and
a hotlink would break on someone else's page rather than here. That GitHub Pages drops the
six at once: the branch is authoritative, but a CDN copy can outlive the push by minutes —
the 404 probe was taken after the rebuild, not instead of it.

**Files.** `tools/publish-tree.py` (fifth check, `PUBLIC_UNLINKED`, the `без читателя`
line), `submission-kit/` (four screenshots + README), `img/shot4.webp` and
`img/shot4-ru.webp` (deleted), the skill `stars-bots-ops`: `scripts/landing-sweep.py` (+1),
`scripts/landing-live-assets.py` (six stale allowlist entries dropped),
`references/landing-qa.md`. No page, no text, no price and no picture the visitor sees
changed.

## The sentence left step 3 and stayed in the search result and in the screen reader (24.10.2026)

**What was found.** The previous pass took "the bot solves it" out of step 3 and the hero
subheadline in all nine languages. It left the same sentence in the one place a parent reads
**before** the click. `meta.desc` in Hindi said the bot is one "जो होमवर्क को स्टेप-बाय-स्टेप
हल करता है" — that solves the homework step by step; Turkish said "Ödevleri adım adım çözen,
… bir Telegram botu" — a bot that solves the homework step by step. Both sit in the tab
title's description, the search snippet, the bold line of a Telegram link preview and, word
for word, in the JSON-LD `description` block that crawlers read. The page itself answers its
own first FAQ with «नहीं / Hayır» to "is this cheating" and promises the bot stops one step
before the answer.

Two reasons the gate was silent. First, `tools/claims.json` guarded exactly two dictionary
keys — `how.s3d` and `hero.sub` — and the head is built from `meta.title` / `meta.desc`,
which nobody checked against the registry. Second, the Turkish forbid list held `çözer` and
`çözüyor` but not the participle `çözen`: even with the meta keys added, the old string
would have walked through.

**The same sentence was also read aloud.** Chasing the head turned up a third copy that no
dictionary could hold: the `aria-label` of the hero video — the sentence a screen reader
announces before the clip. It was not in `src/locales/` at all. `tools/build.py` carried a
`VIDEO_ALT` table of nine strings and substituted one for the English text at build time, so
that translation lived inside the generator, where every dictionary gate is blind by
construction. Six of the nine promised a solution: es «resuelve», pt «resolve», hi «हल करता
है», id «menyelesaikan», tr «çözüyor», vi «giải bài». EN, RU and UK used the unit-name verbs —
which is also why the sweep's only question about that attribute ("is it different from the
English one?") answered yes for all of them.

**The fix is two strings, in the page's own verbs.** Hindi now says the bot "समझाता है"
(explains) — the verb of its own hero and step 3 — and "बताता है" for how it covers a topic,
the verb step 3 uses for the reason behind a step. Turkish says "Ödevini adım adım çözmene
yardımcı olan" (helps you solve it step by step), the exact construction of its own hero
subheadline. Both descriptions were measured against the 160-character budget before the
build: 148 and 159. The titles were **not** touched: "हल" and "çözüm" are the product's unit
names the way "разбор" is in Russian, step 3 sells them as a noun, and the previous block's
decision that the unit keeps its name still holds.

The six aria-labels were rewritten by the same rule — each from that language's own hero or
step 3: es «desglosa», pt «divide a tarefa em passos», hi «एक-एक स्टेप में समझाता है», id
«membahas», tr «çözümünü adım adım gösteriyor», vi «trình bày lời giải». The table itself was
then deleted: the video tag carries `data-i18n-attr="aria-label:demo.alt"`, the string sits in
all nine dictionaries, and the generator no longer holds a single translated sentence.

**The gate has two halves now.** The registry guards five keys (`how.s3d`, `hero.sub`,
`meta.title`, `meta.desc`, `demo.alt`) and Turkish gained `\bçözen\b`. On top of that the sweep reads the
**shipped head** of all nine pages — `<title>`, `meta[name=description]`, `og:title`,
`og:description`, `twitter:title`, `twitter:description` and every JSON-LD `description` —
and asks two questions: does each field equal the dictionary string (one source, five
surfaces), and does any of them carry a forbidden verb. Six checks per language plus one on
the registry itself, and one more per language for the video label (`aria-label` must equal
`demo.alt` — the wiring that had silently fed the old table): **2278 → 2342**.

**Controls: seven mutations in a copy of the tree, each rebuilt before the sweep.**

| mutation | expected red line | what it printed |
|---|---|---|
| hi description back to «हल करता है» | dictionary + head | `claim: guarded keys do not promise a solution \| meta.desc: «हल कर»` and the head line naming meta description, og, twitter and json-ld |
| tr description back to «çözen» | new pattern works | `meta.desc: «\bçözen\b»` — the old string would have passed without the added form |
| dictionary clean, `og:description` sabotaged in the built page | head gate is independent | `head: og/twitter copies == dictionary \| og:description` + `head: no solve claim before the click` while the dictionary check stayed green |
| registry told to guard only the two body keys | the registry is watched | `claims registry guards the head keys \| keys=['how.s3d', 'hero.sub']` |
| one JSON-LD description drifted | copies must match | `head: json-ld description == dictionary \| узлов 1` |
| hi `demo.alt` back to «हल करता है» | dictionary, and only the dictionary | `claim: guarded keys do not promise a solution \| demo.alt: «हल कर»` — the equality check stayed green, because the rebuilt page agreed with the bad dictionary |
| dictionary clean, video `aria-label` sabotaged in the built page | equality is independent | `video aria == dictionary \| «डेमो: … हल करता है।»` while the dictionary check stayed green |

**Checked after the change.** `tools/build.py --check`: 24 files identical to a fresh build.
Sweep **2342 / 0**. Nu validator: 0 real findings. `landing-en-leftovers.py`: 0.
`landing-a11y-extra.py`: 124 / 0. `landing-axe-audit.py`: 12 pages, 0 violations.
`landing-render-check.py` with a local server: 4 pages, bullets 4, overflow 0, no JS errors.
The publication check did the measuring twice: after the meta half it named exactly two stale
addresses (`/hi/`, `/tr/`), after the aria half exactly six (`/es/`, `/pt/`, `/hi/`, `/id/`,
`/tr/`, `/vi/`) — each time the whole set of what had changed and nothing else. Published
through `tools/publish-branch.sh` to both mirrors, Pages source read back as `gh-pages/`;
`landing-live-bytes.py`: **26 / 26**, and the nine live pages were then read back one by one
to see the shipped `aria-label` of each, not just the hash of a file.

**What it cannot prove.** That a Hindi or Turkish reader hears "समझाता है" / "yardımcı olan"
as teaching rather than as a softer promise of the same thing — that is a copywriter's ear,
and both lines roll back with one word per language. That the registry is complete: it lists
the verb forms we have seen, so a synonym nobody has written yet would pass — the protection
is only as wide as the list, which is why the head check reads the patterns rather than a
fixed phrase. That no cached preview survives elsewhere: Telegram and the search engines keep
their own copies of a link preview, and a fresh scrape is not something this repo can force.
That the five surfaces are all of them: the page could grow a sixth copy of the description
(`<meta name="application-name">`, a manifest, a second JSON-LD node) and the check would
name it only if it matched one of the six patterns above. That the generator is now
translation-free: a search of `tools/build.py` found one other per-language table — `LABELS`,
the language names in their own script — which is data about the selector, not a sentence
about the product, but that is a reading and not a gate. And that a screen-reader user hears
the new label as help rather than as the same promise in different words: only a listener can
say whether it lands.

**Files.** `src/locales/*.json` (nine files: `demo.alt` added to every one; `meta.desc` also
rewritten in hi and tr), `index-src.html` (`data-i18n-attr` on the video), `tools/build.py`
(`VIDEO_ALT` deleted, its substitution gone), `tools/claims.json` (five keys, one pattern, the
note that records both passes), six language pages and the two md twins that changed with
them, `tools/lastmod.json` (rebuilt), the skill `stars-bots-ops`:
`scripts/landing-sweep.py` (+64), `references/landing-qa.md`. Live pages: `/es/`, `/pt/`,
`/hi/`, `/id/`, `/tr/`, `/vi/`.




## The screenshots were redrawn with a seventh button; the videos above them still had six (24.10.2026)

On 23 October the chat mockups were redrawn because the bot's menu has seven buttons
(`menu_kb()`) and all nine languages had been drawing six — the page's "real chats"
section showed a keyboard the bot never had, and the referral paragraph underneath
advertised the button the pictures left out. That commit changed 27 stills, moved the
generator from a hand-written list to the bot's own source, and wrote `tools/shots.json`
as a ledger. It did not touch the video. Every language page opens with a 13 s loop, and
the poster a visitor sees before pressing play is that loop's last frame; the loops were
cut from other files — the EN and RU captures in `submission-kit-20261014`, the other
seven from `.shots-work` renders — so when the stills were redrawn the pictures that
move stayed as they were. For a day the same page showed seven buttons in the chat
section and six in the hero, and sold a seventh in the paragraph between them.

**What the reading was.** Tesseract on the shipped Spanish poster, bottom of the frame:
`Ejemplos gratis / Analizar un problema / Revisar mi solución / Resumen y tarjetas /
Precios / Ayuda` — six rows, Help last. On the screenshot the page itself displays:
`… / Precios / Invitar a un amigo / Ayuda`. The seven other Latin-script posters read
the same way (`Invite a friend`, `Пригласить друга`, `Convidar um amigo`, `Ajak teman`,
`Arkadaşını davet et`, `Mời bạn bè`, `запросити друга`); the Hindi poster has no OCR
data on this box and gained exactly one text line (18 → 19 with the English model) —
the same one row. The 35 s demo linked from `llms.txt` and the launch platforms carried
the same six-button welcome scene for eight seconds of its thirty-five.

**The fix is a source, not a re-render.** `demo/build-web-loop-langs.sh` used to name an
external catalogue; it now reads `img/shot2[-<lang>].webp` and `img/shot3[-<lang>].webp`
— the two files the page displays. That is a smaller pipeline, not a bigger one: a
rebuild needs no Playwright run, no kit, no scratch workdir, and the loop and the still
are the same picture by construction. The same three files feed scenes 1–3 of the full
demos; scene 4 (the language switch) has no page equivalent and stays in the kit — see
the open item below.

**The gate that was missing.** `demo/captions.json` described the loop's bytes and the
poster's bytes, so "re-cut the video, forgot the poster" was red — but nothing described
what the loop was *cut from*, which is why a redrawn screenshot left nine videos green.
The ledger now carries, per language, `sources.shot2` / `sources.shot3` and their sha256;
`landing-sweep.py` compares them with `img/` on every run (18 checks), adds six for the
full demos' scenes 1–3, and two mechanism checks that do not read the data at all: the
loop builder may not declare an external catalogue (`KIT=` / `SHOTS_DIR=` gone), and the
full demo must take scenes 1–3 from `img/`. Sweep: **2,342 → 2,368 checks.**

**Checked by breaking it.** On a copy of the tree (`LANDING_ROOT`) one screenshot was
redrawn with a red box and the loop left alone. Exactly one new failure appeared, naming
the file, both hashes and the command:

```
FAIL [es] loop cut from page screenshot 3 | реестр 'shot3-es.webp'/705791b95443
≠ файл shot3-es.webp/43ac09f9cbd7 — пересоберите: bash demo/build-web-loop-langs.sh es
```

(The four other failures in that run belong to the copy: no `.git`, no `evidence/`, and
the bot path resolved under the copied tree.)

**Rebuilt.** Nine loops and nine posters in 3 min 17 s; both full demos in 35 s and 37 s.
Every loop kept its shape (13.0 s, 720×1560, 390 frames, 30 fps; poster = frame 389 →
540×1170), both demos theirs (35.5 s, 1,065 frames). Weights moved but stayed inside the
budgets the sweep enforces — loops EN 365 → 410 KB, RU 583 → 448 KB, the seven others
321–407 → 357–458 KB (budget 512 KB); full EN 938 → 988 KB (budget 1 MiB), full RU
1,369 → 1,173 KB (budget 1.5 MiB).

**Checked after the change.** `tools/build.py --check`: 24 files identical to a fresh
build. Sweep **2,368 / 0**. `landing-poster-frames.py`: 9 / 0 (RMSE ≈ 0.0106 — a poster
really is its loop's last frame). `landing-video-motion.py`: 408 / 0. `publish-tree.py
--check`: 109 files, 513 internal references, list complete. Published through
`tools/publish-branch.sh` to both mirrors, Pages source read back as `gh-pages/`;
`landing-live-bytes.py` **26 / 26**, and then the eleven video files were fetched from
the live host one by one and compared by sha256 — **11 / 11 identical**, nine posters too,
so the pages in the world now play the loops with seven buttons.

**What it cannot prove.** That the seventh button is the only difference between what the
videos showed and what the bot does: the chain proves the loop shows the picture the page
shows, and `tools/shots.json` proves the still shows what `menu_kb()` says — but a screen
the bot has and the page has no shot for sits outside that chain, and one does (below).
That OCR is a gate: it is evidence, and the gate is the hash. That a poster still equals
frame 389 when a loop's length changes — the frame poster rule is a constant, not a
lookup, so a 15-second loop would keep the number and pick a different picture. And that
a visitor sees the added row at all: in a 540 px poster it is 24 px tall; the proof here
is the file chain, not the eye.

**Open item for the next block.** Scene 4 of both full demos is the `/lang` screen from
`submission-kit-20261014`: it lists two languages ("Русский / English") and the caption
over it says "Works in Russian and English", while the page and the bot answer in nine.
Fixing it is a real piece of work — draw a nine-row picker in `tools/shots-gen` from the
bot's `LANG_TITLES`, add `img/shot4[-en|-ru].webp`, extend `tools/shots.json`, the
publish list (109 → 111) and the ledger — so it is named here instead of half-done.

**Files.** `demo/build-web-loop-langs.sh` (sources = `img/`, default all nine,
MISSING hint), `demo/build-web-loop-ru.sh` (header), `demo/build-full-demo.sh` (scenes
1–3 = `img/`), `demo/captions.py` (`shot_name()`, `sources` in both ledger sections, two
new check loops), `demo/captions.json` (re-stamped: 9 loops + 2 full demos, 0 problems),
nine `demo/*-web*.mp4`, nine `img/demo-poster*.webp`, two full demos, README (demo
section, the publish-list count 115 → 109, the "Editing" step that still said Pages
serves `main`), `evidence/block-20261024f-video-menu.txt`, and the skill `stars-bots-ops`:
`scripts/landing-sweep.py` (+26 checks).

## The demo's language scene showed two languages, and in Russian an English screen (24.10.2026)

**What was wrong.** Scene 4 of both 35 s demos was the one picture in the chain nobody could
check: it came from `submission-kit-20261014` (`shots_en/shot4_lang_en.png`,
`shots/shot4_answer_en.png`), not from this repository. The picture listed two languages
("Русский / English"), the caption over it said "Works in Russian and English", and the RU demo
put Russian words over an **English** screen (the file it took was the English answer shot, name
and all). The page had said nine for a while (`hero.chip3`, `shots.cap`, FAQ `q3a`), and the bot
answers in nine since `ANSWER_LANG` (22.10). The three page stills were already tied to the bot
by `tools/shots.json`; the fourth scene sat outside that chain, so nothing could notice it.

**Drawn, not borrowed.** `tools/shots-gen` now draws scene 4 the way `cmd_lang()` builds it: the
`lang_menu` message and the keyboard from `LANG_TITLES` in `SUPPORTED` order, two buttons per
row, five rows — read from the bot's i18n, not from a literal. `build_shots()` gained key 4,
`--scenes` selects what to draw, and a two-language run now *adds* to the ledger instead of
replacing it (the first version rewrote the file and would have dropped seven languages).

**Where the file lives, and one plan corrected.** The earlier note said "add
`img/shot4[-en|-ru].webp`, publish list 109 → 111". That would have published two files no page
names — exactly what the fifth publish check (same day) forbids. The scene is video-only, so it
lives in `tools/shots-gen/scenes/` and the publish list stays at **109 files**.

**Captions.** `FULL_ONLY` now says "Works in 9 languages" / "Работает на 9 языках". The string is
video-only and now agrees with the dictionary instead of arguing with it.

**The kit is gone.** `build-full-demo.sh` no longer reads an external catalogue at all: scenes
1-3 from `img/`, scene 4 from `tools/shots-gen/scenes/`, the logo from `img/logo-512.png`
(byte-identical to the kit's, checked by sha256). The build is reproducible from the repository
alone, and the sweep fails if a `KIT=`/`SHOTS=` declaration comes back.

**A gate for the fit.** Nine labels in 405 px each is a layout problem no hash can see. The
renderer now measures every button (`scrollWidth` against `clientWidth`) and exits 1 when a
label does not fit. Checked by breaking it: at 60 px «🇮🇩 Bahasa Indonesia» overflows 510 > 420 px
and the generator fails; at the shipped 30 px nothing does.

**Checked by breaking it (sweep).** In a copy of the tree the ledger's `lang_titles` was cut back
to the two old ones — two failures, each naming the file and the redraw command. Replacing
`shot4.webp` with another picture and adding a `KIT=` line produced three more (bytes, `full demo
scene 4 = its source`, `full demo scene 4 from the generator`). Real tree: **2,368 → 2,376
checks, 0 failed**.

**Rebuilt.** Both demos, 30 s and 29 s of ffmpeg: 35.5 s, 1,065 frames, 720×1560, 30 fps. Weights
stayed inside the budgets the sweep enforces — EN 988 → 996 KB (1 MiB), RU 1,173 → 989 KB
(1.5 MiB). Frames pulled from the delivered files at 28.5 s show nine buttons and the new caption
in both; the caption's every glyph is in the font the sweep checks.

**Reproducible.** A second render of scene 4, on a copy of the tree, produced the same sha256
(`fe00b7c0…`), so "redraw and restamp" cannot silently orphan the demos.

**Published.** `tools/publish-branch.sh`: 109 files to both mirrors, Pages source read back as
`gh-pages/`; `landing-live-bytes.py` 26/26; both demos then fetched from the live host one by one
and compared by sha256 — **2/2 identical** (1,020,066 and 1,013,006 bytes). `build.py --check` 24
files identical, `landing-poster-frames.py` 9/0, `landing-video-motion.py` 408/0.

**What it cannot prove.** That a viewer reads nine rows in a 720 px frame: each button is 113.8 px
on the 1080 px mockup, ~76 px in the delivered video. That a real Telegram client draws the same
flags — several desktop builds render "RU" as two letters instead. That the scene equals the live
bot screen: the chain proves the words equal `LANG_TITLES`, not that Telegram renders them the
same way. And that the burned caption is readable at phone size — that check is the eye, not a
gate.

**Open item for the next block.** None left in the video chain: all four scenes now come from
files this repository can rebuild, and every one of them has a hash in a ledger.

**Files.** `tools/shots-gen/gen_shots.py` (scene 4, `--scenes`, ledger merge, `--force-scene4`,
fit measurement), `tools/shots-gen/mockup.html` (two-button rows), `tools/shots-gen/scenes/shot4.webp`
+ `shot4-ru.webp`, `tools/shots.json` (29 entries, `lang_titles`, `lang_menu`), `demo/captions.py`
(`c4`, `scene_path()`, `scene_source()`, scene-4 sources and check), `demo/captions.json`
(re-stamped: 9 loops + 2 full demos, 0 problems), `demo/build-full-demo.sh` (all inputs from the
repo), both demos, `evidence/block-20261024g-*.txt`, and the skill `stars-bots-ops`:
`scripts/landing-sweep.py` (+8 checks).

## The pause button sat on the chat's battery icon and its menu (24.10.2026)

**What was found.** The hero control that keeps WCAG 2.2.2 honest (the loop starts by itself, so
there must be a way to stop it) was an absolutely positioned 44 px circle in the top-right corner
of the phone frame. The frame is 300 px wide on a phone, so that corner is where the drawn chat
keeps two of its own elements: the battery in the status bar and the three-dot menu in the header.
Nobody had measured what the circle covers — the block that added it wrote "the button sits in the
empty right side of the chat header, covers no text", which was true about text and wrong about
everything else.

The measurement is a subtraction, not an opinion: screenshot the video's rectangle with the button,
hide the button, screenshot again, diff. At 420 px the changed region is **65 × 65 px**, at 1440 px
**95 × 99 px**, both anchored to the frame's top-right corner — the circle, its shadow and the two
icons it covers.

**Why no gate saw it.** The sweep asserted the opposite of the truth: `video toggle in phone frame`
required the button to be *inside* the frame — the defect itself as a requirement, written when the
button was added. The browser battery measured size, labels, click, keyboard, off-screen stop and
`prefers-reduced-motion`, all of which the button did correctly. And the previous entry had filed
that corner under "what it cannot prove — the owner's eye decides": it was not taste, it was two
covered icons, and taste was never the question.

**What is on the page now.** The control left the frame. It sits under it in its own row, right
edges aligned, 10 px gap, 44 px tall, and the row keeps its height whether the button is hidden or
not — so the script that reveals it (and a page without JavaScript) shifts nothing (the CLS/LCP
battery stays at 69 checks / 0 failures). The shape is a pill with a glyph **and a word**: tested with the
glyph alone, the button read as part of the phone — an icon under a phone frame looks like the
phone's own control. The word comes from the dictionary on both sides (`vbtn.pauseShort` /
`vbtn.playShort`, nine languages: Pause/Play, Пауза/Играть, Pausa/Reproducir, Pausar/Reproduzir,
रोकें/चलाएँ, Jeda/Putar, Duraklat/Oynat, Tạm dừng/Phát, Пауза/Відтворити; the Russian play word
became «Смотреть» the same day — see «The button said «Пауза» on screen and «Остановить» to a screen
reader» below) and both sit in one grid cell, so the pill is as wide as the longer word and does not
jump when the state flips. The long
"Pause the demo video" stays as `aria-label` — the visible word is `aria-hidden`, so a screen reader
hears one name, not two.

**Proven by mutation.** A copy of the tree with the control lifted back over the frame (60 px up,
own paint layer) turns the new battery red: 6 failures — geometry (`gap=-60px`) and pixels (a
95 × 99 px difference inside the frame) at both widths. On the real page the same battery is 56
checks / 0 and the diff inside the video rectangle is **empty**, which is the only statement worth
making here: the control covers nothing.

**A gate fired on my own sentence.** The first build after the change failed `нет обещаний
возврата` — the refund policy gate — because a CSS comment said the button does not jump "при
возврате ролика". The word was harmless and the gate read it exactly as designed; the comment was
rewritten ("ролик снова в кадре"). Worth recording: the policy gates read the built page, comments
included.

**A flaky check, fixed rather than tolerated.** `nojs en: кадр стоит` compares two no-JavaScript
frames 0.9 s apart and failed on one run and passed on the next with the same build. The diff was
**10 pixels in a 4 × 5 box out of 137 100** (0.007%) — Chromium repainting a few pixels when the
decoder attaches, not motion. A zero-tolerance pixel gate that flips on its own teaches people to
ignore red, so the check now allows 40 px or 0.05% of the clip and prints the number it saw; real
motion changes tens of thousands.

**Checked after the change.** `build.py --check` 24 files identical (a clean `git clone` of the
mirror rebuilds byte-identical — verified separately today); sweep **2412 / 0** (was 2376: +36
checks, four per language); `landing-video-motion.py` **444 / 0** (was 408: the visible word in both
states); axe **0 violations on 12 pages**; a11y-extra **124 / 0**; wcag22 **43 / 0**; cwv **69 / 0**;
visual pass (18 loads, 9 languages × 2 widths) **0 problems**; external links **0 problems**; live
bytes **26 / 26**; `landing-toggle-clear.py` **56 / 0**; published to `gh-pages` on both mirrors,
Pages source read back as `gh-pages/`.

**What it cannot prove.** That a word under the frame is the shape the owner wants — the pill is a
default, the alternative (glyph alone) is measurably worse and the owner's word overrides this. And
that no later video re-cut puts something interesting in the frame's bottom-right, where the
control now sits below: the control is outside the media, so nothing can be under it, but the
bottom of the frame is where the input bar is drawn and the eye still has to like the pairing.

**Files.** `index-src.html` (markup, `.media-ctrl`, `.video-toggle`, `.vt-text`, `sync()`),
`src/locales/*.json` (+2 keys × 9), the nine built pages + `tools/lastmod.json`, and the skill
`stars-bots-ops`: `scripts/landing-sweep.py` (+36), `scripts/landing-video-motion.py` (+36 and the
still-frame tolerance), `scripts/landing-toggle-clear.py` (new, 56 checks).

## The pictures we upload to launch platforms promised five free breakdowns and two languages (24.10.2026)

**What was found.** `submission-kit/` holds the four 1920×1080 cards the owner uploads *by
file* into the forms of PeerPush, OpenHunts, LaunchIgniter and the Product Hunt gallery. They
were drawn on 15.10.2026 by a hand-assembled page, published by accident from `img/` until
24.10.2026, and then moved out of the published tree so they would stop answering at
`/img/screen1.png`. That move asked one question — "is this file part of the site?" — and the
answer was no; nothing asked what the file *says*. OCR of the bytes as they shipped:

- card 1, `t.me/UchiSamBot — First 5 breakdowns free`. The bot gives **two**: `FREE_TRIALS = 2`
  in `bot/handlers.py`, `tools/prices.json` says two, and the page says "First 2" in five
  places. Five is a promise the product does not keep.
- card 4, `Works in Russian and English` and `One bot, two languages`, over a language menu
  with two rows. The bot and all nine pages answer in nine languages; on eight of the nine
  pages that is the main argument.
- card 1's chat draws **six** menu buttons. The bot has had seven since 23.10 (`Invite a
  friend`), and the previous block redrew all 27 page stills from `menu_kb()` — the four
  cards that leave the building were not redrawn, because they are not in `shots.json`.

Both false claims had already been cut out of the **videos** on 24.10 (the 35-second demo's
outro and the RU captions). The videos were fixed; the stills that ride into other people's
catalogues were not. A launch listing is where a new visitor meets the product first, and it
was meeting a product with two languages and five free breakdowns.

**Why nothing caught it.** Every gate the workshop has is pointed at the *published* tree:
the sweep reads eleven pages, their markdown twins, the legal pages, `llms.txt`, `robots.txt`;
`publish-tree.py` reads what `gh-pages` will contain; `landing-live-bytes.py` reads what the
host actually serves. `submission-kit/` is deliberately outside all three, and the only gate
that mentioned it was `publish-tree.py`'s fifth check, which asks that every *published* file
be named by published text — these files are not published, so they were structurally
invisible. The kit's own README said "four screenshots 1920×1080, made 15.10.2026", which was
true and useless.

**What was done.**

1. `tools/submission-kit.py` — a generator, not a redraw. The four cards are composed in
   Chromium from the *same* images the page shows (`img/shot1..3.webp`,
   `tools/shots-gen/scenes/shot4.webp`), and every line of text is read from the dictionary:
   `hero.title` / `hero.sub` / `hero.chip1` / `hero.chip3` for the first card, `how.s2t`/`s2d`
   and `how.s3t`/`s3d` for the middle two, `hero.chip3` plus the nine names from `LABELS` in
   `tools/build.py` for the last. Nothing is typed by hand, so the cards cannot keep their own
   copy of a claim that later changes. The generator refuses to run if `hero.chip1` does not
   contain the number in `prices.json`, and refuses to draw fewer than nine language names.
2. `submission-kit/manifest.json` — written only by the generator: sha256 of each card, the
   exact strings drawn, the free-breakdown and language counts, and sha256 of every input
   (dictionary, prices, `build.py`, the four source images, three font subsets).
3. Seven sweep checks (section `submission-kit`, 2412 → **2419**): the four files exist; each
   is 1920×1080 by its PNG header; each matches the manifest byte for byte; the manifest
   promises the same number of free breakdowns as `prices.json` and the same number of
   languages as `LABELS`; the inputs still hash to what the manifest recorded ("the dictionary
   was edited, the picture was not redrawn" is red); and no stale claim appears in the
   manifest or in the kit's own README.
4. Two failures the generator now catches that the first version shipped: Chromium's
   `set_content` leaves `<img src="file://…">` empty, so the first set had a white phone and a
   broken logo icon while every geometry check was green — the generator now fails on
   `naturalWidth == 0` for both images. And the nine native names need glyphs the Latin
   subsets do not carry: the card is checked against the union of the declared
   `unicode-range` values (latin, latin-ext, vietnamese, the two Cyrillic names and हिन्दी)
   before it is drawn, because OCR with `eng+rus` cannot see a tofu box.

**Proof — mutations on a copy of the tree (`LANDING_ROOT`), live tree untouched.**

| control | result |
|---|---|
| manifest deleted | `FAIL kit: манифест существует` |
| one byte appended to `screen2.png` | `FAIL … screen2.png: байты не те, что в манифесте` |
| `free_breakdowns` 2 → 3 in `prices.json` | `FAIL … манифест 2, prices.json 3` and `FAIL … перерисовать: tools/prices.json`; the generator itself refuses: `словарь обещает не 3 бесплатных разбора: 'First 2 breakdowns free'` |
| `First 5 breakdowns free` appended to the kit README | `FAIL kit: … | First 5, 5 breakdowns` |
| the whole sweep on that copy | `CHECKS: 2358, FAILED: 5`, one of them `FAIL [kit]` — the section is wired in, not just importable |

Live tree afterwards: sweep **2419 / 0**, `submission-kit.py --check` 7 / 0, `landing-live-bytes.py`
26 / 26 (the site itself was not touched by this block — the cards are not published).

**What it cannot prove.** That the platforms already submitted to show the old files: PeerPush
and the others store their own copy of an uploaded image, and nothing here can reach into
their forms — re-uploading the four cards is the owner's click. That the *design* is what the
owner wants: the layout (headline left, phone right, chips on the first card, whitespace under
the short cards) is a default taken to finish the job, not a decision he made. And that four
cards are the right number for those forms — the set was four on 15.10 and the platforms ask
for one to five; keeping four was the least surprising choice, not a measured one.

---

## The stop button was set in Arial, and the only gate that could see it had to be remembered (24.10.2026)

**What was found.** The control that stops the demo sits under the frame in its own row, and
since 24.10 it carries a visible word: «Пауза» on the Russian page, «Pausa», «Duraklat»,
«रोकें» — one word per language, nine of them, 13 px, weight 600. That word was not set in the
page's typeface. `<button>` does not inherit `font-family`: the browser's own stylesheet gives
it its default (Arial), and `.video-toggle` declared size, weight and letter-spacing but never
a family — so the label was painted by whatever that machine calls Arial: Liberation Sans here,
Segoe UI on Windows, Roboto on Android. The page around it is Manrope. Ask the browser which
font drew each glyph (CDP `CSS.getPlatformFontsForNode`) and all nine pages name the system font
for exactly those two words and for nothing else on the page: en 9 glyphs, ru 11, es 15, pt 16,
hi 9, id 9, tr 13, vi 12, uk 15 — 109 glyphs in a font the site does not ship.

Before that same day the button was a 44-pixel circle holding an icon and no text, so there was
nothing to set in the wrong font. The word arrived in the commit that moved the control out of
the frame to stop it covering the chat's battery icon (c7eab08) — the defect was a side effect
of a fix that did exactly what it promised.

**Why nothing caught it.** The gate that answers this question exists: `landing-glyph-fallback.py`,
written 22.10 after the 404 page drew «हिन्दी» in a system font while every static check was green.
Its own docstring forbids folding it into the sweep — 4–6 seconds per page, and it needs a browser —
so it runs when a block remembers to run it. The last block that remembered was the no-JavaScript
block, and it printed `12 pages / 0 substituted`. That green was true and worthless: the page it
measured had no word on that button, and the battery reports *painted* glyphs — nothing painted,
nothing to report. A gate that says "zero substitutions" while the thing it is supposed to check has
not been written yet reads exactly like a gate that says "the text is ours". The geometry gates
(`toggle-clear`, `wcag22-targets`) measure boxes and never look at a face; the sweep compares page
text with the dictionaries and cannot see which file drew it; every screenshot was taken and read
for layout, not for typeface.

**What was done.**

1. `button,input,select,textarea{font-family:inherit}` after the `body` rule in `index-src.html`,
   with the reason in a comment. This is the durable half: it also covers controls nobody has
   written yet. It changes nothing that was already right — `.contact button.btn` and the form
   fields already took `font:inherit`, and the video toggle keeps its own size, weight and
   letter-spacing because a class beats an element selector.
2. The label now falls through the page's own stack (UchiSam Langs → Manrope → Noto Sans
   Devanagari) like the rest of the text. The battery reports 0 substituted glyphs on all twelve
   pages, Hindi included: those two words used to be drawn by the system's copy of Noto Sans
   Devanagari and are now drawn by the subset the page ships.
3. Ten sweep checks (2419 → **2429**), because the browser battery cannot live in the routine but
   its cause can. On each of the nine pages every `<button>` must get its `font-family` (or `font:`)
   from a top-level CSS rule whose *subject* matches that button: descendant selectors count
   (`.contact button.btn{font:inherit}` covers the submit, and the check must not accuse it),
   pseudo-classes and attribute selectors are stripped, `@media` blocks are excluded so a family
   hidden behind a media query does not pass. One global check demands 18 buttons across the nine
   pages, so the per-page checks cannot go quiet if the control disappears.

**Proof — mutations on a copy of the tree (`LANDING_ROOT`), live tree untouched.**

| control | result |
|---|---|
| previous `index-src.html` restored and rebuilt in a throwaway copy | `CHECKS: 2368, FAILED: 13`, of them nine `FAIL [<lang>] buttons: гарнитура приходит из CSS, а не из UA-таблицы \| нет правила: video-toggle` — one per language, naming the element |
| the same copy, submit button | never named — the matcher reads `.contact button.btn{font:inherit}` correctly; no false accusations |
| sweep on the fixed tree before publishing | `CHECKS: 2429, FAILED: 1` — the failed one is «публикация: живой сайт — это текущая сборка», i.e. the check that says the world still serves yesterday's build |
| sweep after `tools/publish-branch.sh` | `CHECKS: 2429, FAILED: 0` |

**Numbers on the finished build.** Glyph battery 12 pages / 0 substituted (was 9 pages / 109
glyphs); computed `font-family` of `#video-toggle`: `Arial` → `"UchiSam Langs", Manrope, "Noto
Sans Devanagari", …`; pill width before → after, identical at 420 and 1440 px: en 92→92, ru 98→98,
es 124→122, pt 123→122, hi 80→83, id 87→88, tr 106→106, vi 118→115, uk 128→126, inside a 300 px
row with no clipping and no page overflow in any of the 18 cells; `landing-toggle-clear.py` 56/0
(the pill still covers no pixel of the frame), `landing-wcag22-targets.py` 43/0,
`landing-a11y-extra.py` 124/0, axe 0 violations on 12 pages, `landing-cwv.py` 69/0 (the poster is
still the LCP element and CLS did not move), `landing-viewports-extra.py` 94/0,
`landing-render-check.py` ALL OK, `landing-visual-pass.py` PROBLEMS 0 on nine languages × two
widths, `landing-live-bytes.py` 26/26, `landing-fonts.py` 39/0, `landing-links-audit.py` 11 pages
/ 0, `landing-en-leftovers.py` 0, `landing-price-parity.py` 9/0, `landing-site-move-test.py`
8 groups / 0, `landing-poster-frames.py` 9 / 0, `landing-cross-engine.py` 60 runs / 0 in WebKit
and Firefox (429 s).

**What it cannot prove.** That the visitor saw *Arial*: on Windows the same defect shows Segoe UI
and on Android Roboto, so the honest sentence is "a typeface the site does not ship", and the
before/after crops in `evidence/visual-20261024e-buttons/` are evidence for this machine only. That
13 px Manrope is what the button should look like: the size and weight came with the pill as the
design drew it, and changing them is the owner's word, not a gate's. And that nothing else on the
page is drawn in a foreign font: the battery covers every painted glyph on twelve pages *today*,
but it is a photograph, not a hook — the sweep now catches the one cause that produced this defect
(a control with no family) and still cannot catch a family that is declared in the CSS and missing
from the woff2 subset.

## The button said «Пауза» on screen and «Остановить» to a screen reader (24.10.2026)

**What was found.** The control that stops the demo carries one visible word and a longer spoken
name. The visible word comes from `vbtn.pauseShort` / `vbtn.playShort` (nine languages), the name
from `vbtn.pause` / `vbtn.play`. Nothing required the two to agree — and in three of the eighteen
strings they did not:

| language | visible word | spoken name | visible word inside the name? |
|---|---|---|---|
| en | Pause / Play | Pause the demo video / Play the demo video | yes / yes |
| **ru** | **Пауза** | **Остановить демо-видео** | **no** |
| **ru** | **Играть** | **Запустить демо-видео** | **no** |
| **uk** | **Пауза** | **Зупинити демо-відео** | **no** |
| uk | Відтворити | Відтворити демо-відео | yes |
| es, pt, hi, id, tr, vi | Pausa/Pausar, रोकें, Jeda, Duraklat, Tạm dừng, … | the same word inside a longer phrase | yes (all 12) |

That is WCAG **2.5.3 Label in Name**, level A — the criterion written for people who drive the page
with their voice: they read «Пауза» on the screen and say «нажми Пауза», and the browser looks for a
control by that name. It finds nothing. The same mismatch is a smaller lie for anyone helping a
relative over the phone: the helper says "нажмите Пауза", the screen reader says "Остановить
демо-видео".

English passed **by luck**, not by design: «Pause» happens to be the first word of «Pause the demo
video». The Russian and Ukrainian names were written on 22.10, days before the visible word existed
(24.10, the commit that moved the control out from over the frame, c7eab08) — and the block that
added the word checked exactly one thing: that a screen reader hears one name, not two
(`aria-hidden` on the word). It never asked whether the one name contains the word people see.

**Why nothing caught it.** `axe` reports **0 violations on twelve pages** with this defect present,
and it is not a bug in axe: it has a rule for 2.5.3 (`label-content-name-mismatch`), and that rule
reads the element's *text content*. The visible word sits in `<span aria-hidden="true">` — the very
technique that gives a screen reader one clean name hides the word from the checker. The other
a11y batteries (`a11y-extra` 124, `wcag22-targets` 43) measure names and hit areas, not whether one
contains the other.

**What was done.**

1. `src/locales/ru.json` — `vbtn.pause` «Остановить демо-видео» → **«Пауза демо-видео»**;
   `vbtn.play` «Запустить демо-видео» → **«Смотреть демо-видео»**; `vbtn.playShort` «Играть» →
   **«Смотреть»**. The last one is not a11y housekeeping: «Играть» under a video is a calque of
   *play*, while every other language and every Russian player says «воспроизвести/смотреть», and the
   state it labels is a paused poster — a preview you press to watch. The pair now reads naturally
   under the triangle, and the name is the word plus what it acts on.
2. `src/locales/uk.json` — `vbtn.pause` «Зупинити демо-відео» → **«Пауза демо-відео»**; the short
   word «Пауза» and the whole play side were already consistent and are untouched.
3. **18 sweep checks** (2429 → **2447**): for each of nine languages and both states the visible
   short word must be inside the name, compared after normalisation (case, ё/е, apostrophes,
   collapsed spaces) — without it, tr «Duraklat» against «duraklat» and its own «videosunu» would
   produce false red on a correct page.
4. The CSS comment in `index-src.html` that named the old words was corrected in the same pass; it
   ships inside every built page and would otherwise have gone stale silently.

**Proof — mutations on a copy of the tree (`LANDING_ROOT`), live tree untouched.**

| control | result |
|---|---|
| ru reverted to the 24.10 words in a throwaway copy, rebuilt | `CHECKS: 2386, FAILED: 7`, of them `FAIL [ru] video toggle label-in-name (pause) \| видимое='Пауза' имя='Остановить демо-видео'` and the same for `(play)` with `видимое='Играть' имя='Смотреть демо-видео'` |
| the fixed tree, before publishing | `CHECKS: 2447, FAILED: 1` — the failed one is «публикация: живой сайт — это текущая сборка» |
| sweep after `tools/publish-branch.sh` and the CDN catch-up | `CHECKS: 2447, FAILED: 0` |
| runtime state flip on the live-intent build (Playwright, ru and uk) | playing: `state=pause`, visible «Пауза», `aria-label="Пауза демо-видео"`; after the click: `state=play`, visible «Смотреть», `aria-label="Смотреть демо-видео"`; uk: «Пауза»/«Пауза демо-відео», «Відтворити»/«Відтворити демо-відео» |

**Numbers on the finished build.** Pill width at 420 px: en 91.7 → 91.7, ru **97.8 → 118.0**
(the longer word sets the pill; both words share one grid cell, so the width does not jump between
states), uk 126.3 → 126.3 — still the widest, still inside the 300 px row with 10 px gap and an
empty pixel difference inside the frame at 420 and 360 px (`landing-toggle-clear.py` 56 / 0).
`landing-video-motion.py` **444 / 0** (the visible word in both states, all nine languages),
`landing-wcag22-targets.py` **43 / 0**, `landing-a11y-extra.py` **124 / 0**, axe **0 violations on
12 pages**, `landing-cwv.py` **69 / 0**, `landing-glyph-fallback.py` **12 pages / 0 substituted**
(the new word is drawn by our own subset, not by a system font), `landing-visual-pass.py`
**PROBLEMS 0** on nine languages × two widths, `landing-live-bytes.py` **26 / 26**, `build.py
--check` **24 files identical to a fresh build**.

**What it cannot prove.** That «Смотреть» is the word the owner wants — the accessibility half is
forced by the criterion, the choice of word is a default and one line to change back. That a real
voice-control user finds the button: the name now contains the visible word, which is what the
criterion asks, but no speech engine was driven here. And that no other control on the page has the
same mismatch: the new gate covers the one control that has a dictionary pair, the language summary
(`Language: English` with visible `English`) and the CTA were checked by hand and pass — but a future
control that puts its visible word behind `aria-hidden` will be invisible to axe and to this gate
alike, unless it is given the same pair of keys.

**Files.** `src/locales/ru.json`, `src/locales/uk.json`, `index-src.html` (comment), the nine built
pages + their md twins + `tools/lastmod.json`, and in the skill `stars-bots-ops`:
`scripts/landing-sweep.py` (+18). Evidence: `evidence/label-20261024/` (the pill in both states,
ru and uk) and `evidence/visual-20261024j/` (the visual pass this build was measured with).



## The one character the page did not set itself lived in the half of the FAQ nobody opens (24.10.2026)

**The coverage gate had an exception, and the exception was wrong.** Since 22.10 the sweep
proves that every character of visible text on all twelve pages falls inside a declared
`unicode-range` — the lock that appeared after «हिन्दी» was drawn by a system font on the
404. One character was excused by name:

    _EMOJI_OK = {0x2B50}   # ⭐ — системный эмодзи-шрифт, подмены тут нет

That comment was a guess, not a measurement. Asked the browser directly
(`CSS.getPlatformFontsForNode`), the answer to "What are Telegram Stars?" — the sentence
"Stars (⭐) are Telegram's built-in currency" in nine languages — is drawn by two fonts:
Manrope for 294 glyphs and **Noto Color Emoji** for the star. Where an emoji font exists the
page shows a colour emoji inside a Manrope sentence (different height, weight and drawing);
where it does not, a tofu box. It was the only glyph on the site that we did not ship.

**Why the glyph battery had been green.** It measures what was painted. The FAQ lives in
`<details>`; closed, its text has no boxes, `CSS.getPlatformFontsForNode` throws on those
nodes and the battery skipped them without counting. The honest line "12 pages / 0
substitutions" was measured on 2 992 glyphs of 4 899 — the same run with the FAQ open finds
the star immediately. The blind spot was exactly the size of the part of the page nobody had
opened.

**Fixed.** The parenthetical is gone from `q6a` in all nine dictionaries and from the
template: the sentence names the currency in words, and the glyph added nothing except a
foreign font. After the rebuild `grep -c '⭐'` is 0 on every page, on the markdown twins and
in `llms.txt`.

**Four gates, each proven to fail.**
1. The exemption is deleted: coverage has no privileged characters. Putting U+2192 into the
   hero → red, naming `U+2192(→)`.
2. Every `@font-face` must declare `unicode-range` (4–6 faces per page). A range-less face
   claims the whole table and makes the coverage question meaningless.
3. Character floor per page (3 500 / 13 000 / 6 500 / 260): a 27-character stub of
   `404.html` → red. A check that reads nothing is green for free.
4. The glyph battery opens all `<details>` before measuring, prints how many nodes it
   skipped, and holds a glyph floor (3 600 / 15 000 / 8 000 / 280). The same script with the
   opening line removed measures 2 992 glyphs and now says НЕДОМЕРЕНО instead of zero.

Also: no character from the emoji blocks may appear in any landing dictionary — checked at
the source, not only in the build.

**Numbers after the block.** Sweep 2 468 checks, 0 failed (before publishing only the
live-site check was red). Glyph battery 12 pages, 0 substitutions, 0 under-measured —
4 545–5 434 glyphs per language page, privacy 17 851, terms 9 483, 404 347. Visual pass 0
problems on 18 screenshots, keyboard/a11y battery 124/0, validator 0 real findings. The
submission kit was redrawn because its input dictionary changed (the gate is right: text
changed → the pictures are checked again), and its four cards came out byte-stable, which
says the star never reached them.

**Cost.** The battery is slower — it now lays out the open page — and its floor will have to
be lowered deliberately if a page legitimately loses a fifth of its text. That is the point:
it asks to look instead of answering 0.

**What it still cannot prove.** That a string added in a language we do not read is
grammatical; and that a woff2 file behind a declared range really contains the glyph — for
that the browser battery remains the only answer, which is why it now measures the whole page
instead of its visible half.

## The page the editors read was not the page the visitor sees (24.10.2026)

**The tool had three ways of showing something that is not on the page.** `tools/page-text.py` is
not part of the site — it is the eye of pass three, the pass that reads the nine languages as an
article instead of markup. It stripped tags with a regular expression, and the regex produced:

1. **Entity names instead of characters.** The footer separates "Privacy Policy" and "Terms of
   Service" with `&middot;`; the visitor sees `·`, the meaning pass read `&middot;` — three times
   per page. No gate could see it: every gate reads the built page with its own code, where
   `html.unescape` is already applied. The one reader that did not unescape was the one a human
   uses.
2. **Text the visitor never sees, printed as page text.** `#contact-ok`, `#contact-err`,
   `#contact-err-busy` and the video stop button carry `hidden` until their minute comes; the tool
   printed "Thank you! We received your message…" and "The message was not sent…" as ordinary
   sentences, glued into the same paragraph as the question "Questions or feedback?" — a reader
   could not tell where the page ends and the form's future state begins.
3. **Random granularity.** The regex matched the outermost block and swallowed everything nested
   inside it, so the whole FAQ came out as **one line of 2 176 characters** (English; 2 045
   Russian, 2 059 Hindi) and the header as one line of 300. "One block per line" — the tool's own
   contract — was untrue exactly where the block was a `div`.

**Fixed** by parsing instead of pattern-matching: `HTMLParser` with `convert_charrefs=True`
(entities become characters), subtrees of `hidden`, `.sr-only` and `.hp` skipped (screen-reader-only
and honeypot text is not page text), a line closed by the **end** of a block tag rather than its
start — so a step number stays with its heading ("1 Открой бота") instead of hanging alone — and a
space inserted between adjacent inline elements, because `<span>English</span><span>Русский</span>`
has no whitespace in the source and came out as "EnglishРусский".

Result: **51 → 101 lines** per language page, longest line **2 176 → 297** (en), 2 045 → 270 (ru),
2 059 → 319 (hi); entity names 3 → 0; the form's hidden states no longer inside the reading. The
legal pages keep their long clauses (privacy's longest is 935 characters in both versions — a
clause, not a swallowed section).

**Five gates, all in the sweep (58 checks).** Entities decoded; hidden-block text absent — and the
hidden text is taken **from the page** (`<tag … hidden>…</tag>`), so a new hidden state is covered
the day it is written; a line floor per page (90 / 12 / 70 / 60), because a tool that prints half a
page is not "empty", it is "not read"; the page's own `<h1>` must reach the output; and on the nine
language pages no line may exceed 400 characters — twice the longest honest paragraph.

**Each gate proven to fail for its own reason** (a copy of the tree through `LANDING_ROOT`, only
the tool swapped):
- the old regex tool back → **38 red**: entities (9 pages), hidden leaks (9), line floor (51 lines),
  longest line 2 176;
- `hidden` no longer skipped → **9 red**, one per language page, each naming the first leaked
  sentence;
- output truncated to 200 characters → **17 red** (floor, and the headline that never arrived);
- `h1` skipped → **10 red**, each naming the missing headline.

**What it cannot prove.** That the reading is what the eye sees: CSS is not modelled, so the video
stop button prints both of its labels ("Пауза" and "Играть") although `data-state` shows one, and
`display:none` from a stylesheet is unknown to it. Closed `<details>` are printed deliberately — the
meaning pass has to read the FAQ answers, not only the questions — which is why its output is a
reading copy, not a substitute for a screenshot; the browser batteries remain the only answer to
"what is on the screen".

**Numbers after the block.** Sweep 2 526 checks / 0 failed (2 468 before it). Core Web Vitals
re-measured after the last three blocks' text, font and video changes: 69 checks / 0 failed, LCP
192–336 ms on desktop and 1 048 ms on the throttled mobile profile, CLS ≤ 0.0055.

**Files.** `tools/page-text.py` (rewritten), `scripts/landing-sweep.py` in the `stars-bots-ops`
skill (+58 checks), `evidence/block-20261024l/` (the before/after probe against
`document.body.innerText`, per-page stats for all twelve pages, four negative controls), README (this
section and the tool's bullet).

## Every gate read the words; the marks between them belonged to nobody (24.10.2026)

**The Russian answer to the page's most-read question had a missing comma for as long as that
answer existed.** `q8a` — «Сколько времени занимает разбор?» — said "…разбор приходит прямо в чат,
как правило за 5–60 секунд". The Ukrainian text of the same sentence, translated separately, says
"як правило, за 5–60 секунд". One of the two was wrong, and the page could not tell which.

**Why no gate saw it.** Every gate counts words. Prices are compared with `tools/prices.json`, the
free count is pinned in five keys, the claim registry knows which verbs may not describe the bot,
the glyph gate knows every character against a declared `unicode-range`, the reading copy proves
which text the visitor actually sees. Between those words sit spaces, commas, dashes and quotation
marks — and nobody owned them. The sweep stood at 2 526 checks and not one of them looked at a
comma, because a comma is not a claim.

**Found by building the missing gate, not by reading harder.** A typographic probe over the nine
dictionaries (1 116 strings) and the twelve visible pages returned exactly one violation — the
comma. Everything else was already clean: no double spaces, no space before a mark, no `...` where
the ellipsis belongs, no hyphen between digits in place of the en dash, no unpaired «ёлочки» or
brackets, no straight quote in a language that uses guillemets.

**Fixed.** The comma is in `src/locales/ru.json` (`q8a`); the rebuild moved `ru/index.html`, its
markdown twin and `tools/lastmod.json` and nothing else, and `tools/build.py --check` reproduces all
24 generated files.

**The gate — 22 new sweep checks.** Nine of them read a whole dictionary each, twelve read a page
through `tools/page-text.py` (the same reader pass three uses, so template literals, the 404 and
both halves of the bilingual legal pages are covered, with the quote rules chosen by the script of
each line), and one floor check refuses to pass if the dictionaries were not all read. The classes
are the mechanical ones above plus a short, deliberately unambiguous list of Russian and Ukrainian
introductory phrases that always take a comma. "например" and "кстати" are **not** in that list: in
parentheses and after a dash they need no comma, and a gate that cries on correct text stops being
read.

**Each class proven to fail on a copy of the tree** (`LANDING_ROOT`, no site file touched): a double
space in the English `nav.how` → red, naming the key; the comma removed from the Russian dictionary
→ red, naming `q8a`; the same sentence reverted in the built page → red on the page check with the
sentence quoted. Three reds, each naming its own string.

**What it still cannot prove.** Grammar: cases, agreement, word order, and the commas of
constructions the short list does not name. Nor whether a translation means what the English means.
It is a second pair of eyes on the marks, not a proofreader.

**Numbers after the block.** Sweep **2 548 checks / 0 failed** (2 526 before; the only red before
publishing was the live-site check, which compares the published page with the tree). 1 116
dictionary strings and 12 pages are read for punctuation on every run.

**Also in this block.** The *Editing* note above still claimed that scene 4 of the full demo comes
from `submission-kit-20261014`. That open item was closed the same day (block g) and
`demo/build-full-demo.sh` has read `tools/shots-gen/scenes/shot4[-ru].webp` since; the note now says
what is true, and the old wording sits under it with its date instead of being deleted.

**Found, and not fixable here — the words belong to the bot, not to the site.** *(Superseded the same evening,
18:01 — the source was fixed and the pictures were redrawn; see the next entry. The text stays as it was
written, because it records what the site could and could not do on its own.)* The first screenshot
on every language page is the bot's own greeting, drawn from `bot/i18n.py` / `bot/i18n_extra.py`. In
three of the nine languages that greeting still promises that the bot *solves*: pt "resolvo
problemas passo a passo", hi "सवालों को कदम-दर-कदम हल करता हूँ", tr "soruları adım adım çözüyorum" —
the exact claim this site removed from its own step 3 and its meta description in the previous block
(the claim registry bans those very verb forms). The Turkish menu button is labelled "🧠 Soruyu adım
adım çöz" where the other eight say *break down*. So the page says "teaches, does not solve" and its
own picture shows the bot saying the opposite. The picture is a quote, and a quote cannot be
corrected on the site without correcting its source: three lines in the bot, then
`gen_shots.py --langs pt,hi,tr --apply --stamp`, three loops rebuilt and a sweep. The bot's service
restart is the owner's command — cron cannot restart systemd — and the bot lives outside this
repository, so the change is reported rather than made here.

**Files.** `src/locales/ru.json`, `ru/index.html` + `ru/index.html.md` (build), `tools/lastmod.json`,
`scripts/landing-sweep.py` in the `stars-bots-ops` skill (+22 checks), `evidence/block-20261024m/`
(the nine reading copies, two typographic probes, the negative-control run).

**The picture's words were repaired at the source; one button is still left** (24.10.2026, evening)

The paragraph above ended with "the change is reported rather than made here". Half an hour later the three
lines were fixed where they live — in the bot's own dictionaries, `study-bot` commit `064051c` ("the greeting
promised to solve problems; the product explains them step by step") — and the site stopped quoting the old
text: `python3 tools/shots-gen/gen_shots.py --langs pt,hi,tr --apply --stamp` redrew nine screenshots in the
three languages, the three web loops were cut again from those screenshots (18:00), and
`demo/captions.json` / `tools/shots.json` were restamped. Sweep **2 548 checks / 0 failed**.

What that fix did not reach: **the Turkish menu button** — the keyboard drawn in the first and third screenshots
still reads "🧠 Soruyu adım adım çöz" where the other eight say *break down / analizar / розібрати*
(`bot/i18n_extra.py`, the `solve` key of the `tr` block, line 218). The greeting was fixed, the button was not,
so the Turkish page still carries a picture of a button that promises to solve — the one claim the page itself
denies in `q10a`. The fix is one line in the bot, `gen_shots.py --langs tr --apply --stamp`, then the Turkish
loop rebuilt. Not made here: the bot lives outside this repository.

And the live bot is still running the pre-fix code: its process started at 12:14, the dictionaries were written
at 17:58. Until the owner restarts the unit (`systemctl --user restart study-bot.service` — cron cannot restart
systemd), a Portuguese, Hindi or Turkish student who presses Start gets the old greeting while the page above
the button shows the new one.

**Zoom was measured on three of nine languages, and nobody asked whether the text survived it** (24.10.2026)

Found: the WCAG 1.4.4 block of `landing-a11y-extra.py` zoomed three pages — en, ru, hi, the ones the author
reads himself. The other six languages were never zoomed, though 640×512 is exactly a 1280×1024 laptop after
two Ctrl+'+' presses, and a long translation is what breaks first. The block also asked only the easy question:
"does the page scroll sideways". A box with a fixed height and `overflow:hidden` never scrolls — it loses words
silently, and no battery asked about that.

Did: `ZOOM_LANGS = PAGES` (11 pages instead of 3) and a second question on every page — `zoom200 <page>:
nothing cut off` reads every element whose own content is taller or wider than its box, skipping `.sr-only` /
`.hp` (they clip themselves on purpose), the horizontal slider, and `text-overflow: ellipsis` (a design
decision, not a loss).

Numbers: 33 zoom checks (11 pages × 3), battery **151 checks / 0 failed** in 42 s. Teeth proven on a mutated
copy of the site: the vi page — a language that had never been zoomed — got a 24 px box holding 77 px of text
and one unbreakable word. `zoom200 vi: nothing cut off` FAIL (`DIV 640x77>640x24`), `zoom200 vi: no h-scroll`
FAIL (548 px), and the older reflow gate fired too (868 px at 320). The other ten pages stayed green: the gate
names the page that broke instead of painting the whole battery red.

**Also measured, nothing to fix** (24.10.2026): every `<img>` on all 12 pages — 125 of them — was compared with
its file. The `width`/`height` attributes may be a display size (a 1080×2340 screenshot is declared 540×1170 for
2× screens, a 2400×600 badge is declared 240×60), so the question is not equality but shape: 0 distorted, every
`srcset` descriptor equals the real pixel width of its file, and all nine preview cards plus the legal one are
1200×630 — the 1.91:1 crop a chat client makes.

**Files.** `scripts/landing-a11y-extra.py` in the `stars-bots-ops` skill (+27 checks),
`evidence/block-20261024n/` (the mutated run, the real run, the zoom and geometry probes), `README.md` (this
entry and the superseded note above).

## The only two fields on the page were invisible until you typed in them (24.10.2026)

**What was wrong.** The email field and the message box — the whole of the contact form — were white
on a white card, outlined in `--line` (#E3EAF7). Against the white on both sides of that line the
contrast is **1.21:1**; WCAG 1.4.11 asks for 3:1 for "visual information required to identify user
interface components and states". The border is the only thing that says *you can write here*, and it
was as good as absent. What a visitor actually saw was the placeholder, at 4.6:1 — and a placeholder
disappears with the first character typed. Between those two moments the form was two unlabelled
blank spaces on a white card, on a page whose background is #F7FAFF.

**Why no gate saw it.** Every contrast gate on this site measures **text**: axe's `color-contrast`,
the 4.5:1 rows in the sweep (`.btn`, `p`, the active chip), the AA battery. `landing-wcag22-targets.py`
measures how big a target is, `landing-env-prefs.py` measures forced-colors, `landing-glyph-fallback.py`
measures whether a glyph exists. The string `1.4.11` appeared in none of them. The gate that would
have caught this is one nobody wrote, because a border had never been asked a question.

**Fixed.** `index-src.html`, one declaration: the fields' border moves from `--line` to **#8490A6** —
the page's own `--muted` (#50617F) at 70 % over white, **3.22:1** against the field and 3.08:1
against the page background. Width stays 1 px, radius stays 12 px, the focus state (outline + border
in the brand blue, 5.13:1) is untouched, so the layout does not move by a pixel. The build rewrote the
nine language pages, their markdown twins and `tools/lastmod.json`; `tools/build.py --check` reproduces
all 24 generated files.

**The gate — 19 new checks in `landing-a11y-extra.py`.** Section F walks every page that carries
`#contact-form` (nine of the eleven) and asks, per field, whether the boundary is *identifiable*: a
border at ≥3:1 against both the field's own fill and what is outside it, or a fill that separates it
from its surroundings at ≥3:1. Each check prints the three ratios it measured, so a red names the side
that failed instead of the element. A floor check refuses to pass unless all nine pages were asked —
the same floor the zoom block needed after it turned out to have measured three languages of nine.

**Each side proven to fail.** On a copy of the tree with the old border put back (`LANDING_ROOT`, no
site file touched) the battery goes **170 checks / 18 failed** — one per field per language, each
naming the page, the field and `border/fill=1.21 border/outside=1.21`. The real tree: **170 / 0 in
45 s**; axe stays at 12 pages / 0 violations.

**What it cannot prove.** That 3.22:1 is *enough* to see the box in the sun on a cheap phone — the
standard sets a floor, not a guarantee, and the owner's eye still decides whether a line or a fill is
the right shape for this form. Nor does it say anything about the contact card's own 1.21:1 outline:
the card is decoration, not a control, and stays as designed. And it reads only elements the page
marks as form fields — a future `<select>` or file input is covered the day it appears, a custom
`div` pretending to be one is not.

**Numbers.** Sweep **2 548 / 0** after publishing; accessibility battery **170 / 0** (151 before
this block). Live bytes re-read: `/` and the eight language pages serve this build.

**Files.** `index-src.html`, `index.html` + the eight language pages + their `.md` twins +
`tools/lastmod.json` (build), `scripts/landing-a11y-extra.py` in the `stars-bots-ops` skill
(+19 checks), `evidence/block-20261024o/` (the real run, the mutated run, the after-measurement,
the contrast table).

## The particle took the comma with it, and nobody was asked about it (24.10.2026)

**What was wrong.** Two sentences, printed on the page since the language pages were generated
(15.10.2026) — one in the pricing answer, one in the contact card:

> Подписки и автосписаний нет — платишь только когда сам решишь.
> Используем твой e-mail только чтобы ответить на обращение.

Both are subordinate clauses («когда сам решишь», «чтобы ответить») behind a subordinating
conjunction that has an intensifying particle in front of it («только»). Russian punctuation puts the
comma **before the particle**, not before the conjunction — gramota.ru, справочная служба: «если
перед подчинительным союзом стоят усилительные частицы как раз, только, лишь, исключительно и т. п.,
то запятая перед ними ставится вопреки интонации». Ukrainian puts it in the same place: «частки
навіть, тільки, лише, хіба що перед підрядними сполучниками не відділяються» (the particle does not
detach from the conjunction, so the comma stands before it — Український правопис §5.5 lists only
не, і, то as comma-cancelling). Neither sentence had a comma at all, in either language.

What makes it a defect rather than a style: the same file already does it right twice — «Бот
объясняет каждый шаг и его смысл, чтобы ты мог самостоятельно решить похожую задачу», «…показывает
каждый шаг и правило за ним, чтобы следующую задачу ты решил сам». The dictionary contradicted
itself, and the wrong pair sat in the **pricing answer** (the most-asked question on the page) and in
the **contact card** (the last thing a person reads before writing to us).

**Why no gate saw it.** The typography block added earlier the same day reads punctuation: double
spaces, a space before a mark, `...` instead of `…`, a hyphen instead of a dash between numbers,
unpaired guillemets, a straight quote in ru/uk, and a deliberately short list of introductory words.
It also said what it does not do: «ЧЕГО НЕ ДОКАЗЫВАЕТ: запятые в оборотах, которых нет в списке». A
subordinate clause was exactly such an оборот. The word-level gates (claims, prices, numbers,
glossary) read words; the meaning pass reads meaning. One comma, in two of the nine languages, sat
between them.

**Fixed.** Four strings, one character each: `src/locales/ru.json` (`q6a`, `contact.note`) and
`src/locales/uk.json` (`q6a`, `contact.note`). Nothing else moved — the build rewrote `/ru/`,
`/uk/` and their `.md` twins, and `tools/lastmod.json` moved exactly two dates. No English text, no
layout: a comma is not a reflow.

**The gate — one new class, plus a self-test so the class cannot rot.** `_particle_no_comma()`: for
every «только/лишь» + «когда/если/чтобы/чтоб/пока/где» in Russian and «лише/тільки» + «коли/якщо/
щоб/поки/де» in Ukrainian, the character before the particle must be a punctuation mark. Places where
the particle follows a conjunction («и только если», «но только если» — both live in privacy/terms)
are skipped on purpose: there the clause boundary is held by meaning, not by letters, and a red there
would be false. The class runs inside the nine dictionary rows and the twelve page rows; the new
2 549th check is a self-test — «Платишь только когда сам решишь» must come back red and «Платишь,
только когда сам решишь» green, in both languages — so that a later "improvement" to the pattern
cannot leave the gate green forever.

One more thing changed in those rows: the page loop used to pick its rules by *script* (`ru` if the
line had Cyrillic, else `en`), so Ukrainian pages were measured with **Russian** rules. Pages now
carry their own language — that is how «лише коли» on `/uk/` gets caught by the page row and not only
by the dictionary row.

**Each side proven to fail.** The same tree before the fix: **2 548 checks / 4 failed** — the ru and
uk dictionary rows and the ru and uk page rows, each naming its own sentence. After the fix, before
publishing: 2 549 / 1, and that one was the publishing gate saying the live site still served
yesterday's bytes. A mutated copy (`LANDING_ROOT`, old text put back into both dictionaries and both
pages) reproduces the same four typography failures next to copy-only artifacts — no `.git`, no
`evidence/`, no study-bot path — 11 failed there, 4 of them the defect.

**What it cannot prove.** That a comma before the particle is what a reader *wants* — the norm is
normative, and an ear may still prefer a rewording («платишь только тогда, когда…»); that call stays
with the owner. Nor does the class cover the other subordinate clauses in these files: «который»,
«если», «когда» without a particle are read only by the human pass, and the legal pages' «и только
если» / «но только если» are still judged by meaning. It also reads Russian and Ukrainian only.

**Numbers.** Sweep **2 549 / 0** after publishing; `tools/build.py --check` 24 / 24;
`publish-tree.py --check` 109 files, 513 internal links, list complete; live bytes **26 / 26** match
the tree; the `gh-pages` branch updated on both mirrors and the Pages source read back as
`gh-pages/`.

**Files.** `src/locales/ru.json`, `src/locales/uk.json`, `/ru/index.html`, `/uk/index.html` + their
`.md` twins + `tools/lastmod.json` (build), `scripts/landing-sweep.py` in the `stars-bots-ops` skill,
`evidence/block-20261024p/` (the pre-fix run, the post-fix run, the mutated copy, the final run).


## Every language was checked alone, and nobody asked whether the nine still agreed (24.10.2026)

**What was searched.** The site is not short of gates: 2 549 checks on the markup and the nine
dictionaries, axe on 12 pages (0 violations), the local vnu validator (no real findings — 126 known
false «trailing slash on void elements»), live bytes byte-for-byte against the tree. Every one of
those reads a language **by itself**: does `ru` have the right keys, does `hi` carry its own
shots, does `tr` price the pack at 120 Stars. Not one of them ever asked the question that a
translated page actually fails: *do the nine still say the same thing as each other?*

That is how two of this project's worst defects lived: «First 5 breakdowns free» on the launch
pictures while the page said two, and «çözen» (solves) in the Turkish description while the product
sold the opposite. Each language was individually valid and beautiful; only the comparison was
missing.

**What was measured before touching anything** (read-only): numbers across the nine dictionaries
(no drift); the DOM skeleton of the nine pages against the English one (390 elements, identical);
`llms.txt` page titles against `meta.title` (9 of 9); the product unit's terminology inside each
language — `desglose`, `pembahasan`, `phân tích`, `çözüm`, `हल` each hold one word for the breakdown,
with `solución`/`lời giải` appearing only where a pupil's own solution is meant; the first phone
screen upright (390×844 and 360×640, all nine — the hero button sits fully above the fold
everywhere); and the published site opened in a real browser as a visitor, all nine languages.
Nothing on the site was wrong.

**What was wrong.** The new browser battery itself. On a deliberately wrong address it did not turn
red — it **crashed**: `document.querySelector('details.lang-dd')` is `null` on a page that is not
ours, and `.open = true` threw. A gate that falls over instead of reporting has the same defect as a
gate that is always green: it cannot tell «everything is fine» from «I could not look». It was found
by the negative control, not by the happy path — which is the whole reason the negative control is
run.

**Fixed.** `landing-live-runtime.py`: all four interactive checks now look for the element and return
«not opened» instead of throwing, and the address is an environment variable (`LANDING_LIVE_BASE`)
so the wrong-address control is reproducible. On a wrong address the battery now reports **121
checks / 93 failed, exit 1**; on the real site **121 / 0**.

**The gate — a new class: parity of the nine languages** (sweep 2 549 → 2 571). Three things, each
of which has already gone wrong once in this project in another form:

1. **Numbers.** «2 free breakdowns», «30 Stars», «5–60 seconds» are not translated. A number that
   lives in one language only is either a translation slip or a promise the other eight do not make.
   Comma decimals are normalised (`5,5` ≡ `5.5`), and the rule carries a three-case self-test —
   equal sets pass, a missing number is caught, a decimal comma is not a difference.
2. **Skeleton.** The nine pages come from one template, so the sequence of elements must be the
   same. A section that disappears in one language is a template/build error, not a translation
   one — exactly what a hand-edit to `/es/` produces. Attributes that *must* differ by language
   (href, lang, hreflang, alt, aria-label, content, src, poster, id, name, action) are excluded, or
   the gate would be red on every language by design. Self-test: a lost `<footer>` must be caught, a
   changed `href`/`lang`/`alt` must not.
3. **`llms.txt`.** The file written for machines is not generated from a template field the build
   validates per language: its page titles are hand-written, so a rewritten headline can leave an
   agent quoting the old name. Now each of the nine titles must end with that language's `meta.title`.

**Each side proven to fail.** A copy of the tree (`LANDING_ROOT`, no `.git`, no `evidence/`), three
breakdowns at once: «30 Stars» → «35 Stars» in `tr.json` with an honest rebuild; the `#parents`
section cut out of `es/index.html`; the Hindi title in `llms.txt` rewritten. Result: the numbers
class named **eight languages missing 35 and Turkish missing 30** — the drift is named, not just
sensed; the skeleton class named the exact vanished subtree («нет 28
(main[tabindex=-1]>section.sec)»); the `llms.txt` class printed both strings side by side. Full log
in `evidence/block-20261024q/negative-three-mutations.txt`.

**Two new batteries**, both with their own negative control, both in the `stars-bots-ops` skill:

- `landing-live-runtime.py` — **121 checks**: the published site opened as a visitor on all nine
  addresses (HTTP 200, console errors, failed requests, 4xx/5xx, broken images, video ready and
  sized, the language's own font in `loaded`, eight switcher links, `html lang`, canonical, the
  language menu, the FAQ, the sticky button after scrolling), plus `robots.txt`, `sitemap.xml`,
  `llms.txt` and `og-en.png`. The bytes could match the build and the page still not work; this is
  the check that would say so. On a wrong address: 93 failed.
- `landing-first-screen.py` — **18 checks**: the hero button fully above the fold on 390×844 and
  360×640 for all nine languages, with the heading, lead and video positions printed. Earlier
  batteries only measured the phone **on its side** (844×390) for three languages. That is not how
  the traffic arrives: Telegram, upright, sometimes a 360-pixel-wide budget phone, and a longer
  language (Hindi, Vietnamese) pushing the button one line lower is enough to lose the tap. With a
  heading pushed 600 px down, the battery reports 2 problems and exits 1.

**What it cannot prove.** Parity proves that nine languages agree — not that any of them reads
well; a native ear, and the owner's, are still the only instrument for that. It says nothing about
numbers that live in the page rather than in a dictionary: `prices.json`, `answer-time.json` and the
bot itself have their own gates. And only the first screen was measured, not the page behind it.

**Numbers.** Sweep **2 571 / 0**; `tools/build.py --check` 24 / 24; `publish-tree.py --check` 109
files, 513 internal links, list complete; live runtime **121 / 0**; first screen **18 / 0**; axe
**12 pages / 0**; vnu: no real findings. The site itself was not changed by this block, so nothing
was published — the publication checks inside the sweep are green, which means `gh-pages` already
carries the current build.

**Files.** `scripts/landing-sweep.py`, `scripts/landing-live-runtime.py`,
`scripts/landing-first-screen.py` in the `stars-bots-ops` skill; `evidence/block-20261024q/`
(the run before, the three-mutation copy, the live runtime positive and negative, the first-screen
positive and negative, and the four probes that searched the site before any gate was written).
