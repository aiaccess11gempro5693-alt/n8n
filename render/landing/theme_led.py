"""Стиль «Табло лифта» для Instagram Reels ИИАВАТАР (борд
scratch/img/ig3_board_led.png, выбран 23.10.2026 для Reels №3 «Лифт и зеркала»):
почти чёрный #0E0E10, янтарный LED #FFB000, сталь #3A3D42, белый. Заголовки — Oswald
Bold капслоком, текст — Inter Bold. Язык: янтарное свечение на ключевом слове,
стальные плашки, LED-табло из точек (цифры этажей, «МИЛЛИОНЫ · 1 ГОД»), штамп.
Тот же набор компонентов, что в theme_light.py, плюс led_panel / stamp / photo_card.

Только оформление: компонент рисует RGBA PNG и возвращает путь.
Раскладку и тайминги задаёт скрипт ролика (build_ig3.py).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
F_HEAD = f"{FONTS}/Oswald-Bold.ttf"
F_BODY = f"{FONTS}/Inter-Bold.otf"
F_BODY_S = f"{FONTS}/Inter-SemiBold.otf"

GRAPHITE = (14, 14, 16, 255)       # фон (имя сохранено для совместимости)
ORANGE = (255, 176, 0, 255)        # акцент — янтарный LED
CREAM = (255, 255, 255, 255)
INK = (255, 255, 255, 255)         # основной текст на тёмном — белый
DARK = (14, 14, 16, 255)
WHITE = (255, 255, 255, 255)
GREY = (150, 152, 158, 255)
STEEL = (58, 61, 66, 255)
CARD = (34, 36, 40, 245)           # стальная карточка
PAD_COLOR = "0x0E0E10"
PROGRESS_COLOR = "0xFFB000"
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
    """Почти чёрный с янтарным свечением сверху; grid — LED-сетка точек и
    вертикальные стальные полосы (стены лифтовой шахты)."""
    im = Image.new("RGBA", (W, H), GRAPHITE)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.1, -H * 0.2, W * 0.9, H * 0.25], fill=(255, 176, 0, 46))
    gd.ellipse([-W * 0.4, H * 0.75, W * 0.6, H * 1.2], fill=(58, 61, 66, 90))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(170)))
    d = ImageDraw.Draw(im)
    if variant == "grid":
        for x in (90, W - 90):
            d.line([(x, 0), (x, H)], fill=(58, 61, 66, 160), width=3)
        for y in range(40, H, 34):
            for x in range(40, W, 34):
                a = 16 if (x * 7 + y * 3) % 11 else 44
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 176, 0, a))
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
            if m == "o":
                _glow_text(im, (x, y), t, f)
            col = {"w": INK, "o": ORANGE, "box": DARK, "g": GREY}[m]
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
            d.text((x, y), t, font=fs, fill=(DARK if m == "box" else INK) if m != "o" else ORANGE)
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
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=CARD, outline=(17, 17, 17, 40), width=3)
    y = 40
    for i, text in enumerate(items):
        if i > active:
            # будущий пункт — пустой слот (не спойлерим текст)
            d.rounded_rectangle([40, y + 12, 160, y + 132], radius=24, outline=(17, 17, 17, 60), width=3)
            d.rounded_rectangle([196, y + 60, w - 220, y + 84], radius=12, fill=(17, 17, 17, 18))
            y += row
            continue
        cur = i == active
        box = ORANGE if cur else (17, 17, 17, 255)
        d.rounded_rectangle([40, y + 12, 160, y + 132], radius=24, fill=box)
        num = f"0{i + 1}"
        nb = tbox(num, fn)
        d.text((100 - (nb[2] - nb[0]) / 2 - nb[0], y + 72 - (nb[3] - nb[1]) / 2 - nb[1]), num, font=fn,
               fill=DARK if cur else WHITE)
        tb = tbox(text, ft)
        d.text((196, y + 72 - (tb[3] - tb[1]) / 2 - tb[1]), text, font=ft, fill=INK if cur else GREY)
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
    fill = color or (CARD if not crossed else (34, 36, 40, 230))
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=24, fill=fill, outline=ORANGE if not crossed else STEEL,
                        width=4)
    tx = (w - tw_) / 2 - bb[0]
    d.text((tx, 35 - bb[1]), text.upper(), font=f, fill=ORANGE if not crossed else GREY)
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
    d.rounded_rectangle([0, 0, lw, hh - 1], radius=24, fill=CARD, outline=STEEL, width=3)
    d.text((50 - bl[0], 35 - bl[1]), left, font=f, fill=INK)
    d.rounded_rectangle([w - rw, 0, w - 1, hh - 1], radius=24, fill=ORANGE)
    d.text((w - rw + 50 - br[0], 35 - br[1]), right, font=f, fill=DARK)
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
    d.text((30 - bb[0], 20 - bb[1]), text.upper(), font=f, fill=DARK)
    return _save(_shadow(im, blur=10, k=0.5), path)


def cta_card(path, w=1000, word="ЛИФТ"):
    """Финальная карточка: «НАПИШИТЕ «СЛОВО» В ДИРЕКТ» + @iiavatar.video."""
    f1, f2 = font(F_HEAD, 112), font(F_BODY, 52)
    im = Image.new("RGBA", (w, 520), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 10
    for t, m in (("НАПИШИТЕ", "w"), (f"«{word}»", "box"), ("В ДИРЕКТ", "w")):
        bb = tbox(t, f1)
        x = (w - (bb[2] - bb[0])) / 2 - bb[0]
        if m == "box":
            d.rounded_rectangle([x + bb[0] - 22, y + bb[1] - 16, x + bb[2] + 22, y + bb[3] + 16], radius=18,
                                fill=ORANGE)
        d.text((x, y), t, font=f1, fill=DARK if m == "box" else INK)
        y += 132
    h2 = "@iiavatar.video"
    bb = tbox(h2, f2)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], y + 18), h2, font=f2, fill=GREY)
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
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(14, 14, 16, 225), outline=(58, 61, 66, 255), width=3)
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
            d.text((x, y), words[i], font=f, fill=DARK if i == hi else WHITE)
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
        col = rnd.choice([(255, 176, 0, 110), (0, 200, 255, 70), (14, 14, 16, 90)])
        d.rectangle([0, y, W, y + hh], fill=col)
    im.save(path)
    return path


def flash(path, W, H, color="orange"):
    c = {"orange": (255, 176, 0, 120), "white": (255, 255, 255, 150)}[color]
    Image.new("RGBA", (W, H), c).save(path)
    return path


# ---------------------------------------------------------------- «Табло лифта»

def _glow_text(im, xy, text, f, color=ORANGE, blur=14):
    """Янтарное свечение под текстом (как у LED)."""
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).text(xy, text, font=f, fill=color[:3] + (200,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))


def _dots(text, f_size, pitch, color=ORANGE, off=(58, 52, 40, 255), cols=None):
    """Текст точечной матрицей: рисуем мелко, каждую «клетку» — точкой."""
    f = font(F_HEAD, f_size)
    bb = tbox(text, f)
    tw_, th = bb[2] - bb[0], bb[3] - bb[1]
    m = Image.new("L", (int(tw_) + 2, int(th) + 2), 0)
    ImageDraw.Draw(m).text((-bb[0] + 1, -bb[1] + 1), text, font=f, fill=255)
    nx, ny = m.width, m.height
    if cols:
        nx = max(nx, cols)
    im = Image.new("RGBA", (nx * pitch, ny * pitch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = pitch * 0.36
    ox = (nx - m.width) // 2
    for y in range(ny):
        for x in range(nx):
            mx = x - ox
            on = 0 <= mx < m.width and m.getpixel((mx, y)) > 110
            cx, cy = x * pitch + pitch / 2, y * pitch + pitch / 2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color if on else off)
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    glow.alpha_composite(im)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(pitch * 0.9)))
    out.alpha_composite(im)
    return out


def led_panel(path, kicker, text, w=980, size=16, pitch=5):
    """Стальная плашка с подписью и LED-табло из точек: «УСКОРИТЬ ЛИФТЫ:» /
    «МИЛЛИОНЫ · 1 ГОД»."""
    fk = font(F_BODY, 46)
    led = _dots(text.upper(), size, pitch)
    if led.width > w - 100:
        raise ValueError(f"led_panel: «{text}» шире карточки")
    kb = tbox(kicker.upper(), fk)
    sh = led.height + 60
    h = 40 + (kb[3] - kb[1]) + 30 + sh + 44
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=30, fill=CARD, outline=STEEL, width=4)
    for x in range(0, w, 6):   # шлифованная сталь
        d.line([(x, 4), (x, h - 5)], fill=(255, 255, 255, 6 if (x // 6) % 3 else 12), width=1)
    for cx, cy in ((26, 26), (w - 26, 26), (26, h - 26), (w - 26, h - 26)):   # винты
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(90, 94, 100, 255))
    d.text((50 - kb[0], 40 - kb[1]), kicker.upper(), font=fk, fill=WHITE)
    sy = 40 + (kb[3] - kb[1]) + 30
    d.rounded_rectangle([40, sy, w - 40, sy + sh], radius=16, fill=(8, 8, 9, 255), outline=(70, 60, 30, 255), width=3)
    im.alpha_composite(led, (int((w - led.width) / 2), int(sy + 30)))
    return _save(_shadow(im, blur=18, k=0.7), path)


def floor_display(path, text, arrow="up", size=22, pitch=8):
    """Табло этажа: стрелка ▲/▼ и цифры точками в чёрной рамке."""
    led = _dots(text, size, pitch)
    a = led.height
    w = a + 40 + led.width + 80
    h = led.height + 60
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=18, fill=(8, 8, 9, 255), outline=STEEL, width=4)
    x0, y0 = 30, 30
    tri = [(x0, y0 + a), (x0 + a, y0 + a), (x0 + a / 2, y0)] if arrow == "up" else \
          [(x0, y0), (x0 + a, y0), (x0 + a / 2, y0 + a)]
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(tri, fill=ORANGE)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    im.alpha_composite(g)
    im.alpha_composite(led, (int(x0 + a + 40), 30))
    return _save(_shadow(im, blur=14, k=0.7), path)


def stamp(path, lines, angle=-8, size=86):
    """Штамп: янтарная двойная рамка, текст капслоком, лёгкий наклон."""
    f = font(F_HEAD, size)
    step = int(size * 1.08)
    widths = [tbox(t.upper(), f)[2] - tbox(t.upper(), f)[0] for t in lines]
    w = int(max(widths) + 110)
    h = int(len(lines) * step + 80)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, w - 5, h - 5], radius=20, fill=(14, 14, 16, 200), outline=ORANGE, width=9)
    d.rounded_rectangle([20, 20, w - 21, h - 21], radius=12, outline=ORANGE, width=3)
    y = 40
    for t in lines:
        bb = tbox(t.upper(), f)
        x = (w - (bb[2] - bb[0])) / 2 - bb[0]
        _glow_text(im, (x, y - bb[1] + 4), t.upper(), f, blur=10)
        d.text((x, y - bb[1] + 4), t.upper(), font=f, fill=ORANGE)
        y += step
    im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im, blur=16, k=0.8), path)


def photo_card(path, src, w=980, h=None, caption=None):
    """Картинка истории в стальной рамке с янтарной кромкой; caption — плашка снизу."""
    ph = Image.open(src).convert("RGBA")
    h = h or int(w * ph.height / ph.width)
    k = max(w / ph.width, h / ph.height)
    ph = ph.resize((int(ph.width * k) + 1, int(ph.height * k) + 1), Image.LANCZOS)
    ph = ph.crop(((ph.width - w) // 2, (ph.height - h) // 2, (ph.width - w) // 2 + w, (ph.height - h) // 2 + h))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=30, fill=255)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.paste(ph, (0, 0), m)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=30, outline=STEEL, width=8)
    d.rounded_rectangle([8, 8, w - 9, h - 9], radius=24, outline=(255, 176, 0, 170), width=3)
    if caption:
        fc = font(F_HEAD, 64)
        bb = tbox(caption.upper(), fc)
        cw, ch = bb[2] - bb[0] + 60, bb[3] - bb[1] + 40
        x0, y0 = (w - cw) / 2, h - ch - 34
        d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=14, fill=ORANGE)
        d.text((x0 + 30 - bb[0], y0 + 20 - bb[1]), caption.upper(), font=fc, fill=DARK)
    return _save(_shadow(im, blur=20, k=0.8), path)
