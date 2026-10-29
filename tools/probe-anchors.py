#!/usr/bin/env python3
"""probe-anchors.py — read-only probe of the eye's anchors, no model in the path.

Prints, for every language of the site and every named block, the heading and up to
three body lines the eye would grade a frame against. Used to prove an anchor fix
before spending a model call (29.10.2026: the FAQ heading on en/id — "FAQ", three
letters — had been dropped by the eye's own line floor, so the block was graded
against a card question instead of its heading).

The eye itself lives outside this tree and is named by the caller — this file must not
carry the path, because the repository is public and the sweep refuses our own names.

  python3 tools/probe-anchors.py --eye /path/to/landing-eye.py [--sections faq]
  LANDING_EYE=/path/to/landing-eye.py python3 tools/probe-anchors.py
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("--eye", default=os.environ.get("LANDING_EYE", ""),
                help="path to the eye script (outside this repository)")
ap.add_argument("--sections", default="", help="comma list of block names; empty = all")
ap.add_argument("--langs", default="", help="comma list of languages; empty = all")
args = ap.parse_args()

if not args.eye or not Path(args.eye).is_file():
    raise SystemExit("probe-anchors: --eye PATH is required (the eye script is not part of this tree)")

spec = importlib.util.spec_from_file_location("landing_eye", args.eye)
eye = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eye)

# the fourteen blocks the notebook names: ids on the page plus the named marks
sections = args.sections.split(",") if args.sections else sorted(set(eye.SECTION_MARK) | {
    "head", "hero", "how", "features", "pricing", "faq", "parents", "ref", "contact",
    "band", "bands", "cta", "footer", "proof",
})
langs = args.langs.split(",") if args.langs else list(eye.LANGS)

out = {}
missing = 0
for lang in langs:
    out[lang] = {}
    for sec in sections:
        a = eye.section_anchors(ROOT, lang, sec)
        out[lang][sec] = a
        if not a.get("heading"):
            missing += 1

print(json.dumps(out, ensure_ascii=False, indent=1))
print(f"ANCHORS: {len(langs)} langs x {len(sections)} blocks, without heading: {missing}")
