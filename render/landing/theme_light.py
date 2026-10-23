"""Стиль «Светлый журнальный» для Instagram Reels ИИАВАТАР (борд
scratch/img/ig2_board_light.png, выбран 23.10.2026 для Reels №2): тёплый белый
#F5F3EE, чернила #111111, сигнальный красный #FF3B30. Заголовки — Oswald Bold
капслоком (как Bebas Neue на борде), текст — Montserrat ExtraBold. Язык: красные
плашки под ключевым словом, красные подчёркивания, белые карточки с тонкой
рамкой, крупные субтитры на тёмной плашке с текущим словом в красной.
Тот же набор компонентов, что в theme_brand.py — меняются только цвета.

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

GRAPHITE = (245, 243, 238, 255)   # фон (имя сохранено для совместимости)
ORANGE = (255, 59, 48, 255)        # акцент — сигнальный красный
CREAM = (17, 17, 17, 255)
INK = (17, 17, 17, 255)
WHITE = (255, 255, 255, 255)
GREY = (120, 118, 112, 255)
CARD = (255, 255, 255, 250)
PAD_COLOR = "0xF5F3EE"
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
    sh.putalpha(im.getchannel("A").point(lambda v: v * k * 0.45))   # на светлом фоне тень мягче
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
    gd.ellipse([W * 0.45, -H * 0.15, W * 1.4, H * 0.35], fill=(255, 59, 48, 22))
    gd.ellipse([-W * 0.5, H * 0.7, W * 0.5, H * 1.2], fill=(17, 17, 17, 14))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(180)))
    if variant == "grid":
        rnd = random.Random(4)
        d = ImageDraw.Draw(im)
        pts = [(rnd.uniform(0, W), rnd.uniform(0, H * 0.55)) for _ in range(46)]
        for i, a in enumerate(pts):
            for b in pts[i + 1:]:
                if math.dist(a, b) < 210:
                    d.line([a, b], fill=(17, 17, 17, 14), width=2)
        for x, y in pts:
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 59, 48, 80))
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
            col = {"w": INK, "o": ORANGE, "box": WHITE, "g": GREY}[m]
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
            d.text((x, y), t, font=fs, fill=(WHITE if m == "box" else INK) if m != "o" else ORANGE)
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
               fill=WHITE)
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
    fill = color or (ORANGE if not crossed else (255, 255, 255, 250))
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=24, fill=fill,
                        outline=None if not crossed else (17, 17, 17, 50), width=3)
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
    d.rounded_rectangle([0, 0, lw, hh - 1], radius=24, fill=(255, 255, 255, 250), outline=(17, 17, 17, 50), width=3)
    d.text((50 - bl[0], 35 - bl[1]), left, font=f, fill=INK)
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
        d.text((x, y), t, font=f1, fill=WHITE if m == "box" else INK)
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
        col = rnd.choice([(255, 59, 48, 110), (0, 200, 255, 80), (17, 17, 17, 60)])
        d.rectangle([0, y, W, y + hh], fill=col)
    im.save(path)
    return path


def flash(path, W, H, color="orange"):
    c = {"orange": (255, 59, 48, 110), "white": (255, 255, 255, 170)}[color]
    Image.new("RGBA", (W, H), c).save(path)
    return path


# ---------------------------------------------------------------- Reels №2: кривая забывания

def _curve_points(x0, y0, w, h, jumps, n=240):
    """Кривая удержания: 100 % → экспоненциальное падение; на каждом повторении
    (доля оси x) — подскок к 100 % и более пологое падение."""
    import math as m
    pts, level_start, tau, t_prev = [], 1.0, 0.18, 0.0
    marks = []
    js = list(jumps)
    for i in range(n + 1):
        t = i / n
        if js and t >= js[0]:
            js.pop(0)
            marks.append(len(pts))
            t_prev, tau = t, tau * 2.4
        v = 0.2 + 0.8 * m.exp(-(t - t_prev) / tau)
        pts.append((x0 + w * t, y0 + h * (1 - v)))
    return pts, marks


def chart(path, mode, state, w=980, labels=None, h=720):
    """Карточка-график «Кривая забывания». mode='forget' — одна падающая линия;
    state 1 — с отметкой «−50 % за сутки». mode='repeat' — state = число
    повторений (0–3): на каждом линия подскакивает вверх, подписи под точками."""
    fT, fS, fM = font(F_HEAD, 62), font(F_BODY_S, 34), font(F_HEAD, 44)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=CARD, outline=(17, 17, 17, 40), width=3)
    d.text((44, 34), "КРИВАЯ ЗАБЫВАНИЯ", font=fT, fill=INK)
    gx, gy, gw, gh = 110, 150, w - 170, h - 270
    for k, lab in ((0, "100%"), (0.5, "50%"), (1, "0%")):
        y = gy + gh * k
        d.line([(gx, y), (gx + gw, y)], fill=(17, 17, 17, 30), width=2)
        d.text((gx - 92, y - 18), lab, font=fS, fill=GREY)
    d.line([(gx, gy), (gx, gy + gh)], fill=INK, width=4)
    d.line([(gx, gy + gh), (gx + gw, gy + gh)], fill=INK, width=4)
    jumps = [0.22, 0.48, 0.78][:state] if mode == "repeat" else []
    pts, marks = _curve_points(gx, gy, gw, gh, jumps)
    d.line(pts, fill=ORANGE, width=10, joint="curve")
    if mode == "forget":
        d.text((gx + 10, gy + gh + 24), "время", font=fS, fill=GREY)
        if state >= 1:
            i = int(len(pts) * 0.2)
            x, y = pts[i]
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=ORANGE)
            tag_t = "−50% за сутки"
            tb = tbox(tag_t, fM)
            bx, by = x + 34, y - 30
            d.rounded_rectangle([bx, by - 10, bx + tb[2] - tb[0] + 40, by + tb[3] - tb[1] + 22], radius=14, fill=ORANGE)
            d.text((bx + 20 - tb[0], by + 6 - tb[1]), tag_t, font=fM, fill=WHITE)
    else:
        names = labels or ["сейчас", "завтра", "через неделю"]
        for k, idx in enumerate(marks):
            x, y = pts[idx]
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=ORANGE)
            lab = names[k]
            lw = tw(lab, fS)
            d.text((x - lw / 2, gy + gh + 24), lab, font=fS, fill=INK)
            d.line([(x, y + 18), (x, gy + gh)], fill=(255, 59, 48, 120), width=3)
    return _save(_shadow(im, blur=18, k=0.5), path)


def question_card(path, kicker, lines, w=980):
    """Карточка вопроса: красная плашка-киккер и крупный вопрос."""
    fk, fq = font(F_HEAD, 56), font(F_BODY, 62)
    lh = 80
    kb = tbox(kicker.upper(), fk)
    h = 60 + (kb[3] - kb[1]) + 40 + len(lines) * lh + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=CARD, outline=(17, 17, 17, 40), width=3)
    kw = kb[2] - kb[0] + 50
    d.rounded_rectangle([40, 40, 40 + kw, 40 + kb[3] - kb[1] + 30], radius=12, fill=ORANGE)
    d.text((65 - kb[0], 55 - kb[1]), kicker.upper(), font=fk, fill=WHITE)
    y = 40 + kb[3] - kb[1] + 30 + 40
    for line in lines:
        d.text((44, y), line, font=fq, fill=INK)
        y += lh
    return _save(_shadow(im, blur=18, k=0.5), path)


def countdown(path, num, size=300):
    """Круг обратного отсчёта с цифрой (3, 2, 1)."""
    f = font(F_HEAD, int(size * 0.62))
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([6, 6, size - 6, size - 6], fill=(255, 255, 255, 250), outline=ORANGE, width=12)
    bb = tbox(str(num), f)
    d.text(((size - (bb[2] - bb[0])) / 2 - bb[0], (size - (bb[3] - bb[1])) / 2 - bb[1]), str(num), font=f, fill=INK)
    return _save(_shadow(im, blur=14, k=0.5), path)


def answer_card(path, word, w=980):
    """Ответ: слово крупно на красной плашке и галочка."""
    f = font(F_HEAD, 130)
    bb = tbox(word.upper(), f)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    h = bh + 90
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    total = bw + 60 + 40 + h
    x0 = (w - total) / 2
    d.rounded_rectangle([x0, 0, x0 + bw + 60, h - 1], radius=22, fill=ORANGE)
    d.text((x0 + 30 - bb[0], 45 - bb[1]), word.upper(), font=f, fill=WHITE)
    cx = x0 + bw + 60 + 40 + h / 2
    cy, r = h / 2, h / 2 - 4
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK)
    d.line([(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.35), (cx + r * 0.5, cy - r * 0.35)], fill=WHITE, width=16,
           joint="curve")
    return _save(_shadow(im, blur=14, k=0.5), path)
