"""Стиль ролика 4 «Продукт за 60 секунд» — сервис доставки «Быстро».

Дизайн-система A «Свежий рынок» (борд scratch/img/l4_board2_a.png, выбран
07.10.2026; тёмный «Тёмный продукт» отклонён как похожий на прошлые ролики):
кремовый фон #FFF6E9, свежий зелёный #23A455, томатный #FF4B2E, горчичный
#FFC531, чернила #1E2A22. Шрифт — Nunito Black/ExtraBold (округлый, как Fredoka
на борде; у Fredoka нет кириллицы). Знака ₽ в Nunito нет — он берётся из Rubik.

Язык компонентов: стикеры с белой обводкой и мягкой тенью, крупные цифры,
ценник-«бирка», дудл-стрелки и искры, скруглённые пилюли. Компоненты рисуют
RGBA PNG; монтажный движок — render/landing/build_l3.py (через build_l4.py).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
F_HEAD = f"{FONTS}/Nunito-Black.ttf"
F_BODY = f"{FONTS}/Nunito-ExtraBold.ttf"
F_BODY_S = f"{FONTS}/Nunito-Bold.ttf"
F_RUB = f"{FONTS}/Rubik-ExtraBold.ttf"

CREAM = (255, 246, 233, 255)
GREEN = (35, 164, 85, 255)
TOMATO = (255, 75, 46, 255)
MUSTARD = (255, 197, 49, 255)
INK = (30, 42, 34, 255)
WHITE = (255, 255, 255, 255)
GREY = (150, 150, 140, 255)
PAD_COLOR = "0xFFF6E9"   # фон под тряской кадра

_fc = {}


def font(path, size):
    from PIL import ImageFont
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def tw(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(text, font=f)


def tbox(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textbbox((0, 0), text, font=f)


def _save(im, path):
    im.save(path)
    return path


def _shadow(im, blur=16, k=0.28, dx=0, dy=12, pad=34):
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (60, 40, 20, 255))
    sh.putalpha(im.getchannel("A").point(lambda v: v * k))
    out.alpha_composite(sh, (pad + dx, pad + dy))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def _outline(im, width=10, color=WHITE):
    """Белая обводка-«стикер» по альфе."""
    a = im.getchannel("A")
    grown = a.filter(ImageFilter.MaxFilter(width * 2 + 1))
    out = Image.new("RGBA", im.size, color[:3] + (0,))
    out.putalpha(grown)
    out.alpha_composite(im)
    return out


def _pad(im, p):
    out = Image.new("RGBA", (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    out.alpha_composite(im, (p, p))
    return out


def text_runs(d, x, y, text, f, fill):
    """Текст с подменой ₽ на глиф из Rubik (в Nunito его нет)."""
    parts = text.split("₽")
    for i, part in enumerate(parts):
        d.text((x, y), part, font=f, fill=fill)
        x += tw(part, f)
        if i < len(parts) - 1:
            fr = font(F_RUB, int(f.size * 0.92))
            d.text((x, y + f.size * 0.06), "₽", font=fr, fill=fill)
            x += tw("₽", fr)
    return x


def text_w(text, f):
    parts = text.split("₽")
    fr = font(F_RUB, int(f.size * 0.92))
    return sum(tw(p, f) for p in parts) + tw("₽", fr) * (len(parts) - 1)


# ---------------------------------------------------------------- фоны

def sparkle(d, cx, cy, r, color, wdt=7):
    for a in range(4):
        ang = a * math.pi / 2
        d.line([(cx + math.cos(ang) * r * 0.35, cy + math.sin(ang) * r * 0.35),
                (cx + math.cos(ang) * r, cy + math.sin(ang) * r)], fill=color, width=wdt)


def background(path, W, H, variant="plain", seed=0):
    """Кремовый фон. plain — мягкие пятна цвета; doodle — плюс дудлы
    (искры, листики-дуги, точки); green / mustard / tomato — заливка цветом
    палитры для типографических сцен."""
    flat = variant.endswith("_flat")   # заливка цветом без дудлов (под заголовки)
    variant = variant.replace("_flat", "")
    base = {"green": GREEN, "mustard": MUSTARD, "tomato": TOMATO}.get(variant, CREAM)
    im = Image.new("RGBA", (W, H), base)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    if base == CREAM:
        g.ellipse([-W * 0.4, -H * 0.1, W * 0.6, H * 0.35], fill=(255, 197, 49, 60))
        g.ellipse([W * 0.45, H * 0.55, W * 1.4, H * 1.05], fill=(35, 164, 85, 40))
    else:
        g.ellipse([-W * 0.3, -H * 0.2, W * 0.9, H * 0.45], fill=(255, 255, 255, 50))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(170)))
    if variant in ("doodle", "green", "mustard", "tomato") and not flat:
        rnd = random.Random(seed + 11)
        d = ImageDraw.Draw(im)
        col = (255, 255, 255, 90) if base != CREAM else (35, 164, 85, 70)
        col2 = (255, 255, 255, 70) if base != CREAM else (255, 75, 46, 60)
        for _ in range(7):
            sparkle(d, rnd.randint(40, W - 40), rnd.randint(40, H - 40), rnd.randint(18, 34), col, 6)
        for _ in range(26):
            x, y = rnd.randint(0, W), rnd.randint(0, H)
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=col2)
    im.save(path)
    return path


def photo_bg(path, photo, W, H, ax=0.5, ay=0.5, zoom=1.0):
    """Продуктовый кадр на весь экран (cover-кроп)."""
    ph = Image.open(photo).convert("RGB")
    k = max(W / ph.width, H / ph.height) * zoom
    ph = ph.resize((round(ph.width * k), round(ph.height * k)), Image.LANCZOS)
    ox, oy = int((ph.width - W) * ax), int((ph.height - H) * ay)
    ph.crop((ox, oy, ox + W, oy + H)).save(path)
    return path


def photo_half(path, photo, W, H, rect, fade_side=None, ax=0.5, ay=0.5, variant="plain", grey=0.0):
    """Кремовый фон + фото в прямоугольнике rect (x, y, w, h); fade_side —
    сторона, где фото растворяется в фон; grey — доля обесцвечивания («было»)."""
    im = Image.open(background(path, W, H, variant)).convert("RGBA")
    x, y, w, h = rect
    ph = Image.open(photo).convert("RGB")
    k = max(w / ph.width, h / ph.height)
    ph = ph.resize((round(ph.width * k), round(ph.height * k)), Image.LANCZOS)
    ox, oy = int((ph.width - w) * ax), int((ph.height - h) * ay)
    ph = ph.crop((ox, oy, ox + w, oy + h))
    if grey:
        ph = Image.blend(ph, ph.convert("L").convert("RGB"), grey)
    ph = ph.convert("RGBA")
    if fade_side:
        a = Image.new("L", (w, h), 255)
        d = ImageDraw.Draw(a)
        band = int(w * 0.35)
        for i in range(band):
            v = int(255 * (i / band) ** 1.6)
            xx = w - band + i if fade_side == "right" else band - 1 - i
            d.line([(xx, 0), (xx, h)], fill=255 - v)
        ph.putalpha(a)
    im.alpha_composite(ph, (x, y))
    im.save(path)
    return path


# ---------------------------------------------------------------- типографика

def headline(path, lines, w, size=104, align="left", lh=1.34):
    """Заголовок. Строка — список кусков (текст, режим): 'k' чернила,
    'g' зелёный, 't' томатный, 'w' белый, 'G' белым по зелёной пилюле,
    'T' белым по томатной, 'M' чернилами по горчичной."""
    f = font(F_HEAD, size)
    step = int(size * lh)
    pad = 26
    h = len(lines) * step + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = pad
    for line in lines:
        full = sum(text_w(t, f) for t, _ in line) + tw(" ", f) * (len(line) - 1) \
            + sum(size * 0.5 for _, m in line if m.isupper())
        x = (w - full) / 2 if align == "center" else (w - full if align == "right" else 0)
        for t, m in line:
            bw = text_w(t, f)
            if m.isupper():
                bb = tbox(t, f)
                fill = {"G": GREEN, "T": TOMATO, "M": MUSTARD}[m]
                d.rounded_rectangle([x, y + bb[1] - size * 0.16, x + bw + size * 0.5, y + bb[3] + size * 0.2],
                                    radius=int(size * 0.32), fill=fill)
                x += size * 0.25
            col = {"k": INK, "g": GREEN, "t": TOMATO, "w": WHITE, "G": WHITE, "T": WHITE, "M": INK}[m]
            text_runs(d, x, y, t, f, col)
            x += bw + tw(" ", f) + (size * 0.25 if m.isupper() else 0)
        y += step
    return _save(_shadow(_pad(im, 12), k=0.18), path)


def logo(path, size=150, angle=-6, text="Быстро"):
    """Логотип-стикер (по умолчанию «Быстро») с полосками скорости: зелёная пилюля, белая обводка."""
    f = font(F_HEAD, size)
    t = text
    bb = tbox(t, f)
    tw_ = bb[2] - bb[0]
    w, h = int(tw_ + size * 1.5), int((bb[3] - bb[1]) + size * 0.7)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=GREEN)
    d.text((size * 0.45 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), t, font=f, fill=WHITE)
    # «молния» — три полоски скорости справа
    cx = size * 0.45 + tw_ + size * 0.18
    for i, dy in enumerate((-0.18, 0, 0.18)):
        y = h / 2 + dy * size
        d.rounded_rectangle([cx + i * 6, y - 7, cx + size * 0.55 - i * 10, y + 7], radius=7, fill=MUSTARD)
    im = _outline(_pad(im, 16), 12).rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im), path)


def sticker_text(path, text, fill=TOMATO, ink=WHITE, size=72, angle=-5):
    """Короткая надпись-стикер на пилюле с белой обводкой."""
    f = font(F_HEAD, size)
    bb = tbox(text, f)
    w, h = int(text_w(text, f) + size * 0.9), int((bb[3] - bb[1]) + size * 0.62)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=fill)
    text_runs(d, size * 0.45, (h - (bb[3] - bb[1])) / 2 - bb[1], text, f, ink)
    im = _outline(_pad(im, 14), 10).rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im), path)


def timer(path, text="60:00", size=170, fill=TOMATO, angle=-4):
    """Таймер-стикер: круглый будильник-циферблат слева + цифры на пилюле."""
    f = font(F_HEAD, size)
    bb = tbox(text, f)
    r = int(size * 0.62)
    w, h = int(r * 2 + (bb[2] - bb[0]) + size * 0.75), int(max(2 * r, (bb[3] - bb[1]) + size * 0.5))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([r, (h - (bb[3] - bb[1]) - size * 0.46) / 2, w - 1, (h + (bb[3] - bb[1]) + size * 0.46) / 2],
                        radius=int(size * 0.4), fill=fill)
    cy = h / 2
    d.ellipse([0, cy - r, 2 * r, cy + r], fill=WHITE, outline=fill, width=int(size * 0.09))
    d.line([(r, cy), (r, cy - r * 0.6)], fill=INK, width=int(size * 0.08))
    d.line([(r, cy), (r + r * 0.45, cy)], fill=INK, width=int(size * 0.08))
    d.ellipse([r - 10, cy - 10, r + 10, cy + 10], fill=INK)
    d.text((2 * r + size * 0.2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), text, font=f, fill=WHITE)
    im = _outline(_pad(im, 16), 12).rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im), path)


def big_number(path, num, unit, sub, color=GREEN, w=760, k=1.0):
    """Огромная цифра + единица («60 мин») и подпись под ней; карточка-стикер.
    k — масштаб шрифтов (для тесных раскладок)."""
    fn = font(F_HEAD, int(300 * k))
    fu = font(F_HEAD, int(110 * k))
    fs = font(F_BODY, int(62 * k))
    nb = tbox(num, fn)
    nw = text_w(num, fn)
    uw = text_w(unit, fu)
    w = max(w, int(nw + 24 + uw + 120), int(text_w(sub, fs) + 68 + 80))   # содержимое всегда влезает
    h = 70 + (nb[3] - nb[1]) + 40 + 90 + 50
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=60, fill=WHITE)
    x0 = (w - nw - 24 - uw) / 2
    text_runs(d, x0, 70 - nb[1], num, fn, color)
    ub = tbox(unit, fu)
    text_runs(d, x0 + nw + 24, 70 + (nb[3] - nb[1]) - (ub[3] - ub[1]) - ub[1] - 8, unit, fu, INK)
    sw = text_w(sub, fs)
    sy = 70 + (nb[3] - nb[1]) + 40
    d.rounded_rectangle([(w - sw) / 2 - 34, sy, (w + sw) / 2 + 34, sy + 90], radius=45, fill=color)
    sb = tbox(sub, fs)
    text_runs(d, (w - sw) / 2, sy + (90 - (sb[3] - sb[1])) / 2 - sb[1], sub, fs, WHITE)
    return _save(_shadow(_outline(_pad(im, 12), 10)), path)


def price_tag(path, big="0 ₽", small="доставка", note="от 1 000 ₽", w=720, angle=6):
    """Ценник-бирка: горчичная бирка с дыркой и верёвочкой, крупное «0 ₽»."""
    fb = font(F_HEAD, 230)
    fs = font(F_BODY, 66)
    fn = font(F_HEAD, 70)
    bb = tbox(big, fb)
    h = 60 + 70 + 20 + (bb[3] - bb[1]) + 40 + 100 + 60
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    notch = 120
    d.polygon([(notch, 0), (w - 1, 0), (w - 1, h - 1), (notch, h - 1), (0, h / 2)], fill=MUSTARD)
    d.ellipse([notch * 0.45 - 22, h / 2 - 22, notch * 0.45 + 22, h / 2 + 22], fill=CREAM)
    cx = notch + (w - notch) / 2
    y = 60
    sw = text_w(small, fs)
    text_runs(d, cx - sw / 2, y - tbox(small, fs)[1], small, fs, INK)
    y += 90
    text_runs(d, cx - text_w(big, fb) / 2, y - bb[1], big, fb, INK)
    y += (bb[3] - bb[1]) + 40
    nw = text_w(note, fn)
    nb = tbox(note, fn)
    d.rounded_rectangle([cx - nw / 2 - 34, y, cx + nw / 2 + 34, y + 100], radius=50, fill=GREEN)
    text_runs(d, cx - nw / 2, y + (100 - (nb[3] - nb[1])) / 2 - nb[1], note, fn, WHITE)
    im = _outline(_pad(im, 16), 12)
    return _save(_shadow(im.rotate(angle, resample=Image.BICUBIC, expand=True)), path)


def photo_card(path, photo, w, h, ax=0.5, ay=0.5, angle=0, radius=56):
    """Продуктовый кадр в скруглённой рамке-стикере."""
    ph = Image.open(photo).convert("RGB")
    k = max(w / ph.width, h / ph.height)
    ph = ph.resize((round(ph.width * k), round(ph.height * k)), Image.LANCZOS)
    ox, oy = int((ph.width - w) * ax), int((ph.height - h) * ay)
    ph = ph.crop((ox, oy, ox + w, oy + h)).convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    ph.putalpha(m)
    im = _outline(_pad(ph, 16), 14)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im), path)


def map_chip(path, text="Курьер на карте"):
    """Чип: точка курьера-«пин» + надпись."""
    f = font(F_HEAD, 64)
    bb = tbox(text, f)
    h = 130
    w = int(128 + tw(text, f) + 50)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=WHITE)
    d.ellipse([28, 28, 102, 102], fill=TOMATO)
    d.ellipse([52, 52, 78, 78], fill=WHITE)
    d.text((128 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=INK)
    return _save(_shadow(_outline(_pad(im, 10), 8)), path)


def was_card(path, items, w=940):
    """«Было»: серая карточка, пункты зачёркнуты томатной линией."""
    fh = font(F_HEAD, 84)
    fi = font(F_BODY, 70)
    h = 60 + 100 + len(items) * 96 + 50
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=56, fill=(232, 228, 220, 255))
    d.text((60, 60 - tbox("Было", fh)[1]), "Было", font=fh, fill=GREY)
    y = 60 + 110
    for it in items:
        bb = tbox(it, fi)
        d.text((60, y - bb[1]), it, font=fi, fill=GREY)
        mid = y + (bb[3] - bb[1]) / 2
        d.line([(50, mid + 4), (60 + bb[2] + 14, mid - 6)], fill=TOMATO, width=10)
        y += 96
    return _save(_shadow(_pad(im, 8), k=0.15), path)


def now_card(path, big="3", text="касания", w=940):
    """«Стало»: зелёная карточка, огромная «3» и три круга-касания."""
    fb = font(F_HEAD, 260)
    fh = font(F_HEAD, 84)
    ft = font(F_HEAD, 96)
    h = 470
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=56, fill=GREEN)
    d.text((60, 56 - tbox("Стало", fh)[1]), "Стало", font=fh, fill=MUSTARD)
    bb = tbox(big, fb)
    d.text((60 - bb[0], h - 50 - bb[3]), big, font=fb, fill=WHITE)
    tb = tbox(text, ft)
    tx = 60 + (bb[2] - bb[0]) + 40
    d.text((tx, h - 70 - tb[3]), text, font=ft, fill=WHITE)
    for i in range(3):   # касания — круги с «волной»
        cx, cy = w - 110 - i * 120, 110
        d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=WHITE)
        d.ellipse([cx - 58, cy - 58, cx + 58, cy + 58], outline=(255, 255, 255, 140), width=6)
    return _save(_shadow(_outline(_pad(im, 12), 10)), path)


def strike_chip(path, text, size=56, angle=0):
    """Серый чип с томатным зачёркиванием: «уже дома — не покупаем»."""
    f = font(F_HEAD, size)
    bb = tbox(text, f)
    h = int((bb[3] - bb[1]) + size * 0.8)
    w = int(tw(text, f) + size * 1.1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=WHITE)
    x0 = size * 0.55
    d.text((x0 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=INK)
    d.line([(x0 - 10, h / 2 + 6), (x0 + tw(text, f) + 10, h / 2 - 6)], fill=TOMATO, width=max(6, size // 7))
    im = _outline(_pad(im, 10), 8)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im), path)


def list_card(path, title, items, done, w=860, size=56):
    """Карточка-корзина: заголовок и пункты; первые done пунктов — с зелёной галочкой."""
    fh = font(F_HEAD, int(size * 1.15))
    fi = font(F_BODY, size)
    step = int(size * 1.6)
    h = 50 + int(size * 1.4) + 30 + len(items) * step + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=48, fill=WHITE)
    d.text((48, 50 - tbox(title, fh)[1]), title, font=fh, fill=GREEN)
    y = 50 + int(size * 1.4) + 30
    for i, it in enumerate(items):
        r = size * 0.5
        cyy = y + size * 0.55
        if i < done:
            d.ellipse([48, cyy - r, 48 + 2 * r, cyy + r], fill=GREEN)
            check_mark(d, 48 + r * 0.45, cyy - r * 0.5, r * 1.1, WHITE, max(5, size // 9))
            col = INK
        else:
            d.ellipse([48, cyy - r, 48 + 2 * r, cyy + r], outline=(210, 205, 195, 255), width=5)
            col = (190, 186, 178, 255)
        tb = tbox(it, fi)
        d.text((48 + 2 * r + 26, cyy - (tb[1] + tb[3]) / 2 + size * 0.06), it, font=fi, fill=col)
        y += step
    return _save(_shadow(_outline(_pad(im, 12), 10)), path)


def chip(path, text, fill=WHITE, ink=INK, size=66, angle=0, dot=None):
    """Чип-аудитория: пилюля с цветной точкой."""
    f = font(F_HEAD, size)
    bb = tbox(text, f)
    h = int((bb[3] - bb[1]) + size * 0.8)
    pad_l = int(size * 1.25) if dot else int(size * 0.5)
    w = int(tw(text, f) + pad_l + size * 0.55)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=fill)
    if dot:
        r = size * 0.3
        d.ellipse([size * 0.5 - r + 6, h / 2 - r, size * 0.5 + r + 6, h / 2 + r], fill=dot)
    d.text((pad_l - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=ink)
    im = _outline(_pad(im, 10), 8)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im), path)


def cta_button(path, text="Скачать «Быстро»", w=960, size=82):
    """Кнопка-призыв: томатная пилюля со стрелкой-треугольником."""
    f = font(F_HEAD, size)
    bb = tbox(text, f)
    h = int(size * 2.3)
    w = max(w, int((bb[2] - bb[0]) + 90 + size * 1.6))   # текст и стрелка всегда влезают
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=TOMATO)
    tx = (w - (bb[2] - bb[0]) - 90) / 2
    d.text((tx - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=WHITE)
    ax = tx + (bb[2] - bb[0]) + 40
    d.polygon([(ax, h / 2 - 32), (ax + 52, h / 2), (ax, h / 2 + 32)], fill=WHITE)
    return _save(_shadow(_outline(_pad(im, 12), 10)), path)


def doodle_arrow(path, w=240, h=200, color=GREEN, flip=False):
    """Дудл-стрелка от руки (дуга с наконечником)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(20 + (w - 60) * t, h - 30 - math.sin(t * math.pi) * (h - 70)) for t in [i / 30 for i in range(31)]]
    d.line(pts, fill=color, width=12, joint="curve")
    ex, ey = pts[-1]
    d.line([(ex, ey), (ex - 44, ey - 18)], fill=color, width=12)
    d.line([(ex, ey), (ex - 18, ey - 44)], fill=color, width=12)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return _save(im, path)


