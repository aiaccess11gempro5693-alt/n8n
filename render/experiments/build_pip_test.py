"""
ЭКСПЕРИМЕНТАЛЬНЫЙ прототип — НЕ часть продакшн-пайплайна, НЕ трогает
render/visual/ или build_trend_video.py. Прямой запрос пользователя
(22.09.2026): "давай попробуем другую версию" — аватар полный экран
только во время приветствия, дальше уменьшается в PIP в углу, а весь
остальной кадр занимает динамичная полноэкранная презентация (картинки,
переходы), субтитры остаются как есть. "Это мы сейчас не меняем
правила, это мы сейчас тестируем" — одноразовый тест на сцене 1,
результат не заменяет текущий продакшн-формат без отдельного решения
пользователя.

Переиспользует уже сгенерированные реальные ассеты последнего продакшн-
рендера (kb-scene-1.mp4, scratch/illustration-1*.png, word_layout.json)
— ничего не генерирует заново.
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from visual import components as C

RENDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(RENDER)
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)

FONT = f"{RENDER}/fonts/Inter-Bold.otf"
FONTSIZE = 40
BASE_COLOR = "0x2B2F33"
PANEL_COLOR = "0xF7F9FB"
ACCENT = "0x2A7F82"
SCENE_DUR = 16.002

# ---------- заголовок/подписи — теми же компонентами, что в продакшене ----------
title_img = C.render_kicker_word("", "ЗАПРОС НА «ИММУНИТЕТ»", max_width=1300)
title_img.save(f"{ASSETS}/title.png")
labels = {
    "item0": "Реклама и медиа",
    "item1": "Интернет и статьи",
    "item2": "Советы окружения",
    "context": "Уверенный запрос покупателя",
}
for key, text in labels.items():
    C.render_top_title(text, 900).save(f"{ASSETS}/label-{key}.png")

# ---------- тайминги (реальные, из последнего продакшн-манифеста сцены 1) ----------
GREET_END = 1.12
S0, S1 = 1.2, 1.8            # окно анимации сжатия аватара в PIP
W2, H2 = 420, 236             # размер PIP (16:9)
X2, Y2 = 1460, 644            # позиция PIP — правый край, выше субтитровой плашки (y0=900)

SEGMENTS = [
    ("title", 1.8, 7.166, f"{ASSETS}/title.png", None, 309, 430, False),
    ("item0", 7.166, 8.802, f"{REPO}/scratch/illustration-1-item0.png", f"{ASSETS}/label-item0.png", 80, 80, True),
    ("item1", 8.802, 10.345, f"{REPO}/scratch/illustration-1-item1.png", f"{ASSETS}/label-item1.png", 80, 80, True),
    ("item2", 10.345, 12.23, f"{REPO}/scratch/illustration-1-item2.png", f"{ASSETS}/label-item2.png", 80, 80, True),
    ("context", 12.23, 16.002, f"{REPO}/scratch/illustration-1.png", f"{ASSETS}/label-context.png", 80, 80, True),
]

import json
wl = json.load(open(f"{RENDER}/word_layout.json", encoding="utf-8"))
PANEL = wl["panel"]
chunks = wl["scenes"]["1"]["chunks"]

inputs = ["-i", f"{RENDER}/kb-scene-1.mp4",
          "-f", "lavfi", "-i", f"color=c=0x14141c:s=1920x1080:d={SCENE_DUR}"]
idx = 2
fc = []

fc.append(f"[1:v]format=rgba[bg_base]")
prev = "bg_base"

for name, start, end, img_path, label_path, lx, ly, is_photo in SEGMENTS:
    inputs += ["-loop", "1", "-t", f"{SCENE_DUR}", "-i", img_path]
    img_idx = idx; idx += 1
    raw = f"{name}_raw"
    if is_photo:
        u = f"min(max((t-{start})/({end}-{start})\\,0)\\,1)"
        zoom = f"(1.0+0.06*{u})"
        fc.append(
            f"[{img_idx}:v]format=rgba,"
            f"scale=w='trunc(1920*{zoom}/2)*2':h='trunc(1920*{zoom}/2)*2':eval=frame,"
            f"crop=1920:1080:x='(iw-1920)/2':y='(ih-1080)/2'[{raw}]"
        )
    else:
        fc.append(f"[{img_idx}:v]format=rgba[{raw}]")
    faded = f"{name}_f"
    fade_out_st = end - 0.25
    fc.append(f"[{raw}]fade=t=out:st={fade_out_st:.3f}:d=0.25:alpha=1[{faded}]")
    nxt = f"stage_{name}"
    ox, oy = (0, 0) if is_photo else (lx, ly)
    fc.append(f"[{prev}][{faded}]overlay=x={ox}:y={oy}:enable='between(t,{start:.3f},{end:.3f})'[{nxt}]")
    prev = nxt

    if label_path:
        inputs += ["-loop", "1", "-t", f"{SCENE_DUR}", "-i", label_path]
        lbl_idx = idx; idx += 1
        lbl_faded = f"{name}_lbl_f"
        fc.append(f"[{lbl_idx}:v]format=rgba,fade=t=out:st={fade_out_st:.3f}:d=0.25:alpha=1[{lbl_faded}]")
        lbl_nxt = f"stage_{name}_lbl"
        fc.append(f"[{prev}][{lbl_faded}]overlay=x={lx}:y={ly}:enable='between(t,{start:.3f},{end:.3f})'[{lbl_nxt}]")
        prev = lbl_nxt

bg_final = prev

# ---------- аватар: полный экран -> плавное сжатие в PIP ----------
w_expr = f"if(lt(t\\,{S0})\\,1920\\,if(lt(t\\,{S1})\\,1920+({W2}-1920)*(t-{S0})/({S1}-{S0})\\,{W2}))"
h_expr = f"if(lt(t\\,{S0})\\,1080\\,if(lt(t\\,{S1})\\,1080+({H2}-1080)*(t-{S0})/({S1}-{S0})\\,{H2}))"
x_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{X2}*(t-{S0})/({S1}-{S0})\\,{X2}))"
y_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{Y2}*(t-{S0})/({S1}-{S0})\\,{Y2}))"

fc.append(f"[0:v]scale=w='{w_expr}':h='{h_expr}':eval=frame[av_scaled]")
fc.append(f"[{bg_final}][av_scaled]overlay=x='{x_expr}':y='{y_expr}':eval=frame[with_avatar]")

# ---------- субтитры (упрощённо: та же плашка/шрифт/цвет, без покадровой караоке-подсветки — только для теста композиции) ----------
prev = "with_avatar"
for ci, cc in enumerate(chunks):
    cond = f"between(t,{cc['start']},{cc['end']})"
    pn = f"panel{ci}"
    fc.append(f"[{prev}]drawbox=x={PANEL['x']}:y={PANEL['y']}:w={PANEL['w']}:h={PANEL['h']}:"
              f"color={PANEL_COLOR}@0.94:t=fill:enable='{cond}'[{pn}]")
    prev = pn
    an = f"acc{ci}"
    fc.append(f"[{prev}]drawbox=x={PANEL['x']}:y={PANEL['y']}:w={PANEL['accent_bar_w']}:h={PANEL['h']}:"
              f"color={ACCENT}@1.0:t=fill:enable='{cond}'[{an}]")
    prev = an
    for li, lf in enumerate(cc["line_files"]):
        nxt = f"txt{ci}_{li}"
        lx = PANEL["tx"] + lf["x_offset"]
        ly = PANEL["ty0"] + li * PANEL["line_height"]
        fc.append(f"[{prev}]drawtext=fontfile={FONT}:fontcolor={BASE_COLOR}:fontsize={FONTSIZE}:"
                  f"textfile={lf['file']}:x={lx}:y={ly}:enable='{cond}'[{nxt}]")
        prev = nxt

out_path = f"{os.path.dirname(os.path.abspath(__file__))}/scene1-pip-presentation-test.mp4"
cmd = [
    "ffmpeg", "-y", *inputs,
    "-filter_complex", ";".join(fc),
    "-map", f"[{prev}]", "-map", "0:a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "25",
    "-c:a", "aac", "-b:a", "192k",
    out_path,
]
print("running ffmpeg...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("STDERR TAIL:\n", r.stderr[-4000:])
    raise SystemExit("ffmpeg failed")
print("OK ->", out_path)
