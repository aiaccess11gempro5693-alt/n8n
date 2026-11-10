"""Reels №32 «Прайм Москвы» — по референсу TikTok @11_etazh «Москва никогда не спит».

Без ведущего: неоновая моушн-графика на ночном пиксельном городе, всё рисуется кодом
покадрово (PIL → ffmpeg). Рамка «▶ PLAY / дата» по углам, неоновые заголовки, курс
рубля, графики нефти, рост Москва-Сити, плеер с треком эпохи, столбики Forbes,
стадион, табло 3:1, крах осенью 2008-го, крупные заглавные субтитры по 2–3 слова.

Музыки в файле нет — трек Moscow Never Sleeps добавляется в приложении Instagram
при ручной публикации (через API звук из библиотеки не прикрепить).

python3 render/landing/build_ig32.py [--preview t1,t2,...]  →  render/landing/ig32-9x16.mp4
"""
import difflib
import json
import math
import os
import random
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as SFX  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCEN = f"{ROOT}/docs/scenarios/insta-32-moscow-prime.md"
AUDIO = f"{ROOT}/scratch/ig32/voice.mp3"
MUSIC = f"{ROOT}/scratch/music/ig32-mns-loop.mp3"
MUSIC_GAIN = 0.5
WHISPER = f"{ROOT}/scratch/ig32-whisper-final.json"
OUT = f"{ROOT}/render/landing/ig32-9x16.mp4"
TMP = f"{ROOT}/render/landing/.ig32"
FD = f"{ROOT}/render/fonts"

W, H, FPS = 1080, 1920, 30
PINK, CYAN, GOLD, RED, GREEN, WHITE = (255, 62, 165), (40, 225, 255), (255, 206, 84), (255, 64, 72), (60, 210, 90), (255, 255, 255)
GREY = (150, 140, 175)
SAFE_TOP, SAFE_BOTTOM = 250, 1500
SUB_Y = 1395


def font(name, size):
    return ImageFont.truetype(f"{FD}/{name}", size)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def pop(x):
    """0→1 с перелётом (масштаб появления)."""
    x = min(max(x, 0.0), 1.0)
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


# ---------- слова и тайминги ----------

def script_text():
    s = open(SCEN, encoding="utf-8").read().split("## Текст для озвучки (eleven_v3)")[1]
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", " ", s)).strip()


def norm(w):
    return re.sub(r"[^\wё]", "", w.lower().replace("ё", "е"))


def timed():
    ws = json.load(open(WHISPER))["words"]
    text = script_text().split()
    a, b = [norm(w) for w in text], [norm(x["word"]) for x in ws]
    st, en = [None] * len(text), [None] * len(text)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            st[blk.a + k], en[blk.a + k] = ws[blk.b + k]["start"], ws[blk.b + k]["end"]
    for arr in (st, en):
        for i, t in enumerate(arr):
            if t is None:
                prev = next((arr[j] for j in range(i - 1, -1, -1) if arr[j] is not None), 0.0)
                nxt = next((arr[j] for j in range(i + 1, len(arr)) if arr[j] is not None), prev + 0.4)
                arr[i] = prev + (nxt - prev) * 0.5
    return [(w, s, e) for w, s, e in zip(text, st, en) if norm(w)], ws[-1]["end"]


WORDS = []


def at(phrase, after=0.0):
    p = [norm(x) for x in phrase.split()]
    n = [norm(w) for w, _, _ in WORDS]
    for i in range(len(n) - len(p) + 1):
        if n[i:i + len(p)] == p and WORDS[i][1] >= after - 0.01:
            return WORDS[i][1]
    raise KeyError(phrase)


NOBREAK = {"в", "во", "к", "с", "со", "и", "а", "но", "за", "на", "до", "не", "по", "из", "от", "у", "о", "из",
           "две", "сто", "сорок", "тысячи", "три", "пару", "семьдесят", "девяносто", "наша", "один", "чем", "когда", "она"}


def sub_chunks():
    out, cur = [], []
    for w, s, e in WORDS:
        cur.append((w, s, e))
        txt = " ".join(x for x, _, _ in cur)
        weak = norm(w) in NOBREAK
        if re.search(r"[.!?…,:»]$", w) or ((len(cur) >= 3 or len(txt) > 17) and not weak):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    merged = []
    for c in out:   # очень короткий кусок («Больше,») приклеиваем к следующему
        if merged and (merged[-1][-1][2] - merged[-1][0][1] < 0.6 or c[-1][2] - c[0][1] < 0.45) \
                and len(" ".join(x for x, _, _ in merged[-1] + c)) <= 24 and not re.search(r"[.!?…]»?$", merged[-1][-1][0]):
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    out = merged
    res = []
    for i, c in enumerate(out):
        t0 = c[0][1]
        t1 = out[i + 1][0][1] if i + 1 < len(out) else c[-1][2] + 0.5
        t1 = min(t1, c[-1][2] + 0.6)
        res.append((t0, t1, [x for x, _, _ in c]))
    return res


# ---------- спрайты ----------

CACHE = {}


def neon_text(text, size, col, fname="Unbounded-Black.ttf", glow=1.0, skew=-0.12, core=None):
    key = ("n", text, size, col, fname, glow, skew, core)
    if key in CACHE:
        return CACHE[key]
    f = font(fname, size)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d0.textbbox((0, 0), text, font=f)
    pad = int(size * 0.6) + 20
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), text, font=f, fill=255)
    if skew:
        m = m.transform((w + int(abs(skew) * h), h), Image.AFFINE, (1, skew, -abs(skew) * h if skew < 0 else 0, 0, 1, 0),
                        resample=Image.BICUBIC)
        w = m.width
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for r, a in ((size * 0.35, 0.55 * glow), (size * 0.12, 0.9 * glow)):
        g = m.filter(ImageFilter.GaussianBlur(r))
        layer = Image.new("RGBA", (w, h), col + (0,))
        layer.putalpha(g.point(lambda v, a=a: int(min(255, v * a * 1.6))))
        im.alpha_composite(layer)
    c = core or tuple(int(v * 0.35 + 255 * 0.65) for v in col)
    body = Image.new("RGBA", (w, h), c + (0,))
    body.putalpha(m)
    im.alpha_composite(body)
    CACHE[key] = im
    return im


