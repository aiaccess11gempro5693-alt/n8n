#!/bin/bash
set -e
R="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENES=/tmp/final-scenes
IMAGES=/tmp/final-images-v5
FONT="$R/fonts/Inter-Bold.otf"
TOTAL=8

# --- v6: более "технологичный" монтаж ---
# 1) Ken Burns (плавный зум) на фоновых картинках вместо статичного кадра.
# 2) Подписи не появляются рывком, а всплывают снизу с fade-in.
# 3) Чипы в мульти-сценах (3/5/6) появляются по очереди (каскад), а не все разом.
# 4) Рамка PIP-аватара — акцентный цвет вместо белой.
# 5) Счётчик сцены "NN/08" в левом нижнем углу на каждой сцене.
# 6) Глобальный прогресс-бар по всей длине финального ролика (в build_concat_cmd.py).

kenburns () {
  # $1=DUR -> фильтр медленного зума на статичном изображении
  local dur=$1
  local frames
  frames=$(python3 -c "import math;print(math.ceil(${dur}*25)+10)")
  echo "scale=2688:1536,zoompan=z='min(zoom+0.0008,1.12)':d=${frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=25,setsar=1"
}

# 15.09.2026: счётчик сцены "NN/08" в левом нижнем углу — УБРАН по
# прямому запросу ("убери дату в левом нижнем углу и никогда не делай её
# в правый угол... чтобы там этого не было"). Правило зафиксировано в
# docs/design-system.md: никаких элементов ни в одном углу кадра.
# Функция counter_tag больше не существует — все вызовы удалены ниже,
# остался только progress_track (полноширинный бар, не угловой элемент).

# Прогресс-бар по сценам — раньше пробовали одной растущей полосой
# (drawbox с шириной от t), но в этой версии ffmpeg такие expressions
# не пересчитываются по кадрам без танцев с багами (см. коммит про
# w/h). Обход: НЕ анимация внутри сцены, а N статичных сегментов,
# честно нарисованных заново в КАЖДОЙ сцене — прогресс "прыгает" от
# сцены к сцене, а не течёт плавно внутри одной, но зато не ловит баг
# вообще, потому что ничего не меняется от t.
progress_track () {
  # $1=N (текущая сцена, 1..8)
  local n=$1 i x
  local total_w=1840 gap=6
  local seg_w
  seg_w=$(python3 -c "print(round((${total_w}-7*${gap})/8))")
  local chain="" x_cursor=40
  for i in $(seq 1 8); do
    local color
    if [ "$i" -le "$n" ]; then color="0x2A7F82@0.95"; else color="0x2A7F82@0.18"; fi
    chain+="drawbox=x=${x_cursor}:y=1074:w=${seg_w}:h=6:color=${color}:t=fill,"
    x_cursor=$((x_cursor + seg_w + gap))
  done
  echo "${chain%,}"
}

# Плашка субтитров — теперь ПОЛНАЯ дословная реплика диктора целиком
# (не короткий пересказ), нарезанная на чанки по <=2 строки, чанки
# сменяют друг друга на протяжении ВСЕЙ сцены; внутри чанка бегущая
# коралловая подсветка идёт по словам (см. docs/design-system.md, п.3,
# правки 14.09.2026). Плашка теперь ФИКСИРОВАННОГО размера/позиции на
# всех сценах (не подгоняется по ширине под текст, как раньше — это и
# давало "неровный"/скачущий вид от сцены к сцене).
#
# Вся геометрия и тайминги посчитаны заранее в compute_word_layout.py
# (word_layout.json); caption_filter.py по нему генерирует готовый
# фрагмент filter_complex. Инвариант из старой версии сохранён: в любой
# момент времени реально активна ровно ОДНА пара drawtext (base чанка +
# текущее подсвеченное слово) — у ffmpeg drawtext есть баг, при котором
# НЕСКОЛЬКО одновременно видимых (enable=true) drawtext в одном графе
# рендерятся мельче все, кроме первого; строго взаимоисключающие
# enable-окна (between/gte без пересечений) обходят это.
glass_caption () {
  # $1=input_label $2=output_label $3=N $4=canvas_input_index
  python3 "$R/caption_filter.py" "$3" "$1" "$2" "$4"
}