def check_mark(d, x, y, s, color=WHITE, width=None):
    width = width or max(6, int(s * 0.16))
    d.line([(x, y + s * 0.5), (x + s * 0.38, y + s * 0.85), (x + s, y + s * 0.1)], fill=color, width=width,
           joint="curve")


def tick_tag(path, text, fill=GREEN, size=60, angle=0):
    """Бирка с галочкой: «плотные ✓»."""
    f = font(F_HEAD, size)
    bb = tbox(text, f)
    h = int((bb[3] - bb[1]) + size * 0.8)
    r = h * 0.36
    w = int(tw(text, f) + size * 0.6 + 2 * r + size * 0.5)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=fill)
    cxx = size * 0.35 + r
    d.ellipse([cxx - r, h / 2 - r, cxx + r, h / 2 + r], fill=WHITE)
    check_mark(d, cxx - r * 0.55, h / 2 - r * 0.5, r * 1.1, fill, max(5, int(size * 0.1)))
    d.text((cxx + r + size * 0.3 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=WHITE)
    im = _outline(_pad(im, 10), 8)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im), path)


def notif_card(path, title, sub, w=720):
    """Пуш-уведомление: белая карточка, зелёный значок-корзина, заголовок и строка."""
    ft = font(F_HEAD, 58)
    fs = font(F_BODY_S, 46)
    h = 190
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=44, fill=WHITE)
    d.rounded_rectangle([30, 35, 150, 155], radius=32, fill=GREEN)
    # корзина
    d.polygon([(55, 80), (125, 80), (115, 130), (65, 130)], fill=WHITE)
    d.arc([70, 55, 110, 95], 180, 360, fill=WHITE, width=7)
    d.text((180 - tbox(title, ft)[0], 40 - tbox(title, ft)[1]), title, font=ft, fill=INK)
    d.text((180, 118 - tbox(sub, fs)[1]), sub, font=fs, fill=GREY)
    d.ellipse([w - 60, 30, w - 30, 60], fill=TOMATO)
    return _save(_shadow(_outline(_pad(im, 10), 8)), path)


