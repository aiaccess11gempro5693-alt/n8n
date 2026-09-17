"""
Финальная сборка (шаг 5, заменяет build_concat_cmd.py) — 17.09.2026,
"современный монтаж" вместо голых наложений (см. design-system.md, раздел
"Динамика кадра и переходы (17.09.2026)"):
  A. Ken Burns (медленный зум на аватаре весь ролик).
  B. punch-in на 1-2 ключевых репликах за ролик (не на каждой сцене).
  C. заголовок — overshoot-scale вместо слайда (иконки/подписи — слайд, как раньше).
  D. переход между сценами не показывает тексты двух сцен одновременно —
     текст гаснет ДО перехода, кроссфейдится только видео, текст следующей
     сцены появляется ПОСЛЕ перехода.
Субтитры — через ту же crop-маску, что и раньше (без "двоения" слов).

Под новый сценарий правь: PUNCH{}, ICON_SCENES (иконки те же, что раньше
задавались в render_icon_scenes.py), HEADLINE_PLAN берётся из
render_headlines.py как раньше.
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
ICONS = "/home/user/n8n/scratch"

sys.path.insert(0, RENDER)
from pill_gen_all import rounded_pill, TEAL, CORAL  # noqa: E402
from render_headlines import PLAN as HEADLINE_PLAN  # noqa: E402

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


def clamp(x, lo, hi):
    return max(lo, min(x, hi))


scenes = [1, 2, 3, 4, 5, 6, 7, 8]
durs = {n: dur(f"{FINAL_SCENES}/scene-{n}.mp4") for n in scenes}
print("durations:", durs)

PUNCH = {1: 1.122, 8: 2.614}  # секунда триггерного слова для punch-in

# ---------- шаг 1: Ken Burns (+punch) на каждый сырой клип аватара ----------
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

# ---------- шаг 2: иконки-стикеры на data-сценах (2,3,5,6) ----------
with open(f"{WL}/pills/pill_info.json") as f:
    pinfo = json.load(f)
with open(f"{WL}/pills/pill_info5.json") as f:
    pinfo5 = json.load(f)


def below_pos(icon_x, icon_sz, pill_w, gap=30):
    center = icon_x + icon_sz / 2
    return round(clamp(center - pill_w / 2, 20, 1920 - 20 - pill_w))


def beside_pos(icon_x, icon_y, icon_sz, pill_h, gap=30):
    return icon_x + icon_sz + gap, round(icon_y + (icon_sz - pill_h) / 2)


m = pinfo["scene2-pill1"]
X, Y, SZ = 1350, 180, 520
bx = below_pos(X, SZ, m["pill_w"]); by = Y + SZ + 30
scene2_icons = [dict(png=f"{ICONS}/scene2-icon1.png", x=X, y=Y, sz=SZ, start=8.3,
                      label="Добраться до сути", pill_png=f"{WL}/pills/scene2-pill1.png",
                      pill_w=m["pill_w"], pill_h=m["pill_h"], pill_margin=m["margin"],
                      pill_bx=bx, pill_by=by, fs=34)]

SZ3 = 330; XL, XR, Y0, Y1 = 60, 1540, 60, 460
defs3 = [
    ("scene3-icon1.png", XL, Y0, 7.15, "Болеет каждую осень", "scene3-pill1"),
    ("scene3-icon2.png", XR, Y0, 12.13, "Слабость после ОРВИ", "scene3-pill2"),
    ("scene3-icon3.png", XL, Y1, 15.56, "Просто устал", "scene3-pill3"),
    ("scene3-icon4.png", XR, Y1, 20.81, "Уже принимает БАДы", "scene3-pill4"),
]
scene3_icons = []
for png, x, y, st, label, pillname in defs3:
    mm = pinfo[pillname]
    bx = below_pos(x, SZ3, mm["pill_w"]); by = y + SZ3 + 30
    scene3_icons.append(dict(png=f"{ICONS}/{png}", x=x, y=y, sz=SZ3, start=st, label=label,
                              pill_png=f"{WL}/pills/{pillname}.png", pill_w=mm["pill_w"], pill_h=mm["pill_h"],
                              pill_margin=mm["margin"], pill_bx=bx, pill_by=by, fs=34))

SZ5 = 110; ICX = 1300
rows5 = [50, 220, 390, 560]
defs5 = [
    (rows5[0], 2.92, "Что именно беспокоит?", "scene5-pill1", "scene5-icon1.png"),
    (rows5[1], 11.28, "Длительность симптомов", "scene5-pill2", "scene5-icon2.png"),
    (rows5[2], 14.26, "Приём других препаратов", "scene5-pill3", "scene5-icon3.png"),
    (rows5[3], 19.86, "Хронические заболевания", "scene5-pill4", "scene5-icon4.png"),
]
scene5_icons = []
for y, st, label, pillname, png in defs5:
    mm = pinfo5[pillname]
    bx, by = beside_pos(ICX, y, SZ5, mm["pill_h"])
    scene5_icons.append(dict(png=f"{ICONS}/{png}", x=ICX, y=y, sz=SZ5, start=st, label=label,
                              pill_png=f"{WL}/pills/{pillname}.png", pill_w=mm["pill_w"], pill_h=mm["pill_h"],
                              pill_margin=mm["margin"], pill_bx=bx, pill_by=by, fs=28))

SZ6 = 470
defs6 = [
    ("scene6-icon1.png", 80, 120, 13.79, "Излишняя стимуляция", "scene6-pill1", 472, 89),
    ("scene6-icon2.png", 1400, 120, 17.2, "Восстановительная поддержка", "scene6-pill2", 627, 89),
]
scene6_icons = []
for png, x, y, st, label, pillname, pw, ph in defs6:
    bx = below_pos(x, SZ6, pw); by = 620
    scene6_icons.append(dict(png=f"{ICONS}/{png}", x=x, y=y, sz=SZ6, start=st, label=label,
                              pill_png=f"{WL}/pills/{pillname}.png", pill_w=pw, pill_h=ph,
                              pill_margin=40, pill_bx=bx, pill_by=by, fs=34))

ICON_SCENES = {2: scene2_icons, 3: scene3_icons, 5: scene5_icons, 6: scene6_icons}
CKEY = "colorkey=0xE91E8F:0.35:0.12"


def render_icons(scene_n, icons, base_path, out_path, D):
    inputs = ["-i", base_path]
    for ic in icons:
        inputs += ["-i", ic["png"]]
    for ic in icons:
        inputs += ["-i", ic["pill_png"]]
    n = len(icons)
    fc = []
    for i, ic in enumerate(icons):
        idx = i + 1
        fc.append(f"[{idx}:v]scale={ic['sz']}:{ic['sz']},{CKEY},eq=saturation=1.4:contrast=1.1:brightness=0.03,format=rgba,split=2[icon{idx}clean_a][icon{idx}clean_b]")
        fc.append(f"[icon{idx}clean_a]alphaextract,split=2[mask{idx}_a][mask{idx}_b]")
        fc.append(f"[mask{idx}_a]" + ",".join(["dilation"] * 7) + f"[mask{idx}_outline]")
        fc.append(f"[mask{idx}_b]" + ",".join(["dilation"] * 10) + f",gblur=sigma=6[mask{idx}_shadow]")
        fc.append(f"color=0xFFFFFF:s={ic['sz']}x{ic['sz']}[white{idx}]")
        fc.append(f"[white{idx}][mask{idx}_outline]alphamerge[outline{idx}]")
        fc.append(f"color=0x000000:s={ic['sz']}x{ic['sz']}[black{idx}]")
        fc.append(f"[black{idx}][mask{idx}_shadow]alphamerge,colorchannelmixer=aa=0.45[shadow{idx}]")
    fc.append("[0:v]scale=1920:1080[base]")
    prev = "base"
    for i, ic in enumerate(icons):
        idx = i + 1
        Xc, Yc, ST = ic["x"], ic["y"], ic["start"]
        ease = f"max(0,1-(t-{ST})/0.35)"
        nxt = f"s{idx}a"
        fc.append(f"[{prev}][shadow{idx}]overlay=x={Xc}+10:y='{Yc}+14-40*{ease}':enable='gte(t,{ST})'[{nxt}]")
        prev = nxt
        nxt = f"s{idx}b"
        fc.append(f"[{prev}][outline{idx}]overlay=x={Xc}:y='{Yc}-40*{ease}':enable='gte(t,{ST})'[{nxt}]")
        prev = nxt
        nxt = f"s{idx}c"
        fc.append(f"[{prev}][icon{idx}clean_b]overlay=x={Xc}:y='{Yc}-40*{ease}':enable='gte(t,{ST})'[{nxt}]")
        prev = nxt
    for i, ic in enumerate(icons):
        idx = i + 1
        pin = f"{n + idx}:v"
        PST = round(ic["start"] + 0.15, 3)
        pease = f"max(0,1-(t-{PST})/0.3)"
        BX, BY, PW, PH = ic["pill_bx"], ic["pill_by"], ic["pill_w"], ic["pill_h"]
        MARGIN = ic["pill_margin"]
        OX, OY = BX - MARGIN, BY - MARGIN
        nxt = f"p{idx}a"
        fc.append(f"[{prev}][{pin}]overlay=x={OX}:y='{OY}-30*{pease}':enable='gte(t,{PST})'[{nxt}]")
        prev = nxt
        nxt = f"p{idx}b"
        label_esc = ic["label"].replace("'", r"\'").replace(":", r"\:")
        fc.append(
            f"[{prev}]drawtext=fontfile={FONT}:fontcolor=white:fontsize={ic['fs']}:text='{label_esc}':"
            f"shadowcolor=black@0.35:shadowx=1:shadowy=1:"
            f"x={BX}+({PW}-text_w)/2:y='{BY}+({PH}-text_h)/2-30*{pease}':"
            f"enable='gte(t,{PST})':alpha='min((t-{PST})/0.25\\,1)'[{nxt}]"
        )
        prev = nxt
    filter_complex = ";\n".join(fc)
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", f"[{prev}]", "-map", "0:a", "-t", str(D),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "copy",
        out_path,
    ]
    run(cmd, f"scene{scene_n} icon overlay")


video_paths = {}
for n in scenes:
    if n in ICON_SCENES:
        out_path = f"{OUT_DIR}/video-scene-{n}.mp4"
        render_icons(n, ICON_SCENES[n], kb_paths[n], out_path, durs[n])
        video_paths[n] = out_path
    else:
        video_paths[n] = kb_paths[n]

# ---------- шаг 3: crossfade всех 8 видео-слоёв (БЕЗ текста) ----------
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

# ---------- шаг 4: границы "текст должен молчать" вокруг каждого перехода ----------
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
    print(f"scene {n}: g0={g0[n]:.3f} text_window=[{cap_start_global[n]:.3f}, {cap_end_global[n]:.3f}]")

# ---------- шаг 5: субтитры (crop-маска) по всем 8 сценам на общем таймлайне ----------
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

# ---------- шаг 6: заголовки (overshoot-scale), по PLAN из render_headlines.py,
# переведённые на глобальное время и обрезанные под "тихую" зону перехода ----------
pill_inputs = []
for n in scenes:
    for i, seg in enumerate(HEADLINE_PLAN[n]):
        start = seg["start"] + g0[n]
        start = max(start, cap_start_global[n])
        end = seg.get("end")
        if end is None:
            end = cap_end_global[n]
        else:
            end = min(end + g0[n], cap_end_global[n])
        if end <= start:
            continue
        name = f"h{n}-{i}"
        meta = rounded_pill(f"{OUT_DIR}/{name}.png", seg["text"], seg["fs"], seg["color"], pad_x=40, pad_y=22)
        pill_inputs.append((f"{OUT_DIR}/{name}.png", meta, seg["text"], seg["fs"], start, end))

for p, *_ in pill_inputs:
    inputs += ["-i", p]

SLIDE_OVERSHOOT = 1.14
POP1 = 0.16
POP2 = 0.30

for idx, (p, meta, text, fs, start, end) in enumerate(pill_inputs):
    pin_idx = idx + 2  # 0 = combined_video, 1 = прозрачный холст
    OW, OH = meta["outer_w"], meta["outer_h"]
    bx, by = 60, 60
    margin = meta["margin"]
    ox, oy = bx - margin, by - margin
    cond = f"between(t,{start},{end})"
    s_expr = (
        f"if(lt(t,{start}),0,"
        f"if(lt(t,{start}+{POP1}),(t-{start})/{POP1}*{SLIDE_OVERSHOOT},"
        f"if(lt(t,{start}+{POP2}),{SLIDE_OVERSHOOT}-(t-{start}-{POP1})/({POP2}-{POP1})*({SLIDE_OVERSHOOT}-1.0),1.0)))"
    )
    scaled = f"pillscaled{idx}"
    fc2.append(f"[{pin_idx}:v]scale=w='trunc({OW}*({s_expr}))':h='trunc({OH}*({s_expr}))':eval=frame[{scaled}]")
    nxt = f"hd{idx}"
    fc2.append(
        f"[{prev}][{scaled}]overlay="
        f"x='{ox}+({OW}-{OW}*({s_expr}))/2':y='{oy}+({OH}-{OH}*({s_expr}))/2':"
        f"enable='{cond}'[{nxt}]"
    )
    prev = nxt
    text_esc = text.replace("'", r"\'").replace(":", r"\:")
    nxt2 = f"hdt{idx}"
    fc2.append(
        f"[{prev}]drawtext=fontfile={FONT}:fontcolor=white:fontsize={fs}:text='{text_esc}':"
        f"shadowcolor=black@0.35:shadowx=1:shadowy=1:"
        f"x={bx}+({meta['pill_w']}-text_w)/2:y={by}+({meta['pill_h']}-text_h)/2:"
        f"enable='{cond}':alpha='min((t-{start})/0.2\\,1)'[{nxt2}]"
    )
    prev = nxt2

filter_complex = ";\n".join(fc2)
final_out = f"{OUT_DIR}/full-trend-video.mp4"
cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", filter_complex,
    "-map", f"[{prev}]", "-map", "0:a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "25",
    "-c:a", "aac", "-b:a", "192k",
    final_out,
]
run(cmd, "final text pass (8 scenes)")
print("DONE ->", final_out)
