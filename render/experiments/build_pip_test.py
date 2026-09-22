"""
ЭКСПЕРИМЕНТАЛЬНЫЙ прототип — НЕ часть продакшн-пайплайна, НЕ трогает
render/visual/ или build_trend_video.py. Прямой запрос пользователя
(22.09.2026): "давай попробуем другую версию" — аватар полный экран
только во время приветствия, дальше уменьшается в PIP в углу, а весь
остальной кадр занимает динамичная полноэкранная презентация (картинки,
переходы), субтитры остаются как есть. "Это мы сейчас не меняем
правила, это мы сейчас тестируем" — одноразовый тест на сцене 1.

22.09.2026 (2) — правки по прямому фидбэку на v1:
  - PIP перенесён в правый ВЕРХНИЙ угол (было — правый край над
    субтитрами, не понравилось).
  - Вся презентация (картинки + заголовки + подсветка слов в субтитрах)
    перекрашена в тёплые тона — фото аватара тёплые (дерево, свет
    аптеки), сгенерированные картинки были холодными, разнобой.
    Картинки — ffmpeg `colorbalance` (плюс красный/жёлтый, минус синий).
    Заголовки/подписи — акцентный цвет компонентов переопределён на
    тёплый терракотовый (вместо продакшн-тила) + общий тёплый тон-шифт
    всей уже отрендеренной карточки (PIL, чтобы захватить и текстуру
    карточки, не только акцентную линию). Подсветка слова в субтитрах —
    тот же тёплый цвет, что и везде.
  - Ken Burns зум на картинках убран по прямому запросу — статичный
    кадр (только cover-кроп под 16:9, без анимации).
  - Заголовок отцентрирован — и по горизонтали, и по вертикали в
    свободной зоне между PIP (теперь сверху) и субтитровой плашкой.

Переиспользует уже сгенерированные реальные ассеты последнего продакшн-
рендера (kb-scene-1.mp4, scratch/illustration-1*.png, word_layout.json)
— ничего не генерирует заново.
"""
import json
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from visual import components as C
from visual import style as S

RENDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(RENDER)
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)

FONT = f"{RENDER}/fonts/Inter-Bold.otf"
FONTSIZE = 40
BASE_COLOR = "0x2B2F33"
PANEL_COLOR = "0xF7F9FB"
WARM_ACCENT = "0xE0824A"  # тёплый терракотовый — заменяет продакшн-тил (0x2A7F82) только в этом тесте
SCENE_DUR = 16.002


def warm_shift(img, r_mul=1.16, g_mul=1.02, b_mul=0.78):
    """Сдвигает уже отрисованную карточку (заголовок/подпись) в тёплую
    сторону — захватывает не только акцентную линию, но и саму текстуру
    карточки (тёмно-сливовая с бирюзовым свечением — свечение тоже
    становится тёплым)."""
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    r = r.point(lambda v: min(255, int(v * r_mul)))
    g = g.point(lambda v: min(255, int(v * g_mul)))
    b = b.point(lambda v: max(0, int(v * b_mul)))
    return Image.merge("RGBA", (r, g, b, a))


# ---------- заголовок/подписи — теми же компонентами, что в продакшене,
# но с временно переопределённым тёплым акцентом ----------
S.ACCENT = (224, 130, 74, 255)
S.ACCENT_SOFT = (224, 130, 74, 150)

title_img = warm_shift(C.render_kicker_word("", "ЗАПРОС НА «ИММУНИТЕТ»", max_width=1300))
title_img.save(f"{ASSETS}/title.png")
labels = {
    "item0": "Реклама и медиа",
    "item1": "Интернет и статьи",
    "item2": "Советы окружения",
    "context": "Уверенный запрос покупателя",
}
for key, text in labels.items():
    warm_shift(C.render_top_title(text, 900)).save(f"{ASSETS}/label-{key}.png")

