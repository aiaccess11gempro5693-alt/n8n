from PIL import Image, ImageDraw, ImageFilter
from fontTools.ttLib import TTFont
import json

import os
R = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = f"{R}/fonts/Inter-Bold.otf"
os.makedirs(f"{R}/pills", exist_ok=True)
font = TTFont(FONT_PATH)
cmap = font.getBestCmap()
hmtx = font["hmtx"]
upm = font["head"].unitsPerEm

def text_width(s, fontsize):
    total = 0.0
    for ch in s:
        name = cmap.get(ord(ch))
        if name is None:
            total += fontsize*0.55
            continue
        aw, _ = hmtx[name]
        total += aw * fontsize / upm
    return total

def darken(color, factor=0.72):
    return tuple(int(c*factor) for c in color[:3]) + (255,)

def rounded_pill(path, text, fontsize, color, pad_x=40, pad_y=22, radius=None, ss=4,
                  shadow_off=(6,10), shadow_blur=10, shadow_alpha=110, border_w=3):
    tw = text_width(text, fontsize)
    w = int(tw + 2*pad_x)
    h = int(fontsize*1.35 + 2*pad_y)
    if radius is None:
        radius = h // 2
    margin = shadow_blur*3 + max(shadow_off)
    W, H, RAD = w*ss, h*ss, radius*ss
    M = margin*ss
    canvas = Image.new("RGBA", (W+2*M, H+2*M), (0,0,0,0))
    shadow = Image.new("RGBA", canvas.size, (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sx, sy = shadow_off[0]*ss, shadow_off[1]*ss
    sd.rounded_rectangle([M+sx, M+sy, M+W-1+sx, M+H-1+sy], radius=RAD, fill=(0,0,0,shadow_alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur*ss/2))
    canvas = Image.alpha_composite(canvas, shadow)
    body = Image.new("RGBA", canvas.size, (0,0,0,0))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([M, M, M+W-1, M+H-1], radius=RAD, fill=color, outline=darken(color), width=border_w*ss)
    canvas = Image.alpha_composite(canvas, body)
    canvas = canvas.resize(((W+2*M)//ss, (H+2*M)//ss), Image.LANCZOS)
    canvas.save(path)
    return {"outer_w": canvas.size[0], "outer_h": canvas.size[1], "margin": margin, "pill_w": w, "pill_h": h}

TEAL = (33, 110, 113, 255)
CORAL = (224, 93, 66, 255)
FS = 34

labels = [
    ("scene2-pill1", "Добраться до сути", CORAL),
    ("scene3-pill1", "Болеет каждую осень", TEAL),
    ("scene3-pill2", "Слабость после ОРВИ", CORAL),
    ("scene3-pill3", "Просто устал", TEAL),
    ("scene3-pill4", "Уже принимает БАДы", CORAL),
    ("scene5-pill1", "Что именно беспокоит?", TEAL),
    ("scene5-pill2", "Длительность симптомов", CORAL),
    ("scene5-pill3", "Приём других препаратов", TEAL),
    ("scene5-pill4", "Хронические заболевания", CORAL),
    ("scene6-pill1", "Излишняя стимуляция", CORAL),
    ("scene6-pill2", "Восстановительная поддержка", TEAL),
]

info = {}
for name, text, color in labels:
    path = f"{R}/pills/{name}.png"
    meta = rounded_pill(path, text, FS, color)
    info[name] = meta
    print(name, text, meta)

with open(f"{R}/pills/pill_info.json", "w") as f:
    json.dump(info, f, indent=2)

# scene5 needs smaller font (tight space beside a centered avatar) —
# regenerate those 4 at a smaller size with tighter padding
labels5 = [
    ("scene5-pill1", "Что именно беспокоит?", TEAL),
    ("scene5-pill2", "Длительность симптомов", CORAL),
    ("scene5-pill3", "Приём других препаратов", TEAL),
    ("scene5-pill4", "Хронические заболевания", CORAL),
]
info5 = {}
for name, text, color in labels5:
    path = f"{R}/pills/{name}.png"
    meta = rounded_pill(path, text, 28, color, pad_x=30, pad_y=18)
    info5[name] = meta
    print(name, text, meta)
with open(f"{R}/pills/pill_info5.json", "w") as f:
    json.dump(info5, f, indent=2)