def steps_card(path, steps, w=960):
    """«Стало»: зелёная карточка с тремя шагами-кругами и стрелками."""
    fh = font(F_HEAD, 70)
    fs = font(F_HEAD, 52)
    h = 470
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=56, fill=GREEN)
    d.text((56, 44 - tbox("Стало: 3 касания", fh)[1]), "Стало: 3 касания", font=fh, fill=WHITE)
    n = len(steps)
    seg = (w - 80) / n
    for i, st in enumerate(steps):
        cxx = 40 + seg * (i + 0.5)
        d.ellipse([cxx - 70, 170, cxx + 70, 310], fill=WHITE)
        nb = tbox(str(i + 1), fh)
        d.text((cxx - (nb[2] - nb[0]) / 2 - nb[0], 240 - (nb[3] - nb[1]) / 2 - nb[1]), str(i + 1), font=fh, fill=GREEN)
        sb = tbox(st, fs)
        d.text((cxx - (sb[2] - sb[0]) / 2 - sb[0], 350 - sb[1]), st, font=fs, fill=WHITE)
        if i < n - 1:
            ax = cxx + 95
            d.polygon([(ax, 222), (ax + 34, 240), (ax, 258)], fill=MUSTARD)
    return _save(_shadow(_outline(_pad(im, 12), 10)), path)