render_avatar_only () {
  N=$1
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  ffmpeg -y -i "$IN" -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]scale=1920:1080,$(progress_track $N)[base];\
$(glass_caption base outv $N 1)" \
    -map "[outv]" -map 0:a \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

render_bg_pip_single () {
  N=$1
  IMG="$IMAGES/scene-${N}.png"
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  ffmpeg -y -loop 1 -t "$DUR" -i "$IMG" -i "$IN" -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]$(kenburns $DUR)[bg];\
[1:v]scale=480:270,pad=496:286:8:8:0x2A7F82,setsar=1[pipv];\
[bg][pipv]overlay=W-496-40:H-286-40[comp];\
[comp]$(progress_track $N)[base];\
$(glass_caption base outv $N 2)" \
    -map "[outv]" -map 1:a -t "$DUR" \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

# Фиксированные равные "чипы" вместо auto-width box=1, появляются каскадом
# (по очереди, а не все разом) — через enable=gte(t,START).
chip_box () {
  # $1=color $2=x $3=y $4=w $5=h $6=start
  echo "drawbox=x=${2}:y=${3}:w=${4}:h=${5}:color=${1}@0.95:t=fill:enable=gte(t\,${6})"
}
chip_text () {
  # $1=textfile $2=fontsize $3=box_x $4=box_y $5=box_w $6=box_h $7=start
  echo "drawtext=fontfile=${FONT}:fontcolor=white:fontsize=${2}:textfile=${1}:x=${3}+(${5}-text_w)/2:y=${4}+(${6}-text_h)/2:enable=gte(t\,${7}):alpha=min((t-${7})/0.25\,1)"
}

# Сцена 3: 4 равных чипа в ряд сверху, появляются по очереди слева направо
render_scene_3 () {
  N=3
  IMG="$IMAGES/scene-${N}.png"
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  # Картинка — сетка 2x2 (карточки: слева/справа x2 строки). Подписи
  # теперь тоже мини-сеткой 2x2 в верхней полосе, колонки совпадают с
  # колонками карточек под ними (раньше все 4 подписи шли в один ряд
  # слева направо, из-за чего 2 и 3 пункт оказывались НЕ над своими
  # карточками — правили по жалобе на несовпадение текста с картинкой).
  BW=420; BH=70; FS=28
  # YB было 105 (почти вплотную к YT=20) — не соответствовало реальной
  # раскладке картинки, где вторая строка иконок находится далеко внизу
  # кадра. Новая scene3-flat-v2.png сгенерирована по явным процентам
  # (docs/design-system.md, п.4: карточки 3/4 — y:55-88% кадра), отсюда
  # и новое YB (14.09.2026, правка по прямой жалобе на несовпадение).
  XL=480; XR=1020; YT=20; YB=480
  ffmpeg -y -loop 1 -t "$DUR" -i "$IMG" -i "$IN" -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]$(kenburns $DUR)[bg];\
[1:v]scale=480:270,pad=496:286:8:8:0x2A7F82,setsar=1[pipv];\
[bg][pipv]overlay=W-496-40:H-286-40[c0];\
[c0]$(chip_box 0x2A7F82 $XL $YT $BW $BH 0.0)[b1];\
[b1]$(chip_box 0xF2836B $XR $YT $BW $BH 0.18)[b2];\
[b2]$(chip_box 0x2A7F82 $XL $YB $BW $BH 0.36)[b3];\
[b3]$(chip_box 0xF2836B $XR $YB $BW $BH 0.54)[b4];\
[b4]$(chip_text $R/text/3-item1.txt $FS $XL $YT $BW $BH 0.0)[t1];\
[t1]$(chip_text $R/text/3-item2.txt $FS $XR $YT $BW $BH 0.18)[t2];\
[t2]$(chip_text $R/text/3-item3.txt $FS $XL $YB $BW $BH 0.36)[t3];\
[t3]$(chip_text $R/text/3-item4.txt $FS $XR $YB $BW $BH 0.54)[c1];\
[c1]$(progress_track $N)[base];\
$(glass_caption base outv $N 2)" \
    -map "[outv]" -map 1:a -t "$DUR" \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

