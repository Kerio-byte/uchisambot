#!/bin/bash
# Build the full 35 s demo (720x1560, 30 fps) for one language:
#   en -> demo/uchiambot-demo.mp4        ru -> demo/uchiambot-demo-ru.mp4
#
# Same pipeline as the submission kit (build-demo.sh / build-demo-en.sh):
#   intro card 3 s (fade in), four 8 s scenes, outro card 3 s (fade out), xfade
#   0.5 s at 2.5 / 10 / 17.5 / 25 / 32.5 s; zoompan rendered at 2160x4680 and
#   downscaled (otherwise the slow zoom quantises into repeated frames);
#   H.264 preset faster crf23, +faststart, no audio.
#
# EVERY WORD COMES FROM demo/captions.py: intro tagline = foot.tag, outro promise
# = hero.chip1, captions 2 and 3 = the same strings as the hero loop (page
# dictionary), captions 1 and 4 and the two outro buttons are video-only and live
# in FULL_ONLY. Before 22 Oct 2026 the outro said "5 free step-by-step solutions"
# while the product gives two and the page promises two, and the RU demo carried
# English captions over Russian screenshots. The ledger (demo/captions.json,
# section "full") records the strings and the bytes; landing-sweep.py fails when
# they disagree.
#
# Sources: $KIT/shots_en (en) and $KIT/shots (ru), overridable with KIT=...
# Run from anywhere:  bash demo/build-full-demo.sh en|ru
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
KIT="${KIT:-$ROOT/../submission-kit-20261014}"
FB=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
F=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
L="${1:?usage: build-full-demo.sh en|ru}"

case "$L" in
  # 24.10.2026: сцены 1-3 — те же файлы, что показывает страница (img/shotN[-<lang>].webp).
  # Раньше все четыре снимались из внешнего каталога submission-kit; после перерисовки
  # макетов 23.10 (седьмая кнопка «Пригласить друга») полное демо продолжало показывать
  # шесть кнопок. Сцена 4 — переключение языка — своей картинки на странице не имеет
  # и остаётся из каталога; она клавиатуру не показывает.
  en) SHOTS="$KIT/shots_en"; S1="$ROOT/img/shot1.webp"; S2="$ROOT/img/shot2.webp"
      S3="$ROOT/img/shot3.webp"; S4="$SHOTS/shot4_lang_en.png"; OUT="$HERE/uchiambot-demo.mp4" ;;
  ru) SHOTS="$KIT/shots";    S1="$ROOT/img/shot1-ru.webp"; S2="$ROOT/img/shot2-ru.webp"
      S3="$ROOT/img/shot3-ru.webp"; S4="$SHOTS/shot4_answer_en.png"; OUT="$HERE/uchiambot-demo-ru.mp4" ;;
  *) echo "unknown language: $L" >&2; exit 2 ;;
esac
for f in "$S1" "$S2" "$S3" "$S4"; do
  [ -f "$f" ] || { echo "MISSING: $f" >&2; exit 1; }
done

C() { python3 "$HERE/captions.py" "$@"; }
TAG=$(C full-intro "$L")
OT=$(C full-outro "$L" title)
OS=$(C full-outro "$L" sub)
OC=$(C full-outro "$L" cta)
OW=$(C full-outro "$L" where)
C1=$(C full "$L" 1); C2=$(C full "$L" 2); C3=$(C full "$L" 3); C4=$(C full "$L" 4)

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

convert -size 1080x2340 gradient:'#1E2A78-#3D5AFE' \
  \( "$KIT/logo-512.png" -resize 460x460 \) -gravity center -geometry +0-330 -composite \
  -font "$FB" -pointsize 104 -fill white -gravity center -annotate +0+120 'UchiSamBot' \
  -font "$F" -pointsize 46 -fill '#EAF0FF' -gravity center -annotate +0+250 "$TAG" \
  -font "$FB" -pointsize 48 -fill '#4FC3F7' -gravity center -annotate +0+400 't.me/UchiSamBot' \
  "$WORK/intro.png"