def plain_text(text, size, col, fname="Montserrat-ExtraBold.ttf", shadow=True):
    key = ("p", text, size, col, fname, shadow)
    if key in CACHE:
        return CACHE[key]
    f = font(fname, size)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d0.textbbox((0, 0), text, font=f)
    pad = 16
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(s).text((pad - bb[0] + 3, pad - bb[1] + 4), text, font=f, fill=(0, 0, 0, 200))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(4)))
    ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), text, font=f, fill=col + (255,))
    CACHE[key] = im
    return im


def pill(text, col, size=30, fg=(20, 12, 30)):
    key = ("pill", text, col, size, fg)
    if key in CACHE:
        return CACHE[key]
    f = font("Montserrat-ExtraBold.ttf", size)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d0.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = tw + 40, th + 26
    pad = 24
    im = Image.new("RGBA", (pw + pad * 2, ph + pad * 2), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((pad, pad, pad + pw, pad + ph), 10, fill=col + (160,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + pw, pad + ph), 10, fill=col + (255,))
    d.text((pad + 20 - bb[0], pad + 13 - bb[1]), text, font=f, fill=fg + (255,))
    CACHE[key] = im
    return im


def bubble(text, col):
    key = ("bub", text, col)
    if key in CACHE:
        return CACHE[key]
    f = font("Montserrat-ExtraBold.ttf", 36)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d0.textbbox((0, 0), text, font=f)
    pw, ph = bb[2] - bb[0] + 56, bb[3] - bb[1] + 40
    pad = 26
    im = Image.new("RGBA", (pw + pad * 2, ph + pad * 2), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((pad, pad, pad + pw, pad + ph), ph // 2, outline=col + (255,), width=6)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + pw, pad + ph), ph // 2, fill=(24, 16, 44, 235), outline=col + (255,), width=4)
    d.text((pad + 28 - bb[0], pad + 20 - bb[1]), text, font=f, fill=(255, 255, 255, 255))
    CACHE[key] = im
    return im


def place(canvas, spr, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    s = spr
    if abs(scale - 1) > 0.005:
        s = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        s = s.copy()
        s.putalpha(s.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - s.width / 2), int(cy - s.height / 2)
    canvas.alpha_composite(s, (max(0, x), max(0, y)),
                           (max(0, -x), max(0, -y)))


def appear(canvas, spr, cx, cy, lt, t0=0.0, alpha=1.0, kind="pop"):
    """Появление спрайта в момент t0 локального времени."""
    x = lt - t0
    if x < 0:
        return
    if kind == "pop":
        k = min(x / 0.35, 1)
        place(canvas, spr, cx, cy, alpha * min(1, x / 0.12), pop(k) * 0.4 + 0.6 if k < 1 else 1.0)
    elif kind == "flicker":
        on = 1.0 if x > 0.45 else (1.0 if int(x * 30) % 3 else 0.25)
        place(canvas, spr, cx, cy, alpha * on)
    elif kind == "rise":
        k = ease(x / 0.4)
        place(canvas, spr, cx, cy + (1 - k) * 40, alpha * k)
    else:
        place(canvas, spr, cx, cy, alpha * min(1, x / 0.25))


# ---------- фон: ночной пиксельный город ----------

def build_background():
    rnd = random.Random(7)
    bg = Image.new("RGB", (W, H))
    arr = np.zeros((H, W, 3), np.float32)
    top, mid, bot = np.array([10, 8, 26]), np.array([24, 16, 52]), np.array([46, 18, 64])
    for y in range(H):
        k = y / H
        c = top + (mid - top) * (k / 0.55) if k < 0.55 else mid + (bot - mid) * ((k - 0.55) / 0.45)
        arr[y, :] = c
    bg = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    blobs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(blobs)
    for _ in range(14):
        x, y, r = rnd.randint(0, W), rnd.randint(200, 1500), rnd.randint(40, 140)
        c = rnd.choice([PINK, (140, 60, 220), (90, 40, 160), CYAN])
        d.ellipse((x - r, y - r, x + r, y + r), fill=c + (rnd.randint(18, 40),))
    bg.alpha_composite(blobs.filter(ImageFilter.GaussianBlur(40)))
    # здания
    city = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(city)
    wins = []
    x = -20
    while x < W:
        bw = rnd.randint(90, 190)
        top_y = rnd.randint(1180, 1560)
        shade = rnd.randint(16, 30)
        dc.rectangle((x, top_y, x + bw, H), fill=(shade, shade - 4, shade + 22, 255))
        for wy in range(top_y + 18, H, 34):
            for wx in range(x + 12, x + bw - 16, 26):
                wins.append((wx, wy, rnd.random()))
        x += bw + rnd.randint(-10, 6)
    # передний ряд потемнее
    x = -30
    while x < W:
        bw = rnd.randint(120, 220)
        top_y = rnd.randint(1500, 1700)
        dc.rectangle((x, top_y, x + bw, H), fill=(12, 9, 26, 255))
        for wy in range(top_y + 20, H, 36):
            for wx in range(x + 14, x + bw - 18, 28):
                wins.append((wx, wy, rnd.random()))
        x += bw + rnd.randint(-10, 10)
    bg.alpha_composite(city)
    return bg, wins


def window_layers(wins, n=4):
    rnd = random.Random(3)
    cols = [(255, 214, 120), (255, 120, 200), (120, 220, 255), (255, 180, 90)]
    layers = []
    for k in range(n):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for wx, wy, p in wins:
            lit = p < 0.2 or (p < 0.3 and rnd.random() < 0.5)
            if lit:
                c = cols[int(p * 100) % 4]
                a = int(90 + 100 * rnd.random())
                d.rectangle((wx, wy, wx + 12, wy + 15), fill=c + (a,))
        glow = im.filter(ImageFilter.GaussianBlur(6))
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.alpha_composite(glow)
        out.alpha_composite(im)
        layers.append(out)
    return layers


def frame_ui(date):
    key = ("ui", date)
    if key in CACHE:
        return CACHE[key]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (190, 180, 215, 150)
    L = 46
    for (x, y, sx, sy) in ((40, 225, 1, 1), (W - 40, 225, -1, 1), (40, 1530, 1, -1), (W - 40, 1530, -1, -1)):
        d.line((x, y, x + sx * L, y), fill=c, width=4)
        d.line((x, y, x, y + sy * L), fill=c, width=4)
    f = font("Montserrat-ExtraBold.ttf", 30)
    d.polygon((78, 262, 78, 290, 100, 276), fill=c)
    d.text((112, 258), "PLAY", font=f, fill=c)
    fm = font("Unbounded-Black.ttf", 28)
    tw = d.textlength(date, font=fm)
    d.text((W - 78 - tw, 258), date, font=fm, fill=GOLD + (220,))
    CACHE[key] = im
    return im


# ---------- элементы сцен ----------

def chart_sprite(points, upto, col, label=None, crash=None):
    """График нефти: points — [(год, $)], upto — доля пройденной линии (0..1)."""
    w, h = 900, 620
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1, y0, y1 = 90, 860, 560, 60
    for v in (0, 50, 100, 150):
        y = y0 - (y0 - y1) * v / 150
        d.line((x0, y, x1, y), fill=(120, 110, 160, 70), width=2)
        d.text((10, y - 14), f"${v}", font=font("Montserrat-Bold.ttf", 24), fill=(170, 160, 200, 170))
    for yr in (2000, 2002, 2004, 2006, 2008):
        x = x0 + (x1 - x0) * (yr - 2000) / 9
        d.text((x - 32, y0 + 14), str(yr), font=font("Montserrat-Bold.ttf", 24), fill=(170, 160, 200, 170))
    pts = [(x0 + (x1 - x0) * (yr - 2000) / 9, y0 - (y0 - y1) * v / 150) for yr, v in points]
    # длина по доле
    segs = list(zip(pts, pts[1:]))
    lens = [math.dist(a, b) for a, b in segs]
    tot, cut = sum(lens), sum(lens) * upto
    line, acc = [pts[0]], 0
    for (a, b), L in zip(segs, lens):
        if acc + L <= cut:
            line.append(b)
            acc += L
        else:
            k = (cut - acc) / L if L else 0
            line.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
            break
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).line(line, fill=col + (255,), width=16, joint="curve")
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    d.line(line, fill=col + (255,), width=7, joint="curve")
    if crash:
        cpts, cup = crash
        cl = [line[-1]] + [(x0 + (x1 - x0) * (yr - 2000) / 9, y0 - (y0 - y1) * v / 150) for yr, v in cpts]
        n = max(2, int(len(cl) * cup) + 1)
        seg = cl[:n]
        if cup < 1 and len(seg) >= 2:
            a, b = cl[n - 2], cl[min(n - 1, len(cl) - 1)]
        g2 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g2).line(seg, fill=RED + (255,), width=16)
        im.alpha_composite(g2.filter(ImageFilter.GaussianBlur(10)))
        d.line(seg, fill=RED + (255,), width=7)
        line = seg
    hx, hy = line[-1]
    d.ellipse((hx - 11, hy - 11, hx + 11, hy + 11), fill=(255, 255, 255, 255))
    if label:
        p = pill(label, GOLD, 30)
        im.alpha_composite(p, (int(min(w - p.width, max(0, hx - p.width / 2))), int(max(0, hy - p.height - 6))))
    return im


OIL = [(2000, 28), (2001, 24), (2002, 25), (2003, 29), (2004, 38), (2005, 54), (2006, 65)]
OIL2 = OIL + [(2007, 72), (2008.5, 147)]


def towers(grow, cranes=1.0, dim=1.0):
    w, h = 820, 900
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    spec = [(60, 120, 430, CYAN), (200, 130, 620, PINK), (350, 140, 800, PINK), (510, 130, 700, CYAN), (660, 110, 520, GOLD)]
    base = h - 10
    for i, (x, bw, th, col) in enumerate(spec):
        k = ease((grow - i * 0.08) / 0.7)
        if k <= 0:
            continue
        top = base - th * k
        a = int(255 * dim)
        d.rectangle((x, top, x + bw, base), fill=(20, 14, 40, 230), outline=col + (a,), width=5)
        for wy in range(int(top) + 24, base - 10, 30):
            for wx in range(x + 16, x + bw - 14, 24):
                if (wx * 7 + wy * 3) % 5 < 3:
                    d.rectangle((wx, wy, wx + 10, wy + 12), fill=col + (int(110 * dim),))
        if cranes > 0 and k > 0.6:
            cy = top - 70
            d.line((x + bw * 0.5, top, x + bw * 0.5, cy), fill=GOLD + (int(230 * dim),), width=5)
            d.line((x + bw * 0.5 - 50, cy, x + bw * 0.5 + 110, cy), fill=GOLD + (int(230 * dim),), width=5)
            d.line((x + bw * 0.5 + 90, cy, x + bw * 0.5 + 90, cy + 40), fill=GOLD + (int(200 * dim),), width=3)
    glow = im.filter(ImageFilter.GaussianBlur(14))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(im)
    return out


def rate_board(val, blink):
    w, h = 820, 360
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((20, 20, w - 20, h - 20), 18, outline=RED + (200,), width=8)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    d.rounded_rectangle((20, 20, w - 20, h - 20), 18, fill=(14, 10, 22, 245), outline=RED + (230,), width=3)
    d.text((w / 2, 70), "ОБМЕН ВАЛЮТ", font=font("Montserrat-ExtraBold.ttf", 32), fill=(200, 190, 220, 255), anchor="mm")
    d.text((70, 160), "USD/RUB", font=font("Montserrat-ExtraBold.ttf", 44), fill=(255, 255, 255, 255), anchor="lm")
    if blink:
        d.polygon((w - 110, 180, w - 70, 180, w - 90, 140), fill=RED + (255,))
    s = f"{val:5.2f}"
    for i, ch in enumerate(s):
        cx = 220 + i * 92
        d.rounded_rectangle((cx - 40, 210, cx + 40, 320), 8, fill=(30, 22, 34, 255))
    txt = neon_text(s, 92, RED, "Unbounded-Black.ttf", skew=0)
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    place(tmp, txt, 404, 268)
    im.alpha_composite(tmp)
    return im


def player(t):
    w, h = 760, 820
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, 430
    for r, col, wd in ((370, CYAN, 4), (330, PINK, 5)):
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), outline=col + (230,), width=wd)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(6)))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col + (200,), width=2)
    bx0, by0, bx1, by1 = cx - 230, cy - 270, cx + 230, cy + 250
    d.rounded_rectangle((bx0, by0, bx1, by1), 36, fill=(176, 176, 196, 255), outline=(230, 230, 245, 255), width=6)
    d.rounded_rectangle((bx0 + 36, by0 + 34, bx1 - 36, by0 + 160), 12, fill=(12, 30, 34, 255))
    msg = "  MOSCOW NEVER SLEEPS  ·  2007  ·"
    fnt = font("Montserrat-ExtraBold.ttf", 30)
    scr = Image.new("RGBA", (bx1 - bx0 - 90, 40), (0, 0, 0, 0))
    ds = ImageDraw.Draw(scr)
    full = msg * 3
    off = (t * 150) % ds.textlength(msg, font=fnt)
    ds.text((-off, 0), full, font=fnt, fill=CYAN + (255,))
    im.alpha_composite(scr, (bx0 + 45, by0 + 44))
    for i in range(16):
        hgt = 10 + 50 * abs(math.sin(t * (5 + i % 4) + i * 1.7))
        x = bx0 + 52 + i * 23
        col = PINK if i % 3 else CYAN
        d.rectangle((x, by0 + 150 - hgt, x + 14, by0 + 150), fill=col + (255,))
    dx, dy, dr = cx, cy + 60, 165
    d.ellipse((dx - dr, dy - dr, dx + dr, dy + dr), fill=(225, 225, 245, 255))
    for r, col in ((150, (200, 170, 240)), (120, (240, 200, 245)), (90, (190, 225, 250))):
        d.ellipse((dx - r, dy - r, dx + r, dy + r), outline=col + (255,), width=10)
    a0 = (t * 220) % 360
    d.arc((dx - 140, dy - 140, dx + 140, dy + 140), a0, a0 + 70, fill=PINK + (255,), width=10)
    d.ellipse((dx - 30, dy - 30, dx + 30, dy + 30), fill=(120, 120, 140, 255))
    d.ellipse((dx - 10, dy - 10, dx + 10, dy + 10), fill=(60, 60, 70, 255))
    fn = font("DejaVuSans.ttf", 50) if os.path.exists(f"{FD}/DejaVuSans.ttf") else None
    for k in range(6):
        ang = t * 0.9 + k * math.pi / 3
        nx, ny = cx + 345 * math.cos(ang), cy + 345 * math.sin(ang)
        col = (CYAN, GOLD, PINK)[k % 3]
        d.ellipse((nx - 12, ny - 4, nx + 8, ny + 12), fill=col + (230,))
        d.line((nx + 7, ny + 4, nx + 7, ny - 30), fill=col + (230,), width=4)
    return im


