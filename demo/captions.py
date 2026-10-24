#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The hero loops' baked captions: one source, one ledger.

The nine 13 s hero loops carry two step captions drawn into the pixels
(drawtext). Until 22 Oct 2026 those strings were hand-copied literals inside
`demo/build-web-loop-langs.sh` and `demo/build-web-loop-ru.sh` (and the EN loop
came from the submission kit), while the same words live in the page
dictionaries. A translator could reword `how.s2t` and the video would keep the
old wording silently — the page and the video are two faces of one promise.

Now:
  cap1 = "2<sep> <how.s2t> — <tail>"     (tail = video-only wording: "text or photo")
  cap2 = "3<sep> <shot3.alt without the brand>"
  sep  = "·", except hi where the Devanagari font has no U+00B7, so "."

`--ledger` writes `demo/captions.json`: the exact strings baked into each loop
plus the loop's sha256 and byte count. The QA sweep (`landing-sweep.py`) fails
when the dictionary and the ledger disagree, or when a loop's bytes are not the
ones the ledger describes — i.e. a re-cut video that nobody re-stamped.

Usage:
    python3 demo/captions.py cap1 <lang>        # print one caption
    python3 demo/captions.py cap2 <lang>
    python3 demo/captions.py full <lang> <1-4>  # the 35 s demo's scene captions
    python3 demo/captions.py check              # compare ledger with dictionaries
    python3 demo/captions.py ledger [lang ...]  # rewrite the ledger (after a rebuild)

The full 35 s demos (`demo/uchiambot-demo.mp4`, `-ru.mp4`, linked from llms.txt
and the launch platforms) carry the same two middle captions plus an intro and an
outro. Their intro tagline is `foot.tag` and their outro promise is `hero.chip1` —
both dictionary keys — because the outro used to say "5 free step-by-step
solutions" while the product gives two and the page says two. Scenes 1 and 4 and
the two outro buttons are video-only wording, listed in `FULL_ONLY`.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / 'src' / 'locales'
LEDGER = ROOT / 'demo' / 'captions.json'

LANGS = ['en', 'ru', 'es', 'pt', 'hi', 'id', 'tr', 'vi', 'uk']

# Video-only tail of the "send a task" scene. It is not a dictionary key: on the
# page the same idea is a sentence (how.s2d), not a label. Kept here so the tail
# has exactly one copy too.
TAIL = {
    'en': 'text or photo',
    'ru': 'текстом или фото',
    'es': 'texto o foto',
    'pt': 'texto ou foto',
    'hi': 'टेक्स्ट या फोटो',
    'id': 'teks atau foto',
    'tr': 'yazı ya da fotoğraf',
    'vi': 'chữ hoặc ảnh',
    'uk': 'текстом або фото',
}

# shot3.alt ends (or, for hi/tr, starts) with the brand; the caption is the label
# without it. Per language, because the preposition is part of the language.
BRAND = {
    'en': r'\s+from\s+UchiSamBot$',
    'ru': r'\s+от\s+UchiSamBot$',
    'es': r'\s+de\s+UchiSamBot$',
    'pt': r'\s+do\s+UchiSamBot$',
    'hi': r'^UchiSamBot\s+से\s+',
    'id': r'\s+dari\s+UchiSamBot$',
    'tr': r"^UchiSamBot'tan\s+",
    'vi': r'\s+từ\s+UchiSamBot$',
    'uk': r'\s+від\s+UchiSamBot$',
}
BRAND_PREFIX = {'hi', 'tr'}          # brand first -> the label needs a capital
# Number-to-caption joiner: "2 · text" everywhere, "2. text" for hi (no U+00B7 in
# the Devanagari subset).
JOINER = {'hi': '. '}
DEFAULT_JOINER = ' · '

VIDEO = {'en': 'uchiambot-demo-web.mp4'}

