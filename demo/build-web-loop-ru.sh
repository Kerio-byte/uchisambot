#!/bin/bash
# Rebuild the RU web hero loop (demo/uchiambot-demo-web-ru.mp4) with Russian step captions.
# Same pipeline as submission-kit-20261014/demo/build-demo.sh:
#   zoompan 2880x6240 -> 2160x4680 -> scale 720x1560, drawtext (DejaVuSans-Bold 28, white
#   on #3D5AFE@0.85, borderw 16, y=h-150), xfade fade 0.5 s; 30 fps, H.264 veryslow crf30,
#   +faststart, no audio. Structure replicated from the previous loop: scene1 (shot2) 8.0 s,
#   transition at 7.2 s, scene2 (shot3) 5.8 s -> 13.0 s total (390 frames).
# Sources: kit RU chat shots (1080x2340 PNG). Override SHOTS=... to rebuild elsewhere.
# Run from anywhere:  bash demo/build-web-loop-ru.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SHOTS="${SHOTS:-/home/jar/Projects/stars-bots/promo/submission-kit-20261014/shots}"
OUT="$HERE/uchiambot-demo-web-ru.mp4"
FB=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf

ZP="scale=2880:6240,zoompan=z='min(zoom+0.0004,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
CAP="fontfile=$FB:fontsize=28:fontcolor=white:box=1:boxcolor=0x3D5AFE@0.85:boxborderw=16:x=(w-text_w)/2:y=h-150"

ffmpeg -y -v warning \
 -i "$SHOTS/shot2_task_ru.png" \
 -i "$SHOTS/shot3_answer_ru.png" \
 -filter_complex "\
[0:v]$ZP:d=240:s=2160x4680:fps=30,scale=720:1560,drawtext=$CAP:text='2 · Отправь задачу — текстом или фото',format=yuv420p,setsar=1[v1];\
[1:v]$ZP:d=174:s=2160x4680:fps=30,scale=720:1560,drawtext=$CAP:text='3 · Пошаговый разбор',format=yuv420p,setsar=1[v2];\
[v1][v2]xfade=transition=fade:duration=0.5:offset=7.2,format=yuv420p[vout]" \
 -map "[vout]" -c:v libx264 -preset veryslow -crf 30 -movflags +faststart -an "$OUT"

ls -la "$OUT"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames,duration,bit_rate -of default=nw=1 "$OUT"
echo "OK: $OUT"