# ---------- тайминги (реальные, из последнего продакшн-манифеста сцены 1) ----------
GREET_END = 1.12
S0, S1 = 1.2, 1.8            # окно анимации сжатия аватара в PIP
W2, H2 = 420, 236             # размер PIP (16:9)
X2, Y2 = 1460, 40             # позиция PIP — правый ВЕРХНИЙ угол

# заголовок — по центру кадра, в свободной зоне между PIP и субтитрами
TITLE_SAFE_TOP, TITLE_SAFE_BOTTOM = Y2 + H2, 900
title_x = (1920 - title_img.width) // 2
title_y = (TITLE_SAFE_TOP + TITLE_SAFE_BOTTOM) // 2 - title_img.height // 2

SEGMENTS = [
    ("title", 1.8, 7.166, f"{ASSETS}/title.png", None, title_x, title_y, False),
    ("item0", 7.166, 8.802, f"{REPO}/scratch/illustration-1-item0.png", f"{ASSETS}/label-item0.png", 80, 80, True),
    ("item1", 8.802, 10.345, f"{REPO}/scratch/illustration-1-item1.png", f"{ASSETS}/label-item1.png", 80, 80, True),
    ("item2", 10.345, 12.23, f"{REPO}/scratch/illustration-1-item2.png", f"{ASSETS}/label-item2.png", 80, 80, True),
    ("context", 12.23, 16.002, f"{REPO}/scratch/illustration-1.png", f"{ASSETS}/label-context.png", 80, 80, True),
]

wl = json.load(open(f"{RENDER}/word_layout.json", encoding="utf-8"))
PANEL = wl["panel"]
chunks = wl["scenes"]["1"]["chunks"]

inputs = ["-i", f"{RENDER}/kb-scene-1.mp4",
          "-f", "lavfi", "-i", f"color=c=0x14141c:s=1920x1080:d={SCENE_DUR}",
          "-f", "lavfi", "-i", f"color=c=black@0.0:s=1920x1080:d={SCENE_DUR}"]
CAP_CANVAS_IDX = 2
idx = 3
fc = []

fc.append(f"[1:v]format=rgba[bg_base]")
prev = "bg_base"

# 22.09.2026 (4) — прямая правка: НЕ накладывать цвет-грейдинг фильтром
# поверх картинок ("не надо накладывать бежевый фильтр") — вместо этого
# сами картинки перегенерированы заново (illustration.get_or_generate,
# те же composite id "1"/"1-item0..2") с промптом, явно требующим тёплую
# золотисто-медовую палитру на этапе генерации. Здесь — просто cover-
# кроп под 16:9, без цвет-коррекции и без зума (убран по запросу).
for name, start, end, img_path, label_path, lx, ly, is_photo in SEGMENTS:
    inputs += ["-loop", "1", "-t", f"{SCENE_DUR}", "-i", img_path]
    img_idx = idx; idx += 1
    raw = f"{name}_raw"
    if is_photo:
        fc.append(
            f"[{img_idx}:v]format=rgba,"
            f"scale=1920:1920,crop=1920:1080:(iw-1920)/2:(ih-1080)/2[{raw}]"
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

# ---------- аватар: полный экран -> плавное сжатие в PIP (теперь верхний правый угол) ----------
w_expr = f"if(lt(t\\,{S0})\\,1920\\,if(lt(t\\,{S1})\\,1920+({W2}-1920)*(t-{S0})/({S1}-{S0})\\,{W2}))"
h_expr = f"if(lt(t\\,{S0})\\,1080\\,if(lt(t\\,{S1})\\,1080+({H2}-1080)*(t-{S0})/({S1}-{S0})\\,{H2}))"
x_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{X2}*(t-{S0})/({S1}-{S0})\\,{X2}))"
y_expr = f"if(lt(t\\,{S0})\\,0\\,if(lt(t\\,{S1})\\,{Y2}*(t-{S0})/({S1}-{S0})\\,{Y2}))"

