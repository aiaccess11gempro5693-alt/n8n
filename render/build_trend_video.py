"""
Финальная сборка — единый presentation-слой (design-system.md, "9.
Композиционный движок" + переработка 17.09.2026 (5): editorial-стиль вместо
"иконка+тёмная карточка"). Всё, что раньше было отдельно "иконки-стикеры на
data-сценах" (шаг 2, ffmpeg dilation-фильтры) и "заголовки" (шаг 6, pill-бейдж
в (60,60) из render_headlines.py) — теперь ОДИН проход: presentation/compose_scene.py
собирает для КАЖДОЙ из 8 сцен готовый набор PNG-слоёв (statement/annotated
grid/checklist/comparison — что уместно по смыслу сцены), этот скрипт только
накладывает их на общий таймлайн с той же "тихой зоной" вокруг переходов, что
и субтитры.

Сохранено без изменений: Ken Burns/punch-in на аватаре, переходы между
сценами, субтитры (crop-маска караоке).

Legacy (не используется в этом пути, оставлено в render/legacy/ для
истории): layout_engine.py (вчерашний движок координат), render_headlines.py
(PLAN — заменён content_model.py), render_icon_scenes.py, render_scenes.sh.
"""
import json
import os
import subprocess
import sys

RENDER = os.path.dirname(os.path.abspath(__file__))
WL = RENDER
OUT_DIR = RENDER
FONT = f"{RENDER}/fonts/Inter-Bold.otf"
FINAL_SCENES = "/tmp/final-scenes"

sys.path.insert(0, RENDER)
from presentation.compose_scene import compose_scene  # noqa: E402

with open(f"{WL}/word_layout.json", encoding="utf-8") as f:
    manifest = json.load(f)
PANEL = manifest["panel"]
SCENES_WL = manifest["scenes"]
FONTSIZE = 40
BASE_COLOR = "0x2B2F33"
HL_COLOR = "0xF2836B"
PANEL_COLOR = "0xF7F9FB"
ACCENT = "0x2A7F82"

SCENE_KIND = {1: "avatar", 2: "data", 3: "data", 4: "avatar", 5: "data", 6: "data", 7: "avatar", 8: "avatar"}


def transition_for(prev_n, next_n):
    if SCENE_KIND[next_n] == "data" and SCENE_KIND[prev_n] != "data":
        return "smoothleft", 0.35
    return "fade", 0.5


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    ).stdout.strip()
    return float(out)


