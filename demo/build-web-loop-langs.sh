#!/bin/bash
# Build the per-language web hero loops (13 s) with step captions IN THE PAGE LANGUAGE,
# then refresh each language's video poster.
#
# Same pipeline as demo/build-web-loop-ru.sh (the kit build-demo.sh):
#   zoompan 2880x6240 -> 2160x4680 -> scale 720x1560, drawtext: white 28 px on
#   #3D5AFE@0.85 box (boxborderw 16, x=(w-text_w)/2, y=h-150), xfade fade 0.5 s;
#   30 fps, H.264 veryslow crf30, +faststart, no audio.
#   Structure: scene1 (shot2) 8.0 s, transition at 7.2 s, scene2 (shot3) 5.8 s -> 13.0 s (390 frames).
#
# Captions = site dictionary terms (how.s2t / shot3.alt core), tail per language chosen
# to match the bot's wording ("текст или фото"). hi: Noto Sans Devanagari has no "·"
# (U+00B7), so the step separator there is "." — deliberate, documented in README.
# drawtext text_shaping defaults to on, so HarfBuzz shapes Devanagari correctly.
#
# Sources: tools/shots-gen PNG renders (1080x2340) from the scratch workdir.
#   If missing, regenerate:  python3 tools/shots-gen/gen_shots.py --langs <l>[,<l>...]
#   (no --apply needed; PNG renders are written regardless). EN/RU loops have their own
#   scripts/sources and are NOT rebuilt here.
# Poster: last frame of the loop -> img/demo-poster-<lang>.webp (540x1170), same rule
#   as the original EN/RU posters.
#
# Run from anywhere:  bash demo/build-web-loop-langs.sh [lang ...]   (default: es pt hi id tr vi uk)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
SHOTS_DIR="${SHOTS_DIR:-/home/jar/.hermes/cache/scratch/shots-gen/work}"
FB=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
FN=/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf

LANGS=("$@")
if [ ${#LANGS[@]} -eq 0 ]; then LANGS=(es pt hi id tr vi uk); fi

cap1() {  # 2 · <how.s2t> — <текст или фото>
  case "$1" in
    es) echo '2 · Envía tu tarea — texto o foto' ;;
    pt) echo '2 · Envie uma tarefa — texto ou foto' ;;
    hi) echo '2. सवाल भेजें — टेक्स्ट या फोटो' ;;
    id) echo '2 · Kirim soal — teks atau foto' ;;
    tr) echo '2 · Ödevini gönder — yazı ya da fotoğraf' ;;
    vi) echo '2 · Gửi bài tập — chữ hoặc ảnh' ;;
    uk) echo '2 · Надішли завдання — текстом або фото' ;;
    *) echo "no caption for $1" >&2; return 1 ;;
  esac
}
cap2() {  # 3 · <shot3.alt core>
  case "$1" in
    es) echo '3 · Desglose paso a paso' ;;
    pt) echo '3 · Explicação passo a passo' ;;
    hi) echo '3. स्टेप-बाय-स्टेप हल' ;;
    id) echo '3 · Pembahasan langkah demi langkah' ;;
    tr) echo '3 · Adım adım çözüm' ;;
    vi) echo '3 · Phân tích từng bước' ;;
    uk) echo '3 · Покроковий розбір' ;;
    *) echo "no caption for $1" >&2; return 1 ;;
  esac
}
font() { [ "$1" = hi ] && echo "$FN" || echo "$FB"; }

ZP="scale=2880:6240,zoompan=z='min(zoom+0.0004,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

for L in "${LANGS[@]}"; do
  SRC2="$SHOTS_DIR/$L/shot2.png"
  SRC3="$SHOTS_DIR/$L/shot3.png"
  if [ ! -f "$SRC2" ] || [ ! -f "$SRC3" ]; then
    echo "MISSING: $SRC2 / $SRC3 — regenerate with: python3 $ROOT/tools/shots-gen/gen_shots.py --langs $L" >&2
    exit 1
  fi
  F=$(font "$L"); C1=$(cap1 "$L"); C2=$(cap2 "$L")
  CAP="fontfile=$F:fontsize=28:fontcolor=white:box=1:boxcolor=0x3D5AFE@0.85:boxborderw=16:x=(w-text_w)/2:y=h-150"
  OUT="$HERE/uchiambot-demo-web-$L.mp4"
  ffmpeg -y -v warning \
   -i "$SRC2" \
   -i "$SRC3" \
   -filter_complex "\
[0:v]$ZP:d=240:s=2160x4680:fps=30,scale=720:1560,drawtext=$CAP:text='$C1',format=yuv420p,setsar=1[v1];\
[1:v]$ZP:d=174:s=2160x4680:fps=30,scale=720:1560,drawtext=$CAP:text='$C2',format=yuv420p,setsar=1[v2];\
[v1][v2]xfade=transition=fade:duration=0.5:offset=7.2,format=yuv420p[vout]" \
   -map "[vout]" -c:v libx264 -preset veryslow -crf 30 -movflags +faststart -an "$OUT"
  # Poster: last frame (n=389) -> 540x1170 webp, same as the EN/RU posters.
  ffmpeg -y -v error -i "$OUT" -vf "select='eq(n,389)',scale=540:1170" -frames:v 1 \
    -c:v libwebp -quality 80 -compression_level 6 "$ROOT/img/demo-poster-$L.webp"
  ls -la "$OUT" "$ROOT/img/demo-poster-$L.webp"
  ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames,duration -of default=nw=1 "$OUT"
  echo "OK: $L"
done