# The 35 s demos: scene 1, scene 4, and the two outro button lines are video-only.
# Scene 2 = the hero loop's cap1, scene 3 = its cap2, the intro tagline is
# foot.tag and the outro promise is hero.chip1 — those four come from the
# dictionaries, so the demo cannot promise a different product than the page.
FULL = {'en': 'uchiambot-demo.mp4', 'ru': 'uchiambot-demo-ru.mp4'}
FULL_ONLY = {
    'en': {'c1': 'Your AI study helper',
           # 24.10.2026: was "Works in Russian and English" while the page says nine
           # languages (hero.chip3, shots.cap, FAQ q3a) and the bot answers in nine
           # (ANSWER_LANG). The scene now shows the real /lang picker with nine rows.
           'c4': 'Works in 9 languages',
           'outro_t': 'Try it for free',
           'outro_cta': 'Open @UchiSamBot',
           'outro_where': 'in Telegram'},
    'ru': {'c1': 'Твой помощник по учёбе',
           'c4': 'Работает на 9 языках',
           'outro_t': 'Попробуй бесплатно',
           'outro_cta': 'Открой @UchiSamBot',
           'outro_where': 'в Telegram'},
}


def video_name(lang):
    return VIDEO.get(lang, f'uchiambot-demo-web-{lang}.mp4')


def dictionary(lang):
    return json.loads((LOCALES / f'{lang}.json').read_text(encoding='utf-8'))


def label(lang):
    """shot3.alt without the brand, capitalised when the brand led the phrase."""
    alt = dictionary(lang)['shot3.alt']
    stripped = re.sub(BRAND[lang], '', alt).strip()
    if stripped == alt:
        raise SystemExit(f'{lang}: shot3.alt does not carry the brand ({alt!r}) — '
                         'update the BRAND regex in demo/captions.py')
    if lang in BRAND_PREFIX:
        stripped = stripped[0].upper() + stripped[1:]
    return stripped


def caption(lang, scene):
    d = dictionary(lang)
    join = JOINER.get(lang, DEFAULT_JOINER)
    if scene == 1:
        return f"2{join}{d['how.s2t']} — {TAIL[lang]}"
    if scene == 2:
        return f"3{join}{label(lang)}"
    raise SystemExit(f'unknown scene {scene!r} (1 or 2)')


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def poster_name(lang):
    return 'demo-poster.webp' if lang == 'en' else f'demo-poster-{lang}.webp'


def shot_name(lang, n):
    """The two page screenshots a loop is cut from (24.10.2026).

    The loop's source used to be an external kit capture or a .shots-work render,
    so redrawing a screenshot left the video untouched: after the 23.10 menu fix
    nine loops still showed six buttons under a page that drew seven. A loop is
    now cut from exactly the file the page displays, and its sha256 goes into the
    ledger — a new screenshot with an old loop is a sweep failure, not silence.
    """
    return f'shot{n}.webp' if lang == 'en' else f'shot{n}-{lang}.webp'


def scene_path(lang, n):
    """Full-demo scene N: 1-3 are the page screenshots, 4 is the /lang mockup.

    Scene 4 is not on the page (the page shows three shots), so it lives next to
    the generator that draws it, in tools/shots-gen/scenes/. It used to come from
    submission-kit-20261014 and showed two languages under a caption that promised
    two, while the page and the bot answer in nine (24.10.2026).
    """
    if n == 4:
        name = 'shot4.webp' if lang == 'en' else f'shot4-{lang}.webp'
        return ROOT / 'tools' / 'shots-gen' / 'scenes' / name
    return ROOT / 'img' / shot_name(lang, n)


def scene_source(lang, n):
    """What the ledger records: scenes 1-3 are named by the page's own file name,
    scene 4 by its path from the repo root (it lives outside img/)."""
    if n == 4:
        return str(scene_path(lang, n).relative_to(ROOT))
    return shot_name(lang, n)


def full_caption(lang, scene):
    """Scene captions of the 35 s demo (1 intro-follower, 2 send, 3 breakdown, 4 languages)."""
    d = dictionary(lang)
    join = JOINER.get(lang, DEFAULT_JOINER)
    extra = FULL_ONLY[lang]
    if scene == 1:
        return f'1{join}{extra["c1"]}'
    if scene == 2:
        return f'2{join}{d["how.s2t"]} — {TAIL[lang]}'
    if scene == 3:
        return f'3{join}{label(lang)}'
    if scene == 4:
        return f'4{join}{extra["c4"]}'
    raise SystemExit(f'unknown full-demo scene {scene!r} (1..4)')


def full_intro_tag(lang):
    return dictionary(lang)['foot.tag']


def full_outro_sub(lang):
    return dictionary(lang)['hero.chip1']