fc.append(f"[0:v]scale=w='{w_expr}':h='{h_expr}':eval=frame[av_scaled]")
fc.append(f"[{bg_final}][av_scaled]overlay=x='{x_expr}':y='{y_expr}':eval=frame[with_avatar]")

# ---------- субтитры: панель + полноценная караоке-подсветка слов (crop-
# техника, как в продакшене — см. build_trend_video.py), цвет подсветки
# теперь тёплый, тот же WARM_ACCENT, что и везде в презентации ----------
prev = "with_avatar"
for ci, cc in enumerate(chunks):
    cond = f"between(t,{cc['start']},{cc['end']})"
    pn = f"panel{ci}"
    fc.append(f"[{prev}]drawbox=x={PANEL['x']}:y={PANEL['y']}:w={PANEL['w']}:h={PANEL['h']}:"
              f"color={PANEL_COLOR}@0.94:t=fill:enable='{cond}'[{pn}]")
    prev = pn
    an = f"acc{ci}"
    fc.append(f"[{prev}]drawbox=x={PANEL['x']}:y={PANEL['y']}:w={PANEL['accent_bar_w']}:h={PANEL['h']}:"
              f"color={WARM_ACCENT}@1.0:t=fill:enable='{cond}'[{an}]")
    prev = an
    for li, lf in enumerate(cc["line_files"]):
        nxt = f"txt{ci}_{li}"
        lx = PANEL["tx"] + lf["x_offset"]
        ly = PANEL["ty0"] + li * PANEL["line_height"]
        fc.append(f"[{prev}]drawtext=fontfile={FONT}:fontcolor={BASE_COLOR}:fontsize={FONTSIZE}:"
                  f"textfile={lf['file']}:x={lx}:y={ly}:enable='{cond}'[{nxt}]")
        prev = nxt
after_grey = prev

fc.append(f"[{CAP_CANVAS_IDX}:v]format=rgba,colorchannelmixer=aa=0.0[cap_tc]")
prev_c = "cap_tc"
for ci, cc in enumerate(chunks):
    cond = f"between(t,{cc['start']},{cc['end']})"
    for li, lf in enumerate(cc["line_files"]):
        nxt = f"cc{ci}_{li}"
        lx = PANEL["tx"] + lf["x_offset"]
        ly = PANEL["ty0"] + li * PANEL["line_height"]
        fc.append(f"[{prev_c}]drawtext=fontfile={FONT}:fontcolor={WARM_ACCENT}:fontsize={FONTSIZE}:"
                  f"textfile={lf['file']}:x={lx}:y={ly}:enable='{cond}'[{nxt}]")
        prev_c = nxt
coral_layer = prev_c

all_words = [(ci, w) for ci, cc in enumerate(chunks) for w in cc["words"]]
n_words = len(all_words)
coral_copies = [f"capcc{i}" for i in range(n_words)]
fc.append(f"[{coral_layer}]split={n_words}[" + "][".join(coral_copies) + "]")

PAD_X, PAD_Y_TOP, PAD_Y_BOT = 6, 10, 16
prev = after_grey
for wi, (ci, w) in enumerate(all_words):
    wcond = f"between(t,{w['start']},{w['end']})"
    wx = PANEL["tx"] + w["x"]
    wy = PANEL["ty0"] + w["line"] * PANEL["line_height"]
    crop_w = round(w["width"] + PAD_X * 2)
    crop_x = round(wx - PAD_X)
    crop_y = round(wy - PAD_Y_TOP)
    crop_h = round(FONTSIZE + PAD_Y_TOP + PAD_Y_BOT)
    crop_label = f"capcrop{wi}"
    fc.append(f"[{coral_copies[wi]}]crop={crop_w}:{crop_h}:{crop_x}:{crop_y}[{crop_label}]")
    nxt = f"capov{wi}"
    fc.append(f"[{prev}][{crop_label}]overlay={crop_x}:{crop_y}:enable='{wcond}'[{nxt}]")
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