# Сцена 5: 4 чипа столбиком справа, Y каждого — на высоте СВОЕЙ строки
# на карточке (раньше все 4 были свалены в один угол вверху, никак не
# привязаны к 4 строкам чек-листа на самой картинке — правили по
# жалобе, что текст "не там, где должен быть"). Координаты строк
# карточки измерены по фактическому рендеру (scene-5.png на холсте
# 1920x1080): карточка y≈155–945, 4 строки поровну. Последняя чуть
# сдвинута вверх, чтобы не залезать на PIP-аватар в углу.
render_scene_5 () {
  N=5
  IMG="$IMAGES/scene-${N}.png"
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  BW=600; BH=64; FS=26
  X=1280; Y0=210; Y1=395; Y2=555; Y3=680
  ffmpeg -y -loop 1 -t "$DUR" -i "$IMG" -i "$IN" -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]$(kenburns $DUR)[bg];\
[1:v]scale=480:270,pad=496:286:8:8:0x2A7F82,setsar=1[pipv];\
[bg][pipv]overlay=W-496-40:H-286-40[c0];\
[c0]$(chip_box 0x2A7F82 $X $Y0 $BW $BH 0.0)[b1];\
[b1]$(chip_box 0xF2836B $X $Y1 $BW $BH 0.18)[b2];\
[b2]$(chip_box 0x2A7F82 $X $Y2 $BW $BH 0.36)[b3];\
[b3]$(chip_box 0xF2836B $X $Y3 $BW $BH 0.54)[b4];\
[b4]$(chip_text $R/text/5-item1.txt $FS $X $Y0 $BW $BH 0.0)[t1];\
[t1]$(chip_text $R/text/5-item2.txt $FS $X $Y1 $BW $BH 0.18)[t2];\
[t2]$(chip_text $R/text/5-item3.txt $FS $X $Y2 $BW $BH 0.36)[t3];\
[t3]$(chip_text $R/text/5-item4.txt $FS $X $Y3 $BW $BH 0.54)[c1];\
[c1]$(progress_track $N)[base];\
$(glass_caption base outv $N 2)" \
    -map "[outv]" -map 1:a -t "$DUR" \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

# Сцена 6: 2 равных чипа сверху, появляются по очереди
render_scene_6 () {
  N=6
  IMG="$IMAGES/scene-${N}.png"
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  BW=560; BH=70; FS=28
  X0=321; X1=1050; Y=80
  ffmpeg -y -loop 1 -t "$DUR" -i "$IMG" -i "$IN" -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]$(kenburns $DUR)[bg];\
[1:v]scale=480:270,pad=496:286:8:8:0x2A7F82,setsar=1[pipv];\
[bg][pipv]overlay=W-496-40:H-286-40[c0];\
[c0]$(chip_box 0xF2836B $X0 $Y $BW $BH 0.0)[b1];\
[b1]$(chip_box 0x2A7F82 $X1 $Y $BW $BH 0.18)[b2];\
[b2]$(chip_text $R/text/6-item1.txt $FS $X0 $Y $BW $BH 0.0)[t1];\
[t1]$(chip_text $R/text/6-item2.txt $FS $X1 $Y $BW $BH 0.18)[c1];\
[c1]$(progress_track $N)[base];\
$(glass_caption base outv $N 2)" \
    -map "[outv]" -map 1:a -t "$DUR" \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

## Подход A (v13) — уже отрендерен и одобрен ранее, для Подхода B (ниже)
## переделывать не нужно.
# render_avatar_only 1
# render_bg_pip_single 2
# render_scene_3
# render_avatar_only 4
# render_scene_5
# render_scene_6
# render_avatar_only 7
# render_avatar_only 8
#
# echo "ALL DONE"