def bars(ny, msk, crown):
    w, h = 820, 760
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = 640
    unit = 6.2
    for (x, val, col, name) in ((150, msk, PINK, "МОСКВА"), (520, ny, CYAN, "НЬЮ-ЙОРК")):
        bw = 170
        if val > 0:
            top = base - val * unit
            g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(g).rectangle((x, top, x + bw, base), fill=col + (200,))
            im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
            for yy in range(int(top), base):
                k = (yy - top) / max(1, base - top)
                c = tuple(int(v * (1 - 0.55 * k)) for v in col)
                d.line((x, yy, x + bw, yy), fill=c + (255,))
            num = neon_text(str(int(round(val))), 70, WHITE if col == PINK else WHITE, skew=0, glow=0.5)
            place(im, num, x + bw / 2, top - 55)
        d.text((x + bw / 2, base + 50), name, font=font("Montserrat-ExtraBold.ttf", 34), fill=col + (255,), anchor="mm")
    d.line((80, base, w - 80, base), fill=(160, 150, 200, 160), width=3)
    if crown > 0:
        p = pill("№1 В МИРЕ", GOLD, 34)
        place(im, p, 235, 70, crown)
    return im


def stadium(t, crowd=0.0):
    w, h = 900, 640
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, 380
    for side in (-1, 1):
        beam = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bx = cx + side * 300
        ImageDraw.Draw(beam).polygon(((bx - 20, 40), (bx + 20, 40), (cx + side * 40, cy + 40), (cx + side * 200, cy + 60)),
                                     fill=(255, 250, 220, 50))
        im.alpha_composite(beam.filter(ImageFilter.GaussianBlur(14)))
        d.rectangle((bx - 40, 30, bx + 40, 48), fill=(250, 245, 230, 255))
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((cx - 380, cy - 190, cx + 380, cy + 190), outline=CYAN + (255,), width=14)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
    d.ellipse((cx - 380, cy - 190, cx + 380, cy + 190), fill=(24, 30, 60, 255), outline=CYAN + (255,), width=5)
    for k in range(60):
        a = k / 60 * 2 * math.pi
        if int(t * 8 + k) % 4 == 0:
            px, py = cx + 345 * math.cos(a), cy + 170 * math.sin(a)
            d.ellipse((px - 4, py - 4, px + 4, py + 4), fill=(255, 240, 200, 255))
    d.ellipse((cx - 300, cy - 135, cx + 300, cy + 135), fill=(40, 150, 70, 255), outline=(240, 255, 240, 255), width=4)
    d.line((cx, cy - 135, cx, cy + 135), fill=(240, 255, 240, 255), width=4)
    d.ellipse((cx - 50, cy - 26, cx + 50, cy + 26), outline=(240, 255, 240, 255), width=4)
    return im


