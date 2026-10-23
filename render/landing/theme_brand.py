"""Стиль серии Instagram Reels бренда ИИАВАТАР (борд scratch/img/ig1_board.png,
23.10.2026): графит #111311, оранжевый #F3531B, тёплый белый #F4F1EC.
Заголовки — Oswald Bold капслоком (узкий жирный гротеск), текст — Montserrat
ExtraBold. Язык: оранжевые плашки под ключевым словом, тонкие оранжевые
линии, крупные субтитры с текущим словом на оранжевой плашке.

Только оформление: компонент рисует RGBA PNG и возвращает путь.
Раскладку и тайминги задаёт скрипт ролика (build_ig1.py).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
F_HEAD = f"{FONTS}/Oswald-Bold.ttf"
F_BODY = f"{FONTS}/Montserrat-ExtraBold.ttf"
F_BODY_S = f"{FONTS}/Montserrat-SemiBold.ttf"

GRAPHITE = (17, 19, 17, 255)
ORANGE = (243, 83, 27, 255)
CREAM = (244, 241, 236, 255)
WHITE = (255, 255, 255, 255)
GREY = (150, 150, 146, 255)
CARD = (30, 32, 30, 240)
PAD_COLOR = "0x111311"
CAP_F = 62

_fc = {}


def font(path, size):
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def tw(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(text, font=f)


def tbox(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textbbox((0, 0), text, font=f)


def _shadow(im, blur=16, k=0.6, dy=10, pad=30):
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 255))
    sh.putalpha(im.getchannel("A").point(lambda v: v * k))
    out.alpha_composite(sh, (pad, pad + dy))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def _save(im, path):
    im.save(path)
    return path


# ---------------------------------------------------------------- фон

def background(path, W, H, variant="plain"):
    """Графит с оранжевым свечением; grid — тонкая сетка-«нейросеть» точками."""
    im = Image.new("RGBA", (W, H), GRAPHITE)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.45, -H * 0.15, W * 1.4, H * 0.35], fill=(243, 83, 27, 46))
    gd.ellipse([-W * 0.5, H * 0.7, W * 0.5, H * 1.2], fill=(243, 83, 27, 30))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(180)))
    if variant == "grid":
        rnd = random.Random(4)
        d = ImageDraw.Draw(im)
        pts = [(rnd.uniform(0, W), rnd.uniform(0, H * 0.55)) for _ in range(46)]
        for i, a in enumerate(pts):
            for b in pts[i + 1:]:
                if math.dist(a, b) < 210:
                    d.line([a, b], fill=(243, 83, 27, 40), width=2)
        for x, y in pts:
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(243, 83, 27, 110))
    im.save(path)
    return path


def edge_mask(path, w, h, top=0, side=0, bottom=0):
    """Маска альфы клипа ведущей: мягкое растворение краёв в фон."""
    m = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(m)
    for i in range(top):
        d.line([(0, i), (w, i)], fill=int(255 * (i / top) ** 1.6))
    for i in range(bottom):
        d.line([(0, h - 1 - i), (w, h - 1 - i)], fill=int(255 * (i / bottom) ** 1.6))
    if side:
        s = Image.new("L", (w, h), 255)
        sd = ImageDraw.Draw(s)
        for i in range(side):
            v = int(255 * (i / side) ** 1.6)
            sd.line([(i, 0), (i, h)], fill=v)
            sd.line([(w - 1 - i, 0), (w - 1 - i, h)], fill=v)
        from PIL import ImageChops
        m = ImageChops.multiply(m, s)
    m.save(path)
    return path


def circle_mask(path, size):
    m = Image.new("L", (size * 2, size * 2), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 2 - 1, size * 2 - 1], fill=255)
    m.resize((size, size), Image.LANCZOS).save(path)
    return path


def ring(path, size, width=10):
    """Оранжевое кольцо вокруг круглого кадра ведущей."""
    s = size + 2 * width + 8
    im = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([8, 8, s * 2 - 9, s * 2 - 9], outline=ORANGE, width=width * 2)
    im = im.resize((s, s), Image.LANCZOS)
    return _save(_shadow(im, blur=18, k=0.7, dy=0), path)


# ---------------------------------------------------------------- типографика

def headline(path, lines, w, size=120, align="center", lh=1.12):
    """Заголовок Oswald капслоком. Строка — список кусков (текст, режим):
    'w' белый, 'o' оранжевый, 'box' белый на оранжевой плашке, 'g' серый."""
    f = font(F_HEAD, size)
    step = int(size * lh)
    pad = 26
    h = len(lines) * step + pad * 2 + int(size * 0.2)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = pad
    sp = tw(" ", f)
    for line in lines:
        segs = [(t.upper(), m) for t, m in line]
        full = sum(tw(t, f) for t, _ in segs) + sp * (len(segs) - 1)
        x = (w - full) / 2 if align == "center" else 0
        for t, m in segs:
            bw = tw(t, f)
            if m == "box":
                bb = tbox(t, f)
                d.rounded_rectangle([x - 16, y + bb[1] - 14, x + bw + 16, y + bb[3] + 14], radius=14, fill=ORANGE)
            col = {"w": WHITE, "o": ORANGE, "box": WHITE, "g": GREY}[m]
            d.text((x, y), t, font=f, fill=col)
            x += bw + sp
        y += step
    return _save(_shadow(im, blur=14, k=0.55), path)


def big_number(path, num, sub_lines, w, size=820):
    """Типографика на весь экран: огромная оранжевая цифра + подпись."""
    fn, fs = font(F_HEAD, size), font(F_HEAD, 104)
    bb = tbox(num, fn)
    nh = bb[3] - bb[1]
    h = nh + 60 + len(sub_lines) * 128 + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], -bb[1]), num, font=fn, fill=ORANGE)
    y = nh + 60
    for line in sub_lines:
        segs = [(t.upper(), m) for t, m in line]
        sp = tw(" ", fs)
        full = sum(tw(t, fs) for t, _ in segs) + sp * (len(segs) - 1)
        x = (w - full) / 2
        for t, m in segs:
            if m == "box":
                b2 = tbox(t, fs)
                d.rounded_rectangle([x - 14, y + b2[1] - 12, x + tw(t, fs) + 14, y + b2[3] + 12], radius=12,
                                    fill=ORANGE)
            d.text((x, y), t, font=fs, fill=WHITE if m != "o" else ORANGE)
            x += tw(t, fs) + sp
        y += 128
    return _save(_shadow(im, blur=18, k=0.5), path)


def rules_card(path, items, active, w=1000):
    """Карточка-список правил с состояниями: показаны пункты до active
    включительно, текущий — оранжевая плашка номера, прошлые — приглушены."""
    fn, ft = font(F_HEAD, 78), font(F_BODY, 58)
    row = 164
    h = 40 + len(items) * row + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=CARD, outline=(243, 83, 27, 120), width=3)
    y = 40
    for i, text in enumerate(items):
        if i > active:
            # будущий пункт — пустой слот (не спойлерим текст)
            d.rounded_rectangle([40, y + 12, 160, y + 132], radius=24, outline=(120, 120, 116, 160), width=3)
            d.rounded_rectangle([196, y + 60, w - 220, y + 84], radius=12, fill=(255, 255, 255, 22))
            y += row
            continue
        cur = i == active
        box = ORANGE if cur else (60, 62, 60, 255)
        d.rounded_rectangle([40, y + 12, 160, y + 132], radius=24, fill=box)
        num = f"0{i + 1}"
        nb = tbox(num, fn)
        d.text((100 - (nb[2] - nb[0]) / 2 - nb[0], y + 72 - (nb[3] - nb[1]) / 2 - nb[1]), num, font=fn,
               fill=WHITE)
        tb = tbox(text, ft)
        d.text((196, y + 72 - (tb[3] - tb[1]) / 2 - tb[1]), text, font=ft, fill=WHITE if cur else GREY)
        y += row
    return _save(_shadow(im, blur=18, k=0.6), path)


def cross_chip(path, text, crossed=True, w=None, color=None):
    """Чип «КАМЕРА» — перечёркнут оранжевой линией (crossed) или оранжевый
    чип-итог (crossed=False)."""
    f = font(F_HEAD, 92)
    bb = tbox(text.upper(), f)
    tw_ = bb[2] - bb[0]
    w = w or int(tw_ + 120)
    h = int(bb[3] - bb[1] + 70)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fill = color or (ORANGE if not crossed else (34, 36, 34, 245))
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=24, fill=fill,
                        outline=None if not crossed else (90, 92, 88, 255), width=3)
    tx = (w - tw_) / 2 - bb[0]
    d.text((tx, 35 - bb[1]), text.upper(), font=f, fill=WHITE if not crossed else GREY)
    if crossed:
        y = h / 2 + 4
        d.line([(tx - 18, y + 10), (tx + tw_ + 18, y - 10)], fill=ORANGE, width=14)
    return _save(_shadow(im, blur=14, k=0.6), path)


def flow(path, left, right, w=1000):
    """«ТЕКСТ → ВИДЕО»: два чипа и оранжевая стрелка между ними."""
    f = font(F_HEAD, 96)
    bl, br = tbox(left, f), tbox(right, f)
    hh = int(max(bl[3] - bl[1], br[3] - br[1]) + 70)
    im = Image.new("RGBA", (w, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = int(bl[2] - bl[0] + 100)
    rw = int(br[2] - br[0] + 100)
    gap = w - lw - rw
    d.rounded_rectangle([0, 0, lw, hh - 1], radius=24, fill=(34, 36, 34, 245), outline=(90, 92, 88, 255), width=3)
    d.text((50 - bl[0], 35 - bl[1]), left, font=f, fill=WHITE)
    d.rounded_rectangle([w - rw, 0, w - 1, hh - 1], radius=24, fill=ORANGE)
    d.text((w - rw + 50 - br[0], 35 - br[1]), right, font=f, fill=WHITE)
    cy = hh / 2
    x0, x1 = lw + 30, w - rw - 30
    d.line([(x0, cy), (x1 - 20, cy)], fill=ORANGE, width=14)
    d.polygon([(x1, cy), (x1 - 46, cy - 32), (x1 - 46, cy + 32)], fill=ORANGE)
    if gap < 140:
        raise ValueError("flow: слишком узко")
    return _save(_shadow(im, blur=14, k=0.6), path)


def tag(path, text, size=48):
    """Плашка-метка: оранжевая, белый текст."""
    f = font(F_HEAD, size)
    bb = tbox(text.upper(), f)
    w, h = int(bb[2] - bb[0] + 60), int(bb[3] - bb[1] + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=ORANGE)
    d.text((30 - bb[0], 20 - bb[1]), text.upper(), font=f, fill=WHITE)
    return _save(_shadow(im, blur=10, k=0.5), path)


def cta_card(path, w=1000):
    """Финальная карточка: «НАПИШИТЕ «ВЕДУЩИЙ» В ДИРЕКТ» + @iiavatar.video."""
    f1, f2 = font(F_HEAD, 112), font(F_BODY, 52)
    im = Image.new("RGBA", (w, 520), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 10
    for t, m in (("НАПИШИТЕ", "w"), ("«ВЕДУЩИЙ»", "box"), ("В ДИРЕКТ", "w")):
        bb = tbox(t, f1)
        x = (w - (bb[2] - bb[0])) / 2 - bb[0]
        if m == "box":
            d.rounded_rectangle([x + bb[0] - 22, y + bb[1] - 16, x + bb[2] + 22, y + bb[3] + 16], radius=18,
                                fill=ORANGE)
        d.text((x, y), t, font=f1, fill=WHITE)
        y += 132
    h2 = "@iiavatar.video"
    bb = tbox(h2, f2)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], y + 18), h2, font=f2, fill=CREAM)
    im = im.crop((0, 0, w, y + 18 + bb[3] + 20))
    return _save(_shadow(im, blur=16, k=0.6), path)


# ---------------------------------------------------------------- субтитры

def caption_layout(words, w):
    f = font(F_BODY, CAP_F)
    lines, cur = [], []
    for i in range(len(words)):
        if cur and tw(" ".join(words[j] for j in cur + [i]), f) > w - 90:
            lines.append(cur)
            cur = [i]
        else:
            cur.append(i)
    if cur:
        lines.append(cur)
    if len(lines) == 2 and len(lines[1]) == 1 and len(lines[0]) > 2:
        lines[1].insert(0, lines[0].pop())
    return lines


def caption(path, words, hi, w):
    """Крупный субтитр: тёмная плашка, белый текст; слово hi — белым на
    оранжевой плашке."""
    f = font(F_BODY, CAP_F)
    lines = caption_layout(words, w)
    lh = 82
    h = 36 + len(lines) * lh + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(17, 19, 17, 225))
    y = 34
    sp = tw(" ", f)
    for line in lines:
        full = sum(tw(words[i], f) for i in line) + sp * (len(line) - 1)
        x = (w - full) / 2
        for i in line:
            bw = tw(words[i], f)
            if i == hi:
                bb = tbox(words[i], f)
                d.rounded_rectangle([x - 12, y + bb[1] - 10, x + bw + 12, y + bb[3] + 12], radius=12, fill=ORANGE)
            d.text((x, y), words[i], font=f, fill=WHITE)
            x += bw + sp
        y += lh
    im.save(path)
    return path


def caption_height(words, w):
    return 36 + len(caption_layout(words, w)) * 82 + 30


# ---------------------------------------------------------------- эффекты

def swipe(path, W, H):
    """Переход: оранжевая диагональная полоса через кадр."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(W * 0.15, 0), (W * 0.85, 0), (W * 0.55, H), (-W * 0.15, H)], fill=ORANGE)
    im.save(path)
    return path


def scanlines(path, W, H):
    """Скан-линии и цветные полосы сбоя для кадра раскрытия."""
    rnd = random.Random(7)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 6):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 70), width=2)
    for _ in range(14):
        y = rnd.uniform(0, H)
        hh = rnd.uniform(6, 40)
        col = rnd.choice([(243, 83, 27, 120), (0, 220, 255, 90), (255, 255, 255, 70)])
        d.rectangle([0, y, W, y + hh], fill=col)
    im.save(path)
    return path


def flash(path, W, H, color="orange"):
    c = {"orange": (243, 83, 27, 120), "white": (255, 255, 255, 150)}[color]
    Image.new("RGBA", (W, H), c).save(path)
    return path
