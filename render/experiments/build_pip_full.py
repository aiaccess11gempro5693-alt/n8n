"""
ЭКСПЕРИМЕНТАЛЬНЫЙ прототип, полное видео (8 сцен) — НЕ часть продакшн-
пайплайна, НЕ трогает render/visual/ или build_trend_video.py. Прямой
запрос пользователя (22.09.2026, после одобрения теста на сцене 1):
"Сделай в этом же формате полное видео".

Формат: аватар на весь экран только во время приветствия (сцена 1),
дальше — навсегда PIP в правом верхнем углу до конца ролика; весь
остальной кадр — динамичная full-screen презентация (реальные тёплые
фото + заголовки + подписи), субтитры как в продакшене (полная
караоке-подсветка), тёплый акцентный цвет везде вместо продакшн-тила.

Переиспользует:
  - render/combined-full.mp4 — уже собранный аватар+аудио со всеми
    переходами (из последнего продакшн-рендера, транзишны/Ken Burns не
    трогаем, они всё равно почти незаметны в маленьком PIP);
  - render/word_layout.json — субтитровые тайминги (панель/чанки/слова);
  - scratch/semantic-analysis-production-scenario4.json — уже посчитанный
    per-scene/per-item состав (concept, elements, trigger_phrase);
  - scratch/illustration-N*.png — реальные фото (перегенерированы тёплыми
    отдельным скриптом ПЕРЕД этим, см. CLAUDE.md 22.09.2026 (5)).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from visual import components as C
from visual import style as S
from visual.timing import trigger_time, enforce_min_gap

RENDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(RENDER)
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)

FONT = f"{RENDER}/fonts/Inter-Bold.otf"
FONTSIZE = 40
BASE_COLOR = "0x2B2F33"
PANEL_COLOR = "0xF7F9FB"
WARM_ACCENT = "0xE0824A"

wl = json.load(open(f"{RENDER}/word_layout.json", encoding="utf-8"))
PANEL = wl["panel"]
sem = json.load(open(f"{REPO}/scratch/semantic-analysis-production-scenario4.json", encoding="utf-8"))
SEM = {r["id"]: r["analysis"] for r in sem["results"]}

SCENES = [1, 2, 3, 4, 5, 6, 7, 8]
DURS = {n: wl["scenes"][str(n)]["duration"] for n in SCENES}

# ---------- глобальный таймлайн — та же арифметика transition_for/g0, что
# в build_trend_video.py (не импортируем тот модуль — он при импорте сам
# запускает сетевые вызовы; здесь только чистая математика длительностей,
# которая должна совпасть с уже собранным combined-full.mp4) ----------
SCENE_KIND = {1: "avatar", 2: "data", 3: "data", 4: "avatar", 5: "data", 6: "data", 7: "avatar", 8: "avatar"}
PAN_DIR = {1: 0, 2: 1, 3: -1, 4: 0, 5: -1, 6: 1, 7: 0, 8: -1}


def transition_for(prev_n, next_n):
    prev_kind, next_kind = SCENE_KIND[prev_n], SCENE_KIND[next_n]
    if next_kind == "data" and prev_kind != "data":
        return ("smoothright" if PAN_DIR.get(next_n, 0) >= 0 else "smoothleft"), 0.35
    if prev_kind == "data" and next_kind != "data":
        return "circleopen", 0.45
    return "fade", 0.5


g0 = {1: 0.0}
trans_dur_in = {1: 0.0}
cum = DURS[1]
for i in range(1, len(SCENES)):
    prev_n, next_n = SCENES[i - 1], SCENES[i]
    _, T = transition_for(prev_n, next_n)
    off = cum - T
    g0[next_n] = off
    trans_dur_in[next_n] = T
    cum = cum + DURS[next_n] - T
COMBINED_DUR = cum

trans_dur_out = {}
for i in range(1, len(SCENES)):
    trans_dur_out[SCENES[i - 1]] = trans_dur_in[SCENES[i]]
trans_dur_out[SCENES[-1]] = 0.0

TEXT_OUT_BEFORE, TEXT_IN_AFTER = 0.35, 0.10
quiet_start, quiet_end = {}, {}
for idx, n in enumerate(SCENES):
    T_in, T_out = trans_dur_in[n], trans_dur_out[n]
    local_start = (T_in + TEXT_IN_AFTER) if idx > 0 else 0.0
    local_end = (DURS[n] - T_out - TEXT_OUT_BEFORE) if idx < len(SCENES) - 1 else DURS[n]
    quiet_start[n] = g0[n] + local_start
    quiet_end[n] = g0[n] + local_end

print("combined_dur", COMBINED_DUR)
for n in SCENES:
    print(f"scene {n}: g0={g0[n]:.3f} quiet=[{quiet_start[n]:.3f},{quiet_end[n]:.3f}]")

# ---------- PIP / полноэкранное приветствие (только сцена 1) ----------
S0, S1 = 1.2, 1.8            # окно анимации сжатия аватара в PIP (глобальное время)
W2, H2 = 420, 236
X2, Y2 = 1460, 40             # правый верхний угол

# ---------- тёплый акцент для заголовков/подписей (тот же приём, что в
# scene1-тесте — не трогает продакшн style.py, только этот скрипт) -------
S.ACCENT = (224, 130, 74, 255)
S.ACCENT_SOFT = (224, 130, 74, 150)


def warm_shift(img, r_mul=1.16, g_mul=1.02, b_mul=0.78):
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    r = r.point(lambda v: min(255, int(v * r_mul)))
    g = g.point(lambda v: min(255, int(v * g_mul)))
    b = b.point(lambda v: max(0, int(v * b_mul)))
    return Image.merge("RGBA", (r, g, b, a))


def local_trigger(sid, phrase, fallback):
    try:
        return trigger_time(sid, phrase)
    except Exception:
        return fallback


# ---------- собираем per-scene "биты" (фото-слой + текст-слой) ----------
class Beat:
    def __init__(self, kind, start, image=None, label=None):
        self.kind = kind  # "photo" | "caption"
        self.start = start
        self.end = None
        self.image = image
        self.label = label


scene_plans = []  # list of dict per scene: {title_img, title_start, title_end, photo_beats, caption_beats}
for n in SCENES:
    a = SEM[n]
    items = sorted([e for e in a["elements"] if e["role"] == "item" and e.get("asset_brief")],
                    key=lambda e: e.get("order") or 0)
    ctx_local = local_trigger(n, a.get("asset_trigger_phrase") or "", 1.0)

    if items:
        # item-сцена (structured_alternatives/checklist): фото+подпись меняются ВМЕСТЕ на каждом бите
        beats = []
        for i, e in enumerate(items):
            t = local_trigger(n, e["trigger_phrase"], 1.0 + i * 1.5)
            img_path = f"{REPO}/scratch/illustration-{n}-item{i}.png"
            beats.append((t, img_path, e["label"]))
        ctx_img = f"{REPO}/scratch/illustration-{n}.png"
        beats.append((ctx_local, ctx_img, a["asset_caption"]))
        beats.sort(key=lambda b: b[0])
        times = enforce_min_gap([b[0] for b in beats], min_gap=1.2)
        photo_beats = [Beat("photo", g0[n] + t, image=b[1], label=b[2]) for t, b in zip(times, beats)]
        caption_beats = []  # подписи уже встроены в photo_beats для item-сцен
    else:
        # non-item сцена (cause_effect/qa/comparison/typography): ОДНО
        # фото на весь "корпус" сцены, подписи (элементы) листаются
        # отдельным независимым слоем поверх.
        role_kicker = {"cause": "", "mechanism": "", "effect": "", "left": "", "right": "",
                       "question": "", "answer": "", "headline": ""}
        elems = sorted([e for e in a["elements"]], key=lambda e: e.get("order") or 0)
        cap_beats_raw = []
        for i, e in enumerate(elems):
            t = local_trigger(n, e["trigger_phrase"], 1.0 + i * 1.5)
            cap_beats_raw.append((t, e["label"]))
        cap_beats_raw.sort(key=lambda b: b[0])
        cap_times = enforce_min_gap([b[0] for b in cap_beats_raw], min_gap=1.2) if cap_beats_raw else []
        caption_beats = [Beat("caption", g0[n] + t, label=b[1]) for t, b in zip(cap_times, cap_beats_raw)]
        ctx_img = f"{REPO}/scratch/illustration-{n}.png"
        photo_start = caption_beats[0].start if caption_beats else quiet_start[n] + 0.3
        photo_beats = [Beat("photo", photo_start, image=ctx_img, label=None)]

    # финальные времена окончания (до конца quiet-зоны сцены)
    for lst in (photo_beats, caption_beats):
        for i, b in enumerate(lst):
            b.end = lst[i + 1].start if i + 1 < len(lst) else quiet_end[n]

    title_end = min([b.start for b in photo_beats] + [b.start for b in caption_beats]) if (photo_beats or caption_beats) else quiet_end[n]
    title_start = 1.8 if n == 1 else quiet_start[n]
    title_end = max(title_end, title_start + 0.9)

    scene_plans.append({
        "n": n, "title": a["scene_title"], "title_start": title_start, "title_end": title_end,
        "photo_beats": photo_beats, "caption_beats": caption_beats,
    })

# ---------- рендерим PNG-ассеты (заголовки/подписи), warm-shift ----------
def render_title(text, key):
    img = warm_shift(C.render_kicker_word("", text.upper(), max_width=1300))
    img.save(f"{ASSETS}/title-{key}.png")
    return img


def render_label(text, key):
    img = warm_shift(C.render_top_title(text, 900))
    img.save(f"{ASSETS}/label-{key}.png")
    return img


TITLE_SAFE_TOP, TITLE_SAFE_BOTTOM = Y2 + H2, PANEL["y"]

for plan in scene_plans:
    n = plan["n"]
    timg = render_title(plan["title"], f"s{n}")
    plan["title_img"] = f"{ASSETS}/title-s{n}.png"
    plan["title_w"], plan["title_h"] = timg.size
    for i, b in enumerate(plan["photo_beats"]):
        if b.label:
            render_label(b.label, f"s{n}-p{i}")
            b.label_img = f"{ASSETS}/label-s{n}-p{i}.png"
        else:
            b.label_img = None
    for i, b in enumerate(plan["caption_beats"]):
        render_label(b.label, f"s{n}-c{i}")
        b.label_img = f"{ASSETS}/label-s{n}-c{i}.png"

print("assets rendered")

# ---------- ffmpeg filter graph ----------
inputs = ["-i", f"{RENDER}/combined-full.mp4",
          "-f", "lavfi", "-i", f"color=c=0x14141c:s=1920x1080:d={COMBINED_DUR:.3f}",
          "-f", "lavfi", "-i", f"color=c=black@0.0:s=1920x1080:d={COMBINED_DUR:.3f}"]
CAP_CANVAS_IDX = 2
idx = 3
fc = []

fc.append("[1:v]format=rgba[bg_base]")
prev = "bg_base"

k = 0
for plan in scene_plans:
    n = plan["n"]
    # заголовок сцены — центр по горизонтали, центр свободной вертикальной
    # зоны между PIP (сверху) и субтитрами (снизу)
    tx = (1920 - plan["title_w"]) // 2
    ty = (TITLE_SAFE_TOP + TITLE_SAFE_BOTTOM) // 2 - plan["title_h"] // 2
    inputs += ["-loop", "1", "-t", f"{COMBINED_DUR:.3f}", "-i", plan["title_img"]]
    ti = idx; idx += 1
    tf = f"title{k}_f"
    fc.append(f"[{ti}:v]format=rgba,fade=t=out:st={plan['title_end']-0.25:.3f}:d=0.25:alpha=1[{tf}]")
    tn = f"stage_title{k}"
    fc.append(f"[{prev}][{tf}]overlay=x={tx}:y={ty}:enable='between(t,{plan['title_start']:.3f},{plan['title_end']:.3f})'[{tn}]")
    prev = tn
    k += 1

    for b in plan["photo_beats"]:
        inputs += ["-loop", "1", "-t", f"{COMBINED_DUR:.3f}", "-i", b.image]
        pi = idx; idx += 1
        raw = f"ph{k}_raw"
        fc.append(f"[{pi}:v]format=rgba,scale=1920:1920,crop=1920:1080:(iw-1920)/2:(ih-1080)/2[{raw}]")
        pf = f"ph{k}_f"
        fade_out_st = b.end - 0.25
        fc.append(f"[{raw}]fade=t=out:st={fade_out_st:.3f}:d=0.25:alpha=1[{pf}]")
        pn = f"stage_ph{k}"
        fc.append(f"[{prev}][{pf}]overlay=x=0:y=0:enable='between(t,{b.start:.3f},{b.end:.3f})'[{pn}]")
        prev = pn
        if b.label_img:
            inputs += ["-loop", "1", "-t", f"{COMBINED_DUR:.3f}", "-i", b.label_img]
            li = idx; idx += 1
            lf = f"lb{k}_f"
            fc.append(f"[{li}:v]format=rgba,fade=t=out:st={fade_out_st:.3f}:d=0.25:alpha=1[{lf}]")
            ln = f"stage_lb{k}"
            fc.append(f"[{prev}][{lf}]overlay=x=80:y=80:enable='between(t,{b.start:.3f},{b.end:.3f})'[{ln}]")
            prev = ln
        k += 1

    for b in plan["caption_beats"]:
        inputs += ["-loop", "1", "-t", f"{COMBINED_DUR:.3f}", "-i", b.label_img]
        li = idx; idx += 1
        lf = f"cap{k}_f"
        fade_out_st = b.end - 0.25
        fc.append(f"[{li}:v]format=rgba,fade=t=out:st={fade_out_st:.3f}:d=0.25:alpha=1[{lf}]")
        ln = f"stage_cap{k}"
        fc.append(f"[{prev}][{lf}]overlay=x=80:y=80:enable='between(t,{b.start:.3f},{b.end:.3f})'[{ln}]")
        prev = ln
        k += 1

bg_final = prev

# ---------- аватар: полный экран -> PIP (правый верхний), затем PIP до конца видео ----------
w_expr = f"if(lt(t\\,{S0})\\,1920\\,if(lt(t\\,{S1})\\,1920+({W2}-1920)*(t-{S0})/({S1}-{S0})\\,{W2}))"
h_expr = f"if(lt(t\\,{S0})\\,1080\\,if(lt(t\\,{S1})\\,1080+({H2}-1080)*(t-{S0})/({S1}-{S0})\\,{H2}))"
x_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{X2}*(t-{S0})/({S1}-{S0})\\,{X2}))"
y_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{Y2}*(t-{S0})/({S1}-{S0})\\,{Y2}))"

fc.append(f"[0:v]scale=w='{w_expr}':h='{h_expr}':eval=frame[av_scaled]")
fc.append(f"[{bg_final}][av_scaled]overlay=x='{x_expr}':y='{y_expr}':eval=frame[with_avatar]")

# ---------- субтитры: панель + полная караоке-подсветка (тёплый акцент),
# глобальные тайминги = локальные + g0[n], точно как в build_trend_video.py ----------
cap_chunks = []
for n in SCENES:
    for cc in wl["scenes"][str(n)]["chunks"]:
        g_start = max(cc["start"] + g0[n], quiet_start[n])
        g_end = min(cc["end"] + g0[n], quiet_end[n])
        if g_start >= quiet_end[n] or g_end <= quiet_start[n]:
            continue
        lines = [{"file": lf["file"], "x": PANEL["tx"] + lf["x_offset"], "y": PANEL["ty0"] + li * PANEL["line_height"]}
                  for li, lf in enumerate(cc["line_files"])]
        words = []
        for w in cc["words"]:
            ws, we = w["start"] + g0[n], w["end"] + g0[n]
            ws, we = max(ws, quiet_start[n]), min(we, quiet_end[n])
            if we <= ws:
                continue
            words.append({"text": w["text"], "start": ws, "end": we,
                          "x": PANEL["tx"] + w["x"], "y": PANEL["ty0"] + w["line"] * PANEL["line_height"], "width": w["width"]})
        cap_chunks.append({"start": g_start, "end": g_end, "lines": lines, "words": words})

prev = "with_avatar"
for ci, cc in enumerate(cap_chunks):
    cond = f"between(t,{cc['start']:.3f},{cc['end']:.3f})"
    pn = f"panel{ci}"
    fc.append(f"[{prev}]drawbox=x={PANEL['x']}:y={PANEL['y']}:w={PANEL['w']}:h={PANEL['h']}:color={PANEL_COLOR}@0.94:t=fill:enable='{cond}'[{pn}]")
    prev = pn
    an = f"acc{ci}"
    fc.append(f"[{prev}]drawbox=x={PANEL['x']}:y={PANEL['y']}:w={PANEL['accent_bar_w']}:h={PANEL['h']}:color={WARM_ACCENT}@1.0:t=fill:enable='{cond}'[{an}]")
    prev = an
    for li, lf in enumerate(cc["lines"]):
        nxt = f"txt{ci}_{li}"
        fc.append(f"[{prev}]drawtext=fontfile={FONT}:fontcolor={BASE_COLOR}:fontsize={FONTSIZE}:textfile={lf['file']}:x={lf['x']}:y={lf['y']}:enable='{cond}'[{nxt}]")
        prev = nxt
after_grey = prev

fc.append(f"[{CAP_CANVAS_IDX}:v]format=rgba,colorchannelmixer=aa=0.0[cap_tc]")
prev_c = "cap_tc"
for ci, cc in enumerate(cap_chunks):
    cond = f"between(t,{cc['start']:.3f},{cc['end']:.3f})"
    for li, lf in enumerate(cc["lines"]):
        nxt = f"cc{ci}_{li}"
        fc.append(f"[{prev_c}]drawtext=fontfile={FONT}:fontcolor={WARM_ACCENT}:fontsize={FONTSIZE}:textfile={lf['file']}:x={lf['x']}:y={lf['y']}:enable='{cond}'[{nxt}]")
        prev_c = nxt
coral_layer = prev_c

all_words = [w for cc in cap_chunks for w in cc["words"]]
n_words = len(all_words)
coral_copies = [f"capcc{i}" for i in range(n_words)]
fc.append(f"[{coral_layer}]split={n_words}[" + "][".join(coral_copies) + "]")

PAD_X, PAD_Y_TOP, PAD_Y_BOT = 6, 10, 16
prev = after_grey
for wi, w in enumerate(all_words):
    wcond = f"between(t,{w['start']:.3f},{w['end']:.3f})"
    crop_w = round(w["width"] + PAD_X * 2)
    crop_x = round(w["x"] - PAD_X)
    crop_y = round(w["y"] - PAD_Y_TOP)
    crop_h = round(FONTSIZE + PAD_Y_TOP + PAD_Y_BOT)
    crop_label = f"capcrop{wi}"
    fc.append(f"[{coral_copies[wi]}]crop={crop_w}:{crop_h}:{crop_x}:{crop_y}[{crop_label}]")
    nxt = f"capov{wi}"
    fc.append(f"[{prev}][{crop_label}]overlay={crop_x}:{crop_y}:enable='{wcond}'[{nxt}]")
    prev = nxt

out_path = f"{os.path.dirname(os.path.abspath(__file__))}/full-pip-presentation.mp4"
cmd = [
    "ffmpeg", "-y", *inputs,
    "-filter_complex", ";".join(fc),
    "-map", f"[{prev}]", "-map", "0:a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "25",
    "-c:a", "aac", "-b:a", "192k",
    out_path,
]
print(f"filter graph: {len(fc)} filters, {len(inputs)//2} inputs")
print("running ffmpeg (this will take a while)...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("STDERR TAIL:\n", r.stderr[-6000:])
    raise SystemExit("ffmpeg failed")
print("OK ->", out_path)