def flag(d, x, y, w, h, cols):
    for i, c in enumerate(cols):
        d.rectangle((x, y + i * h / 3, x + w, y + (i + 1) * h / 3), fill=c + (255,))


def scoreboard(score, flash):
    w, h = 860, 300
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((20, 20, w - 20, h - 20), 20, outline=CYAN + (230,), width=10)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w - 20, h - 20), 20, fill=(12, 14, 34, 245), outline=CYAN + (255,), width=4)
    flag(d, 70, 70, 120, 80, [(250, 250, 250), (30, 70, 200), (220, 30, 40)])
    flag(d, w - 190, 70, 120, 80, [(200, 30, 40), (250, 250, 250), (30, 70, 180)])
    fs = font("Montserrat-ExtraBold.ttf", 30)
    d.text((130, 200), "РОССИЯ", font=fs, fill=(255, 255, 255, 255), anchor="mm")
    d.text((w - 130, 200), "НИДЕРЛ.", font=fs, fill=(255, 255, 255, 255), anchor="mm")
    sc = neon_text(score, 120 if not flash else 132, GOLD, skew=0)
    place(im, sc, w / 2, 150)
    return im


def crowd_layer(t, a):
    im = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    for k in range(26):
        x = k * 44 + rnd.randint(-10, 10)
        hh = 120 + rnd.randint(0, 80) + 12 * math.sin(t * 6 + k)
        d.ellipse((x - 20, 420 - hh - 40, x + 20, 420 - hh), fill=(14, 10, 24, 255))
        d.rectangle((x - 26, 420 - hh - 8, x + 26, 420), fill=(14, 10, 24, 255))
        if k % 4 == 1:
            sw = 10 * math.sin(t * 5 + k)
            px, py = x + 22, 420 - hh - 140
            d.line((px, 420 - hh - 20, px, py), fill=(200, 200, 210, 255), width=4)
            for i, c in enumerate([(250, 250, 250), (30, 70, 200), (220, 30, 40)]):
                d.polygon(((px, py + i * 22), (px + 90, py + i * 22 + sw), (px + 90, py + (i + 1) * 22 + sw),
                           (px, py + (i + 1) * 22)), fill=c + (255,))
    if a < 1:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