def build_ledger(langs=None, full=None):
    langs = langs or LANGS
    full = full if full is not None else list(FULL)
    old = {}
    if LEDGER.exists():
        doc = json.loads(LEDGER.read_text(encoding='utf-8'))
        old = doc.get('langs', {})
        old_full = doc.get('full', {})
    else:
        old_full = {}
    out = {'version': 2,
           'note': 'Written by demo/captions.py — the exact captions baked into '
                   'each hero loop and each full demo, plus the file bytes. Re-stamp '
                   'after a rebuild; landing-sweep.py fails when this disagrees with '
                   'the dictionaries or with the files.',
           'langs': old, 'full': old_full}
    for lang in langs:
        path = ROOT / 'demo' / video_name(lang)
        poster = ROOT / 'img' / poster_name(lang)
        if not path.exists():
            raise SystemExit(f'missing loop: {path}')
        if not poster.exists():
            raise SystemExit(f'missing poster: {poster} (a loop is never rebuilt '
                             'without its poster — the page shows it before play)')
        out['langs'][lang] = {
            'video': video_name(lang),
            'sha256': sha256(path),
            'bytes': path.stat().st_size,
            'sources': {
                'shot2': shot_name(lang, 2),
                'shot2_sha256': sha256(ROOT / 'img' / shot_name(lang, 2)),
                'shot3': shot_name(lang, 3),
                'shot3_sha256': sha256(ROOT / 'img' / shot_name(lang, 3)),
            },
            'poster': poster_name(lang),
            'poster_sha256': sha256(poster),
            'poster_bytes': poster.stat().st_size,
            'joiner': JOINER.get(lang, DEFAULT_JOINER),
            'tail': TAIL[lang],
            'cap1': caption(lang, 1),
            'cap2': caption(lang, 2),
            'keys': {'cap1': 'how.s2t', 'cap2': 'shot3.alt'},
        }
    for lang in full:
        path = ROOT / 'demo' / FULL[lang]
        if not path.exists():
            raise SystemExit(f'missing full demo: {path}')
        out['full'][lang] = {
            'video': FULL[lang],
            'sha256': sha256(path),
            'bytes': path.stat().st_size,
            'sources': {
                'shot1': shot_name(lang, 1),
                'shot1_sha256': sha256(ROOT / 'img' / shot_name(lang, 1)),
                'shot2': shot_name(lang, 2),
                'shot2_sha256': sha256(ROOT / 'img' / shot_name(lang, 2)),
                'shot3': shot_name(lang, 3),
                'shot3_sha256': sha256(ROOT / 'img' / shot_name(lang, 3)),
                'shot4': scene_source(lang, 4),
                'shot4_sha256': sha256(scene_path(lang, 4)),
            },
            'caps': {str(n): full_caption(lang, n) for n in (1, 2, 3, 4)},
            'intro_tag': full_intro_tag(lang),
            'outro_sub': full_outro_sub(lang),
            'keys': {'intro_tag': 'foot.tag', 'outro_sub': 'hero.chip1',
                     'caps.2': 'how.s2t', 'caps.3': 'shot3.alt'},
        }
    LEDGER.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n',
                      encoding='utf-8')
    return out