# ============================================================
# Подход B (эксперимент, 15.09.2026, docs/design-system.md):
# аватар ВСЕГДА на весь кадр (без PIP, без фоновой картинки-коллажа),
# отдельные изолированные иконки (сгенерированы на magenta-фоне,
# вырезаются через ffmpeg colorkey) "плавают" вокруг него по бокам,
# подпись — под каждой иконкой. Позиции подобраны так, чтобы не
# перекрывать ни лицо/корпус аватара (он в центре кадра), ни плашку
# субтитров (x:40-1340, y:900-1050 — все иконки/подписи заканчиваются
# выше y=900 с запасом). Иконки на СТИЛЕВОМ фоне 0xE91E8F (реальный тон
# magenta, который реально отдаёт Nano Banana — не идеальный #FF00FF из
# промпта) — если для конкретной иконки останется кайма, поправить
# similarity/blend точечно для неё.
ICONS=/home/user/n8n/scratch
CKEY="colorkey=0xE91E8F:0.35:0.12"

icon_ov () {
  # $1=input_idx $2=x $3=y $4=size $5=start(sec) $6=prev_label $7=out_label
  # Белая карточка (#F7F9FB) под иконкой — без неё иконка на фоне живого
  # видео (полки аптеки) плохо читается (правка 15.09.2026, по прямой
  # жалобе "их не видно"). Карточка — простой прямоугольник с отступом
  # ICON_PAD со всех сторон, появляется вместе с иконкой (тот же enable).
  # ВАЖНО: без fade — иконка это ОДИН кадр PNG без -loop, у него
  # собственный таймлайн застревает в t=0, поэтому fade=t=in:st=START
  # для start>0 никогда "не доходит" до полной непрозрачности (кадр
  # навечно остаётся в "до-fade" состоянии = невидим). enable=gte(t,...)
  # у overlay/drawbox оценивается по таймлайну ОСНОВНОГО потока (как и
  # у chip_box/chip_text), поэтому жёсткое появление работает корректно.
  # 15.09.2026 (v17) — по запросу "крупнее, ярче, читаемее" (не
  # загораживая фармацевта): карточка теперь полностью непрозрачная
  # (было 0.97) для более чёткого контраста с живым фоном, и сама
  # иконка после chromakey дополнительно проходит через eq (насыщенность
  # +40%/контраст +10%/лёгкая подсветка) — бирюзовые/коралловые линии
  # становятся заметно ярче на белой подложке. Сам размер (${4}) вырос
  # по каждой сцене отдельно — см. render_scene_*_icons ниже, с
  # пересчитанными координатами, чтобы новый размер рос ТОЛЬКО в сторону
  # от аватара (к краю кадра), а не в его сторону.
  local pad=20
  local cx=$((${2}-pad)) cy=$((${3}-pad)) cs=$((${4}+2*pad))
  echo "[${6}]drawbox=x=${cx}:y=${cy}:w=${cs}:h=${cs}:color=0xF7F9FB@1.0:t=fill:enable=gte(t\,${5})[card${1}];[${1}:v]scale=${4}:${4},${CKEY},eq=saturation=1.4:contrast=1.1:brightness=0.03[ico${1}];[card${1}][ico${1}]overlay=${2}:${3}:enable=gte(t\,${5})[${7}]"
}

# Сцена 2 — 1 иконка (лупа+вопрос) справа от аватара
render_scene_2_icons () {
  N=2
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  ffmpeg -y -i "$IN" -i "$ICONS/scene2-icon1.png" -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]scale=1920:1080,$(progress_track $N)[base];\
$(icon_ov 1 1350 180 520 0.0 base ic1);\
[ic1]$(chip_box 0xF2836B 1330 730 560 72 0.0)[b1];\
[b1]$(chip_text $R/text/2-item1.txt 30 1330 730 560 72 0.0)[c1];\
$(glass_caption c1 outv $N 2)" \
    -map "[outv]" -map 0:a \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