def firework(canvas, cx, cy, lt, col, period=1.4, phase=0.0):
    x = ((lt + phase) % period) / period
    r = 30 + 140 * ease(x)
    a = int(255 * (1 - x))
    d = ImageDraw.Draw(canvas)
    for k in range(14):
        ang = k / 14 * 2 * math.pi
        px, py = cx + r * math.cos(ang), cy + r * math.sin(ang) + 30 * x * x
        d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=col + (a,))


def face_control(lt):
    w, h = 820, 560
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).rectangle((470, 60, 640, 520), fill=(255, 220, 160, 200))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
    d.rectangle((470, 60, 640, 520), fill=(250, 226, 170, 255))
    d.polygon(((470, 520), (640, 520), (760, 560), (360, 560)), fill=(250, 226, 170, 90))
    # охранник и очередь
    d.ellipse((400, 250, 450, 300), fill=(8, 6, 16, 255))
    d.rectangle((385, 295, 465, 520), fill=(8, 6, 16, 255))
    for k in range(6):
        x = 60 + k * 52
        hh = 300 + (k % 3) * 18
        d.ellipse((x - 20, hh - 44, x + 20, hh - 4), fill=(20, 14, 34, 255))
        d.rectangle((x - 26, hh, x + 26, 520), fill=(20, 14, 34, 255))
    return im


# ---------- сцены ----------

def build_acts():
    T = {}
    T["hook"] = 0.0
    T["year"] = at("Но был год")
    T["y2007"] = at("Две тысячи седьмой")
    T["crash"] = at("А началось")
    T["d98"] = at("Девяносто восьмой")
    T["fall"] = at("Рубль")
    T["y2000"] = at("Потом приходят")
    T["oil"] = at("и нефть")
    T["city"] = at("У реки")
    T["club"] = at("И Москву")
    T["clubs"] = at("Клубы до рассвета")
    T["fc"] = at("Фейс-контроль")
    T["jam"] = at("Пробки")
    T["track"] = at("А из каждой")
    T["forbes"] = at("Весна")
    T["ny"] = at("В Нью-Йорке")
    T["msk"] = at("В Москве")
    T["more"] = at("Больше, чем")
    T["may"] = at("Май")
    T["june"] = at("Июнь")
    T["score"] = at("Три", T["june"])
    T["street"] = at("И город до утра")
    T["july"] = at("Июль")
    T["peak"] = at("Это пик")
    T["autumn"] = at("А осенью")
    T["empty"] = at("Клубы пустеют")
    T["over"] = at("Праздник")
    T["prime"] = at("Вот таким")
    T["next"] = at("Чей прайм")
    T["piter"] = at("Питера")
    T["kazan"] = at("Казани")
    T["write"] = at("Пиши")
    return T