def check():
    led = json.loads(LEDGER.read_text(encoding='utf-8'))['langs']
    bad = 0
    for lang in LANGS:
        if lang not in led:
            print(f'FAIL {lang}: not in the ledger')
            bad += 1
            continue
        row = led[lang]
        for scene, key in ((1, 'cap1'), (2, 'cap2')):
            want = caption(lang, scene)
            if row.get(key) != want:
                print(f'FAIL {lang}:{key} ledger={row.get(key)!r} dictionary={want!r}')
                bad += 1
        path = ROOT / 'demo' / row['video']
        if not path.exists():
            print(f'FAIL {lang}: {path.name} is gone')
            bad += 1
        elif sha256(path) != row['sha256']:
            print(f'FAIL {lang}: {path.name} is not the file the ledger describes '
                  f'(sha256 differs) — rebuild the loop and re-stamp')
            bad += 1
        if 'poster_sha256' not in row:
            print(f'FAIL {lang}: the ledger has no poster stamp — rebuild and restamp')
            bad += 1
            continue
        poster = ROOT / 'img' / row.get('poster', poster_name(lang))
        if not poster.exists():
            print(f'FAIL {lang}: {poster.name} is gone')
            bad += 1
        elif sha256(poster) != row['poster_sha256']:
            print(f'FAIL {lang}: {poster.name} was not made from this loop '
                  f'(poster sha256 differs) — rebuild the loop, it refreshes the poster')
            bad += 1
        # 24.10.2026: the loop must be cut from the screenshot the page shows now.
        src = row.get('sources')
        if not src:
            print(f'FAIL {lang}: the ledger names no screenshot sources — rebuild and restamp')
            bad += 1
            continue
        for n in (2, 3):
            name = shot_name(lang, n)
            shot = ROOT / 'img' / name
            if not shot.exists():
                print(f'FAIL {lang}: {name} is gone')
                bad += 1
            elif src.get(f'shot{n}') != name:
                print(f'FAIL {lang}: the ledger says the loop was cut from '
                      f'{src.get(f"shot{n}")!r}, the page shows {name!r} — rebuild the loop')
                bad += 1
            elif sha256(shot) != src.get(f'shot{n}_sha256'):
                print(f'FAIL {lang}: {name} was redrawn after the loop was cut '
                      f'(sha256 differs) — the video still shows the old picture; '
                      f'rebuild it: bash demo/build-web-loop-langs.sh {lang}')
                bad += 1
    doc = json.loads(LEDGER.read_text(encoding='utf-8'))
    for lang in FULL:
        row = doc.get('full', {}).get(lang)
        if not row:
            print(f'FAIL {lang}: the full demo is not in the ledger — rebuild and restamp')
            bad += 1
            continue
        for n in (1, 2, 3, 4):
            want = full_caption(lang, n)
            if row.get('caps', {}).get(str(n)) != want:
                print(f'FAIL {lang}:full{n} ledger={row.get("caps", {}).get(str(n))!r} '
                      f'dictionary={want!r}')
                bad += 1
        for field, want in (('intro_tag', full_intro_tag(lang)),
                            ('outro_sub', full_outro_sub(lang))):
            if row.get(field) != want:
                print(f'FAIL {lang}:{field} ledger={row.get(field)!r} dictionary={want!r}')
                bad += 1
        path = ROOT / 'demo' / row['video']
        if not path.exists():
            print(f'FAIL {lang}: {path.name} is gone')
            bad += 1
        elif sha256(path) != row['sha256']:
            print(f'FAIL {lang}: {path.name} is not the file the ledger describes '
                  f'(sha256 differs) — rebuild the full demo and re-stamp')
            bad += 1
        src = row.get('sources') or {}
        for n in (1, 2, 3, 4):
            want = scene_source(lang, n)
            shot = scene_path(lang, n)
            if src.get(f'shot{n}') != want or not shot.is_file():
                print(f'FAIL {lang}:full the ledger does not point scene {n} at {want}')
                bad += 1
            elif sha256(shot) != src.get(f'shot{n}_sha256'):
                print(f'FAIL {lang}:full {want} was redrawn after the demo was built — '
                      f'rebuild it: bash demo/build-full-demo.sh {lang}')
                bad += 1
    print(f'ledger: {len(LANGS)} loops + {len(FULL)} full demos, {bad} problem(s)')
    return 1 if bad else 0


def main(argv):
    if len(argv) >= 3 and argv[1] in ('cap1', 'cap2'):
        print(caption(argv[2], 1 if argv[1] == 'cap1' else 2))
        return 0
    if len(argv) >= 4 and argv[1] == 'full':
        print(full_caption(argv[2], int(argv[3])))
        return 0
    if len(argv) >= 3 and argv[1] == 'full-intro':
        print(full_intro_tag(argv[2]))
        return 0
    if len(argv) >= 4 and argv[1] == 'full-outro':
        lang, part = argv[2], argv[3]
        if part == 'sub':
            print(full_outro_sub(lang))
        else:
            print(FULL_ONLY[lang][{'title': 'outro_t', 'cta': 'outro_cta',
                                   'where': 'outro_where'}[part]])
        return 0
    if len(argv) >= 2 and argv[1] == 'check':
        return check()
    if len(argv) >= 2 and argv[1] == 'ledger':
        build_ledger(argv[2:] or None)
        print(f'wrote {LEDGER}')
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