# Сцена 3 — 4 иконки по углам вокруг аватара
render_scene_3_icons () {
  N=3
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  # v17: SZ 300->330 (+10%, ограничено высотой — 2 строки карточек
  # должны поместиться над плашкой субтитров y=900) + правый столбец
  # сдвинут с XR=1560 на 1540, чтобы карточка выросшего размера не
  # упёрлась в правый край кадра (avatar-facing край у каждой иконки
  # фиксирован независимо от размера — тут не растёт риск перекрыть
  # аватара, растёт только внешний край к углу).
  SZ=330
  XL=60; XR=1540; Y0=60; Y1=460
  ffmpeg -y -i "$IN" \
    -i "$ICONS/scene3-icon1.png" -i "$ICONS/scene3-icon2.png" \
    -i "$ICONS/scene3-icon3.png" -i "$ICONS/scene3-icon4.png" \
    -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]scale=1920:1080,$(progress_track $N)[base];\
$(icon_ov 1 $XL $Y0 $SZ 0.0 base ic1);\
$(icon_ov 2 $XR $Y0 $SZ 0.18 ic1 ic2);\
$(icon_ov 3 $XL $Y1 $SZ 0.36 ic2 ic3);\
$(icon_ov 4 $XR $Y1 $SZ 0.54 ic3 ic4);\
[ic4]$(chip_box 0x2A7F82 40 420 370 64 0.0)[b1];\
[b1]$(chip_box 0xF2836B 1520 420 370 64 0.18)[b2];\
[b2]$(chip_box 0x2A7F82 40 820 370 64 0.36)[b3];\
[b3]$(chip_box 0xF2836B 1520 820 370 64 0.54)[b4];\
[b4]$(chip_text $R/text/3-item1.txt 26 40 420 370 64 0.0)[t1];\
[t1]$(chip_text $R/text/3-item2.txt 26 1520 420 370 64 0.18)[t2];\
[t2]$(chip_text $R/text/3-item3.txt 26 40 820 370 64 0.36)[t3];\
[t3]$(chip_text $R/text/3-item4.txt 26 1520 820 370 64 0.54)[c1];\
$(glass_caption c1 outv $N 5)" \
    -map "[outv]" -map 0:a \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

# Сцена 5 — это ЧЕК-ЛИСТ вопросов (последовательность, не независимые
# варианты!) — раньше использовала ту же 2x2-угловую раскладку, что и
# сцена 3, из-за чего 4 пункта списка выглядели раскиданными по углам
# без всякой связи друг с другом (прямая жалоба 15.09.2026: "чек-лист
# должен быть чек-листом... должна быть логика, о чём говорится").
# Теперь — ОДНА вертикальная колонка справа, иконка слева от подписи в
# каждой строке (как в реальном чек-листе), 4 строки друг под другом —
# читается как единый список, а не как 4 разрозненные картинки.
render_scene_5_icons () {
  N=5
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  # v17: иконка 90->110 (+22%), строки раздвинуты со 150 до 170px, чтобы
  # карточка (110+2*20 pad=150) не касалась соседней — есть большой запас
  # по вертикали до плашки субтитров (y=900), им и воспользовались.
  # Подпись вертикально центрируется относительно новой высоты иконки:
  # offset=(SZ-LH)/2=(110-70)/2=20.
  SZ=110
  ICX=1430
  LX=1570; LW=330; LH=70; FS=24
  Y0=50; Y1=220; Y2=390; Y3=560
  ffmpeg -y -i "$IN" \
    -i "$ICONS/scene5-icon1.png" -i "$ICONS/scene5-icon2.png" \
    -i "$ICONS/scene5-icon3.png" -i "$ICONS/scene5-icon4.png" \
    -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]scale=1920:1080,$(progress_track $N)[base];\
