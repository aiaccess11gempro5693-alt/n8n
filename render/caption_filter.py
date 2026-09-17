import json
import sys

import os
R = os.path.dirname(os.path.abspath(__file__))
FONT = f"{R}/fonts/Inter-Bold.otf"
FONTSIZE = 40
BASE_COLOR = "0x2B2F33"
HL_COLOR = "0xF2836B"
PANEL_COLOR = "0xF7F9FB"
ACCENT = "0x2A7F82"

# n=scene, in_label/out_label=video pipeline labels, canvas_idx=ffmpeg
# input index of the extra transparent lavfi color source added to this
# scene's command (see render_scenes.sh).
#
# ПОЧЕМУ crop-маска, а не "два drawtext с посчитанным x" (было в v13
# черновике): при вычислении x подсвеченного слова через сумму ширин
# символов из таблицы шрифта (без реального кернинга/хинтинга, который
# применяет сам ffmpeg/FreeType при рендере) для слов в глубине строки
# накапливается расхождение в несколько пикселей — на кадре это видно
# как "двоение"/смещение слова (серая и коралловая копия не совпадают).
# Обход: рендерим ОДИН И ТОТ ЖЕ текст чанка ДВАЖДЫ на прозрачных
# холстах-двойниках (серый и коралловый, идентичные x/y/шрифт/размер —
# значит идентичные позиции глифов), и просто ВЫРЕЗАЕМ (crop) из
# коралловой копии прямоугольник текущего слова, накладывая его поверх
# уже посаженной серой копии в ТОЧНО ТУ ЖЕ позицию. Так подсветка
# гарантированно совпадает пиксель-в-пиксель с серым текстом — это не
# оценка, а буквально та же отрисовка.
n = int(sys.argv[1])
in_label = sys.argv[2]
out_label = sys.argv[3]
canvas_idx = sys.argv[4]

with open(f"{R}/word_layout.json", encoding="utf-8") as f:
    manifest = json.load(f)

panel = manifest["panel"]
scene = manifest["scenes"][str(n)]
chunks = scene["chunks"]

parts = []

# 1) панель (плашка + акцентная полоса) поверх основного видео
p1 = f"cap{n}_panel"
p2 = f"cap{n}_acc"
parts.append(
    f"[{in_label}]drawbox=x={panel['x']}:y={panel['y']}:w={panel['w']}:h={panel['h']}:"
    f"color={PANEL_COLOR}@0.94:t=fill[{p1}]"
)
parts.append(
    f"[{p1}]drawbox=x={panel['x']}:y={panel['y']}:w={panel['accent_bar_w']}:h={panel['h']}:"
    f"color={ACCENT}@1.0:t=fill[{p2}]"
)

# 2) прозрачный холст-вход дублируется на серую и коралловую ветки.
# ВАЖНО: lavfi "color=c=black@0.0" полностью ИГНОРИРУЕТ "@0.0" — сама
# color-нода всегда отдаёт alpha=255 (проверено побайтово через
# rawvideo-дамп), поэтому одного format=rgba недостаточно: канвас
# оставался непрозрачным и overlay гасил всё видео в чёрный экран.
# Фикс: явно обнулить альфа-канал через colorchannelmixer=aa=0.0 после
# format=rgba — это реально даёт alpha=0 по всему кадру.
parts.append(f"[{canvas_idx}:v]format=rgba,colorchannelmixer=aa=0.0,split=2[cap{n}_tg][cap{n}_tc]")

# серая ветка: по очереди КАЖДАЯ СТРОКА каждого чанка — отдельный
# drawtext со своим центрирующим x (см. compute_word_layout.py), вместо
# одного multiline-вызова с фиксированным левым x (у ffmpeg drawtext нет
# built-in центрирования multiline-блока со строками разной длины).
prev_g = f"cap{n}_tg"
for ci, chunk in enumerate(chunks):
    is_last = ci == len(chunks) - 1
    cond = f"gte(t\\,{chunk['start']})" if is_last else f"between(t\\,{chunk['start']}\\,{chunk['end']})"
    for li, lf in enumerate(chunk["line_files"]):
        nxt = f"cap{n}_g{ci+1}_{li+1}"
        x = panel["tx"] + lf["x_offset"]
        y = panel["ty0"] + li * panel["line_height"]
        parts.append(
            f"[{prev_g}]drawtext=fontfile={FONT}:fontcolor={BASE_COLOR}:fontsize={FONTSIZE}:"
            f"textfile={lf['file']}:x={x}:y={y}:"
            f"enable={cond}[{nxt}]"
        )
        prev_g = nxt
grey_layer = prev_g

# коралловая ветка: те же строки, те же центрированные x/y — только цвет другой
prev_c = f"cap{n}_tc"
for ci, chunk in enumerate(chunks):
    is_last = ci == len(chunks) - 1
    cond = f"gte(t\\,{chunk['start']})" if is_last else f"between(t\\,{chunk['start']}\\,{chunk['end']})"
    for li, lf in enumerate(chunk["line_files"]):
        nxt = f"cap{n}_c{ci+1}_{li+1}"
        x = panel["tx"] + lf["x_offset"]
        y = panel["ty0"] + li * panel["line_height"]
        parts.append(
            f"[{prev_c}]drawtext=fontfile={FONT}:fontcolor={HL_COLOR}:fontsize={FONTSIZE}:"
            f"textfile={lf['file']}:x={x}:y={y}:"
            f"enable={cond}[{nxt}]"
        )
        prev_c = nxt
coral_layer = prev_c

# наложить серый слой текста на видео
after_grey = f"cap{n}_wg"
parts.append(f"[{p2}][{grey_layer}]overlay=0:0[{after_grey}]")

# ffmpeg не разрешает использовать один и тот же labelled-выход
# несколько раз как вход разных фильтров ("Stream specifier matches no
# streams" при повторном использовании) — поэтому явно размножаем
# coral_layer через split на N копий, по одной на каждое слово сцены.
all_words = [(ci, wi, w) for ci, chunk in enumerate(chunks) for wi, w in enumerate(chunk["words"])]
n_words = len(all_words)
coral_copies = [f"cap{n}_cc{i+1}" for i in range(n_words)]
parts.append(f"[{coral_layer}]split={n_words}[" + "][".join(coral_copies) + "]")

# по каждому слову (по всем чанкам подряд) — вырезать его прямоугольник
# из своей копии коралловой отрисовки и наложить точно в ту же позицию
# поверх серого
prev = after_grey
PAD_X = 6
PAD_Y_TOP = 10
PAD_Y_BOT = 16
for idx, (ci, wi, w) in enumerate(all_words):
    is_final = idx == n_words - 1
    wcond = f"gte(t\\,{w['start']})" if is_final else f"between(t\\,{w['start']}\\,{w['end']})"
    y = panel["ty0"] + w["line"] * panel["line_height"]
    x = panel["tx"] + w["x"]
    crop_w = round(w["width"] + PAD_X * 2)
    crop_x = round(x - PAD_X)
    crop_y = round(y - PAD_Y_TOP)
    crop_h = round(FONTSIZE + PAD_Y_TOP + PAD_Y_BOT)
    crop_label = f"cap{n}_crop{ci+1}_{wi+1}"
    parts.append(f"[{coral_copies[idx]}]crop={crop_w}:{crop_h}:{crop_x}:{crop_y}[{crop_label}]")
    nxt = out_label if is_final else f"cap{n}_ov{ci+1}_{wi+1}"
    parts.append(f"[{prev}][{crop_label}]overlay={crop_x}:{crop_y}:enable={wcond}[{nxt}]")
    prev = nxt

print(";".join(parts))
