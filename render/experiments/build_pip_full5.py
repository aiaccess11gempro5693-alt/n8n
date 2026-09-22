"""
ЭКСПЕРИМЕНТАЛЬНЫЙ прототип v5, полное видео (8 сцен) — НЕ часть
продакшн-пайплайна. Правит v4 по прямому фидбэку пользователя
(22.09.2026, без скриншотов в этот раз — баги найдены аудитом кода
по словесному описанию "растянутая картинка", "неровно, заголовок в
одном месте, картинки несимметрично", "маленькие квадраты, куча
свободного места"):

  1. **Растяжение фото в "story"-сценах** — квадратный (1024x1024)
     исходник масштабировался НАПРЯМУЮ в 1920x1080-подобные размеры
     (`scale=w='1920*zoom':h='1080*zoom'`) — разные коэффициенты по
     осям (~1.875 по ширине, ~1.055 по высоте) реально растягивали
     фото по вертикали. Исправлено: сначала равномерный cover-crop до
     квадрата 1920x1920 (как у blurred-подложки), потом Ken Burns zoom
     с ОДИНАКОВЫМ коэффициентом по обеим осям.
  2. **Заголовок не по центру относительно контента** — TOP_TITLE_ZONE
     была {x0:60,x1:1420} (центр 740px), тогда как весь остальной
     контент (NEW_LEFT/RIGHT, DUO_*) симметричен и центрирован на
     960px (истинный центр кадра) — заголовок визуально "гулял" левее.
     Исправлено: TOP_TITLE_ZONE тоже центрирована на 960 (проверено
     ассертом), правый край по-прежнему строго левее PIP.
  3. **"Дуэт": маленькие карточки в огромных пустых слотах** — слоты
     были 840px шириной, но реально влезающее квадратное фото
     ограничено ВЫСОТОЙ (между заголовком и субтитрами), а не шириной
     слота — получалось ~350px фото в 840px слоте, много пустого места
     вокруг. Слоты пересчитаны под реально достижимый размер (~400px
     фото + поля = 500px слот), пара по-прежнему центрирована на 960px.

Раздел ниже (типы сцен) не менялся с v4 — план из 5 типов сцен по-прежнему в силе:

  - "list"  (сцены 1, 3, 5)  — фото + список/чек-лист (формат v3, без
             изменений: hero сразу, ghost-слоты до триггера).
  - "story" (сцены 2, 7)     — НЕТ бокового списка/карточек. Резкое
             полноэкранное фото с медленным Ken Burns (1.0->1.06) на
             всю тихую зону сцены, поверх — ОДНА центрированная строка
             (киккер + фраза), которая СМЕНЯЕТСЯ по ходу сцены
             (причина -> механизм -> следствие), а не накапливается.
  - "duo"   (сцены 4, 6)     — два фото-карточки рядом (симметрично),
             каждая со своей подписью; левая сразу, правая — по
             реальному триггеру (ghost до этого). Для сцены 6
             переиспользованы существующие per-item фото; для сцены 4
             одна из двух картинок — новая (см. gen_scene4_duo.py,
             "шаблонный совет" на контрасте с "адресная помощь").
  - "quote" (сцена 8)        — самый спокойный тип: только размытое
             фото на весь кадр + заголовок, без карточек и текста —
             намеренная пауза перед концом ролика.

PIP/аватар, тайминг сцен (g0/quiet-зоны), караоке-субтитры, тёплый
акцент, полноэкранная размытая подложка (для list/duo/quote) — БЕЗ
изменений относительно v3.
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

RENDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(RENDER)
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets5")
os.makedirs(ASSETS, exist_ok=True)

FONT = f"{RENDER}/fonts/Inter-Bold.otf"
FONTSIZE = 40
BASE_COLOR = "0x2B2F33"
PANEL_COLOR = "0xF7F9FB"
WARM_ACCENT = "0xE0824A"
BG_COLOR = "0x1f160c"

wl = json.load(open(f"{RENDER}/word_layout.json", encoding="utf-8"))
PANEL = wl["panel"]
SEM_PATH = f"{REPO}/scratch/semantic-analysis-production-scenario4.json"
sem_json = json.load(open(SEM_PATH, encoding="utf-8"))
ANALYSIS = {r["id"]: r["analysis"] for r in sem_json["results"]}

SCENES = [1, 2, 3, 4, 5, 6, 7, 8]
DURS = {n: wl["scenes"][str(n)]["duration"] for n in SCENES}

SCENE_TEMPLATE = {1: "list", 2: "story", 3: "list", 4: "duo", 5: "list", 6: "duo", 7: "story", 8: "quote"}

# ---------- глобальный таймлайн (идентично v1-v3) ----------
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
    print(f"scene {n}: template={SCENE_TEMPLATE[n]:6s} g0={g0[n]:.3f} quiet=[{quiet_start[n]:.3f},{quiet_end[n]:.3f}]")

# ---------- PIP-геометрия (идентична v1-v3) ----------
S0, S1 = 1.2, 1.8
W2, H2 = 420, 236
X2, Y2 = 1460, 40
PIP_ZONE = {"x0": X2, "y0": Y2, "x1": X2 + W2, "y1": Y2 + H2}

# ---------- тёплый акцент во всех visual-компонентах ----------
S.ACCENT = (224, 130, 74, 255)
S.ACCENT_SOFT = (224, 130, 74, 150)

# ---------- геометрия для "list" (как в v3) и "duo" ----------
# v5 фикс (прямая жалоба на v4): TOP_TITLE_ZONE раньше была {60,1420} —
# центр 740px, тогда как весь остальной контент (NEW_LEFT/RIGHT, DUO_*)
# симметричен и центрирован на 960px (истинный центр кадра) — заголовок
# визуально "гулял" левее, не совпадая с центром картинок под ним.
# Теперь TOP_TITLE_ZONE тоже центрирована на 960, при этом её правый
# край (1420) по-прежнему строго левее PIP (1460).
TOP_TITLE_ZONE = {"x0": 500, "x1": 1420, "y0": 26, "y1": 150}
NEW_LEFT = {"x0": 160, "x1": 910, "y0": 290, "y1": 860}
NEW_RIGHT = {"x0": 1010, "x1": 1760, "y0": 290, "y1": 860}
# DUO: раньше слоты были 840px шириной, но реально влезающее квадратное
# фото (ограничено высотой между заголовком и субтитрами, а не шириной
# слота) — всего ~400px, из-за чего вокруг маленькой карточки оставалось
# много пустого места. Слоты пересчитаны под реально достижимый размер
# фото (500px с полями), пара по-прежнему центрирована на 960px.
DUO_LEFT = {"x0": 410, "x1": 910, "y0": 290, "y1": 860}
DUO_RIGHT = {"x0": 1010, "x1": 1510, "y0": 290, "y1": 860}
assert NEW_LEFT["x0"] == 1920 - NEW_RIGHT["x1"]
assert DUO_LEFT["x0"] == 1920 - DUO_RIGHT["x1"]
assert TOP_TITLE_ZONE["x1"] < PIP_ZONE["x0"]
assert (TOP_TITLE_ZONE["x0"] + TOP_TITLE_ZONE["x1"]) // 2 == (NEW_LEFT["x0"] + NEW_RIGHT["x1"]) // 2 == 960
assert NEW_RIGHT["y0"] > PIP_ZONE["y1"] and DUO_RIGHT["y0"] > PIP_ZONE["y1"]

COMP.LEFT_COLUMN = NEW_LEFT
COMP.RIGHT_COLUMN = NEW_RIGHT
LAY.LEFT_COLUMN = NEW_LEFT
LAY.RIGHT_COLUMN = NEW_RIGHT


def _col_w(col):
    return col["x1"] - col["x0"]


def _col_h(col):
    return col["y1"] - col["y0"]


# ---------- прогреваем кеш illustration.py уже готовыми картинками с
# диска (включая свежую "4-left", если уже сгенерирована и влита из
# main) — без новых сетевых вызовов внутри ЭТОГО скрипта. ----------
for fn in os.listdir(f"{REPO}/scratch"):
    if not fn.startswith("illustration-") or not fn.endswith(".png"):
        continue
    key = fn[len("illustration-"):-len(".png")]
    if key.startswith(("card-plate", "photoreal", "recal", "testD", "testG")):
        continue
    with ILL._raw_cache_lock:
        if key not in ILL._raw_cache:
            ILL._raw_cache[key] = Image.open(f"{REPO}/scratch/{fn}").convert("RGBA")
    if key.isdigit():
        with ILL._raw_cache_lock:
            ILL._raw_cache[int(key)] = ILL._raw_cache[key]
print("illustration cache primed")
assert "4-left" in ILL._raw_cache, "scene4 duo-left image missing — run gen_scene4_duo.py and merge main first"


# ---------- SceneSemantics loader (идентично v2/v3) ----------
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


def make_ghost(img, alpha_mul=0.32):
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    a = a.point(lambda v: int(v * alpha_mul))
    return Image.merge("RGBA", (r, g, b, a))


class Placed:
    def __init__(self, image, x, y, trigger, fade_out=None, is_asset=False):
        self.image = image
        self.x = x
        self.y = y
        self.trigger = trigger
        self.fade_out = fade_out
        self.is_asset = is_asset  # True = показывается сразу, без ghost-слоя


HERO_TRIGGER_LOCAL = 0.2


def build_list_items(sem):
    """Как в v3: compose()+place_group(), главное фото — сразу, остальное — ghost до триггера."""
    groups = COMP.compose(sem)
    placed = []
    for g in groups:
        is_asset_group = len(g.items) == 1 and g.items[0].kind == "asset"
        group_placed = LAY.place_group(g)
        if is_asset_group and group_placed:
            group_placed[0].trigger = HERO_TRIGGER_LOCAL
        for pi in group_placed:
            placed.append(Placed(pi.image, pi.x, pi.y, pi.trigger, pi.fade_out, is_asset=is_asset_group))
    return placed


ROLE_KICKER = {"cause": "Причина", "mechanism": "Механизм", "effect": "Следствие",
               "question": "Вопрос", "answer": "Ответ", "headline": "", "item": "", "left": "", "right": ""}


def build_story_items(sem):
    """Одна центрированная строка (киккер+фраза), СМЕНЯЮЩАЯСЯ по ходу
    сцены на реальных триггерах — никакой боковой колонки/карточек."""
    elems = sorted(sem.elements, key=lambda e: e.order or 0)
    triggers = COMP._synced_triggers(sem, elems)
    placed = []
    for i, (e, t) in enumerate(zip(elems, triggers)):
        img = C.render_headline(e.label, 1500, kicker=ROLE_KICKER.get(e.role, ""), align="left")
        x = (1920 - img.width) // 2
        y = PANEL["y"] - img.height - 40
        fade_out = triggers[i + 1] if i + 1 < len(elems) else None
        placed.append(Placed(img, x, y, t, fade_out=fade_out, is_asset=True))
    return placed


CAPTION_RESERVE = 70  # ~chip_h(49.5) + chip_gap(16), запас под однострочную подпись render_image_card


def _duo_card(path, caption, col):
    """Масштабирует фото так, чтобы ГОТОВАЯ карточка (фото + подпись +
    рамка/тень render_image_card) целиком влезала в колонку и по ширине,
    и по высоте — раньше учитывалась только ширина, из-за чего карточка
    получалась выше колонки (905px против доступных 520px) и подпись
    уезжала за нижний край кадра, под субтитровую плашку."""
    img = Image.open(path).convert("RGBA")
    margin = 2 * (C.CARD_SHADOW_BLUR + C.PAD)
    max_w = _col_w(col) - margin
    max_h = _col_h(col) - margin - CAPTION_RESERVE
    ratio = min(max_w / img.width, max_h / img.height)
    img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))))
    card = C.render_image_card(img, caption=caption)
    x = col["x0"] + max(0, (_col_w(col) - card.width) // 2)
    y = col["y0"] + max(0, (_col_h(col) - card.height) // 2)
    return card, x, y


def build_duo_items(sem, n):
    if n == 6:
        items = sorted([e for e in sem.elements if e.role == "item"], key=lambda e: e.order or 0)
        left_e, right_e = items[0], items[1]
        left_path = f"{REPO}/scratch/illustration-6-item0.png"
        right_path = f"{REPO}/scratch/illustration-6-item1.png"
        left_cap, right_cap = left_e.asset_caption, right_e.asset_caption
        right_trigger = COMP._element_trigger(sem, right_e, 1)
    elif n == 4:
        eff = [e for e in sem.elements if e.role == "effect"][0]
        left_path = f"{REPO}/scratch/illustration-4-left.png"
        right_path = f"{REPO}/scratch/illustration-4.png"
        left_cap, right_cap = "Шаблонный совет", eff.label
        right_trigger = COMP._element_trigger(sem, eff, 1)
    else:
        raise ValueError(f"no duo mapping for scene {n}")

    l_card, lx, ly = _duo_card(left_path, left_cap, DUO_LEFT)
    r_card, rx, ry = _duo_card(right_path, right_cap, DUO_RIGHT)
    return [
        Placed(l_card, lx, ly, HERO_TRIGGER_LOCAL, is_asset=True),
        Placed(r_card, rx, ry, right_trigger, is_asset=False),
    ]


scene_manifest = {}
scene_context_photo = {}
for n in SCENES:
    sem = load_sem(n)
    tpl = SCENE_TEMPLATE[n]
    scene_context_photo[n] = f"{REPO}/scratch/illustration-{n}.png"

    if tpl == "list":
        placed = build_list_items(sem)
    elif tpl == "story":
        placed = build_story_items(sem)
    elif tpl == "duo":
        placed = build_duo_items(sem, n)
    elif tpl == "quote":
        placed = []
    else:
        raise ValueError(tpl)

    title_img = C.render_top_title(sem.scene_title, _col_w(TOP_TITLE_ZONE))
    tx = TOP_TITLE_ZONE["x0"] + max(0, (_col_w(TOP_TITLE_ZONE) - title_img.width) // 2)
    ty = TOP_TITLE_ZONE["y0"] + max(0, (_col_h(TOP_TITLE_ZONE) - title_img.height) // 2)
    placed.append(Placed(title_img, tx, ty, 0.3 if n != 1 else 1.8, is_asset=True))

    entries = []
    for ei, pi in enumerate(placed):
        fname = f"s{n}-el{ei}.png"
        pi.image.save(f"{ASSETS}/{fname}")
        ghost_file = None
        if not pi.is_asset:
            ghost_file = f"{ASSETS}/s{n}-el{ei}-ghost.png"
            make_ghost(pi.image).save(ghost_file)

        start_local = pi.trigger
        end_local = pi.fade_out if pi.fade_out is not None else DURS[n]
        start_g = max(g0[n] + start_local, quiet_start[n])
        end_g = g0[n] + end_local if pi.fade_out is not None else quiet_end[n]
        end_g = max(end_g, start_g + 0.5)
        entries.append({"file": f"{ASSETS}/{fname}", "ghost_file": ghost_file,
                         "x": pi.x, "y": pi.y, "start": start_g, "end": end_g})
    scene_manifest[n] = entries
    print(f"scene {n}: template={tpl:6s} concept={sem.visual_concept:24s} elements={len(entries)}")

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

# ---------- фоновая подложка на всю тихую зону сцены: "story" — резкое
# фото с медленным Ken Burns; остальные шаблоны — размытая версия того
# же фото (как в v3), никогда не голый цвет. ----------
for n in SCENES:
    inputs += ["-loop", "1", "-t", f"{COMBINED_DUR:.3f}", "-i", scene_context_photo[n]]
    bgimg_idx = idx
    idx += 1
    raw = f"scenebg{n}_raw"
    if SCENE_TEMPLATE[n] == "story":
        # v5 фикс: раньше квадратный (1024x1024) исходник масштабировался
        # НАПРЯМУЮ в 1920x1080-подобные размеры (w='1920*zoom', h='1080*zoom')
        # — разные коэффициенты по осям (~1.875 vs ~1.055) реально растягивали
        # фото. Теперь сначала равномерный cover-crop до квадрата 1920x1920
        # (тот же приём, что у blurred-подложки ниже), и только ПОТОМ
        # Ken Burns zoom — с ОДИНАКОВЫМ коэффициентом по обеим осям.
        dur = max(quiet_end[n] - quiet_start[n], 0.1)
        zoom = f"(1+0.06*min(max((t-{quiet_start[n]:.3f})/{dur:.3f}\\,0)\\,1))"
        fc.append(
            f"[{bgimg_idx}:v]format=rgba,scale=1920:1920,"
            f"scale=w='1920*{zoom}':h='1920*{zoom}':eval=frame,"
            f"crop=1920:1080:(iw-1920)/2:(ih-1080)/2[{raw}]"
        )
    else:
        fc.append(
            f"[{bgimg_idx}:v]format=rgba,scale=1920:1920,crop=1920:1080:(iw-1920)/2:(ih-1080)/2,"
            f"gblur=sigma=22,eq=brightness=-0.20:saturation=0.70[{raw}]"
        )
    faded = f"scenebg{n}_f"
    fc.append(
        f"[{raw}]fade=t=in:st={quiet_start[n]:.3f}:d=0.3:alpha=1,"
        f"fade=t=out:st={quiet_end[n]-0.3:.3f}:d=0.3:alpha=1[{faded}]"
    )
    nxt = f"stage_scenebg{n}"
    fc.append(f"[{prev}][{faded}]overlay=x=0:y=0:enable='between(t,{quiet_start[n]:.3f},{quiet_end[n]:.3f})'[{nxt}]")
    prev = nxt

# slide-in + ease-out-back entrance (build_trend_video.py, 21.09.2026 (10))
# + ghost-слой (тусклая копия ДО реального триггера) для не-hero элементов.
ENT = 0.4
EASE_C1, EASE_C3 = 1.70158, 2.70158
vk = 0
for n in SCENES:
    for el in scene_manifest[n]:
        if el["ghost_file"]:
            inputs += ["-loop", "1", "-t", f"{COMBINED_DUR:.3f}", "-i", el["ghost_file"]]
            gidx = idx
            idx += 1
            graw = f"ghost{vk}_raw"
            fc.append(f"[{gidx}:v]format=rgba[{graw}]")
            gfaded = f"ghost{vk}_f"
            fc.append(f"[{graw}]fade=t=in:st={quiet_start[n]:.3f}:d=0.3:alpha=1[{gfaded}]")
            gnxt = f"stage_ghost{vk}"
            fc.append(
                f"[{prev}][{gfaded}]overlay=x={el['x']}:y={el['y']}:"
                f"enable='between(t,{quiet_start[n]:.3f},{el['start']:.3f})'[{gnxt}]"
            )
            prev = gnxt

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
        if el["y"] < TOP_TITLE_ZONE["y1"]:
            slide_x, slide_y = el["x"], f"({el['y']}-22*(1-{ease}))"
        else:
            direction = -1 if el["x"] < 960 else 1
            slide_x, slide_y = f"({el['x']}+{direction * 44}*(1-{ease}))", el["y"]

        nxt = f"visov{vk}"
        fc.append(f"[{prev}][{faded}]overlay=x='{slide_x}':y='{slide_y}':enable='between(t,{start:.3f},{end:.3f})'[{nxt}]")
        prev = nxt
        vk += 1

bg_final = prev

# ---------- аватар: полный экран -> PIP, затем PIP до конца видео ----------
w_expr = f"if(lt(t\\,{S0})\\,1920\\,if(lt(t\\,{S1})\\,1920+({W2}-1920)*(t-{S0})/({S1}-{S0})\\,{W2}))"
h_expr = f"if(lt(t\\,{S0})\\,1080\\,if(lt(t\\,{S1})\\,1080+({H2}-1080)*(t-{S0})/({S1}-{S0})\\,{H2}))"
x_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{X2}*(t-{S0})/({S1}-{S0})\\,{X2}))"
y_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{Y2}*(t-{S0})/({S1}-{S0})\\,{Y2}))"

fc.append(f"[0:v]scale=w='{w_expr}':h='{h_expr}':eval=frame[av_scaled]")
fc.append(f"[{bg_final}][av_scaled]overlay=x='{x_expr}':y='{y_expr}':eval=frame[with_avatar]")

# ---------- субтитры: без изменений относительно v1-v3 ----------
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

out_path = f"{os.path.dirname(os.path.abspath(__file__))}/full-pip-presentation-v5.mp4"
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
