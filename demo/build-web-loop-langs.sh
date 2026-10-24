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
# Sources (24.10.2026): the page's own screenshots — img/shot2.webp + img/shot3.webp
#   (en) or img/shot2-<lang>.webp + img/shot3-<lang>.webp. Before this the loop was
#   cut from an external kit capture (en/ru) or from .shots-work renders (the other
#   seven), so redrawing a screenshot left the video behind: after the 23.10 menu
#   fix every loop still showed six buttons under a page that drew seven.
#   Now the video is cut from the very file the page displays, and the ledger stores
#   each source's sha256 — a new screenshot with an old loop is a sweep failure.
#   No external catalogue and no render run is needed to rebuild a loop.
#
# Poster: last frame of the loop -> img/demo-poster[-<lang>].webp (540x1170),
#   same rule as the original posters. It is part of the delivered page: a
#   re-captioned loop with a stale poster would show the old words before play.
#
# Run from anywhere:  bash demo/build-web-loop-langs.sh [lang ...]
#   default: all nine (en ru es pt hi id tr vi uk)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
FB=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
FN=/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf

LANGS=("$@")
if [ ${#LANGS[@]} -eq 0 ]; then LANGS=(en ru es pt hi id tr vi uk); fi

cap1() { python3 "$HERE/captions.py" cap1 "$1"; }
cap2() { python3 "$HERE/captions.py" cap2 "$1"; }
font() { [ "$1" = hi ] && echo "$FN" || echo "$FB"; }

sources() {  # sets SRC2 SRC3 for one language
  # 24.10.2026: источник — САМА КАРТИНКА СТРАНИЦЫ (img/shot2/3[-<lang>].webp), а не
  # макет из внешнего каталога submission-kit и не свежий рендер .shots-work.
  # Причина: 23.10 макеты перерисовали с седьмой кнопкой «Пригласить друга», а
  # ролики остались нарезанными из старых файлов — девять видео показывали
  # клавиатуру из шести кнопок, которой у бота не было никогда. Теперь ролик и
  # скриншот — один и тот же файл байт в байт, и реестр demo/captions.json хранит
  # sha256 источника: перерисовали скриншот, не перерезав ролик, — свип краснеет.
  local SUF=""
  [ "$1" != en ] && SUF="-$1"
  SRC2="$ROOT/img/shot2${SUF}.webp"
  SRC3="$ROOT/img/shot3${SUF}.webp"
}

ZP="scale=2880:6240,zoompan=z='min(zoom+0.0004,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

for L in "${LANGS[@]}"; do
  sources "$L"
  if [ ! -f "$SRC2" ] || [ ! -f "$SRC3" ]; then
    echo "MISSING: $SRC2 / $SRC3" >&2
    echo "  (the page's screenshot for this language — img/shotN[-<lang>].webp; generate:" >&2
    echo "   python3 $ROOT/tools/shots-gen/gen_shots.py --langs $L --apply)" >&2
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