convert -size 1080x2340 gradient:'#1E2A78-#3D5AFE' \
  \( "$KIT/logo-512.png" -resize 320x320 \) -gravity center -geometry +0-560 -composite \
  -font "$FB" -pointsize 84 -fill white -gravity center -annotate +0-140 "$OT" \
  -font "$F" -pointsize 48 -fill '#EAF0FF' -gravity center -annotate +0-10 "$OS" \
  -font "$FB" -pointsize 68 -fill '#4FC3F7' -gravity center -annotate +0+180 "$OC" \
  -font "$F" -pointsize 44 -fill white -gravity center -annotate +0+300 "$OW" \
  "$WORK/outro.png"

# zoompan is rendered at 1440x3120 (2x the delivered 720x1560) and downscaled:
# enough supersampling for smooth sub-pixel motion without holding six 2160x4680
# frame buffers at once — the 3x variant segfaulted ffmpeg 6.1.1 on this box
# (22 Oct 2026), the 2x runs clean.
ZPS="${ZPS:-1440x3120}"
ZP="scale=$ZPS,zoompan=z='min(zoom+0.0004,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
CAP="fontfile=$FB:fontsize=28:fontcolor=white:box=1:boxcolor=0x3D5AFE@0.85:boxborderw=16:x=(w-text_w)/2:y=h-150"
VOUT="$WORK/out.mp4"
# Quality knobs: the full demo must stay inside its weight budget (EN ≤1 MiB,
# RU ≤1.5 MiB, enforced by the QA sweep). This content is mostly static UI with a
# slow zoom, so a high CRF still reads cleanly; the per-language defaults were
# measured, not guessed (EN crf32 → 916 KB, RU crf33 → 1.30 MB, both read clean
# against the files they replace).
PRESET="${PRESET:-slow}"
case "$L" in
  en) CRF="${CRF:-32}" ;;
  ru) CRF="${CRF:-33}" ;;
esac

ffmpeg -y -v warning \
 -i "$WORK/intro.png" -i "$S1" -i "$S2" -i "$S3" -i "$S4" -i "$WORK/outro.png" \
 -filter_complex "\
[0:v]$ZP:d=90:s=$ZPS:fps=30,scale=720:1560,fade=in:st=0:d=0.5,format=yuv420p,setsar=1[v0];\
[1:v]$ZP:d=240:s=$ZPS:fps=30,scale=720:1560,drawtext=$CAP:text='$C1',format=yuv420p,setsar=1[v1];\
[2:v]$ZP:d=240:s=$ZPS:fps=30,scale=720:1560,drawtext=$CAP:text='$C2',format=yuv420p,setsar=1[v2];\
[3:v]$ZP:d=240:s=$ZPS:fps=30,scale=720:1560,drawtext=$CAP:text='$C3',format=yuv420p,setsar=1[v3];\
[4:v]$ZP:d=240:s=$ZPS:fps=30,scale=720:1560,drawtext=$CAP:text='$C4',format=yuv420p,setsar=1[v4];\
[5:v]$ZP:d=90:s=$ZPS:fps=30,scale=720:1560,fade=out:st=2.5:d=0.5,format=yuv420p,setsar=1[v5];\
[v0][v1]xfade=transition=fade:duration=0.5:offset=2.5[x1];\
[x1][v2]xfade=transition=fade:duration=0.5:offset=10[x2];\
[x2][v3]xfade=transition=fade:duration=0.5:offset=17.5[x3];\
[x3][v4]xfade=transition=fade:duration=0.5:offset=25[x4];\
[x4][v5]xfade=transition=fade:duration=0.5:offset=32.5,format=yuv420p[vout]" \
 -map "[vout]" -c:v libx264 -preset "$PRESET" -crf "$CRF" -movflags +faststart -an "$VOUT"
mv "$VOUT" "$OUT"

# The ledger must describe the file that was just built.
python3 "$HERE/captions.py" ledger >/dev/null
echo "--- $L full demo"
echo "  intro tagline : $TAG"
echo "  $C1 | $C2 | $C3 | $C4"
echo "  outro         : $OT / $OS / $OC $OW"
ls -la "$OUT"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames,duration -of default=nw=1 "$OUT"