ACTS = ["hook", "y2007", "crash", "d98", "y2000", "city", "club", "track", "forbes", "may", "june", "july", "autumn",
        "over", "next"]
DATES = {"hook": "2007", "y2007": "2007", "crash": "1998", "d98": "08.1998", "y2000": "2000 – 2006", "city": "2006",
         "club": "2007 · 03:00", "track": "2007", "forbes": "03.2008", "may": "21.05.2008", "june": "21.06.2008",
         "july": "07.2008", "autumn": "10.2008", "over": "2004 – 2008", "next": "20XX"}


def draw_act(cv, name, lt, T, t):
    st = T[name]
    if name == "hook":
        appear(cv, neon_text("МОСКВА", 120, PINK), 540, 470, lt, 0.0, kind="flicker")
        appear(cv, neon_text("НИКОГДА НЕ СПИТ", 66, CYAN), 545, 590, lt, 0.25, kind="flicker")
        y0 = T["year"] - st
        for i, (txt, col, x, y) in enumerate((("Москва в прайме?", PINK, 360, 780), ("а когда был прайм?", CYAN, 690, 900),
                                               ("2007 — топ", CYAN, 330, 1010), ("где Москва?", PINK, 720, 1110))):
            appear(cv, bubble(txt, col), x, y, lt, y0 + i * 0.45, kind="pop")
    elif name == "y2007":
        appear(cv, neon_text("ПРАЙМ МОСКВЫ", 74, PINK), 540, 520, lt, 0.0, kind="flicker")
        k = ease(lt / 0.7)
        yr = int(round(1998 + 9 * k))
        appear(cv, neon_text(str(yr), 230, GOLD, skew=0), 540, 760, lt, 0.05, kind="fade")
        appear(cv, plain_text("ПИК ЭПОХИ", 46, WHITE), 540, 930, lt, 0.7, kind="rise")
    elif name == "crash":
        dim = Image.new("RGBA", (W, H), (0, 0, 0, int(120 * ease(lt / 0.4))))
        cv.alpha_composite(dim)
        appear(cv, neon_text("ДО ПРАЙМА", 96, GREY, glow=0.5), 540, 640, lt, 0.0, kind="flicker")
        appear(cv, plain_text("город без денег", 48, (200, 190, 220), "Montserrat-Bold.ttf"), 540, 770, lt, 0.4, kind="rise")
    elif name == "d98":
        cv.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 90)))
        appear(cv, pill("ДЕФОЛТ · 17.08.1998", RED, 34, WHITE), 540, 470, lt, 0.0, kind="pop")
        k = ease((t - T["fall"]) / 2.2)
        val = 6.29 + (20.65 - 6.29) * k
        board = rate_board(val, int(t * 3) % 2 == 0 and t > T["fall"])
        appear(cv, board, 540, 780, lt, 0.15, kind="rise")
        if t > T["fall"]:
            appear(cv, plain_text("× 3", 90, RED, "Unbounded-Black.ttf"), 540, 1080, lt, T["fall"] - st + 1.6, kind="pop")
        f = t - T["d98"] - 0.6
        if 0 < f < 0.25:
            cv.alpha_composite(Image.new("RGBA", (W, H), RED + (int(90 * (1 - f / 0.25)),)))
    elif name == "y2000":
        oil_t = T["oil"] - st
        if lt < oil_t + 0.3:
            a = 1.0 if lt < oil_t else max(0, 1 - (lt - oil_t) / 0.3)
            appear(cv, pill("НОВЫЙ ВЕК", GOLD, 32), 540, 560, lt, 0.0, a, kind="pop")
            appear(cv, neon_text("2000", 220, GOLD, skew=0), 540, 760, lt, 0.1, a, kind="pop")
            for i, (x, y, c) in enumerate(((250, 560, PINK), (830, 640, CYAN), (300, 960, GOLD), (800, 990, PINK))):
                if a > 0.5:
                    firework(cv, x, y, lt, c, phase=i * 0.37)
        else:
            appear(cv, pill("НЕФТЬ · $ ЗА БАРРЕЛЬ", GOLD, 30), 540, 470, lt, oil_t, kind="pop")
            up = ease((lt - oil_t - 0.2) / 3.5)
            lab = "$65" if up > 0.97 else None
            place(cv, chart_sprite(OIL, max(0.01, up), PINK, lab), 540, 860, min(1, (lt - oil_t) / 0.3))
    elif name == "city":
        appear(cv, pill("МОСКВА-СИТИ", CYAN, 34), 540, 420, lt, 0.0, kind="pop")
        place(cv, towers(lt / 2.6), 540, 900, min(1, lt / 0.2))
    elif name == "club":
        appear(cv, pill("КЛУБЫ · 2007", PINK, 30, WHITE), 540, 420, lt, 0.0, kind="pop")
        appear(cv, neon_text("FACE CONTROL", 92, PINK), 540, 540, lt, 0.1, kind="flicker")
        place(cv, face_control(lt), 540, 930, min(1, lt / 0.3))
        for i, (key, txt, col, x, y) in enumerate((("clubs", "до рассвета", CYAN, 300, 1180),
                                                   ("jam", "пробки в 03:00", GOLD, 760, 1180))):
            appear(cv, bubble(txt, col), x, y, lt, T[key] - st, kind="pop")
    elif name == "track":
        appear(cv, pill("2007 · ТРЕК ЭПОХИ", GOLD, 32), 540, 400, lt, 0.0, kind="pop")
        place(cv, player(lt), 540, 870, min(1, lt / 0.3), 0.85 + 0.15 * ease(lt / 0.5))
    elif name == "forbes":
        appear(cv, pill("FORBES · ВЕСНА 2008", GOLD, 30), 540, 420, lt, 0.0, kind="pop")
        appear(cv, neon_text("МИЛЛИАРДЕРОВ В ГОРОДЕ", 54, PINK), 540, 520, lt, 0.15, kind="flicker")
        ny = 71 * ease((t - T["ny"]) / 1.0) if t > T["ny"] else 0
        msk = 74 * ease((t - T["msk"]) / 1.0) if t > T["msk"] else 0
        crown = min(1, max(0, (t - T["more"]) / 0.3))
        place(cv, bars(ny, msk, crown), 540, 950, min(1, lt / 0.3))
    elif name == "may":
        appear(cv, pill("21.05.2008 · ЛУЖНИКИ", GOLD, 30), 540, 420, lt, 0.0, kind="pop")
        appear(cv, neon_text("ФИНАЛ", 96, CYAN), 540, 540, lt, 0.1, kind="flicker")
        appear(cv, neon_text("ЛИГИ ЧЕМПИОНОВ", 62, PINK), 540, 650, lt, 0.3, kind="flicker")
        place(cv, stadium(lt), 540, 980, min(1, lt / 0.3), 0.9 + 0.1 * ease(lt / 0.6))
    elif name == "june":
        appear(cv, pill("ЕВРО-2008 · 1/4 ФИНАЛА", CYAN, 30), 540, 420, lt, 0.0, kind="pop")
        sc_t = T["score"] - st
        score = "3:1" if lt >= sc_t else "0:0"
        fl = 0 <= lt - sc_t < 0.25
        place(cv, scoreboard(score, fl), 540, 640, min(1, lt / 0.3))
        appear(cv, plain_text("ДОП. ВРЕМЯ · 21.06.2008", 30, CYAN, "Montserrat-ExtraBold.ttf"), 540, 830, lt, 0.3, kind="fade")
        if fl:
            cv.alpha_composite(Image.new("RGBA", (W, H), GOLD + (int(80 * (1 - (lt - sc_t) / 0.25)),)))
        if t > T["street"]:
            k = ease((t - T["street"]) / 0.6)
            cv.alpha_composite(crowd_layer(lt, k), (0, 1330 - 420 + int((1 - k) * 120)))
            for i, (x, y, c) in enumerate(((220, 960, PINK), (860, 1010, GOLD), (540, 900, CYAN))):
                firework(cv, x, y, lt, c, phase=i * 0.5)
            appear(cv, pill("СОТНИ ТЫСЯЧ НА УЛИЦАХ", GOLD, 32), 540, 960, lt, T["street"] - st + 0.3, kind="pop")
    elif name == "july":
        appear(cv, pill("ИЮЛЬ 2008 · НЕФТЬ", GOLD, 30), 540, 420, lt, 0.0, kind="pop")
        up = ease(lt / 2.4)
        pk = t >= T["peak"]
        lab = ("$147 · ПИК" if pk else "$147") if up > 0.97 else None
        place(cv, chart_sprite(OIL2, max(0.01, up), PINK, lab), 540, 860, min(1, lt / 0.3))
        if pk and int((t - T["peak"]) * 4) % 2 == 0 and t - T["peak"] < 1.2:
            cv.alpha_composite(Image.new("RGBA", (W, H), GOLD + (35,)))
    elif name == "autumn":
        appear(cv, pill("ОСЕНЬ 2008", RED, 32, WHITE), 540, 420, lt, 0.0, kind="pop")
        cup = ease(lt / 1.6)
        place(cv, chart_sprite(OIL2, 1.0, PINK, None, crash=([(2008.75, 70), (2008.95, 40)], cup)), 540, 860)
        if lt > 0.5:
            g = neon_text("КРИЗИС", 120, RED)
            jit = (random.Random(int(lt * 20)).randint(-10, 10)) if lt < 1.3 else 0
            appear(cv, g, 540 + jit, 1180, lt, 0.5, kind="flicker")
    elif name == "over":
        pt = T["prime"] - st
        if lt < pt:
            appear(cv, plain_text("праздник закончился", 54, (200, 190, 220), "Montserrat-Bold.ttf"), 540, 760, lt, 0.1,
                   kind="fade")
        else:
            place(cv, towers(1.0, 1.0, 0.55), 540, 880, min(1, (lt - pt) / 0.5))
            appear(cv, neon_text("ПРАЙМ", 120, PINK), 540, 450, lt, pt, kind="flicker")
            appear(cv, neon_text("МОСКВЫ", 120, PINK), 540, 580, lt, pt + 0.15, kind="flicker")
            appear(cv, neon_text("2004 – 2008", 64, CYAN, skew=0), 540, 700, lt, pt + 0.45, kind="pop")
    elif name == "next":
        appear(cv, neon_text("ЧЕЙ ПРАЙМ", 100, PINK), 540, 520, lt, 0.0, kind="flicker")
        appear(cv, neon_text("СЛЕДУЮЩИЙ?", 72, CYAN), 545, 640, lt, 0.2, kind="flicker")
        appear(cv, bubble("ПИТЕР?", CYAN), 540, 820, lt, T["piter"] - st, kind="pop")
        appear(cv, bubble("КАЗАНЬ?", PINK), 540, 940, lt, T["kazan"] - st, kind="pop")
        appear(cv, pill("ПИШИ В КОММЕНТАРИЯХ", GOLD, 34), 540, 1100, lt, T["write"] - st, kind="pop")