def down_arrow(path, h=160, color=GREEN):
    """Толстая скруглённая стрелка вниз («было → стало»)."""
    w = int(h * 0.9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sw = int(w * 0.3)
    d.rounded_rectangle([(w - sw) / 2, 0, (w + sw) / 2, h * 0.62], radius=sw // 2, fill=color)
    d.polygon([(0, h * 0.45), (w, h * 0.45), (w / 2, h)], fill=color)
    return _save(_outline(_pad(im, 10), 8), path)


def sparkles(path, w=200, color=MUSTARD):
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sparkle(d, w * 0.38, w * 0.42, w * 0.32, color, 11)
    sparkle(d, w * 0.78, w * 0.2, w * 0.15, color, 8)
    sparkle(d, w * 0.75, w * 0.78, w * 0.12, color, 7)
    return _save(im, path)


def ring(path, size, color=GREEN, width=22):
    """Кольцо вокруг лица в круглой раскладке."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([width / 2, width / 2, size - width / 2, size - width / 2], outline=color, width=width)
    d.ellipse([width * 1.6, width * 1.6, size - width * 1.6, size - width * 1.6], outline=WHITE, width=8)
    return _save(im, path)


# ---------------------------------------------------------------- субтитры

CAP_F = 58


def caption_layout(words, w):
    f = font(F_BODY, CAP_F)
    lines, cur = [], []
    for i, word in enumerate(words):
        if cur and text_w(" ".join(words[j] for j in cur + [i]), f) > w - 90:
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
    """Субтитр: белая скруглённая плашка с тонкой зелёной обводкой, чернильный
    Nunito; текущее слово — на горчичной пилюле."""
    f = font(F_BODY, CAP_F)
    lines = caption_layout(words, w)
    lh = 80
    h = 36 + len(lines) * lh + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=40, fill=(255, 255, 255, 245), outline=GREEN, width=5)
    y = 34
    sp = tw(" ", f)
    for line in lines:
        full = sum(text_w(words[i], f) for i in line) + sp * (len(line) - 1)
        x = (w - full) / 2
        for i in line:
            bw = text_w(words[i], f)
            if i == hi:
                bb = tbox(words[i], f)
                d.rounded_rectangle([x - 12, y + bb[1] - 10, x + bw + 12, y + bb[3] + 12], radius=22, fill=MUSTARD)
            text_runs(d, x, y, words[i], f, INK)
            x += bw + sp
        y += lh
    im.save(path)
    return path


# ---------------------------------------------------------------- переход и вспышки

def swipe(path, W, H):
    """Переход: зелёная волна с горчичной каймой пролетает через кадр."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    amp, band = 70, W * 0.62

    def edge(off):
        return [(W * 0.5 + off + amp * math.sin(y / H * math.pi * 3), y) for y in range(0, H + 1, 20)]
    left, right = edge(-band / 2), edge(band / 2)
    d.polygon(left + right[::-1], fill=GREEN)
    for e in (left, right):
        d.line(e, fill=MUSTARD, width=26)
    return _save(im, path)


def flash(path, W, H, color="yellow"):
    c = {"yellow": (255, 197, 49, 120), "green": (35, 164, 85, 110), "white": (255, 255, 255, 170),
         "red": (255, 75, 46, 110)}[color]
    Image.new("RGBA", (W, H), c).save(path)
    return path
