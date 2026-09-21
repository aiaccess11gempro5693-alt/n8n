"""
Финальная сборка — новая визуальная система (17.09.2026 (7), спроектирована
с нуля после RESET по мастер-промпту "новая visual system с нуля"). Канон
(не тронут этим этапом):

  1. Ken Burns (+punch-in) на аватаре.
  2. Переходы между сценами (crossfade).
  3. Субтитры (crop-маска караоке, синхронизация по словам).

Плюс новый presentation-слой — `render/visual/` (CONTENT -> SEMANTIC ->
VISUAL_CONCEPT -> COMPOSITION -> LAYOUT -> VALIDATION -> RENDER, см.
`render/visual/README.md`). Это typography-driven editorial-графика
(заголовки/списки/чек-листы/сравнения), а НЕ возврат старых icon+pill/card
решений — они удалены из истории 17.09.2026 и не переиспользуются.
"""
import json
import os
import subprocess

from visual.render_visual_layer import build_all as build_visual_layer
from visual.semantic_analysis import analyze_scenes

RENDER = os.path.dirname(os.path.abspath(__file__))
WL = RENDER
OUT_DIR = RENDER
FONT = f"{RENDER}/fonts/Inter-Bold.otf"
FINAL_SCENES = "/tmp/final-scenes"

with open(f"{WL}/word_layout.json", encoding="utf-8") as f:
    manifest = json.load(f)

PANEL = manifest["panel"]
SCENES_WL = manifest["scenes"]

# Тот же текст, что и NARRATION в compute_word_layout.py (канон, источник
# истины по субтитрам/таймингу — не трогаем тот файл, чтобы не рисковать
# пересчётом word_layout.json/text/*; дублирование текста здесь безопаснее,
# чем импорт модуля с side-effects на верхнем уровне).
NARRATION = {
    1: 'Здравствуйте. "Иммунитет" — пожалуй, одно из самых популярных слов в современной аптеке. Люди слышат его в рекламе, читают в интернете, обсуждают с друзьями. И приходят к вам с ощущением, что знают, чего хотят.',
    2: 'Но за этим уверенным запросом почти всегда стоит что-то конкретное — то, что человек пока не сформулировал. И именно фармацевт помогает добраться до сути.',
    3: 'Итак, покупатель говорит: "Дайте что-нибудь для иммунитета". Что он имеет в виду? Возможно, он болеет каждую осень и хочет это изменить. Возможно, только недавно перенёс ОРВИ и чувствует слабость. Возможно, просто устал и решил, что виноват "плохой иммунитет". А возможно, он уже принимает три разных БАДа и хочет добавить четвёртый.',
    4: 'Каждая из этих ситуаций требует разного ответа. И только уточнив запрос, вы сможете дать рекомендацию, которая реально поможет, а не просто "что-то от иммунитета".',
    5: 'Помогут несколько простых вопросов: что именно вас беспокоит — частые простуды, постоянная усталость, долгое восстановление после болезни? Как давно вы замечаете это состояние? Принимаете ли сейчас какие-то витамины, добавки или препараты? Есть ли хронические заболевания?',
    6: 'Эти вопросы не просто помогают подобрать препарат — они защищают покупателя. Например, если человек уже пьёт поливитаминный комплекс с высокой дозой витамина С, добавлять ещё один иммуномодулятор может быть излишним. А тому, кто только вышел из болезни, нужна восстановительная поддержка, а не стимуляция.',
    7: 'Когда покупатель слышит такие вопросы, он понимает: здесь не просто продают — здесь думают о его здоровье. Это ощущение бесценно.',
    8: 'Иммунитет — это не один препарат. Это системная забота. И вы — часть этой системы. Спасибо, что подходите к этому серьёзно.',
}

# STEP: реальный текст 8 production-сцен -> SEMANTIC ANALYSIS (Gemini, через
# semantic_analysis.analyze_scenes — реальный LLM-вызов, не локальная
# имитация) -> COMPOSITION -> LAYOUT solver -> VALIDATION -> PNG-ассеты.
scenes_for_analysis = [
    {"id": n, "text": NARRATION[n], "duration": SCENES_WL[str(n)]["duration"]}
    for n in [1, 2, 3, 4, 5, 6, 7, 8]
]
scene_semantics = analyze_scenes(scenes_for_analysis, output_name="semantic-analysis-production-scenario4")

VIS_DIR = f"{RENDER}/visual_assets"
visual_manifest = build_visual_layer(scene_semantics, VIS_DIR)
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

# ---------- шаг 1: Ken Burns (+punch) на каждый сырой клип аватара (канон) ----------
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

video_paths = kb_paths

# ---------- шаг 2: crossfade всех 8 видео-слоёв (БЕЗ текста, канон) ----------
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

# ---------- шаг 3: границы "текст должен молчать" вокруг каждого перехода
# (канон — нужно субтитрам, не является design/layout правилом самим по себе) ----------
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

# ---------- шаг 4: субтитры (crop-маска) по всем 8 сценам на общем таймлайне
# (канон — система синхронизации речи, не трогать) ----------
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

# ---------- шаг 5: visual layer (render/visual/ — CONTENT -> SEMANTIC ->
# VISUAL_CONCEPT -> COMPOSITION -> LAYOUT -> VALIDATION -> RENDER). Каждый
# элемент — заранее провалидированный PNG (safe zones уже гарантированы
# validate.py), появляется fade-in в свой триггер (реальный тайминг слова
# диктора) и гаснет fade-out либо когда его сменяет вторая стадия
# (keyword_emphasis), либо на границе "тихой зоны" перехода (тот же принцип,
# что уже применяется к субтитрам выше — никогда не режется жёстко на
# кроссфейде). ----------
next_input_idx = 2  # 0=combined_video, 1=lavfi canvas
vis_k = 0
for n in scenes:
    for el in visual_manifest["scenes"][n]["elements"]:
        inputs += ["-loop", "1", "-t", f"{combined_dur:.3f}", "-i", f"{VIS_DIR}/{el['file']}"]
        img_idx = next_input_idx
        next_input_idx += 1

        start = max(g0[n] + el["trigger"], cap_start_global[n])
        end = (g0[n] + el["fade_out"]) if el["fade_out"] is not None else cap_end_global[n]
        end = max(end, start + 0.5)
        fade_out_st = max(start + 0.1, end - 0.3)

        raw = f"visraw{vis_k}"
        fc2.append(f"[{img_idx}:v]format=rgba[{raw}]")
        faded = f"visfade{vis_k}"
        fc2.append(
            f"[{raw}]fade=t=in:st={start:.3f}:d=0.3:alpha=1,"
            f"fade=t=out:st={fade_out_st:.3f}:d=0.3:alpha=1[{faded}]"
        )
        nxt = f"visov{vis_k}"
        fc2.append(f"[{prev}][{faded}]overlay={el['x']}:{el['y']}:enable='between(t,{start:.3f},{end:.3f})'[{nxt}]")
        prev = nxt
        vis_k += 1

filter_complex = ";\n".join(fc2)
final_out = f"{OUT_DIR}/full-trend-video.mp4"
cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", filter_complex,
    "-map", f"[{prev}]", "-map", "0:a",
    "-t", f"{combined_dur:.3f}",  # safety cap: выход не может быть длиннее канона, что бы ни было в графе
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "25",
    "-c:a", "aac", "-b:a", "192k",
    final_out,
]
run(cmd, "final pass: Ken Burns + переходы + субтитры + visual layer")
print("DONE ->", final_out)