$(icon_ov 1 $ICX $Y0 $SZ 0.0 base ic1);\
$(icon_ov 2 $ICX $Y1 $SZ 0.18 ic1 ic2);\
$(icon_ov 3 $ICX $Y2 $SZ 0.36 ic2 ic3);\
$(icon_ov 4 $ICX $Y3 $SZ 0.54 ic3 ic4);\
[ic4]$(chip_box 0x2A7F82 $LX $((Y0+20)) $LW $LH 0.0)[b1];\
[b1]$(chip_box 0xF2836B $LX $((Y1+20)) $LW $LH 0.18)[b2];\
[b2]$(chip_box 0x2A7F82 $LX $((Y2+20)) $LW $LH 0.36)[b3];\
[b3]$(chip_box 0xF2836B $LX $((Y3+20)) $LW $LH 0.54)[b4];\
[b4]$(chip_text $R/text/5-item1.txt $FS $LX $((Y0+20)) $LW $LH 0.0)[t1];\
[t1]$(chip_text $R/text/5-item2.txt $FS $LX $((Y1+20)) $LW $LH 0.18)[t2];\
[t2]$(chip_text $R/text/5-item3.txt $FS $LX $((Y2+20)) $LW $LH 0.36)[t3];\
[t3]$(chip_text $R/text/5-item4.txt $FS $LX $((Y3+20)) $LW $LH 0.54)[c1];\
$(glass_caption c1 outv $N 5)" \
    -map "[outv]" -map 0:a \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

# Сцена 6 — 2 иконки слева/справа от аватара
render_scene_6_icons () {
  N=6
  IN="$SCENES/scene-${N}.mp4"
  OUT="$R/scene-${N}.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  # v17: 420->470 (+12%). Правая иконка сдвинута с x=1420 на 1400, чтобы
  # выросшая карточка не упёрлась в правый край кадра — avatar-facing
  # край (слева от правой иконки) при этом не приближается к аватару
  # сильнее исходного.
  SZ=470
  ffmpeg -y -i "$IN" -i "$ICONS/scene6-icon1.png" -i "$ICONS/scene6-icon2.png" \
    -f lavfi -i "color=c=black@0.0:s=1920x1080:r=25:d=${DUR}" -filter_complex "\
[0:v]scale=1920:1080,$(progress_track $N)[base];\
$(icon_ov 1 80 120 $SZ 0.0 base ic1);\
$(icon_ov 2 1400 120 $SZ 0.18 ic1 ic2);\
[ic2]$(chip_box 0xF2836B 60 620 510 72 0.0)[b1];\
[b1]$(chip_box 0x2A7F82 1380 620 510 72 0.18)[b2];\
[b2]$(chip_text $R/text/6-item1.txt 28 60 620 510 72 0.0)[t1];\
[t1]$(chip_text $R/text/6-item2.txt 28 1380 620 510 72 0.18)[c1];\
$(glass_caption c1 outv $N 3)" \
    -map "[outv]" -map 0:a \
    -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 25 \
    -c:a aac -b:a 160k \
    "$OUT"
}

# 16.09.2026: render_scene_2_icons/3_icons/5_icons/6_icons above (white
# card + all-icons-pop-at-once) are SUPERSEDED — по прямой жалобе
# ("белые плашки не смотрятся", "хочется динамики", "шрифт нечитаемый",
# "цвет сливается с фоном") заменены на icon-scene рендер через
# render_icon_scenes.py в этой же папке: иконки — "стикер" (белая
# обводка через дилатацию альфа-маски + мягкая тень, без белой
# карточки), появление синхронизировано с точным таймингом слова в
# word_layout.json (не единый каскад в начале сцены), подписи —
# скруглённые pill-бейджи (сгенерированы через pill_gen_all.py на PIL,
# по размеру текста), центрированные под иконкой (в layout "beside" для
# сцены 5 — сбоку, по вертикали строки). Функции ниже оставлены только
# для истории/справки, НЕ вызывать для новых рендеров сцен 2/3/5/6.
render_avatar_only 1
# render_scene_2_icons   # см. render_icon_scenes.py
# render_scene_3_icons   # см. render_icon_scenes.py
render_avatar_only 4
# render_scene_5_icons   # см. render_icon_scenes.py
# render_scene_6_icons   # см. render_icon_scenes.py
render_avatar_only 7
render_avatar_only 8

echo "avatar-only scenes done — now run: python3 pill_gen_all.py && python3 render_icon_scenes.py"
