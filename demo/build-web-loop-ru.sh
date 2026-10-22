#!/bin/bash
# Rebuild the RU web hero loop (demo/uchiambot-demo-web-ru.mp4) with Russian step
# captions. Thin wrapper around demo/build-web-loop-langs.sh, so there is ONE
# pipeline and ONE source of the caption strings (demo/captions.py, from
# src/locales/ru.json). Before 22 Oct 2026 this file had its own copy of the
# pipeline and two hard-coded Russian captions that could drift from the page.
#
# Sources: kit RU chat shots (submission-kit-20261014/shots), overridable with
# KIT=... Run from anywhere:  bash demo/build-web-loop-ru.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
exec bash "$HERE/build-web-loop-langs.sh" ru
