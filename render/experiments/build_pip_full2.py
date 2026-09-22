"""
ЭКСПЕРИМЕНТАЛЬНЫЙ прототип v2, полное видео (8 сцен) — НЕ часть
продакшн-пайплайна, НЕ трогает build_trend_video.py. Правит v1
(full-pip-presentation.mp4) по прямому фидбэку пользователя (22.09.2026):

  1. "Промежуточные экраны с заголовком на чёрном фоне не подходят" —
     v1 показывало голый тёмный lavfi-канвас между появлениями элементов.
     Фикс: вместо одной full-bleed фото-подложки теперь настоящая
     презентационная раскладка через render/visual/composition.py +
     components.py (те же текстурированные тёплые карточки, что и в
     заголовке — никогда не бывает голого фона).
  2. "Надписи на картинках на английском — пусть генерирует на русском" —
     у двух иконок сцены 1 (ТВ-реклама, статья в телефоне) явно виден
     текст на экране устройства; промпты переписаны с требованием
     русского текста + тёплой палитры, картинки перегенерированы заново
     (композитные id "1-item0"/"1-item1" перезаписаны).
  3. "Должен быть формат презентации — иконки, текст, булиты, подсветка
     тем, переходы, а не просто картинка на фоне" — вместо full-bleed
     фото + pill-подписи теперь переиспользуется УЖЕ ГОТОВЫЙ композиционный
     движок продакшна (composition.compose() -> per-scene ColumnGroup/Item
     с реальными bullet/checklist/chain-компонентами, номерными
     маркерами, иконками-миниатюрами и акцентной подсветкой) — просто с
     ДРУГОЙ геометрией колонок (avatar теперь маленький PIP в углу, а не
     во весь кадр, поэтому колонки шире/выше), тёплым акцентом вместо
     продакшн-тила, и entrance-анимацией (slide-in + ease-out-back),
     перенесённой из build_trend_video.py.

PIP/аватар, тайминг сцен (g0/quiet-зоны) и караоке-субтитры — БЕЗ
изменений относительно v1 (там жалоб не было).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from visual import components as C
from visual import style as S
from visual import composition as COMP
from visual import layout as LAY
from visual import illustration as ILL
from visual.semantic_analysis import VisualElement, SceneSemantics
from visual.timing import enforce_min_gap

RENDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(RENDER)
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets2")
os.makedirs(ASSETS, exist_ok=True)

FONT = f"{RENDER}/fonts/Inter-Bold.otf"
FONTSIZE = 40
BASE_COLOR = "0x2B2F33"
PANEL_COLOR = "0xF7F9FB"
WARM_ACCENT = "0xE0824A"
BG_COLOR = "0x1f160c"  # тёплый тёмно-коричневый вместо холодного 0x14141c из v1

wl = json.load(open(f"{RENDER}/word_layout.json", encoding="utf-8"))
PANEL = wl["panel"]
SEM_PATH = f"{REPO}/scratch/semantic-analysis-production-scenario4.json"
sem_json = json.load(open(SEM_PATH, encoding="utf-8"))
ANALYSIS = {r["id"]: r["analysis"] for r in sem_json["results"]}

SCENES = [1, 2, 3, 4, 5, 6, 7, 8]
DURS = {n: wl["scenes"][str(n)]["duration"] for n in SCENES}

# ---------- глобальный таймлайн (идентично v1) ----------
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

# ---------- PIP-геометрия (идентична v1) ----------
S0, S1 = 1.2, 1.8
W2, H2 = 420, 236
X2, Y2 = 1460, 40
PIP_ZONE = {"x0": X2, "y0": Y2, "x1": X2 + W2, "y1": Y2 + H2}

# ---------- тёплый акцент во всех visual-компонентах ----------
S.ACCENT = (224, 130, 74, 255)
S.ACCENT_SOFT = (224, 130, 74, 150)

# ---------- НОВАЯ геометрия колонок для PIP-формата: аватар больше не
# занимает всю высоту кадра, поэтому колонки шире/выше, чем в продакшне.
# LEFT — широкая колонка под главную фотографию (render_image_card).
# RIGHT — узкая, но высокая колонка под список пунктов/цепочку — специально
# НЕ заходит в X-диапазон PIP (x0=1460), поэтому ей не нужно освобождать
# место по Y под PIP и она может начинаться выше, как и LEFT. ----------
NEW_LEFT = {"x0": 60, "x1": 940, "y0": 170, "y1": 860}
NEW_RIGHT = {"x0": 980, "x1": 1420, "y0": 170, "y1": 860}
TOP_TITLE_ZONE = {"x0": 60, "x1": 1420, "y0": 26, "y1": 150}
assert NEW_RIGHT["x1"] < PIP_ZONE["x0"], "right column must not reach under the PIP box"
assert TOP_TITLE_ZONE["x1"] < PIP_ZONE["x0"], "title zone must not reach under the PIP box"

COMP.LEFT_COLUMN = NEW_LEFT
COMP.RIGHT_COLUMN = NEW_RIGHT
LAY.LEFT_COLUMN = NEW_LEFT
LAY.RIGHT_COLUMN = NEW_RIGHT


def _col_w(col):
    return col["x1"] - col["x0"]


def _col_h(col):
    return col["y1"] - col["y0"]


# ---------- фикс #2: два ассета сцены 1 показывают экран устройства с
# читаемым текстом — промпт переписан на явный русский текст + тёплую
# палитру (та же формулировка, что уже сработала для тёплого тона в
# прошлом раунде), перегенерируются заново тем же композитным id ----------
RUSSIAN_TEXT_SUFFIX = (
    ", any readable text, words or headline visible in the photo must be in "
    "Russian language using Cyrillic letters, NOT English, NOT Latin script"
)
WARM_SUFFIX = (
    ", warm golden-hour color palette, amber and honeyed tones, warm natural "
    "light, NOT cool-toned, NOT blue-toned"
)
FIXED_BRIEFS = {
    (1, 0): ANALYSIS[1]["elements"][0]["asset_brief"] + WARM_SUFFIX + RUSSIAN_TEXT_SUFFIX,
    (1, 1): ANALYSIS[1]["elements"][1]["asset_brief"] + WARM_SUFFIX + RUSSIAN_TEXT_SUFFIX,
}
for (n, i), brief in FIXED_BRIEFS.items():
    ANALYSIS[n]["elements"][i]["asset_brief"] = brief
with open(SEM_PATH, "w", encoding="utf-8") as f:
    json.dump(sem_json, f, ensure_ascii=False, indent=2)
print("patched asset_brief for scene1 item0/item1 (warm + Russian text), regenerating...")
for (n, i), brief in FIXED_BRIEFS.items():
    label = ANALYSIS[n]["elements"][i]["label"]
    img = ILL.get_or_generate(f"{n}-item{i}", brief, narration_text=label, max_width=300, aspect_ratio="1:1")
    if img is None:
        raise SystemExit(f"regeneration failed for scene {n} item {i}")
print("scene1 item0/item1 regenerated")

# ---------- прогреваем кеш illustration.py остальными уже готовыми тёплыми
# картинками (без новых сетевых вызовов) ----------
for fn in os.listdir(f"{REPO}/scratch"):
    if not fn.startswith("illustration-") or not fn.endswith(".png"):
        continue
    key = fn[len("illustration-"):-len(".png")]
    if key in ("1-item0", "1-item1"):
        continue  # уже свежие в кеше после регенерации выше
    if key.startswith(("card-plate", "photoreal", "recal", "testD", "testG")):
        continue
    with ILL._raw_cache_lock:
        if key not in ILL._raw_cache:
            ILL._raw_cache[key] = Image.open(f"{REPO}/scratch/{fn}").convert("RGBA")
    # composite item ids приходят как int scene_id, но "1", "1-item0" и т.п.
    # совпадают по строковому представлению — прогреваем оба варианта ключа
    if key.isdigit():
        with ILL._raw_cache_lock:
            ILL._raw_cache[int(key)] = ILL._raw_cache[key]
print("illustration cache primed")


# ---------- SceneSemantics loader (из уже посчитанного JSON + word_layout) ----------
def _scene_text(n):
    words = []
    for chunk in wl["scenes"][str(n)]["chunks"]:
        words.extend(w["text"] for w in chunk["words"])
    return " ".join(words)


def load_sem(n):
    a = ANALYSIS[n]
    elements = [
        VisualElement(
            role=e["role"], label=e["label"], sublabel=e.get("sublabel", ""),
            order=e.get("order", 0), trigger_phrase=e.get("trigger_phrase", ""),
            asset_brief=e.get("asset_brief", ""), asset_caption=e.get("asset_caption", ""),
        )
        for e in a["elements"]
    ]
    return SceneSemantics(
        scene_id=n, text=_scene_text(n), duration=DURS[n],
        main_message=a["main_message"], scene_title=a["scene_title"],
        information_structure=a["information_structure"], visual_goal=a["visual_goal"],
        asset_required=a["asset_required"], asset_type_raw=a.get("asset_type", ""),
        asset_brief=a["asset_brief"], asset_caption=a["asset_caption"],
        composition_intent=a.get("composition_intent", ""), motion_intent=a.get("motion_intent", ""),
        avoid=a.get("avoid", []), no_asset_reason=a.get("no_asset_reason"),
        visual_concept=a["visual_concept"], asset_strategy=a["asset_strategy"],
        elements=elements, asset_trigger_phrase=a.get("asset_trigger_phrase", ""),
    )


# ---------- compose() + place_group() по каждой сцене, плюс top-title ----------
class Placed:
    def __init__(self, image, x, y, trigger, fade_out=None):
        self.image = image
        self.x = x
        self.y = y
        self.trigger = trigger
        self.fade_out = fade_out


scene_manifest = {}  # n -> list[dict(file,x,y,start_global,end_global)]
for n in SCENES:
    sem = load_sem(n)
    groups = COMP.compose(sem)
    placed = []
    for g in groups:
        placed.extend(LAY.place_group(g))

    title_img = C.render_top_title(sem.scene_title, _col_w(TOP_TITLE_ZONE))
    tx = TOP_TITLE_ZONE["x0"] + max(0, (_col_w(TOP_TITLE_ZONE) - title_img.width) // 2)
    ty = TOP_TITLE_ZONE["y0"] + max(0, (_col_h(TOP_TITLE_ZONE) - title_img.height) // 2)
    placed.append(Placed(title_img, tx, ty, 0.3 if n != 1 else 1.8))

    entries = []
    for ei, pi in enumerate(placed):
        fname = f"s{n}-el{ei}.png"
        pi.image.save(f"{ASSETS}/{fname}")
        start_local = pi.trigger
        end_local = pi.fade_out if pi.fade_out is not None else DURS[n]
        start_g = max(g0[n] + start_local, quiet_start[n])
        end_g = g0[n] + end_local if pi.fade_out is not None else quiet_end[n]
        end_g = max(end_g, start_g + 0.5)
        entries.append({"file": f"{ASSETS}/{fname}", "x": pi.x, "y": pi.y,
                         "start": start_g, "end": end_g})
    scene_manifest[n] = entries
    print(f"scene {n}: concept={sem.visual_concept:24s} elements={len(entries)}")

print("visual assets rendered")

# ---------- ffmpeg filter graph ----------
inputs = ["-i", f"{RENDER}/combined-full.mp4",
          "-f", "lavfi", "-i", f"color=c={BG_COLOR}:s=1920x1080:d={COMBINED_DUR:.3f}",
          "-f", "lavfi", "-i", f"color=c=black@0.0:s=1920x1080:d={COMBINED_DUR:.3f}"]
CAP_CANVAS_IDX = 2
idx = 3
fc = []

fc.append("[1:v]format=rgba[bg_base]")
prev = "bg_base"

# slide-in + ease-out-back entrance — перенесено из build_trend_video.py
# (21.09.2026 (10)) без изменений формулы.
ENT = 0.4
EASE_C1, EASE_C3 = 1.70158, 2.70158
vk = 0
for n in SCENES:
    for el in scene_manifest[n]:
        inputs += ["-loop", "1", "-t", f"{COMBINED_DUR:.3f}", "-i", el["file"]]
        img_idx = idx
        idx += 1

        start, end = el["start"], el["end"]
        fade_out_st = max(start + 0.1, end - 0.3)

        raw = f"visraw{vk}"
        fc.append(f"[{img_idx}:v]format=rgba[{raw}]")
        faded = f"visfade{vk}"
        fc.append(
            f"[{raw}]fade=t=in:st={start:.3f}:d=0.3:alpha=1,"
            f"fade=t=out:st={fade_out_st:.3f}:d=0.3:alpha=1[{faded}]"
        )

        u = f"min(max((t-{start:.3f})/{ENT}\\,0)\\,1)"
        ease = f"(1+{EASE_C3}*pow(({u})-1\\,3)+{EASE_C1}*pow(({u})-1\\,2))"
        if el["y"] < TOP_TITLE_ZONE["y1"]:  # верхний заголовок — заходит сверху
            slide_x, slide_y = el["x"], f"({el['y']}-22*(1-{ease}))"
        else:
            direction = -1 if el["x"] < 960 else 1
            slide_x, slide_y = f"({el['x']}+{direction * 44}*(1-{ease}))", el["y"]

        nxt = f"visov{vk}"
        fc.append(f"[{prev}][{faded}]overlay=x='{slide_x}':y='{slide_y}':enable='between(t,{start:.3f},{end:.3f})'[{nxt}]")
        prev = nxt
        vk += 1

bg_final = prev

# ---------- аватар: полный экран -> PIP (правый верхний), затем PIP до конца видео ----------
w_expr = f"if(lt(t\\,{S0})\\,1920\\,if(lt(t\\,{S1})\\,1920+({W2}-1920)*(t-{S0})/({S1}-{S0})\\,{W2}))"
h_expr = f"if(lt(t\\,{S0})\\,1080\\,if(lt(t\\,{S1})\\,1080+({H2}-1080)*(t-{S0})/({S1}-{S0})\\,{H2}))"
x_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{X2}*(t-{S0})/({S1}-{S0})\\,{X2}))"
y_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{Y2}*(t-{S0})/({S1}-{S0})\\,{Y2}))"

fc.append(f"[0:v]scale=w='{w_expr}':h='{h_expr}':eval=frame[av_scaled]")
fc.append(f"[{bg_final}][av_scaled]overlay=x='{x_expr}':y='{y_expr}':eval=frame[with_avatar]")

# ---------- субтитры: без изменений относительно v1 ----------
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

out_path = f"{os.path.dirname(os.path.abspath(__file__))}/full-pip-presentation-v2.mp4"
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