def run(cmd, label):
    print(f"=== {label} ===", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FFMPEG STDERR TAIL:\n", r.stderr[-4000:])
        raise SystemExit(f"{label} failed")
    print(f"{label} OK", flush=True)


scenes = [1, 2, 3, 4, 5, 6, 7, 8]
durs = {n: dur(f"{FINAL_SCENES}/scene-{n}.mp4") for n in scenes}
print("durations:", durs)

PUNCH = {1: 1.122, 8: 2.614}  # секунда триггерного слова для punch-in

# ---------- шаг 1: Ken Burns (+punch) на каждый сырой клип аватара (канон, не менялся) ----------
kb_paths = {}
for n in scenes:
    D = durs[n]
    K = 0.05 if SCENE_KIND[n] == "avatar" else 0.035
    zoom = f"(1.0+{K}*(t/{D}))"
    if n in PUNCH:
        T = PUNCH[n]
        zoom += f"+0.05*clip(min((t-({T}-0.4))/0.4\\,({T}+2.1-t)/0.6)\\,0\\,1)"
    out_path = f"{OUT_DIR}/kb-scene-{n}.mp4"
    run([
        "ffmpeg", "-y", "-i", f"{FINAL_SCENES}/scene-{n}.mp4",
        "-vf",
        f"scale=w='trunc(1920*({zoom})/2)*2':h='trunc(1080*({zoom})/2)*2':eval=frame,"
        f"crop=1920:1080:x='(iw-1920)/2':y='(ih-1080)/2'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "copy",
        out_path,
    ], f"scene{n} ken burns" + (" + punch" if n in PUNCH else ""))
    kb_paths[n] = out_path

# presentation-слой (иконки/statement/checklist/comparison) больше НЕ
# запекается в клип каждой сцены по отдельности — он идёт единым проходом
# ПОСЛЕ crossfade (шаг 6 ниже), на общем таймлайне, с той же "тихой зоной"
# вокруг переходов, что и субтитры. video_paths = kb_paths напрямую.
video_paths = kb_paths

# ---------- шаг 2: crossfade всех 8 видео-слоёв (БЕЗ текста) ----------
inputs = []
for n in scenes:
    inputs += ["-i", video_paths[n]]

filter_parts = []
g0 = {1: 0.0}          # глобальное время начала (локальный t=0) каждой сцены
trans_dur_in = {1: 0.0}   # длительность входящего перехода (0 для первой сцены)
cum = durs[1]
prev_v, prev_a = "0:v", "0:a"
for i in range(1, len(scenes)):
    prev_n, next_n = scenes[i - 1], scenes[i]
    trans, T = transition_for(prev_n, next_n)
    off = cum - T
    g0[next_n] = off
    trans_dur_in[next_n] = T
    outv = f"v{i}" if i < len(scenes) - 1 else "vout"
    outa = f"a{i}" if i < len(scenes) - 1 else "aout"
    filter_parts.append(f"[{prev_v}][{i}:v]xfade=transition={trans}:duration={T}:offset={off:.3f}[{outv}]")
    filter_parts.append(f"[{prev_a}][{i}:a]acrossfade=d={T}[{outa}]")
    prev_v, prev_a = outv, outa
    cum = cum + durs[next_n] - T
    print(f"  {prev_n}->{next_n}: {trans} ({T}s) global_start={off:.3f}")

combined_dur = cum
print("combined_dur", combined_dur)

ambient_idx = len(scenes)
inputs += ["-i", f"{RENDER}/ambient_bed.m4a"]
filter_parts.append(f"[{prev_a}][{ambient_idx}:a]amix=inputs=2:duration=first:normalize=0[afinal]")

combined_video = f"{OUT_DIR}/combined-full.mp4"
run([
    "ffmpeg", "-y", *inputs,
    "-filter_complex", ";".join(filter_parts),
    "-map", "[vout]", "-map", "[afinal]",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "25",
    "-c:a", "aac", "-b:a", "192k",
    combined_video,
], "crossfade combine (8 scenes)")

# ---------- шаг 3: границы "текст должен молчать" вокруг каждого перехода (канон) ----------
TEXT_OUT_BEFORE = 0.35
TEXT_IN_AFTER = 0.10

trans_dur_out = {}
for i in range(1, len(scenes)):
    trans_dur_out[scenes[i - 1]] = trans_dur_in[scenes[i]]
trans_dur_out[scenes[-1]] = 0.0

local_start_delay = {}
local_end_cut = {}
for idx, n in enumerate(scenes):
    T_in = trans_dur_in[n]
    T_out = trans_dur_out[n]
    local_start_delay[n] = (T_in + TEXT_IN_AFTER) if idx > 0 else 0.0
    local_end_cut[n] = (durs[n] - T_out - TEXT_OUT_BEFORE) if idx < len(scenes) - 1 else durs[n]

cap_start_global = {n: g0[n] + local_start_delay[n] for n in scenes}
cap_end_global = {n: g0[n] + local_end_cut[n] for n in scenes}
for n in scenes:
    print(f"scene {n}: g0={g0[n]:.3f} quiet_zone=[{cap_start_global[n]:.3f}, {cap_end_global[n]:.3f}]")

# ---------- шаг 4: субтитры (crop-маска) по всем 8 сценам на общем таймлайне (канон) ----------
cap_chunks = []
for n in scenes:
    chunks = SCENES_WL[str(n)]["chunks"]
    for ci, chunk in enumerate(chunks):
        g_start = max(chunk["start"] + g0[n], cap_start_global[n])
        g_end = min(chunk["end"] + g0[n], cap_end_global[n])
        if g_start >= cap_end_global[n] or g_end <= cap_start_global[n]:
            continue
        is_last_overall = (n == scenes[-1]) and (ci == len(chunks) - 1)
        lines = [
            {"file": lf["file"], "x": PANEL["tx"] + lf["x_offset"], "y": PANEL["ty0"] + li * PANEL["line_height"]}
            for li, lf in enumerate(chunk["line_files"])
        ]
        words = []
        for w in chunk["words"]:
            ws = w["start"] + g0[n]
            we = w["end"] + g0[n]
            ws = max(ws, cap_start_global[n])
            we = min(we, cap_end_global[n])
            if we <= ws:
                continue
            words.append({"text": w["text"], "start": ws, "end": we,
                          "x": PANEL["tx"] + w["x"], "y": PANEL["ty0"] + w["line"] * PANEL["line_height"],
                          "width": w["width"]})
        cap_chunks.append({"start": g_start, "end": g_end, "is_last": is_last_overall, "lines": lines, "words": words})

inputs = ["-i", combined_video]
inputs += ["-f", "lavfi", "-i", f"color=c=black@0.0:s=1920x1080:r=25:d={combined_dur}"]
CANVAS_IDX = 1

fc2 = []
prev = "0:v"

# панели (фон+акцент) — по одной enable-полосе на сцену
for n in scenes:
    pn = f"panel{n}"
    fc2.append(f"[{prev}]drawbox=x={PANEL['x']}:y={PANEL['y']}:w={PANEL['w']}:h={PANEL['h']}:"
               f"color={PANEL_COLOR}@0.94:t=fill:enable='between(t,{cap_start_global[n]},{cap_end_global[n]})'[{pn}]")
    prev = pn
    an = f"acc{n}"
    fc2.append(f"[{prev}]drawbox=x={PANEL['x']}:y={PANEL['y']}:w={PANEL['accent_bar_w']}:h={PANEL['h']}:"
               f"color={ACCENT}@1.0:t=fill:enable='between(t,{cap_start_global[n]},{cap_end_global[n]})'[{an}]")
    prev = an

for ci, cc in enumerate(cap_chunks):
    cond = f"gte(t,{cc['start']})" if cc["is_last"] else f"between(t,{cc['start']},{cc['end']})"
    for li, lf in enumerate(cc["lines"]):
        nxt = f"cg{ci}_{li}"
        fc2.append(
            f"[{prev}]drawtext=fontfile={FONT}:fontcolor={BASE_COLOR}:fontsize={FONTSIZE}:"
            f"textfile={lf['file']}:x={lf['x']}:y={lf['y']}:enable='{cond}'[{nxt}]"
        )
        prev = nxt
after_grey = prev

fc2.append(f"[{CANVAS_IDX}:v]format=rgba,colorchannelmixer=aa=0.0[cap_tc]")
prev_c = "cap_tc"
for ci, cc in enumerate(cap_chunks):
    cond = f"gte(t,{cc['start']})" if cc["is_last"] else f"between(t,{cc['start']},{cc['end']})"
    for li, lf in enumerate(cc["lines"]):
        nxt = f"cc{ci}_{li}"
        fc2.append(
            f"[{prev_c}]drawtext=fontfile={FONT}:fontcolor={HL_COLOR}:fontsize={FONTSIZE}:"
            f"textfile={lf['file']}:x={lf['x']}:y={lf['y']}:enable='{cond}'[{nxt}]"
        )
        prev_c = nxt
coral_layer = prev_c

all_words = [(ci, w) for ci, cc in enumerate(cap_chunks) for w in cc["words"]]
n_words = len(all_words)
coral_copies = [f"capcc{i}" for i in range(n_words)]
fc2.append(f"[{coral_layer}]split={n_words}[" + "][".join(coral_copies) + "]")

PAD_X, PAD_Y_TOP, PAD_Y_BOT = 6, 10, 16
prev = after_grey
for idx, (ci, w) in enumerate(all_words):
    is_final = idx == n_words - 1
    wcond = f"gte(t,{w['start']})" if is_final else f"between(t,{w['start']},{w['end']})"
    crop_w = round(w["width"] + PAD_X * 2)
    crop_x = round(w["x"] - PAD_X)
    crop_y = round(w["y"] - PAD_Y_TOP)
    crop_h = round(FONTSIZE + PAD_Y_TOP + PAD_Y_BOT)
    crop_label = f"capcrop{idx}"
    fc2.append(f"[{coral_copies[idx]}]crop={crop_w}:{crop_h}:{crop_x}:{crop_y}[{crop_label}]")
    nxt = f"capov{idx}"
    fc2.append(f"[{prev}][{crop_label}]overlay={crop_x}:{crop_y}:enable='{wcond}'[{nxt}]")
    prev = nxt

# ---------- шаг 5: presentation-слой (headline/statement/annotated grid/
# checklist/comparison — что уместно по смыслу каждой сцены), на глобальном
# таймлайне, обрезано под ту же "тихую" зону, что и субтитры/раньше заголовки.
# Каждый layer — уже полностью отрисованный PIL PNG (текст+иконка+scrim
# запечены внутри), ffmpeg только накладывает его с плавным fade+лёгким
# подъездом снизу (design-system.md, '13. Timing' — спокойный motion, не
# "стикер поп-ин") ----------
PRES_DIR = f"{RENDER}/presentation_out"
os.makedirs(PRES_DIR, exist_ok=True)

pres_layers = []  # (path, x, y, global_start, global_end)
for n in scenes:
    layout, layers = compose_scene(n)
    print(f"scene {n}: presentation layout={layout}, {len(layers)} layer(s)")
    for i, l in enumerate(layers):
        path = f"{PRES_DIR}/p{n}-{i}.png"
        l.image.save(path)
        gs = max(g0[n] + l.start, cap_start_global[n])
        ge = (g0[n] + l.end) if l.end is not None else cap_end_global[n]
        ge = min(ge, cap_end_global[n])
        if ge <= gs:
            print(f"  !! слой {i} сцены {n} вне тихой зоны, пропущен (gs={gs:.3f} ge={ge:.3f})")
            continue
        pres_layers.append((path, l.x, l.y, gs, ge))

for p, *_ in pres_layers:
    inputs += ["-i", p]

FADE = 0.3
RISE = 18
for idx, (p, X, Y, GS, GE) in enumerate(pres_layers):
    pin_idx = idx + 2  # 0 = combined_video, 1 = прозрачный холст
    ease_in = f"max(0,1-(t-{GS})/{FADE})"
    faded = f"pf{idx}"
    fc2.append(
        f"[{pin_idx}:v]format=rgba,"
        f"fade=t=in:st={GS}:d={FADE}:alpha=1,"
        f"fade=t=out:st={GE - FADE}:d={FADE}:alpha=1[{faded}]"
    )
    nxt = f"pv{idx}"
    fc2.append(f"[{prev}][{faded}]overlay=x={X}:y='{Y}+{RISE}*{ease_in}':enable='between(t,{GS},{GE})'[{nxt}]")
    prev = nxt

filter_complex = ";\n".join(fc2)
final_out = f"{OUT_DIR}/full-trend-video.mp4"
cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", filter_complex,
    "-map", f"[{prev}]", "-map", "0:a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "25",
    "-c:a", "aac", "-b:a", "192k",
    final_out,
]
run(cmd, "final presentation-layer pass (8 scenes)")
print("DONE ->", final_out)
