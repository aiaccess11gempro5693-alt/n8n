import subprocess

import os
R = os.path.dirname(os.path.abspath(__file__))
scenes = [1,2,3,4,5,6,7,8]

# Раньше везде был один и тот же fade 0.5с независимо от смысла сцены.
# Теперь тип/длительность перехода зависит от того, ВО ЧТО въезжаем:
# заход в сцену с данными (иллюстрация/инфографика) — более энергичный
# wipe покороче, сигнализирует "новая информация"; заход обратно к
# говорящей голове или между двумя соседними data-сценами — спокойный
# fade, чтобы не мельтешить одним и тем же приёмом подряд.
SCENE_KIND = {1: "avatar", 2: "data", 3: "data", 4: "avatar", 5: "data", 6: "data", 7: "avatar", 8: "avatar"}

def transition_for(prev_n, next_n):
    if SCENE_KIND[next_n] == "data" and SCENE_KIND[prev_n] != "data":
        return "smoothleft", 0.35
    return "fade", 0.5

def dur(path):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",path], capture_output=True, text=True).stdout.strip()
    return float(out)

durs = [dur(f"{R}/scene-{n}.mp4") for n in scenes]
print("durations:", durs)

inputs = []
for n in scenes:
    inputs += ["-i", f"{R}/scene-{n}.mp4"]

filter_parts = []
cum = durs[0]
prev_v = "0:v"
prev_a = "0:a"
for i in range(1, len(scenes)):
    trans, T = transition_for(scenes[i-1], scenes[i])
    offset = cum - T
    outv = f"v{i}" if i < len(scenes)-1 else "vout"
    outa = f"a{i}" if i < len(scenes)-1 else "aout"
    filter_parts.append(f"[{prev_v}][{i}:v]xfade=transition={trans}:duration={T}:offset={offset:.3f}[{outv}]")
    filter_parts.append(f"[{prev_a}][{i}:a]acrossfade=d={T}[{outa}]")
    prev_v = outv
    prev_a = outa
    cum = cum + durs[i] - T
    print(f"  scene {scenes[i-1]}->{scenes[i]}: {trans} ({T}s)")

# Примечание: пробовали добавить растущий прогресс-бар (drawbox с шириной
# от t/total_duration) поверх [vout] — в этой сборке ffmpeg (6.1.1) drawbox
# не пересчитывает w/x по кадрам от 't' вне триггера enable (подтверждено
# изолированными тестами: ширина остаётся константной с первого кадра),
# а с enable получается только вкл/выкл, не плавный рост. Отказались от
# этого элемента, чтобы не показывать сломанный статичный бар.

# Тихая амбиентная подложка (синтезированная — не лицензированный трек,
# честный плейсхолдер вместо полной тишины) смешивается под уже готовую
# дорожку реплик. normalize=0, чтобы amix не просаживал громкость речи
# вдвое просто потому что входов два.
ambient_idx = len(scenes)
inputs += ["-i", f"{R}/ambient_bed.m4a"]
filter_parts.append(f"[aout][{ambient_idx}:a]amix=inputs=2:duration=first:normalize=0[afinal]")

filter_complex = ";".join(filter_parts)
print("total duration:", cum)

cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", filter_complex,
    "-map", "[vout]", "-map", "[afinal]",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "25",
    "-c:a", "aac", "-b:a", "192k",
    f"{R}/final_test_video.mp4"
]

with open(f"{R}/concat_cmd.sh", "w") as f:
    f.write("#!/bin/bash\nset -e\n")
    f.write(" ".join(f'"{c}"' if " " in c or "[" in c else c for c in cmd))
    f.write("\n")

print("written concat_cmd.sh")
