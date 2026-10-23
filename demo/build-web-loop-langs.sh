#!/bin/bash
# Build the per-language web hero loops (13 s) with step captions IN THE PAGE
# LANGUAGE, then refresh each language's poster and re-stamp demo/captions.json.
#
# Same pipeline as the kit build (submission-kit-20261014/demo/build-demo.sh):
#   zoompan 2880x6240 -> 2160x4680 -> scale 720x1560, drawtext: white 28 px on
#   #3D5AFE@0.85 box (boxborderw 16, x=(w-text_w)/2, y=h-150), xfade fade 0.5 s;
#   30 fps, H.264 veryslow crf30, +faststart, no audio.
#   Structure: scene1 (shot2) 8.0 s, transition at 7.2 s, scene2 (shot3) 5.8 s
#   -> 13.0 s (390 frames).
#
# CAPTIONS ARE NOT WRITTEN HERE. demo/captions.py derives them from
# src/locales/<lang>.json (how.s2t, and shot3.alt without the brand), so the
# video and the page cannot drift apart: landing-sweep.py fails when the
# dictionary, the ledger and the loop bytes disagree. The one video-only phrase
# (the "text or photo" tail) lives in that script too.
# hi: the Devanagari subset has no "·" (U+00B7), so its joiner is "." — handled
# by captions.py. drawtext text_shaping defaults to on, so HarfBuzz shapes the
# Devanagari conjuncts.
#
# Sources (overridable via env):
#   KIT (default: $ROOT/../submission-kit-20261014)
#     en -> $KIT/shots_en/shot2_task_en.png + shot3_answer_en.png
#     ru -> $KIT/shots/shot2_task_ru.png    + shot3_answer_ru.png
#   SHOTS_DIR (default: $ROOT/.shots-work)
#     <lang> -> $SHOTS_DIR/<lang>/shot2.png + shot3.png
#   If the shots-gen renders are gone:
#     python3 tools/shots-gen/gen_shots.py --langs <l>[,<l>...]
#
# Poster: last frame of the loop -> img/demo-poster[-<lang>].webp (540x1170),
#   same rule as the original posters. It is part of the delivered page: a
#   re-captioned loop with a stale poster would show the old words before play.
#
# Run from anywhere:  bash demo/build-web-loop-langs.sh [lang ...]
#   default: es pt hi id tr vi uk       (en and ru are built the same way)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
KIT="${KIT:-$ROOT/../submission-kit-20261014}"
SHOTS_DIR="${SHOTS_DIR:-$ROOT/.shots-work}"
FB=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
FN=/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf

LANGS=("$@")
if [ ${#LANGS[@]} -eq 0 ]; then LANGS=(es pt hi id tr vi uk); fi

cap1() { python3 "$HERE/captions.py" cap1 "$1"; }
cap2() { python3 "$HERE/captions.py" cap2 "$1"; }
font() { [ "$1" = hi ] && echo "$FN" || echo "$FB"; }

sources() {  # sets SRC2 SRC3 for one language
  case "$1" in
    en) SRC2="$KIT/shots_en/shot2_task_en.png"; SRC3="$KIT/shots_en/shot3_answer_en.png" ;;
    ru) SRC2="$KIT/shots/shot2_task_ru.png";    SRC3="$KIT/shots/shot3_answer_ru.png" ;;
    *)  SRC2="$SHOTS_DIR/$1/shot2.png";         SRC3="$SHOTS_DIR/$1/shot3.png" ;;
  esac
}

ZP="scale=2880:6240,zoompan=z='min(zoom+0.0004,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

for L in "${LANGS[@]}"; do
  sources "$L"
  if [ ! -f "$SRC2" ] || [ ! -f "$SRC3" ]; then
    echo "MISSING: $SRC2 / $SRC3" >&2
    echo "  (shots-gen renders: python3 $ROOT/tools/shots-gen/gen_shots.py --langs $L)" >&2
    exit 1
  fi
  F=$(font "$L"); C1=$(cap1 "$L"); C2=$(cap2 "$L")
  CAP="fontfile=$F:fontsize=28:fontcolor=white:box=1:boxcolor=0x3D5AFE@0.85:boxborderw=16:x=(w-text_w)/2:y=h-150"
  if [ "$L" = en ]; then OUT="$HERE/uchiambot-demo-web.mp4"; else OUT="$HERE/uchiambot-demo-web-$L.mp4"; fi
  ffmpeg -y -v warning \
   -i "$SRC2" \
   -i "$SRC3" \
   -filter_complex "\
[0:v]$ZP:d=240:s=2160x4680:fps=30,scale=720:1560,drawtext=$CAP:text='$C1',format=yuv420p,setsar=1[v1];\
[1:v]$ZP:d=174:s=2160x4680:fps=30,scale=720:1560,drawtext=$CAP:text='$C2',format=yuv420p,setsar=1[v2];\
[v1][v2]xfade=transition=fade:duration=0.5:offset=7.2,format=yuv420p[vout]" \
   -map "[vout]" -c:v libx264 -preset veryslow -crf 30 -movflags +faststart -an "$OUT"
  # Poster: last frame (n=389) -> 540x1170 webp, same as the original posters.
  if [ "$L" = en ]; then POSTER="$ROOT/img/demo-poster.webp"; else POSTER="$ROOT/img/demo-poster-$L.webp"; fi
  ffmpeg -y -v error -i "$OUT" -vf "select='eq(n,389)',scale=540:1170" -frames:v 1 \
    -c:v libwebp -quality 80 -compression_level 6 "$POSTER"
  # The ledger must describe the file that was just built.
  python3 "$HERE/captions.py" ledger "$L" >/dev/null
  echo "--- $L: $C1  |  $C2"
  ls -la "$OUT" "$POSTER"
  ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames,duration -of default=nw=1 "$OUT"
  echo "OK: $L"
done
echo "ledger restamped: $HERE/captions.json"
