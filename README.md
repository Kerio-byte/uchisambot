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
- `tools/page-canary.json` — the per-page measurement (28.10.2026): for each of the twelve pages,
  which classes of breakage a named catcher caught, with the catcher's sha and the date. Written by
  `landing-page-canary.py` (`stars-bots-ops`), which breaks one page at a time and requires the
  catcher to name **that** page; judged by `landing-page-canary-ledger.py` in six clauses (pages on
  disk, the static catcher's code, **every** catcher's code from `catchers`, a catch per page, no
  missed cell, something breakable on every page), and the sweep fails if the ledger is older than a
  catcher's code or a page on disk is missing from it. **Seven** classes since 28.10.2026: four of
  markup (`relative-dead`, `missing-anchor`, `duplicate-id`, `self-link-dead`, catcher
  `landing-links-audit.py`), three of layout (`overflow`, catcher `landing-page-overflow.py` — a
  `200vw` block in the body; `contrast`, catcher `landing-page-contrast.py` — a paragraph at 1.04:1;
  `first-screen`, catcher `landing-page-fold.py` — a `100vh` block in the body, which pushes the
  title and the primary button past the fold), all three visible only to a browser. The measurement
  is now 84 cells (7 × 12 pages): 81 caught, 3 not applicable (`404.html` has no relative links,
  anchors or ids). Added because the sum of checks could not answer whether any page was unread,
  and two pages were.
- `tools/publish-tree.py` — the one list of what counts as the site (107 files; this line said 109
  until 28.10.2026 — two badge files left together with their platforms, 109 → 108 → 107), and `--check`
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
kit build (13.0 s, 720×1560, x264 veryslow crf30; poster = frame 389 → 720×1560
WebP, the loop's own resolution since 26 Oct 2026 — a 540-wide poster was stretched
1.56× by every 3× phone, see the diary entry "The still frame was softer"). **Sources are the page's own screenshots** (24 Oct 2026): `img/shot2[-<lang>].webp`
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

Printing (added 25.10.2026): until this block the page had no print rules, and a printout of
it was a table of contents — an A4 sheet carrying `01 How it works`, `02 What's inside`, …
with blank paper under every heading (8 sheets, 6 of them nearly empty on English). Three
screen-only behaviours caused it, and none of them has a condition on paper: the reveal
(`html.js .rv{opacity:0}`) waits for a scroll that a sheet never performs, so 37 of 37 blocks
stayed transparent; the browser prints without backgrounds, so the white text on the dark band
(`#0E1526`) and on the brand-blue buttons printed white on white; and the phone shots sit in a
horizontal rail (1 771 px of content in a 678 px window), of which only a third of the first
screenshot reached the paper. Closed FAQ answers do not print at all — the inside of a
`<details>` is the browser's to hide and CSS cannot reopen it. The `@media print` block at the
end of the stylesheet releases the reveal, turns the band and the buttons into dark ink on
white, hides the screen furniture (header menu, sticky bar, skip link, video toggle, the 648 px
video frame), lays the three shots out as one row, underlines links, prints the bot address
once in the footer (`t.me/UchiSamBot` — a button cannot be pressed on paper) and keeps cards
and the footer from breaking across sheets; a four-line `beforeprint` handler opens every FAQ
answer and `afterprint` closes it again (the answers are the useful half of a kept printout).
Measured: 7–8 A4 sheets per language, no blank sheet, no light-on-white text, no
`position:fixed`. The footer also loses its screen spacing on paper (`padding:10px 0 0;
margin-top:20px` instead of 44/56/34 px): with the screen numbers the block stands 274 px tall,
does not fit the 241 px left on the sheet and moves away whole, so the eighth sheet carried the
footer and nothing else in Russian (25.10.2026, entry below). Covered by `landing-print.py`
(147 checks: nine languages × layout assertions + the PDF's own text, answer text and page
count) with a control that strips the block and turns 111 checks red; eight static markers hold
the same strings in the sweep. Where a section heading lands and whether the footer stands alone
on the last sheet is `landing-print-main.py` (213 checks, 25.10.2026).
Beyond A4 portrait (added 25.10.2026): all four batteries printed one paper — `format='A4'`, no
`landscape` argument, no other size — while the print dialog offers Letter beside A4 and a
landscape switch, so both were one click away and neither had been looked at. On **A4 landscape**
the page printed **11 sheets in all nine languages and sheet 5 carried exactly zero characters**
(not almost empty: no text at all), because the phone strip takes the full text width and a
screenshot's height is 2.17 of its width: 324×730 px on a landscape sheet whose box is 703 px tall,
so `figure.shot{break-inside:avoid}` moved each phone to a sheet of its own and the captions
trailed to the next one. Fixed by printing the phones at one size on paper —
`.shots{max-width:678px;margin-inline:auto}` inside `@media print`; 678 px is exactly the strip's
width on portrait A4, so a wider sheet no longer enlarges it, and it stays centred under the
section heading, which is centred. Landscape went 11 → 10 sheets, no sheet is empty of text, the
thinnest sheet in any language carries 110 characters; portrait A4 and Letter did not change by a
single character per sheet. Letter prints 8 sheets where portrait A4 prints 7 (en/es/pt/hi/tr/vi)
and A5 prints 12–14 — measured, budgeted in `tools/print-papers.json`, and not treated as a defect.
The text column had no cap at all, which only showed on a wide sheet: `main` is unbounded and the
inner `.wrap{max-width:1060px}` is 280 mm — wider than every paper the dialog offers — so on A4
landscape the prose ran the full 277 mm of text area and its longest line reached **260 mm (ru),
244 mm (en)**, against 178 mm on portrait A4. Now
`@media print{main,body>footer{max-width:210mm;margin-inline:auto}}` — the paper column is never
wider than the sheet's short side. Portrait A4 (190 mm), Letter (196) and A5 (128) are untouched by
arithmetic and by measurement (same sheets, same characters per sheet); landscape lines fall to
191.7–199.7 mm, and eight languages stay at 10 sheets while Indonesian takes 11 (the extra sheet
carries 480 characters — real text, not a footer). The rule is held by the line-width check below
and by a static marker on each of the nine pages.
Gate: `landing-print-paper.py` (**969 checks**, 9 languages × Letter / A4 landscape / A5), whose
control `--mutate railwidth` turns **18 checks red** and `--mutate colwidth` turns **7 red** (the
languages whose line actually reaches the edge; `hi` and `uk` never did, which is why they stay
green).
The three pages outside the generator print under their own rule: `privacy.html` and
`terms.html` lose the skip link and the footer badge strip (three lazy pictures that never
reach a print layout — a 46 px hole on the sheet), keep a section heading on the sheet with its
text, and are compacted on paper (paragraphs 9 px, lists 10/4, `h2` 20/8; on `terms.html` 7 px,
10/3, 16/7) so that the footer does not take a sheet of its own; `404.html` prints as one sheet
with its button as dark ink.
All three declare **`@page{margin:6mm}`** (25.10.2026, evening): without it the top line of every
sheet sat at −1.2 mm — above the paper's edge, with the tops of the letters gone — and the sides
5.3 mm from the edge, because page margins are the only thing that repeats on every sheet (a
container's padding guards the first sheet's top and the last one's bottom, nothing in between).
Six millimetres is the cheapest margin that puts a letter beyond 4 mm: after it the top gap is
4.8 mm, the sides 11 mm, the bottom 5.6 mm. 8 mm and the landing's 12/10 mm were measured and
rejected — on A5 they hand the policy a sheet carrying 88 characters, and 12/10 costs two sheets
on A4.
Measured on **all four sheets the dialog offers** — A4 portrait, Letter, A4 landscape, A5 — by
`landing-print-pages.py` (**391 checks**, 12 page × paper pairs, budget
`tools/print-pages-papers.json`): page count from `pdfinfo` against the text chunking, ink per
sheet, no sheet ending with a heading or with a two-word fragment, no non-final sheet under 200
characters, the footer not alone (last-sheet characters ÷ footer characters > 1.20), no printed line
wider than 210 mm, no word nearer than 4 mm to any paper edge and sheets within budget; its
controls `--mutate` turn **22 checks red**, `--mutate colwidth` **2 red** (the two legal pages in
landscape, where the line reaches 274.8 mm without the `.wrap` cap) and `--mutate nopage` **8 red**
(privacy and terms on all four papers; `404` stays green at 27–85 mm from every edge, which is the
truth — the defect was never there). Their longest printed line is 199.8 mm on A4, 205.4 on Letter,
206.1 on landscape and 137.6 on A5 — the column is theirs already, so the landing's column rule was
measured there and deliberately not added: it would have cost Letter/privacy a sheet of its own
(7 → 8, the eighth the footer alone); the landing's *margins* are not the landing's *column* and
were added, at 6 mm rather than 12/10. Contrast on the same pages is
`landing-print-contrast.py` (3 543 checks: every element with its own text on twelve pages in
Chromium, Firefox and WebKit, against the white sheet and against its own plate).
Without JavaScript the FAQ still prints closed — that limitation is the browser's, not a hidden
promise.

Footer: one centered "Featured on" strip of official launch-platform badges — Fazier,
StartupBase, ShowMeBestAI, LiftOff, Startup Fame, Aura++ and the LiftOff "day" award.
Uniform 46 px height (40 px on small screens), lazy-loaded official assets served from this
repository (`img/badges/`, seven files, byte-identical to what the platforms serve — see
"the last thing the page asked of other people's servers", 23.10.2026), links open in a new
tab with `rel="noopener"`. **Every** badge link points at our own page on the platform —
no exceptions, because a badge that lands on a front page proves nothing. `privacy.html` /
`terms.html` carry the required LiftOff + Startup Fame badges in the same style. 25.10.2026,
two removals and one repair: LaunchIgniter's badge left the hero (the platform deleted our
product page, the link led to "Product Not Found"); OpenHunts Club's badge left the strip
(its catalogue of 3 837 projects has no page for us, and the badge pointed at the front
page, where nothing could be checked); and ShowMeBestAI's badge was re-pointed from its
front page to our page there, which its own sitemap had listed all along (see "the footer
promised seven platforms", 25.10.2026).

> SUPERSEDED (23.10 → 25.10.2026), kept for history: the strip carried eight badges, and
> the paragraph read "Badge links point at the platform's product page where one exists
> (Fazier: `fazier.com/launches/uchisambot-study-helper`)" — the words "where one exists"
> were the hole: two badges pointed at front pages, and no gate asked whether the product
> was on the platform at all.

> SUPERSEDED (22.10 → 23.10.2026), kept for history: until 23.10 every badge but Startup
> Fame was a hotlink to the platform's own asset, and the Fazier one had to be written as
> the canonical single-slash path `fazier.com/api/v1/public/…`. The 23.10 pass moved all
> nine badges into `img/badges/` and removed every third-party badge URL, so no request
> leaves a page for a platform until the visitor clicks.

Badge strip shape (22.10.2026): eight badges on a 1440 screen used to wrap 6+2 — the
two-badge second row sat centered under the first and the strip read as unfinished. The
strip is capped at `max-width:780px` (the four widest badges total 714 px, the fifth no
longer fits), so it formed two even rows of four; on a 420 screen it was two per row.
25.10.2026, after OpenHunts left: seven badges, four then three, centered — the 780 px cap
now buys 4+3 on a desktop and 2+2+2+1 on a phone instead of 4+4. The strip stays a "row of
four" by construction; whether seven should become six (drop the duplicate LiftOff launch
badge, which leads to the same page as the award) or eight again (a real eighth platform)
is the owner's call, not a layout accident.

Earned award badge (21.10.2026): on 19 Oct 2026 LiftOff placed UchiSamBot (Study Helper)
#1 in its daily competition and issued a proof badge for it. It is the platform's own
asset, stored locally like the rest — `img/badges/liftoff-day.webp`, 360×120 — and
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
pins the local path on all nine pages plus the file itself; since 23.10 it is simply one of
the nine local files — the first one that had to be moved.

Badge failure fallback (21.10.2026, still in place): when the badges were hotlinks the
platforms' edges throttled — a fresh 9-language × 2-viewport capture found at least one
badge request with `naturalWidth=0` in 5 of 18 renders, and an 18-page browser smoke run
saw `startupfa.me` fail on 10 pages while a single request to the same URL returned 200. A
visitor on such a render saw the browser's broken-image glyph plus alt text. Each of the
nine badges (one in the hero, eight in the footer) carries
`onerror="(this.closest('a')||this).style.display='none'"`: an asset that cannot load
removes its own link from the strip and the remaining badges reflow, and the sweep asserts
that handler on all nine language pages. Since 23.10 the files come from our own host, so
the handler is belt-and-braces rather than the only line of defence; the browser smoke now
cuts our own badge files at the network layer instead of the platforms' — all nine blocked
means nine links hidden, no broken icon and no horizontal overflow, while one blocked file
hides exactly that link and leaves the other eight loaded.

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

Privacy policy vs the site's real data flows (21.10.2026, rewritten 23.10.2026): the
policy named GitHub Pages and Web3Forms only, while every page then loaded nine hotlinked
badge images from eight launch platforms — the visitor's browser asked each platform for
the picture, so that platform saw the visitor's IP address and the site it came from — and
the contact form keeps a token in `sessionStorage`, which the policy never mentioned.
Section 7 of `privacy.html` (EN and RU) lists the eight platforms with their domains, says
what the platform sees and that the rest is covered by its own policy, states that the site
itself sets no cookies and runs no analytics, advertising or third-party scripts, and
explains the session token; "Last updated" moved to 21 October 2026 in both language parts
and to 23 October 2026 after the badges moved home, where the same section now says the
pictures are ours and a request leaves only when the visitor clicks a platform. The sweep
still ties
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
missing file instead of just a count. At that time those seven assets were hotlinked by
the platforms' terms, so a single CDN miss hid that link (`onerror`) rather than breaking
the page — distinguishing "not yet" from "broken" is the whole point of the wait. Since
23.10 the files are local and the wait still does its job: it separates "our host was slow"
from "the file is gone", and the onerror fallback covers the second.

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
(stars-bots-ops) extracts frame 389 of each loop and compares it with the poster by RMSE.
Calibration on all nine: a fresh poster scores 0.0102–0.0110; the stale
Russian one scored 0.0431 and the English poster with the old wording 0.0324. The threshold
is 0.02, which separates the two classes with room on both sides.
> УСТАРЕВШЕЕ (до 26.10.2026): тогда кадр для сравнения жёстко уменьшался до 540×1170.
> Постер с 26.10.2026 — 720×1560, поэтому рамка сравнения берётся с постера; на новой
> резолюции калибровка 0.00676–0.00790, чужой язык 0.1419–0.1490 (см. запись
> «The still frame was softer than the film it stands in for»).

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
endpoint must be loopback or private (`127.0.0.1`, `::1`, `localhost`, `10/8`, `172.16/12`,
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
our own endpoint | scheme=http host=127.0.0.1 from /proc`, which also proves the check reads the
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
- `tools/publish-branch.sh` now pushes that branch to **every** remote (GitHub serves it, Forgejo
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
## The phone on its side had no button (24.10.2026)

The previous block closed the first screen **upright** and said in its own report that the phone on
its side had only ever been measured for three languages, on one size. That gap was the block's
work: measure the first screen in **landscape** for all nine languages, on two real screens.

**What the measurement found.** At 844×390 (an iPhone on its side) and 740×360 (an ordinary Android
on its side) the hero button of three languages ended below the bottom edge:

| language | 844×390 | 740×360 |
|---|---|---|
| pt | 392 vs 390 — 2 px past | 378 vs 360 — 18 px past |
| vi | 392 vs 390 — 2 px past | 378 vs 360 — 18 px past |
| uk | 421 vs 390 — **31 px past** | 407 vs 360 — **47 px past** |

The button is 55 px tall, so on the Ukrainian page held sideways it was almost entirely off screen
at the moment the page opened. Nothing was broken in the markup: the hero in landscape is a single
centred column, and the vertical budget simply ran out — 63 px header + 34 px hero padding + a
two-line 40 px heading (96 px) + a four-line lead (115 px) + its 26 px bottom margin = 334 px of a
360 px screen; the button started at 352.

**The fix** is one media query, `@media(max-height:430px) and (orientation:landscape)`: header
62→52 px, hero padding 34→16 px, heading `clamp(26px,4.6vw,34px)` instead of 40, lead 17 px with
10/16 margins. The button now ends at 273 px on both landscape screens: 87 and 117 px of headroom.
Portrait (640 and 844 tall) and desktop (window height above 430) are outside the query — checked by
screenshot at 390×844 and 1440×900, both unchanged. A laptop window 1000×400 will get the compact
hero too; that is a deliberate default, noted for the owner.

**The gate grew from 18 checks to 36.** `scripts/landing-first-screen.py` now measures four screens
per language: 390×844, 360×640, 844×390, 740×360 — the hero button, heading, lead and video
positions printed for each.

**Proven to fail.** A real copy of the tree (`cp -a`), the new rule cut out of the copy's
`index-src.html`, an honest rebuild of the copy, the battery run against it with `LANDING_ROOT`:
**six problems, exit 1**, naming exactly `land-844x390/pt, vi, uk` and `land-740x360/pt, vi, uk`.
With the rule in place the same battery is 36 / 0.

**The instrument was wrong once, too.** The first version of that negative control made the copy
with `cp -al`. `tools/build.py` writes the finished pages in place, and through a hardlink that
rewrote the **original** tree — the sweep immediately went red with «на диске не то, что даёт
свежая сборка» on ten pages. The copy for a negative control has to be a real copy (`cp -a`); a
hardlinked copy is only safe while nothing writes to it. Restored by an honest rebuild; the lesson
went into the skill next to the negative-control rule.

**Also re-checked after the shorter header.** The language menu computes its own height limit from
the viewport and the sticky bar: at 740×360 it now caps at 292 px, scrolls, its last item is
reachable, the sticky bar does not cover it, and there is no horizontal scroll — 0 problems across
five screens (landscape en, hi, uk; portrait ru, vi).

**What it cannot prove.** That the rest of the landscape page is fine — only the first screen, the
menu and the sticky bar were measured. That 430 px is the right cut-off: it is the height where a
landscape phone ends and a tablet window begins, not a measured threshold. And that 34 px is the
right heading size on its side — it was chosen because 40 px took two lines and a third of the
screen, which is taste, not a measurement.

**Numbers.** Sweep **2 571 / 0**; `tools/build.py --check` 24 / 24; first screen **36 / 0**
(negative control 6 / exit 1); live runtime **121 / 0**; live bytes 26 / 26; axe **12 pages / 0**;
publish tree 109 files, 513 internal links. Published through `tools/publish-branch.sh` (main and
`gh-pages`, both mirrors, `ls-remote` agrees at `e6f40ef`).

**Files.** `index-src.html` (+ the nine built pages, `tools/lastmod.json`);
`scripts/landing-first-screen.py` and `SKILL.md` in the `stars-bots-ops` skill;
`evidence/block-20261024r/` (first screen 36, the landscape negative control, the menu regression,
live bytes, live runtime, axe, the sweep after publishing).

## The phone on its side was wider than the breakpoint (24.10.2026)

The previous block closed the sideways phone: it measured 844×390 and 740×360, found the hero button
under the bottom edge on pt, vi and uk, and added the compact landscape query. Both of those screens
are **narrower than 860 px** — and 860 is exactly where the layout stops being a phone: from 861 px
the hero is a two-column desktop grid, the language switcher is a dropdown, and the sticky bar is
switched off.

A sideways phone is often wider than that. iPhone 16 is 874×402, iPhone XR/11/XS Max is 896×414,
Pixel 7/8 are 915×412, iPhone 13/14 Pro Max is 926×428, iPhone 14/15/16 Pro Max is 932×430. On those
the visitor got the **desktop** hero: two columns, `align-items:center` on `.hero-in`, so the text
column was centred against the 648 px phone on its right and started 130 px down the page. The hero
button ended at **435 px** (screen 402), **445 px** (screen 430), **459 px** (screens 412 and 414) —
under the bottom edge in **all nine languages**: 45 measurements, 45 failures. And the sticky button
is not there to save it, because it lives inside `max-width:860px`.

Nothing was wrong with the markup; the media query was asking the wrong question. Width does not
answer "is this screen short?" — the compact query already existed, but it only sized the type, and
the two columns stayed centred. **The fix is one declaration inside it:
`.hero-in{align-items:start}`.** After it the button ends at 258..341 px on all five wide screens —
61 to 120 px of headroom per language.

**The gate is a device table now, not round numbers.** `scripts/landing-first-screen.py` went from
4 screens / 36 checks to **14 screens / 252 checks**: two upright (390×844, 360×640) and twelve
sideways — 568×320 (iPhone SE), 667×375 (8/SE2-3), 736×414 (6/7/8 Plus), 812×375 (X/11 Pro/mini),
844×390 (12/13/14), 851×393 (14 Pro/15), 874×402 (16), 896×414 (XR/11/XS Max), 915×412 (Pixel 7/8),
926×428 (13/14 Pro Max), 932×430 (14/15/16 Pro Max), 740×360 (cheap Android). Each pair asserts the
hero button is entirely above the bottom edge and that the page is no wider than the screen; the
run also prints a per-screen worst language and its headroom, so 126 rows do not have to be read.

**Proven to fail.** A real copy (`cp -a`), the one declaration cut out of the copy, an honest rebuild
of the copy, the battery against it with `LANDING_ROOT`: **45 problems, exit 1**, naming exactly
`land-874x402`, `land-896x414`, `land-915x412`, `land-926x428`, `land-932x430` × nine languages. With
the declaration in place the same battery is 252 / 0.

**The menu in the same band.** At those widths the header is the desktop one, so the language
switcher is its own dropdown — nobody had opened it on a 430 px screen. Measured at 932×430 and
874×402: nine entries, the list caps at 338 px and 292 px, scrolls with the "more below" shadow, the
last language is reachable, Escape closes and returns focus to the summary. Added to
`landing-a11y-extra.py` (two languages at 932×430 plus a page-error check): **170 → 187 checks**,
still 0 failed.

**What it cannot prove.** That iOS Safari lays these out the same way — everything here is Chromium;
that 430 px is the right cut-off (it is the tallest landscape phone, not a measured threshold); that
the rest of the page below the hero is fine in landscape — only the first screen and the menu were
measured; and that the desktop two-column hero is the right layout for a sideways phone at all —
this block kept it and only stopped it from centring, because a 900 px wide screen has room for two
columns even when it is 400 px tall.

**Numbers.** Sweep **2 571 / 0**; `tools/build.py --check` 24 / 24; first screen **252 / 0**
(negative control 45 / exit 1); a11y-extra **187 / 0**; WCAG 2.2 **43 / 0**; viewports-extra
**94 / 0**; axe **12 pages / 0**; live runtime **121 / 0**; live bytes **26 / 26**; publish tree
109 files, 513 internal links. Published through `tools/publish-branch.sh` (main and `gh-pages`,
both mirrors, `ls-remote` agrees at `017dcea` / `9a08cb9`).

**Files.** `index-src.html` (+ the nine built pages, `tools/lastmod.json`);
`scripts/landing-first-screen.py` (rewritten to the device table), `scripts/landing-a11y-extra.py`
(+the 932×430 menu run) and `SKILL.md` in the `stars-bots-ops` skill;
`evidence/block-20261024s/` (first screen 252, the wide negative control, the menu at 932×430,
live bytes, live runtime, the sweep after publishing, four hero screenshots).

## The sideways phone was measured down to the hero, and no further (25.10.2026)

The previous block closed with a sentence it could not answer: “the rest of the page below the hero
is fine in landscape — only the first screen and the menu were measured”. Two blocks in a row had
fixed the sideways phone and both stopped at the fold: first screen, header. Below it are six
sections, eight anchors, a FAQ with eleven answers, a contact form — and a sticky bar that takes a
sixth of a 360 px tall screen when it is there at all.

This block measured the rest. `scripts/landing-landscape-page.py`: three real landscape screens on
both sides of the 860 breakpoint — 932×430 (iPhone 14/15/16 Pro Max, wider than the breakpoint),
740×360 (cheap Android, narrow enough for the sticky bar), 568×320 (iPhone SE, first generation, the
lowest screen the page is expected on) — nine languages, **Chromium and WebKit** (Telegram on iOS is
WKWebView). Per screen × language: the document is no wider than the screen; visible content stays
inside its own section (the content of a closed `<details>` is not counted — it has no box on
screen); all eight header anchors land below the sticky header; the last FAQ answer opens fully and
does not slide under the bottom bar; the shots rail can be scrolled to its third frame; the submit
button is on screen and uncovered; no JS errors. **956 checks, 0 failed.**

**The defect it found was the bar itself.** The sticky CTA lived in `@media(max-width:860px)`, and
the header carries no button of its own. On 932×430 the hero button ends at y = 313 and the next
button is at y = 2921: **6.2 screens of scrolling with nothing to tap** — on a phone, because the
phone was held sideways and its width crossed a desktop breakpoint. The same defect the previous
block fixed one screen higher: the rule asked about width where the question was “is this a phone”.
Fixed by asking the pointer — `@media(max-width:860px), (hover:none) and (pointer:coarse)`, the same
query in the JS `matchMedia`, and on a wide coarse-pointer screen the bar's button is
`flex: 0 1 420px` centred, because a full-width 932 px button reads as a banner. The desktop is
unchanged, and that is checked rather than assumed: a separate context with `is_mobile=False,
has_touch=False` at the same 932×430 must keep the bar at `display: none`.

**Proven to fail.** The battery carries its own control (`--control`): a style injected after load
that zeroes `scroll-padding-top` and forces the bar on wide screens. Control run: **114 checks,
48 red, exit 1**; without the control **956 / 0**. Two measurement traps were closed on the way, both
of which had already produced false readings. The bar's `transition: transform .22s` runs on its own
clock, so a single reading caught it mid-slide (top 318 on a 360 px screen) — the state is now re-read
until its bottom meets the screen's. And `scrollTo` ignores `scroll-padding-bottom`, so “the answer
under the bar” is only a real check when the scroll is `scrollIntoView({block:'end'})`. The section's
own 84 px top padding hid a bad anchor landing as well: the check compares the section's edge, not
the heading — which is exactly why the control zeroes the padding and still finds the heading at
y = 85.

**One false red, and what it cost.** The first cross-engine run, started while three other browsers
were working, reported `webkit/desktop/pt` with eleven “broken” local images and two click timeouts.
The same page alone was clean, and the whole battery alone was 60 / 0. WebKit starves under load; a
red from a contended run has to be re-run alone before it is believed — otherwise the next block
“fixes” a page that was never broken.

**What it cannot prove.** That a real notch behaves like WebKit here — safe-area insets are zero in
emulation, and the page does not use `viewport-fit=cover`, so the notch is expected to shrink the
layout viewport instead of overlapping it, but that is reading, not measurement. That a tablet should
get the sticky bar at all: the rule is “coarse pointer”, so an iPad now shows it — a default, not a
decision. That 420 px is the right width for the button on a wide phone — taste, written down as a
default. And that any of the nine texts is what a native reader wants: this block measured boxes, not
words.

**Numbers.** Sweep **2 571 / 0** (after publishing); `tools/build.py --check` 24 / 24; landscape page
**956 / 0** (control 114 / 48 red, exit 1); first screen **252 / 0**; cross-engine **60 / 0**;
a11y-extra **187 / 0**; WCAG 2.2 **43 / 0**; viewports-extra **94 / 0**; axe **12 pages / 0**; live
bytes **26 / 26**; live runtime **121 / 0**; publish tree 109 files, 513 internal links. Published
through `tools/publish-branch.sh` (main and `gh-pages`, both mirrors).

**Files.** `index-src.html` (+ the nine built pages, `sitemap.xml`, `tools/lastmod.json`);
`scripts/landing-landscape-page.py` and `SKILL.md` in the `stars-bots-ops` skill;
`evidence/block-20261025a/` (landscape page 956, the control at 114 / 48 red, cross-engine 60, three
screenshots of the bar on a sideways phone, one of it absent under a mouse, and the raw numbers).

## The tablet was a device nobody had measured, and the one zone it owns (25.10.2026)

The block before this one closed with a sentence it did not answer: the sticky bar moved from a width
query to a pointer query, so an iPad now shows it — “a default, not a decision”. Tablets as a class had
never been measured at all: every battery before them named phones (390×844, 932×430, 568×320,
360×640) or the desktop (1440×900, 1920×1080). On a tablet three things happen at once, and none of
them happens at either end:

1. width 768…860: the layout is already single-column (≤860) while the header menu is still visible
   (it hides only ≤760) — a combination that exists nowhere else;
2. width 861…1366 with a coarse pointer: the desktop grid **plus** a sticky bar;
3. height 1024…1366: the bar now lives on a screen where it never existed, and can cover a FAQ
   answer or the submit button.

`scripts/landing-tablet-page.py`: eight real iPad screens in both orientations — 768×1024 (mini 5/6,
9.7"), 810×1080 (10.2"), 820×1180 (Air 11" / 10th gen), 834×1194 (Pro 11"), 1024×768, 1180×820 (Air
landscape), 1194×834 (Pro 11" landscape), 1366×1024 (Pro 12.9") — nine languages, **Chromium and
WebKit**. Per screen × language: the document is no wider than the screen; visible content (the
content of a closed `<details>` has no box and is not counted) stays inside its own section; the hero
button is fully above the fold; the header is exactly as tall as the desktop's, measured in the same
run at 1440×900 rather than written as a constant; the header menu and the language switch do not
overlap — at 768…860 they are neighbours; the bar is absent at the top and present after scrolling,
≤64 px tall, flush with the bottom, and on a wide tablet its button is ≤440 px and centred; the bar is
hidden when the shots' own button is on screen; the shots rail can be scrolled to its last frame; the
submit button is visible and uncovered; the last FAQ answer does not slide under the bar; no JS errors.
**1804 checks, 0 failed** — and every one of the 144 page runs produced 12 or 13 checks, so a run that
silently half-loaded would show up as a hole in the count instead of passing.

The control injects three deliberate defects (zero `scroll-padding-bottom`, a 120 px bar, a full-width
button on a wide tablet) and reddens **26 of 204** checks on English alone, so the battery is not green
by construction.

**The gap it named and did not close.** The battery's own header says the 768…860 zone exists nowhere
else — and then only proves that the nav does not overlap the language switch. Nobody opened that menu
on a tablet: every earlier menu run was at 420 px (no header menu at all), 844×390 (short landscape)
or 1440×900. `scripts/landing-tablet-menu.py` closes it — three narrow iPads × en/ru/hi × both
engines, **162 checks**: closed at load, opens on click, exactly nine items, the list entirely on
screen (all four edges), no item clipped by its own list, exactly one `aria-current="page"`, Escape
closes and returns focus to the summary, a click outside closes. **162 / 0.** Its control (the list
clipped to 60 px and pushed 320 px right) reddens **27**, and both classes — “on screen” and “not
clipped” — go red, not just one.

**Margins, not just passes.** The bar is exactly 59 px on all 144 runs; the tightest hero clearance is
186 px (Hindi at 1024×768, both engines); 806 px is the widest bar button anywhere, and that is the
narrow screen's full-width button at 834 px, which the check deliberately does not constrain — above
860 the button never exceeds 440 px. On the menu: the list is 430 px tall on all three screens, sits
at x 548…748 on a 768 px screen, and all nine items are inside it in every run.

**What it cannot prove.** That a real notch or home indicator behaves like the emulator — safe-area
insets are zero in emulation and the page does not use `viewport-fit=cover`, so the notch is expected
to shrink the layout viewport rather than overlap it, but that is reading, not measurement. That a
tablet should get the sticky bar at all: the rule is “coarse pointer”, so an iPad does — still a
default, not a decision. That 420 px (or 440 px) is the right button width — taste. That an iPad with
a trackpad behaves like a touch tablet: `pointer:fine` means no bar, and that combination was not
measured. And nothing about the nine texts: this block measured boxes, not words.

**Numbers.** `tools/build.py --check` 24 / 24; sweep **2598 / 0**; tablet **1804 / 0** (control 204 /
26 red); tablet menu **162 / 0** (control 162 / 27 red).

**Files.** No site file changed — both batteries are proof, not a fix, so `index-src.html`, the nine
built pages and the publish tree are untouched and nothing was re-published. `scripts/landing-tablet-page.py`,
`scripts/landing-tablet-menu.py` and `SKILL.md` in the `stars-bots-ops` skill;
`evidence/tablet-page-20261025T024748.json` (1804), `evidence/tablet-menu-20261025T025600.json` (162),
their two control files, and two screenshots of the bar on an upright and a sideways iPad.

## The page was walked forwards; nobody walked it backwards (25.10.2026)

The forward Tab walk with the sticky bar on screen has been measured (`landing-wcag22-targets.py`,
2.4.11, nine languages). The backward walk never was — and it is the other edge of the screen and a
different rule inside the browser. Tabbing down, the browser brings the focused element to the nearest
edge, which is the bottom: there the bar is 59 px tall and `scroll-padding-bottom` reserves 78. Tabbing
up, the same element arrives at the top edge, where the header is 63 px and `scroll-padding-top:84px`
is meant to hold it back. Whether that reserve works in the opposite direction, and whether WebKit
honours `scroll-padding` for focus scrolling the way Chromium does, was reading, not measurement.

`scripts/landing-backtab.py`: three screens (390×844 phone, 768×1024 iPad, 1440×900 desktop), en/ru/hi,
**Chromium and WebKit** — 18 page runs. Per run: a forward walk from the top and a backward walk from
the last element, both tagged with an index before walking, so the two can be compared stop by stop.
**A** no stop is hidden entirely (the WCAG 2.4.11 minimum); **B** no stop is hidden by more than half,
containers taller than 60 % of the viewport excluded — the shots rail is legitimately taller than the
screen and its top may sit under the header; **C** the backward walk visits exactly the same set of
elements; **D** its order is exactly the forward order reversed; **E** the bar really was on screen
during the walk (a check that never sees the bar proves nothing), ≤65 px, and is absent on the mouse;
**F** no JS errors. **120 checks, 0 failed.**

The margins are the interesting part, because "not hidden" can be true by a pixel: on every one of the
18 runs, every focused element no taller than 60 % of the screen was **fully** visible — a share of
**1.0**, which means not one pixel of it sat under the bar or under the header; the bar was on screen
for **13–15** of the ~40 stops on touch screens and for **0** on the desktop.

Three traps, all of them the harness's, not the page's. The first probe reported three "defects" on the
phone and eight on the tablet — the skip link, the brand, the language summary and the nav links:
elements *inside* the sticky header, which the code counted as "covered by the header", and at
`scrollY 0` the header covers nothing. The
second version compared the two walks naively and every page went red on order: the browser wraps
around after the last element, so both lists ended with a duplicate of the element they started from.
The reverse walk now stops when the circle closes, and the order is compared by position, not by list
equality. The third: an element the page's own script creates after load (the video pause button) has
no tag, so it silently dropped out of the set comparison — it now gets a tag the first time it takes
focus.

The control removes both `scroll-padding` reservations and inflates the bar to 200 px, and reddens
**48 of 120** checks — with FAQ summaries *fully* hidden, which is exactly the class of defect the
reserve was written for.

## The word that did not fit stayed invisible to every gate (25.10.2026)

"Page is not wider than the screen" is checked by half a dozen batteries. A box that hides its own
overflow is invisible to all of them: the document is honest, the layout is honest, and the visitor
reads "Study helper for school…" where the sentence continues behind the edge. At 320 px — a cheap
Android, a first-generation iPhone SE — and in nine languages, where Turkish glues words together and
Vietnamese and Hindi produce long unbreakable runs, this is not a theoretical class.

`scripts/landing-text-clip.py`: two narrow screens (320×568, 360×640) × nine languages × two engines,
**all `<details>` opened before the measurement** — otherwise the longest text on the page, the FAQ
answers, is never measured at all. 303–304 elements per page. **A** nothing is clipped by its own box
(`overflow-x: hidden|clip` and `scrollWidth > clientWidth`); **B** no `text-overflow: ellipsis` is
actually truncating; **C** no block sits outside the screen horizontally unless it lives inside a
scroll container. **148 checks, 0 failed.**

Three exclusions keep the battery honest, and the first run is why they exist: `.sr-only` (1 px wide by
design), anything inside a scroller — the shots rail and the language list are scroll containers where
`scrollWidth > clientWidth` is the normal state, and without that exclusion the rail alone produced
eight "defects" per page — and boxes with zero width.

The control plants a nowrap heading in 120 px, a 60 px paragraph with an ellipsis and a footer pushed
40 vw to the right: **108 of 148** checks go red, and all three classes, not just one.

**What neither battery can prove.** That a hardware keyboard on an iPad behaves like Tab in an
emulator; that Safari's collapsing toolbar scrolls the focused element the same way with a dynamic
viewport; that a screen reader's virtual cursor lands where Tab lands. And that half the element is the
right line for B — WCAG asks only that the focused element is not *entirely* hidden; the stricter line
is this project's own, and it is deliberately stricter than the standard.

**Numbers.** `tools/build.py --check` 24 / 24; sweep **2598 / 0**; text clipping **148 / 0** (control
148 / 108 red); backward walk **120 / 0** (control 120 / 48 red).

**Files.** No site file changed — both batteries are proof, not a fix, so the nine pages, the template
and the publish tree are untouched and nothing was re-published. `scripts/landing-text-clip.py`,
`scripts/landing-backtab.py` and `SKILL.md` in the `stars-bots-ops` skill;
`evidence/text-clip-20261025T032328.json` (148), `evidence/backtab-20261025T032735.json` (120), their
two control files.

## Eleven batteries sat out the last CSS change, and nobody had ever turned the phone (25.10.2026)

Two gaps, one block.

**The first is not a defect but an absence of evidence.** The rule on this project is explicit — any change to CSS
or `@font-face` invalidates every browser battery, because a rule that moves one box moves all eleven pages. The
last four CSS commits (24.10 14:12, 22:34, 23:53, 25.10 01:26) changed the pause button's typeface, the sticky
bar's media query from width to pointer, the landscape band under 430 px, and the tablet zone. What ran after them:
the tablet batteries (02:19–03:01), the backward Tab walk and the text-clip battery (03:23–03:58). What did not:
axe (last run 22.10), a11y-extra (23.10), wcag22, env-prefs, viewports-extra, fonts, cwv, render-check,
cross-engine (all 22.10), and `landing-video-motion.py` (24.10 09:37 — three hours *before* the pause button was
changed to the site's own typeface). Nine batteries and the one script whose subject had just been edited were
sitting in the past. That is the exact shape of the failure this rule was written for: the site is green because
nothing is looking.

So they were all re-run against the current build, in order, each one's full output kept:
`build --check` 24/24; sweep **2598 / 0**; render-check **ALL OK** (mobile single column, no-JS path, no JS errors);
axe 12 pages **0 violations**; a11y-extra **187 / 0**; wcag22 targets **43 / 0**; env-prefs **45 / 0**;
viewports-extra **94 / 0**; fonts **39 / 0**; cwv **69 / 0**; cross-engine **60 runs, 0 problems** (426 s);
video-motion **444 / 0**; browser-smoke **18 runs, 0 problems**; external links 0 problematic; publish tree 513
internal links, nothing missing and nothing from the workshop. **3831 numeric checks, zero failures** — and,
separately, the published branch compared byte for byte with the working tree: 109 of 109 files identical, so the
world is not showing yesterday's build.

**The second gap is a class nobody had measured: the rotation.** Every measurement on this site happened *at rest*:
the page was opened at a size and measured at that size. Rotation is a different event — it resizes the window of a
*live* page. Two `resize` handlers wake up (the sticky bar's `sync`, the language list's `fit`), the browser
recomputes every `IntersectionObserver` on its own, and scroll anchoring rewrites `scrollY` to keep the reader's
content in place. A bug here does not look like a broken page; it looks like a phone turned sideways and a language
menu whose last three languages are behind the edge.

`scripts/landing-rotate.py` (port 8277, `--control`): four real portrait/landscape pairs (390×844 iPhone 14,
375×667 iPhone SE, 412×915 Pixel, 768×1024 iPad) × en/ru/hi × Chromium and WebKit = **24 runs, 288 checks**.
Per run: **A** the rotation is not a reload (a marker set in `window` survives both turns) and the document is
never wider than the screen in any of the three states; **B** the block that stood at the top edge before the turn
is still on screen after it (within ¾ of a screen), and a deeply scrolled page is not thrown back to the top;
**C** the sticky bar, after a turn and *without any scroll*, keeps its rule — no second copy of the button when
`#contact`, the footer or the shots CTA is in frame, and present, ≤64 px and pinned to the bottom otherwise;
**D** the language list, opened *before* the turn, still fits afterwards (bottom inside the screen, at least two
items visible), and after turning back its pixel cap returns to the previous value — proof the recalculation
happened rather than "was cut once and stayed cut"; **E** back at the starting size, the document height and the
vertical position of the hero heading, `#pricing`, `#contact` and the footer equal a **fresh load** at that size
within ±2 px — otherwise a layout from another size is still in the page; **F** no JS errors.

**288 / 0.** The number worth keeping: the language list's cap goes **430 → 292 → 430 px** in *both* engines, and
the document height returns with **0 px** of drift on all 24 runs, so the return to portrait is the same page the
visitor would have got by loading it fresh. Three traps, and all three were the harness's:

1. "The last section above the top edge" looks like the reader's place, and is not: when the screen gets shorter
   and the scroll position moves, a *different* section becomes the last one above the edge. Twelve correct pages
   went red in WebKit before the check was replaced by an absolute anchor — the block under the top edge, and
   where that block ended up on screen after the turn.
2. The list's cap is set by `fit()` inside `requestAnimationFrame`, not by CSS, and a fixed 300 ms pause is a
   promise about the browser that the browser has not made: on the **first** page of each pair in WebKit the
   battery read the CSS value (712 px) and then compared it with the recomputed 430 — that is CSS compared with JS,
   not a stale layout. It now waits for the inline value to appear, up to two seconds, and says so if it never does.
3. The centre of the screen is not a reference point either: the centre of a 390 px-high screen is a different
   place in the document than the centre of an 844 px-high one, so "the section under the centre" changes by
   design. Another twelve red pages, all correct.

The control removes the mechanism instead of the symptom: before load, the page's `addEventListener` is wrapped so
`resize` and `orientationchange` are never registered — the page keeps its portrait cap. **18 of 288 go red**, and
the split is the interesting part: all eighteen are D1 on the three *phone* pairs (cap stuck at 430 px on a 390 px
screen, the list's bottom at 486 px, the lower languages behind the edge), while the iPad pair stays green because
430 px still fits a 768 px-high landscape screen. The control discriminates; it does not paint everything red.
A control that does not redden the class it was written for means the battery is blind, and this one is not.

**What the battery cannot prove.** That a real device rotation is a viewport resize. iOS and Android re-create the
visual viewport, collapse toolbars, and re-lay out on their own schedule; Playwright's `set_viewport_size` is the
closest approximation available here, not the thing itself. A hardware rotation that behaves differently would not
show up in these 288 checks.

**Numbers.** build `--check` 24 / 24; sweep 2598 / 0; axe 12 pages / 0; a11y-extra 187 / 0; wcag22 43 / 0;
env-prefs 45 / 0; viewports 94 / 0; fonts 39 / 0; cwv 69 / 0; cross-engine 60 / 0; video-motion 444 / 0;
smoke 18 / 0; external links 0 / 0; publish tree 513 links / 0; published branch 109 / 109 identical;
rotation **288 / 0** (control 288 / 18 red).

**Files.** No site file changed — the re-run is proof and the new battery is proof, so the nine pages, the
template and the publish tree are untouched and nothing was re-published. `scripts/landing-rotate.py` and
`SKILL.md` in the `stars-bots-ops` skill; `evidence/block-20261025b/` (every battery's full output),
`evidence/rotate-20261025T045054.json` (288) and `evidence/rotate-control-20261025T045354.json` (18 red).

## The link promised the price; the page took the reader on a 4,500-pixel tour (25.10.2026)

Every anchor on this site has been measured — three batteries do nothing but press menu links and check that
the block lands below the sticky header. All of them pressed the link **inside an already open page**. A link
in a Telegram post arrives differently: the address carries `#pricing` before anything has happened, and the
browser must travel on its own. That is an arrival, not a navigation, and nobody had measured it.

Chromium animates it. `html{scroll-behavior:smooth}` is written for the reader who clicks a menu item; applied
to the arrival it turns the jump into a flight: **#pricing — 1120 ms over 4817 px** (it starts 400 ms after
commit and ends at 1520), **#contact — 1400 ms over 7533 px**. WebKit (Telegram on iOS is WKWebView) lands in
one step, two samples 24 ms apart. And under `prefers-reduced-motion` Chromium is instant as well, because the
page already carries `@media(prefers-reduced-motion){html{scroll-behavior:auto}}`. So the page had already
decided an arrival should not be animated — it only decided that for the people who ask the operating system.

The speed is the smaller half. **A key press during the flight stops it.** Measured at 560 ms:

| the reader pressed | where `#pricing` ended up |
| --- | --- |
| ArrowDown | **3587 px below the top of the screen** |
| PageDown | 382 px |
| Space | 1046 px |
| wheel −240 | 84 px — the flight continued |
| tap on the hero | 84 px — the flight continued |

The one thing that cancels the flight is the one thing a keyboard user does while wondering why the page is
moving: he ends up four screens above the price the link promised, and nothing tells him. The wheel and the tap
do *not* cancel it — I expected them to, measured, and was wrong.

**The fix is nine lines in `<head>`**, and it is the technique the form already uses after a submit, where
`confirmSent()` sets `scrollBehavior` to `auto` around its own `scrollIntoView` because clearing the query and
the anchor throws the reader to the top. If the address carries a fragment, the document scrolls instantly until
the first `pointerdown`/`keydown`/`wheel`/`touchstart`; smoothness comes back at the first contact, earlier than
the click on the menu item that wants it. No fragment — nothing changes.

**After:** the flight is 0 ms — a single movement sample, 364 ms after commit, at 84 px, in both engines.
ArrowDown at 560 ms now moves the reader 40 px down *from the price*, which is his own scroll. That is the local
server; the live host was asked the same question — `#pricing` and `#contact` stand at 84 px by `load` + 400 ms in
both engines, with `scroll-behavior: auto` in effect on the served page.

**The battery.** `scripts/landing-deeplink.py` (port 8278, `--control`): nine languages × six anchors (`#how`,
`#subjects`, `#pricing`, `#faq`, `#contact`, `#main`) × Chromium and WebKit at 390×844 = 108 arrivals, six
checks each — the block sits on `scroll-padding-top`; the arrival is complete by `load` + 400 ms; no late drift
between 400 and 1600 ms; the target is not invisible (the reveal fired); its heading is below the header and in
the top half of the screen; no JS errors. The other half guards the opposite direction: at 1440×900 in en/ru/hi
a real click on a menu item must still be *smooth* (≥ 5 scroll events, not one), must still land on the padding,
and a page loaded without a fragment must keep `scroll-behavior: smooth`. **684 checks, 0 failed.**

**The control** rewrites exactly one line in the HTML as it is served (`auto` → `smooth`, through
`context.route`, no copies of the tree) and counts what it rewrote: 108 pages, 216 lines — the second hit is the
form's own line, which is the same string. **90 red: 45 A2 + 45 A3**, and the split is the proof: all 54 WebKit
arrivals stay green (WebKit never flew), all nine `#main` stay green (they stand at the top of the document,
there is nothing to fly over), and A1 stays green everywhere — the destination was always right; only the
journey was wrong.

**Two harness traps, both mine.** The first version navigated without the fragment (the anchor was in the check,
not in the URL): 306 red on a correct page — and the numbers said so, `y=0` with `top` equal to the absolute
offset. The second: `#main` is the skip link's target and stands on the 63rd line of the document, right under
the header, so demanding `top == scroll-padding-top` from it demands a negative scroll — 36 more false reds.
`landed()` now knows three legal outcomes (the padding, the bottom of the document, the top of the document),
each written down with its reason, because the next block would otherwise "fix" a page that was never broken.

**A cheap gate for a cheap failure.** The browser battery is not part of the sweep (the sweep has to stay fast),
so the sweep got two static checks: the guard is present in all nine pages and stands inside `<head>`. Controlled
the usual way — delete it from `ru` and move it to the end of `<body>` in `vi`: `[deeplink] guard есть во всех
девяти страницах | нет в: ru` and `[deeplink] guard стоит в <head> | не в <head>: vi`, both naming the page, and
after `build.py` the three files come back to the same sha (`22097bda`, `0990cfae`, `0d3ed728`).

**What it cannot prove.** That Telegram's in-app browser behaves like Playwright. Both engines it uses were
measured — Chromium on Android, WKWebView on iOS — but the in-app shell is not the same thing, and a real phone's
fragment scroll happens against a warm cache and a real network, not a local server.

**Numbers.** The page changed, so every battery ran again — nineteen of them, `evidence/block-20261025c/`:
build `--check` 24/24; sweep **2600 / 0** (2598 plus the two new guards); render-check ALL OK; axe 12 pages / 0;
a11y-extra 187 / 0; wcag22 43 / 0; env-prefs 45 / 0; viewports 94 / 0; fonts 39 / 0; cwv 69 / 0; cross-engine
0 problems; rotate 288 / 0; landscape 956 / 0; tablet 1804 / 0; backtab 120 / 0; text-clip 148 / 0; first-screen
252 / 0; video-motion 444 / 0; smoke 18 / 0; external links 0 / 0; publish tree 513 links / 0; deeplink
**684 / 0** (control 90 red).

**Files.** `index-src.html` and the nine built pages, `tools/lastmod.json`; `scripts/landing-deeplink.py`,
`scripts/landing-sweep.py` (+2 checks) and `SKILL.md` in the `stars-bots-ops` skill;
`evidence/block-20261025c/`, `evidence/deeplink-run-20261025.json`, `evidence/deeplink-control-20261025.json`.

## Thirty decisions were carried out; the file that explains the site had stopped agreeing (25.10.2026)

The council (designer, marketer, SEO) met on 15 October in two rounds and its decisions
drove ten days of work. Nobody had ever held that list against the site *as a list*. Some
decisions got a static marker in the sweep on 17.10; the rest lived in prose, in chat rooms
and in this README, and prose is what rots.

So I read all six round files again (they live outside the site, in the room archive), wrote the
decisions down as thirty separate rows, and checked every row against the tree and a
browser rather than against my memory of commits: the hero's visual order at 420×760 in all
nine languages, the sticky bar's height in all nine at 320 and 420, the 404 page at three
widths, the live host byte-for-byte, the sitemap's eleven addresses, the font budgets, the
badge strip, the tags, the reveal rule. The table is `docs/council-20261015.md`, and the
short answer is: **thirty of thirty were carried out.** One was repealed by the owner
(GSC/Bing verification, 16.10 — the site is temporary, promotion waits for the domain
move). Three are deviations with a measured reason written next to them: the badge files
live here instead of being hotlinks, the font budget is 160 KB instead of 100 (nine scripts
do not fit in 100), the sticky bar is 59 px instead of 56 (the button inside is 46, and
shrinking it to hit the number would make the target smaller than a finger).

Two decisions had no gate at all, and both are load-bearing for money:

| decision | how it is kept today | what breaks without a gate |
| --- | --- | --- |
| mobile order: title → lead → button → video → chips | `.hero-left{display:contents}` + `order:1..6`, and nothing else | delete `.hero-phone{order:4}` and the video drops 700 px below the chips while the platform badge floats above it — every existing battery stays green |
| "the reveal must not delay the hero CTA" | the button's wrapper simply has no `rv` class | add `rv` and the main action is `opacity:0` until the observer fires |

Both are now sweep checks with controls: dropping the `order` rule gives **9 red**
(`phone: None`), restoring it gives 0; adding `rv` to the wrapper gives **9 red**
(`class=cta-row rv`), removing it gives 0.

**The real find was in the documentation.** Every gate on this site reads pages. None reads
the prose that tells the next editor what the pages do. On 23.10 all nine launch badges
moved into `img/badges/` — the page stopped asking other people's servers for a picture
before the visitor clicked anything — and the privacy policy was rewritten in both languages
to say exactly that. The descriptive half of this README, the part above the diary that a new
editor reads first, still said the opposite in **six places**: "all hotlinked from the
platforms except the Startup Fame one", "the hotlinked badge asset uses `fazier.com/api/v1/…`",
the award badge "hotlinked like the rest", "every badge but Startup Fame is a hotlink", the
browser smoke that "requires 9 of 9 links hidden", and the privacy paragraph that described
the old flow as current. Two days of a true page and a false description. That is precisely
the failure the stale-mention rule exists for, and it is invisible to every battery we own.

The descriptive section is corrected in six places, and the hotlink era is kept as history
under an explicit `SUPERSEDED (22.10 → 23.10.2026)` marker rather than deleted: the diary
entries from 21–23 October describe the measurements that produced the change and must stay
readable. A new sweep check holds the line — with the pages serving the badges themselves,
the descriptive part (everything above the first dated heading) may not call them hotlinks,
and the mutation is the pre-fix README, which turns it red naming all three phrases.

**Numbers.** sweep **2619 / 0** (2600 + 2 hero guards + 1 documentation guard); `build.py
--check` 24/24 (no page was rebuilt — this block changed no page); live bytes 26/26 with the
404 probe answering HTTP 404 and our own page; live assets 0 problems, sitemap 11/11 = 200;
hero order measured in nine languages as h1 → lead → button → video → chips → badge; sticky
bar 59 px in all nine with a one-line label at 320 and 420; 404 page at 320×568, 420×760 and
1024×768 with no overflow, no clipped text and only the inline legal links below 24 px
(exempt as inline text).

**What this does not prove.** That the council's decisions were right — only that each one
is present. And it does not re-run the browser batteries: the pages did not change in this
block, so their last full run stands (`evidence/block-20261025c/`).

**Files.** `README.md` (six paragraphs in the descriptive section, the marker, this entry);
`docs/council-20261015.md` (new, thirty rows); `scripts/landing-sweep.py` (+3 checks) and
`SKILL.md` in the `stars-bots-ops` skill.

## The page printed as a table of contents (25.10.2026)

Forty-one batteries on this site look at a screen — a phone held upright, a phone held sideways, a
tablet nobody had measured, a keyboard walking backwards. None of them looked at paper, and paper is
the one place where the page keeps none of its promises: there is no scroll to reveal what scroll
hides, no click to open what a click hides, and — the part that decides everything — the browser
prints **without backgrounds** unless a reader ticks a box in a dialog nobody opens.

The first honest print of the English page (A4, print background off, the browser's own default)
came out as **eight sheets, six of them nearly empty**. Sheet one carried the hero and the four
steps. Sheets two to eight carried the section numbers and their headings — `01 How it works`,
`02 What's inside`, `03 School subjects`, `04 Real chats with the bot`, `05 Pricing`, `06 FAQ`,
`For parents`, the final call to action, the contact form — and blank paper underneath. Ink per
sheet, measured on the rendered pages: 15 %, then 1.3 %, 1.1 %, 0.06 %, 0.6 %, 0.1 %, 0.2 %, 0.4 %.
The prices, the eleven FAQ answers, the parents paragraph and the whole form were not on the paper
at all.

Three screen behaviours, each with no condition on a sheet:

| what | why it is invisible on paper | measured |
| --- | --- | --- |
| the reveal (`html.js .rv{opacity:0}`) | waits for a scroll, and a sheet never scrolls | 37 of 37 blocks transparent |
| white text on the dark band (`#0E1526`, `color:#fff`) and on every brand-blue button | the background is dropped, the text stays white | 2 blocks + every CTA |
| the shots rail (`overflow-x`, `grid-auto-columns:86%`) | the window is printed, not the scroll | 1 771 px of content in 678 px → a third of one screenshot |

A fourth was not layout at all: a closed `<details>` is hidden by the browser's own internals, so the
printed FAQ was eleven questions with a `+` and no answers — the half of the page a reader keeps
paper for. CSS cannot reopen it (`::details-content{content-visibility:visible}` changed nothing in
Chromium 141); `beforeprint` can, and `afterprint` closes the questions again.

**The fix** is one `@media print` block at the end of the stylesheet plus eleven lines of script:
release the reveal; print the band and the buttons as dark ink on white with a border; hide the
screen furniture (header menu, sticky bar, skip link, video toggle, the 648 px video frame, and the
footer badge strip — its nine logos are lazy-loaded pictures that never reach a print layout, so the
strip printed as a hole); lay the three shots out as one row; underline links; print the bot address
once at the bottom (`t.me/UchiSamBot`, because a button cannot be pressed on paper); keep cards, FAQ
items and the footer from breaking across sheets; and open every FAQ answer before the snapshot. The
three hand-written pages outside the generator got the same treatment — `privacy.html` and
`terms.html` lose the `position:fixed` "Skip to content" link (Chromium printed it in the middle of
the policy text, where it has no business on a sheet), and `404.html` gets its button back: white
text on a dropped brand background printed as an empty rectangle. That last one had to be fixed in
`tools/build.py`, because the 404 page is generated — a hand edit to `404.html` was silently
overwritten by the next build, which is the workshop teaching the same lesson it taught on 23.10.

**Numbers.** New battery `landing-print.py`: **147 checks, 0 problems** — nine languages × twelve
layout assertions, plus the PDF's own text (the first FAQ answer of each language in its own words,
no sheet under 20 characters, no more than twelve sheets), plus the three standalone pages. Its
control, `--mutate strip`, deletes the print block from the loaded page and turns **111 checks red**
(twelve per language and three on the standalone pages — every family fails in every language),
which is the only reason to trust the green. Sheets per language: 7–8; the thinnest sheet carries
1.9 % ink (Russian's last page, 170 characters), the shots sheet 16–17 % (it is mostly pictures).
The rest of the block, unchanged in purpose and re-run because the CSS changed: sweep **2 701 / 0**
(2 620 + nine `foot-badges` markers; before publishing exactly one check is red — the live site still
serves the previous build), render-check ALL OK with no JS errors, axe 12 pages 0 violations,
a11y-extra 187/0, WCAG 2.2 targets 43/0, keyboard backwards 120/0, text-clip 148/0, environment
preferences 45/0, viewports 94/0, fonts 39/0, Core Web Vitals 69/0, rotations 288/0, deep link 684/0,
video motion 444/0, first screen 252/0, tablet 1 804/0, tablet menu 162/0, landscape 956/0, glyph
fallback 12 pages 0 substitutions, visual pass 0 problems, smoke 18 runs 0 problems, links 11 pages
0 problems, `build.py --check` 24/24, cross-engine 60 runs 0 problems, Nu validator 14 known-false
messages per page (unchanged). The launch-platform cards were **re-stamped, not redrawn**: the gate
"inputs are not newer than the manifest" went red the moment `tools/build.py` changed (it is one of
the ten inputs), the generator produced all four PNGs byte-identical (`sha256sum -c` before and
after), so only the manifest's hash list moved — which is the point of that gate: it makes you look.

**What this does not prove.** Only Chromium was measured — the engine this house has batteries for;
Firefox and Safari print the same CSS in their own way, and nothing was checked on a real printer or
on paper. The footer address is `t.me/UchiSamBot` without the `start=` tag: on paper that tag had
nowhere to land, so a printed page cannot tell us which language the reader came from.

**Files.** `index-src.html` (the `@media print` block, the `beforeprint` handler); `tools/build.py`
(the 404 page's print rule); `privacy.html`, `terms.html` (the skip link); every built page;
`README.md` (a "Printing" paragraph in the descriptive half and this entry); `landing-print.py` (new)
and `landing-sweep.py` (+9 markers) and `SKILL.md` in the `stars-bots-ops` skill.

**Printed from the live site, not from the working tree.** After publishing, the same measurement
ran against `kerio-byte.github.io/uchisambot/` and `/ru/`: 37 of 37 blocks transparent on screen,
0 in print, the band's text `rgb(17, 17, 17)`, `t.me/UchiSamBot` in the footer, the first FAQ answer
present in the PDF, seven sheets for English and eight for Russian — the published page and the tree
print the same way.

## The policy's last sheet carried one line, and the badges were a hole (25.10.2026)

The print block measured the landing page and stopped at its edge. The three pages outside the
generator got one rule each — `skip{display:none}` on the policy and the terms, the button's colours
on the 404 — and nobody asked the two questions that only make sense on a sheet: **what is on the
last sheet**, and **what is on the page at all**. Both had answers.

**The badge strip printed as a hole.** `privacy.html` and `terms.html` carry the same "Featured on"
strip as the landing page, and the landing page hides it in print for a measured reason: the nine
logos are `loading="lazy"` pictures, a print layout never scrolls to them, so they arrive as
nothing. On the legal pages the strip was not hidden. Measured in print media: `.foot-badges` present,
`display:flex`, height 46 px, and all three images `naturalWidth 0` — a 46 px band of blank paper
between the footer links and the bottom of the sheet, the same defect that was fixed on the landing
page and missed one file over.

**The policy's last sheet was a single line of footer.** An A4 print of `privacy.html` came out as
**eight sheets**, and the eighth carried `Home · Privacy Policy · Terms of Service` — nothing else.
Ink on that sheet: **0.07 %**, while the seven before it carry 6–8 %. The terms were fine (5 sheets,
the last one 4.25 % ink with section 9 on it), so the defect was the policy's length, not the
rule. Compacting the paper layout — `main{padding-top:8px}`, `h3{margin-top:10px}`,
`footer{margin-top:8px;padding:10px 0 0;break-before:avoid}` — puts section 9 and the footer on the
same sheet: **7 sheets instead of 8**, last sheet 2 097 characters and 5.9 % ink. `break-before:avoid`
alone was tried first and does nothing (measured: still 8 sheets) — the engine cannot pull a block
backwards that does not fit; it only refuses to push it forward. It stays as a guard for the day a
paragraph is added and the footer would fit by a hair.

**The gate was wrong before the site was.** The first version of the new battery read the PDF with
`pdftotext -layout` and split on `\f` — but `pdftotext` ends *every* sheet with a form feed, so the
split leaves an empty tail, and that tail was reported as "sheet 9 is empty" on the policy, "sheet 6"
on the terms, "sheet 2" on the 404. `pdfinfo` said 8, 5 and 1. The same mistake then sent the 404's
`body{min-height:100vh}` to the workshop for a fix it did not need: the page has printed as one sheet
all along (`pdfinfo: Pages 1`), and `min-height:100vh` on paper is exactly one page, which centres the
404 where it belongs. That change was reverted, not shipped. The battery now cross-checks
`pdfinfo Pages` against the number of text chunks and judges emptiness by **ink**, not by text
length: 0.07 % is a sheet with one line on it, and only a picture-less, line-less sheet reads 0.

**Numbers.** New `landing-print-pages.py`: **52 checks, 0 problems** — per page: page count agreement
between `pdfinfo` and the text chunking, ink per sheet ≥ 0.15 %, no sheet empty of text, no sheet
ending with one of the page's own `h1/h2/h3`, no sheet ending in a one-or-two-word fragment, and no
sheet under 200 characters before the last. Sheets: policy 7, terms 5, 404 1; ink 5.9–8.3 %, 4.2–6.5 %,
1.7 %. Its control, `--mutate strip`, removes the print rules from the loaded page and turns **3
checks red** (policy back to 8 sheets with a 0.07 % last sheet, plus the skip link's text surfacing at
the foot of two sheets). Second battery, `landing-print-contrast.py`: **3 543 checks, 0 problems** —
twelve pages (nine languages plus the policy, the terms and the 404) × three engines (Chromium,
Firefox, WebKit) × every element that carries its own text, each measured against a white sheet (the
browser drops backgrounds by default) and against its own background, at WCAG thresholds (4.5, 3.0 for
large text). Its control, `--mutate noprint`, deletes `@media print` and turns **135 checks red** (five
elements per page per engine: the two CTAs, the closing band's heading and paragraph, the form's
button). Re-run because the CSS changed: sweep **2 705 / 0** (2 703 + the two new markers; before
publishing the only red is the live site still serving the old build), `landing-print.py` **147 / 0**,
`build.py --check` **24 / 24**.

**What this does not prove.** Chromium's PDF is the only paper that was actually produced: Firefox and
WebKit were measured as *CSS applied in print media*, not as a PDF — Playwright prints to PDF only in
Chromium, and this machine's Firefox is a snap whose `--print-to-pdf` writes nothing (checked: a
screenshot from the same headless run works, the PDF flag does not). The 1 181 elements per engine are
legibility, not pagination. Nothing was printed on a real printer or on paper.

**Files.** `privacy.html`, `terms.html` (the print block, the badge strip, the compaction);
`landing-print-pages.py` (new), `landing-print-contrast.py` (new), `landing-sweep.py` (+2 markers) and
`SKILL.md` in the `stars-bots-ops` skill; this entry and the "Printing" paragraph above.

## The landing printed eight sheets, and the eighth was the footer (25.10.2026)

Three print batteries measured this page. `landing-print.py` reads the print layout and the PDF of
all nine languages, `landing-print-pages.py` asks where a heading lands — but only on the policy,
the terms and the 404 — and `landing-print-contrast.py` measures legibility on a sheet. Nobody asked
the two questions that only make sense on a sheet with nine sections: **where does a section heading
land on the nine language pages**, and **what exactly is on their last sheet**.

**The footer printed as a sheet of its own.** In Russian the page came out as eight sheets, and the
eighth carried five lines: the bot's title, the payments line, the policy links, the badge names and
`t.me/UchiSamBot` — 196 characters and 0.56 % ink. Ukrainian and Indonesian also ran to eight
(309/0.85 % and 335/1.02 %). Measured from the paper, the foot of the seventh sheet in Russian held
85 mm of nothing. The cause was not text: `footer{padding:44px 0 34px;margin-top:56px}` is screen
spacing, and it lives on paper too. The block stands 274 px tall, the sheet had 241 px left, and
`footer .foot{break-inside:avoid}` moved the whole thing to a fresh sheet rather than split it.

**Fixed by giving the footer paper spacing**, the same way the policy was fixed yesterday:
`@media print{footer{padding:10px 0 0;margin-top:20px}}` — 166 px instead of 274. Russian goes from
eight sheets to seven, and its last sheet now carries 544 characters, twelve of them not the footer.
The other seven languages did not change: en/es/pt/hi/tr/vi stay at seven sheets, and their last
sheets already carried the form's closing line above the footer.

**Ukrainian and Indonesian still print eight.** Their first big gap is earlier: three phone
screenshots sit in one row, each `figure.shot` is 495 px tall and `break-inside:avoid` keeps it
whole, so on sheet two a 365–385 px remainder cannot take the rail and the sheet ends with 96–101 mm
of blank paper. Cutting a screenshot in half to save a sheet was rejected — the picture is the
argument, and a half picture on two sheets is worse than a spare sheet. The numbers are recorded in
`tools/print-sheets.json`, one budget per language: a regression above it is red, and a page that
gets shorter means the budget comes down by hand.

**The gate was blind in the way it was first written.** The first version asked whether the last
sheet carried any line that the footer's `innerText` does not contain. With the screen paddings
restored as a control it turned **one** check red instead of two: pdftotext and `innerText` break
lines differently, and the printed address is generated content (`.foot::after`) that `innerText`
never sees. The footer text is now assembled with its pseudo-element, and the question is answered
by volume instead: last sheet characters ÷ footer characters. The thinnest real sheet is ×1.61
(uk), the defect is ×1.09 (ru), so the threshold sits at ×1.20 in the gap between them. With that,
`--mutate footerpad` turns two checks red on Russian: eight sheets, and a footer alone on the last.

**Numbers.** New `landing-print-main.py`: **213 checks, 0 problems** — per language: `pdfinfo` agrees
with the text chunking, sheets within budget, no sheet under 0.15 % ink, no sheet ending with its own
`h1/h2/h3`, no sheet under 200 characters before the last, and the footer not alone on the last.
Measured both on the tree and, after publishing, on `kerio-byte.github.io/uchisambot/` — same sheet
counts and same per-sheet characters, so the live site prints what the tree prints. Re-run because
the print CSS changed: `landing-print.py` **147 / 0**, `landing-print-pages.py` **52 / 0**,
`landing-print-contrast.py` **3 543 / 0**, sweep **2 707 / 0**, `build.py --check` **24 / 24**.

**What this does not prove.** Chromium's PDF only, and no real printer. A blank third of a sheet
before the screenshots rail (96–101 mm in uk/id) stays: a 495 px figure cannot be split across
sheets without cutting the picture, and that trade was refused, not missed. Nothing here says the
page is worth printing — only that if someone does, no sheet is wasted on the footer alone.

**Files.** `index-src.html` (the footer rule in `@media print`), every built page, `tools/print-sheets.json`
(new); `landing-print-main.py` (new) and `SKILL.md` in the `stars-bots-ops` skill; this entry and the
"Printing" paragraph above.

## The sheet was turned, and one page of paper carried no words at all (25.10.2026)

Four print batteries measured this page, and all four printed one paper: `format='A4'`, no
`landscape` argument, no other size. A print dialog puts «Альбомная» and «Letter» one click away
from A4, so the page had two print layouts nobody had ever looked at. Measured on the tree:

**A4 landscape: 11 sheets in all nine languages, and sheet 5 carried exactly zero characters.**
Not "almost empty" — pdftotext returns nothing at all for that sheet, and it was also the palest
on the page (0.35–0.59 % ink). Sheet 4 carried 67–103 characters (the section heading
`04 Real chats with the bot` and its lead), sheet 6 the four captions that belong under the
screenshots (406–497 characters, since the pricing section starts on the same sheet). The cause
is the same arithmetic that once made the phone mockups 45 % thinner than their files: the strip
is `repeat(3,1fr)` of the text width, and a phone screenshot is 2.17 times as tall as it is wide.
Portrait A4 gives the strip 678 px — each figure 215×495 px inside a sheet box 1032 px tall,
comfortable. Landscape gives it 1007 px — each figure 324×730 px inside a box 703 px tall: the
figure is taller than the sheet it stands on, and `figure.shot{break-inside:avoid}` carries each
one whole to a sheet of its own, with the captions flowing after it.

**Fixed by printing the phones at one size on paper**: `.shots{max-width:678px}` inside
`@media print` — 678 px is exactly what the strip measures on a portrait A4, so a wider sheet no
longer enlarges it. Landscape went from **11 sheets to 10**, the zero-character sheet is gone, and
the thinnest sheet in any language now carries 110 characters (ru; 112 uk, 115 hi, 126 es,
129 id, 135 en, 142 pt, 147 vi). Portrait A4 and Letter did not move by a single character per
sheet: compared sheet by sheet, character by character, before and after the change.

**Centring came from looking, not from measuring.** With the cap alone the strip sat at the left
edge of a 1007 px column while its own section heading is centred on the sheet — a 678 px block
with 329 px of white to its right. `margin-inline:auto` puts the strip's centre at 524 px in a
1047 px sheet, which is the heading's centre. On portrait A4 the strip is the full text width, so
there is nothing to centre and nothing changed. This is the one part of the block that no battery
would have caught: the numbers were green before the rule and after it.

**Letter and A5 were measured, not fixed.** Letter prints 8 sheets where portrait A4 prints 7
(en/es/pt/hi/tr/vi), because the sheet is 18 mm shorter and the same content needs one more sheet;
no sheet is empty, and the strip fits (700×523 px in a 963 px box). A5 prints 12–14 sheets, and
its sheet 6 carries 57–64 characters (125 in vi, 160 in pt) — the three phones with their captions
and nothing else, which is a picture, not waste. Both are budgeted instead of "fixed": a page
printed on a smaller sheet takes more sheets, and that is arithmetic, not layout.

**The gate.** New `landing-print-paper.py`: **939 checks, 0 problems** — 9 languages × (Letter,
A4 landscape, A5), and per language: `pdfinfo` agrees with the text chunking, no sheet empty of
text, no sheet under 0.15 % ink, no sheet ending with its own `h1/h2/h3`, the footer not alone on
the last sheet (last-sheet characters ÷ footer characters > 1.20, the threshold measured
yesterday), and sheets within `tools/print-papers.json`. Control `--mutate railwidth` removes the
cap and turns **18 checks red**: in all nine languages landscape returns to 11 sheets and to a
sheet with zero characters. One static marker on each of the nine pages holds the rule in the
sweep.

**What this does not prove.** A5 landscape is not covered and will not be: three phones across a
186 mm sheet is 62 mm per phone, and a phone screen 62 mm wide is 134 mm tall on a 128 mm sheet —
no CSS makes that fit without printing the screen smaller than its own captions. And landscape
sheets are printed with longer lines than portrait ones: median 97 characters against 84 (max 137
against 94). That is a typographic decision — cap the column on a wide sheet and pay for it in
sheets — so it is measured and left to its own block rather than quietly changed here. Chromium's
PDF only, no real printer, and nothing here says anyone should print a landing page.

**Files.** `index-src.html` (the strip rule in `@media print`), every built page,
`tools/print-papers.json` (new); `landing-print-paper.py` (new), the sweep marker and `SKILL.md` in
the `stars-bots-ops` skill; this entry and the "Printing" paragraph above.

## The policy was printed well on one of the four sheets the dialog offers (25.10.2026)

The print block has been measured five times now — four batteries for the landing page, one for the
legal pages — and every one of those runs printed **portrait A4**. The dialog beside it offers
Letter, a landscape switch and A5. A probe of the three pages outside the generator on the three
sheets nobody had used, before any fix:

* **Letter / `privacy.html`: 8 sheets, and the eighth held 40 characters** — the footer line alone,
  0.08 % ink. The same defect that was fixed on portrait A4 yesterday, one sheet of paper away.
* **A4 landscape / `privacy.html`: sheet 3 ended with the heading "5. Your rights and deletion"** —
  the section itself started on sheet 4.
* **A5 / `terms.html`: sheet 8 ended with "12. Изменения"**, for the same reason.

Portrait A4 was clean on all three pages (7 / 5 / 1 sheets), which is exactly why nobody had looked.

**Cause, and it is not the paper.** The landing page's `@media print` carries two ideas the legal
pages never received: `h1,h2,h3{break-after:avoid}` (a heading may not be the last thing on a sheet)
and a paper rhythm tighter than the screen's. Without the first, a heading sits at the foot of a
sheet; without the second, the policy's 15 section gaps and 40 paragraph gaps add up to more than a
sheet, so on Letter — 18 mm shorter — the footer was pushed onto one of its own.

**Fixed by giving both legal print blocks the same two ideas**: headings `break-after:avoid`, list
items `break-inside:avoid`, and paper spacing (paragraphs 12 → 9 px, lists 14/6 → 10/4, `h2`
30/10 → 20/8). After: **Letter 8 → 7 sheets**, footer back on the section sheet (ink 0.08 → 5.90 %,
last sheet 2 418 characters); **A4 landscape stays 10 sheets but no sheet ends with a heading** and
the thinnest sheet carries 2.03 % ink instead of 1.15 %; **A5 terms 9 → 8 sheets** with the heading
back on its own section (thinnest sheet 1.52 → 5.19 % ink). Portrait A4 did not change in sheet
count (7 / 5 / 1); its policy last sheet carries 1 826 characters against 2 097 before, because the
compaction moved the break points and the footer now shares a fuller sheet.

**The gate.** `landing-print-pages.py` was rewritten from one paper to four: 12 page × paper pairs,
**342 checks, 0 problems**, budgets in `tools/print-pages-papers.json` (A4 7/5/1, Letter 7/5/1,
landscape 10/7/1, A5 13/8/1). Every old check survived (page count from `pdfinfo` against the text
chunking, ink per sheet, no heading at the foot, no two-word fragment, no non-final sheet under 200
characters) and the footer ratio — last-sheet characters ÷ footer characters > 1.20, the threshold
measured yesterday on the landing page — now runs on every pair instead of only on portrait A4. The
control `--mutate` strips `@media print` and turns **17 checks red**, including `pdfinfo` disagreeing
with the text chunking (8 against 7) because on A5 the stripped page leaves a sheet with no ink at
all — which is why the two counts are compared rather than one trusted.

**One false positive was fixed, not worked around.** The "sheet ends with a one- or two-word
fragment" check fired on A5 / `404.html`, where the last line of the page is the footer link
"Terms": a document's last line is allowed to be short — nothing follows it. The check now runs on
every sheet except the last, and a heading is no longer reported twice (once as a heading, once as a
fragment), which is what the A5 terms failure had been doing.

**What this does not prove.** Chromium's PDF only, no real printer, and A5 landscape is still out
of scope (a phone screen does not fit a 128 mm sheet without printing it smaller than its captions).
The compaction moves break points on every paper, so the numbers in the budget are the only thing
standing between a reader and a footer-only sheet: that is why it is a gate and not a note. And
nothing here says a legal page needs to be printed at all — it says that when it is, the paper the
reader picked is the paper we measured.

**Files.** `privacy.html`, `terms.html` (the two print blocks), `tools/print-pages-papers.json` (new),
`tools/lastmod.json`; `landing-print-pages.py` (rewritten for four papers), two new sweep markers per
legal page in the `stars-bots-ops` skill; this entry and the "Printing" paragraph above.

## A landscape sheet set its text 260 mm wide (25.10.2026)

Yesterday's block measured this and left it to its own block in one line: "cap the column on a wide
sheet and pay for it in sheets". Measuring it before fixing it changed both the size of the defect
and the price of the fix.

**The old number was inflated by the tool.** "Median 97 characters per line, max 137" came from
counting rows of `pdftotext -layout`. On a wide sheet that tool puts the three cards of one grid row
on one row of text: 137 "characters" were three different cards standing side by side, and the
"line" ran from the left edge of the first to the right edge of the third. Measured by coordinates
instead (`pdftotext -bbox`: words on one baseline within ±2 pt and no gap over 8 pt are one line; a
gap of tens of points is the next card), the defect is real but different: the longest line of
**running text** on A4 landscape was **260 mm in Russian, 244 mm in English and 253 mm in Spanish
and Portuguese**, against **178 mm** on portrait A4 — about 100 characters where the site's own
portrait measure is 85. Hindi was already at 195 mm and Ukrainian at 192 mm, which is why those two
never looked wrong.

**Cause.** The shots strip got a cap on paper (678 px) because a phone 324×730 px does not fit a
703 px sheet. The text column never got one and never needed one on portrait: `main` is unbounded,
but the inner `.wrap{max-width:1060px}` is 280 mm, more than every paper the dialog offers, so only a
sheet wider than 280 mm could expose it — and the landscape sheet is 297 mm with 277 mm of text
area.

**Fix.** `@media print{main,body>footer{max-width:210mm;margin-left:auto;margin-right:auto}}` — the
paper column is never wider than the sheet's short side, and the footer sits in the same column
instead of starting at the sheet's left margin. The rule is a no-op on portrait A4 (190 mm of text
area), Letter (196) and A5 (128) by arithmetic, and the measurements agree to the character: Letter
and A5 came back with the same sheets and the same characters per sheet as before the rule. On A4
landscape the longest line fell to **191.7–199.7 mm across the nine languages**.

**Sheets: eight languages unchanged, one +1.** Landscape stayed at 10 sheets in eight languages;
Indonesian needs 11, and that eleventh sheet carries 480 characters — real text pushed over, not a
footer alone. The trade was taken deliberately (a 196.8 mm line instead of 251 mm for one sheet in
one language) and written into `tools/print-papers.json` next to the number, because a budget that
grows without a reason stops being a budget.

**The legal pages were measured and left alone.** Their column is not the sheet's: `.wrap{max-width:
820px}` is 217 mm, so their longest printed line is 199.8 mm on A4, 205.4 on Letter, 206.1 on
landscape and 137.6 on A5 — under the threshold already. The landing's rule was tried there first
and reverted: on Letter it costs the policy a sheet of its own (7 → 8, the eighth holding the footer
and nothing else), which is exactly the defect the previous block removed. One thing measured and
not fixed, because it is a different block: the legal pages declare no `@page` margins while the
landing declares 12/10 mm, so under a zero-margin print they run 5 mm from the paper edge and
otherwise take their margins from the reader's dialog. Giving them the landing's margins costs
privacy 7 → 9 sheets on A4 and 13 → 18 on A5 with the footer alone on the last one — measured, not
started.

**The gate.** Both print batteries now refuse a printed line wider than **210 mm**, measured by word
coordinates, on every sheet of every paper: 27 new checks in `landing-print-paper.py` (**969 checks,
0 problems**) and 12 in `landing-print-pages.py` (**354, 0**). Controls prove the check bites where
the defect was and only there: `--mutate colwidth` takes the cap off and turns **7 checks red** in
landscape (the seven languages whose line actually reaches the edge — Hindi and Ukrainian stay green
at 195 and 192 mm), while portrait, Letter and A5 stay green; on the legal pages the same mutation
turns **2 red** (privacy and terms in landscape, 286.9 mm without their `.wrap` cap).

**What this does not prove.** Chromium's PDF only, no real printer. The cap moves page breaks, so the
Indonesian budget is one number standing between a reader and a half-empty sheet. And 210 mm is still
about 90 characters: this block brings a wide sheet back to the site's own measure, it does not make
that measure narrow — on portrait A4 the same page still prints 178 mm lines.

**Files.** `index-src.html` (the rule), the nine built pages, `tools/print-papers.json` (one number
and its reason); `landing-print-paper.py` and `landing-print-pages.py` (the line-width check in both,
a `colwidth` control in both), one sweep marker on each of the nine pages in the `stars-bots-ops`
skill; this entry and the "Printing" paragraph above.

## The policy's first line was printed above the edge of the paper (25.10.2026)

The previous block ended with one item written down and not started: *"the legal pages declare no
`@page` margins while the landing declares 12/10 mm, so under a zero-margin print they run 5 mm from
the paper edge and otherwise take their margins from the reader's dialog."* This block took it, and
the first measurement found the sentence too kind.

**What was actually on the paper.** Printed with no margins, `privacy.html` and `terms.html` put the
top line of *every* sheet at **−1.2 mm** — above the paper's edge, not "5 mm from" it. The tightest
word on A4 is «7.» on sheet 7, on A5 «Условия» on sheet 5, on Letter «A» on sheet 2: on a real
printer those lines lose the tops of their letters. The sides sat at 5.3 mm, the bottom at 0.1 mm. The
`404.html` card was never near an edge (27–85 mm) — it is centred in a card, and it is the honest
control: the defect belongs to flowing text, not to the site.

**Why the containers could not fix it.** A container's `padding` guards the top of the first sheet
and the bottom of the last one; everything in between is the paper's business. Only `@page` margins
repeat on every sheet, which is why the landing has had them since the first print block and the
legal pages had none — they were written before anyone printed more than the landing.

**Why no battery had caught it.** Every print battery prints through Chromium with zero margins, so
the defect was present in every one of the 354 green checks: they counted sheets, ink and line width,
and never asked where the first word of a sheet stands. That is now a check of its own.

**How much margin to buy.** Measured, not guessed — the same twelve page × paper pairs with `@page`
margins of nothing, 6, 8, 10 and 12/10 mm, reading the gap from every word to every edge:

| margin | top gap | privacy A4 / Letter / landscape / A5 | terms A4 / Letter / landscape / A5 |
| --- | --- | --- | --- |
| none | −1.2 mm | 7 / 7 / 10 / 13 | 5 / 5 / 7 / 8 |
| 6 mm | 4.8 mm | 8 / 8 / 10 / 15 | 5 / 6 / 7 / 9 |
| 8 mm | 6.7 mm | 8 / 8 / 10 / 16 | 5 / 6 / 7 / 10 |
| 12/10 mm (the landing's) | 10.7 mm | 9 / 9 / 11 / 18 | 6 / 6 / 8 / 10 |

Twelve-ten is out at once: it costs the policy two sheets on A4 and five on A5, and its last sheet
carries 193 characters. Eight millimetres is out for a subtler reason — on A5 it buys a sixteenth
sheet holding 88 characters, and on Letter a sixth for the terms holding 89, which is the
footer-alone defect this site has already fixed twice. Six millimetres is the cheapest margin that
puts a letter beyond the 4 mm floor: after it the top gap is 4.8 mm, the sides 11.0–11.4, the bottom
5.6, on all four papers and all three pages.

**What the six millimetres cost, and to whom.** The policy goes 7 → 8 sheets on A4 and Letter and
13 → 15 on A5; the terms go 8 → 9 on A5 only, because their paper rhythm was tightened at the same
time (`p` 9 → 7 px, `li` 4 → 3, `h2` 20/8 → 16/7, `h3` 16/6 → 14/5) to hold Letter at five sheets —
without it the same margins added a sixth sheet holding one footer line. The policy kept the looser
rhythm on purpose: tightening it changed no sheet count and only moved 300 characters off the last
sheet, and a fuller last sheet reads better than a denser page. But the cost falls on a print that
almost nobody makes. **Against the print a reader actually gets** — the dialog's default margin of
0.4 in, which is 10.16 mm — the numbers were 8 / 9 / 17 sheets for the policy and 6 / 6 / 10 for the
terms; with the page's own 6 mm they are 8 / 8 / 15 and 5 / 5 / 9. Nothing gets worse; the two
papers where the reader's default was wider than the page's own margin get better by a sheet or two.

**The gate.** `landing-print-pages.py` now measures the gap from every word to all four paper edges,
on every sheet, and refuses anything under **4 mm** — the width of the unprintable strip on a
consumer laser, 3 mm on an inkjet. Twelve new checks; the battery reads **391 checks, 0 problems**,
where the count above 354 comes from the five extra sheets the margins buy. Controls: `--mutate
nopage` puts the margins back to zero and turns **8 checks red** — privacy and terms on all four
papers, `404` green because it truly is far from every edge — `--mutate colwidth` still **2 red**
(274.8 mm lines in landscape without the `.wrap` cap), `--mutate` now **22 red** instead of 17,
because stripping the print CSS also exposes the edges.

**What this does not prove.** Chromium's own PDF writer, not a printer: `@page` wins there even when
the margin is explicitly passed as zero, and the interactive dialog's "None" was not tested — no
script can click it. The 4 mm floor is a convention, not a measurement of the reader's hardware; a
printer with a 6 mm dead zone would still trim the first line on paper printed with no margins, which
is why the guard is a floor and not a promise. And the budgets in `tools/print-pages-papers.json`
were raised by hand for the sheets this block bought — a budget that only ever rises stops being a
budget, so each number carries its reason in the file.

**Files.** `privacy.html`, `terms.html`, `404.html` (the `@page` rule; 404's lives in
`tools/build.py`), `tools/print-pages-papers.json` (four budgets and the reason), `landing-print-pages.py`
(the edge check, the `nopage` control, 391 checks); one sweep marker in the `stars-bots-ops` skill;
this entry and the "Printing" paragraph above.

## The hero badge pointed at a product the platform had deleted (25.10.2026)

The print thread ended last block with the legal pages getting "@page{margin:6mm}". One default of
the print dialog had never been measured: the checkbox that is already ticked when the dialog
opens — "Headers and footers". Measured first, before assuming anything. With Chromium's own
date/title line at the top and URL/page-number line at the bottom, the header's ink sits at
5.6-7.5 mm from the top on every sheet and the first line of body text starts at 8.0 mm on a
continuation sheet — a 0.5 mm gap and no overlap; the footer's ink runs 289.9-292.0 mm on A4
against a last line ending at 284.9 mm, a 5.1 mm gap; the sheet count is identical with the
checkbox on and off on all four papers (landing 7 / 8 / 10 / 14, legal pages 8 / 5 / 1); and no
row of ink covers more than 55% of the sheet width on any of the 78 sheets of the sixteen
documents. Nothing to fix: the browser keeps its own lines inside the margin, and the site cannot
switch that checkbox off from CSS.

**Then the links.** All 70 external addresses still answered 200 — which is exactly why the
defect had survived: 200 is not the same as "the page is still there". A content check found it
in one line: `launchigniter.com/product/uchisambot-study-helper` answered **200** with the title
**"Product Not Found - LaunchIgniter"**, and the platform's sitemap lists 2 824 product pages
with our slug in none of them. That badge was in the hero — the third thing a visitor sees,
after the headline and the button — and it was the only mark on the page whose click could prove
nothing.

**The first version of the gate stayed green, and that mattered.** The first content check
searched the whole response for the product name and passed: the slug survives in the Next.js
RSC payload of the "not found" page. The gate now strips `script/style/noscript/svg`, treats a
`<title>` containing "not found", "404" or "не найден" as a failure, and looks for the name only
in text a person can read. Failed first after that: red on exactly one address, the right one.
A search engine can be fooled the same way, which is why the check reads text and title, not bytes.

**Fix.** The hero badge is removed (its markup, its three CSS rules and the `order:6` step of the
mobile hero), its file `img/badges/launchigniter.svg` is deleted (the published tree went from
109 files to 108), the platform is gone from `BADGE_ALTS` in `tools/build.py`, and section 7 of
the policy no longer lists it in either language — the policy now says seven platforms and names
seven. The footer strip keeps its eight badges and still lays out 4 + 4; the hero ends with the
three chips. The cost is named: the page loses its only above-the-fold third-party mark. The
alternative — keeping the badge and pointing it at the platform's front page, as four other
badges already do — was rejected, because the hero would then carry a claim whose page the
platform has deleted. If the owner wants a mark back in the hero, the LiftOff "No. 1 of the Day"
award is the one we can prove, and it would have to leave the footer strip (seven badges = 4 + 3,
a ragged row).

**Gate.** `landing-external-links.py` (stars-bots-ops) now requires every link whose path contains
the product's slug to mention the product in its visible text: 40 links confirmed and 0 problems
after the fix, 1 problem before it. Badges that lead to a platform's front page print a note
instead ("the product cannot be checked on a front page") — those four stay a manual question,
and only showmebest.ai's sitemap still lists us.

**Regression.** Sweep 2 731 checks, 0 failed (badge counts 9 -> 8, localized alts 8 -> 7, hero
mobile steps 6 -> 5); browser smoke: all eight badge files cut -> eight links hidden, one file cut
-> seven visible, 0 problems; visual pass: 8/8 badges loaded, rows [4, 4], 0 problems; print 147
checks, four papers 969, legal pages 391, first screen 252 — all clean; live tree comparison 26
files OK and the 404 probe still answers with our own page. Published through
`tools/publish-branch.sh` to both mirrors (`gh-pages`, 108 files), and the live pages no longer
contain the dead address.

**What this does not prove.** That the four home-page badges are still true: a platform's front
page does not list its products, so nothing automatic can confirm those launches, and only
showmebest.ai's sitemap confirmed itself. That remains a manual question for the next block, and
it is written here rather than in a task list nobody opens.

**Files.** `index-src.html` (markup, three CSS rules, the mobile order step), `tools/build.py`
(`BADGE_ALTS`), `img/badges/launchigniter.svg` (deleted), `privacy.html` (section 7 in both
languages and its own date), the nine built pages and their markdown twins, `tools/lastmod.json`,
`sitemap.xml`; `landing-external-links.py` (the soft-404 check) and four counts in
`landing-sweep.py`, `landing-browser-smoke.py`, `landing-visual-pass.py`; this entry and the
footer paragraph above.

## The footer promised seven platforms; one of them had no page to show (25.10.2026)

The previous block ended with a sentence it could not act on: four badges led to the front pages
of launch platforms, a front page never lists its products, so nothing automatic could say whether
we were still there. The honest next step was not to guess but to ask each platform the only
question it can answer — does its own catalogue contain a page about us?

**The index first, the page second.** Every platform publishes a sitemap; that is the list it
makes for search engines, and a product that is not in it is not being shown to anyone who is not
holding a direct link. ShowMeBestAI's sitemap (4 497 addresses) contains
`showmebest.ai/ai-tools/kerio-byte-github-io-uchisambot`, and that page answers 200 with the
product named five times in the text a person reads. The badge, however, pointed at
`showmebest.ai` — the front page. So the claim was true and unprovable at the same time, and the
cost of the unprovability was paid by the visitor: the click landed on a catalogue search instead
of the page about the bot.

**OpenHunts was the other kind of answer.** Its sitemap lists 4 077 addresses, 3 837 of them
`/projects/…` pages. Not one of the 3 837 is ours, and the direct address
`openhunts.com/projects/uchisambot-study-helper` answers **200** with the title **"Project Not
Found"** — the same soft-404 shape as LaunchIgniter, and the same trap inside it: searching the raw
response for the product name finds it twice, because the slug lives on in the Next.js RSC payload.
Read only the text a person sees, and the name appears zero times. The badge pointed at
`openhunts.com`, the front page, where this could never show.

**What this cannot tell.** Whether we were ever listed there and the page was removed, or never
listed at all. The usual way to settle that — the Internet Archive — is not evidence here: its CDX
API returns an empty list even for pages that exist right now (LiftOff's product page and Fazier's
launch page both came back empty), so "no capture" would only mean "the API answered nothing".
Therefore the only thing that can be said is the thing that matters for a badge: there is no page
today, and a badge is a promise about today.

**Fix.** ShowMeBestAI's badge now points at our page there — the soft-404 gate checks it from now
on like any other product link. OpenHunts' badge is removed with its markup, its file
`img/badges/openhunts.webp` (published tree 108 → 107 files), its entry in `BADGE_ALTS` in
`tools/build.py`, and its name from section 7 of the policy in both languages (seven platforms →
six). The strip is seven badges now: 4 + 3 on a desktop, 2 + 2 + 2 + 1 on a phone, both centered.
The cost is named: the second row is ragged, and one platform fewer appears on the page. Keeping
the badge because "everyone else has eight" would have kept a promise nobody can check —
the same trade the hero badge lost earlier today.

**Gate.** `landing-external-links.py` used to print a note for a badge that lands on a front page
("the product cannot be checked on a front page"). That note was the hole: it made an unverifiable
badge look like a clean result for months. Now every link wrapping a file in `img/badges/` must land
on a page whose visible text names the product; a front page fails by definition, and the printed
reason says what to do — point the badge at our page or take it off. Negative control: putting
`https://showmebest.ai` back into one built page turns the gate red on exactly that address
(`значок ведёт туда, где продукта нет: no`, 1 problem), and the built page is restored afterwards.

**Regression.** Sweep 2 739 checks, 0 failed except the publication staleness every unpublished
build shows (footer hosts 7 → 6, localised alts 7 → 6, degrade-on-error 8 → 7, policy platforms
seven → six, plus a new "no openhunts badge" check in all nine languages). Negative control for
the sweep: adding the badge back reddens 23 checks, the new ones among them, and the tree is
rebuilt clean afterwards. Browser smoke: 18 runs, 0 problems; cutting all seven files hides all
seven links, cutting one leaves six visible. Visual pass: 9 languages × 2 viewports, 0 problems,
badges 7/7, rows `[4, 3]` and `[2, 2, 2, 1]`. Print: 147 + 213 + 391 checks, 0 failed (the strip is
`display:none` on paper, so pagination did not move). Submission kit redrawn — `tools/build.py` is
one of its recorded inputs: four 1920×1080 cards, manifest rebuilt, 7/7 kit checks green.

**What this does not prove.** That the six remaining pages will still be there tomorrow: a platform
can delete a page the day after it is checked, and only the next run of the gate will see it. And
it does not say a badge is worth its space — that is a marketing question, not a link question.

**Files.** `index-src.html` (the ShowMeBestAI href, the OpenHunts block removed and explained in
place), `tools/build.py` (`BADGE_ALTS`), `img/badges/openhunts.webp` (deleted), `privacy.html`
(section 7 in both languages: six platforms, each picture leads to our page there), the nine built
pages, `tools/lastmod.json`, `submission-kit/*` (four cards + manifest); `landing-external-links.py`
(the badge rule, the dead duplicate `domain_alive` removed), `landing-sweep.py` (four counts and
the "no openhunts badge" check), `landing-browser-smoke.py` (7 / 6), and this entry with the footer
and strip-shape paragraphs above.

## The phone header had no room left, and the Ukrainian page proved it (25.10.2026)

The text-spacing gate (WCAG 1.4.12) had been asking two pages — English and Russian — at one width,
1280 px. That is the pair the author reads himself, and it is the same hole the zoom gate had until
24 October: nine languages existed, two were measured. The first wider run (nine languages × 320,
420 and 1280) answered with a defect that no screenshot would show, because the page did not look
broken — it moved.

**The measurement.** At 320 CSS px the header row is exactly as wide as the page margins:
20 (padding) + 126 (logo) + 22 (gap) + 10 (switcher margin) + 122 (switcher) = 280 = 320 − 2×20.
Zero slack. The WCAG 1.4.12 overrides (line-height 1.5, letter-spacing .12em, word-spacing .16em,
paragraph spacing 2em) grow the brand 126 → 133 and, in Ukrainian, the switcher label 122 → 139:
the row needs 304 px. The document becomes **324 px wide on a 320 px screen** — a 4 px pan, and the
one thing a phone user with enlarged letter spacing could do about it is drag the page sideways.
Two more languages failed the same run without any page scroll: Portuguese and Indonesian put the
switcher's right edge at 318 and 314 px against a content edge of 300 — the control ate 18 and 14 px
of the page's right margin, invisible to the eye and to every existing gate, which measured scroll
and never the row itself.

**Fix.** One rule, no new markup: on phones the row is `justify-content:space-between` with no gap,
and the switcher loses its 10 px left margin — `@media(max-width:760px){.top-in{justify-content:space-between;gap:0}.lang-dd{margin-left:0}}`.
The dead space between the logo and the switcher (32 px) becomes slack, and the switcher sits at the
right margin, which is where the desktop layout already puts it after the nav. After the change: the
document is 320 px wide in all nine languages, the switcher's right edge lands exactly on the margin
(300 / 340 / 400 px at those widths), 8 px spare for the longest label at 320 and 2 px at 340 —
the widest case is Portuguese at 340, not Ukrainian at 320, which is why the spare is counted, not
assumed.

**The visible cost, named.** The switcher now sits at the right margin instead of directly after the
logo: at 420 px it moves 93 px right (its box went from 199–295 to 292–400), at 320 it moves 5 px
(English) to 28 px (Hindi). Nothing overlaps, nothing is cut, the header keeps its 62 px height —
but this is a layout decision on every phone, and one word from the owner reverts it. It was taken
because the alternative was a red gate with an exception written next to it, and the exception is
what this project has already paid for once: a note that made an unverifiable badge look clean for
months.

**Gate.** `landing-a11y-extra.py` section D was rewritten: nine languages × 320/420/1280 = 27
measurements, three checks each — no horizontal scroll, no text cut by its own box (the actual
1.4.12 requirement, measured with the same `CLIP_JS` the zoom gate uses), and the header row stays
inside the margins (switcher's right edge ≤ content edge, brand's right edge ≤ switcher's left).
A floor check asserts that 27 were asked, so a shortened language list cannot leave the section
green and empty. Negative control: a copy of the tree with the rule stripped out fails exactly four
checks — pt 318 > 300, id 314 > 300, uk 324 > 300 and uk scroll 4 px; with the rule the same battery
is 267 checks, 0 failed. The sweep grew by a static guard per language page (nine checks, 2 748 in
total) which is red if the rule disappears from a built page — behaviour is measured in the browser,
the rule's presence is measured without one.

**Regression.** Sweep 2 748 / 0 after publication (the same sweep, before publishing, showed only
the staleness line — the live site was one build behind). WCAG 2.2 targets and focus 43 / 0;
first-screen 252 / 0; visual pass nine languages × two viewports, problems 0, badges 7/7;
browser smoke 18 runs, 0 problems; environment preferences 45 / 0; print of the main page 213 / 0
(the header is `display:none` on paper, so pagination did not move). Published from
`tools/publish-tree.py` — 107 files to both mirrors, Pages source read back as `gh-pages/`.

**What this does not prove.** That the new position is the prettier one — that is taste, and the
numbers above are not an argument about taste. That the gate itself agrees across engines: section D
is Chromium only, as it always was; the three failing pages were checked by hand on the live site
(uk, pt, id at 320 with the same overrides) in Chromium, Firefox and WebKit — 320/320 and `ok=True`
in all nine runs, so the rule is not a Chromium accident, but that is a spot check, not a gate.
And that spacing wider than the standard's test values still fits: at 320, letter-spacing beyond
.12em would need slack the header does not have, and the honest answer there is the two-row layout
the wrap experiment showed (it changed the baseline look in four languages, so it was rejected in
favour of the right-margin rule).

**Files.** `index-src.html` (the media rule and its explanation), the nine built pages with their
`og` headers untouched, `tools/lastmod.json`, `sitemap.xml`; `landing-sweep.py` (one check),
`landing-a11y-extra.py` (section D: three checks per measurement, the floor, the docstring),
`docs/council-20261015.md` (the sweep count and what it now covers), `evidence/block-20261025i/`
(sweep before and after publication, the battery logs, the negative control, the three-engine spot check of the live site), and this entry.

## The header row was proven in one engine, and the form had never been measured with the keyboard up (25.10.2026)

Two parameters had never varied in any battery this project owns: **the engine** — every wide
battery is Chromium — and **the height** — each battery fixes the screen and keeps it until the
run ends. The previous entry named the first limit itself: the three-engine check of the new
header rule was *"a spot check, not a gate"*. The second limit had never been named, and it sits
on the only conversion path the page has: the contact form on a phone, where the keyboard takes
half the screen the moment a finger touches the field.

**The header, in three engines.** The rule of 25.10 (`@media(max-width:760px){.top-in{justify-content:space-between;gap:0}.lang-dd{margin-left:0}}`)
was counted, not measured, everywhere except Chromium: Portuguese at 340 px kept 2 px of spare.
The width of a word comes from our own woff2, but the shaper is the engine's — a different one
can set the same letters a pixel or two wider, and 2 px of spare is not a margin. `landing-header-engines.py`
measures the row in Chromium, Firefox and WebKit at nine languages × six widths of the ordinary
page (320, 340, 420, 760, 761, 900) and × three widths under the WCAG 1.4.12 overrides
(320, 340, 420): four checks per run — the document is not wider than the screen, the switcher's
right edge stays inside the page margin, the logo does not touch the switcher, the header menu
does not touch it either. **973 checks, 0 failed** (243 runs plus a floor). All nine languages put
the switcher's right edge exactly on the margin in all three engines, which is what the rule
promised.

Width 761 is not decoration: it is the first width **without** the phone rule, and it had never
been measured by anyone — the tablet battery starts at 768, the phone batteries stop at 760, so
seven pixels of desktop layout with a visible header menu lived between them. They are clean.

**The negative control, and a weak one that lied.** Removing the rule from a copy of the tree
turns the same battery red in five places: pt `ddRight=317.5` against a limit of 300, id 313.5,
uk 324.2 **and** the document 324 px wide on a 320 px screen (a 4 px sideways pan), plus uk at 340.
The first attempt at this control replaced the rule with `.top-in{gap:0}` — half the fix left in
place — and produced exactly **one** red. A control that keeps half the fix is a control that
hides the defect; the entry records it because the weaker version looked convincing.

**The keyboard.** On 320×568 — the smallest phone the batteries know — an open keyboard leaves
308 px of visible page. `landing-keyboard-form.py` taps the e-mail field, shrinks the viewport the
way Android Chrome does (layout viewport = screen minus keyboard), and measures nine checks per
run at nine languages × three phones (320×568 → 308, 360×800 → 500, 390×844 → 500): no sideways
scroll; the field being typed into is visible for at least 60% of its height; the sticky bar is
not shown while the form is in frame; the send button fits entirely in the frame after scrolling
to it and is not covered by the bar; the typed text survives the keyboard opening; the page stays
at the form instead of jumping to the top; after the keyboard closes the bar does not cover the
form. **244 checks, 0 failed.** The 60% threshold is deliberate: a browser scrolls to the caret,
not to the frame, and the probe showed the input's bottom edge sitting 4 px under the line at
320×568 — demanding the whole frame would be a gate that cries wolf on every run.

**A harness failure worth writing down.** The re-run of the tablet battery failed instantly with
`Address already in use`: the header probe was holding port 8266, which is the tablet battery's
default. That is the harness fighting itself, not the site; the same battery re-ran green
(1 804 checks, 0). Batteries with fixed ports cannot be run in parallel.

**Regression — the whole battery after the last CSS change.** 31 batteries (the 29 of the
harness plus the two new ones), 12 124 checks, 0
failures, plus the static sweep 2 748 / 0 and axe on 12 pages, 0 violations: a11y-extra 267,
wcag22-targets 43, first-screen 252, text-clip 148, rotate 288, tablet-menu 162, tablet-page
1 804, landscape-page 956, backtab 120, deeplink 684, video-motion 444, viewports-extra 94,
env-prefs 45, fonts 39, cwv 69, third-party 108, print 147, print-main 213, print-paper 969,
print-pages 391, print-contrast 3 543, live-runtime 121, the two new batteries 973 + 244; runs
without a checks count: visual pass 18 screens, render-check 11 pages, browser smoke 18,
cross-engine 60, glyph fallback 12 pages, Nu 11 pages, link audit 11 pages. Nothing was published:
the site tree did not change in this block, and the sweep's publication checks read the live bytes
green against the tree.

**What this does not prove.** That WebKit-on-Linux is Safari-on-iOS: same engine family, different
build, different font stack underneath. That shrinking the viewport is the same event as a Gboard
appearing: the height is a fair approximation and the browser's own scroll-into-view heuristic is
not reproduced, which is exactly why the gate asks for 60% and not 100%. That printing **from a
phone** works: Chrome on Android lays the page out at the viewport width, `page.pdf()` lays it out
at the paper width, so the phone-print case is not covered by any battery here and is not claimed —
it would need a real device. And that the new gates would have caught today's site: they are green
now, which is the only thing they say.

**Files.** `docs/council-20261015.md` (two batteries added to "what guards this"), the skill's
`scripts/landing-header-engines.py` and `scripts/landing-keyboard-form.py` (new, with their
docstrings carrying the numbers), `references/landing-qa.md` (the two holes, the controls and four
pitfalls), `SKILL.md` (the CSS-change battery list), `evidence/block-20261025j/` (37 logs:
the 29 harness batteries, the tablet re-run, the two new gates, both negative controls,
the sweep, axe), and this entry.

## A browser setting that grows only the text pushed the header off the screen (25.10.2026)

Thirty-one batteries have measured how this page behaves at a different *scale*: zoom at 200 %,
the WCAG 1.4.12 spacing overrides, rotation, a short landscape screen, an open keyboard. None of
them measured a different *kind* of scale — the browser's own **minimum font size**. Chrome and
Edge offer it as a slider that stops at 24 px; Firefox has the same control under Settings →
Fonts → Advanced (the `font.minimum-size.*` prefs). It raises the text and nothing else: boxes,
padding and a rigid header row keep their pixels. Zoom moves both, so no zoom test can reproduce
it, and the phone header row fitted earlier the same day had been counted in pixels.

**What it did.** At a 24 px minimum, on a 320 px screen the Ukrainian page scrolled sideways by
32 px, Portuguese by 21, Indonesian by 13. At 761 px — the first width where the header menu
appears, and a width no battery had touched until the previous block — Russian scrolled sideways
by 124 px, Ukrainian by 116, Portuguese by 98, Spanish by 86. At 900 px Russian put the switcher
5 px past the margin; at 1024 px everything was clean. The cause was one line,
`.top-in{height:62px}`: a rigid row that could neither wrap nor give the switcher less room than
its own words.

**A defect the setting did not create, only exposed.** At the ordinary font, Indonesian at
320–340 px had always been squeezed: its label is 166 px wide, the logo takes 147, and the row
has 280–300 px. With wrapping forbidden the browser did what flexbox does — it shrank the box, and
"Bahasa Indonesia" broke into two lines inside a 38 px pill (measured: label height 44.8 px
against a one-line 22.4). No battery ever saw it, because nothing overflowed and nothing was
clipped: every box sat inside the margins, the words were simply the wrong shape. A screenshot of
the old state is kept in the evidence folder.

**The fix, and its price.** The row wraps (`flex-wrap:wrap`, `min-height` instead of `height`),
nothing in it may shrink (`flex:0 0 auto` on the brand, the menu and the switcher) and the
language label cannot break (`white-space:nowrap`). Wrapping rather than truncating: a cut language
name is worse than a second line. The price is named — Indonesian at 320–340 px now carries a
two-row header, 74 px instead of 62; it is the only place where the content genuinely does not
fit, and one word from the owner ends it. Russian, Portuguese, Vietnamese and Ukrainian at 761 px
with a 24 px minimum get three rows (brand, menu, switcher): that is what "nothing fits" looks like
when no word may be lost.

**The consequence that had to be fixed too.** A taller sticky header broke anchor arrival.
`html{scroll-padding-top:84px}` is 63 px of header plus 21 px of air; with two rows the heading
landed 12 px *under* the header at 320 px and 52 px under it at 761. A script at the end of the
body now measures the header and sets the padding to its height plus 20 px — and only when the
header is taller than usual: at 63 px it removes the inline style, the CSS rule stays in force,
and the ordinary 84 px landing is untouched (the arrival battery still measures it). One detail
cost a red line and is worth the sentence: Firefox jumps to the fragment while parsing, *before*
the script runs, so setting the padding was not enough there — 5.4 px of air left at 761 px with
a 78.6 px header. The script therefore re-places the target once, instantly, right after it has
measured the header, and never on resize.

**The gate.** `landing-min-font.py` runs two engines at two levels (16 and 24 px), six widths
(320, 340, 420, 761, 900, 1440) and nine languages, five of them on the wide widths, with ten
checks per run plus part 0 — "at the ordinary font nothing moved". The checks: the setting applied;
no sideways scroll; nothing outside the right edge; the switcher inside the margin; a hit landing
on the switcher; a target of at least 44×24; the label on one line; neighbours not overlapping when
they share a row; the header under 45 % of the screen; the open language list inside the viewport;
and an anchor landing below the header with air. **1 554 checks, 0 failed.**

**Two controls, because one was not enough.** The copy with the three CSS rules reverted and the
padding script cut out gives **1 532 checks, 82 failures** — sideways scroll, the switcher past the
margin, the torn label, the dead hit-test, the list outside the frame: the defects this block
found, each in the language and width where it lived. That copy also carries *yesterday's* header,
which never grew, so the anchor check passes there and proves nothing; the anchor fix therefore has
its own control, which strips only the script out of the served HTML (`context.route`, the way the
arrival battery does it) and counts substitutions: **9 checks, 6 failures, both engines**, the
heading 11.6 px and 51.8 px under the header.

**A trap worth writing down.** The first version of the gate proved the setting had applied by
reading `getComputedStyle(summary).fontSize`. Chromium reports the raised size (14 → 24 px);
**Firefox keeps reporting 14 px** while laying the text out at 24 — 39 red lines on a healthy
page. A minimum font size is geometry, so the gate now measures geometry: the label's height
against a one-line probe in the same engine. The Chromium route is the engine setting behind the
slider (`--blink-settings=minimumFontSize`); the profile route (`webkit.webprefs.minimum_font_size`
in a prepared profile) was tried first and does nothing under Playwright's headless profile — the
label stayed at 14 px — so the gate's docstring says which of the two it uses instead of implying
it is the dialog.

**Regression.** Eighteen batteries after the change, **7 202 checks, 0 failures**: a11y-extra 267,
header-engines 973, first-screen 252, viewports-extra 94, tablet-menu 162, landscape-page 956,
rotate 288, keyboard-form 244, wcag22-targets 43, text-clip 148, deeplink 684, backtab 120,
env-prefs 45, print-main 213, print-paper 969, cwv 69, live-runtime 121 and the new gate 1 554.
Around them: the static sweep **2 775 / 0** (now including the three new checks and the publication
pair), axe **0 violations on 12 pages**, the link audit 11 pages / 0 problems, Nu 11 pages / no
findings, the browser smoke 18 pages clean, the render check 11 pages `ALL OK`, the cross-engine
sweep 60 runs / 0 problems, and the live checks — 26 of 26 bytes identical, assets, runtime 121 / 0.

Two batteries had to be taught that a header can now be two rows: `landing-a11y-extra.py` and
`landing-header-engines.py` both compared the logo's right edge with the switcher's left edge across
*anything*, which was true while the row could not wrap. They reddened 4 and 24 times on a healthy
page, and both now compare only neighbours that share a row.

**One battery did not finish, and it is not the site.** `landing-tablet-page.py` hangs right after
its two screenshots — the Chromium process disappears, Playwright waits on a socket forever. It
hangs in exactly the same place, with the same silence, when pointed at yesterday's tree
(`LANDING_ROOT` at the previous commit), which is what makes it a harness problem and not this
change; the previous block saw the same battery lose its browser once. Its subject — the tablet
layout and the sticky bar — is covered by tablet-menu, viewports-extra, header-engines,
landscape-page, rotate and first-screen, all green. It is written down here rather than quietly
dropped, and it stays an open item for the harness.

**What this does not prove.** That the headless flag is byte-for-byte the user's slider: it flips
the same Blink setting the preference feeds, but the preference route could not be exercised
headless, and that is why both engines were measured instead of one. That a real phone with this
setting behaves identically: both engines were measured, no device was touched. That a three-row
sticky header is pleasant: it is the honest alternative to a 124 px sideways scroll, not a design
choice. And that the settings users actually pick are 16 and 24: those are "large" and the top of
Chrome's slider, the two ends that matter.

**Files.** `docs/council-20261015.md` (three new static checks in "what guards this"),
`scripts/landing-min-font.py` (new, its docstring carrying the numbers), `scripts/landing-sweep.py`
(two header checks, one anchor check, the old phone-rule string updated), `scripts/landing-a11y-extra.py`
and `scripts/landing-header-engines.py` (both compared the logo with the switcher by X across rows,
which the wrap turned into 4 and 24 false reds — now row-aware), `evidence/block-20261025k/`
(the gate, both controls, the whole harness after the change, the old-state screenshots), and this
entry.

> **Corrected on 26.10.2026:** the paragraph above about `landing-tablet-page.py` "hanging" is wrong.
> The battery finished every time it was given more than its real duration, and it had already
> finished at 22:18 the day before (1 804 / 0). What looked like a socket wait was a seven-minute run
> killed by a five-minute timeout, and "the Chromium process disappears" was `ps | grep chrom` not
> knowing that WebKit's process is called `MiniBrowser`. The harness now prints its progress, its
> expected duration, and recovers from the one real crash that is there (llvmpipe). See the entry
> below.

## The battery that "hangs" was a five-minute timeout and a blind `ps` (26.10.2026)

**The entry above said `landing-tablet-page.py` hangs** right after its two screenshots, that the
Chromium process disappears and that Playwright waits on a socket forever. None of that is true, and
this is the battery the project uses to judge eight iPad screens in two engines.

**It finished seven times tonight, and it had finished yesterday.** English: 204 checks, 0 failed,
80 s. Nine languages: **1 804 / 0 in 447 s** — Chromium 145 s, WebKit 302 s. And the file the
previous block pointed at as evidence, `evidence/tablet-page-20261025T221832.json`, is not a crash
dump: it holds 1 804 checks with 0 failures, written at 22:18. A battery with a hang in it does not
write that file.

**What the "hang" actually was.** The battery printed two lines and then nothing:
`снимок: …tablet-tab-768x1024.png` and `…tablet-tab-1024x768.png`. Those are its only two prints, and
they fall at the end of the first and the fifth Chromium screen — the second at ~140 s. Everything
after them belongs to WebKit, which printed nothing until the final summary. A 300-second timeout
therefore kills the process in WebKit's half, and the log ends exactly "right after its two
screenshots", with `rc=143`. That is the whole observed signature: no socket wait, only a battery
that needs 447 s and a person who waited 300.

**Why the browser looked dead.** WebKit's process is called **MiniBrowser**; nothing in its name
matches "chrom" or "webkit". `ps | grep chrom` prints nothing while WebKit is alive — and so does
`ps | grep -E 'chrom|WebKit|WebContent'`, which is what this block's own sampler used: it printed
`browser_procs=0 rss_mb=0` for two minutes of a healthy WebKit run, and the block nearly wrote the
same wrong sentence a second time. `pgrep -a MiniBrowser` is the question that has an answer.

**A real crash was there as well, and it is the engine's.** Three WebKit runs died for good tonight
with `TargetClosedError: Page.evaluate: Target page, context or browser has been closed`, and the
kernel log at the first of them — `llvmpipe-20[3137122]: segfault at 1fa` at 02:21:49 — names
WebKitGTK's software rasterizer, not the page. The same nine languages pass 902 WebKit checks in the
run before and the run after, so the page is not the suspect.

**What the harness now does about all three.** It prints a line per engine and per screen, flushed,
with seconds and the running check count, so silence is no longer indistinguishable from work. It
prints the expected duration computed from measured cost (`PER_RUN_S`: Chromium 2 s, WebKit 4 s a
run) — 7.5 min for the full sweep, against 7.4 measured. It writes `seconds` and `engine_restarts`
into the JSON, so the next block reads the duration instead of guessing it. It arms a watchdog
(`LANDING_WATCHDOG`, 1800 s): if the run ever does hang, it prints `WATCHDOG`, dumps its stack and
exits 4, instead of waiting for someone else's timeout. It catches `TargetClosedError`, reopens the
context, re-runs **that one language**, drops that language's half-written checks so the count cannot
double, prints a `!` line and records the crash in `engine_restarts`. It gained `LANDING_ENGINES` to
run one engine, and `LANDING_SELF_CRASH=1` to close a page on purpose and prove the recovery path
without waiting for an accident.

**The recovery path ran on real crashes, not only on a rehearsal.** The rehearsal: `LANDING_SELF_CRASH=1`,
English, page closed by hand — 204 / 0, one restart recorded, count unchanged. Then the real thing,
twice: `webkit/tab-1194x834/en` in the WebKit-only run, and `webkit/tab-810x1080/ru` in the final
full run. Both printed the `!` line, retried, and finished with the normal count — 902 / 0 and
1 804 / 0, with the crashed screen still producing its 117 checks.

**Compositing off was measured and not adopted.** `WEBKIT_DISABLE_COMPOSITING_MODE=1` is the usual
advice for llvmpipe crashes, so it was tested on nine languages: 902 WebKit checks, 0 red, the same
names — and 55 details differing by 1–2 px. Then two runs in the *same* mode were compared: 72
details differ by 1–2 px. The flag's effect is inside the run-to-run noise, so adopting it would have
been a change with no measurable benefit and a false sense of a fix; the harness keeps the engine as
it is and survives the crash with a retry.

**The tablet area against the new header.** The header-wrap commit (01:32) had never been through
this battery: every tablet number in the entry above was measured at 22:18, before it. Tonight's run
is the first after the change — **1 804 / 0**, the header 63 px on the tablet and 63 px on the
desktop probe in all 144 runs, the bar 59 px in 146 measurements (0 in the two desktop probes that
require its absence).

**Numbers.** tablet 1 804 / 0 in 447 s, one engine restart (English smoke 204 / 0 in 80 s; WebKit
alone 902 / 0 in 293 s, one restart); control 404 checks / 52 red on two languages, and **204 / 26
red** on English alone, re-run on the final artifact so the documented figure stays the measured one;
rehearsal 204 / 0 with one restart; compositing comparison 902 vs 902, 0 red both, 55 details apart,
against 72 between two runs in one mode.

**What this does not prove.** That llvmpipe will not crash again: it is the engine's software GL, and
three runs died tonight; what changed is that a crash costs a retry instead of a red run or a silent
night. That a retry is always safe: if a crash were ever caused by the page, the retry would crash
again and the run would fail on the second attempt — the wanted behaviour, but not yet seen. That
1–2 px of noise is harmless everywhere: it was measured on the bar's top edge, so any new check with
a 1 px tolerance has to measure its own spread first. And nothing here makes the battery cheap: seven
and a half minutes is a block's background job, not a step in the static sweep.

**Files.** `scripts/landing-tablet-page.py` (progress, duration estimate, watchdog, retry,
`LANDING_ENGINES`, `LANDING_SELF_CRASH`, `seconds` and `engine_restarts` in the JSON, docstring with
the measured durations and both traps), `SKILL.md` in the `stars-bots-ops` skill,
`evidence/block-20261026a/` (every run above, the kernel line, the comparison and summary scripts,
their output), and this entry. No site file changed; nothing was re-published.

## The hero video was 62–73 % of the page, and it downloaded before the first word (26.10.2026)

Nobody had ever measured the byte weight of a visit. There are 56 batteries in the skill and 2 775
static checks, and not one of them answered the question a person on a phone in Delhi actually asks:
how much does this page pull before it is useful? The answer, measured for the first time this block
on a cold context at 390×844 with every response counted and gzipped separately:

| language | whole page, gzip | of it the video | without the video |
|---|---|---|---|
| en | 480 KB | 394 KB | 86 KB |
| ru | 534 KB | 432 KB | 102 KB |
| es | 504 KB | 416 KB | 87 KB |
| pt | 527 KB | 437 KB | 89 KB |
| hi | 537 KB | 338 KB | 199 KB |
| id | 517 KB | 431 KB | 86 KB |
| tr | 480 KB | 381 KB | 99 KB |
| vi | 509 KB | 400 KB | 108 KB |
| uk | 541 KB | 438 KB | 102 KB |

**The video is not compressible and it was being fetched on every visit.** MP4 does not respond to
gzip — the fourth column is what compression does to it: nothing. The markup carried
`preload="metadata"`, which sounds frugal, but the script autoplays the loop, so the browser fetched
the whole 344–444 KB file anyway, on the first screen, before the visitor had read the headline. On
the slowest connections that one file costs more than the entire rest of the page (86–199 KB) with
the poster included.

**What changed.** The markup now ships `preload="none"`: with no script, no connection and no
decision, nothing of the video is requested at all — the poster carries the hero. The script sets
`preload="auto"` only when it has decided to autoplay. And that decision gained a third signal. It
used to be two: `prefers-reduced-motion` and `navigator.connection.saveData`. Now it is three — the
third is `effectiveType`, which the browser itself estimates as `slow-2g` / `2g` / `3g` / `4g`: on
2G and 3G there is no autoplay, the visitor sees the poster and a play button, and the same rule
covers them as everyone else (a manual tap always plays — the person's choice outranks the estimate
of their channel).

**One variable instead of two conditions in three places.** The old code repeated `!reduce && !save`
in the initial start, inside `canPlay()` (which `IntersectionObserver` and `visibilitychange` call),
and — implicitly — in the loop attribute. Adding a third signal to that shape means editing three
lines and getting one of them wrong; the wrong one would restart the video from `visibilitychange`
in open defiance of the rule. The gate now holds the shape, not just the line: the sweep requires
`var auto = !reduce && !save && !slow;` **and** `if (auto) play();` in every one of the nine pages.
That sweep check used to assert the old literal and went red nine times the moment the script
changed — which is the check doing its job, and the reason it was rewritten rather than deleted.

**A new battery, because a rule without a measurement is a comment.** `landing-video-weight.py`
(skill `stars-bots-ops`, port 8271, read-only, evidence in `evidence/block-20261026b/`) — **129
checks, 0 failed**:

- **Weight per language:** the whole page ≤ 600 KB gzip, the page without the video ≤ 230 KB gzip
  (hi is the heaviest at 199 KB — Devanagari), ≤ 15 requests, and exactly one video: the language's
  own.
- **On 3g** (the context's `navigator.connection` replaced by an init script, which is how Android
  reports the real network type): the video is requested **zero** times, `readyState` is 0 — no data
  at all — the poster is there, the button is visible and offers "play", and the video is paused.
- **Then the tap:** the file arrives, the video plays, `preload` returns to `auto`. This is the check
  that matters most, because an economy that leaves a dead button is worse than the bytes saved.
- **The three old rules still hold:** `saveData` on 4g — no autoplay; `prefers-reduced-motion` — no
  autoplay; plain 4g — autoplay works.
- **No Network Information API at all** (Safari, Firefox): autoplay works. Not knowing the channel
  must not punish the visitor.

**The control ran on the previous tree, not on a rehearsal.** `git archive HEAD` into a scratch
directory, `LANDING_ROOT` pointed at it: **63 red checks, 7 per language** — the video requested, 4
of 4 ready state, `preload="metadata"`, the button offering "pause" because the video was already
playing. Same battery, same page, one commit apart. The script now takes `LANDING_ROOT` and
`LANDING_PORT` for exactly this reason.

**A trap worth writing down.** `effectiveType` on desktop Chrome is always `4g` — measured under a
real CDP throttle of 400 kbit/s with 400 ms latency, where the API still answered `4g`, `downlink 10`,
`rtt 0`. So the rule is honest but blind on desktop, and it bites only where it was meant to: Android.
Testing it therefore requires overriding `navigator.connection` in an init script — a real throttle
would have produced a green run that proves nothing. The docstring says this instead of implying the
battery measured a slow network end to end.

**What was deliberately not done.** Cutting the file itself (a re-encode at 273 kbit/s for 720×1560 is
already lean for a screencast with small text) and turning autoplay off on phones altogether (that
would take the demo away from the many on LTE to save the few on 3G, and the hero's composition is
on the owner's list of his own decisions, not mine). The measurable saving on a slow link is 344–444
KB per visit; on 4G nothing changed.

**Regression.** Static sweep **2 793 / 0** (was 2 775: three new checks per language replaced one),
video-motion **444 / 0** (the stop button, Enter, off-screen pause and the reduce-context all still
behave), cwv **69 / 0** (LCP still the poster, 276–396 ms on desktop, mobile above the fold),
first-screen **252 / 0**, link audit 11 pages / 0 problems, external links 69 URLs / 0 problems,
live bytes **26 / 26** identical and the 404 probe still ours. Published through
`tools/publish-branch.sh` to both mirrors (107 files); the sweep's publication check — the one that
went red between the edit and the push — is green again on the live tree.

**What this does not prove.** That Android's estimate says `3g` exactly when the network is slow: the
battery proves our logic given that value, not the value. That a 4G visitor is better off: they still
download 344–444 KB, and the fix does not make the file smaller. And that the budgets are right:
600/230/15 are today's numbers plus headroom, not an industry norm — the first future page that
legitimately grows past them will have to argue with the gate.

**Files.** `index-src.html` (the `preload` attribute, the `slow` signal, the single `auto` variable,
the tap that returns `preload` to `auto`), the nine built pages, `sitemap.xml` and
`tools/lastmod.json`; `scripts/landing-video-weight.py` (new), two checks in `scripts/landing-sweep.py`
(`video preload none` / `video preload metadata gone` / `video slow-link rule`, and the rewritten
`video starts under preference gate`), `docs/council-20261015.md` (one line in "what guards this"),
`SKILL.md` in the `stars-bots-ops` skill, `evidence/block-20261026b/` (the before-fix probe, its
JSON, the battery's weight table and the control run), and this entry.

## The badge question that was left "manual" answers itself when the links are product pages (26.10.2026)

The entry of 25.10 ended with a sentence it could not close: "that the four home-page badges are
still true … remains a manual question for the next block". Checked today, by the gate that owns that
question rather than by memory: `landing-external-links.py` walks **69 URLs** and prints, next to
every badge link, whether the product is named on the page it lands on. All **six** footer badges
answer `значок ведёт на страницу, где продукт назван` — fazier, startupbase, showmebest, lift-off,
startupfa and aura++ each lead to a product page that carries the name, not to a front page. **0
problems.** The question was already answered when those front-page links were replaced (the two
badges whose platforms had deleted the product are gone — the sweep forbids `launchigniter.com` and
`openhunts.com` from coming back); today's run only proves the replacement holds.

**What this does not prove.** That a platform will still list the product tomorrow: the check reads
the page as it is now, and a platform deleting a listing tomorrow turns this gate red tomorrow, not
today. That is the intended behaviour — a badge is a claim, and the claim is checked, not remembered.

## The visitor who came back got an entrance animation on a page he had already read (26.10.2026)

Every battery until today walked the page one way: `goto`, look, scroll. A visitor does something
else — he taps the main button, Telegram opens, he comes back with the browser's Back button and
lands where he left off. Nobody had measured that walk. The closest gate, `landing-deeplink.py`,
arrives by `#anchor` on a *fresh* document, which is a different state.

**What the measurement found.** The reveal script hides every `.rv` block (`html.js .rv{opacity:0}`)
and lets the IntersectionObserver show them. On a return the browser restores the scroll position
*after* that script has run, and the observer delivers its first records on the *next* frame.
Measured at DOMContentLoaded — the state that goes into the first paint — the pre-fix page showed
**0 of 37 blocks** on the return (Chromium 390×844, all nine languages; WebKit **5 of 37**, where the
browser had already painted the top). The visitor who came back to a page he had read got a fresh
half-second fade from nothing, and blocks that had not entered the frame stayed transparent until
he scrolled. The `#faq` arrival had the same shape: **8 of 11** cards transparent and `minOpacity 0`
at the moment the browser had already jumped to them.

**The fix** (`index-src.html`, the reveal script, ~15 lines). When `performance.getEntriesByType
('navigation')[0].type === 'back_forward'` — with `performance.navigation.type === 2` as the fallback
for engines without the newer API — the page shows *all* blocks before the first paint and never
observes them. When the address carries a hash, the anchor's `.rv` chain is shown the same way. A
normal arrival from the top takes neither branch: the entrance stays, because it is a designed
microinteraction (council, item 25), and the battery measures that side too — 0 blocks pre-shown on
a fresh load.

**Provision.** New battery `landing-return.py` — 9 languages × Chromium-phone + WebKit-phone, 216
checks (A: the entrance is intact and scrolling still reveals; B: return — all blocks shown, scroll
restored, sticky band shown, video paused, typed address kept, 0 JS errors; C: `#faq` — every card
shown). After: **216 / 0**. On the previous commit (`a1f8c3a`, in a worktree) the same battery is
**216 / 54** — every B check (18) and every C check (36) red — while the A checks are green on both
trees, which is what makes the red mean something: the battery separates "came back" from "came
first" instead of failing everything red.

**The metric had to learn the observer's own rule.** The first version of check A counted a block
as "in the frame" when `top < innerHeight`, and painted a correct page red eight times: a 165 px
block at the very bottom edge had 9.5 px (5.8 %) inside the *observer's* frame — that frame is
shortened by `rootMargin: -8 %`, and a block needs 6 % of its own height — so the observer was right
to stay silent. The check now mirrors the rule instead of approximating it.

**What this does not prove.** That nothing is painted before DOMContentLoaded — those frames belong
to the browser (blank, or the previous page) and no page script can reach them; what is proven is the
document's state at the moment its own first paint is composed. And that a return is instant from
**bfcache**: in this environment Chromium never restores from it (a plain `data:` page is not
restored either, and `notRestoredReasons` comes back `masked`), so "the browser restored it
instantly" stays unmeasured here. The measured path is the reload a returning visitor gets when
bfcache is unavailable — the common case for a page carrying a video.

**Files.** `index-src.html` (the revealed branch) and every built page; `landing-return.py` (new),
one static marker in the sweep (the rule reached all nine built pages, 2794 checks) and `SKILL.md`
in the `stars-bots-ops` skill; this entry.

## The demo's stop button had no answer for a file that never arrived (26.10.2026)

Every battery until today measured the video's **successful** life: its weight, its autoplay, the
pause, the poster, the two labels, the return from Back. The failure was never measured, and on a
phone it is ordinary — a dropped connection, a 404 after a file is renamed, a file that arrives short.

**What the measurement found** (`evidence/block-20261026d/probe-before-fix.py`, 99 measurements,
en/ru/hi, Chromium 390×844). All three failures end with the poster on screen, the control on screen
and **not one JS error**: the page is silent about a demo it cannot play. And the error arrives in two
different places depending on how the fetch started:

- fetch started by autoplay → `error` lands on the `<video>`, `error.code = 3`
  (`MEDIA_ERR_DECODE`), `readyState = 1`;
- fetch started by the button (`preload="none"`, then play) → `error` lands on the **`<source>`**, the
  `<video>` keeps `error === null` and `networkState === 3` (`NETWORK_NO_SOURCE`), and **`paused` reads
  `false`** while nothing is decoded (`timeline.txt`). `sync()` believes `paused`, so the button is
  labelled *Pause* over a still frame, and tapping it again only waits: `play()` on an element with no
  source queues a request that no source can satisfy.

**The first fix was wrong, and the battery said so in numbers.** Listening to the `<video>` alone (the
first shape, the one the probe happened to show) turned the truncated file green and left **five of
the six scenarios red in both engines** — the commonest failure never reaches the element's own
handler. The shipped rule listens to both, judges with one predicate (`networkState === 3 || error`),
waits one task before believing a source error (so a second `<source>` could still win), retries
**once** (`load()` + play, silent — a radio dropout is not a verdict), and on the second failure hides
the control and marks the frame `data-video="failed"`. `playing` brings back both the control and the
right to retry, so a dropout that heals does not leave a page that has given up. The poster stays in
every case: a still frame of the demo is honest, a button that cannot act is not.

**Provision.** New battery `scripts/landing-video-failure.py`: **38 runs** — Chromium × five languages
(en, ru, hi, vi, uk) and WebKit × three (en, hi, uk — WebKit is what Telegram on iOS runs) over six
scenarios: recover-by-tap, permanent abort, permanent 404, truncated body, healthy tap, autoplay
recovery. **228 checks.** After the fix: **228 / 0** (38 runs, 109 s). Control on the previous commit
(`--control`, `git archive HEAD` in a temp tree): **228 / 95** — every permanent scenario red with
"hidden=False display=flex", "paused=False" and "hits=1" (no retry request at all). Two checks are
there to catch a fix that over-reaches: the video must be requested **exactly twice** in a failure (a
retry, not a storm) and the document height must stay within 40 px of the healthy page (the control
left the layout instead of breaking it). Both are green on the healthy path too, where the request
count is **1** — the retry must not exist when nothing failed.

**Provision, second half.** One static marker in the sweep (`video failure handled`, 9 pages, sweep
now 2803 checks) so an edit cannot drop the handler silently; the whole family re-run after the JS
change: video-motion **444 / 0**, video-weight **129 / 0**, browser-smoke **18 runs, 0 problems**,
`build.py --check` **24 / 24**, `publish-tree.py --check` **495 links**.

**On the world, not only on the tree.** After the gh-pages publication, `evidence/block-20261026d/
live-check.py` walks the live site (root, ru, hi; Chromium phone): healthy — the control is visible,
`display:flex`, `state=pause`, `readyState=4`, playing; with the mp4 aborted at the browser —
`hidden=true`, `display:none`, `paused=true`, `data-video="failed"`, poster in place. Six runs, six
answers, no exceptions.

**What this does not prove.** A *hanging* connection: a server that accepts the request and never
answers fires no error event at all, so the same dead control can still be offered, and no amount of
listening for `error` will see it — that needs a watchdog, and a watchdog on a slow-but-working link
would hide a demo that was about to play. Left open and named, not papered over. Also that the retry
rescues a real dropout: the battery's abort is a clean failure, not three seconds of dead air.

**Files.** `index-src.html` (the video script) and the nine built pages; `landing-video-failure.py`
(new), `landing-sweep.py` (one marker), `SKILL.md`; evidence `block-20261026d/` — probe, timeline,
battery run and control logs, regression logs; this entry.

## The channel that accepted the request and said nothing (26.10.2026)

The previous entry closed the class *the file never arrived* and named the one it could not close: a
server that accepts the request and never answers fires **no event at all** — no `error`, no `load` —
so any amount of listening for a failure sees nothing. It left the sentence "a watchdog on a
slow-but-working link would hide a demo that was about to play" as the reason not to write one. That
reason is right about *time* and wrong about *progress*, and the measurement says so.

**What the visitor saw** (`evidence/block-20261026e/probe-before-fix.py`, 9 runs — en/ru/hi ×
hanging request / throttled-but-alive / healthy, Chromium 390×844, every run sampled at 0.5, 3, 6,
10 and 15 s). With the request hanging: `readyState = 0`, `networkState = 2` (`LOADING`), **0 bytes
buffered**, **no JS error** — and the control, which had been showing *Play*, flips itself to
**Pause** the moment `play()` is called and keeps saying *Pause* (`aria-label="Pause the demo
video"`, ru «Пауза демо-видео», hi «डेमो वीडियो रोकें») for as long as the visitor is willing to
watch. At 15 s the state is unchanged. Tapping it then is worse than nothing: it sets `userPaused`,
pauses an element that never played, and issues **no second request** — the visitor cannot even ask
again. On the same page, in the same 10 seconds, a healthy response gives `readyState = 4` with
13.0 s buffered and playing. One page, one script, two answers — and the wrong one is silent.

**The distinction the fix is built on.** A hanging connection is not a slow connection: a slow
connection delivers **bytes** (`progress`), a hang delivers none, and a playing video delivers
**time** (`timeupdate`). So the watchdog does not measure slowness, it measures *silence* — it
records the buffered end and the `timeupdate` counter when it is armed and, 8 s later, requires
**either** to have grown. Bytes arriving → slow link, no verdict. Ticks arriving → playing, no
verdict. Neither → the control must stop claiming playback: it returns to *Play* and stays on
screen (a hang is not a verdict, so unlike `failed` it does not hide), the frame is marked
`data-video="stalled"`, and a tap is a **new attempt** (`load()` + play) rather than a pause. The
first `progress`, `loadeddata`, `canplay` or `playing` clears the state, so a link that heals puts
the button back on its own. 8 s is four times the slowest first-frame delay measured here (216
kbit/s: `readyState = 2` with 1.8 s buffered at the second second) and shorter than a visitor waits
for a button that does nothing.

**Two things the engines taught, both by failing.** (1) `readyState` is not a liveness signal:
WebKit kept `readyState = 4` on a stream that had gone silent, with `currentTime` frozen at 7.23 s
for fourteen seconds — the first version of the fix trusted that number and stayed green on paper
while the pill said *Pause* over a still frame. The counter that cannot lie is `timeupdate`.
(2) With autoplay allowed and the mp4 hanging, **WebKit never fires `load`** (`goto` with
`wait_until='load'` timed out at 30 s). Nothing visible depends on it — the page has no `load`
listener — but the battery now navigates that scenario on `domcontentloaded`, and the fact is
written here instead of being retried away.

**Provision.** New battery `scripts/landing-video-hang.py`: **21 runs** — Chromium × four languages
(en, ru, hi, uk), WebKit × three (en, hi, uk), seven scenarios: hang-at-start, tap-retries-after-heal,
slow-but-alive (216 kbit/s, twelve samples), healthy, autoplay-hang, user-paused-then-hang, and
hang-mid-file (the channel goes silent *after* playback started, connection held open). **144
checks**, run in **265 s**: **144 / 0**. Control on the previous commit (`--control`,
`git archive HEAD` in a temp tree), same battery: **144 / 45** — every hang run red with
`state='pause'`, `label='Pause the demo video'`, `marker=None`; every retry red with `hits=1` and
`rs=0 paused=True`. The slow-link scenario is the anti-overreach check and it is green on **both**
trees on purpose: the watchdog must not exist there. The control also earned its keep by catching
a flaky check of ours — the slow run asserts time, not `readyState`, because at 216 kbit/s the
channel is *slower than the file* (27 KB/s against ~34 KB/s), so a starved buffer at the twelfth
second is the channel's property, not a defect.

**Provision, second half.** Four static markers in the sweep (watchdog counts silence, cleared by
the first byte, keeps the control, tap retries — 9 pages, sweep now 2839 checks) so an edit cannot
drop the watchdog silently. The whole video family re-run after the JS change: video-failure
**228 / 0**, video-weight **129 / 0**, video-motion **444 / 0**, browser-smoke **18 runs, 0
problems**, `build.py --check` **24 / 24**, `publish-tree.py --check` **495 links**.

**On the world, not only on the tree.** After the gh-pages publication,
`evidence/block-20261026e/live-check.py` walks the live site (root, ru, hi; Chromium phone, 24
checks, **24 / 0**): healthy — playing, `state=pause`, 13 s buffered; with the mp4 held at the
browser — `state=play`, `data-video="stalled"`, control visible, exactly **one** request, and the
label the visitor reads is the language's own («Смотреть демо-видео», «डेमो वीडियो चलाएँ»).

**What this does not prove.** That 8 s is the right number for a human — it is a bound derived from
the fastest and slowest delivery measured here, not a study. That a retry after a long hang resumes
anything: `load()` restarts the file from the first frame, so a visitor who had watched 6 s starts
again at 0 — the honest alternative (resume where it stopped) needs a server that answers ranges,
which GitHub Pages does but a hung connection never did. And the mid-file scenario needs a channel
slower than the file to reproduce at all; on a fast link the whole 400 KB is buffered and there is
nothing left to hang.

**Files.** `index-src.html` (the video script) and the nine built pages; `landing-video-hang.py`
(new), `landing-sweep.py` (four markers), `SKILL.md`; evidence `block-20261026e/` — probe, three
engine probes, battery run and control logs, live check; this entry.

## The still frame was softer than the film it stands in for (26.10.2026)

Every battery in this house measured the page as geometry: does the box fit, does the text wrap, does
the picture sit where the layout put it. Twenty-odd of them ran at device scale 1 or 2, and not one
ever asked how many pixels the **file** brings to a screen that asks for more. The three passes closed
the layout; this is the other axis, and it was open the whole time.

**What the measurement found.** `evidence/block-20261026f/` — a probe over nine languages × four
profiles, `ratio = file pixels / (CSS width × devicePixelRatio)`, where 1.0 means "exactly enough" and
anything below means the browser is inventing pixels. The hero frame is `width:min(300px,72vw)`: on a
390-wide phone 280.8 CSS px, on a 420-wide one 302.4. At DPR 3 — every iPhone, most Android phones —
that asks for **842–907 device pixels**. The poster file was **540**: ratio **0.641** (0.600 on the
420 phone), while the video it stands in for is 720, ratio 0.855. So the still was a third softer than
the film — and the still is exactly what a visitor on 3G, with data saving on, or with reduced motion
sees *instead of* the film, plus what everyone sees for the first few hundred milliseconds. The
visitors with the worst connection got the softest frame on the page. The rest of the tree was fine:
the chat screenshots are 1080 px in a 297–616 CSS box (1.11–1.65 of what is asked; the tablet rail is
the one place 12 % short), the platform badges 120–600 px at 40–46 CSS (1.0–6.5).

**The fix is a resolution, not a design.** The poster is the loop's last frame, so the honest file is
the frame's own size: 720×1560, no `scale` in the ffmpeg line — that `scale=540:1170` was the only
thing inventing pixels. Nine posters, **+12.3 KB each** (pages are 100–211 KB gzip without the loop
against a 230 KB budget; LCP 944–1024 ms against 2500). The build script now writes the poster at the
loop's resolution, and the ledger stores both sizes read back **from the files** (`poster_size` from
the WebP container, `video_size` from ffprobe) — so re-stamping the ledger cannot "agree" a shrunken
poster with its film: the sweep compares the two numbers and goes red.

**What the fix is worth, measured.** Hero frame at 390×3×, the mp4 blocked so the poster is all the
browser can paint, before and after: sharpness (variance of Laplacian) **260.6 → 375.3 = +44 %**, and
on the strip carrying the burned-in caption **113.5 → 249.2 = +120 %**. Only **1.4 %** of pixels differ
by more than 16/255 — the signature of removed interpolation, not of a redrawn picture. The eye is a
worse instrument here than the metric: shown both frames at 1:1, an image model called both "crisp",
so this entry does not claim a visible improvement. It claims a file that no longer asks the screen to
invent a third of its pixels, and the caption is where a human would notice first.

**Provision.** New battery `scripts/landing-pixel-density.py` (port 8273, READ-ONLY, accepts
`LANDING_ROOT`/`LANDING_PORT`): nine languages × five profiles (390 and 420 CSS px at 3×, tablet 760
and desktop 1280 at 2×, plus a 1× control), **558 checks / 0**. Five rules, each from the measurement:
poster = the loop's frame; poster ratio ≥ the film's ratio in the same box (0.855 at 390×3, 0.80 at
420×3, 1.20 at 2×); no raster stretched more than 15 %; SVG counted separately, because a vector's
`naturalWidth` is a number from the file (`fazier.svg` reports 103 px in any box) — and a check that
vectors *were* counted, so the exclusion cannot become a hole; and the 1× control, which passes only
if the probe is measuring at all. Two static markers in the sweep (9 × 2 = 18 checks, sweep now
**2857 / 0**). Control on the previous commit (`git archive HEAD`): **108 red** — every language red on
the poster rule at the 3× profiles.

**Regressions after the change.** video-weight **129 / 0** (heaviest page hi 211 KB of the 230 budget),
cwv **69 / 0**, visual-pass **0 problems** across nine, `build.py --check` **24 / 24**,
`publish-tree.py --check` **495 links**, live-assets **90 assets, 0 problems** — after the Pages build
caught up (the first run was 18 problems, all posters: that is the deploy being behind, not a defect),
live density check **12 / 0**.

**On the world, not only on the tree.** `evidence/block-20261026f/live-check.py` walks the live site
(en, ru, hi; Chromium 390×3, 12 checks, **12 / 0**): the poster's live bytes are the local file's
bytes, the file's size is the loop's frame, and the ratio the visitor's screen gets is 0.855. It also
taught the one thing the tree could not: **`videoWidth` is 0 when the mp4 is cut off** — with no
metadata the browser knows nothing about the frame, and the poster is the only thing it has. That is
why the live check makes two passes, one with the film and one without, instead of one clever one.

**What this does not prove.** That a human sees the difference on the phone: the metric moved 44 %, the
eye at 1:1 did not. That 720 px is *enough* on a 3× phone: it is not — the screen asks for 842–907 and
the film itself is 720, so the poster now sits at the film's ceiling (0.855 / 0.80) rather than at the
screen's. Raising that ceiling means re-encoding nine loops at 1080 px — roughly double the bytes of a
file that is already 62–73 % of the page — which is an owner decision, not a poster's. And the gain on
2× screens was never the issue there: the poster went from 0.90 to 1.20, i.e. from nearly enough to
spare.

**Files.** nine `img/demo-poster[-<lang>].webp` at 720×1560; `demo/build-web-loop-langs.sh` (poster
step), `demo/captions.py` (WebP container reader, ffprobe sizes, two ledger fields, one new check),
`demo/captions.json` (restamped); `landing-pixel-density.py` (new), `landing-sweep.py` (two markers),
`SKILL.md` and `references/landing-batteries.md`; evidence `block-20261026f/` — probe, battery,
control, before/after hero frames, sharpness numbers, live check; this entry.

## The wider the screen, the fewer badges fitted, and on the narrowest phone one stood alone (26.10.2026)

**What was found.** The footer strip of platform badges is the one block on all nine pages that
geometry gates measured at two widths only — 420 and 1440 px in `landing-visual-pass.py` — and the
sweep watched just two strings of its CSS. Walking it at sixteen widths, one pixel apart around every
boundary, found two defects and one claim in the source that had quietly stopped being true.

**What the measurement found.** (1) *A reverse step.* At 700 px four badges fitted in the first row,
at 701 three, at 703 four again. The compact-size media query ended at 700, so the badge grew from 40
to 46 px and the four badges in DOM order needed 602 + 3 × 20 = 662 px of inner width — while the
footer's inner width is 661 at 701 and 662 at 702. For two pixels of screen the strip gets *worse* as
the screen gets *wider*. (2) *A lone badge in the middle.* At 320 px (inner 280) the strip laid out
2+1+2+2: the widest badge — ShowMeBestAI, 4.00 : 1, 160 px at height 40 — cannot pair with the next
one (startupbase, 3.75 : 1, 150 px): 160 + 150 + 14 = 324 > 280. The forced single badge landed in the
*second* row, between rows of two, so the strip read as broken rather than as wrapped. At 300 px it
was 2+1+2+1+1 — two lone rows. (3) *A number that outlived its strip.* The comment above the rule
still promised "ровные 4+4" and "сумма четырёх самых широких = 714" — true for the eight-badge strip
of 22.10; the eighth badge went on 25.10 with OpenHunts, and today's four widest sum to 659 (602 in
DOM order). Nothing recomputed it: the only gate near it checks that the gap string is present.

**The fix.** The compact-size rule now ends at 702 px — the width where the grown badge stops costing
a row (measured one pixel apart: 700 → 4+3, 701–702 → 3+4, 703 → 4+3). A second rule under 360 px
sets the badge to 34 px and the gap to 8, where the pairs do close: 300–360 px now lay out 2+2+2+1 and
the strip is 30–80 px shorter (160 px instead of 190 at 320 and 240 at 300). The comment was rewritten
with numbers measured on the built page, and it names the badge that sets the ceiling.

**In the sweep.** Two static markers per page — "badge strip grows at 702" and "badge strip narrow
360" — so a later CSS edit that moves either boundary back turns red instead of shipping (2875 checks).
The dynamic half is a new battery, `landing-badge-rows.py`: nine languages × sixteen widths = 144
measurements, 1017 checks, and six invariants that did not exist anywhere before — all seven badges
present and loaded; no row before the last holding fewer than two badges; no row wider than the strip;
no horizontal scroll on the page; **a monotone layout** (as the screen grows the first row never loses
a badge and the strip never gains a row); and at 1440 the strip lays out exactly 4+3 with the fifth
badge provably not fitting, so the ceiling in the comment is computed, not written. Against the
previous tree the same battery returns **27 failures** — nine languages × (300, 320) for the lone
badge, nine languages × 702 for the reverse step — so the gate is proven on the defect, not on the fix.

**What this does not prove.** That a person notices a 34 px badge instead of a 40 px one on a 320 px
phone: the geometry is proven, the taste is not — 34 px is 85 % of 40 on a screen that is 82 % of a
390 px one. That 300 px deserves a rule at all: it exists for Galaxy Fold closed and a handful of
Android Go devices, and the alternatives were a lone badge or a strip wider than the screen. That the
row capacity is monotone *everywhere*: at 600 px the strip wraps 3+4 and at 700 4+3, so the number in
the first row still changes inside the 600–700 band — a wrap, not a defect, and the battery only
requires that it never *falls* as the screen grows. That the nine built pages live in Telegram's own
webview as they do in Chromium: the battery runs one engine, as every geometry battery here does.

**Files.** `index-src.html` (two media queries and the comment above them) and the nine built pages
with their markdown twins; `landing-badge-rows.py` (new), `landing-sweep.py` (two markers, 2857 →
2875); `SKILL.md` and `references/landing-batteries.md`; this entry; evidence `block-20261026g/` — six
probes (rows, widths, the 1-px walk across the boundary, narrow screens, and the two that disagreed
before the truth was 1 px wide), battery run and control, sweep before and after, live check.

## The Hindi page downloaded 660 letters to draw 57 (26.10.2026)

**What was found.** `/hi/` was the heaviest page on the site and the only one whose font was
larger than the page's own HTML. Noto Sans Devanagari was served whole — 121 192 B, 769
glyphs, weights 100–900 — while the built page uses **57 codepoints**. A cold load measured
in Chromium at 390 px (4g profile, so the hero loop autoplays) came to 937.3 KiB in 16
requests: video 344.8, HTML 120.0, **font 118.4**, three screenshots 163.4, poster 41.2,
Latin Manrope 24.8. The font was the third item and the only one that could shrink without
touching a single pixel of the design.

**What the measurement found.** Subsetting the file to the 57 characters the site actually
draws (57 of ~660) gives 69 960 B — 58 % of the original, 463 glyphs, all 12 GSUB features
(`akhn half pres blwf abvs psts …`) and the variable `wght 100..900` axis kept. `/hi/` drops
from 937.3 to 887.2 KiB (−50.1 KiB, −5.3 %) and the closed-page font budget from 142.6 to
92.6 KiB. The first try was **28 bytes smaller and wrong**: built with `opts.hinting = False`
the file weighed 69 932 B, the geometry was identical to the pixel (same document height,
same h1 line count, same block heights), and the picture was not — screenshot comparison of
one page against the same page with the full font served in place of the subset returned
**12 631 differing pixels in the h1, 35 288 in the lead, 1 015 in the footer**. A canvas
measurement had already hinted at it (the same Hindi strings measured 1.5–2.7 % wider), which
is what sent the block to pixels instead of trusting geometry. With hinting kept the same
pages return **0 differing pixels**; hinting is part of the drawing, not an optimisation.

**The fix.** `tools/subset-deva.py` builds `fonts/noto-sans-devanagari-hi.woff2` from
`tools/font-src/noto-sans-devanagari.woff2` (the full file moved out of the published `fonts/`
directory — the sweep's "every published file has a reader" check caught it as a 118 KB asset
no page names). The registry `tools/deva-subset.json` holds the exact codepoints, the source
sha256, the output sha256 and the byte counts; `tools/build.py` reads it, declares the subset
on `/hi/` and **fails** if any page uses a Devanagari codepoint that is not in the registry,
printing the command that regenerates it. The codepoint set is collected from the sources —
the Hindi dictionary, the template, the builder, the legal pages — and from the built pages as
a cross-check: reading only built pages deadlocks the workflow, because editing the dictionary
adds a letter the generator cannot see until the build that refuses to run succeeds.

**In the sweep.** Three new markers and one rewritten (2875 → 2878 checks): the subset is
≤80 KB and matches the registry in bytes and sha256; the registry was built from the source
file that is actually in the tree; `/hi/` declares the subset with the same `unicode-range`
and no page declares the full Noto; the registry covers every Devanagari codepoint of all nine
pages; nobody preloads it. A new battery, `landing-font-identity.py`, opens `/hi/` twice —
the font request is answered once with the subset, once with the full source — and compares
h1, lead, a FAQ answer and the footer pixel by pixel, requiring 0 differing pixels per
element *and* proof that the swap applied (otherwise the check is empty). Against the
hinting-stripped subset the same battery returns 3 failures (12 631 / 35 288 / 1 015 px);
against the shipped file 7/0. `landing-fonts.py` keeps a separate 80 KB ceiling and asserts
the full Noto is never requested; `landing-glyph-fallback.py` on `/hi/` reports 141 text
nodes, 4 545 glyphs, **0 substitutions** — every glyph still comes from our own face.

**What this does not prove.** That a visitor notices 50 KiB: on 4g it is a few hundred
milliseconds, and the visible gain is only that the Hindi text has less to wait for before it
swaps from the system font. That 69 960 B is the floor: dropping hinting is smaller and
changes the drawing, dropping the `dist`/`abvm` features would be smaller still and break
matra placement. That Linux Chromium draws like Android Chrome or Safari: the identity test
runs one engine on one platform, and FreeType's hinting is exactly the part that differs
between them. That other scripts need nothing: Cyrillic and Vietnamese pages carry Manrope
subsets of 14.5 and 8.5 KB, already smaller than any page subset would be. Also measured in
this block and found clean: every media-query boundary in the stylesheet walked at ±1 px on
en/ru/hi (90 page loads, no horizontal scroll, no element past the edge, no clipped text, no
grid that loses a column as the screen grows) and the FAQ accordion opened and closed on 99
questions in Chromium, WebKit and Firefox (the card collapses back to its summary, the answer
stays inside its box, no JS errors).

**Files.** `tools/subset-deva.py` (new), `tools/deva-subset.json` (new),
`fonts/noto-sans-devanagari-hi.woff2` (new), `tools/font-src/noto-sans-devanagari.woff2`
(moved), `tools/build.py`, `tools/make-lang-fonts.py`, `tools/lang-fonts.json`, `hi/index.html`
with its twin and `tools/lastmod.json`, `submission-kit/manifest.json`; `landing-font-identity.py`
(new), `landing-sweep.py`, `landing-fonts.py`, `SKILL.md`, `references/landing-batteries.md`,
`references/landing-qa.md`; evidence `block-20261026h/` — the weight probe, the codepoint
probe, four subset variants, the canvas width test, the geometry test, the pixel test with its
zero-noise control, the battery and its control on the hinting-stripped file, the build guard
and its two controls, the glyph and font batteries.

## The language menu followed the button to the edge of the screen (26.10.2026)

Yesterday's block taught the header row to wrap: with the browser's minimum font size at 24 px
(Chrome's slider top) the row no longer pushes the page sideways, it drops a line. The battery
that proved it measures the *pill* — inside the right padding, tappable, neighbours on the same
line not touching it. Nobody asked where the pill ends up, and nobody opened the panel.

**What the measurement found.** At 761–900 px with the minimum at 24 px the pill sits at the
LEFT edge of the screen (30…172 px: the row wraps, the pill is its last item, so it starts the
second line). The panel of nine languages was positioned `right:0` against that pill and is
243 px wide — its right edge went to 172 and its left edge to **−36 px (uk) … −120 px (hi)**.
Nine navigation entries with the first characters cut off and the left part of every tap target
outside the screen. At the normal setting the same panel sits at 541…741 and is fine, which is
why the fifteen existing batteries never saw it.

**The fix** is three CSS declarations and no new markup: the containing block of the panel is the
header row, not the pill — `.top-in{position:relative}`, `.lang-dd` loses `position:relative`,
`.lang-list{right:20px}` where 20 px is the page's own padding (`.wrap`). The panel's right edge
now equals the page's content edge whatever the header's height. The normal case is unchanged:
right edge 741 at 761 px and 1230 at 1440 px before and after, page heights identical
(`landing-visual-pass.py`, PROBLEMS 0, all nine languages). The panel's top moves from 58 to
70 px — below the whole header instead of overlapping its last 5 px; that 12 px shift is the only
visual difference in the change.

**In the gateway.** New battery `landing-langlist-fit.py`: three engines (Chromium with
`--blink-settings=minimumFontSize=24`, Firefox with the real `font.minimum-size.*` pref, WebKit at
the normal setting — headless has no minimum to set there, and the report says so), seven widths
(320/420/761/768/900/1280/1440), nine languages, nine checks per run: the setting applied (pill
height 38 → 54 px), the panel inside the screen on all four sides, its right edge on the page's
content edge, it does not cover its own pill, nine entries present, every entry inside the screen
horizontally, the visible ones hit-testable at their centre (entries below the panel's scroll window
count as scrolling, not as failure — nine 44 px rows do not fit a phone and the list scrolls by
design since 23.10), and no sideways document scroll. **3591 checks, 0 failed.** The negative
control `--mutate` restores the old anchoring in the served HTML (rewriting the response, no file
touched) and returns **846 checks, 74 failed** — every one at the minimum of 24 px, panel left edge
−36…−120, the same numbers as the pre-fix probe, which is what makes the green mean something.

**What this does not prove.** That a visitor with a 24 px minimum font is common: the slider is off
by default and the pages were readable without this fix — what is proven is that the navigation is
not clipped when he sets it. That Safari on a real tablet wraps the header the same way: WebKit
runs here at the normal setting only, and the wrap itself is Chromium/Firefox territory. That the
12 px the panel dropped cannot matter anywhere: no measurement moved, but a design review by eye is
not a measurement.

**Files.** `index-src.html` (three declarations + the comment that says why), all nine built pages
with their twins, `tools/lastmod.json`, `sitemap.xml`; `landing-langlist-fit.py` (new) and two
markers in `landing-sweep.py` (2896 checks); `SKILL.md`, `references/landing-qa.md`; evidence
`block-20261026i/` — the pre-fix probe with 27 failures, the same probe after (0 of 126), the
battery, its negative control, four regression batteries (`landing-min-font.py` 1554/0,
`landing-a11y-extra.py` 267/0, `landing-tablet-menu.py` 162/0, `landing-visual-pass.py`
PROBLEMS 0), the sweep and the live-byte comparison.


## The badge was alive and the gate was red, and the suite had never been run together (26.10.2026)

Every block for a week ran four to six batteries and wrote "green". The sweep — 2,896
checks over the files — runs on its own. Nobody had ever started the fifty-seven behavioural
batteries in one pass, so "the suite passes" rested on the memory of past blocks, not on a
run. `landing-regress-all.py` (new) is that run: every READ-ONLY battery in turn, its own
timeout, one JSON journal holding the exit code, the `CHECKS/FAILED` line and the last six
lines of output.

**The suite's first finding was its own price.** Seventeen batteries took forty minutes. Two
do not fit 420 s — `landing-cross-engine.py` (36 runs × two engines) and `landing-deeplink.py`
— and `landing-header-engines.py` finished at 419.5 s, half a second under a ceiling that was
meant to be generous. The rest of the alphabet did not fit the block's clock. A suite whose
slowest member is measured in minutes is not an instrument to run after every edit; it is a
weekly one, and now the journal says so instead of the estimate.

**The only red was the gate, not the page.** `landing-external-links.py` failed on the Startup
Fame badge: `https://startupfa.me/s/-51` answers **429** to a plain urllib request, with
`server: Vercel` and `x-vercel-mitigated: challenge`. That is not a dead page — it is Vercel's
anti-bot checkpoint, which lets a browser with JavaScript through and does not let a script
in. A real Chromium gets the same address and draws it: `<title>` "UchiSamBot — review,
pricing & alternatives | Startup Fame", the product named in the visible text ("UchiSamBot
(Study Helper) is a Telegram bot for school students…"). The badge leads where it promises;
the red was the gate's.

**Two wrong repairs before the right one.** The first version judged the wall by the browser's
*first response status* — but a page behind a passed challenge still reports the challenge code
on the first response (measured on the platform's own front page: status 403, title "Startup
Fame - Discover Awesome Startups", eighty lines of text: a live page whose first answer is
403). The second version left the wait as soon as the title stopped looking like a checkpoint —
and Vercel's challenge page has an **empty** title at first, so the loop exited on nothing and
declared a live badge dead. Then, holding the real title, it read the body too early: the title
of the real page arrives *before* its text, so the product was not there yet and the badge
failed as "product not named" — on a page that names it three times. The final shape waits for
*settled* text (two identical reads, ≥200 characters), judges by the rendered page, and treats
a wall the browser cannot pass as **"not checked", exit code 2** — never a silent pass, never a
false red.

**Controls.** `--browser-probe URL` runs the same code against one address: the product page
returns 0 with the product named, the platform's front page (alive, no product on it) returns 1.
Same path, opposite verdicts — so the check discriminates instead of rubber-stamping. After the
repair: 0 problems, 0 unverified, exit 0.

**What this does not prove.** That 48 batteries is the whole set: ten are excluded by design
(live mailbox, live bot, the real form send) and have their own conditions. That the thirty-one
batteries this block's clock did not reach are green — they are one command away, and their last
green comes from earlier blocks, which is exactly the memory this entry was written against. And
the uncomfortable one: only seven of the fifty-eight batteries carry a negative control
(`--mutate`), so for the other fifty-one a pass still cannot be told apart from a battery that
measures nothing.

**Files.** `landing-external-links.py` (browser verdict, `--browser-probe`, exit 2),
`landing-regress-all.py` (new), `SKILL.md`; evidence `block-20261026j/` — the red run,
both wrong repairs, the green run and both controls.

## The set was green in pieces, and three of its batteries measured nothing at all (26.10.2026)

**The premise this block paid off.** The previous entry ended with the honest sentence that
the thirty-one batteries its clock did not reach were "one command away", and that their green
came from earlier blocks — memory, not a run. This block ran that command: `landing-regress-all.py`
started at `landing-landscape-page.py` and finished the set.

**The first thirty-one, and three reds in one second.** Twenty-eight green: `landscape-page`
956 checks, `langlist-fit` 3 591, `tablet-page` 1 804, `min-font` 1 554, `print-paper` 969,
`return` 216, `video-hang` 144, `wcag22-targets` 43. Three red — and every one of them failed in
**1.0 s**, which is not how a page fails.

**A red that takes one second is the harness.** `landing-print-contrast.py`,
`landing-render-check.py` and `landing-visual-pass.py` all died on
`ERR_CONNECTION_REFUSED` to the loopback port each of their headers asks for. Each of them
says in that header "start `python3 -m http.server` first"; inside a block that was done by
hand, so the battery looked alive. In the suite nobody raised the server, and three gates —
3 543 checks in
`print-contrast` alone, the whole "white text prints as white on paper" sweep — had been
measuring an empty port. The runner now owns that: `NEED_SERVER` names the port each battery
declares in its header, the runner raises the server on the built tree, waits for the port to
accept, runs the battery and stops the server. All three went green (3 543 / 0, 10 s, `PROBLEMS 0`),
and the same three still go red when the page is broken — see the controls below.

**Two "timeouts" were the clock, not the page.** `cross-engine` was red at 420 s; at 1 200 s it
answers in **425.9 s** with `PROBLEMS 0`. `deeplink` was red at 420 s; it answers in **422.4 s**
with **684 checks, 0 failed**. Two seconds over the line, reported for two days as a page defect —
the same species as the five-minute timeout two entries up. `header-engines` had already finished
at 419.5 s, half a second under it.

**Two batteries wanted another interpreter.** `landing-page-lang.py` and `landing-stop-rule.py`
import `bot.*` (aiogram, aiohttp). Under the workspace interpreter they would have failed
`No module named 'aiogram'` — a red of the runner. `NEED_BOT` runs them with
`study-bot/venv/bin/python` in the bot's own directory; `page-lang` then answers in 4.6 s.

**The suite does not fit one block, so it learned to resume.** `--from NAME --append --out FILE`:
the journal continues from the letter a run stopped at and does not repeat batteries already
recorded. The first attempt at this silently wrote to the module constant instead of the chosen
path — caught by reading the file, not by trusting the flag; fixed before the run that counted.

**The count, for the first time in one journal.** 48 batteries in the set (59 scripts; 11 are
excluded by design — the live site, the live mailbox, the live bot, the real form send, the sweep,
the runner itself). All 48 ran: **19 014 checks, 0 red**, plus the static sweep at
**2 896 checks / 0 failed** against the same tree. `evidence/block-20261026k/coverage.py` prints
this table from the journals and names any battery that never ran — the answer is none.

**A green battery is not yet evidence, so three of them were made to fail on purpose.** Only seven
of the 48 carried a negative control. `landing-render-check.py --mutate` now rewrites the section's
`h2` in the DOM after load: four pages go red on `title`, exit 1. `landing-visual-pass.py --mutate`
injects a 3 000 px block outside the slider: `PROBLEMS 36` (18 `H-OVERFLOW` + 18 `over <div>`),
exit 1. `print-contrast --mutate` (which already existed and had never been run inside the suite)
strips `@media print`: **CHECKS 3 408, FAILED 138**, white-on-white buttons and footer links. Without
the mutation the same three answer 0 and exit 0 — one path, opposite verdicts.

**What this does not prove.** That 45 of the 48 are worth their green: they still have no control,
and a battery that measures nothing passes exactly like a battery that measures everything. That the
page is good — a gate only says the tree agrees with the gate; the visual and the meaning passes were
other blocks' work and are not re-proven by a green suite. And that the eleven excluded batteries are
green: they need the live site, the mailbox and the bot, and were last measured on their own terms.

**Files.** `landing-regress-all.py` (`--from` / `--append` / `--out`, `NEED_BOT`, `NEED_SERVER`,
journal path bug), `landing-render-check.py` and `landing-visual-pass.py` (`--mutate`); evidence
`block-20261026k/` — the 31-battery run, `coverage.py` and its table, both slow re-runs, three
controls and three clean re-runs of the same three batteries.

## The checks that read the words had never once been red (26.10.2026)

**The premise came with a red.** The previous entry ended with the honest sentence that only
a handful of the 48 batteries carry a negative control. Before any control could be written,
the sweep answered **2 896 checks, 1 failed** — on the tree the previous block had committed as
green. The hit was that block's own entry: it printed a loopback address with its port and the
name of the automation package the suite runs under. The opsec gate reads every tracked file,
not only the pages the site serves, and it is right to: the repository is public, so the
notebook is read by people whether or not the site hides it. Two sentences were reworded — the
addresses are described now, not printed — and the sweep answered 2 896 / 0. The lesson is
ordering, not spelling: the entry gets written **before** the final sweep, otherwise the gate
passes on a tree that does not yet contain the text it is meant to judge.

**A battery that could not fail.** `landing-en-leftovers.py` hunts English sentences left on the
eight translated pages. It printed its findings as JSON and never called `exit`: **0 findings
and 500 findings both ended the process with code 0**, so the suite counted it as green
evidence since 21.10. It now exits 1 on any finding and reports `CHECKS: 8, FAILED: 0`. The
verdict was proven on a broken copy rather than by reading the code: nine pages copied, one
English sentence written into the English page and into the Russian one — `FAILED: 1`, exit 1,
the sentence quoted in the finding, and the same copy untouched stayed at 0.

**Three more batteries were taught to fail, on copies, one defect each.**

- `landing-page-lang.py`: one deep-link label on the Russian page misspelled (`_sticky` →
  `_stickyx`). Result: **exactly one** problem, `ru` only, naming both sets of labels; the
  other eight languages stayed green; the untouched copy answered 0.
- `landing-price-parity.py`: two mutations, one on each side of the promise. The bot's pack of
  15 raised by 10 → **exactly one** mismatch, `pack15`, 310 against 300. The shop window's pack
  of 5 lowered by 1 → **exactly one** mismatch, `pack5`, 119 against 120. A mutation that only
  proved "something went red" would not have told these apart.
- `landing-links-audit.py`: four defects, one per class of link the battery claims to check — a
  dead relative target, an anchor pointing at nothing, a duplicate `id`, a bot link without its
  start label. Each produced **exactly one** finding of its own kind; the copy without them
  produced none.

Every control counts its substitutions first: a control that matches nothing reports green while
having changed nothing, which is the failure it was written to expose.

**The gap became a number, and the number was better than the last entry said.** New
`landing-controls-ledger.py` reads the same set as the runner (the skip list is imported from
it, so the two cannot drift) and counts a control only when a flag is *wired in the code* —
`add_argument('--mutate'…)` or `'--flag' in sys.argv`; a mention in a comment does not count,
and the sweep mentions `--mutate` only in a comment. The answer: **48 batteries, 23 with a
control** (12 `--mutate`, 10 `--control`, 1 `--selftest`), **1 pointer only**, **24 with
nothing**. Before this block it was 19 / 1 / 28. The earlier note "seven of fifty-eight" was
not wrong so much as narrow: it counted `--mutate` alone, and the ten `--control` flags break a
copy just as deliberately. `--control URL` in `landing-print-crossengine.py` is the one
exception and is counted as a pointer: it points the battery at another build instead of
breaking anything. > SUPERSEDED (27.10.2026, same day): that battery now has a real `--mutate` — see
"Every battery in the set can finally be shown red"; no battery in the set is a pointer any more.

**Controls are no longer remembered, they are run.** `landing-regress-all.py` gained a
`CONTROLS` list and `--controls`: each entry names the arguments under which that battery is
obliged to fail, success is exit code 0 and no "НЕ СРАБОТАЛ" in the output. Four entries, four
caught, one command, 1.4 s. The controls are deliberately not part of the plain run —
the plain run measures the page, the controls measure the instrument — but a control nobody
runs is memory, and this block was written against memory.

**What this does not prove.** That the other **24 batteries** are worth their green: they still
have no control, and the ledger now prints their names on demand. That the four new controls
prove more than the one defect each was given: a battery has several clauses and a single
mutation exercises one of them. That the production path was exercised — the controls mutate
copies, and only `en-leftovers` was also run against a broken tree through `--root`. And the
uncomfortable one: nothing controls the controls, so a control that silently stops matching
will report "caught" the day its own regex rots.

**Files.** `landing-en-leftovers.py` (verdict, `--root`, `--mutate`), `landing-page-lang.py`
(`--root`, `--mutate`), `landing-price-parity.py` (`--mutate bot|site`), `landing-links-audit.py`
(`--root`, `--mutate` with four defects), `landing-controls-ledger.py` (new),
`landing-regress-all.py` (`CONTROLS`, `--controls`, ledger in the skip list); evidence
`block-20261026l/` — nine clean and mutated logs, the ledger, four runner journals, the broken
tree that proves the verdict, and the sweep after the reworded entry.

## The control that could not fail found a battery reading the wrong width (26.10.2026)

**Three of the twenty-four.** The last entry left the gap as a number: 48 batteries, 23 with a
control, 24 without. This block took three of the 24 — the ones that measure geometry the browser
only knows after layout: `landing-wcag22-targets.py`, `landing-first-screen.py`,
`landing-badge-rows.py`. Unlike the previous block, no copy of the tree was mutated: the defect is
injected into the live page after load, so the page on disk stays the page under test. The ledger
now reads **26 with a control, 1 pointer, 21 without**.

**Each control has to prove it was applied before it may judge.** A style that matches no element
changes nothing and reports green — the exact failure these controls exist to expose. So the
control records its own substitution first: the smallest visible `.btn` is **16 px** tall (was 48),
`scroll-padding-bottom` computes to **0 px** while the bottom bar is **123 px** tall (was 78 px of
padding and a 53 px bar), `scroll-padding-top` computes to **0 px** (was 84 px), the first badge
measures **168 px** wide and the strip **1 020 px** where the design's ceiling is 780 px. If a
number does not move, the control says so and fails.

**What the three controls returned.**

- `landing-wcag22-targets.py --control targets|focus|anchor|all`: targets → **18 reds**, all of
  them 2.5.8, every one naming the button and its 171×16 box; focus → **9 reds**, all of them
  2.4.11's "focused element not obscured", none of the anchor checks; anchor → **4 reds**, all of
  them the anchor landing on two pages × two devices. Run together, `--control all` gives
  18 + 9 + 4 and **nothing else red** — three clauses, three separate evidences, one command.
- `landing-first-screen.py --control fold`: the hero button's row pushed 560 px down →
  **126 of 126** screen × language pairs red, all of them "кнопка до … > экрана", no horizontal
  overflow claimed. The first attempt used 420 px and left the 390×844 phone green with 12 px to
  spare — the control was measured, not assumed, and the number was raised until the defect
  actually reached every screen.
- `landing-badge-rows.py --control dense`: badges forced to 168 px and the strip widened to
  1 200 px → **45 reds** of "no row but the last stands alone" (one badge per row on 300–390 px)
  and **9 reds** of "1440 lays out 4+3" (which became 5+2), **zero foreign reds**. Widening the
  badges alone was not enough: at 168 px on the design's 780 px strip the split stayed 4+3, so the
  control also widens the strip — that is the mechanism that lets the fifth badge into the first
  row, and without it the claim would have stayed unproven while the control looked green.

**The wide control found a defect in the battery, not in the page.** `landing-first-screen.py`
checked overflow with `scrollWidth > innerWidth`. On a mobile context Chrome **expands the layout
viewport to fit the content**, so `innerWidth` grows with the defect: a body forced to
`100vw + 120px` read 510 against 510, a 900 px hero read 900 against 900. The measured table
(kept in the evidence folder) shows `clientWidth` staying at 390 through all of it. The check now
compares `scrollWidth` with `clientWidth`, the clean page still answers **252 checks, 0 problems**,
and `--control wide` turns **126 of 126** pairs red. Until this block that clause had never been
red, and could not have been: it was reading the number the defect inflates.

**The runner can now carry two defects for one battery.** `CONTROLS` was a dictionary keyed by
script name, so a second control for the same battery was impossible. It is a list of
`(battery, arguments)` pairs now. `--controls` runs **8 and catches 8**: the four old ones in
1.4 s total, then `fold` 64 s, `wide` 64 s, `wcag all` 91 s, `dense` 126 s.

**Regress after the edits.** Clean runs of the three touched batteries: `first-screen`
**252 / 0**, `badge-rows` **1 017 / 0**, `wcag22` **43 / 0**. The three batteries that the earlier
full-set journal recorded red at the harness — `landing-render-check.py`,
`landing-visual-pass.py`, `landing-print-contrast.py` — were re-run under the current runner and
came back green: 10.3 s, 130.8 s, 72.1 s, the last with **3 543 checks, 0 failed**. Their red was
the runner's, as the harness entry said; this block turned that sentence into a run.

**Open, and it is the same defect in other hands.** Six more batteries compare `scrollWidth` with
`innerWidth` while opening mobile contexts: `landing-a11y-extra.py`, `landing-keyboard-form.py`,
`landing-landscape-page.py`, `landing-render-check.py`, `landing-rotate.py`,
`landing-tablet-page.py`. Whether each is blind depends on which clause uses the number and which
context it runs in — it has to be measured with a control the way this one was, not fixed by
grep. That is the next block's queue, and it is written here so it cannot be remembered as done.

**What this does not prove.** That the remaining **21 batteries** are worth their green. That each
control exercises every clause of its battery: `badge-rows` asserts six invariants and the control
touches two, `wcag22` covers three of its own but not the JavaScript-error check. That an injected
style is the same event as a source-level regression — a real edit also changes the built pages,
and no tree was broken this time. And that the full 48-battery set was re-run in this block: it
was not. Only the three touched batteries and the three harness victims were run, and the last
complete journal still contains the two timeouts that the 900-second clock was meant to fix.

**Files.** `landing-wcag22-targets.py` (`--control targets|focus|anchor|all`, `arm()`, verdict),
`landing-first-screen.py` (`--control fold|wide`, `arm()`, verdict, `clientW` in the probe and in
the overflow clause), `landing-badge-rows.py` (`--control dense`, `arm()`, verdict),
`landing-regress-all.py` (`CONTROLS` as pairs, four new entries); evidence `block-20261026m/` —
four control logs, three clean logs, the ledger, and the overflow probe with its measurement
table.


## The window on a phone grew with the defect, and five batteries asked it anyway (26.10.2026)

**The queue arrived with its own warning.** The previous entry ended with six batteries that
compare `scrollWidth` with `innerWidth` while opening mobile contexts, and with the sentence that
whether each of them is blind "has to be measured with a control the way this one was, not fixed
by grep". This block measured first and fixed second.

**Twelve windows, three numbers, one defect.** New `probe-iw-vs-dw.py` opens the windows the
batteries open and reads `innerWidth`, `documentElement.clientWidth` and `scrollWidth` before and
after a defect that adds 120 px of overflow. Chromium answered:

| window | defect adds | innerWidth | clientWidth | old clause (sw ≤ iw+1) | new clause (sw ≤ cw+1) |
|---|---|---|---|---|---|
| desktop 320 / 640 / 420 / 1280, `is_mobile=False` | +120 | unchanged | unchanged | red | red |
| phone and tablet 390×844, 844×390, 768×1024, 1024×768, `is_mobile=True` | +120 | **+120** | unchanged | **green** | red |

Seven of the twelve windows were blind, and all seven were mobile: on a phone Chromium expands the
layout viewport to fit the overflowing document, so the number the clause compared against grew by
exactly the amount it was supposed to catch. The four `a11y-extra` clauses were **not** blind — they
work on a desktop context, where the viewport does not grow — so a grep-driven "fix" of all six
would have rewritten a battery that was already honest and proved nothing about it.

**WebKit never had the defect, and would have hidden it.** The same probe in WebKit (five windows,
`probe-webkit.py`): `innerWidth` stayed 390 / 844 / 768 / 1024 / 1440 and the old clause caught the
overflow every time. So this was never "mobile is blind" — it was one engine's layout-viewport
expansion, in the engine the phone actually runs. `landscape-page` and `tablet-page` run both
engines: their width clause was blind in the chromium half and honest in the webkit half — exactly
the shape a single green line in a log cannot show.

**The fix is a different number, and both engines agree on it.** Five batteries now compare
`scrollWidth` with `documentElement.clientWidth` and print all three numbers when they speak:
`landing-render-check.py` (the phone clause), `landing-keyboard-form.py` (clause A),
`landing-landscape-page.py` (clause A), `landing-rotate.py` (clause A after each turn) and
`landing-tablet-page.py` (clause A). On clean pages `clientWidth == innerWidth` in every measured
window in both engines, so the stricter-looking comparison is not stricter on an honest page —
measured, not assumed. `landing-a11y-extra.py` moved to the same number too: its clause was honest,
but the next reader copies the nearest line, and one number in six batteries is cheaper than a note.

**The first shape of the control was too loud, and the noise was measured.** The defect was a body
forced to `calc(100vw + 120px)`. It worked — the clause went red — but it also moved every box:
`keyboard-form`'s tap on the message field waited 30 s for an input that now covered it, the control
run took 103 s against 113 s for the whole 27-run battery, and it produced 8 reds where 6 were
expected. The defect became an absolutely positioned pseudo-element 120 px past the right edge
(`body::after`, out of flow). `probe-pseudo.py` measured it in 8 windows and both engines:
`scrollWidth` +120 every time, the first button's left edge moved **0 px**, the new clause red
every time. In `keyboard-form` the style tag exists only for the duration of the A measurement and
is removed before the next tap.

**What the controls returned — one red per measurement, no foreign reds.**

- `render-check --control`: **5** width reds — the four desktop pages and the phone — in 11 s; the
  phone line reads `sw=510 cw=390 iw=510`, which is the blindness written down as a number: the old
  clause would have compared 510 with 510 and said "fine".
- `keyboard-form --control`: **6 of 6** runs, one per language × device, 55 checks, **0 foreign
  reds**, 28 s (clean run of the same battery: 244 checks, 0 failed, 113 s).
- `landscape-page --control-wide` (en, ru): **12 of 12** — 2 languages × 2 engines × 3 screens, 96 s.
- `tablet-page --control-wide` (en, ru, chromium): **16 of 16** — 2 languages × 8 screens, 37 s.
- `rotate --control-wide` (en): **16 of 16** — 4 device pairs × 2 turns, 59 s.
- `a11y-extra --control`: **49 of 49** — 11 reflow + 11 zoom + 27 text-spacing measurements, every
  one naming `overflow=120`, and `iw=320` unchanged on the desktop windows.

**Clean runs after the edits.** 244 (keyboard-form) + 956 (landscape) + 1 804 (tablet) + 288
(rotate) + 267 (a11y-extra) = **3 559 checks, 0 failed**, plus `render-check` ALL OK. The five
numbers match their pre-edit baselines (a11y-extra 267/0 from 25.10, landscape 956/0 and tablet
1 804/0 measured earlier today), so this block moved the instrument, not the page. The five clean
runs took 19 minutes on a quiet machine; their controls took 5.

**The ledger counts batteries, not controls, and now says 28.** Two new `--control` flags
(`keyboard-form`, `a11y-extra`) moved it from 26 to 28 — now 12 `--mutate`, 15 `--control`, 1
`--selftest`, 1 pointer, **19 without anything**. The three `--control-wide` flags do not move the
number, and that is worth saying out loud: they sit on batteries that already had a control, and the
ledger's unit is a battery with at least one wired control. Five of the six questions from the last
entry are closed; the sixth (`a11y-extra`) turned out not to be a defect and now has a control that
says so.

**A control nobody runs is memory; the runner runs them.** `landing-regress-all.py`'s `CONTROLS`
went from 8 entries to 13, an entry may carry its own environment (`LANDING_LANGS`,
`LANDING_ENGINES`) so a slow battery is proved on a subset instead of being left out, and a battery
that needs a served root gets one in the control path as well — before this, `render-check` would
have failed its control for want of a server, and the next reader would have concluded the page was
broken. One command, `--controls`, answered **13 of 13 caught in 4.7 minutes**, the five new ones
among them; a control that is written down but never run is a note, not a fact.

**What this does not prove.** That the 19 batteries without controls are worth their green. That the
same pattern is gone everywhere: five more scripts still compare `scrollWidth` with `innerWidth`
(`landing-contact-e2e.py`, `landing-cross-engine.py`, `landing-visual-pass.py`,
`landing-browser-smoke.py`, `landing-env-prefs.py`), two of them open mobile contexts, and this
block did not measure whether their clauses are blind. That one mutation per battery exercises every
clause: `render-check` asserts five things per page and the control touches one. That an injected
pseudo-element is the same event as a source-level regression — a real edit also changes the built
pages, and no tree was broken this time. And that the full 48-battery set is green: it was not
re-run; only the five touched batteries (clean) and their controls were.

**Files.** `landing-render-check.py` (`--control`, `WIDTH_JS`, `width` in every line),
`landing-keyboard-form.py` (`--control`, `docCW`, clause A renamed to "with the keyboard open" — it
was measured after the keyboard opened and called "without"), `landing-landscape-page.py`,
`landing-tablet-page.py`, `landing-rotate.py` (`--control-wide`, `cw` in the reading, A compares with
it), `landing-a11y-extra.py` (`--control`, `dw`/`sw` in the reading), `landing-regress-all.py`
(`CONTROLS` 8 → 13, env per entry, server for controls); evidence `block-20261026n/` — three probes
with their JSON, nine run logs and `summary.json`, the control logs of the runner.


## The window grew by exactly the defect, and two clauses were happy with it (26.10.2026)

**The queue was a sentence, not a task.** The previous entry ended with five batteries still
comparing `scrollWidth` with `innerWidth` — `contact-e2e`, `cross-engine`, `visual-pass`,
`browser-smoke`, `env-prefs` — two of them opening mobile contexts, and with the words that whether
each clause is blind "has to be measured with a control the way this one was, not fixed by grep".
This block measured first and edited second.

**Thirteen windows, the batteries' own contexts, one defect.** `probe-five-blind.py` reproduces each
battery's context exactly (engine, viewport, `is_mobile`, `has_touch`, `device_scale_factor`,
JavaScript on/off) and injects the same 120 px defect: an absolutely positioned `body::after` past
the right edge, out of flow, so `scrollWidth` grows by 120 and no box moves (`dBtn=0` in all
thirteen). The defect goes **into the markup** through `page.route`, not through `add_style_tag`,
because `contact-e2e` measures with JavaScript disabled — one event, thirteen cases.

| battery | engine | window | is_mobile | old clause `sw ≤ iw+1` | new clause `sw ≤ cw+1` |
|---|---|---|---|---|---|
| contact-e2e | chromium | 390×844, JS off | no | **red** (dIW=0) | red |
| cross-engine | chromium | 420×915 | **yes** | **green, dIW=+120** | red |
| cross-engine | webkit | 420×915 | yes | red (dIW=0) | red |
| cross-engine | firefox | 420×915 | no (unsupported) | red | red |
| cross-engine | ×3 | 1440×900 | no | red | red |
| visual-pass | chromium | 420×844 | **yes** | **green, dIW=+120** | red |
| visual-pass | chromium | 1440×900 | no | red | red |
| browser-smoke | chromium | 1280×900 / 390×844 | no | red | red |
| env-prefs | chromium / webkit | 420×915 | no | red | red |

Two of thirteen were blind, both chromium with `is_mobile=True`: `innerWidth` grew by exactly the
defect (420 → 540) while `clientWidth` stayed 420. All thirteen clauses written against
`documentElement.clientWidth` went red, and on clean pages the three numbers are equal
(`sw = cw = iw` in every row), so the stricter-looking comparison is not stricter on an honest page.

**`cross-engine` was blind in a branch it does not run.** `run_engine` opens mobile contexts with
`is_mobile=True` for every engine except firefox, and `main()` loops over `('webkit','firefox')`:
chromium is never launched there. The live battery was honest by engine choice, not by design, and
the blind branch sat one tuple entry away with a comment that gave no hint.

**The loud control fires on the blind window — which is why nobody noticed.** Before the fix,
`visual-pass --mutate` (a 3000 px wide div) went red on the mobile window as well: `doc=3000
vw=1680`. Chromium clamps the layout-viewport growth at four times the width (420 → 1680), so a
defect larger than the clamp still exceeds `innerWidth`, while a 120 px overflow sits inside the
clamp and is invisible. A coarse control passes over a fine blindness — therefore the new control is
120 px, not 3000.

**Eight files, one number.** The five named batteries now compare `scrollWidth` with
`documentElement.clientWidth`; `grep` then turned up three more with the same line —
`header-engines` (document clause), `video-motion` (320 px clause), `toggle-clear` — all honest in
their present contexts and all one `is_mobile=True` away from the same blindness, so all three moved
to the same number. `cross-engine` keeps `overflowIw` deliberately: the control prints with it that
the old clause was blind. `header-engines` keeps `innerWidth` for the switcher's right-edge limit —
that clause measures a position inside the row, not the width of the document.

**Two controls, and both print the blindness as a number.** `cross-engine --control`: chromium
mobile, en — clean `sw=420 cw=420 iw=420`, after the defect `sw=540 cw=420 iw=540`; new clause red,
old clause blind, in the same line. `visual-pass --control-wide` on en,ru × mobile,desktop: **4 of
4** red, and the mobile line reads `doc=540 cw=420 iw=540`. With the loud defect the same battery
produced 4 flags as well — the difference is that the soft defect is the one the old clause could
not see. `CONTROLS` went from 13 to 16; the ledger counts 29 of 48 batteries with a wired control,
1 pointer, 18 without anything.

**Three batteries did not parse under the interpreter that has the browsers.** `contact-e2e`,
`rotate` and `sweep` used f-strings with a backslash, or `','.join(...)` inside the expression —
3.12-only syntax. The suite's own runs use python 3.14, so they ran there; but
`python3 landing-rotate.py` under the uitest venv (3.11, the one whose webkit and chromium match the
installed builds) died with `SyntaxError` before the first page. All three were rewritten without the
3.12-only forms, and all **62** scripts now compile under 3.11 and 3.14. `landing-regress-all.py`
compiles every battery before running it and journals `PARSE-ERROR` with the line number instead of
a mysterious red.

**Clean runs after the edits — the page did not move.** `sweep` 2 896 checks / 0 failed;
`contact-e2e` 910 / 0 (135 s — the first time it ran at all under 3.11); `visual-pass` 18 windows,
PROBLEMS 0 (131 s); `browser-smoke` 18 runs, 0 problems; `env-prefs` 45 / 0; `header-engines`
973 / 0 (419 s); `toggle-clear` 56 / 0; `video-motion` 444 / 0 (104 s); `cross-engine` 60 runs,
0 problems (426 s).

**The controls, run by the runner rather than remembered.** `--controls`: **16 of 16 caught** in
605 s. The two new entries sit on the two defects that differ in size, and both print the numbers
they fired on: `visual-pass --control-wide` 4 windows of 4, `visual-pass --mutate` 4 of 4 (the loud
block, which also exercises the element-level clause), `cross-engine --control` 1 of 1. Making
`visual-pass` usable as a control took a small edit of its own: it used to exit 1 whenever it found
anything, and the runner reads code 0 as "caught", so its control could never have been in the list —
it now says `КОНТРОЛЬ ПОЙМАЛ` and exits 0 in the two mutation modes only.

**What this does not prove.** That the 18 batteries without controls are worth their green. That one
defect per battery exercises every clause: `visual-pass` asserts image aspect ratios, badge rows,
clipped text and heading sizes in the same probe, and the width control touches one of them. That an
injected pseudo-element is the same event as a source-level regression — a real edit also changes the
built pages, and no tree was broken this time. That firefox's mobile emulation was measured:
playwright has no `is_mobile` for it, so that column is honestly "not applicable", not "honest". And
that the full 48-battery set was re-run: it was not.

**Files.** `landing-cross-engine.py` (`overflow` on clientWidth, `overflowIw`, `--control`,
`run_width_control`), `landing-visual-pass.py` (`clientW` in the probe and in both clauses,
`--control-wide`, `WIDE_CSS`), `landing-browser-smoke.py`, `landing-contact-e2e.py` (and the f-string
it could not parse), `landing-env-prefs.py`, `landing-header-engines.py`, `landing-video-motion.py`,
`landing-toggle-clear.py`, `landing-rotate.py`, `landing-sweep.py`, `landing-regress-all.py`
(compile gate, `CONTROLS` 13 → 16); evidence `block-20261026o/` — `probe-five-blind.py` and its JSON
(13 windows × 3 numbers × before/after), `ctl-before-visual-pass.log` (the loud defect on the
pre-fix battery), `ctl-wide-visual-pass.log`, `clean-*.log` for nine batteries, `run-battery.py`,
`ledger.json`.

## Three green batteries that had never once been red (27.10.2026)

**A control remembered is a control not run.** The ledger counts 48 batteries and says which of them
can be broken on purpose. Three of the hero-video batteries sat in the other column: `video-motion`
(444 checks, 408 of them about the stop mechanism WCAG 2.2.2 requires), `toggle-clear` (56 checks
that compare pixels of the frame with and without the button) and `poster-frames` (9 checks that the
poster is the last frame of its own loop). All three printed "0 failed" — and not one of them had a
control: nothing proved they would notice the absence of the thing they measure.

**Each break is the defect the battery was written for.** Every control builds a hardlinked copy of
the tree and unlinks the file it edits, so the working tree is never touched:

- `--control nobutton` removes the `<button id="video-toggle">` element itself from all nine pages.
  **183 red**, of which 18 say in plain words that the stop button is not in the built page; nothing
  else went red.
- `--control overlap` lifts the button's row 52 px up, onto the frame — the defect of 24.10. The
  pixel clause fires in **7 cases out of 7**, the gap reads −52 px: 21 red, no foreign ones.
- `--control swap` swaps the English and Russian posters. RMSE **0.14896 / 0.14891** against a
  threshold of 0.02, while the other seven languages stay at 0.00676–0.00790 — the two classes apart
  by a factor of nineteen, as calibrated on 26.10.

**Three things this block learned the hard way.** In this build English has no `en/` directory — its
page is the root one, and the first control run died on "no page …/en/index.html", a break in the
harness rather than in the page. Removing the button does not redden only the button clauses: the
same script that shows the button also starts the loop and stops it off screen (`if (!btn) return`
sits above the visibility subscriptions), so `autoplay runs` and `reduce: not autoplaying` go red as
a consequence — the verdict has to name the shapes it expects, or the control is red forever and
worth nothing. And a mutation has to print what it applied: "caught" and "the break never landed"
look identical from an exit code alone, so each control reports the number of pages or files it
changed.

**Clean runs after the edits.** `video-motion` 444 checks / 0 failed (104 s), `toggle-clear` 56 / 0,
`poster-frames` 9 / 0; `sweep` before the edits 2 896 / 0. The runner then proved the controls itself,
one command and no memory: `--controls` **19 of 19 caught**, the three new entries among them, and the
whole list green in one pass. The ledger now reads **32 of 48** batteries with a wired control, one
pointer, **15 without anything**.

**What this does not prove.** That the remaining 15 batteries are worth their green. That one break
per battery exercises every clause: `video-motion` also asserts labels from the dictionaries and the
320 px layout, and the missing-button control touches only what depends on the button.

**Files.** `landing-video-motion.py` (`--control nobutton`, the control tree builder, the verdict),
`landing-toggle-clear.py` (`--control overlap`, root as an argument), `landing-poster-frames.py`
(`--root` and `LANDING_ROOT`, `--control swap`), `landing-regress-all.py` (`CONTROLS` 16 → 19).

## Two loudest claims had never been red, and one of them had never seen the desktop (27.10.2026)

**The queue was the ledger.** The previous block closed with `landing-controls-ledger.py` reading
**32 of 48** batteries with a wired control, one pointer, **15 without anything**. Two of those 15
carry the loudest claims on the site: `landing-axe-audit.py` has printed `TOTAL VIOLATIONS: 0`
since 16.10, and `landing-glyph-fallback.py` has printed `0 подмен` since 22.10. A green run from
either is worth exactly what its ability to go red is worth, and neither had ever gone red. This
block took both — and the second one answered a question the first could not: it turned out to be
blind to the desktop.

**Nine skipped nodes, printed for three days and never explained.** Since 24.10 the glyph battery
has printed `пропущено=9` on every language page and `=1` on the legal pages — 84 text nodes
across the site whose glyphs were never counted. `probe-skipped.py` walked those nodes through
CDP and asked each one for its computed display, its boxes and its text: the `<title>`, four
header links, and four hidden form messages (`contact-ok`, two `contact-err`, `Sending…`). The
title and the form messages have no boxes at any width — honest skips, they are never drawn. The
four links are `display:inline` with **zero boxes at 420 px** because an ancestor hides them, and
they have boxes at 1280: `How it works`, `Features`, `Pricing`, `FAQ`.

**So the battery had been measuring the phone and calling it the site.** Every run since 22.10
opened the pages at 420×900. The header menu exists in the DOM of all nine language pages, is
rendered only above the breakpoint, and no other battery asks which font drew it — the sweep reads
files, the header batteries read geometry. The page is fine: measured at 1280, all four links are
drawn by Manrope. The proof was not.

| page | phone 420 | desktop 1280 | desktop added |
|---|---|---|---|
| en | 4 894 | 4 934 | +40 |
| ru | 4 790 | 4 840 | +50 |
| es | 5 434 | 5 488 | +54 |
| pt | 5 391 | 5 443 | +52 |
| hi | 4 545 | 4 586 | +41 |
| id | 5 286 | 5 318 | +32 |
| tr | 4 975 | 5 024 | +49 |
| vi | 5 287 | 5 340 | +53 |
| uk | 4 981 | 5 029 | +48 |
| privacy.html | 17 826 | 18 037 | +211 |
| terms.html | 9 483 | 9 585 | +102 |
| 404.html | 347 | 349 | +2 |

147 212 glyphs in two windows, 73 239 and 73 973, and every one of them custom. The desktop window
adds 734. Only 30 of the 40 on `en` are the four links; the other ten are spread over 31
paragraphs that draw one or two **fewer** or **more** glyphs in a wider window (26 up, +64; 9
down, −24). And on the legal pages there is no new node at all: `privacy.html` has 92 measured
nodes at both widths and +211 glyphs, distributed over 64 paragraphs, each +1…+12. `glyphCount`
from CDP is a shaped-glyph count, not a character count: the same sentence, broken into different
lines at a different width, is a slightly different number of glyphs. The floor is therefore a
bound, not an equality — which is what it always was, and now it is stated.

**Both windows, and a floor for each.** Instead of picking one width, the battery measures each
page at 420×900 and 1280×900 and reports both (`глифов=4894+4934`). `FLOOR` keeps its 24.10 phone
numbers; `FLOOR_WIDE` was measured today and cut by 15 % (4 100 default, 15 300 privacy, 8 100
terms, 290 on the 404). An undercount in **either** window is red, and the verdict names the
window (`hi/desktop: 4 586 глифов < пола …`).

**The control is one heading, not a whole page.** The cheap defect is a page-wide
`body{font-family:Georgia}` — and it is the wrong one: a battery that asked only "did any custom
font load at all" would still go red, and that clause is not the one this battery has.
`--control` injects `#main h1{font-family:Georgia,"Times New Roman",serif!important}` into
`ru/index.html` of a hard-linked copy and requires the battery to name that page in **both**
windows: it does, **31 glyphs per window**, while `en` beside it stays at zero. The clean copy runs
in full first — 12 pages × 2 windows, 0 substitutions, 0 undercounts — because a control must also
prove that the copy itself does not break the pages.

**axe: a defect the rule set actually has.** `--control` copies the tree, drops
`<img src="/img/logo.svg" width="12" height="12">` — no `alt` — inside `<main>` of
`ru/index.html`, and requires exactly one violation, `image-alt`, on that page and none on
`index.html` beside it: clean copy 12 pages / 0 violations, defect copy
`ru/index.html -> ['image-alt']`, `index.html -> ничего`. Twenty-one seconds for both runs
together. The harness detail that makes two runs in one process possible: both reuse port 8242, so
the server is closed with `server_close()` as well as `shutdown()` — a listening socket left open
is an «Address already in use» on the second run.

**Both batteries now speak the journal's sentence.** Neither printed `CHECKS: N, FAILED: M`, so
`landing-regress-all.py` journalled them as `checks=None` — two batteries were invisible in the
full run's check count. axe counts pages (12), the glyph battery counts a page in a window (24).

**Clean runs after the edits.** `axe` 12 pages / 0 violations (16 s, `CHECKS: 12, FAILED: 0`);
`glyph` 12 pages × 2 windows / 147 212 glyphs / 0 substitutions / 0 undercounts (33 s,
`CHECKS: 24, FAILED: 0`); `sweep` 2 896 checks / 0; the runner on each file in turn:
`checks=12 failed=0` and `checks=24 failed=0`. Controls: axe — 12 pages clean, then exactly one
`image-alt` on the broken page and none on the neighbour; glyph — 24 measurements clean, then 31
glyphs per window on `ru/` and zero on `en`. The ledger now reads **34 of 48** batteries with a
wired control, one pointer, **13 without anything**.

**What this does not prove.** That the 13 remaining batteries are worth their green. That one
defect per battery exercises every clause: axe runs a hundred-odd rules and one `image-alt` proves
the pipeline, not the rule set; the glyph control moves one element and says nothing about clipped
text or about the drawing being right beyond `isCustomFont`. That the two windows cover the site:
320 px, the tablet breakpoints and print are other batteries, measured on their own.

**Files.** `landing-axe-audit.py` (`--control`, `--root`/`LANDING_ROOT`, the copy builder, the
verdict, the `CHECKS` line), `landing-glyph-fallback.py` (`WINDOWS` 420+1280, `FLOOR_WIDE`,
`--control`, `--root`/`LANDING_ROOT`, comma list in `--only`, the `CHECKS` line),
`landing-regress-all.py` (`CONTROLS` 19 → 21). Evidence in `evidence/block-20261027a/`:
`probe-skipped.py` (+ the `skipped-nodes-w420/w1280.json` it wrote), `probe-desktop-glyphs.py`,
`probe-node-diff.py` (+ `node-diff.json`), `probe-glyph-widths.py`, `glyph-2windows.json`,
`clean-axe.log`, `clean-glyph.log`, `ctl-axe.log`, `ctl-glyph.log`, `summarise*.py`.

## Two green batteries guarded the loudest numbers on the site, and the markup was not the mechanism (27.10.2026)

**The ledger named eleven.** `landing-controls-ledger.py` read **34 of 48** batteries with a wired
control, one pointer, **13 without anything**. Two of those thirteen carry numbers a visitor acts on:
`landing-fonts.py` prints 41 green checks that a page downloads ≤160 KB of fonts, that opening the
language menu adds ≤12 KB, and that the 404 carries its own Devanagari; `landing-video-weight.py`
prints 129 green checks that the hero video is not fetched on 3G and that the first screen fits in
600 KB. A green run from either was worth exactly what its ability to go red was worth, and neither
had ever been asked to.

**The font control is the October defect, replayed.** `--control` builds a hard-linked copy, runs the
battery on that copy **untouched** first — 41 of 41, because a control must also show that the copy
itself does not break the pages — and then writes one `<style>` before `</head>` of `ru/index.html`:
an `@font-face` for a *foreign full subset* (`/fonts/noto-sans-devanagari-hi.woff2`, 68 KB) plus
`details.lang-dd[open] .lang-list>*{font-family:"CtlForeign"!important}`. That is the 22.10 defect in
its own words — a foreign script's full subset arriving when the switcher opens, not before. The
battery names it twice and leaves the neighbour alone:

| | closed | on open | red |
|---|---|---|---|
| `ru/` as built | 38.4 КБ | +6.1 КБ | 0 of 41 |
| `ru/` with the defect | 38.4 КБ | **+68.3 КБ** | 2 of 41: «открытие ≤ 12 КБ», «чужие полные сабсеты» |
| `en` beside it, same copy | 24.3 КБ | +9.0 КБ | 0 |

**The video control was not where the defect lives.** The obvious break is the markup —
`preload="none"` → `auto` on `#hero-video`. It is the wrong one: the inline script at the bottom of
the page reads the channel and *rewrites* that attribute in its first frame, so `preload` in markup is
a fallback for the no-script case only. A markup-only defect is then a race between the parser and the
script — sometimes red, sometimes not — and a control whose redness depends on a race proves nothing.
The load-bearing line is `var auto = !reduce && !save && !slow;`: drop `&& !slow` and 3G becomes 4G for
that language. That one line, changed in `ru/index.html` of the copy, turns six clauses red — three
expected («ролик не запрошен», «readyState 0», «preload none») and three honest consequences of the
same defect (the video is playing, so «на паузе» is red; the button says «пауза»; the click then
pauses it). **123 of 129**, every red one on `ru`, `en` untouched.

**The runner could not run one control.** `--controls` ignored `--only`, so proving a new control meant
23 controls in a row — half an hour — and in practice the proof was skipped rather than paid for. The
controls loop now takes `--only` and prints its own scope (`контролей: 2 из 23`), so a partial run
cannot be read as a full one. Through it: **2 of 23, both caught, 265 s** (`fonts` 84.5 s,
`video-weight` 180.6 s).

**Both files were rewritten, not patched.** Three changes to each (arguments, split into
`measure()`, `--control`) plus the port pitfall — `shutdown()` alone leaves the listening socket, and
the second run in the same process dies on «Address already in use», so both close with
`server_close()` too. The rewrite is faithful, and the clean numbers say so: `fonts` 41/41 in 42.4 s
before and after, `video-weight` 129/129 in 90.6 s and 90.2 s. The ledger now reads **36 of 48**
batteries with a wired control (12 `--mutate`, 23 `--control`, 1 `--selftest`), one pointer,
**11 without anything**.

**What this does not prove.** That the eleven remaining batteries are worth their green. That one
defect per battery exercises every clause: the font control hits the two «open» clauses and says
nothing about the 160 KB cap on a closed page or about the 404 clause (each needs its own defect — a
page-wide large `@font-face`, a 404 page that declares no Devanagari face); the video control hits the
3G branch of one language, while `reduce`, `saveData`, 4G and «no Network Information API» are four
more branches with no control of their own. That 3G is really 3G: `navigator.connection` is still
substituted by an init script, and desktop Chrome reports `4g` under real throttling — the rule is
blind there, and that stands. Chromium only: WebKit and Firefox font loading is not measured by this
pair.

**Files.** `landing-fonts.py` (`--root`/`LANDING_ROOT`, `--port`, `--evidence`, `--control`, the
`measure()` split, `server_close()`), `landing-video-weight.py` (same, plus the JS-line defect
`DEFECT_FROM`/`DEFECT_TO` that refuses to run if the line is gone), `landing-regress-all.py`
(`CONTROLS` 21 → 23, `--only` for the controls loop). Evidence in `evidence/block-20261027b/`:
`clean-fonts.log`, `clean-fonts-refactor.log`, `ctl-fonts.log`, `clean-video.log`,
`clean-video-refactor.log`, `ctl-video.log`, `runner-controls.log`, `control-fonts.json`,
`control-video.json`, `fonts.json`, `video-weight.json`.

## Three batteries read the real tree and had never been red, and the fourth element of the first was a blank rectangle (27.10.2026)

**The ledger said eight.** After the font/video pair the count stood at **36 of 48** with a wired control,
one pointer, **11 without anything**. Three of those eleven were not marginal: `landing-font-identity.py`
(7 clauses — the 70 KB Devanagari subset draws what the 121 KB source draws), `landing-site-move-test.py`
(17 clauses — a change of address propagates to 24 files) and `landing-header-engines.py` (973 clauses — the
header row stays inside the margins in Chromium, Firefox and WebKit, under WCAG 1.4.12 spacing too). All three
read the tree as built; none could be made red by anything. The ledger now reads **39 of 48**, one pointer,
**8 without anything**.

**The font battery was blind on one of its four elements.** `--control` needed a defect, and the honest defect
was the October one replayed: a subset built from the same source with the same 57 codepoints and `hinting=False`
— the file that was 28 B lighter on 26.10 and drew the page differently. The first run was red on three
elements and **green on the FAQ answer**. Not a lucky pass: the screenshots were 696×178 at **one colour**,
794 B, both runs. The answer lives inside `details.rv`, and `.rv` is revealed by an IntersectionObserver — at
capture time the block was still `opacity:0`, so Playwright photographed an empty rectangle twice, and
«0 расхождений» meant «nothing was drawn». It had been that way since the battery was written. The fix is a
style tag before capture (`.rv{opacity:1!important;…}` — 306 colours after it, the same element now reads
**15 851 px** against the no-hinting twin) plus a floor: a frame with fewer than **20 colours** fails the clause
instead of passing it, and run 2 is checked for paint too. The battery went 7 clauses → **12**.

**The control is the October file, byte for byte.** `landing-font-identity-twin.py` repeats `tools/subset-deva.py`
with one line changed (`opts.hinting = True` → `False`) and runs under an interpreter that has fontTools+brotli —
the system python does not, so the battery probes `LANDING_FONTTOOLS_PY` and then the known venvs and refuses to
pretend. Output: **69 932 B** against the shipped **69 960 B**, i.e. the 26.10 defect reproduced to the byte.

| element | clean pair | no-hinting twin |
|---|---|---|
| h1 (800, 350×72) | 0 px | **12 631 px** — the number from 26.10 |
| lead (400, 350×115) | 0 px | **35 288 px** — the number from 26.10 |
| FAQ answer with matras (348×88) | 0 px | **15 851 px** — a clause that could not have been red before |
| footer (14 px, 350×21) | 0 px | **1 015 px** |
| total | 0 px on 4 of 4 | **64 785 px on 4 of 4** |

**The move test needed a defect the build could not repair.** The obvious control — write the old address into a
hand-written file — is worthless here: `tools/build.py` normalises every address listed in `previous`, and its own
`audit_site_address()` aborts the build on any foreign host, so the injected address either disappears or the copy
never gets built. The defect has to survive a *green* build, and the clause that matters does: the form's return
address carries the page's language (`?sent=1#contact-card`). One line removed from `build.py` in the copy and the
return falls back to the root — 8 of the 9 languages named (en passes, because `url_for('en')` is the root), with
canonical, sitemap, robots and the `{{BASE}}` clauses left green. Clean copy **17 / 17**, defective copy **17 with 1
red**, and the red one lists `ru, es, pt, hi, id, tr, vi, uk`.

**The header battery's own docstring was wrong.** It said: «часть 2 без правила 25.10 красная». Rolled the two
declarations back in a copy (`gap:2px 22px`, `.lang-dd{margin-left:0}`) and measured: **109 checks, 0 red** in
Chromium — because `flex-wrap:wrap` on `.top-in` remains, and the switcher simply drops to a second line, which is
legal for every clause the battery has. So the battery proves «the row does not leave the margins» and says nothing
about the 25.10 aesthetics (the switcher's position at the right edge is not measured at all). The docstring now says
so. The control reproduces the failure the rule exists to prevent: at ≤760 px the row stops wrapping
(`flex-wrap:nowrap`), and the battery reddens **33 of 325** — every red at 320 or 340 px, **0 at 420+**, named by
«документ не шире экрана» (3) and «переключатель внутри правого поля» (30). Clean copy **325 / 0** in the same run.

**Numbers.** Full runs on the real tree: font-identity **12 / 0** in 5 s, site-move **17 / 0** in 12 s (copy + build),
header-engines **973 / 0** in 420 s. Controls: font-identity **4 of 4 red**, site-move **8 languages named**,
header-engines **33 red of 325**, all three with the clean copy or clean pair green in the same invocation.
`landing-regress-all.py`: `CONTROLS` **23 → 26**, and the twin helper was added to `SKIP` — it matches
`landing-*.py` and would otherwise have entered the suite as a «battery without a control» and inflated the ledger.

**What this does not prove.** That the other eight are worth their green — they are the same kind of claim. One
defect per battery does not exercise every clause: the font control is Chromium at DSF 2 on one page, and it proves
the hinting half only — a subset built from the wrong codepoint set (a dropped matra) has no control yet; the move
test moves to `example.org` and proves nothing about a real host, redirects at the edge, DNS or TLS; the header
control breaks one rule at one breakpoint, while 761 px, the menu clause and the right-edge position have no defect
of their own. And the twin keeps following `tools/font-src` and the registry, so it proves the battery sees a
drawing change, not that the shipped subset is the right subset.

**Files.** `landing-font-identity.py` (`--control`, forced reveal, colour floor, `measure()` split, `server_close()`),
`landing-font-identity-twin.py` (new; `--probe`, `--source/--registry/--out`), `landing-site-move-test.py`
(`--control`, `--dst`, `run()`/`control()`, `drop_redirect_language()`), `landing-header-engines.py` (`--control`,
`run(root, engines, langs)`, `BROKEN_HEADER_CSS`, corrected docstring), `landing-regress-all.py` (`CONTROLS`
23 → 26, `SKIP` + twin). Evidence in `evidence/block-20261027c/`: `clean-font-identity.log`,
`ctl-font-identity.log`, `clean-site-move.log`, `ctl-site-move.log`, `clean-header-engines.log`,
`ctl-header-engines.log`, `ledger.log`.

## One of the two numbers could go blind without a sound, and the other could only be wrong about the file it was written for (27.10.2026)

**The ledger said eight.** After the three-battery block the count stood at **39 of 48** with a wired control,
one pointer, **8 without anything**. Two of those eight carried the numbers a visitor feels in the first second:
`landing-cwv.py` (69 clauses — LCP ≤ 2500 ms, CLS ≤ 0.1, FAQ tap ≤ 200 ms, nine languages plus three desktops) and
`landing-pixel-density.py` (558 clauses — how many pixels a file gives against what the screen asks, 9 languages ×
5 profiles). Both read the tree as built. Neither had ever been red. The ledger now reads **41 of 48**
(28 `--control`, 12 `--mutate`, 1 `--selftest`), one pointer, **6 without anything**.

**One of the two clauses could go blind silently, and it was the quiet one.** The LCP clause cannot: it requires
`lcp['t'] is not None`, so a dead `PerformanceObserver` reddens the clause instead of passing it. CLS is a sum —
no entries means `0`, and `CLS <= 0.1` is then green forever. So the defect had to be a **shift**, not a slow
paint: a 260 px band inserted above `<main>` **1.2 s after `DOMContentLoaded`** — a banner with no space reserved
for it, which is the shape this defect takes in the wild. Numbers: `ru` mobile **CLS 0.2851**, `ru` desktop
**0.1679**; exactly the two CLS clauses red, LCP green in the same run (the band appears at 1.2 s, the 2.5 s
threshold is not touched), **67 of 69** green on the defective copy and **69 / 69** on the clean copy in the same
invocation.

**The pixel battery had a control of its probe and none of its thresholds.** Rule 5 («on 1x every file must be
≥ 1.0») keeps the measurement alive, but rules 1–4 — the four numbers the battery exists for — had never been red
on a real defect: «everything is in order» and «the threshold compares nothing» printed the same word. The honest
defect was the historical file: `img/demo-poster-ru.webp` cut from 720×1560 to **540×1170** (**46.1 KB → 33.8 KB**),
the poster the battery was written about. Red: rule 1 (poster ≠ frame) on **5 profiles**, rule 2 (poster softer
than the loop) on **5**, rule 4 (the 3x ceiling) on the **two 3x** profiles — **12 of 124** (the control runs
`en`+`ru`: it proves the clause, not the size of the set), no stray failure, clean copy **124 / 124**. The weight
clause stayed green *because* the defect made the file smaller: a poster shrunk to fit the budget is exactly the
defect the budget cannot see.

**Numbers.** Full runs on the real tree, before and after the rewrite: cwv **69 / 0 — 77 s → 76 s**,
pixel-density **558 / 0 — 174 s → 174 s**, so the split changed no clause. What the cwv run says today: LCP
**992–1032 ms** on the phone (element `video.`, i.e. the hero poster), CLS **0–0.0016**, FAQ tap 6.8–17 ms, and
the whole 69-clause set in 76 s. `landing-regress-all.py`: `CONTROLS` **26 → 28**, and `--controls --only
cwv,pixel` gives **2 of 28, both caught** (153 s, 80 s) — the partial run prints its scope, so it cannot be read as
the whole list.

**What this does not prove.** One defect per battery. The band proves the shift observer, not the other eight
languages (they were green in both runs) and not the shape of a shift caused by a late font swap or a lazy image;
the LCP clause still has no defect of its own — a poster arriving after 2.5 s is `landing-video-weight.py`'s
territory, and its control breaks a different line. In pixel-density the defect is a poster only: the chat frames
(rule 3), the SVG exclusion and the 1x probe rule have no defect of their own. And the pair says nothing about the
six still in the ledger: `landing-env-prefs.py` (45 clauses — reduced motion, saveData, forced colours),
`landing-return.py` (216 — the visitor who came back with «back»), `landing-viewports-extra.py` (tablet, landscape,
1920, Slow 3G), `landing-browser-smoke.py` (18 runs over nine languages), `landing-external-links.py` (network, not
in the sweep) and `landing-stop-rule.py` (13 live tasks against the bot's prompt).

**Files.** `landing-cwv.py` (`--root/--port/--evidence/--control`, `probe()`/`measure()` split, `server_close()`,
`DEFECT_HTML`, control JSON), `landing-pixel-density.py` (the same split, `measure(root, port, langs)`,
`inject_defect()` — PIL downscale behind a broken hard link), `landing-regress-all.py` (`CONTROLS` 26 → 28; the
stale «13 of 48 without control» in the header replaced by a pointer at the ledger), `SKILL.md` (ledger count,
`--root` instead of `LANDING_ROOT`, the new control). Evidence in `evidence/block-20261027d/`: `clean-cwv.log`,
`clean-cwv-refactor.log`, `ctl-cwv.log`, `clean-pixel.log`, `clean-pixel-refactor.log`, `ctl-pixel.log`,
`runner-controls.log`, `control-cwv.json`, `control-pixel.json`.

## The settings battery had no way to be broken, and the return battery had only a pointer at an old commit (27.10.2026)

**The ledger said six.** After the first-second block it read **41 of 48** with a wired control, one pointer,
**6 without anything**: `landing-env-prefs.py` (45 clauses — reduced motion, saveData, forced colours, dark,
WebKit), `landing-return.py` (216 — the visitor who came back), `landing-viewports-extra.py`,
`landing-browser-smoke.py`, `landing-external-links.py`, `landing-stop-rule.py`. Two of them carry states a
visitor actually meets in the first minute, and neither had ever been red.

**The settings battery could not be broken at all, and that was the defect.** `landing-env-prefs.py` held its
tree in a literal path and a fixed port: the only way to break something was to break the live tree. Ten days of
green, and not one of the 45 clauses could have been shown to fail. The tree and the port are arguments now
(`--root`, `LANDING_ROOT`, `LANDING_PORT`); the evidence folder follows the tree.

**Its control is the defect the battery was written about.** The forced-colours rule exists because until 17.10
the buttons were plain text in the Windows high-contrast theme — `border 0px none`, no outline, nothing that
says "press me". The fix is one line: `@media(forced-colors:active){.btn,.contact button.btn,.lang-dd
summary{border:1px solid}}`. The control copies the tree on hard links, cuts that block out of the built
`index.html` (brace-matched, so a nested block cannot be left half-removed), and measures both copies. Numbers:
the defective page reddens **exactly three** border clauses — `CTA .btn=0px/none`, `submit=0px/none`,
`переключатель языка=0px/none` — while the five-node clause «color differs from background» and the overflow
clause stay green, and the clean copy is **0 of 0** red in the same invocation. That "three red, the neighbours
green" is the point: a battery that reddens everything proves a break, not a clause.

**The return battery had a pointer, and a pointer is not a control.** Its header offered
`LANDING_ROOT=<previous commit>`, which was honest on 26.10 and useless afterwards: it shows the battery
separates an old commit from a new one, not that the clause sees a defect. The carrying decision is one
expression in the reveal script — `var back = (!!nav && nav.type === 'back_forward') || (!!performance.navigation
&& performance.navigation.type === 2);`. The control kills **both** signals in all nine built pages
(`'back_forward'` → a type that does not exist, `=== 2` → `=== 99`); killing one would be a control that stays
green wherever the engine falls back to the other. Numbers, en+ru × Chromium-phone + WebKit-phone (48 checks):
clean copy **48 / 0**; defective copy **48 checks, 4 red** — and all four are the clause the battery exists for
(«B после возврата показано всё»): Chromium `en` `hidden=8 revealed=0/37`, Chromium `ru` `hidden=9 revealed=0/37`,
WebKit `en` `hidden=1 revealed=5/37`, WebKit `ru` `hidden=6 revealed=5/37`. The other **44 stay green** — the
normal entrance still animates (A), scrolling still reveals (A), `#faq` still arrives shown (C), the scroll
position still comes back, the sticky band, the paused video, the typed address and the zero JS errors are
untouched. A break that reddens the return and leaves the arrival alone is what makes the red mean "came back",
not "the reveal script is gone".

**Numbers.** Full runs on the real tree, before and after the rewrite: env-prefs **45 / 0 — 22 s → 22 s**,
return **216 / 0 — 149 s → 149 s**, so the split changed no clause. `landing-regress-all.py`: `CONTROLS`
**28 → 30**, and `--controls --only env-prefs,return` gives **2 of 30, both caught** (4.8 s and 68.4 s), with the
scope printed so a partial run cannot be read as the whole list. The ledger now reads **43 of 48** (12
`--mutate`, 30 `--control`, 1 `--selftest`), one pointer, **4 without anything**.

**What this does not prove.** One defect per battery. In env-prefs the control breaks forced colours only: the
reduce branch, saveData, the dark-scheme delta and the WebKit half have no defect of their own (the reduce
branch's carrying line — `var auto = !reduce && !save && !slow;` — is controlled in `landing-video-weight.py`,
a different battery), and only the English page is broken, so the language half of the clause set is proven by
the clean run alone. In return the control runs en+ru, so it proves the clause and not the other seven
languages, and it breaks the reveal script, not the other things a returning visitor needs — bfcache still
cannot be measured in this environment. And the pair says nothing about the four still in the ledger:
`landing-viewports-extra.py`, `landing-browser-smoke.py`, `landing-external-links.py` (network, not in the
sweep) and `landing-stop-rule.py` (13 live tasks against the bot's prompt).

**Files.** `landing-env-prefs.py` (`--root`/`--control`, `run()`/`control()` split, `fc_verdict()`,
`strip_fc_rule()`, hard-link copy with unlink+write), `landing-return.py` (`--root`/`--langs`/`--control`,
`run()`/`control()` split, `RESULTS`, `control_tree()`), `landing-regress-all.py` (`CONTROLS` 28 → 30,
the header pointer left as it was), `SKILL.md` (ledger count and the two lessons). Evidence in
`evidence/block-20261027e/`: `clean-env-prefs.log`, `ctl-env-prefs.log`, `clean-env-prefs-refactor.log`,
`clean-return.log`, `clean-return-refactor.log`, `ctl-return.log`, `return-control-clean.json`,
`return-control-defect.json`.

## Two batteries that watched nine languages had never once been red (27.10.2026)

**The ledger said four.** After the settings-and-return block it read **43 of 48** with a wired control, one
pointer, **4 without anything**: `landing-viewports-extra.py`, `landing-browser-smoke.py`,
`landing-external-links.py` (network, not in the sweep) and `landing-stop-rule.py` (13 live tasks against the
bot's prompt). Two of the four are the batteries a visitor actually meets: the viewport battery measures the
tablet, the landscape, the wide screen, Slow 3G and the 404 page (94 clauses), and the smoke battery loads all
nine languages at desktop and at phone width (18 runs). Both had been green since they were written, and neither
could be made red.

**Neither could be broken, and that was the defect.** `landing-viewports-extra.py` held the tree in a literal
path and a fixed port; `landing-browser-smoke.py` did the same and, worse, ran at import — the server started,
the browser opened and the verdict printed while the file was being read, so there was no place to hand it a
different tree. Ten days of green with no way to show a single clause failing. Both now take the tree and the
port as arguments (`--root`, `LANDING_ROOT`, `LANDING_PORT`), and both are split into `run()` and `control()`:
the sweep calls `run()`, the control calls the same page-checking code and reads its findings directly, so the
control cannot drift away from the clauses it is proving.

**The wide screen loses its ceiling.** Section C is the one that says text does not stretch across a 1920
monitor, and its carrying line is `.wrap{max-width:1060px;margin:0 auto;padding:0 20px}`. The control copies the
tree on hard links and cuts `max-width:1060px;` out of the rule in `index.html` and `ru/index.html` (the two
pages that section measures), then loads both copies at 1920x1080. Numbers: clean copy measures **1060 px** and
**0 red** in en and ru; the defective copy measures **1920 px** and reddens **exactly two clauses** — `C en: wrap
<=1060 and centered` and `C ru: wrap <=1060 and centered`. The sticky band's `display:none`, the hero's two
columns and the overflow clause stay green, which is the point: a battery that reddens everything proves a break,
not a clause. The honest limitation is in the docstring: `centered` stays true (left 0 is the centre of a 1920
box), so this defect proves the width half of the clause and not the centring half.

**The smoke's own historical defect had stopped reproducing, and the first control came back green.** The battery
was written on 23.10, when `.video-toggle{display:grid}` beat the browser's `[hidden]{display:none}` and the pause
button hung on screen, dead, before its script ever ran. The obvious control — put that exact rule back into the
copy — printed **clean copy 0 problems, defective copy 0 problems**. The reason is four days of progress: the
button's `hidden` attribute is now cleared by the script itself once the clip plays (`btn.hidden = false`), and
measured at 1280 and at 390 the attribute is simply gone by the time the battery looks (`hiddenAttr: False,
display: flex`). The class of defect is alive; its carrier is not. The defect moved to a node that stays hidden
until a human acts — the form's success message: `<style>.contact-ok{display:block}</style>` in the ru page.
Numbers: clean copy **2 runs, 0 problems**; defective copy **2 runs, 2 problems**, and each is a single clause,
`hidden attribute overridden by CSS: p#contact-ok.contact-ok`, on `ru/desktop` and `ru/mobile`; the other
fourteen clauses of each run stay green.

**Numbers.** Full runs on the real tree, before and after the rewrite: viewports-extra **94 / 0 in 96–98 s**
(mobile-tablet block, landscape, wide, Slow 3G, 404), smoke **18 runs / 0 problems** with both badge-degradation
scenarios (7 badges, all files cut: 7 hidden, 0 visible broken; one file cut: 1 hidden, 6 visible and loaded).
`landing-regress-all.py`: `CONTROLS` **30 → 32**, and `--controls --only viewports-extra,browser-smoke` gives
**2 of 32, both caught** (6.6 s and 39.8 s), with the scope printed so a partial run cannot be read as the whole
list. The ledger now reads **45 of 48** (12 `--mutate`, 32 `--control`, 1 `--selftest`), one pointer, **2 without
anything**.

**What this does not prove.** One defect per battery, on a subset of pages: the wide control breaks en and ru
only, so the other seven languages rest on the clean run alone, and the smoke control breaks one page in one
width pair, so its remaining fourteen clauses — title, one h1, `main#main`, the skip link, the FAQ count, the
form fields, the redirect field, the tagged link, the video poster, the alt texts, the text markers, the JS
errors, the image loads — are proven green, not proven able to see a fault. The two remaining batteries still
have no control: `landing-external-links.py` reads the live network outside this sweep, and
`landing-stop-rule.py` drives 13 live tasks against the bot's prompt. And the rewrite itself is the risk this
entry cannot rule out: the numbers above rest on the two clean runs recorded here, not on a clause-by-clause
comparison of old output and new.

**Files.** `landing-viewports-extra.py` (`--root`/`LANDING_PORT`, `run()`/`control()` split, `WRAP_JS`,
`HERO_COLS_JS`, `wide_measurements()`, `wide_reds()`, `wide_verdict()`, `strip_wrap_max()`, `control_tree()`),
`landing-browser-smoke.py` (rewritten from a top-level script into `sweep()`/`run()`/`control()` with `--root`,
`PAGE_JS` and `issues_for()` shared by both paths, `faq_count()`, `scroll_through()`, `badge_degradation()`),
`landing-regress-all.py` (`CONTROLS` 30 → 32), `SKILL.md` (ledger count, the controls count, and the lesson that a
historical defect can stop reproducing). Evidence in `evidence/block-20261027f/`: `clean-viewports.log`,
`clean-smoke.log`, `runner-controls.log`, `vpx-control.log`, `smoke-control.log`.

## Every battery in the set can finally be shown red, and the worst clause counted white as dark (27.10.2026)

**The last two batteries in the set that had never been red.** The ledger read 45 of 48 with a control, one
pointer, two with nothing: `landing-external-links.py` (the live network: 69 addresses, "ПРОБЛЕМНЫХ: 0") and
`landing-stop-rule.py` (the page's promise that the bot stops one step short of the answer: 13 live tasks against
the bot's prompt). The pointer was `landing-print-crossengine.py`, whose flag only handed the battery another
build. All three now have a defect they are obliged to catch, and the ledger reads **48 of 48, 0 pointers,
0 with nothing**.

**The network battery could not even be handed a different tree.** The root was a literal, so there was nowhere
to put a fault: the same lesson as the settings battery yesterday, one day later. It now takes `--root` (and the
environment variable), and `--mutate` builds a copy of the tree on hard links — no build file is touched, because
every edit goes through unlink-then-write — and repoints the first badge of two pages at a fake platform served
from the machine itself, on a port the operating system picks. The two fake pages are the two historical defects
of 25.10 reproduced literally rather than invented: one answers 200 with the title "Project Not Found" (a deleted
product page that still returns 200), the other answers 200 with "Discover Awesome Startups" and never mentions
the product (a badge pointing at the platform's front page). Numbers: the clean copy scans **69 addresses, 0
problems, 0 unverified**; the copy with the fault produces **exactly two problems** — `title: Project Not Found
[badge-page]` and `no [badge-page]` — and nothing else moved; the run prints both sets and exits 0 only when the
counts match. 68 s.

**The promise battery was cheap to break once the prompt was the parameter.** Three controls, none of which
touches the GPU: `--control rule` cuts the "не называй…" line out of the prompt for types 2 and 3 and expects
**18 of 18** clauses red (nine languages, two types) with the type-1 clauses untouched; `--control type1` slips
the same prohibition into the "explain the topic" prompt and expects **9 of 9**; `--control judge` replaces the
model with a canned body that names the answer and expects the battery to exit 1 — which proves the judging half,
the half that belongs to us. The contract half runs in 4.6 s. The live half still runs its 13 tasks, and on the
real tree it prints **0 named, 0 errors, 0 photos without the condition read**, 5.6–13.3 s per task.

**The second control found a blindness instead of confirming a clause.** `--control type1` came back green on its
first run. The clause searched for the lowercase «не называй», and a rule line written the way a person writes
one — «Не называй ответ…», capital letter — went straight past it, so a leak of the prohibition into the topic
explanation was invisible to the contract. Both clauses now compare without regard to case, and the same control
reddens 9 of 9. The lesson is older than this file: a check that reads words must read meaning, not spelling.

**The print battery's hardest clause counted white as dark.** "Текст тёмный" was one string comparison:
`bodyColor.startswith(('rgb(17, 17, 17)', 'rgb(2', 'rgb(0, 0, 0)'))`. The prefix `rgb(2` is satisfied by
`rgb(255, 255, 255)` exactly as well as by the site's `rgb(20, 32, 58)`, so white and near-white text were
recorded as dark, and the clause could not go red on the defect the whole print block exists for — white text on
a band whose dark background the browser does not print, i.e. white on white. The old behaviour is proved by a
four-line script kept with the evidence rather than argued. It is replaced by a number: every sampled text element
must reach WCAG contrast **4.5** against the **paper** — the body's background, because a browser prints no
backgrounds — plus a new clause that the paper itself is light (luminance 0.80). The control then cuts the two
`@media print` lines that give the dark bands a white background and dark text, and the copy reddens **exactly
four clauses** — contrast, en and ru, Firefox and WebKit — while reveal, skip link and header stay green. Clean
copy **20 checks / 0 failed**, live site **20 / 0**, control 29 s. The pointer is gone with it: this battery now
breaks something, so the ledger counts it like the rest.

**Numbers.** `landing-regress-all.py` `CONTROLS` 32 → 37;
`--controls --only external-links,stop-rule,print-crossengine` gives **5 of 37, all caught**, 68.0 + 4.6 + 4.6 +
4.6 + 28.9 s, and the scope is printed so a partial run cannot be read as the whole list. Full clean runs of the
three batteries on the real tree: external links 69 / 0 / 0 unverified; stop rule 13 tasks / 0 named / 0 errors;
print 20 / 0.

**What this does not prove.** The network control scans the whole address list twice, so a third-party outage
inside those two minutes can redden the clean copy for a reason that is not the mutation — the run prints the
offending address so the difference stays readable. The fake pages prove the badge clause, not the soft-404 clause
that guards product pages reached by a plain link. The judge control proves the judgement, not the model: a model
can still name the answer on a wording nobody tried, in a language the six text cases do not speak. The print
control cuts the band rules on all nine pages, but the battery reads only two of them, so the other seven rest on
the clean run alone.

**Files.** `landing-external-links.py` (`--root`, `scan()`, `control()`, the fake-platform handler, hard-link
clone, badge repointing), `landing-stop-rule.py` (`--bot-root`, `contract()` returning its failures,
case-insensitive rule test, `control_rule()`, `control_type1()`, the judge branch), `landing-print-crossengine.py`
(rewritten: `measure()`, colour parsing, WCAG luminance and contrast, a sample table behind `--report`,
`--base`/`--mutate`, `control()`), `landing-regress-all.py` (`CONTROLS` 32 → 37). The two previous versions of
the rewritten batteries are kept in the skills repository's own history. Evidence in `evidence/block-20261027g/`:
`clean-external-links.log`, `control-external-links.log`, `clean-stop-rule.log`, `control-stop-rule.log`,
`control-stop-type1.log`, `control-stop-judge.log`, `control-print.log`, `runner-controls.log`, and
`old-print-clause-blind.py` with its log.

## The whole set ran at once for the first time, and it caught a race no single battery could see (27.10.2026)

**Why a full run was the missing step.** The previous blocks proved, one battery at a time, that every one of the 48
could be made red (`landing-controls-ledger.py`: 48 of 48, 0 pointers). What no block had done is run the 48
together on the real tree. The last full journal was 26.10 and covered 31 batteries — three of its reds belonged to
the runner (a local server that was never started) — and the set has grown by seventeen batteries since. "Everything
is green" rested on the memory of separate runs, not on a run.

**What the run found.** 48 batteries, 5 616 s (1 h 34 min), 19 095 named checks in the journal, one red:
`landing-min-font.py`, `[firefox минимум 16 якорь 761 ru#pricing]` — «цель=84 низ шапки=78.6 зазор=5.4 высота
шапки=78.6», against a clause that demands 10 px of air.

**It was a race, not a number.** The same battery passed on 26.10 and passed a 55-check rerun immediately after the
failure; the next identical rerun failed with the same 5.4. A four-run probe with samples at load and 100, 300 and
700 ms after it showed the mechanism: at minimum font 16 on 761 px the Russian header wraps to two lines (78.6 px)
only after Manrope swaps in. The page's anchor script re-scrolled once, at the end of the body, when the header was
still single-line (63.6 px) — it placed the target at 63.6 + 20 ≈ 84, and the font swap then pushed the header's
bottom to 78.6, leaving 5.4 px, the exact number the script was written on 25.10 to remove. `fonts.ready` afterwards
corrected `scroll-padding-top` to 99 px but never moved the page: the probe caught `pad=99px` and `target=84` in the
same sample — the padding was right and the page was in the wrong place.

**The fix makes header height an event instead of an instant.** `ResizeObserver` on `.top`, plus `load` and
`fonts.ready`, re-settle the landing while the visitor has not touched the page; only explicit gestures count
(wheel, touchstart, keydown, mousedown), because the script's own `scrollTo` raises `scroll` and would otherwise
cancel the correction on its first tick. A `lastH` guard keeps the same height from being re-scrolled twice, and a
normal header (≤ 70 px) still clears the inline style, so the plain page stays CSS-only at 84 px.

**Numbers.** Probe: 16 samples of 16 now read 20.4 px (before: 2 of 4 runs at 5.4). `landing-min-font.py` full
1 554 checks / 0 twice in a row. The anchor control still reddens 6 of 9 with the script stripped — chromium 761
−51.8, chromium 320 (id#faq) −12.2, chromium 320 (uk#pricing) −11.8, firefox 320 (both anchors) −11.8, firefox 761
−52.2 — so the clause did not become the thing it was proving. `landing-deeplink.py` 684 / 0 (ordinary landing at
84 px untouched). After publishing: sweep 2 896 / 0, first screen 252 / 0, Core Web Vitals 69 / 0, and the live site
itself exercised rather than only compared — nine languages rendered 121 / 0, no third-party request 108 / 0, all
eleven addresses in the sitemap 200 (`evidence/block-20261027h/live.log`).

**What this does not prove.** One run is a snapshot of one machine at one hour: the timing-sensitive batteries
(CWV, video hang) may read differently on a loaded host, and the journal records that hour's paces, not a promise.
The anchor clause is measured at three width/language pairs; the other six languages rest on the script being
byte-identical across the nine pages, which the build check enforces. A visitor who scrolls before the font arrives
keeps the browser's landing by design — the correction never steals a scroll someone started.

**Files.** `index-src.html` (the anchor block), nine rebuilt pages and `sitemap.xml`; `evidence/block-20261027h/`
(`full-run.log`, `full-run.json`, `min-font-fix.log`, `post-fix.log`). Nothing in the battery changed: the page was
wrong.

## Six controls existed in the code, and no run had ever pulled them (27.10.2026)

**The ledger's number was true and its consequence was not.** `landing-controls-ledger.py` says 48 of 48 batteries
have a control wired, and that is exactly what it measures: a flag a reader can find in the source. The runner's
`CONTROLS` list is a different fact — 37 entries covering 33 distinct batteries — so fifteen batteries had a control
that no runner path had ever executed. This is the same shape the earlier blocks kept finding, one level up: a green
line that proves nothing about the battery, because nobody ever asked it to go red.

**Six of the fifteen were the layout and clipping family, and they came in two languages.** Four already spoke the
suite's convention (0 = caught): `a11y-extra --control` reddened 49 of 49 width measurements (74.8 s through the
runner), `backtab --control` 48 of 120 reverse-Tab clauses (232 s), `text-clip --control` 108 (52 s, three injected
defects), `tablet-menu --control` 27 of 162 (52 s, the list cut to 60 px). All four were clean in the 27.10 full run
(267 / 120 / 148 / 162 checks, 0 failed), so the red belongs to the defect and not to the tree.

**Two spoke the opposite code.** `deeplink --control` rewrote 108 pages and 324 lines and reddened 90 of 684 checks,
then exited 1 — the same code it uses for a broken page. `langlist-fit --mutate` reddened 112 of 3 591 and also
exited 1. The runner's rule is `code == 0` for "caught", so both would have printed `НЕ ПОЙМАЛ` at the exact moment
they caught their defect. That is not cosmetic: a control that shouts "broken" when it succeeds teaches the reader
to ignore it, and the next person to switch the flag on would have "fixed" the mutation. Both batteries now return 0
when the control catches and 1 when the page stays green — the branch every other battery in the set already had.

**A count, because a mutation that does not land is a green control.** `langlist-fit` applied three CSS replacements
in the served HTML and never said whether they landed; the handler now counts pages and lines and prints them (10
pages / 30 lines on the subset). `deeplink` already printed its rewrites (108 pages / 324 lines).

**Both slow ones enter the runner on a subset.** `deeplink` gained `LANDING_LANGS` (default still nine) and is listed
as `en,ru,hi`: 425 s on nine languages became 168 s through the runner, and the control still names the defect (252
checks, 30 red). `langlist-fit` is listed with `--lang ru --quick`: 491 s became 23 s (114 checks, 12 red). Clean runs
on the same subsets: 252 / 0 and 114 / 0 — the red is the mutation, not the subset.

**The ledger now counts both facts.** Its second column asks whether the runner pulls the control at all, so the
blind spot that produced this block cannot come back silently: 48 batteries, 48 wired, 39 pulled by the runner in 43
entries, **9 outside the list** — and those nine are named in the output, not implied.

**Numbers.** `CONTROLS` 37 → 43 entries (33 → 39 distinct batteries).
`--controls --only a11y-extra,backtab,text-clip,tablet-menu,deeplink,langlist-fit` → **6 of 43 caught in 603 s**
(75 / 233 / 52 / 52 / 168 / 23 s), every one by its own defect; the six clean runs behind them are the 27.10 full-run
journal plus the two subset runs above.

**What this does not prove.** That the other nine batteries' controls catch: the print family (`print`, `print-main`,
`print-pages`, `print-paper`, `print-contrast`), `min-font`, `nu-validate`, `video-failure` and `video-hang` all still
end with `1 if problems else 0`, so registering them today would print `НЕ ПОЙМАЛ` at the moment they succeed — the
same defect fixed here twice, in nine more places. That all 43 controls pass in one command: the full control pass has
never been run end to end; every entry rests on a subset run, and a subset is not the whole. That one mutation per
battery exercises every clause: `a11y-extra`'s control touches the width clause only, and its 49 red of 49 are width
measurements out of 267 checks. And that a caught control makes the clause worth having: it makes the clause able to
fail, which is a smaller claim and the one the word "control" actually means.

**Files.** `landing-regress-all.py` (`CONTROLS` 37 → 43, with the counts and the two exit-code repairs in comments),
`landing-deeplink.py` (`import os`, `LANDING_LANGS`, control exit branch), `landing-langlist-fit.py` (`pages`/`hits`
counters in the serve handler, the `КОНТРОЛЬ:` line, control exit branch), `landing-controls-ledger.py` (runner
column: `runner_module()`, `runner_entries()`, `--json` fields). Evidence in `evidence/block-20261027i/`:
`ctrl-textclip.log`, `ctrl-tabletmenu.log`, `ctrl-deeplink.log` (the full nine-language control before the fix: 684
checks, 90 red, exit 1), `ctrl-deeplink-subset.log`, `clean-deeplink-subset.log`, `ctrl-langlist.log` (3 591 checks,
112 red, exit 1), `ctrl-langlist-subset.log`, `clean-langlist-subset.log`, `ledger.txt`, `ledger.json`,
`runner-controls-six.log`.

## Nine controls could not say "caught", and one mutation had stopped touching the page (27.10.2026)

**The debt was written down by the previous entry, not discovered here.** That block closed by naming nine
batteries that still ended with `1 if problems else 0` — the code they use for a broken page. The runner reads
`code == 0` as caught, so adding any of them to `CONTROLS` would have printed `НЕ ПОЙМАЛ` at the exact moment it
caught its defect: the same repair two batteries had received hours earlier, unapplied in nine more places. Six of
them ended with the wrong code; two carried a pointer where a mutation should be; the ninth had a self-test that
never touches a page. And one of the six hid a second fault: a mutation that no longer touched anything.

**`video-failure` and `video-hang` pointed at the tree they were written on.** Both carried `--control`, and it ran
`git -C ROOT archive HEAD` — today's HEAD. On the commit where each battery was written that clone was the pre-fix
tree and the defect was real; every commit since moved HEAD further from it, and today the control clones the fixed
tree and is green by construction. The ledger counted both as wired, because it reads a flag in the source — the
same distance the last block named between "wired" and "pulled". Both now build the defect itself on a hard-link
copy of the working tree and print what landed: the source-event listener removed (**9 pages / 9 lines**), the
watchdog threshold moved from 8 s to 600 s (**9 pages / 9 lines**). A mutation that lands on nothing exits 1 and
says `КОНТРОЛЬ НЕ СОБРАЛСЯ`, instead of passing as a catch.

**One mutation had quietly stopped touching the page.** `landing-print-paper.py --mutate railwidth` returned
**969 checks, 0 failed** — the clean numbers to the check — and exited 1. The 25.10 fix that capped the printed
column at 210 mm also, unnoticed, made that mutation harmless: the rail of screenshots never grew wider than the
column containing it, so removing the rail's own cap changed nothing at all. The mutation reproduced a defect that
could no longer exist, and nothing in the battery asked whether the break had landed. Repaired to reproduce the
state before 25.10 (both caps off), it reddens **24 of 993**. Its sibling `--mutate colwidth` was still alive:
**7 of 966**.

**A docstring that quoted yesterday's budgets.** `print-main`'s control note promised reds on ru/uk/id. The 25.10
decision gave id and uk an accepted budget of eight sheets, so only ru — budget seven — can redden; the mutation
now adds a sheet to ru and the two clauses about the footer fail there: `ru: листов не больше бюджета (7) — 8
листов` and `ru: подвал не напечатан отдельным листом — 196 знаков при подвале 180`. The note says so now instead
of promising three.

**Numbers.** Ten controls, each run through the runner:

| battery | mutation | checks | red | wall |
|---|---|---|---|---|
| `landing-print.py` | `--mutate strip` | 147 | 111 | 23.7 s |
| `landing-print-main.py` | `--mutate footerpad` | 216 | 2 | 25.5 s |
| `landing-print-pages.py` | `--mutate` | 386 | 22 | 14.8 s |
| `landing-print-paper.py` | `--mutate railwidth` (both caps) | 993 | 24 | 74.8 s |
| `landing-print-paper.py` | `--mutate colwidth` | 966 | 7 | 73.3 s |
| `landing-print-contrast.py` | `--mutate` | 3 408 | 138 | 72.1 s |
| `landing-min-font.py` | `--control-anchor` | 9 | 6 | 10.3 s |
| `landing-nu-validate.py` | `--selftest` | 2 fixtures | 1 broken / 0 clean | 3.5 s |
| `landing-video-failure.py` | `--control` on S2 | 56 | 32 | 97.2 s |
| `landing-video-hang.py` | `--control` on S1 | 56 | 21 | 87.4 s |

`--controls --only <nine names>` gives **10 of 53 caught, 0 missed, 482.8 s**. `CONTROLS` 43 → 53 entries,
39 → 48 batteries; the ledger now reads 48 batteries, 48 wired, **48 pulled by the runner in 53 entries, 0 outside
the list** — the nine named as outside yesterday are inside today.

**What the reds are measured against.** The clean run of each battery on the real tree, from the 27.10 full-run
journal unless noted: `print` 0 problems; `print-main` 213 / 0 (`ru` prints seven sheets, the mutation adds an
eighth with 196 characters against a 180-character footer);
`print-pages` 391 / 0; `print-paper` 969 / 0; `print-contrast` 3 543 / 0; `min-font` 1 554 / 0 twice after the
anchor race was fixed; `video-failure` 228 / 0 over 40 runs; `video-hang` 144 / 0 over 21. The two video subsets were
also run clean today, in the same hour as their controls: **56 / 0 each**, against 56 / 32 and 56 / 21 with the
mutation — same clauses, same subset, same machine, so the red is the break and not the narrowing.

**What this does not prove.** `nu-validate`'s control proves the classifier — a broken fixture becomes a finding, a
clean one stays silent — and says nothing about the walk over eleven pages: a page that moved out of `PAGES` would
be a battery checking ten pages and printing 0. The video controls run one scenario each (S2 for the failure
battery, S1 for the hang); every other scenario in both plans rests on the clean run alone. `print-main`'s mutation
reddens only ru, because id and uk carry an accepted budget of eight sheets; the two clauses are proven able to
fail, not proven to watch all nine languages. `print-paper`'s `colwidth` reddens item 7 (line length) only — items
1, 3, 4 and 5 have no control of their own. And the 53 entries have still never run in one command: every entry rests on a subset, and
a subset is not the whole. A caught control makes a clause able to fail; it does not make the clause worth having.

**Files.** `landing-print.py`, `landing-print-main.py`, `landing-print-pages.py`, `landing-print-paper.py`,
`landing-print-contrast.py`, `landing-min-font.py` (control exit branch: 0 = caught, 1 = page stayed green),
`landing-video-failure.py` (`_clone`, `_strip_source_listener`, `LANDING_ONLY`, mutation counter, control exit
branch), `landing-video-hang.py` (`_clone`, `_silence_watchdog`, mutation counter, control exit branch),
`landing-print-paper.py` (railwidth mutation rebuilt to the pre-25.10 state), `landing-print-main.py` (control note),
`landing-nu-validate.py` (final `КОНТРОЛЬ:` line so the runner's summary shows a sentence, not `}`),
`landing-regress-all.py` (`CONTROLS` 43 → 53, the two paper mutations as separate entries, the subset environment
for both video batteries). Evidence in `evidence/block-20261027j/`: `ctrl-print.log`, `ctrl-print-main.log`,
`ctrl-print-pages.log`, `ctrl-print-paper.log` (the blind 969 / 0, exit 1), `ctrl-print-paper-railwidth2.log`,
`ctrl-print-paper-colwidth.log`, `ctrl-print-contrast.log`, `ctrl-min-font.log`, `ctrl-video-failure.log`,
`ctrl-video-hang.log`, `ctrl-runner-nine.log`, `ledger.txt`.

## The whole list ran in one block, and the sentence about one command was retired (27.10.2026)

**The debt was a sentence.** The entry above closed with: *the 53 entries have still never run in one
command: every entry rests on a subset, and a subset is not the whole.* This block ran all 53, in
13 commands of one to nine entries, and then counted the coverage instead of remembering it.

**What ran.** 16 logs in `evidence/block-20261027k/`, **53 of 53 entries covered, 53 caught at least
once, 0 blind, 3 785 s of runs**. An entry is the pair (battery, its arguments) — the runner counts
53 because four batteries carry more than one mutation: `first-screen` (fold, wide), `visual-pass`
(control-wide, mutate), `stop-rule` (rule, type1, judge) and `print-paper` (railwidth, colwidth).
The heaviest: `header-engines` 278.3 s, `video-motion` 260.6 s, `backtab` 234.0 s,
`video-weight` 180.2 s, `deeplink` 171.3 s, `cwv` 153.1 s, `badge-rows` 127.5 s; ten entries stand
past 90 s and twenty-one past a minute; the lightest, `page-lang`, 0.1 s.

**Why the one-command criterion was retired instead of scheduled.** Every entry already runs as its
own subprocess with its own server on its own port, so a single process over all 53 would prove one
thing the coverage tool does not: that the runner's loop resolves the names in `CONTROLS`. That is
exactly what `landing-controls-coverage.py` checks, and it checks it against the source of truth —
it imports `CONTROLS` from the runner rather than keeping a copy, and matches each pair against the
`ПОЙМАЛ / НЕ ПОЙМАЛ` lines of the block's logs. The complaint inside that sentence was the other
half — *every entry rests on a subset* — and no monolith touches it: a mutation targets the pages and
languages it was written for. Scheduling an hour of machine time to close the cosmetic half while
the substantive one stayed open would have been the same trade as a 70 MB shell around a native
app. So the tool is the answer, and the limit is named below instead of chased.

**The two kinds of evidence, side by side.** A control proves a clause can fail on its own subset.
The clean run of the whole battery proves the clause passes on the whole. Neither substitutes for the
other, and both are dated today: the set of 48 batteries ran 09:36, one red —
`min-font` in Firefox at 761 px, the anchor landing 5.4 px below the sticky header's air; fixed 09:52,
green at 09:56 twice, and re-run in this block: **1 554 checks, 0 failed**.

**Two defects the pass found in the tools' own words.** Six batteries printed `CONTROL_FAILED: N` in
the branch that means the control *caught* the defect — `backtab`, `landscape-page`, `rotate`,
`tablet-menu`, `tablet-page`, `text-clip`. A log line that says "failed" at the moment of success is
the same liar as a ledger column that says "wired" for a control nobody pulls; the runner reads the
last line, so the verdict printed next to a catch read as its opposite. All six now print one
sentence — `КОНТРОЛЬ: подмена встала — покраснело N, время T s` — and `tablet-menu`, which printed no
evidence path at all in control mode, prints it. Second: `deeplink` wrote today's control into
`deeplink-control-20261025.json`, because the date was typed into the file name instead of stamped;
Monday's file and today's were the same name.

**One red belonged to me, not to the page.** `cwv` ran twice at once — a batch in the background and
a re-run in the foreground — and both bind one port: the batch died in 0.2 s with a red, the re-run
alone took 153.1 s and caught (69/69 clean, 67/69 broken). Two runs of one battery on one port is not
a page defect but it looks exactly like one in a log, which is why the coverage tool carries a third
state, *disputed*, and refuses to call such an entry covered until the reason is named. Here it is.

**Regression after the fixes.** All seven touched batteries re-run through the runner: `backtab`
234.0 s, `deeplink` 171.3 s, `landscape-page` 95.4 s, `rotate` 59.4 s, `tablet-menu` 53.8 s,
`tablet-page` 20.3 s, `text-clip` 52.7 s — 7 of 7 caught, with the new sentence and today's evidence
names (`deeplink-control-20261027T143222.json`).

**What this does not prove.** A control reddens its own subset, not nine languages. A caught control
makes a clause able to fail; it does not make the clause worth having — `print-paper`'s railwidth
lesson, unchanged. Coverage proves each entry ran once and caught once, not that the mutation
reproduces the right defect. And the disputed `cwv` is one caught run, not two.

**Files.** `landing-backtab.py`, `landing-landscape-page.py`, `landing-rotate.py`,
`landing-tablet-menu.py`, `landing-tablet-page.py`, `landing-text-clip.py` (the `CONTROL_FAILED`
line; tablet-menu also gains the evidence path in control mode), `landing-deeplink.py` (stamped
evidence name, `import time`), `landing-controls-coverage.py` (new: coverage from source `CONTROLS`
against a block's logs, `--dir`, `--json`, exit 1 on a missing or blind entry),
`landing-regress-all.py` (`SKIP` entry for the new tool, so the suite stays 48 batteries).
Evidence in `evidence/block-20261027k/`: 16 `ctrl-*.log`, `coverage.json`.

## The batteries read eleven pages and eight languages; both controls wrote to one (27.10.2026)

**The queue was one sentence of the last entry.** *A control reddens its own subset, not nine
languages.* Two batteries were the plainest case of it, because the number of pages is the whole
claim: `landing-en-leftovers.py` reads the English page and all eight language pages, and
`landing-links-audit.py` reads eleven — nine pages plus `privacy` and `terms`. Their first controls
wrote to one page each: the leftover control put the untranslated sentence into EN and `ru` and
asked only that *some* finding appear (`hits >= 2`), and all four link defects were planted in
`index.html`. A page silently dropped from either walk stayed green, and nothing in the suite would
have said so.

**The second hole was measured before it was fixed.** Nine pages share one template, and each
yields exactly **142 text nodes**. A page reduced to its header and footer — the shape of an
unbuilt or half-built language page — yields **29**, and the old battery reported **0 problems** on
it: "no English leftovers" is true of a page that has almost no text. So the walk needed a floor as
much as it needed breadth. The floor is **85 % of the English page's nodes (120 of 142)** — measured
on today's markup, not guessed, and low enough that a translation may legitimately differ.

**What changed.** `landing-en-leftovers.py` now reports two clauses per language, `CHECKS: 16`:
the page was read (node floor) and it carries no English leftover. `--mutate` (also `--mutate all`)
writes the marker into all **nine** pages and requires a finding in **each of the eight languages**,
exactly one per language, none on EN, and a clean copy at zero — it caught with
`['es','hi','id','pt','ru','tr','uk','vi']` named one by one. `--mutate stub` cuts `<main>` out of
`vi` and requires that language named as cut (29 nodes against the 120 floor) with the other eight
green. `landing-links-audit.py` now opens with a clause the old one did not have: the page list is
compared with **the disk** (`pages_on_disk()` — root, every two-letter language directory that has
an `index.html`, `privacy`, `terms`), so a page that exists and is missing from `PAGES` is a finding
with its own name instead of silence; `CHECKS: 12`. Its `--mutate` puts the four defects on **four
different pages** — `index.html`, `ru/index.html`, `vi/index.html`, `privacy.html` — and each finding
must carry the name of the page it was planted in; `--mutate orphan` creates `xx/index.html` and
requires the battery to call it unaudited.

**The runs.** Four controls through the runner, **4 of 55 entries, 4 caught, 1.6 s**:
`--mutate` 0.2 s, `--mutate stub` 0.3 s, `--mutate` 0.7 s, `--mutate orphan` 0.4 s. Clean runs after
the edits: `en-leftovers` **16 checks, 0 failed**, `links-audit` **12 checks, 0 failed** — both
through the runner, not only by hand (`evidence/block-20261027l/`).

**What this does not prove.** That the other 53 entries mutate as many pages as they read: this block
measured two, and the rest need the same measurement, not a grep. That four of eleven pages is
eleven — the spread proves the walk reaches a language page and a legal page, not that it reaches
every one. That the 85 % floor is right for markup that does not yet exist; it is a ratio measured
on nine pages that are identical by construction, and a future page with a different template would
have to be measured again. And that a link or a language page is *correct*: the walk can now be
shown to reach each page, and reaching is not judging.

**Files.** `landing-en-leftovers.py` (two clauses per language, `MIN_NODES_RATIO`, `--mutate
[all|stub]`), `landing-links-audit.py` (`pages_on_disk()`, the unaudited-page clause, four defects
on four pages, `--mutate [defects|orphan]`), `landing-regress-all.py` (two new pairs, 53 → 55
entries). Evidence in `evidence/block-20261027l/`: four clean logs (by hand and through the
runner), four control logs, one runner pair log.

## Every control was counted; nobody had watched what it writes (27.10.2026)

**The queue was one sentence again.** *The other 53 entries need the same measurement, not a grep.*
Two blocks had repaired two controls that wrote to one page while their battery read nine or eleven,
and both times the proof was a hand reading of `mutate()`. `shutil.copy2` looks identical in a control
that breaks one page and one that breaks nine, so the code cannot answer the question. This block
answers it by watching the file system while each control runs.

**The instrument.** `landing-open-trace.py` runs a battery under an audit hook on `open`, wraps
`Path.write_text`, `write_bytes` and `shutil.copyfile/copy2/copy` to hash the content *after* each
write, and patches `SimpleHTTPRequestHandler.translate_path` to record every page the battery's own
server hands to the browser. The hash is compared with the live page: a copy of the tree writes the
same bytes and stays "copy", a defect writes other bytes and is named. `landing-control-breadth.py`
runs the entries from `CONTROLS` one at a time — same entry, same arguments, same environment — and
prints, for each: pages changed, pages read, pages walked but not touched.

**The instrument lied four times, and each lie was caught by a known answer.** A `Path` passed to
`io.open` arrives in the audit event as an object, and an `isinstance(path, str)` guard silently
dropped *every* mutation write while reads (which are strings) passed: `en-leftovers --mutate` reported
0 changed pages of 9. `shutil.rmtree` in Python 3.12 deletes through `dir_fd`, so the removal event
carries a bare file name with no directory — the "hash it just before deletion" plan measured nothing.
The early hasher fires *before* the write, so a half-copied page looked changed: `en-leftovers --mutate
stub` reported **6** changed pages where the defect was **1**. And a child `python3 tools/build.py`
writes pages in another process with no wrappers: `site-move-test --control` rebuilds twelve pages and
read as **0**. All four are fixed; the last one is why the same battery now shows 12 of 12.

**What the fifty-five entries say.** 12 controls change at least every page their battery reads;
10 change fewer (clause proof on a subset); 23 change no page at all because the defect lives in the
browser (`page.evaluate`, `add_style_tag`) or in the source (`site.json`, the bot's price); 9 show
neither a served page nor a written file (bot batteries, `file://` walks, a self-test of a classifier);
1 — `landing-pixel-density --control` — was not measured: its copy is deleted before the hash lands.

**One hole was real.** `landing-page-lang.py` reads nine language pages and broke a single label on
`ru`. A page dropped from its list of nine stayed green, and the control could not say so. It now breaks
one label on **each** of the nine pages and requires a finding per language: `ПОЙМАЛ … по 1–1 находки
на язык`, 0.1 s. The instrument confirms 9 changed of 9 walked, where an hour earlier it measured 1.

**The other nine subsets are named.** `axe` breaks one image on one page, `glyphs` one heading,
`fonts` and `video-weight` only `ru`, `cwv` only `ru` of nine, `external-links` two of eleven,
`links-audit` four of twelve — every one of them is documented in the runner as "the control proves the
clause, the clean run proves the coverage". The measurement turns that sentence into a number and, in
one case, corrects it: `landing-return --control` is described as an en+ru subset, and the instrument
shows it writes **nine** pages — the subset is what it *measures*, not what it breaks.

**What this does not prove.** That a page missing from a battery's list is caught: the walk is only
visible where the battery served or read a page, so a page it never asks for is invisible unless a
control writes it. That "0 pages changed" means harmless: 23 entries break the page in the browser,
which no file hash can see. That the nine unobserved entries are green for the right reason. And that
the numbers are the same on a rerun: 8 of the 55 took longer than two minutes, the two video controls
alone took 443 s, and the whole measurement of the set took 58.6 minutes of wall clock.

**Files.** `landing-open-trace.py` (new: audit hook, write wrappers, child `sitecustomize`,
`translate_path` patch), `landing-control-breadth.py` (new: entry runner, page mapping by path, copy
vs defect by hash, verdicts), `landing-page-lang.py` (mutation on all nine pages, one finding per
language), `landing-regress-all.py` (both tools in `SKIP`, the page-lang comment rewritten; still
48 batteries / 55 entries). Evidence in `evidence/block-20261027m/`: `breadth.json`, `breadth.txt`,
`breadth-final.txt` (grouped), `breadth.log`; the three re-measured entries in `block-20261027m2/`.

## The one unmeasured control was writing a file no hook was watching (27.10.2026)

The first breadth measurement left exactly one entry without a verdict: `landing-pixel-density.py
--control`, filed as "its copy is deleted before the hash lands". That diagnosis was wrong, and the
wrongness was in the instrument, not the control: the control breaks the hero poster
(`img/demo-poster-ru.webp`) — it writes a **picture** — and `landing-open-trace.py` accepted audit
events for `.html` only. Nothing was deleted before anything; the hook was simply not looking.

**Four things had to change in one instrument, and each was a defect on its own.**

The trace now accepts the site's own files as well as pages (webp/png/jpg/svg/mp4/webm/woff2/css/js/
xml/txt/json) and asks the tree which pages reference the changed file — by file name in the markup,
and for fonts through the `<style>` block, because a font is pulled by CSS and appears in no page.
The hash now waits for the write to finish: the audit event fires **before** the bytes land, so an
instant hash hashes emptiness — that is why `PIL.Image.save` had been "always changed" even on a copy.
Both hashes are now summed instead of the last one winning: `os.remove` hashes the **old** file before
deleting it (`p.unlink()` in the control), and the write hashes the new one; keeping only "final"
dropped precisely the hash that *is* the defect. And paths that `shutil.rmtree` reports as bare names
(Python 3.12 deletes through `dir_fd`) are dropped instead of being glued onto the tracer's cwd —
`…/scripts/llms.txt` has nothing to do with the site.

**Measured.** `landing-pixel-density --control` is a **subset**: 1 changed page (`ru`) of 2 read,
through the file `img/demo-poster-ru.webp` — named, not "unmeasured". A second entry moved without
being touched: `landing-poster-frames --control swap` used to be filed as "not observed" (it writes no
page) and is now "changed (reading not visible)": two files, `img/demo-poster.webp` and
`img/demo-poster-ru.webp`, which is exactly what swapping frames means.

**The other 54 verdicts were re-measured, not carried over.** They had been taken by an instrument
that could not see a single file, and a set of numbers gathered by two different instruments is not a
set of numbers. The full pass is 55 entries, **52.1 minutes** of wall clock, all exit code 0, one
instrument (`f37e2dacff66`): **12 full, 11 subsets, 23 break the page in the browser, 8 not observed,
1 changed out of view, and 0 without a verdict** (was 1). The hour is survivable by construction now:
the journal (`breadth.json`) is written after **every** entry and `--resume` takes what is already
there — learned the hard way when a 420-second tool cap killed the second chunk at entry 4, and the
eight finished entries came back instead of being re-run.

**The number stopped living in a paragraph.** It is `tools/control-breadth.json`: 55 records, each
carrying the verdict, the changed pages, the file it went through, the `sha` of the battery it
measured and the `sha` of the instrument that measured it; the header carries the `sha` of the whole
`CONTROLS` list. `landing-control-breadth-ledger.py` is the gate over it and answers five questions
separately — every entry of the list measured; measured by the same battery code; measured by the same
instrument; no record left without a verdict; the list unchanged since — because "the list matched"
and "the code is the same" are different facts and must not share one green. The sweep carries the
five as five checks (**2901 checks** now, was 2896).

**Both answers were shown.** The gate is green on the real registry; on four fakes it is red and names
the entry: a record deleted (`нет замера: landing-en-leftovers.py --mutate`), a foreign code hash
(`deadbeef0000 ≠ 9c8d870e65c8`), an old instrument, a record whose verdict is "not measured". The
sweep itself was made red by swapping in the incomplete registry — `FAIL [global] breadth: у каждой
записи списка контроля есть замер | нет замера: …`, exit 1 — and went green again after the file was
restored byte for byte (`cmp` silent).

**What this does not prove.** That a page a battery never asks for is caught: the reading side is
visible only where the battery served or read a page, and 23 entries break the page in the browser
where no file hash can reach. That the 8 "not observed" entries are green for the right reason. That
the asset→page map is complete: it matches by file name in the markup, so a file referenced only from
JavaScript would be reported as an orphan instead of a page. And that a rerun gives the same numbers —
timing batteries (cwv, video-weight, external-links, 75–181 s each) will vary.

**Files.** `landing-open-trace.py` (asset suffixes, `_sha_stable`, summed hashes, cwd-noise guard),
`landing-control-breadth.py` (asset→page mapping, per-entry instrument, journal after every entry,
`--resume`, `--write-registry`), `landing-control-breadth-ledger.py` (new: the five-question gate),
`landing-sweep.py` (five checks), `tools/control-breadth.json` (new: 55 records). Evidence in
`evidence/breadth-remeasure-20261027/` (`breadth.json` journal, `chunk2.log`, `chunk3.log`) and
`evidence/block-20261027n/` (sweep green, sweep red on the incomplete registry, final green).

## The price was exact, and all nine languages called it «about» (27.10.2026)

`120 Stars / 5 = 24`. `300 / 15 = 20`. Both numbers are exact, and the page hedged both:
«Около 24 звёзд за разбор — выгода 20%», «About 24 Stars per breakdown — save 20%» — and the same
hedge, translated, in the other seven dictionaries (`Unos`, `Cerca de`, `Sekitar`, `yaklaşık`,
`Khoảng`, `Приблизно`, `लगभग`). It was the only place on the page where a fact the site *knows* was
written as an estimate, and it sat on the money screen, where a hedge reads as «we are not sure what
you get» next to a savings percentage the page states exactly.

**Found by reading, not by a gate.** The sweep has always compared the *numbers* in those two lines
with `tools/prices.json` (`_num_in` for the per-unit price and the discount), so 24 and 20 were
correct — the doubt was in the words around them, which no check looked at.

**Fixed in nine dictionaries and in the template's own English fallback** (`index-src.html` carries
the English text inline; the build refuses a dictionary that disagrees with it). Then rebuilt, re-stamped
the launch kit and published.

**Both halves were shown red before green.** The first sweep after the dictionary edit was red for two
reasons, and both were real: `шаблон: встроенный английский == en.json | p2d: шаблон 'About 24 …' !=
словарь '24 …'`, and `kit: входы не новее манифеста | перерисовать: src/locales/en.json` — the kit's
four cards are drawn from `en.json`, and their manifest records its sha, so a text edit that is not
followed by a redraw is exactly the «текст поправили, картинку нет» the gate exists to catch. After the
template fallback, the rebuild and `tools/submission-kit.py` (4 cards redrawn, 10 inputs matched) the
same sweep is **2901 / 0**. The publication check was red until `tools/publish-branch.sh` ran, and green
after it. The live pages now carry «24 Stars per breakdown», «24 звезды за разбор», «24 Stars por
desglose» … and a search for every one of the nine hedge words returns nothing on any of the nine live
addresses (`curl | grep -c`).

**What it does not prove.** That 24 and 20 are the right prices — these come from `tools/prices.json`,
and equality with the bot's own numbers is `landing-price-parity.py`'s job, which this change did not
touch. That the discount sentences read well in languages nobody on this machine speaks: they were
edited by removing one word, not re-translated, and a native reader is still the only judge of 「20%
बचत」.

**Files.** `src/locales/*.json` (9 files, two lines each), `index-src.html` (inline English fallback),
the 9 rebuilt pages and their `.md` twins, `submission-kit/manifest.json` (re-stamp), `tools/lastmod.json`.
Evidence in `evidence/block-20261027o/` (`sweep.log` red, `sweep2.log` green, `price-m-ru.png`,
`price-m-tr.png`, `price-m-vi.png`, `price-d-*.png`).

## Two questions about text size that ended in no change (27.10.2026)

The reader's own text settings were never asked about: every battery measured the page at 16 px with
a browser that renders what the CSS says. Two probes, both read-only, both thrown away after answering.

**Does the page follow the reader's base font size?** Set `html{font-size}` to 150 % and 200 % at
390 px and measured every page: no horizontal scroll, nothing clipped, all nine languages clean. Then
measured whether that answer means anything — `h1` stayed at 30 px and body text at 16 px at 150 % and
at 200 %, because the type scale is in px, not rem. So the clean result is honest but narrow: the page
is *immune* to the root font size rather than *responsive* to it. Rewriting the scale in rem would move
every geometry the batteries assert (44 px targets, the 59 px sticky bar, the hero order, section
margins) for a reader who is already served by page zoom, which `landing-a11y-extra.py` measures at
640×512 — the real 200 % case. Left alone, recorded here.

**Does the page survive a forced minimum font size?** That is the setting that grows text *without*
reflow, the one a px-locked page cannot absorb. Firefox was launched with `font.minimum-size.x-western
= 20`: the smallest text on the page was still 13 px, i.e. the preference never reached the page in this
harness. A probe that cannot move the thing it measures is blind, and adding it to the sweep would have
added a green that can never be red — the exact failure the last twenty blocks were spent removing. Not
added. The detector itself was proven on planted defects (a 90 px nowrap word, a 40 px three-line box, a
600 px block), so the blindness is the harness's, not the checker's.

**Files.** Nothing in the tree changed. The three probes and their controls were scratch files kept
outside the repository (pruned after 24 h); the numbers above are from `evidence/block-20261027o/`.

## The set ran whole for the first time in a day, and a run that lost three batteries read as complete (27.10.2026)

The behaviour set had not been run end to end since 26.10: each block ran four to six batteries,
and «everything is green» rested on the memory of the previous blocks. The last journal before
today had one battery in it, from 15:17. So the set ran whole: **49 batteries, 19 104 checks, 0
red, 94.8 minutes** (`--per 900`), journal `evidence/block-20261027p/full.json`. The slowest were
`landing-langlist-fit.py` (490 s, 3 591 checks), `landing-tablet-page.py` (429 s, 1 804),
`landing-cross-engine.py` (427 s), `landing-header-engines.py` (424 s, 973) and
`landing-print-contrast.py` (71 s, 3 543). Nine live batteries — the published site, the mailbox,
the bot and the end-to-end letter — were not run: they are out of the set by design and each has
its own conditions.

**The count was not the whole answer.** A journal is a list of rows, and `--report` counted rows:
`батарей: 46 | красных: 0`, exit 0. Measured, not supposed: the same code taken from
`git show HEAD` and pointed at a copy of today's journal with its first three batteries deleted
printed exactly that line and exited 0 — an incomplete run was indistinguishable from a complete
one, and the missing three were visible only to someone who remembered there should be 49.

**Fix.** `report()` now computes the set the run itself uses (every `landing-*.py` minus `SKIP`)
and reds on missing, extra and duplicate rows, naming them. The same doctored journal after the
fix: exit 1, `НЕ ХВАТАЕТ (3): landing-a11y-extra.py, landing-axe-audit.py, landing-backtab.py`.
The end-of-run summary counts the same way (`батарей: N из 49`), so a run cut short by its budget
is red instead of quietly short.

**New gate `landing-set-parity.py`.** Three static questions about the SKIP literal, read from
the source and not from the set object (a set hides what a reader needs): every skipped name
exists as a file; every skipped name carries a reason of at least four characters and not a dash;
no name appears twice, because `{'a','a'}` collapses silently. `--journal` does not reimplement
the completeness rule — it asks the runner and prints the runner's verdict, one rule in one place.
Five negative controls — ghost, noreason, dupes, drop, extra — all five caught in 0.37 s; with no
journal at hand the drop and extra controls synthesize one from the set, so a control never waits
for evidence to exist.

**The control that broke the instrument.** The first run of the five controls copied the scripts
directory by symlink — the runner among them — and wrote the mutated copy through that link, so
three junk entries landed in the real `SKIP`. Caught by running the thing (the next control died
with `SameFileError`), the runner was restored from its source list, and the gate no longer links
the runner: it writes a real copy and unlinks any link first. A control that can damage the tool
is worse than no control, so the failure is written down rather than quietly fixed.

**In the sweep.** Two checks (2 901 → 2 903): the composition, and «the gate catches five planted
defects». Proven red by planting `landing-ghost-battery.py` into the real `SKIP`:
`FAIL [global] набор: у каждой отложенной батареи есть файл, причина и нет повторов |
skip-files: нет файла: landing-ghost-battery.py`; removed, green again.

**What this does not prove.** That the batteries are the right ones: the gate proves every file
is accounted for, not that the account is worth having. And that a battery's green means what its
name says — that is the controls list, a separate question with its own counter.

**Files.** `landing-regress-all.py` (set comparison in `report()` and in the run summary, one new
`SKIP` line for the gate), `landing-set-parity.py` (new; 17 skipped names now), `landing-sweep.py`
(+2 checks). Evidence: `evidence/block-20261027p/` — the journal, the «before» code taken from
git, both reports, the gate and its five controls.

## The gate never said it was a gate, and the set counted it as a battery (27.10.2026)

The composition gate from the previous block asks three questions about the `SKIP` literal: every
skipped name exists as a file, every one carries a reason, no name appears twice. All three were
green, and all three looked in one direction only — at what had been *left out*. Nothing asked
whether what had been left *in* was really a battery. So when the control-breadth gate
(`landing-control-breadth-ledger.py`) landed in the same directory as the batteries and was never
declared in `SKIP`, the set simply grew: **49 batteries**, and the full run of 27.10 executed the
gate as the 49th, at 0.1 s with no `CHECKS` line in the journal. The counter was honest about the
symptom and unreadable about the cause: `батарей в наборе: 49 | с контролем: 48 | без контроля: 1`
— which reads like one page battery with no proof at all, not like an instrument parked in the
wrong list.

**Fix, two parts.** The gate is declared where gates belong, in `SKIP` with its reason — the set is
48 again, and 18 names are skipped for stated reasons. And the composition gate now asks the
question that was missing: *is everything left in the set actually a battery?* It does not
re-implement the rule; `landing-controls-ledger.py` already knows what counts as a control (a flag
wired in code, not a word in a docstring), so the gate asks it with `--json` and judges only the
numbers: every battery in the set has a control, and every control is pulled by a run. On the live
tree before the fix, the answer came back red and named the file:
`FAIL control | в наборе без контроля (гейт? объяви в SKIP с причиной): landing-control-breadth-ledger.py`.

**The instrument answered about the wrong directory.** Both new controls — `undeclared` (the
gate's `SKIP` line removed in a copy) and `unpulled` (a `CONTROLS` entry renamed, so a battery keeps
its control in code but no run pulls it) — reported `НЕ ПОЙМАЛ` on the first run. The reason was not
the mutation: in a copy of the tree the counter is a symlink, `__file__.resolve()` follows it into
the **real** directory, and the gate received a truthful answer about the live tree instead of the
copy. The counter now takes `--scripts DIR` and echoes the directory it answered about; the gate
compares that echo with the directory it asked about and fails loudly on a mismatch
(`счётчик ответил про другой каталог`). This is the same class as the earlier control that wrote
through a symlink: a copy is not a copy until the instrument agrees it is.

**After.** `--mutate all`: 7 of 7 caught, each exactly on the `control` clause —
`undeclared → в наборе без контроля … landing-control-breadth-ledger.py`,
`unpulled → контроль не тянет ни один прогон: landing-a11y-extra.py`. The gate on the live tree:
`набор: 48 батарей | отложено: 18 | вопросов: 0`. The counter: `48 | с контролем: 48 | без
контроля: 0`, every control pulled. The breadth gate still reads 55 records with the same
instrument. The sweep: **2 903 → 2 904 checks, 0 red** — one check for the new question, and the
mutation check now demands seven catches instead of five (timeout raised to 240 s for the seven).

**What this does not prove.** That 48 is the right number. A live battery parked in `SKIP` with a
plausible reason still passes: the gate proves every file is either run or explained, not that the
explanation is right. And it does not prove a battery measures what its name says — that is the
control list, a separate question with its own counter.

**Left open, measured.** In the same journal, **13 of 49 rows** are green with `checks: null`:
twelve batteries print their own summary line (`ИТОГО: 9 проверок…`, `ALL PASS`) instead of
`CHECKS: n, FAILED: m`, so the journal's 19 104 checks is a sum over the rows that happen to speak
one format. A battery whose count silently dropped from 40 to 1 is indistinguishable from one whose
count was never printed — the next block's question, named here with the number rather than
remembered.

**Files.** `landing-regress-all.py` (one `SKIP` line), `landing-set-parity.py` (fourth question,
instrument-identity check, two new controls), `landing-controls-ledger.py` (`--scripts`, the
answered directory in `--json`), `landing-sweep.py` (+1 check, 5 → 7 catches). Evidence:
`evidence/block-20261027q/` — the gate red on the live defect, the counter before the fix, the
sweep after it.

## Thirteen rows were green with no number, and the sum was a sum of the talkative (27.10.2026)

The previous block ended with a measured sentence: **13 of 49 rows** in the full-run journal were
green with `checks: null`, so the headline figure "19 104 checks" was a sum over the rows that
happened to speak one format. This block closed that sentence, and it turned out to describe two
different defects.

**The first one was in the reader, not in the writers.** `landing-first-screen.py` printed
`CHECKS: 252, PROBLEMS: 0` and `landing-print.py` printed `CHECKS: 147, PROBLEMS: …` — both had a
real count. The runner's regex demanded `FAILED:` immediately after `CHECKS:`, so it discarded
numbers it was looking straight at. A second vocabulary is not a synonym; it is a blind spot with
good manners. Of the thirteen mute rows, one was not a battery at all but the control-breadth gate
parked in the set (fixed in block q); the other twelve were batteries, and every one of them was
measuring something.

**The contract is now one line, and it is the same line everywhere** — `CHECKS: n, FAILED: m`.
The twelve counts, each in that battery's own unit:

```
browser-smoke 18 | cross-engine 60 | external-links 69 | first-screen 252 | nu-validate 12
page-lang 71 | poster-frames 9 | price-parity 9 | print 147 | render-check 37
stop-rule 13 | visual-pass 306
```

The regex accepts `FAILED` or `PROBLEMS` (old wording still parses, so a battery nobody has
touched yet is not silently mute), and the part that matters: **a green row without a count is
red**. `--report` prints `без счёта: N`, names the batteries and exits 1 — thirteen rows that used
to read as "0 problems" now read as what they were, an empty cell. The runner also takes `--only`
as a comma list: one block edited twelve batteries, and twelve runner invocations is twelve manual
commands.

**The second defect is the one a format cannot fix.** A count can fall silently: a battery whose
walk lost eight of nine languages prints an honest `CHECKS: 1, FAILED: 0` — small, tidy, green. The
only way to tell that from "forty, all clean" is a memory of the last time. That memory is now a
file. `landing-counts.json` holds 48 records of `{checks, taken}`, each on the battery's own scale,
and `landing-count-ledger.py` judges four separate clauses: no count · not in the ledger · ledger
entry with no row in the journal (a renamed battery leaves a ghost) · count fell. Controls `--mutate
all`: 4 of 4, each red on its own clause and named. `--stamp` raises the record; lowering it needs
`--lower`, because quiet narrowing is exactly what the file exists to forbid. The runner calls the
gate at the end of **every full run** — one rule, one place, as with the composition gate —
while `--only` runs are exempt: a partial journal must not be judged against a complete ledger.

**After, measured.** A journal stitched from the 36 rows of the 22:06 full run and the 12 rows
re-run after the fix (`evidence/block-20261027r/merged.json`; `merge.py` states the stitch, so
nobody later mistakes it for one run): **48 of 48 rows, 20 107 checks, 0 red, 0 uncounted** — up
from 19 104 over 36 rows, because twelve batteries had been measuring all along and their numbers
were being dropped on the floor. Set composition, all five questions: `набор: 48 батарей |
отложено: 19 | вопросов: 0`, with `журнал: батарей: 48 из 48 | проверок: 20 107 | красных: 0 | без
счёта: 0`. Count ledger on the same journal: green. Control breadth: 55 of 55, same instrument
`f37e2dacff66`. Sweep: **2 905 checks, 0 red** — one new check, that the ledger's four clauses can
be broken at all.

**A silent 18 → 1 was caught, not argued.** On a copy with one count lowered to 1:
`FAIL счёт упал: landing-browser-smoke.py — было 18, стало 1`, gate exit 1; and `--stamp` on the
same copy refuses — `ОТКАЗ … уменьшение только с --lower`.

**The cost nobody budgets for.** Editing a battery invalidates its control-breadth record, because
the record pins the battery's sha. The sweep reddened at once on 14 records of the ten batteries
touched here: `breadth: замер снят тем же кодом батарей | landing-browser-smoke.py --control
(d4576830314d ≠ 483ccbd61dab)`. Fixing it meant re-measuring exactly those 16 entries — ten minutes,
not the 52 of the whole list — and merging them into `tools/control-breadth.json` without touching
the other 39 (`merge-breadth.py`, which warns if a verdict or a walk changed; none did, verdicts
identical, times within 0.3 s). Rule for the skill: change a battery's code, re-measure its breadth
entry.

**What this does not prove.** That the number means "how much of the site was checked". It does
not: the units differ per battery — a run, a page, a poster, a task — and 20 107 is a sum of unlike
things. The ledger guards each battery against its own past, not a common denominator, and
comparing two batteries by count is meaningless.

**Left open, named.** (1) A common denominator (pages × languages × clauses) would make the sum
mean something; today it only guards against shrinkage. (2) The gate trusts `--stamp`: a battery
that shrinks and is stamped with `--lower` on purpose is a decision, and the file records the
decision, never the reason for it.

**Files.** Twelve batteries (`browser-smoke`, `cross-engine`, `external-links`, `first-screen`,
`nu-validate`, `page-lang`, `poster-frames`, `price-parity`, `print`, `render-check`, `stop-rule`,
`visual-pass`), `landing-regress-all.py` (regex, `mute_rows`, comma `--only`, ledger call, journal
written even when the budget ends before the first battery, one `SKIP` line),
`landing-count-ledger.py` (new), `landing-counts.json` (new, 48 records),
`landing-sweep.py` (+1 check), `tools/control-breadth.json` (16 entries re-measured). Evidence:
`evidence/block-20261027r/` — merged journal, ledger before and after, the caught 18 → 1, the four
controls, sweep log; `evidence/breadth-r-20261027/`.

## The page every lost visitor saw was the one no walk was reading (28.10.2026)

Block r ended with two named questions. This block took the first — *a common denominator would make
the sum mean something* — and it turned out not to be a bookkeeping question at all.

**Why a denominator is the wrong shape.** 20 107 checks cannot be divided into anything, because the
units differ by construction: a run, a page, a poster, a task. Dividing a sum of unlike things by a
number does not make it a measurement; it makes it a quotient with a decimal point. What the site
actually has is a **surface**: twelve pages. The useful question is not "how many checks per page"
but "is there a page that no instrument reads" — and that question has an answer that can be
observed instead of argued: break the page and see whether anybody shouts.

**The defect was in the list, twice.** `landing-links-audit.py` began its walk by comparing `PAGES`
with `pages_on_disk()` — a good idea from the previous day, except that `pages_on_disk()` was a
*second copy* of the same list (`index.html`, `privacy.html`, `terms.html`) with the language
directories appended. The copy and the original agreed with each other and both forgot
`404.html`: the page every lost visitor is shown, carrying fourteen absolute links, one image and a
`?start=src_landing_404` deeplink. It was on disk, it was served, it was published — and no link walk
ever opened it.

**The same shape, one layer down.** All twelve pages carry absolute self-links (`<base>/es/`,
`<base>/privacy.html`) — 137 of them — because they must work from any depth. Every offline battery
treats `https://…` as external and skips it; the one battery that does check absolute addresses
(`landing-external-links.py`) walks the eleven content pages and not the 404. So a renamed or
deleted page would have left up to fourteen dead links on the busiest page of the site, and the set
would have stayed green: nothing was wrong with the checks, nothing was reading.

**The measurement, before and after.** `landing-page-canary.py` breaks each page four ways
(relative dead target, missing same-page anchor, duplicate id, absolute self-link to a missing
directory) — but only with the classes the page's own markup can carry, and it requires the catcher
to name **that** page and **that** class. Run against the battery as it stood at `HEAD` (the file was
taken out of git, not retyped), it measured **33 of 48 cells caught, 12 misses, and `404.html` with
zero catches**: every one of the twelve self-link cells was blind. After the fix: **45 caught of 45
applicable, 0 misses, 3 not applicable** — `404.html` has no relative href, no anchor and no id, and
that is now printed with a reason instead of counting as a pass.

**What changed in the instrument.** (1) `pages_on_disk()` enumerates the disk — every `*.html` in the
root except the build template, named once in `NOT_A_PAGE`, plus every two-letter directory with its
own page — so a new page appears in the parity check by itself instead of needing a second list to be
remembered. (2) `404.html` is in `PAGES`, and the t.me deeplink `src_landing_404` now shows up in the
audit output as evidence that it is really read. (3) A sixth clause: absolute self-links must resolve
to a file or a directory-with-page **in the tree**; the base comes from `sitemap.xml` (the common
prefix of `<loc>`) and not from `tools/site.json`, because the control's copy has no `tools/`. No
sitemap — the line prints `САМОССЫЛКИ: НЕ ИЗМЕРЕНО` and the count drops by twelve, so blindness
cannot look like a pass. (4) The control gained a fifth defect on a fifth page: an absolute self-link
of `404.html` pointed at a missing directory, which must produce exactly one finding naming
`404.html`. All five caught, on five different pages.

**The gate, five clauses.** `landing-page-canary-ledger.py` compares `tools/page-canary.json` with
the disk and with the catcher's sha: *pages* (a new page must be canaried), *code* (an edited catcher
stales the measurement), *caught* (every page has a catch), *missed* (no applicable cell and no page
"not in the list"), *empty* (every page has something to break). Control `--mutate`: 5 of 5, each
defect reddens exactly its own clause and no other.

**After, measured.** Sweep **2 910 checks, 0 red** — five of them new, one per gate clause. Page
canary: 12 pages, 48 cells, 45 caught, 0 missed, 3 not applicable, `catcher_sha f3005edc8def`.
Set composition: `набор: 48 батарей | отложено: 21 | вопросов: 0` — the two new files are gates and
declare themselves in `SKIP` with a reason, which the composition check now accepts without a
question. `landing-links-audit.py` alone in the runner: `checks=25 failed=0` (was 12: twelve pages,
each counted twice, plus the disk parity), and its record in `landing-counts.json` stamped 12 → 25.
Its two breadth entries re-measured and merged (`--mutate` now changes **5** pages instead of 4,
reads 12), 53 records untouched.

**The journal is stitched, and it says so.** The whole set was started and not finished in this block
(an hour and a half of machine time, stopped at two rows when the block's window ran out). The file
the count gate reads is therefore 47 rows of the 27.10 full run plus today's `links-audit` row, joined
by `merge-journal.py` — **48 of 48 rows, 20 120 checks (was 20 107), 0 red, 0 without a number**. The
same rule as block r: a stitch is allowed when it is stated, never when it is discovered later.

**The price nobody budgets for, again.** Editing one battery staled both of its breadth records and
the sweep reddened on them by sha — the same cost block r discovered for twelve batteries. Re-measuring
two entries took three minutes; the rule stands: change a battery's code, re-measure its breadth entry.

**What this does not prove.** That the site is covered, only that it is *reached*: one catcher, four
markup classes. A page could still be invisible to a visual or accessibility class while being caught
on links, and the matrix says nothing about the quality of what is asserted once the page is read.
The 404's membership in the visible-instrument set is proved for links only. And forty-seven of the
journal's forty-eight rows are a day old: only the battery that changed was re-run here.

**Left open, named.** (1) The same canary with chromium catchers — overflow, contrast, first screen —
so each page has to be caught by a visual class too, not only by a markup one. (2) Block r's second
question is untouched: the count ledger still trusts `--stamp` and records the decision without the
reason for it.

**Files.** `landing-links-audit.py` (PAGES + `404.html`, disk enumeration, `NOT_A_PAGE`, the
self-link clause, `САМОССЫЛКИ` line, five-defect control), `landing-page-canary.py` (new),
`landing-page-canary-ledger.py` (new, five clauses, `--mutate` 5/5), `landing-sweep.py` (+5 checks),
`landing-regress-all.py` (two gates in `SKIP` with reasons), `landing-counts.json` (links-audit 25),
`tools/page-canary.json` (new ledger), `tools/control-breadth.json` (2 entries re-measured).

## The measure could break markup, and layout had no witness of its own (28.10.2026)

Block 28 closed with a named question — *the same canary with chromium catchers: overflow, contrast,
first screen, so each page is caught by a visual class too*. This block took the first of the three.

**What was actually missing, said precisely.** Not a name in a list: that was checked before anything
was built and it was complete — 44 browser batteries open the site, `privacy.html` is named by 12 of
them, `terms.html` by 11, `404.html` by 8, and no page is named by none
(`evidence/block-20261028b/who-reads-which-page.txt`). Not a width either: `a11y-extra` reflows all
eleven pages at 320 px, which is narrower than the phone the owner carries. What was missing was a
measurement that can be *asked per page*: the canary could break markup on any page and demand a name
for it, and could not break a layout at all.

**The class and its catcher.** `landing-page-overflow.py` (new): pages taken from the disk by the same
rule as the canary, so a new page measures itself; three widths — 360 (a cheap Android), 420 (the
owner's phone), 1280 (a laptop); one clause per page, `documentElement.scrollWidth − clientWidth`,
compared with `clientWidth` and **not** `innerWidth` (mobile emulation widens the layout viewport when
the document overflows, and the old manner stays silent on a page twice the phone's width); the three
worst offenders printed by tag, class and pixels. Clean tree: **36 checks, 0 red**. Control
`--control wide` — 120 px added to the live document, applied to every page:
**36 of 36 red, 12 of 12 pages named**, and the line says the substitution was proved, not assumed.

**The canary learned a second kind of catcher.** `CLASSES` gained `overflow`; `CATCHER_BY_CLASS` maps a
class to its catcher as a table rather than an `if`; a browser catcher gets `LANDING_ROOT` and a
`--page` hint, so one experiment costs three page loads instead of thirty-six. The findings parser now
strips indentation before the `- ` prefix — browser batteries print `  - page: …`, and without that
every finding would have read as empty. Full measurement: **12 pages, 60 cells, 57 caught, 0 missed,
3 not applicable** (the 404 has no relative href, no anchor and no id; it is caught on `self-link-dead`
and on `overflow`).

**What the run caught in itself.** (1) `--class overflow` wrote the registry — a partial run erasing
the four markup classes from `tools/page-canary.json` while looking like a successful measurement. Now
only a full run writes it, and the rule is written in the script where the next person will read it.
(2) The gate had five clauses and would have stayed green after the new battery's code changed, because
it compared one catcher's sha. A sixth clause `code_all` compares **every** catcher in the registry;
control `--mutate` is **6 of 6**, each defect reddening exactly its own clause.

**The price was the same price, and it was charged again.** Adding the new control to the runner's
`CONTROLS` list staled the breadth registry twice at once: no measurement for the new row, and the
list's sha no longer matched. The sweep said so honestly — **2911 checks, 2 red**. Re-measuring the
row cost 18 s and its verdict is `вне страниц`, which is the truth: this control changes no file, it
widens the document at runtime. The registry was then merged with its other 55 rows untouched and the
header recomputed with the runner's own list (`landing-control-breadth.backup-20261028T015722.json`
kept). Sweep after: **2911 checks, 0 red**.

**What this does not prove.** That the assertion is good: the canary now knows the page's overflow is
*named*, not that the widths, the threshold or the offender list are the right ones. And two classes
still have no experience behind them — `contrast` and `first-screen`.

**Files.** `landing-page-overflow.py` (new), `landing-page-canary.py` (class table, per-class catcher,
partial runs do not write), `landing-page-canary-ledger.py` (sixth clause + control 6/6),
`landing-sweep.py` (+1 check), `landing-regress-all.py` (control row), `tools/page-canary.json`
(60 cells, `catchers`), `tools/control-breadth.json` (56 rows), `references/page-canary.md`.

## The audit said zero about the two thirds of the page it had never read (28.10.2026)

**The number behind the zero.** `landing-axe-audit.py` has printed «0 violations» since 16.10, and on
28.10 the page was asked how much text that number covered. At 420 px axe read **36 of the 125
elements that carry their own text**; at 1280 it read 40 of 129. The reveal blocks
(`html.js .rv{opacity:0}`) keep everything below the first screen invisible until the observer runs,
and axe does not measure the contrast of what it cannot see. A grey paragraph on a grey band below
the fold would have been green for as long as it existed.

**The battery.** `landing-page-contrast.py`: 12 pages × 2 viewports (phone 420, desk 1280) = 24
checks. It reveals the blocks for the measurement only (no file is written), then runs axe's
`color-contrast`. Checked elements: **103 on the index at 420, 107 at 1280** (was 36 and 40), 90 on
privacy, 76 on terms, 18 on 404 — **0 violations**.

**What axe refuses, and what was done instead of «I don't know».** 18 cells per viewport come back
`incomplete`: 11 say the background is a gradient (the tariff card, the parents band, the referral
band), 3 that the element is overlapped (captions under the screenshots, the message field), 4 that
the text is shorter than two characters (step numbers). The battery computes the first two itself
and conservatively: the background is taken from the gradient's own colour stops (the worse end
wins), overlap is ignored as decorative, and the nearest opaque colour is used under the text. Text
shorter than two characters and text filled by a gradient (`background-clip:text`) stay «not
measured» **with a named reason**; any other refusal is a finding, not silence.

**The control.** `--control dim` repaints the text light grey (about 1.5:1) in the live page and must
redden all twelve pages: **12 of 12 caught, 1894 findings**. It also proves the battery's own
arithmetic — the gradient cells are reported at 1.41:1 `[gradient]`, a number axe never produced.

**The class.** The page canary gained a sixth class, `contrast`: a paragraph with `color:#f8f9fb` on
white (1.04:1) is written before `</body>`, and the catcher must name **that** page. Full measure:
**12 pages, 72 cells, 69 caught, 0 missed, 3 not applicable** (the 404 has no relative href, no
anchor and no `id`; it is caught on `self-link-dead`, `overflow` and `contrast`). `--stub` still
turns every applicable cell red, and the gate's `code_all` now compares **six** catchers; its
control is still 6 of 6.

**The floor.** Every page has a floor of checked elements (index 100, privacy 85, terms 70, 404 16);
below it the battery reddens, because «0 violations» over ten elements is the appearance of a
measurement. The sweep gained one check: every page on disk either has its own floor or matches the
language-page rule, so a new root page cannot pass with ten checked elements (2911 → **2912 checks,
0 red**).

**The price.** The new battery joins the run (49 → 50 batteries) and gets a `CONTROLS` row, so the
breadth registry needed a re-measure: 22 s, verdict `вне страниц` — the control changes no file, it
repaints text in the browser. The registry was merged with its other 56 rows untouched; backup
`evidence/control-breadth.backup-20261028T030556.json`.

**What this does not prove.** That the floors are the right numbers, or that the conservative
gradient arithmetic is exact: it can find a defect on a gradient, not clear one. And one class still
has no experience behind it — `first-screen`.

**Files.** `landing-page-contrast.py` (new), `landing-page-canary.py` (sixth class, per-class
catcher), `landing-sweep.py` (+1 check), `landing-regress-all.py` (control row),
`tools/page-canary.json` (72 cells, 6 catchers), `tools/control-breadth.json` (57 rows),
`references/page-canary.md`.

## The one class without a witness was the one a visitor sees first (28.10.2026)

**The gap.** The page canary asked each class of breakage to be named by *that* page, and six classes
answered. The seventh, `first-screen`, had no catcher at all. Three batteries did touch the first
screen — `landing-first-screen.py` (fourteen phone screens in nine languages),
`landing-browser-smoke.py` (the first frame), `landing-viewports-extra.py` (a tablet title, a
landscape pair, a wide-screen layout) — but every one of them prints a finding named by the screen
and the language, `land-844x390/ru`, and the measurement is built on the page's name. A finding that
does not name the page is not a catch, so the class sat there with nothing behind it.

**The catcher.** `landing-page-fold.py` takes the page list from the disk with the same rule the
measurement uses (root plus two-letter directories), so the legal pages and `404.html` — which no
language-driven battery opens — are in it, and it measures two windows per page: a phone at 420×844
and a laptop at 1280×800. The laptop window is new, and so is the pair it asks about: the wide
screens that existed (768×1024, 844×390, 1920×1080, in `landing-viewports-extra.py`) checked a title,
a hero pair for three languages, or a wide-layout rule — never the title-and-button pair on all
twelve pages. Two clauses per window: the `h1` exists, is *visible* (opacity multiplied down the
ancestor chain ≥ 0.9, not `display:none`, not `visibility:hidden`) and lies wholly within the first
screen; and the primary action — the first `a.btn` — is in the same place, visibly. `privacy.html`
and `terms.html` have no button: they are measured on one clause, and the table prints «—» where the
button would be, so the absence is neither a check nor a failure. 44 clauses, 12 pages.

**Two controls, one per clause.** `--control fold` writes `html{padding-top:100vh}`: the content moves
down exactly one screen, and the finding must be about the fold. `--control blank` writes
`main, main *{opacity:0}`: the content stays where it is and becomes invisible, and the finding must
be about visibility. Both named **12 of 12** pages, and each control fails if the other clause's red
appears — a mutation that broke both would prove neither. The height is `vh` and not a pixel count,
because the canary's break has to be the same experience on a 844-px phone and an 800-px laptop.

**The class.** A `100vh` block is written at the start of `body` — a banner or an overlay eating the
first screen, which is what a real ad slot does — and the catcher must name that page. Full measure:
**12 pages, 84 cells, 81 caught, 0 missed, 3 not applicable** (the 404 is caught on `self-link-dead`,
`overflow`, `contrast` and `first-screen`). `--stub` still turns every applicable cell red; the gate
compares **seven** catchers' shas; its own control still catches 6 of 6 parts, one at a time.

**What this does not prove.** That the first screen is *filled*: two clauses are two clauses. Whether
a sticky panel covers the title is `landing-backtab.py`, how much the hero weighs is
`landing-video-weight.py`, whether the text is readable is `contrast`. And the clauses read what the
markup offers first — the first `h1` and the first `a.btn`: put a button in the header above the hero
and the green would be an answer about the header.

**No new sweep check, and one number left for the next full run.** The sweep stays at **2912 checks,
0 red**: a page on disk that the measure forgets already reddens the `pages` clause, and a second
list of pages would be the second copy this project has paid for twice. The set grew 50 → **51
batteries**, the control list 57 → **59** rows, and the two new rows were re-measured on the breadth
instrument (23 s each, verdict `вне страниц` — the controls change no file, they repaint the page),
then merged with the other 57 untouched (backup
`evidence/control-breadth.backup-20261028T041717.json`). The battery's own 44 checks enter
`landing-counts.json` with the next whole run, by design: the registry records runs, not batteries,
and its gate will ask for the stamp by name.

**Files.** `landing-page-fold.py` (new), `landing-page-canary.py` (seventh class, per-class catcher),
`landing-regress-all.py` (two control rows), `tools/page-canary.json` (84 cells, 7 catchers),
`tools/control-breadth.json` (59 rows), `references/page-canary.md`.

## The set held fifty-one batteries, and the last whole run held forty-eight (28.10.2026)

**The gap.** Three blocks in a row added batteries — `landing-page-overflow.py`,
`landing-page-contrast.py`, `landing-page-fold.py` — and each was proven the same way: its own
control turned it red, and the page canary asked it to name every page. What none of the three had
done was run *inside the set*. The last whole run (03:29 the same night) finished with 48 rows and
said so: `батарей: 48 из 51 | НЕ ХВАТАЕТ (3)`, and `--report` returned 1. The gap was nameable only
because the report counts composition since 27.10; before that rule, the same journal would have
printed «48 batteries, 0 red» and read as a whole run. Three green batteries measured on their own
are three facts about three files; a set that has never carried them is a set whose composition is
a memory.

**The run.** One command, no subsets: **51 batteries, 20,224 checks, 0 red, 0 mute, 5,679.5 s
(94.7 min)**, budget 7,200 s not reached, no `SKIPPED-BUDGET` row. The three new batteries carried
their own numbers into it — `overflow` 36, `contrast` 24, `fold` 44 — and the total rose from
20,120 (48 batteries, 03:29) to 20,224, which is exactly those 104 checks and nothing else. Every
row printed the one line the journal reads, so no green cell is a green cell without a number.

**The registry refused the run, and that was the point.** The runner calls
`landing-count-ledger.py` at the end of every whole run. It answered: *«FAIL нет в реестре:
landing-page-contrast.py (проверял 24) — внеси через --stamp»* and the same for `fold` (44) and
`overflow` (36), `CHECKS: 51, FAILED: 3`, exit code 1 — with all fifty-one rows green. A run is not
allowed to widen the registry by itself: the registry is the record of what was *watched* falling,
not of what happened to print a number once. `--stamp` named the three entries (`taken 2026-10-28`),
the registry went 48 → **51 entries**, the sum stayed 20,224, and the gate went green:
`страниц в журнале: 51 | со счётом: 51 | проверок: 20224`, `CHECKS: 51, FAILED: 0`.

**What a whole run proves that separate runs cannot.** Joints. On 27.10 the first whole run in a
day found a race that no single battery could see: two batteries in the same process, one port.
Today's run found none — and «none» is a measurement of a *set*, not a compliment to a page. It
also fixes the arithmetic the earlier journal could only promise: the same battery measured in
isolation and inside the set gives the same number (36 / 24 / 44), so the set does not bend what it
measures.

**What it does not prove.** Nothing about the live site: the live batteries (bytes, assets, runtime,
third-party, form delivery, the bot) are `SKIP` by design and were not run. Nothing about the sum
either: 20,224 adds runs, pages, posters and clauses on nine different scales, and the registry
guards each battery's own count falling — comparing batteries by their numbers is comparing
kilometres to litres. And one clean run is one sample: the 27.10 race was invisible in four separate
green batteries and visible in one run of the set, so «0 red today» is a fact about today's tree,
not a promise about the next edit.

**Files.** `evidence/block-20261028d/full-run.log` and `full-run.json` (51 rows, 20,224 checks,
5,679.5 s), `scripts/landing-counts.json` (51 entries, three added by `--stamp`). No page was
changed: this block measured the instrument, and the instrument is the only thing that moved.

## Nine batteries watched the live side, and not one could say when it last looked (28.10.2026)

The offline set answers questions about the tree: 51 batteries, 20,224 checks, every one of them
shown red at least once. Nothing in it opens the published site as a visitor, reads the mailbox,
or asks the bot what its screens say. That is nine batteries, and they sit outside the set by
design — each has its own conditions (a real Chrome for the letter, a free or deliberately loaded
GPU for the answer time, a token for the mailbox). The price of «by design» was that their history
lived in the prose of this journal: no record of when each one last ran, no witness that a week had
gone by without one, and nowhere for a red live run to stay red. The entry above named exactly
this as the one thing the set does not touch.

**First run through one runner.** One runner (`landing-live-run.py`) reads a register (`tools/live-runs.json`)
and runs whatever the register leaves runnable: six batteries, 1 minute 41 seconds, all green —
bytes 26 files / 0 bad (2.3 s), assets 90 / 0 (12.4 s), runtime 121 checks / 0 (26.5 s), third-party
108 / 0 (51.8 s), inbox 11 / 0 (2.9 s), bot money 9 languages / 0 (4.7 s). Journal
`evidence/live-20261028T071521/journal.json`, one log per battery beside it.

Three did not run, and the register says so in words instead of silence: the answer time (last
measured 23.10 — 6 tasks in a free queue, 4 under a load of two, p90 41.5 s against the ceiling of
120), the live letter and its delivery confirmation (22.10 19:15:34 — 11 checks, stamp and address
matched, the letter found in the mailbox). Those two entries were seeded from their own records,
and each names the file it came from: a memory whose source is unnamed is a guess with a date.

**The register** (`tools/live-runs.json`) records per battery what it needs, how often it must be
measured, what unit it counts, the floor below which a count means narrowed coverage — and `last`.
`last` is written by the runner alone, from a real run, and only for a green row that printed a
number. A green row without a number is red (`НЕМОЙ`), the same rule the offline set learned when
thirteen rows were green with `checks: null`.

**The gate** (`landing-live-ledger.py`) asks nine questions and prints a table of what it knows:
composition both ways against the runner's own `SKIP` (a name in the register with no file, a live
battery in `SKIP` that nobody registered, a registered battery that is still inside the offline
set), the required fields, a reason for a battery that is conditioned forever, «measured at least
once», freshness against `every_days`, the outcome of the last run, and the count against its floor.
Its first run was red for six batteries — «never measured» — and that red was the truth: a register
is only as good as the runs behind it. After today's run it is 9 / 0, and the table prints each
battery's age in days, its count, its floor and its norm.

**Proven red.** Nine controls, each damaging a copy of the register and demanding that the rule
responsible for it (and no other) goes red: `stale`, `red`, `uncover`, `ghost`, `outside`, `drop`,
`nofield`, `silent`, `noreason` — 9 of 9 caught. And the idea was tested from outside the
gate: the register was made to say that one battery was measured 57 days ago, the sweep went red
naming it — `FAIL [global] живая сторона: реестр замеров вне набора полон, свеж и зелёный |
свежесть: … landing-live-bytes.py: последний замер 57 дн. назад при норме 3` — and back green when
the file was restored. A date that can be moved in a file is a date the gate actually reads.

**In the sweep.** Two checks (2,912 → 2,914): the register's verdict, and «the judge catches nine
planted defects». Sweep now 2,914 / 0.

**A rule that reads prose caught itself.** The gate decides which batteries are live from the
reason text in the runner's `SKIP` (the word «живой»). The end-to-end letter's reason read
«--live отправляет настоящее письмо» — no «живой» — so the one battery that sends a real letter
would have been invisible to the composition rule, and the rule would have reported «все живые в
реестре» about eight of nine. The comment now reads «живой прогон формы: --live шлёт настоящее
письмо». A detection rule that reads prose is only as good as the prose; that is now written down
rather than assumed.

**What this does not prove.** That green today means green tomorrow — the register stores an age,
not a guarantee. That the intervals are measurements rather than choices: 3 days for the site
batteries, 1 for the mailbox, 14 for the letter, 30 for the answer time are what a block can do,
not what the promise needs. That the letter path works: it was not exercised today, and the
register carries 22.10. That the answer-time ceiling holds under a loaded queue: last measured
23.10. And nothing about the batteries' own meaning — that a battery named «third-party» really
counts foreign hosts is its own controls' business, not the register's.

**Files.** `tools/live-runs.json` (new; 9 entries, 6 stamped by today's run), `landing-live-run.py`
(new; runner, in `SKIP` as an instrument), `landing-live-ledger.py` (new; gate, in `SKIP`),
`landing-regress-all.py` (two `SKIP` lines, one reason word), `landing-sweep.py` (+2 checks).
Evidence: `evidence/block-20261028e/` (gate, its nine controls, the red proof of the sweep, the
set-parity answer) and `evidence/live-20261028T071521/` (the live journal).

## The two live batteries that answer a real person could only be run by hand (28.10.2026)

Block e gave the live side a register and a judge, and left three entries with `run: false`:
the real letter, the proof of its delivery, and the generations on the GPU. That was honest —
each needs a condition a background run cannot promise — but it had a price nobody had priced:
the register could say *why* a battery stood still, and could not say *with what* it would move.

**The word that was never supplied.** `landing-contact-delivery.py` takes `--stamp "…"`, and
that timestamp is born in the neighbouring run: `landing-contact-e2e.py --live` prints it after
it has sent the letter. In the register the argument was written as `{{STAMP}}`, and the runner
had no flag to fill it — so the argv would have carried the literal braces into the process, and
the battery would have gone red for a reason that belonged to the caller. Two real batteries,
the only ones that touch a living person's path, were runnable in exactly one way: by a human
copying a line out of a terminal. That is the same defect the live group was built to end, one
layer down.

**What the runner learned.** `--cond` includes the conditioned entries; `--set КЛЮЧ=ЗНАЧЕНИЕ`
supplies what only the neighbouring step knows; a placeholder that survives substitution is
printed in words (`нечем заполнить {{STAMP}} — нужен --set STAMP=…`) and goes into `skipped`,
never into the green rows. A new `capture_re` in the register lets the runner *keep* what a
battery printed for the next one — the e2e's stamp is captured, printed on the row, and written
into the journal (`captures`), so the chain "letter → proof of delivery" is two commands instead
of a copy-paste. And the note a stamped record carries now names the journal it came from: with
`--out` the old note pointed at a directory that did not exist, which is a date without a source.

**The path, exercised today, through the runner.** `--cond --only contact-e2e --stamp`:
13 checks, 0 failed, stamp `2026-10-28 08:07:45`, register row written from a real run. Then
`--cond --only delivery --set STAMP="2026-10-28 08:07:45" --stamp`: the letter was found in the
mailbox 1 minute old, the stamp in its body and the test address in its `email` field — 1 letter,
0 failed. An earlier pass of the same chain (stamp `08:02:19`, evidence `block-20261028f/chain-*`)
confirmed the same thing before the code knew how to record it. Nothing here is a simulation:
the letter went through Web3Forms from the published page in a real Chrome on `:9223`.

**The gate's tenth question.** A conditioned entry may not be a battery nobody can start. Rule
`runnable`: every placeholder left in the argv of a `run: false` entry must be declared in the
entry's `placeholders` with a word saying where the value comes from — and a declared placeholder
that the argv does not use is a promise with nothing behind it, also a failure. Control `nofill`
removes the declaration from the delivery record and demands that exactly this rule reddens:
10 controls, 10 caught, one guilt each.

**The red nobody was asking about.** While checking the new rule, the count gate was run plainly
— and it was red: 51 batteries in `landing-counts.json`, 48 rows in the journal, and three
batteries (`page-contrast`, `page-fold`, `page-overflow`) unconfirmed by any run. Not a battery
failure: today's measurement printed exactly the recorded numbers (24 / 44 / 36). The journal was
older than the last register entry, because a full set takes an hour and a half and these three
were edited and measured one at a time afterwards. The sweep had stayed green throughout, and
that is the finding: it proved the gate's four controls could redden, and never asked the gate
about today. A gate nobody asks about the present is a report about the past.

**Both closed.** The three rows were measured (`--only … --append`, 20 s / 20 s / 14 s, 104
checks, 0 red) and stitched into the journal, which is stated rather than discovered: 48 → 51
rows, 20 120 → 20 224 checks, 0 red, 0 mute, copy in `evidence/block-20261028f/`. The count gate
is 51 / 0. Then a check was added to the sweep — *the ledger is green on today's journal*
(2 914 → 2 915) — and proven red from outside: one row removed from a copy of the journal, the
sweep went 2 915 / 1 naming exactly `landing-badge-rows.py`, and back green when the file was
restored. Live side: 10 rules, 0 failed, 10 of 10 controls; set composition 51 batteries, 24
deferred, 0 questions; control breadth 59 records on one instrument; page canary 12 pages, 81
cells, 0 missed.

**What this does not prove.** That the answer time still holds: it was not re-measured today
(23.10, norm 30 days), and a green register entry five days old is a memory, not a measurement.
That the chain survives a cold machine: it needed a real Chrome on `:9223`, and the first launch
on the old `chromium-upwork` profile produced no DevTools port at all — the run that succeeded
used a fresh profile, which is a condition, not a guarantee. That the three stitched rows were
green today for the same reason they were green before: their code was already the current one,
and the numbers matched, but they were not measured as part of a whole set. And that anything
above says the site sells: it says the instruments now ask the questions they were built for.

**Files.** `landing-live-run.py` (`--cond`, `--set`, `capture_re`, unfilled placeholders as
skips, notes naming their journal), `landing-live-ledger.py` (rule `runnable`, control `nofill`),
`landing-sweep.py` (dynamic control count 9 → «все свои», the new "green on today's journal"
check, 2 915), `tools/live-runs.json` (`placeholders` for the delivery record, `capture_re` for
the letter, both conditioned rows stamped from today's runs). Evidence:
`evidence/block-20261028f/` (nofill skip, chain journals, journal before/after, count-ledger
before/after, sweep red and green proofs, `merge-3-rows.py`) and `evidence/live-20261028T0807*/`.





## The button every visitor presses led to a page nobody had opened (28.10.2026)

Nine pages in nine languages make one promise and one gesture: a student reads the page and
presses the button that opens `https://t.me/UchiSamBot`. The link had been checked as a *string*
many times — the sweep compares the `href` on every page, `landing-links-audit.py` proves it is
not broken, `landing-third-party.py` counts foreign hosts. No battery had ever opened what the
link opens. So the second page of the sale — the one every visitor sees **before** the first
message — had never been read by anything in this repository.

**What was there.** A Russian title (`Учебный помощник`), a Russian description, a real avatar,
a working `START BOT` button. And inside that description: *«математика, русский, физика»*.
The subject registry (`tools/subjects.json`) sells **English**, not Russian — the same class of
defect that once shipped to nine pages when translators put the page's own language into the
subject chips. This time it sat one step closer to the buyer, and the site was green.

**Two descriptions, one page.** The first fix looked done and was not. `setMyDescription` is the
long field (≤512), shown in an empty chat before the first message; the page at `t.me` shows the
**short** field (`setMyShortDescription`, ≤120). Nine long texts went in, read-back returned all
nine — and the page did not move: the register said 144 characters, the page showed 102. The
battery caught exactly that, because it compares the *live page* with the register and not the
register with itself. Both fields were then set per language: eight languages take the site's own
`meta.desc` (already written, translated and proofread for the page), the hand-written Russian
long text is preserved verbatim as the `ru` slot, the slot without a language code — the one a
visitor from an unnamed language gets — is English, which is the site's default language. 18
texts, 18 read-backs, 0 mismatches. A third text that had been living in BotFather
(*«Пришлите задачу или вопрос по школьной программе…»*) is gone: three surfaces, one wording now.

**The register, not the BotFather field.** `tools/bot-profile.json` is the single source, in the
same shape as `site.json`, `prices.json` and `subjects.json`: `long` and `short`, nine languages
each, `default`, and a `handwritten` map that says out loud which slot is not derived. The sweep
asks three questions of it (2 915 → 2 919 with the control): the eight long texts must equal the
dictionaries' `meta.desc` word for word; the nine short texts must fit 120 and the default slot
must be Latin; every short text must carry both a word about free and the number from
`prices.json` (2) — otherwise the profile promises "free" in general, which the product does not.

**The battery.** `landing-bot-profile.py` (13 checks, live, Playwright) opens the page the site
points at and reads it as a visitor: 200 and a bot page (a `START` button, not a contact);
`@username` equals the tail of the site's own link, and all twelve pages point at **one** profile;
name non-empty and inside 64; short description inside 120; the short description equals the
register; no Cyrillic in the default slot; no subject outside the canon; a free promise carries
its limit; a real avatar (≥100 px); the button resolves to that same bot; no "not found" text.
Seven controls, each breaking the fetched copy once: `cyrillic`, `empty`, `subject`, `unlimited`,
`photo`, `dead`, `nobot`. First run, before the fix: **two red** — the Cyrillic clause (81 letters)
and the subject clause (`русский`). After the fix: 13 / 0. Controls: 7 / 7 caught, and the
side-effects are named rather than hidden — a broken description also reddens the
register-equality clause, which is honest (the text really did leave the register) but is not
counted as proof.

**Proving the gate can redden, from outside.** The three sweep clauses were broken on disk the
way a person would break them: the default short text replaced with a Russian sentence, the
Turkish short text stripped of its number. The sweep went 2 919 / 2, naming exactly *«кириллица в
слоте по умолчанию: True»* and *«без лимита «2»: ['tr']»*, and back to 2 919 / 0 when the file was
restored. Inside the sweep the same three clauses are also fed a deliberately broken copy of the
register and must all three redden — a fourth check, so the gate is shown to be a gate.

**The live side is ten now.** The new battery is registered in `tools/live-runs.json` (ten entries,
`every_days: 3`, `floor: 13`) and stamped from a real run through `landing-live-run.py --stamp`
(13 checks, 4.0 s). The judge: 10 rules, 0 failed, ten of ten entries fresh, green and above their
floor. Set composition unchanged at 51 batteries in the offline set; the new file is in `SKIP`
with the word «живой» in its reason, which is what makes it visible to the composition rule.

**What this does not prove.** That the title reads for a non-Russian visitor: the display name is
still `Учебный помощник`, and a name is a brand decision, not a translation — measured, reported,
not touched. That Telegram actually *shows* each localized description to a user whose app is in
that language: read-back proves storage, not display, and only a phone in Istanbul would prove
display. That the nine short texts are good copy: they are compressed from approved page text by
this block, not tested on a reader. That the avatar is on brand — only that it exists, loads and
is 320 px wide. And nothing here says the site sells: it says one more surface is now watched by
something other than memory.

**Files.** `landing-bot-profile.py` (new battery, 13 checks, 7 controls), `landing-sweep.py`
(three register clauses + their control, 2 915 → 2 919, live section «девять» → «десять»),
`landing-regress-all.py` (SKIP line with the reason), `landing-live-ledger.py` /
`landing-live-run.py` (docstrings say ten), `tools/bot-profile.json` (new registry: 9 long + 9
short texts), `tools/live-runs.json` (tenth entry, stamped from a real run). Evidence:
`evidence/block-20261028g/` (first red run, controls, register-before/after, sweep red on the
broken registry and green after restore) and `evidence/live-20261028T085940/`.

## The name above the button was Russian for everyone who pressed it (28.10.2026)

Nine pages end on one gesture, and the page it opens has three fields: a name, a long
description, a short one. The previous block translated the two descriptions into nine
languages and left the name alone — it was called a brand decision, measured and reported, not
touched. Measured again with the Bot API, the same measurement is worse than it looked: the
bot holds **nine empty language slots**. `getMyName(language_code=…)` returned `''` for all
nine, and the single slot without a code — the one every unnamed language falls back to — held
«Учебный помощник». So the first thing a visitor from Istanbul, São Paulo or Jakarta read about
the product after pressing the site's main button was a script their phone cannot read. The
site was green, and the defect sat one click past the last gate.

**What the name is now.** Nine names, each the brand plus *the page's own headline* for that
language: `UchiSamBot — Tareas paso a paso en Telegram`, `… — PR langkah demi langkah di
Telegram`, `… — होमवर्क का स्टेप-बाय-स्टेप हल, Telegram में`. They are not new copy: every name
is the `meta.title` of that language's own page, already written and proofread, so the
register cannot drift from the page without the sweep saying so. The Russian name is the one
exception and it is declared: «Учебный помощник» is kept verbatim as `handwritten`, because it is
what the Russian audience already knows, and a brand decision is not a translation. The slot
without a language code takes the English name — the site's default language, the same rule the
descriptions already follow.

**The trap that only a live run could show.** The first version of the writer put the English
name into the *default* slot and stopped. Read-back said "9 of 9 OK" and the battery said
otherwise: `getMyName(language_code="en")` was still empty. The default slot and the `en` slot
are two different fields in Telegram, and a register that names nine languages was describing
eight plus a fallback. That is the same class of lie the previous block found between the long
and the short description — this time one level up. The writer now sets **ten** slots per field
(the default plus all nine), and re-running it for `long` and `short` gave the two descriptions
their missing `en` slots as well: 30 writes, 30 read-backs, 0 mismatches.

**The register.** `tools/bot-profile.json` grew a `name` block in the shape it already had:
`limit` 64, `texts` for nine languages, and a `handwritten` map that says out loud which slot is
not derived. `tools/apply-bot-profile.py` (previously a one-off in a scratch directory, now in
the repository) is the only device that writes the profile: it reads the register, sets the
default slot and the nine, reads everything back, prints no token, and exits 2 — «не проверено» —
when the token or the network is missing instead of going green. `--check` verifies without
writing.

**The battery.** `landing-bot-profile.py` went from 13 checks to **29**: the Bot API has to
answer; the default slot has to equal the register; each of the nine slots has to equal its
register text; no slot may be empty (the original defect, as one clause); every non-handwritten
name must carry the brand; the Russian slot must stay Cyrillic (the owner's name was not
rewritten); every name must fit 64; and — the clause that ties storage to what a person sees —
**the live page's title must equal the default slot**. Controls went from 7 to 11: `ntitle`
(broken page title), `nslot` (empty slot), `nbrand` (name without the brand), `nru` (Latin in the
Russian slot). All eleven caught their own clause; the side effects are named, not counted.

**Before and after, on the real bot.** First run, before the fix: **29 checks, 14 failed** —
the default slot, nine slots, the empty-slot clause, the brand clause, the Cyrillic clause and
the page title. After the register was applied: **29 / 0**, and the title of `t.me/UchiSamBot`
is now the English name, which is the proof that the default slot is what a visitor actually
gets. Eight of the eleven controls break the page-side clauses; three break the name-side ones.

**Proving the gate can redden, from outside.** Two slots were broken on disk the way a person
would break them — `tr` replaced with an English name, `hi` emptied. The sweep went 2 923 / 2
and named them: *«нет: ['hi']»* and *«расходятся с заголовком страницы: ['hi', 'tr']»*, then back
to 2 923 / 0 when the file was restored byte for byte. The sweep also feeds a deliberately
broken copy of the register to the same three clauses and requires all three to redden — a
fourth check, so the gate is shown to be a gate. Sweep: 2 919 → **2 923**.

**The live side stays ten.** `tools/live-runs.json` records the new floor (29, up from 13) and
carries a stamp from a real run: 29 checks, 0 failed, 6.2 s. The ledger judge: 10 rules, 0
failed, all ten entries fresh, green and above their floor.

**What this does not prove.** That a Telegram client *displays* the localized name: read-back
proves storage, and only a phone with its app in Turkish would prove display. That
«UchiSamBot — the page's headline» is a good name for a chat list: it is the page's own title,
chosen for consistency, not tested on a reader — a shorter brand-first name may read better.
That the Russian name should keep its current form: «Учебный помощник» carries no brand, and
putting the brand in front of it is the owner's call, not a translation decision. And nothing
here says the site sells: it says the third field of the second page of the sale is now watched
by something other than memory.

**Files.** `tools/bot-profile.json` (new `name` block: 9 names, limit 64, `handwritten` ru),
`tools/apply-bot-profile.py` (new in the repository: the only writer; 3 fields × 10 slots;
`--check`; exit 2 when unmeasured), `landing-bot-profile.py` (29 checks, 11 controls),
`landing-sweep.py` (3 name clauses + their control, 2 919 → 2 923),
`tools/live-runs.json` (floor 13 → 29, stamped from a real run). Evidence:
`evidence/block-20261028h/` (battery red-before 29/14 and green-after 29/0, the first failed
apply and the ten-slot fix, 11 controls, sweep red on broken names and green after restore) and
`evidence/live-20261028T095001/`.

## The bot answered "Російська" to five languages that had just chosen their own (28.10.2026)

The site's last gesture is the same on all nine pages: press the main button, land in the bot,
press `/lang`, pick your language. The previous two blocks measured what is *above* that button
(the page the button opens, and the name on it). This block measured the screen *inside* it, and
found the one bot screen where six languages out of nine were wrong: the confirmation that
follows the choice.

**What it said.** In Spanish «✅ Idioma: Ruso», in Hindi «✅ भाषा: रूसी», in Turkish «✅ Dil:
Rusça», in Vietnamese «✅ Ngôn ngữ: Tiếng Nga», in Ukrainian «✅ Мова: Російська» — each rendered
in the language the person had just picked, and each naming Russian. For a Ukrainian reader that
is not a typo, it is the wrong answer to a question about identity, delivered in their own
language.

**Why it was wrong by construction, not by translation.** The screen was built for two languages:
a key `lang_set` holding «Язык: Русский», a second key `lang_set_en` holding the English line, and
the choice between them made by the calling code —

```python
t(lang, "lang_set_en") if lang == LANG_EN else t(lang, "lang_set")
```

With two languages this is correct. With nine, `else` means "everyone who is not English gets the
Russian sentence", and the seven translators who filled `lang_set` filled it with the meaning the
Russian slot had: *the language is Russian*. Two of them (Portuguese, Indonesian) wrote their own
language into it by accident and were right; the other five were not. The English slot had the same
disease, hidden one level deeper: `lang_set` in the English dictionary also said "Language:
Russian", and only the branch kept it invisible. It became visible the moment the branch was
replaced by a single function — which is the point of the fix.

**The fix is the removal of a branch, not nine strings.** `handlers.lang_set_text(lang)` renders
`t(lang, "lang_set")`, and `cb_lang` calls it. Each dictionary now names itself: «✅ Язык:
Русский», «✅ Language: English», «✅ Idioma: Español», «✅ Idioma: Português», «✅ भाषा: हिन्दी»,
«✅ Bahasa: Indonesia», «✅ Dil: Türkçe», «✅ Ngôn ngữ: Tiếng Việt», «✅ Мова: Українська». The key
`lang_set_en` is deleted from all nine dictionaries and from the code, so "English is the special
one" has nowhere to live. Nine strings, one function, no branch.

**The battery.** `landing-bot-lang.py` (73 checks, offline, renders through the bot's own code —
`lang_set_text`, `menu_kb`, `t`). Per language: the confirmation is not empty in the register;
it names *its own* language, using the last word of the button the person pressed (`Español`,
`हिन्दी`, `Türkçe`, and `Indonesia` for «Bahasa Indonesia»); it names no other language; it has no
raw placeholders; it has no Cyrillic outside ru/uk; the menu rebuilt after the switch carries seven
labels in the new language; the first screen (`welcome`) names the same language. Global: nine
dictionaries, nine titles, the nine confirmations are pairwise different, `lang_set_en` is gone,
and two AST clauses require that `cb_lang` renders through `lang_set_text` and contains no
`LANG_EN` branch.

**Before and after, on the real dictionaries.** First run, before the texts were touched:
**73 checks, 7 failed** — `свой язык` for en, es, hi, tr, vi, uk, plus `ключ: lang_set_en больше
не нужен`. After: **73 / 0**. Six controls, six caught their own clause: `wrong` (es → «Idioma:
Ruso»), `empty` (tr → empty slot), `raw` (vi → `{lang}`), `cyr` (id → «Bahasa: Русский»), `en`
(uk → «Language: English»), `dupe` (all nine → the Russian line). Side effects are printed and not
counted.

**A control that taught the battery a fact.** The `empty` control first *did not* redden `пусто:`
— because `t()` falls back to English for an empty slot, so a Turkish user never sees an empty
message, they see "✅ Language: English". The clause was measuring the wrong thing: the hole is in
the register, the symptom is English. It now reads the dictionary (`TEXTS[lang]["lang_set"]`) and
the fallback is caught once more by `свой язык: tr`. Both facts are named in the docstring.

**Proving the red from outside.** A copy of the bot tree was made (`BOT_ROOT`), the two-language
path was put back into it — `lang_set_en` in `uk` and the old ternary in `cb_lang` — and the
battery went red on exactly four clauses: the key, the string in the code, the branch, and the
missing call. The untouched copy was green, and the restored copy was green again. The battery
cannot be satisfied by a copy it does not read.

**The always-run gate.** The sweep grew twelve checks (2 923 → **2 935**) reading the same
dictionaries with the same AST parse it already uses for the mockups: nine per-language "names its
own language", plus `lang_set_en` is gone, the nine are different, and no Cyrillic outside ru/uk.
Shown to be a gate: the Spanish slot set back to «✅ Idioma: Ruso» → **2 935 / 1**, naming
`[es] … нет слова «Español»`; `lang_set_en` put back into the Russian dictionary → **2 935 / 1**,
naming `lang_set_en вернулся: ['ru']`; file restored byte for byte (sha256
`5ee92412…b503` before and after) → **2 935 / 0**. Bot tests: 97 → **125 passed, 2 skipped**
(`tests/test_lang_screens.py` is the same rule at the bot's own layer, where a bot developer sees
it without the landing skill).

**The set and the register.** The battery is the **52nd** of the offline set (runner row: 73 checks,
4.8 s, code 0), `landing-counts.json` is stamped (52 of 52 rows, 20 297 checks), and the control
`--mutate all` is measured by the breadth instrument like the other 59 records (60 of 60, same
`instrument`, same `controls_sha`).

**A leftover of the same era, named and not touched.** `welcome_en` is defined in all nine
dictionaries and called by nothing — a shadow copy of the first screen from the two-language
design, already drifted (the Russian one holds the English welcome, the other seven hold their own
language). Nothing shows it to a person today; it is the next block's first item, because a key
that nobody reads is a key that will be "fixed" in one place and shown from the other.

**What this does not prove.** That a person sees it: `study-bot.service` has been running since
27 Oct 14:57 and still holds the old code in memory — the fix reaches a real reader only after a
restart, and a restart is the owner's one command, not a cron job's. That the wording is the best
available: «✅ Idioma: Español» is the plainest sentence that cannot be wrong, not a tested one.
That a leading tick is wanted on this screen at all. And nothing here says the site sells: it says
the last screen a visitor meets inside the product now names the language they chose, and something
other than memory watches it.

**Files.** `bot/handlers.py` (`lang_set_text`, `cb_lang` calls it), `bot/i18n.py` and
`bot/i18n_extra.py` (nine self-naming slots, `lang_set_en` deleted),
`tests/test_lang_screens.py` (new, 7 test functions, 2 skipped for ru/uk), `landing-bot-lang.py`
(new battery: 73 checks, 6 controls, `BOT_ROOT`), `landing-regress-all.py` (`NEED_BOT` + one
`CONTROLS` entry), `landing-sweep.py` (12 checks), `landing-counts.json` (52 entries),
`tools/control-breadth.json` (60 records). Evidence: `evidence/block-20261028i/` (red-before
73/7, green-after 73/0, six controls, the external proof on a copy, sweep red on a broken slot and
on a returned key, green after restore with the file's sha) and
`evidence/breadth-20261028T103629/`.

## Two promises sat in all nine dictionaries and no branch ever said them (28.10.2026)

The previous block closed the language screen by deleting a branch and ended by naming what it had
not touched: `welcome_en`, a key defined in all nine dictionaries and read by nothing. This block
opened it, and the first thing the opening found was that it was not alone.

**What was in the register.** Two keys, present in all nine languages, read by no code path at all:

  • `welcome_en` — a shadow of `welcome` from the two-language design, and already drifted: the
    Russian slot held the English greeting, the English slot held a copy of its own. Nothing showed
    either of them, which is exactly why the drift survived — a future "fix the greeting" would have
    landed in one copy and been judged by the other.
  • `choose_type_invalid` — «Напиши 1, 2 или 3. Или отправь задачу заново.» A sentence written for
    the moment a person types a digit that is not a choice. No branch ever said it, so the moment it
    describes had no answer: typing «4» while a task waited for its type silently created a new task
    out of one character, and the person got «task received» instead of "1, 2 or 3".

**Two keys, opposite diseases, and one sentence does not cover both.** A shadow is deleted. A
promise with no place to be spoken is not deleted — that string is the only thing that names the
hole, and removing it would have taken the hole out of the register while leaving it in the product.
So `welcome_en` is gone from all nine dictionaries (21 lines), and `choose_type_invalid` got its
branch: one ASCII digit 0 or 4–9, with a task waiting, answers with that slot in the person's own
language and returns the type keyboard, so the choice is a press rather than a guess. A typed 1–3
still applies the type, and a digit with no waiting task still becomes a task — the branch is
narrower than "any short text".

**Proven on the handler, not on the string.** `tests/test_dead_keys.py` builds the real router
through `build_router` — the call `main.py` makes — and drives `on_text` with a fake message. Nine
languages: the answer equals `TEXTS[lang]["choose_type_invalid"]`, a keyboard comes back, and the
pending task's id is unchanged, so no task was created. Two languages re-check the working path:
«2» still sets the type. The suite went 125 → **140 passed, 2 skipped**. The battery below cannot
prove this: a literal in the source is not a screen.

**The instrument asks in both directions.** `landing-bot-keys.py` (55 checks, offline, AST only —
no bot import, no Telegram) asks: does every key appear as a literal anywhere in the working code
(a key that appears nowhere cannot be read by any variable either — the field is all literals,
because keys also arrive through `TASK_TYPES[num]`, `hint`, `kind`); does every literal passed to
`t()` exist in the register (otherwise `t()` returns the key and a person reads `task_type_7`); is
any key a shadow of another in a second language (`<key>_<code>`); is any key glued from pieces
(`f"step_{n}"`, `"wel" + "come"` — a static walk cannot see a glued key, so it is forbidden rather
than tolerated); is the register the same in all nine languages and free of empty slots (an empty
slot makes `t()` answer in English).

**Red before, green after, on the same files.** A copy of the bot tree at the previous commit (git
archive, working tree untouched) gives **56 checks, 3 failed**: `читается: welcome_en`,
`читается: choose_type_invalid`, `код: нет тени второго языка`. After the fix: **55 / 0** — 48 keys,
each with a reader, no shadows, no glue. Five controls, each breaking one thing in a copy of the
tree and required to redden its own clause: a key added to all nine (`dead`), a key removed from
seven languages (`missing`), a literal the register does not hold (`orphan`), a glued key (`glued`),
a returned shadow (`shadow`) — **5 / 5**, side reds printed and not counted.

**The gate runs on every commit.** `landing-sweep.py` grew five clauses (2 935 → **2 940**) reading
the same dictionaries and the same literals: every key has a reader, no shadow, no invented literal,
no glue, register not empty. Shown to be a gate: the same sweep against the pre-fix copy reddens
**7**, two of them the new ones, naming both keys — `без читателя: ['choose_type_invalid',
'welcome_en']`; the other five belong to the copy, which has no `.env` and no journal. On the live
tree: 2 940 / 0.

**The set and the register.** The battery is the **53rd** of the offline set (row: 55 checks, 0.1 s,
code 0), `landing-counts.json` stamped, and the control `--mutate all` is measured by the breadth
instrument like the other 60 records (61 of 61, same instrument, same `controls_sha`). The set gate
caught the new battery before anything else did: it was in the set and in no `CONTROLS` row, and the
sweep said so by name — which is the reason that gate exists.

**The next block's first item, named by this one.** The register now guarantees that every key has a
reader, but nothing checks what is *inside* the reader's slot: twelve keys carry substitutions
(`invite_text` carries `{link}`, `{count}`, `{free}`; `task_type` carries `{t_}`; `plan_info` carries
eight), and no battery asks whether a translator dropped one. Measured for the record, so the next
block does not have to guess: **12 keys with substitutions, 0 of 48 mismatched today** — a latent
class, not a live defect. It is next because a dropped `{n}` reads as a sentence missing its number,
and a missing `{link}` reads as an invitation with nothing to press.

**What this does not prove.** That a person sees any of it: `study-bot.service` has been running
since 27 Oct and holds the old code in memory — the branch reaches a real reader only after a
restart, and a restart is the owner's one command, not a block's. That Telegram delivers what the
test captured. That the wording of the apology is the best available: it is the sentence the register
already held in nine languages, now spoken, and nothing tested its tone. And nothing here says the
site sells: it says two promises that sat unspoken for weeks are now either deleted or have a place
to be said, and something other than memory checks the register.

**Files.** `bot/i18n.py`, `bot/i18n_extra.py` (`welcome_en` deleted, 21 lines), `bot/handlers.py`
(the digit branch, 11 lines), `tests/test_dead_keys.py` (new, 15 tests), `landing-bot-keys.py` (new
battery: 55 checks, 5 controls, `BOT_ROOT`), `landing-regress-all.py` (one `CONTROLS` entry),
`landing-sweep.py` (5 checks), `landing-counts.json` (53 entries), `tools/control-breadth.json`
(61 records). Bot commit `1823dde`. Evidence: `evidence/block-20261028j/` (red-before 56/3,
green-after 55/0, five controls, sweep red on the pre-fix copy naming both keys, the bot suite) and
`evidence/breadth-20261028T114511/`.

## The price screen showed `{single}` once, and nothing asked again (28.10.2026)

The previous block closed the register question in one direction: every key has a reader. It ended by
naming what it had not touched — nothing asked what sits *inside* the reader's slot. Twelve keys
carry substitutions, 26 slots in each of nine languages and 234 in all: `plan_info` carries eight
(`{single}`, `{single_tasks}`, `{pack5}`, `{pack5_tasks}`, `{pack15}`, `{pack15_tasks}`, `{disc5}`,
`{disc15}`), `invite_text` three (`{link}`, `{count}`, `{free}`), `admin_stats` five,
`free_trials_left` two, and seven keys carry one each.

**Two ways a template breaks, and one of them shipped.** A translator who drops `{count}` leaves a
sentence that reads «Friends joined: .» — and if the lost slot was `{link}`, the invitation has
nothing to press. A caller who forgets an argument is not hypothetical: on 23.10.2026 one of the two
branches of the price screen called `t(lang, "plan_info")` with no arguments, and every buyer of
every language read «Разбор задачи — {single} ⭐️ ({single_tasks} задача)». `t()` does not crash on
that: it catches the `KeyError`, writes a line to the log, and returns the template as it stands.
The defect is invisible to every check and visible to every person — which is the whole reason the
block exists.

**The instrument asks both sides.** `landing-bot-vars.py` — 42 checks, offline, AST only, the bot is
not imported. Register side: the placeholder set of a key is the same in all nine languages,
compared field by field *including* the format spec (because `{n}` and `{n:,}` are two different
promises); no lone `{` or `}` anywhere; every string of every language really formats with its own
set and comes out with no braces left; every field is a plain name, because `t()` passes keyword
arguments only and `{0}`, `{a.b}`, `{a!r}` are a guaranteed failure on a live person. Code side:
every literal call supplies all placeholders of its key and nothing beyond them (an extra argument
means the register drifted away from the code); no template key is called with no arguments at all
(the exact 23.10 defect); and the one key chosen by a variable (`key = "contact_hello" if email else
…`) must be supplied through a variable-key call — the instrument names the file and line that prove
it rather than accepting silence.

**Red on real history, not on a story.** A copy of the bot tree at the parent of the fix commit
`186a418` (git archive, working tree untouched) gives **42 checks, 2 failed** —
`вызов: plan_info отдаёт все подстановки` and `вызов: шаблон не зовут пустым`, both naming
`handlers.py:461`, the line that shipped the defect. On the live tree: **42 / 0** — twelve
templates, one set in nine languages, every call exact.

**Eight controls, each breaking one thing in a copy of the tree**, each required to redden its own
clause: `drop` (Spanish `invite_text` loses `{count}`), `rename` (Turkish `{link}` → `{lnk}`),
`brace` (Russian `buy_for_task` loses a closing brace), `spec` (`{n}` → `{n:zz}`), `bare` (a call
with no arguments), `miss` (the `count=invited` argument removed from the caller), `extra` (a `zz=1`
invented in the price call), `varcall` (`email=email` removed from the variable-key call) —
**8 / 8**, side reds printed and not counted.

**The gate and the set.** `landing-sweep.py` grew four clauses (2 940 → **2 944**) reading the same
dictionaries: placeholders match in nine languages, braces close, templates format, fields are plain
names. The battery is the **54th** of the offline set (row: 42 checks, 0.1 s, code 0), stamped in
`landing-counts.json`, and its control `--mutate all` is measured by the breadth instrument like the
other records (`62 of 62`, one instrument, one `controls_sha`).

**The next block's first item, named by this one.** The register now guarantees the shape of a
template; nothing asks about the numbers *written by hand* beside it. Measured for the record, so
the next block does not have to guess: **8 keys carry digits outside any placeholder, in all nine
languages** — `processing` promises a wait in seconds, `referral_credited` and `invite_text` promise
«+1» free analysis, `plan_info` numbers its three plans, `choose_type_invalid` names 1, 2, 3. The
23.10.2026 defect was exactly this class: `invite_text` promised a friend five free analyses while
`FREE_TRIALS` was two. None of them is wrong today — the free-analysis count has been substituted
since that fix — but the class is unguarded, and a hand-written «5» cannot notice that the registry
changed to 2.

**What this does not prove.** That a person sees the right *number* in the slot: that is
`landing-bot-money.py` and the bot tests on the real router. That any translation reads well. That
the branch reaches a live reader: `study-bot.service` has held its code in memory since 27 Oct, and
a restart is the owner's one command, not a block's. And nothing here says the site sells.

**Files.** `landing-bot-vars.py` (new battery: 42 checks, 8 controls, `BOT_ROOT`),
`landing-regress-all.py` (one `CONTROLS` entry), `landing-sweep.py` (4 checks),
`landing-counts.json` (54 entries), `tools/control-breadth.json` (62 records). **No bot file
changed:** today's register is consistent in every language, so the block added a gate, not a fix —
the red it proves is the one that shipped on 23.10. Evidence: `evidence/breadth-20261028T131659/`,
`evidence/botvars-breadth-20261028.log`, `evidence/botvars-regress-20261028.log`.
## The diary counted fifty-four rows, and the file held fifty-three (28.10.2026, второй блок дня)

The block before this one ended with a sentence that has a number in it: `landing-counts.json`
(54 entries). The sweep was run first in this block, as it is run first every time, and the count
ledger refused the journal by name: `нет в реестре: landing-bot-vars.py (проверял 42)`. The battery
that block had written, documented and proved had no row in the registry the ledger reads. Fifty-three
rows, not fifty-four. Nothing in that block contradicted itself on purpose — it stamped the journal
into the registry in a run where the new battery was already present, and the registry it stamped was
a different copy from the one the ledger opens; the number in the diary came from the intent, not from
the file. The gap was closed by `--stamp` against the same journal: **54 entries, 0 refusals**, and the
ledger that had gone red now says `CHECKS: 54, FAILED: 0`.

**What that says about the diary, not about the site.** Every claim in this notebook that carries a
number is a claim about a file, and a file can be counted. This one was counted, by a gate, within
the hour — which is the whole difference between a diary that records and a diary that asserts. The
other claim in the same paragraph, `control-breadth.json` (62 records), was checked the same way before
this block committed that file: 62 records, ledger green.

**Two dictionaries, counted for the first time without believing the markup.** The dead-key pass of
the previous block covered the bot's register. The landing has its own: 124 keys in nine dictionaries,
read by `index-src.html` and by `build.py`. A first pass by `data-i18n` attributes alone reported
fifteen dead keys per language and two missing ones — every one of them false: the screenshots' alt
texts are read through `d[f"shot{n}.alt"]` and the language button through a composed `aria-label`,
so a checker that trusts attributes sees a key nobody names and calls it dead. The pass that survives
the test — a key is alive if its name appears anywhere in the template or the generator — reports
**124 keys, 0 read by nothing, 0 uneven across nine languages**. The same instrument, on the bot side,
found a real shadow key this morning; on the landing side it finds the register closed.

**And what is inside the slots.** One key carries a substitution (`badge.alt` → `{name}`), the other
123 carry none. Measured across all nine: **0 mismatches against English, 0 placeholders left visible
in the built pages**. That is the class the bot block named as its next item, measured on the landing
and found empty — a latent class here, not a live defect, and worth the eleven lines it cost.

**The visual layer, honestly.** The full sweep ran 54 batteries and 953 checks and then ran out of its
780-second budget, leaving 26 named `SKIPPED-BUDGET`, most of them the layout batteries. Six of those
were run by hand: `landing-text-clip` 148/0 (36 pages, 298–299 elements each), `landing-first-screen`
252/0 (the fold at 915×412 and up, all nine languages), `landing-page-overflow` 36/0 (0 px on every
page), `landing-viewports-extra` 94/0 (no JS errors under throttle), `landing-render-check` 37/0 and
`landing-visual-pass` 306/0 (font, h1 size and line count, badges, rows, per language at mobile and
desktop; frames in `evidence/visual-20261028/`). The last two need a live `http.server` on :8137 —
launched by hand for this run, because the runner starts it itself only inside the sweep.

**What this does not prove.** That a person looked at those frames: this run had no vision tool, so
every one of the 306 lines is a measurement, and the judgement of a picture is still owed — the
screenshots exist and nothing in this block read them. That the sweep was whole: 26 batteries were
skipped, named, not silently absent. That the registry fix has a history: `landing-counts.json` lives
in the skills tree, not in this repository, so its one-line repair has no commit behind it. And that
the two probes added here are checks: `tools/locale-key-parity.py` and `tools/placeholder-parity.py`
are read-only measurements, not batteries — neither has a control, neither is in the set, and the set
gate would name them if they claimed to be.

**Files.** `tools/locale-key-parity.py`, `tools/placeholder-parity.py` (new, read-only). Registry:
`landing-counts.json` (54 entries, stamped against today's journal). Committed with them: the previous
block's own entry and its `tools/control-breadth.json`.

## The footer sent every visitor to a dead partner, and the policy counted three text links (28.10.2026, третий блок дня)

**What was found.** `aitooltrek.com` answered 404 — the root, the `www` host and with a
browser user-agent alike. Old evidence still shows 200 on 25.10, so it died between the
twenty-fifth and the twenty-eighth. The link stood in the footer of all nine pages and was
named twice in the privacy policy (the English and the Russian section) as one of the
"three text links".

**What was done.** Removed from the template; the footer now carries Realistic AI and
Based Tools AI. The policy says "Two plain text links" in both languages. The
"last updated" date was raised to 28.10 — the date guard rightly refuses a changed text
under yesterday's date — and the rebuild carried the new date into `lastmod`.

**How it was checked, outside the block.** `build.py --check` — 24 of 24 files identical to
a fresh build. The footer was read page by page: exactly two partner links on all eight
language pages (the launch badges are a separate strip). `landing-external-links.py` —
68 external addresses, **0 failed, 0 unverified**. The live policy is byte-identical to the
repository (37 731 bytes), already says "Two plain text links", and `aitooltrek` appears in
neither the built tree nor the live pages.

**The class, named.** A partner check already exists — `landing-external-links.py` counts
anything under 400 as alive — but it is deliberately kept out of the sweep (the network
gives floating results), so a partner that dies on the twenty-sixth is invisible until a
technical pass runs it by hand. A dying partner has no automatic alarm: that is the gap this
block lived through, not one it introduced.

**The count that disagreed with itself.** The publish list measured **107 files**, while the
top of this README still said 109. Recounted: 107 is the truth — two files left together with
their platforms (109 → 108 → 107) — and the top line now says so. 495 internal references,
not the 513 written beside the old number.

**What this does not prove.** That the two remaining partners stay alive: nothing watches
them between passes. That a person looked: this block had no vision tool, and the frames in
`evidence/visual-20261028/` were left unread — a later live session read four of them
(English phone, English desktop, Turkish phone, Russian contact) and found no defect; two
suspected clipped chips turned out to be 10–16 px of padding inside the phone mockup.

**Files.** `index-src.html`, the nine built pages, `privacy.html` + its markdown twin,
`sitemap.xml`, `tools/lastmod.json`; this entry and the corrected file count in the
`publish-tree.py` bullet above.

## The gates the morning fixed were asked again, and every one answered (28.10.2026, четвёртый блок дня)

**What this block is.** Not a hunt — a verification pass. The three blocks of the day
fixed the register, the dead partner and the file count; this block asked every gate
again, end to end, so those fixes stand proved rather than assumed.

**What was run, and what it said.**
- `tools/build.py --check` — 24 of 24 files byte-identical to a fresh build: the tree
  on disk is exactly what the current sources produce (reproducibility).
- `tools/publish-tree.py --check` — the list is complete (107 files), nothing extra,
  all 495 internal references stay inside the list.
- `landing-external-links.py` — 68 external addresses, **0 failed, 0 unverified**
  (the two footer partners included).
- `tools/publish-branch.sh --dry-run` — the staged tree served **81 of 81 addresses**
  with zero errors: a switch of the publish source would not break anything.
- `landing-sweep.py` — **CHECKS: 2944, FAILED: 0, ALL PASS.** The morning's whole
  run counted 2914; the thirty extra checks are the batteries the earlier blocks of
  today added to the set, now in the count.

**The policy read as an article, not as markup.** `tools/page-text.py privacy.html`:
the English half says "Two plain text links in our footer — Realistic AI
(realisticai.io) and Based Tools AI (basedtools.ai)"; the Russian half says "Две
обычные текстовые ссылки в подвале" with the same two names; "Last updated:
28 October 2026". Neither half carries "three text links", "aitooltrek" or a partner
that is no longer in the footer — text and markup agree after the third block's edit.

**What this does not prove.** That the two remaining partners stay alive between
passes: the external-links battery is deliberately kept out of the sweep (the network
gives floating results), so a partner that dies tomorrow has no automatic alarm —
the gap the third block named, not one this block closed. And that a person looked at
the frames: this block had no vision tool, so the 306 measured frames of
`evidence/visual-20261028/` stand on measurement alone.

**Files.** This entry only — no site file was touched, so nothing moves in
`gh-pages`; the push is a main-branch journal push to both mirrors.

## The partner who dies on a Tuesday now has an alarm (28.10.2026, пятый блок дня)

**What the day left open.** The fourth block closed with a named gap: the external-link
battery is network-bound, so it is deliberately kept out of the sweep — which means
nothing watches it. On 25.10 a footer partner was dead for three days and a person found
it, not a check. A gate that only runs when someone remembers to run it is a habit, not a
gate.

**What was built.** The battery now writes a dated ledger, `tools/links-last-seen.json`:
68 addresses, the 11 hosts they live on, a verdict per address, `checked_at` in UTC. The
sweep — offline, no network — asks three separate questions about that ledger: it exists,
it is not older than thirty days, and **every host the pages link to has a verdict in it**.
The third question is the one that matters for the future: a partner added to the footer
without a battery run is now red, not "not yet".

**Proved both ways, not assumed.**
- Before the ledger existed the sweep went to `CHECKS: 2948, FAILED: 3` and named exactly
  the three new questions — the alarm fires on the state it is meant to catch.
- With the ledger written by a fresh run (`68 addresses, 0 failed, 0 unverified`) the same
  sweep returned `CHECKS: 2948, FAILED: 0, ALL PASS`.
- The four extra checks are the four new ones: 2944 → 2948.

**The pretending alarm was caught too.** Editing the battery changed its code, and the
breadth ledger refused to accept an old measurement taken by new code
(`7a2e74d2d7cc ≠ fdb2067890cc`). The row was re-measured (`--mutate`, 78.9 s, breaks `en`
and `ru`, reads 11 pages) and merged into the 62-row registry — the other 61 rows untouched.
That refusal is the reason the registry is worth anything: it will not report a measurement
the current code never made.

**Today's numbers, run fresh in this block.** `build.py --check` 24/24 byte-identical;
`publish-tree.py --check` 107 files, 495 internal references inside the list;
`landing-external-links.py` 68/0/0; `landing-live-bytes.py` 26/26 with the 404 probe
serving its own page; nine language pages 113–125 KB each, 11 hreflang rows apiece;
`landing-visual-pass.py` **306 checks, 0 problems** across nine languages at 420 px and
1440 px — headline 30 px/2 lines on the phone, 56 px/2–3 lines on the desktop, badges
7/7 loaded on every page, zero horizontal overflow outside the slider.

**What this still does not prove.** That the ledger is written on a schedule: it is written
by the battery, and the battery is still run by a block, not by cron. The sweep now
notices when that stops happening (30 days), which turns silence into a red check — it does
not turn silence into a run. And that a person looked at the frames: this block had no
vision tool either, so the 306 frames in `evidence/visual-20261028e` (scratch) stand on
measurement, not on an eye.

**Files.** `tools/links-last-seen.json` (new), `tools/control-breadth.json` (one row
re-measured), this entry; and in `stars-bots-ops`: `landing-external-links.py` (writes the
ledger), `landing-sweep.py` (the three offline questions).

## The sixth block looked in the three places the day had not, and found nothing to fix (28.10.2026, шестой блок дня)

**What this block was for.** The day's five blocks closed the gaps they named; this one went
after the three surfaces none of them had touched: the addresses a visitor can *type*, the
icon the browser puts on the tab, and the legal text read against the database it describes.
It also re-ran the whole stack end to end, because a gate is only worth its last green run.

**Measured fresh in this block.** `landing-sweep.py` **2948 checks, 0 failed** (the build
check inside it: 24 files byte-identical, so the source and the pages on disk still agree);
`landing-price-parity.py` 9 checks, 0 diffs against `bot/payments.py`; `landing-bot-lang.py`
**73 checks, 0 failed** under the bot's own interpreter (aiogram 3.31.0) — the screen that
once said «Idioma: Ruso» to a Spaniard; `landing-bot-money.py` all OK (30/120/300 Stars,
20 %/33 %, two free breakdowns). Live, by hand: `/` 200 (113 647 B), `/ru/` 200 (120 020 B),
`/ru` 301 → `/ru/`, `/index.html` 200 with the same bytes as `/`, an unknown path 404 serving
the site's own 6 442 B page, `http://` 301 → `https://`. Transfer weight the phone actually
downloads: **35.6 / 36.4 / 37.5 KB gzip** for en / ru / hi. `landing-visual-pass.py`
**306 checks, 0 problems** across nine languages at 420 px and 1440 px (headline 30 px/2 lines
on the phone, 56 px/2–3 lines on the desktop, 7/7 badges per page, no overflow outside the
slider).

**The three candidates, and why each was not a defect.**
- *The tab icon.* The page declares three: `img/logo.svg`, `img/icon-64.png`,
  `img/icon-180.png`; all three answer 200 from the root, and the language pages declare
  them as `../img/…`, which resolves to the same files. `/favicon.ico` alone is a 404 — but
  that path is only what a browser asks for when **no** icon is declared, and here they are.
- *The 404 page at depth.* GitHub Pages serves one `/404.html` for the whole tree, so a
  relative asset on it would break two directories down. It has none: every link and the
  logo on it are absolute (checked by fetching `/ru/deep/nope` and reading its `href`/`src`).
- *The privacy policy against the database.* `profiles` stores `common_chats`, and the
  policy does say «how many group chats you share with the Telegram account we use to read
  the profile» — the phrase the sweep's map expects. This block's first grep said the word
  was missing; the grep was wrong, the sentence is split by inline markup. Worth writing
  down: a negative grep is evidence only after the pattern has been read.

**What this does not prove.** That a person looked at the 306 frames: this block had no
vision tool either, so the frames in `evidence/visual-20261028` stand on geometry, not on an
eye. And that the redirect/weight matrix is watched by anything: GitHub Pages owns those
statuses and that gzip, both were measured by hand here, and no battery repeats them — a gate
for them would change a battery's code and therefore cost a breadth measurement and a count
stamp, which is a block of its own, not the tail of this one.

**Files.** This entry only — no page, no dictionary, no battery was touched; the push is a
main-branch journal push to both mirrors.

## The eighth block asked the eye to read a line it could not know in advance (28.10.2026, восьмой блок дня)

**What this block was for.** The seventh entry ended with an admission: `head`, `subjects`, `shots`,
`band` and `footer` had never been through the eye, and for those frames the grounding guard had
nothing to hold on to — no `H1` in a subject grid, a chat mockup or a footer. The battery's own
code answered that hole with `ok_head = bool(got["lang"])`: **one word of language was enough to
call a frame passed.** A model could read nothing at all in the block and still go green.

**The fix, before any measuring.** `expected_anchor(root, lang, section)` (28.10.2026) takes the
first real line of the block out of the built page itself — `h2`, else the first paragraph — and the
prompt now asks for it verbatim: `LINE: <дословно одна строка текста, которую видно в блоке>`.
For frames without a first screen the verdict is now the word overlap between that line and the
HTML's own anchor; the language answer is no longer accepted as proof. If the block has an anchor
but the model read no line, the row is `eye-not-grounded` (red), not a pass. The prompt still forbids
taste judgements and still names only visible breakage as a defect.

**Second fix: silence is transport, not a verdict.** `en` returned an empty `content` twice for
`subjects,shots` — the whole budget went into reasoning. The battery now retries a silent chunk
frame by frame before it writes `eye-silent`, so a page is not failed for a model that stopped
talking.

**Measured (`evidence/eye-20261028`, frames from `evidence/visual-20261028`, nine languages × two
viewports per section).**
- `head,hero` — **9/9 pass**, every language grounded on its own `H1` read verbatim across Latin,
  Cyrillic and Devanagari; zero visible defects.
- `subjects,shots` — 9 pairs: **0 defects, 1 ungrounded (`vi`), 2 silent (`en`, `es`)**. Grounding
  itself worked: `ru` answered «Школьные предметы», matched its anchor 2/2 words (100 %). The red
  rows are the model's, not the page's — `vi` never produced a line, `en`/`es` stayed silent even
  frame by frame. That is a hole in *proof*, and it is reported as a hole.
- `band,footer` — started, **not finished inside this block**: the first language (`en`) came back
  ungrounded at 2/10 words on the `band` anchor. Two readings are possible — the model paraphrased
  the band sentence, or the band sentence is genuinely cut in the frame — and this block did not
  spend the frames to tell them apart. It is the first item of the next block.

**What this does not prove.** That a green row is taste-approved: the eye reports breakage it can
see, and four of the nine languages' lower sections have not been looked at yet. And that the model
is stable: it goes silent on some frames regardless of content, so a silent row must be re-asked,
never read as clean.

**Files.** `stars-bots-ops/scripts/landing-eye.py` (anchor grounding, per-frame retry); this entry.
`evidence/` is gitignored and stays out of the repo. No page, no dictionary, no other battery was
touched.

## The seventh block gave the site an eye, and the eye read all nine headlines (28.10.2026, седьмой блок дня)

**What this block was for.** The six entries above end with the same admission: *this block had
no vision tool, so the frames stand on geometry, not on an eye.* The local Qwen on `:9080`
reports `capabilities: ["completion", "multimodal"]` — the eye was there all day and nobody had
pointed it at a single frame. This block pointed it, and turned it into a battery instead of a
one-off look: `landing-eye.py`.

**How the eye is stopped from lying.** A vision model asked «any defects?» says «looks good»,
which is worth nothing. So the battery carries a grounding guard: the model must read the page
`<h1>` first, the battery extracts the expected headline from the built HTML itself and compares
word by word, and anything under 60 % overlap is reported as `eye-not-grounded` — a red check,
not a pass. An empty answer is `eye-silent`, also red. The worst outcome this battery can produce
is a failed run; it cannot produce a green one it did not earn.

**Measured.** Nine languages × the first screen and the contact block × two viewports = 36 frames
from `evidence/visual-20261028`. Every language passed, and the model read each headline verbatim
across three scripts — Latin («Homework that finally makes sense»), Cyrillic («Домашка, которая
наконец понятна», «Домашка, яка нарешті стає зрозумілою») and Devanagari («होमवर्क, जो अब आखिरकार
समझ में आता है»). Zero visible defects: no clipped text, no overlap, no button off-screen, no
narrow desktop column.

**A limit measured the expensive way.** Six frames in one question returned an empty `content`
for seven languages — the whole token budget went into reasoning and nothing came out. Four
frames per question answer in about 22 s. The battery now chunks the frames by four and labels
silence `eye-silent`, so a run cannot again spend twelve minutes on answers that never arrive.

**What this does not prove.** That the eye agrees with a person: it reads text and reports breaks
it can see; it does not judge taste, and it was not asked to. And that the whole page has been
looked at — `head`, `subjects`, `shots`, `band` and `footer` have not been through the eye yet;
those sections still rest on geometry alone. That is the next block's work, at two sections per
question.

**Files.** `stars-bots-ops/scripts/landing-eye.py` (new); `evidence/eye-20261028/eye.json`
(the 36-frame pass — `evidence/` is gitignored and stays out of the repo); this entry. No page,
no dictionary, no existing battery was modified.

## The eye read one band and was graded against another (28.10.2026, девятый блок дня)

**What this block was for.** The seventh entry named its own gap: `head`, `subjects`, `shots`,
`band` and `footer` had never been through the eye. This block took `band` and `footer` — nine
languages, two viewports, 36 frames already sitting in `evidence/visual-20261028`.

**The floor underneath.** A fresh sweep before any looking: 2 948 checks, 0 failed. Rebuild
reproducibility `tools/build.py --check` — 24 files byte-identical to a clean build. Publish tree
`tools/publish-tree.py --check` — 107 files, 10.0 MB, 495 internal links, every one inside the
list, nothing named that has no reader. Whatever the eye found later, the page underneath it
was intact.

**The first pass was red in all nine languages, and all nine were false.** `landing-eye.py
--sections band,footer` answered `UNGROUNDED` for en, ru, es, pt, hi, id, tr, vi, uk — 0 % to 20 %
word overlap with the expected anchor, in all nine at once. Nine independent reading failures
in nine scripts is not a model problem; it is one mistake made once. The answers themselves said
where: the model had read «Отправь её боту — первые 2 разбора бесплатно» verbatim, which is not a
mislabelled band, that is the call-to-action strip.

**Two strips carried one name.** `landing-visual-pass.py` screenshots the block with selector
`.band` — the strip that asks «Stuck on a problem right now?». `landing-eye.py` looked for its
anchor with `class="[^"]*\bband\b`, and the first class in the page carrying that word is
`principle-band` — the strip that says «Not just answers». The frame and the anchor came from
different elements, and the battery compared them honestly and failed every time. Both files were
right about their own band; the harness had no single meaning for the name.

**And one question still carried two blocks.** Even with the name fixed, the battery asked about
four frames at once — mobile and desktop of `band`, then of `footer` — and required one
`HEADLINE` and one `LINE` in return. One line cannot ground two blocks; whichever block the model
chose, the other was unproven. That is the six-frames-in-one-question mistake of the seventh
entry, one step smaller.

**Fixed, in the battery and not in the pages.** The `band` mark now matches the same element the
screenshots take (`class="band[\s"]`), so the harness has one meaning for one name. The question
is asked once per block — mobile and desktop of that block, two frames — and every block is graded
against its own anchor; the row records all anchors, not the closest one. Re-run in Russian first
(`PASS`, read «Застырял на задаче прямо сейчас?» — the model's own one-letter slip, not the
page's), then all nine: `PASS` for en, ru, es, pt, hi, id, tr, vi, uk. Nine pair-of-frames rows,
0 defects, 0 ungrounded, 0 model-unavailable. The eye read the call-to-action headline verbatim in
Latin, Cyrillic and Devanagari, and found nothing clipped, overlapped or off-screen in the strip
or the footer.

**The promise was read as a promise, not as words.** The strip says, in nine languages, that the
first two breakdowns are free. The number and the offer are identical everywhere — «первые 2
разбора», «the first 2 breakdowns», «los primeros 2 desgloses», «as primeiras 2 explicações»,
«पहले 2 हल», «2 pembahasan pertama», «ilk 2 çözüm», «2 lần phân tích đầu tiên», «перші 2
розбори» — and they match `tools/prices.json` `free_breakdowns: 2`, the hero chip and the payment
answer in every dictionary. The footer names its privacy pages as EN/RU in the seven languages
that do not have their own, which is labelling, not a promise it cannot keep.

**What this does not prove.** That the strip reads well to a person — the eye reports breakage it
can see and is not asked about taste. That the model reads letters perfectly: it wrote «Застырял»
for «Застрял» and still grounded, because the guard counts words, not glyphs, and a one-letter
slip inside a sentence is not a page defect. And that the page has been looked at whole:
`principle-band`, `ref-band` and `parents-band` — three more strips that carry the same word in
their class — have still never been through the eye, and they now have the same name problem this
block fixed for one of them.

**Files.** `stars-bots-ops/scripts/landing-eye.py` (band mark, per-block question, per-block
grading); `evidence/eye-20261028L/eye.json` and `evidence/block-20261028l-*.txt` (`evidence/` is
gitignored and stays out of the repo); this entry. No page, no dictionary, no price file was
touched.

## Three strips the eye had never seen, and an anchor that belonged to the FAQ (28.10.2026, thirteenth block of the day)

**What this block was for.** The twelfth entry named its own gap: `principle-band`, `ref-band` and
`parents-band` carry the same word in their class, had never been through the eye, and shared the
name problem it had fixed for one strip.

**The floor underneath.** `tools/build.py --check` — 24 files byte-identical to a clean build.
`tools/publish-tree.py --check` — 107 files, 495 internal links, all inside the list. Sweep —
2 948 checks, 0 failed. Visual pass after the three parts were added to its frame list — 306 checks,
`PROBLEMS 0`, and 54 new frames (nine languages, two viewports, three strips).

**One name, one element — in both files.** `landing-visual-pass.py` now shoots `.principle-band`,
`.ref-band`, `.parents-band`; `landing-eye.py` anchors each block on the same element. The frame and
the line it is graded against come from one place, which is what the twelfth entry had to learn the
hard way.

**The anchor was reading a different block.** First real run: `principle` and `parents` passed in all
nine languages, `ref` came back `UNGROUNDED` in es, pt, tr, vi — anchored on «Preguntas frecuentes»,
«Perguntas frequentes», «Sıkça sorulan sorular», «Câu hỏi thường gặp». The strip sits right before
the FAQ, and the text window was cut at the next known section mark, so the FAQ heading landed in the
window and the strip was graded against it. Four languages failed on a line no visitor could ever
read inside that frame. The window is now the element's own span, closed by its own tag (balanced
count), so a neighbouring block cannot be borrowed as an anchor.

**And one anchor was three elements glued together.** `<p[^>]*>` also matches `<path …>` inside an
SVG. In EN the `parents` strip opens with an icon, so the «first paragraph» started at the icon's
`<path>` and ran to the first `</p>` — icon, `</svg></div>`, the `h2` and the paragraph, 67 characters
in one string, while Hindi got a clean 16-character `h2`. The same block was measured by a different
ruler in different languages. `<p\b` cannot match `<path`; the same pattern was made safe in
`landing-live-assets.py` and `landing-sweep.py` (their FAQ blocks carry no SVG today, so nothing was
broken there — it is closed as a class, not as a symptom).

**Two smaller things the day's runs paid for.** `--out` wrote its JSON without creating the folder: a
full nine-language pass printed every verdict and then died on the write, losing the evidence —
`mkdir(parents=True)` now runs first. And a strip has no headline, so the model honestly answered
`HEADLINE: ->` while transcribing the sentence into `LINE`; the verdict then read «PASS, глаз прочитал
«->»», a green that looks like garbage. The report quotes the field that has words in it.

**And the ledger that trusted itself too much.** Editing `landing-visual-pass.py` changed its sha, so
the pre-commit sweep refused the commit until the control was re-measured — correct, it is the gate
working. Re-measuring it with `--only landing-visual-pass.py --write-registry` then rewrote the whole
registry with the two filtered records: 62 entries became 2, silently. The registry was restored from
git and the two fresh measurements merged in by key instead; the sweep is green again (2 948 checks,
0 failed) and the ledger still holds 62 records. The write-registry path needs to merge, not replace —
filed here so the next block fixes it, because the next person to run it that way loses the file.

**Result.** `principle` 9/9 `PASS` (en «Not just answers. Learn how to solve the next one.», hi
«सिर्फ़ जवाब नहीं। अगला सवाल खुद हल करना सीखें।», uk «Не лише відповіді…»). `parents` 9/9 `PASS`.
`ref` 5/9 before the anchor fix, 9/9 `PASS` after it — and the raw answer of the EN run shows the
model transcribed the sentence verbatim («Invite a friend – when they solve their first task…»), so
the green rests on the text, not on the word «arrow». 0 defects, 0 ungrounded, 0 model-unavailable
across the three strips, 27 frame-pairs.

**What this does not prove.** That the strips read well to a person — the eye reports breakage it can
see and is not asked about taste. That every block has an anchor: `vi` `subjects` returns an empty
anchor and would be graded on nothing, and `head` has no `h2`/`p` at all — both still rest on geometry
alone, and that is the next block's work. And that the sections the strips live in (`how`, `features`,
`pricing`, `faq`) have been seen: the strips have, their sections have not.

**Files.** `stars-bots-ops/scripts/landing-visual-pass.py` (three parts); `landing-eye.py` (three
marks, element span, tag boundary, mkdir, honest quote); `landing-sweep.py` and
`landing-live-assets.py` (tag boundary); `evidence/visual-20261028/`, `evidence/eye-20261028M/`,
`evidence/eye-20261028N/`, `evidence/eye-20261028P/` (`evidence/` stays out of the repo); this entry.
No page, no dictionary, no price file was touched.

## The registry that could only be replaced, and two blocks the eye had never graded (29.10.2026, fourteenth block of the day)

**What this block was for.** Three things the thirteenth entry named and left standing: the
`--write-registry` path that replaced instead of merged (62 records became 2 on 28.10), `vi`
`subjects` returning an empty anchor, and `head`, which has no `h2` and no paragraph and so rested on
geometry alone in all nine languages.

**The floor underneath.** `tools/build.py --check` — 24 files byte-identical to a clean build.
`tools/publish-tree.py --check` — 107 files, 495 internal links, all inside the list. Sweep —
2 948 checks, 0 failed, before any edit and again after.

**One path, not two.** `landing-control-breadth.py --write-registry <registry>` wrote the file
straight from the rows it had measured, so a one-battery run rewrote a 62-record gate input with the
two records it happened to take. `landing-breadth-merge.py` already existed for exactly this job
(created 28.10 after the same loss cost an hour of restoring by hand), and the thirteenth block used
it by hand while the trap stayed open. The flag now merges: if the target exists it hands the journal
to that one merge tool and inherits its header recomputation (`controls_sha`, `instrument`), and it
refuses to write and returns 1 if the merge fails. A full measurement asks for the old behaviour
explicitly with `--replace-registry`. **Proven on the failure itself** — one battery
(`landing-page-lang.py --mutate`, 0.7 s) re-measured against the live registry: `добавлено: —`,
`заменено: landing-page-lang.py --mutate`, **62 records before and after**, `controls_sha 196e29dc5405`
and `instrument f37e2dacff66` unchanged, `measured` moved to 29.10. The scenario that lost 60 records
now demonstrably cannot.

**An anchor that gave up on the first miss.** `expected_anchor` took the first `h2`, else the first
`<p>`, in the block. The first `<p>` in a section is the decorative number — `<p class="sec-num">03</p>`
— which is two characters, fails the 12-character floor, and ended the search: the real paragraph
three lines below was never looked at. Every Russian block got its anchor from a `h2` long enough to
pass, so the defect only showed where the heading is short: Vietnamese `subjects`, «Các môn học»,
11 characters. The block was silently skipped — not failed, skipped — and the thirteenth entry saw it
as an empty anchor. The search now walks every match and returns the first line that *qualifies*: a
heading of 8+ characters first, then a paragraph of 12+, then a paragraph of 8+, then a heading of 4+.
A heading wins over a paragraph on purpose — it is the line a person sees — and that is what makes
one ruler for nine languages instead of four languages measured by a sentence and five by a heading
(it moved `parents` in en, ru, es, pt from the sentence to «For parents» / «Родителям» /
«Para padres» / «Para pais», which the other five languages already used).

**A header has no headline, but it does have a name.** `head` carries neither `h2` nor `p`, so its
anchor stayed empty in all nine languages and the block was graded on the language word alone. Its
only text, the same in every language, is the wordmark in the logo: `<a class="brand">…<span>UchiSamBot
</span>`. That is a real anchor — a header swapped for another page, or for another language's header,
cannot show it.

**Measured before the model was asked.** A probe over all 90 section-language pairs (10 marks × 9
languages) compared the old rule with the new one against the built pages: **0 pairs without an
anchor** (was 10: nine `head` plus `vi` `subjects`), **14 anchors changed** — the ten that were empty
filled with real text, and the four `parents` headings above — and 76 unchanged, so no block that had
a strong anchor lost it.

**Then the eye.** `landing-eye.py --sections head,subjects --langs vi,ru,en` against the full frame
set: `PASS` for all three, 0 defects, 0 ungrounded, 0 model-unavailable, two questions per language
and each block graded against its own answer. The raw reply shows the Vietnamese run transcribing the
new anchor verbatim — `HEADLINE: Các môn học` — which is the proof the block is now graded on a line,
not on geometry. The header's own `HEADLINE:` line is `->` (there is no heading to transcribe) and its
`LINE:` is `UchiSamBot`; the verdict quotes the field that has words in it, as the thirteenth entry
required.

**What this does not prove.** That all nine languages pass on these two blocks — three were run
(vi, ru, en), the other six were only proved at the anchor level, and the eye costs a model call per
block per language. That a two-word heading («For parents») is as strong a ground as a full sentence —
it is the same anchor every language now uses, but it is a shorter claim. And that `--resume` with
`--write-registry` is safe in every order: the merge path was proved with a journal of one record, not
with a resumed 55-record journal.

**Files.** `stars-bots-ops/scripts/landing-control-breadth.py` (merge by default, `--replace-registry`);
`stars-bots-ops/scripts/landing-eye.py` (qualifying-line search, two floors, heading first, brand
anchor for `head`); `tools/control-breadth.json` (one record re-measured through the merge path —
the file is now dated 29.10 by its own gate); `evidence/eye-20261029A/`, `evidence/breadth-20261029T012330/`,
`evidence/control-breadth.backup-20261029T012331.json` (`evidence/` stays out of the repo); this entry.
No page, no dictionary, no price file was touched.

## The eye finished the nine: six languages, the same two lines, nothing to fix (29.10.2026, fifteenth block of the day)

**What this block was for.** The one thing the fourteenth entry left standing, named in its own "what
this does not prove": it graded `head` and `subjects` on three languages (vi, ru, en) and left the
other six "only proved at the anchor level, and the eye costs a model call per block per language".
This block pays that cost for the six — hi, id, es, pt, tr, uk — so the two blocks are now eye-graded
in all nine languages.

**The floor underneath.** No page, no dictionary, no tool was edited; this block only looks. The
frames the eye reads are a fresh screenshot of the built pages: `landing-visual-pass.py` over
hi, id, es, pt, tr, uk — **204 checks, 0 failed, 0 problems**, mobile 420 px and desktop 1440 px —
and all twelve loads reported the same structure (7/7 badges, the subject rows, the slider only where
the viewport has one), so the eye is reading the site, not a broken capture.

**Then the eye.** `landing-eye.py --sections head,subjects --langs hi,id,es,pt,tr,uk` against those
frames: **PASS for all six, 0 defects, 0 ungrounded, 0 model-unavailable**. Each verdict transcribes
the line the block actually shows in that language — Hindi «UchiSamBot | और कोई भी स्कूली
सवाल, जहाँ आप अटक जाएँ।», Indonesian «Mata pelajaran sekolah», Spanish «Asignaturas escolares»,
Portuguese «E qualquer outra dúvida escolar em que você fic…», Turkish «Ve takıldığın diğer tüm okul
soruları.», Ukrainian «І будь-яке інше шкільне питання, у якому ти зас…» — which is the proof the grade
rests on a read line, not on geometry. With the three the fourteenth block ran, `head` and `subjects`
now pass the eye in all nine languages.

**What this does not prove.** That the eye replaces a person: it reads the line it is shown and checks
it against the dictionary, so a line that is wrong but self-consistent would still pass. And that the
other sections (hero, band, principle, ref, parents, shots) keep their nine-language coverage on this
exact frame set — they were graded in earlier blocks against earlier frames, and this block re-grades
only the two blocks the fourteenth entry opened.

**Files.** `evidence/visual-20261029/` (six new frame sets: hi, id, es, pt, tr, uk × m/d × the ten
sections); `evidence/eye-20261029B/eye.json` and `log.txt` (the six verdicts and the total line).
`evidence/` stays out of the repo. No page, no dictionary, no tool, no price file was touched. This entry.

## The floor is green, the last frame is shot, and the eye is still grading (29.10.2026, sixteenth block)

The gap the previous entry named — six sections without nine-language coverage on today's frames — is this block's work. It started with the floor: `build.py --check` — 24 files byte-identical to a fresh build; `publish-tree.py --check` — 107 files, 495 internal links, all inside the list; the full sweep — **2948 checks, 0 failures**. Then the frame set was completed: the fifteenth block had shot six languages, and the Vietnamese frames were missing from `evidence/visual-20261029` entirely — a fresh `LANDING_LANGS=vi` visual pass added the twenty missing frames (**34 checks, 0 failures, PROBLEMS 0, 7/7 badges loaded on both viewports**). Nine languages, twenty frames each, one directory.

Then the eye. Here the estimate was wrong, and the ledger records it: `CHUNK=4` frames per question, `max_tokens=3000`, the local Qwen on the graphics card — fifty-four questions (6 sections × 9 languages) is an hour of model time, not the fifteen minutes a six-question batch suggested. The run went over the step budget and was left running in the background (session `proc_e61f38b3b2d9`), writing its verdicts to `evidence/eye-20261029C/eye.json`.

**The next block does this first:** check whether `evidence/eye-20261029C/eye.json` exists. If it does — read the verdicts, fix whatever the eye found, and close the six-section gap on today's frames. If it does not (the background process died with the session) — re-run the eye in three batches of two sections × nine languages (18 questions, about twenty-five to thirty minutes each), one batch per block, never fifty-four at once. The local HTTP server on 8137 was left running for the frame work; a fresh one serves identical files.

**What this does not prove.** That the six sections keep their coverage — that is exactly what the in-flight grading decides, and no block before it may claim it. That a fifty-four-question batch fits a single block — it does not; the budget is per-question, and this entry is the measurement.

## Nine out of nine, and not one line under the green (29.10.2026, sixteenth block, приёмка)

The file the previous entry pointed at was there: `evidence/eye-20261029C/eye.json`, nine rows, `failed 0, ungrounded 0, unavailable 0`, `sections: hero, band, principle, ref, parents, shots`. Every verdict read PASS — and the field beside it, `anchor`, was empty: «опорной строки в HTML нет; подтверждён только язык». The green proved the model could name the language of its own answer. It did not prove the answer had read a single line of the page.

The cause sat in the battery, not the page. `landing-eye.py` computed per-section anchors only when `hero` was absent from the section list. This block bundled all six sections, hero among them, so the anchor branch was skipped for every section at once and each fell into the language-only fallback: a regression that turns "we checked the text" into "we checked the language" without changing the word PASS.

Re-grading the saved answers — no model calls, just the six HEADLINE/LINE pairs each response already carried, against the anchors the pages actually hold — gave **52 of 54**. Both misses were the hero block, `vi` and `uk`, each returning the H1 twice instead of the paragraph. The frames were not the cause: the paragraph is visible and legible on both mobile and desktop hero frames (read by eye, verbatim), single-frame reads returned **26/26 words** on the uk pair, and `vi` passed on an ordinary retry. A pair of frames reads worse than one — consistently for uk, intermittently for vi. A false red, not a page defect, and just as costly as a false green.

Both are fixed and verified in the battery: anchors are now computed for every section including hero (the H1 check stays as an extra condition), and a pair that fails its anchor is re-read one frame at a time, desktop first. The runs: `en/hero` PASS by anchor, 27/27 words; `vi/hero` PASS on retry, 40/40; `uk/hero` PASS on the desktop frame, 26/26; `en` on `band,ref` PASS — the non-hero path unchanged.

**What this does not prove.** That the green on the other five sections rested on text before this entry — it did not, and the re-grade above is the evidence, reproducible without the model. The repaired battery was shown on one language per case; the full nine-language run in its new form has not been repeated.


## Six sections, nine languages, and every green now stands on a line of the page (29.10.2026, seventeenth block, приёмка)

The previous entry named the work: the repaired battery had to be shown on all nine languages and six sections in its new form. That is what this block did - fifty-four questions, two frames each, three batches - and the field the last run left empty is full in every row: `anchor` names two real strings per language (`hero`+`band`, `principle`+`ref`, `parents`+`shots`), and the band anchor is the calling band, not `.principle-band`.

- `evidence/eye-20261029D/eye{A,B}.json` - hero, band: 9 rows, `checked 9, failed 0, ungrounded 0, unavailable 0`, anchors 205-238 characters.
- `evidence/eye-20261029E/eye{A,B}.json` - principle, ref: 9 rows, same totals.
- `evidence/eye-20261029F/eye{A,B}.json` - parents, shots: 9 rows, same totals.
- Anchors audited apart from the PASS line (18 rows, 36 anchors, 0 weak) - a green that does not name its section is the defect this week already produced once.

The technical floor held unchanged in the same run: `landing-sweep.py` **2948 checks / 0 failed**, and `landing-external-links.py` **68 checks / 0 failed / 0 unverified** - the network half the sweep deliberately excludes.

**A measurement that cost one run.** The eye was launched with `nohup ... &` from the cron turn; the child was reaped when the turn closed, and only `en` survived - one PASS line and no output file. Background children do not outlive the turn that started them. The eye now runs in the foreground in batches of five and four languages (ten and eight calls), which fits the six-hundred-second ceiling with room to spare: a batch of ten is two to three minutes, not the twenty-five the earlier estimate guessed.

**What this does not prove.** That the six sections stay covered tomorrow - the frames are today's, and an edit invalidates them without a word. That the eye is a typographic proof - it reads the headline and the line, not the whole paragraph; the paragraph belongs to the dictionary, and the sweep owns it. That hero `vi`/`uk` have healed beyond the retry recorded last entry - they passed here on the ordinary two-frame read, which is the evidence, not a theory.

## The floor, the road to the bot, and the one sentence the policy does not carry (29.10.2026, eighteenth block)

This block took the technique from the outside, because every class the inside already owns came back green in the same run: `build.py --check` - 24 files byte-identical to a fresh build; `publish-tree.py --check` - 107 files, 495 internal links, the list complete in both directions; the full sweep - **2948 checks, 0 failures**; `landing-external-links.py` - **68 addresses, 0 failed, 0 unverified**. Then the live site, byte for byte: all **twelve pages** (nine languages, privacy, terms, 404) returned the same sha256 as the tree, so the publication lag the sweep only samples is zero today.

The road from a page to the bot was walked as a visitor walks it: four Telegram links on every page and **thirty-six distinct source payloads** across the nine languages (`src_landing_<lang>`, `_band`, `_shots`, `_sticky`) - every click is attributable to a language and a block, and no anchor is without one (the three bare `t.me/UchiSamBot` strings on the English page are the JSON-LD block and a CSS `content`). The contact form has no JavaScript-only path either: the native POST carries `redirect={{BASE}}?sent=1#contact-card`, and `#contact-card:target:not(.stale) #contact-ok` shows the confirmation without a script - while a reader who arrives at `#contact-card` from anywhere else sees nothing, which is what the `.stale` guard is for.

Numbers and legal marks: the digit set of each of the nine pages equals the English one; `(EN/RU)` stands three times on every non-English, non-Russian page, and the Russian page goes to `#ru`; the pack price the page prints (24 Stars) is 30 × 0.8, the twenty percent it claims.

**The one sentence that is not there.** `privacy.html` defines "we" as "the team operating UchiSamBot" and names no controller and no address beyond the form - while the same document holds itself out to EU/EEA consumers. Naming the operator is a decision, not a fix: it would put the Nalvorn brand, or a legal entity, on a children's product and an address on the page. It is left to the owner and recorded here so that it is not rediscovered as a surprise.

**What this does not prove.** That the contact form delivers today - the last end-to-end run is 22.10, and Web3Forms answers a server-side probe with "This method is not allowed", so the key can only be exercised from a browser. That the eye read these exact bytes: it did - 180 frames were shot at 04:34 today, the pages last changed on 28.10 at 16:55, and nothing in the tree moved after them.


## The letter that finally arrived, and the four batteries that were already green (29.10.2026, nineteenth block)

Block eighteen left one sentence standing as unproven: that the contact form delivers today. The last end-to-end run was 22.10, Web3Forms answers a server-side probe with "This method is not allowed", and the key can only be exercised from a browser. That is what this block did, on the live site, with a real Chrome and a real letter.

**The path, walked end to end.** Chrome 151 on CDP `:9223`, the live Russian page, the form filled and submitted by a person's path rather than a POST: `landing-contact-e2e.py --live --lang ru` - **13 checks, 0 failed**, stamp `2026-10-29 07:37:23` written into the message text. Then the inbox, not the code: `landing-contact-delivery.py --stamp "2026-10-29 07:37:23" --since-minutes 20` - letter `1a18629c3b66b281`, arrived 0 minutes old, sender `UchiSamBot website <notify+v835qy@web3forms.com>`, the stamp and the test address both matching. The four states around it are unchanged and re-measured offline: `landing-contact-e2e.py` without `--live` - **910 checks, 0 failed** across nine languages (action, method, key, hidden fields, per-language redirect, field types and labels, honeypot out of the tab order, native validation, `?sent=1` confirmation in the page's own language, the no-JS path that leaves the form visible).

**Why "arrived" is a stronger word than it was on 24.10.** The search that found this letter is a plain subject search, and a plain search does not see the spam folder. On 24.10 the same battery printed green and the letter was sitting in spam, found only later with `in:spam`. Today's letter was visible to the ordinary search, so it reached the inbox. That is one letter on one day, not a reputation.

**The floor, unchanged, in the same run.** `build.py --check` - 24 files byte-identical to a fresh build; `publish-tree.py --check` - 107 files, 495 internal links, list complete in both directions; `landing-sweep.py` - **2948 checks, 0 failed**; `landing-external-links.py` - **68 addresses, 0 failed, 0 unverified**; `landing-price-parity.py` - 9 checks, 0 discrepancies (24 Stars is 30 x 0.8, the twenty percent the page claims).

**Frames and the eye.** `landing-visual-pass.py` shot fresh frames for all nine languages at 420 px and 1440 px - **306 checks, 0 problems** (no horizontal overflow outside the slider, no clipped text, 7/7 badges loaded on every page, badge rows 4+3). `landing-eye.py` then graded the contact section on three languages against those frames - `ru`, `en`, `hi`, **3 pairs, 0 defects, 0 ungrounded** - and each PASS names the headline it actually read: "Есть вопрос или отзыв?", "Questions or feedback?", "कोई सवाल या सुझाव है?". Evidence: `evidence/visual-20261029-nineteen/`, `evidence/block-20261029-nineteen/eye-contact.json`.

**What this does not prove.** That a stranger's browser will deliver: the run used our machine, our address and our IP, so it proves the path, not the deliverability across providers. That Gmail's classification is stable - one letter, one day, after a week of the same letters being filed as spam on 24.10. That the double-send guard holds when a visitor's extension blocks `fetch` - unchanged from 24.10, where a blocked request leaves the text in the box and the honest "not sent" line. That the operator named in `privacy.html` exists - still the one sentence this policy does not carry, and still the owner's decision. Nothing in the tree was edited by this block: it measured, and every number above came back the number it already was.

## The referral sentence promises without the ceiling the bot enforces (29.10.2026)

The floor first, unchanged in the same run: `build.py --check` - 24 files byte-identical to a
fresh build; `publish-tree.py --check` - the file list complete in both directions, 495 internal
links; `landing-sweep.py` - **2948 checks, 0 failed**; `landing-bot-profile.py` - **29 checks, 0
failed** against the live Bot API; `landing-price-parity.py` - **9 checks, 0 discrepancies** with
`bot/payments.py`.

**The candidate that was not a defect.** `tools/bot-profile.json` says the Russian profile names
`русский` among its subjects while `tools/subjects.json` names `Английский язык`, and the registry's
own note calls `русский` the exact word that made the 24.10 pass red in eight languages. Read on:
the sentence closes the same way in all nine dictionaries (`subj.note`, nine of nine files) - "And
any other school question you are stuck on" / "И любой другой школьный вопрос, где ты застрял". The
24.10 defect was a translator putting the *page's own language* where the canon names a *school
subject*; a hand-written Russian sentence naming a Russian school subject is an example of that
clause, not a mistranslation of the canon. Left alone, and written down here so a later pass does
not "fix" the owner's word into a translation.

**The one that is.** `ref.text` in all nine languages promises the visitor "you get one more free
breakdown" per friend, with no ceiling in any of the nine. The bot has one: `REFERRAL_MAX_CREDITS`
= 20 (`bot/payments.py:43`), enforced at `bot/storage.py:298` - from the twenty-first credited friend
the referrer gets nothing while the page still says they will. Same class as the "five" the
dictionary promised on 23.10 while the bot gave two, only the other way round: the page is kinder
than the product. **Not fixed in this block**: the fix is nine sentences plus the referral answer in
the FAQ, and nine translations written in a hurry are the exact defect three days of this
repository were spent removing. The order for the next block: state the ceiling in `ref.text` of
all nine from the bot's own constant, then add two parity checks - `ref.text` carries no numeral
other than the one, and wherever the ceiling is claimed the number equals `REFERRAL_MAX_CREDITS`.

**What this does not prove.** That twenty friends is the right ceiling - that is a product
decision, not a measurement. That no language casually promises something else in prose the
batteries do not key on: this block read one promise in nine languages, not all of them.

## The promise got the ceiling the product already had, and the number now comes from the constant (29.10.2026, twentieth block)

**What was wrong.** The order the previous entry left was executed as written: `ref.text` in all
nine dictionaries names the ceiling, and the number is not typed nine times - `landing-price-parity.py`
reads `REFERRAL_MAX_CREDITS` out of `bot/payments.py` and demands the same number in all nine
sentences. The unit is the one the Terms already use: **bonus** breakdowns, not "free breakdowns in
total", because the bonus sits on top of the two free trials and "20 free in total" would have
shrunk the page's own offer to 18 bonus ones. EN: *"Invite a friend — when they solve their first
task, you get one more free breakdown. Up to 20 bonus breakdowns in total."* The other eight say
the same sentence in their own words; every one carries exactly one number, 20.

The FAQ has no referral answer to correct - a grep of all nine dictionaries for friend / referr /
invite returns one line, `ref.text` itself - so the second half of the previous block's guess was a
claim about a text that does not exist. Nothing was added to the FAQ: a new question is content,
not a fix for a promise.

**Two checks, one control.** `landing-price-parity.py` grew from 9 to 11: *«реферал ref.text x9:
чужих чисел нет»* (no numeral in the sentence other than the bonus and the ceiling - a translator
writing "3 friends" or "50 breakdowns" turns it red) and *«реферал ref.text x9: потолок ==
REFERRAL_MAX_CREDITS»* (each of the nine names the ceiling **and** the word that makes it a ceiling
- Up to / не больше / Hasta / Até / कुल मिलाकर / Maksimal / en fazla / tối đa / не більше). The
first version of the first check also required *some* number to be present, and the negative
control caught it: deleting the ceiling made two rows red instead of one, and the control refuses a
measurement that cannot name the single defect. Presence belongs to the ceiling check; the other
check owns foreign numerals only. `--mutate reftext` copies the landing's dictionaries, deletes the
ceiling from `en.json` and requires exactly one red, naming 20: **подмен 1, провалов 1, поймано
ровно одно утверждение**.

**The floor.** `build.py --check` - 24 files byte-identical to a fresh build; `publish-tree.py
--check` - 107 files, 495 internal links, the list complete both ways; `landing-sweep.py` - **2948
checks, 0 failures** after the live site was republished from `gh-pages` to both mirrors;
`landing-price-parity.py` - **11 checks, 0 discrepancies**. The submission kit was regenerated
because its manifest hashes `en.json`: 4 cards 1920x1080, 10 inputs matched.

**What this does not prove.** That the nine sentences read naturally to a native speaker - they were
written by the same hand that wrote the previous nine, and the eye has not graded this band yet.
That 20 is reachable in practice: the ceiling is the bot's, the page now repeats it, and nobody has
counted whether twenty credited friends ever happened. That other prose on the page names numbers
the batteries do not key on - this block pinned one sentence, not the dictionary.

## The hero was read nine times, and the battery compared it with a dash (29.10.2026, приёмка двадцать первого блока)

The previous run committed nothing but a message: it measured, and left every page byte-identical. Its one open item said the eye had refused the hero headline in all nine languages - "the frame pair, not the page" - with an order to re-shoot the hero full width.

The frames were not the problem, and neither was the page. In every one of the nine raw answers the model had already read the hero headline correctly: `Homework that finally makes sense`, `Домашка, яка нарешті стає зрозумілою`, and the other seven. What the battery compared it with was a dash.

The run asked two sections in one pass, `ref` first. The referral band carries no headline, and the model honestly answered `HEADLINE: ->` for it. `parse()` kept `->` as a headline, the bundle's "first non-empty headline" became that dash, and the hero H1 was graded against it - nine ungrounded verdicts sitting on a live, readable headline in the same file.

Fixed in `landing-eye.py`: placeholder values (`->`, `—`, `none`, `нет`) are neither headlines nor lines. Re-grading the same saved answers, without a single model call, gives **H1 read 9 of 9, 100%** in every language. The hero paragraph - the anchor - reads in **6 of 9**; `ru`, `hi` and `uk` returned the H1 twice instead of the paragraph, the pair-of-frames flakiness already recorded today for `vi`/`uk`, not a page defect: the paragraph is in the HTML and legible in both frames, read by eye.

**What this does not prove.** That the three paragraph misses are gone - they belong to the model, not the page, and the single-frame retry did not catch them this time. That the next bundled run keeps the fix - the placeholder list is a list, and the next dash the model invents is a new case.

**A process note.** This run committed an empty commit with the report in its message, so the diary had no entry for it and the "last entry" a reader finds was the twentieth block's. A message is not a changelog entry; every run owes the diary a dated one.

## The contact band answered in nine, and the listing outside still promises five (29.10.2026, приёмка двадцать второго блока)

**What was asked.** One block, in order: technique, then the eye, then what the words promise.

**Technique.** `landing-sweep.py` — **CHECKS: 2948, FAILED: 0, ALL PASS**: the nine pages byte-stable against a fresh build, per-language weight budgets, the external-address ledger, the 84-cell page canary, the publish list, and live parity with the tree. Nothing in the technical set moved, and nothing needed to.

**The eye, on the two bands it had read least.** `head` and `contact` stood at four and two readings. The frames of the twenty-first block (`evidence/visual-20261029-twentyone`, 180 frames at 420 and 1440 px) still hold both sections in all nine languages, and they are current: no page byte has moved since 09:04, the frames were shot at 10:11. `landing-eye.py` read them: **9 of 9 grounded, 0 defects, 0 unavailable**. The contact headline came back as written in each language — `Questions or feedback?`, `Есть вопрос или отзыв?`, `¿Preguntas o comentarios?`, `कोई सवाल या सुझाव है?`, `Ada pertanyaan atau masukan?`, `Sorunun ya da geri bildirimin var mı?`, `Có câu hỏi hoặc góp ý?`, `Є питання чи відгук?` — and the anchor line matched on all nine. Since the twenty-first block's parser fix, a dash can no longer stand in for a headline.

**What the contact band promises, read in nine dictionaries.** Every language says the same three things: the message reaches the team, the answer goes to the visitor's email, the email is used only for that answer, no mailing lists; and both refusal lines promise the text stays in the box. That promise is now a battery rather than a reading: `landing-contact-e2e.py --failures` — **CHECKS: 442, FAILED: 0 (88 s)** — four refusal modes per language (connection aborted, 500, 429, and HTTP 200 carrying `success:false`, the dangerous one) each show the refusal line in the page's own language, keep the textarea's text, re-enable the button with its own label, put focus on the alert and send exactly one POST.

**The badge row, read from outside.** Five of the six badge addresses answer 200 and name UchiSamBot on the page they land on (fazier, startupbase, showmebest, lift-off, auraplusplus). `startupfa.me/s/-51` answered **429** — its edge rate-limits a series of requests from one address, the same behaviour recorded on 17.10; not proof the listing is gone, and not proof it is alive either.

**One thing this block found outside the page.** The LiftOff listing, read as an article, still tells the visitor *"Your first 5 breakdowns are free"*, *"Interface languages: Russian and English"* and five subjects. The page and the bot say **two** free breakdowns and nine languages. The page is right — its `q4a` and `cta.sub` are tied to `tools/claims.json` and to the bot's own constant — while the listing was written earlier and cannot be corrected from this repository: it needs an edit on the platform, under the owner's account. Named here so the next reader does not learn it from a visitor.

**What this does not prove.** That a person looked at the frames — the eye is the local model reading saved frames. That the 429 is a rate limit rather than a delisting. That the other five listings say what the page says: only LiftOff was read as an article, the other four were counted for the name and nothing more.

**Files.** This entry only; no site file was touched, so nothing moves in `gh-pages`. The push is a main-branch journal push to both mirrors.

## Five listings promise five, and the page promises two (29.10.2026, приёмка: проверка снаружи)

The entry above read one listing and left five unread: *"That the other five listings say what the page says — only the bot's name was checked, not the text."* Read from outside, with a browser user agent, the answer is worse than the open question.

All five reachable pages carry the same stale text. LiftOff, StartupBase, Fazier, ShowMeBestAI and Aura++ each promise **five** free breakdowns (the page and the bot credit **two**), each name **Russian and English** as the interface languages (the site ships **nine**), and the subject list still leads with *Russian language* where the canon leads with English. The sixth, Startup Fame, answers **429** — a rate limit at its edge, so its text can be neither confirmed nor denied today.

That is not a typo on one page; it is every door telling the visitor a different product from the room behind it. The site is the only surface that is right, and it is the one surface the owner controls directly.

Nothing in the tree changed: listings are edited by hand under the owner's accounts. What this check left behind is one paste per platform — a long description, a short one and a one-line variant, all built from the shipped facts (two free, 30/120/300 Stars at 20% and 33%, nine languages, the step-before-the-answer rule) and keeping each platform's own UTM tag.

**What this does not prove.** That Startup Fame's listing is stale — 429 is not a text. That any platform accepts the replacement — none of the five was edited, and each may cap length or refuse links.

## The range promised a letter, the file had no glyph for it (29.10.2026, приёмка двадцать третьего блока)

**What was asked.** One block, in order: technique, the eye, the words. This run took technique first.

**Technique, re-measured rather than assumed.** `landing-sweep.py` — **CHECKS: 2948, FAILED: 0, ALL PASS** before any edit: nine pages byte-stable against a fresh build, weight budgets, the external-address ledger, the 84-cell canary, the publish list, live parity. Redirects, read from outside for the first time as a matrix: `http://` → **301** to `https://`, `/uchisambot` → **301** to `/uchisambot/`, `/ru` → **301** to `/ru/`, `/uchisambot/` → **200**, `/uchisambot/nonexistent-x9` → **404** (a real one, not a soft 200). `/uchisambot/index.html` answers **200** — a second address for the same page, which GitHub Pages will not redirect; the canonical is self-referential and points at the slash form, so the duplicate is named, not a defect.

**A structural reading that had no gate.** On all eleven shipped pages, ids are unique, every `href="#…"` lands on an existing id, and every `aria-labelledby`/`aria-describedby`/`aria-controls` target exists: **0 duplicates, 0 dangling anchors, 0 dangling aria targets**. This was read once, by hand, and left behind nothing — noted as a gap, not celebrated.

**The gate this block added.** The sweep already asked whether every character of the page text falls inside a declared `unicode-range`. It never asked whether the file behind that range has the glyph. Those are different questions, and only one of them is true by construction: a face that *claims* `U+0451` wins the character, and if the subset was cut too deep the browser takes `.notdef` from that file and never falls back to a system font. Range green, square on the screen, nobody the wiser — the same shape as the caption defect of 23.10, which is why the caption gate exists at all; the page had no equivalent.

Asked of the files themselves with `fc-scan` (FreeType reads woff2; the sweep still needs no fontTools and no brotli), the answer across the nine pages is every declared character has a real glyph: **en 28, ru 75, es 35, hi 79, id 28, pt 38, tr 38, uk 74, vi 85 non-ASCII characters, 0 without a glyph** in the face that claims them. The gate carries a self-test on the two-glyph `langs-vietnamese.woff2` — `U+1EBF` present, `U+0061` absent — so a reader that cannot say "no" fails loudly instead of passing by emptiness. Sweep is now **CHECKS: 2959, FAILED: 0** (+9 languages, +404, +self-test).

**What this does not prove.** That ASCII is covered — the gate reads only non-ASCII on purpose, because the Latin base cut is the one every screenshot in this repository has already exercised. That a glyph is *drawn well*: `fc-scan` reports presence, not shape, and the eye's green covers legibility only for the sections it has read. That the four pages we cannot reach (Startup Fame's 429) say what the page says.

**Files.** `landing-sweep.py` only; no site file was touched, so nothing moves in `gh-pages` and the live bytes are unchanged by this block.

## The page promised anchors nobody was asking about, and three documents nobody had ever looked at (29.10.2026, приёмка двадцать четвёртого блока)

**What was asked.** One block, in order: technique, the eye, the words. This run took the technique and the first measurement of the documents the eye cannot reach.

**The gap this block inherited, in its own words.** The entry above read the structure by hand — unique ids, every `href="#…"` landing on an id, every `aria-*` target existing — got `0 / 0 / 0`, and wrote down: *"This was read once, by hand, and left behind nothing — noted as a gap, not celebrated."* That is the whole problem in one line. A browser says nothing when `#цена` has no target: the click does nothing, no console error, the visitor thinks the link is broken and the maintainer never learns. `aria-labelledby` pointing at a missing id is worse — it is not an error either, it is an empty accessible name, and the screen reader announces nothing at the one place the page meant to explain itself. A promise to the browser that nobody checks is a promise.

**The device, and the device's own lie detector.** `_Struct` reads one document: id counts, in-document anchors, `aria-labelledby` / `aria-describedby` / `aria-controls` targets. Before it is allowed to grade the site it is fed two synthetic documents — a dirty one carrying exactly three violations (duplicated id, dead anchor, dead aria target) and a clean one carrying none but holding a valid anchor, a valid aria triple and `href="#"` (top of page, which is not a missing target). It must return 3 and 0. A reader that cannot say no passes by emptiness, and emptiness is what a broken parser returns.

**The class it found by itself.** Reading the pages, the same device collected a shape it had not been built for: `../privacy.html#ru` — an anchor that lives in another file. Ten of the eleven documents carry none, Russian carries two (policy and terms). A second function resolves the file, then the fragment inside it; its control runs on the live files, not on a string: `privacy.html#ru` must come back clean, `privacy.html#no-such-anchor-x9` must come back as exactly one problem. Both do.

**The numbers.** Eleven shipped documents — nine languages, the English root, and the 404. Every language page: **23 ids, 6 anchors, 2 aria targets**, no duplicates, nothing dangling. The 404 page has **zero of all three**, and that zero is a fact about the document, not a hole in the reader: it is a four-kilobyte page with no navigation. Sweep went from **CHECKS: 2959** to **CHECKS: 2981, FAILED: 0** — twenty-two new checks: two controls and twenty verdicts (eleven documents × two questions), all green on the first honest run.

**The floor underneath, re-measured.** `tools/build.py --check` — 24 files byte-identical to a clean build. `tools/publish-tree.py --check` — list complete, nothing extra, 495 internal links all inside the list.

**Three documents nobody had looked at.** Every frame in this repository is of the main page. `privacy.html`, `terms.html` and `404.html` have been shipped since the beginning and were never shot, never measured, never read — and the policy is exactly what a careful person opens *before* paying, while the 404 is what a lost one gets. New battery `landing-legal-pages.py`, three documents at 420 and 1440 px, seven clauses each: document wider than the window, a leaf element past the right edge, text clipped by its own box, script errors, `<html lang>` present, exactly one non-empty `h1`, the heading set in the page's own face and not the fallback, and contrast of every text block 14 px and up against its real background at 4.5:1. **CHECKS: 42, PROBLEMS: 0, 6 frames** (`evidence/legal-20261029`). The control `--mutate` injects a 120 px strip beyond the right edge: **6 of 6** flagged `H-OVERFLOW doc=540 cw=420` / `doc=1560 cw=1440`, exit 0, `ПОЙМАЛ`; the clean re-run then replaced the doctored frames, so the ones on disk are of the page as shipped.

**What this does not prove.** That a person looked — this block measured geometry, fonts and contrast, it did not read legibility; the eye has no anchor on the legal pages, and asking it without one is the false green of the sixteenth block, where nine of nine `PASS` proved only that the model could name a language. That the legal texts are legally sound — nobody in this repository is a lawyer. That contrast covers text below 14 px, text over images, or hover states. That `aria-*` targets are the *right* ones: this device proves the id exists, never that it names the control.

**Left for the next block.** Give `landing-eye.py` a mark for the legal documents (the `h1` of each, which is stable and unambiguous) so the eye can read `privacy`, `terms` and `404` the way it reads the ten index sections — and then the same for the six external listing pages whose text still promises five free breakdowns and two languages.

**Files.** `landing-sweep.py` (+2 gates, +1 control) and the new `landing-legal-pages.py`, both in the skill tree; this README entry. No site file was touched, so nothing moves in `gh-pages` and the live bytes are unchanged by this block.