HOTWORDS = {"москва", "москвы", "москву", "москве", "прайм", "краха", "дефолт", "рубль", "нулевые", "нефть", "москвасити",
            "клубы", "фейсконтроль", "пробки", "трек", "гимн", "форбс", "миллиардеров", "семьдесят", "лужниках",
            "чемпионов", "голландию", "три", "один", "пик", "кризис", "пустеют", "закончился", "питера", "казани",
            "комментариях", "седьмой", "восьмой", "восьмого", "сорок", "неспит", "never", "sleeps"}
REDWORDS = {"краха", "дефолт", "кризис", "пустеют", "закончился", "рубль"}


def subtitle(words):
    key = ("sub", tuple(words))
    if key in CACHE:
        return CACHE[key]
    f = font("Montserrat-ExtraBold.ttf", 58)
    parts = [w.upper().replace("«", "").replace("»", "") for w in words]
    hot = [norm(w) in HOTWORDS for w in words]
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    sp = d0.textlength(" ", font=f)
    widths = [d0.textlength(p, font=f) for p in parts]
    tw = sum(widths) + sp * (len(parts) - 1)
    while tw > 960:
        f = font("Montserrat-ExtraBold.ttf", f.size - 4)
        sp = d0.textlength(" ", font=f)
        widths = [d0.textlength(p, font=f) for p in parts]
        tw = sum(widths) + sp * (len(parts) - 1)
    h = 110
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    x = (W - tw) / 2
    ds, d = ImageDraw.Draw(sh), ImageDraw.Draw(im)
    for p, wd, hh, w in zip(parts, widths, hot, words):
        ds.text((x + 3, h / 2 + 4), p, font=f, fill=(0, 0, 0, 230), anchor="lm")
        col = (RED if norm(w) in REDWORDS else CYAN) if hh else WHITE
        d.text((x, h / 2), p, font=f, fill=col + (255,), anchor="lm", stroke_width=2, stroke_fill=(10, 6, 20, 255))
        x += wd + sp
    out = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    out.alpha_composite(im)
    CACHE[key] = out
    return out


def render_frame(t, T, total, bg, wlayers, subs):
    cv = bg.copy()
    # окна мерцают; к концу (клубы пустеют) гаснут
    wl = wlayers[int(t * 2) % len(wlayers)]
    dark = 1.0
    if t > T["empty"]:
        dark = max(0.15, 1 - (t - T["empty"]) / 1.5)
    if t > T["prime"]:
        dark = min(1.0, 0.15 + (t - T["prime"]) / 2.0)
    if dark < 0.999:
        wl = wl.copy()
        wl.putalpha(wl.getchannel("A").point(lambda v: int(v * dark)))
    cv.alpha_composite(wl)
    # текущая сцена
    starts = [(T[a], a) for a in ACTS]
    cur = max((s for s in starts if s[0] <= t + 1e-6), key=lambda s: s[0])
    idx = ACTS.index(cur[1])
    end = starts[idx + 1][0] if idx + 1 < len(ACTS) else total
    lt = t - cur[0]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_act(layer, cur[1], lt, T, t)
    out_k = 1.0
    if idx + 1 < len(ACTS) and end - t < 0.15:
        out_k = max(0, (end - t) / 0.15)
    sc = 1.0 + 0.03 * min(1, lt / 4)   # лёгкий наезд внутри сцены
    if out_k < 1 or abs(sc - 1) > 0.002:
        lw, lh = int(W * sc), int(H * sc)
        big = layer.resize((lw, lh), Image.BILINEAR)
        layer = big.crop(((lw - W) // 2, (lh - H) // 2, (lw - W) // 2 + W, (lh - H) // 2 + H))
        if out_k < 1:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * out_k)))
    cv.alpha_composite(layer)
    # вспышка-склейка в начале сцены
    if idx > 0 and lt < 0.08:
        cv.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(28 * (1 - lt / 0.08)))))
    cv.alpha_composite(frame_ui(DATES[cur[1]]))
    for t0, t1, ws in subs:
        if t0 <= t < t1:
            s = subtitle(ws)
            k = min(1, (t - t0) / 0.08)
            cv.alpha_composite(s, (0, int(SUB_Y - 55 + (1 - k) * 10)))
            break
    return cv.convert("RGB")


def main():
    global WORDS
    os.makedirs(TMP, exist_ok=True)
    WORDS, last = timed()
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                           AUDIO]).decode()) + 0.4
    T = build_acts()
    subs = sub_chunks()
    json.dump({"T": T, "subs": subs}, open(f"{TMP}/plan.json", "w"), ensure_ascii=False, indent=1)
    bg, wins = build_background()
    wl = window_layers(wins)
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        for tt in sys.argv[2].split(","):
            render_frame(float(tt), T, total, bg, wl, subs).save(f"{TMP}/prev-{float(tt):05.1f}.jpg", quality=88)
        return
    audio = f"{TMP}/mix.wav"
    ev = [(T[a], "whoosh", 0.35) for a in ACTS[1:]]
    ev += [(T["d98"] + 0.6, "hit", 0.6), (T["score"], "hit", 0.6), (T["autumn"] + 0.5, "glitch", 0.5),
           (T["peak"], "ding", 0.4), (T["msk"], "pop", 0.4), (T["ny"], "pop", 0.35), (T["piter"], "pop", 0.4),
           (T["kazan"], "pop", 0.4)]
    pad = f"{TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", AUDIO, "-af", "apad=pad_dur=0.4", "-ar", "48000", pad], check=True)
    # фон — Moscow Never Sleeps (DJ Smash): 30-секундный фрагмент со страницы звука Instagram,
    # закольцован с кроссфейдами (scratch/music/ig32-mns-loop.mp3); по просьбе пользователя вшит в ролик
    SFX.mix(pad, ev, audio, f"{TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))
    if len(sys.argv) > 1 and sys.argv[1] == "--remux":   # только пересвести звук поверх готового видео
        tmp = OUT.replace(".mp4", "-remux.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, OUT)
        print(OUT, "звук пересведён")
        return
    n = int(total * FPS)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r",
                          str(FPS), "-i", "-", "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset",
                          "medium", "-crf", "19", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p", "-c:a",
                          "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(render_frame(i / FPS, T, total, bg, wl, subs).tobytes())
        if i % 300 == 0:
            print(f"{i}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print(OUT, f"{total:.1f} c")


if __name__ == "__main__":
    main()
