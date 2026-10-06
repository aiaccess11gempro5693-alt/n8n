"""Стиль «Reels-эксперт», вариант A (борд scratch/img/l3_board_a.png, выбран
05.10.2026, на основе scratch/img/l2_board_reels.png): глубокий чёрный #0E0E10,
кислотный жёлтый #FFE600, алярм-красный #FF3B30, белый, серый #8E8E93.
Заголовки — Unbounded Black капслоком, текст — Montserrat ExtraBold.
Язык: жёлтые мазки кисти под ключевыми словами, красные резиновые штампы,
тёмные стикеры с белым контуром и жёлтым номером, полутоновые точки,
крупные субтитры с подсветкой текущего слова жёлтой плашкой.

Только оформление: каждый компонент рисует RGBA PNG и возвращает путь.
Раскладку кадров и тайминги задаёт скрипт ролика (build_l3.py).
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
F_HEAD = f"{FONTS}/Unbounded-Black.ttf"
F_BODY = f"{FONTS}/Montserrat-ExtraBold.ttf"
F_BODY_S = f"{FONTS}/Montserrat-SemiBold.ttf"
F_STAMP = f"{FONTS}/Oswald-Bold.ttf"

BLACK = (14, 14, 16, 255)
YELLOW = (255, 230, 0, 255)
RED = (255, 59, 48, 255)
WHITE = (255, 255, 255, 255)
GREY = (142, 142, 147, 255)
CARD = (26, 26, 30, 255)
GREEN = (52, 199, 89, 255)

_fc = {}


def font(path, size):
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def tw(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(text, font=f)


def tbox(text, f):
    """Реальные границы глифов (x0, y0, x1, y1) от точки рисования (0, 0)."""
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textbbox((0, 0), text, font=f)


def wrap(text, f, max_w):
    lines, cur = [], []
    for word in text.split():
        trial = " ".join(cur + [word])
        if cur and tw(trial, f) > max_w:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    return lines + [" ".join(cur)] if cur else lines


def _save(im, path):
    bb = im.getchannel("A").getbbox()
    im.save(path)
    return path


def _shadow(im, blur=14, k=0.6, dx=0, dy=10, pad=30):
    """Мягкая тень под элементом (читаемость поверх видео)."""
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 255))
    sh.putalpha(im.getchannel("A").point(lambda v: v * k))
    out.alpha_composite(sh, (pad + dx, pad + dy))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


# ---------------------------------------------------------------- фактуры

def brush(w, h, color=YELLOW, seed=1, tilt=0.0):
    """Мазок кисти: рваные края и сужение к концам."""
    rnd = random.Random(seed)
    s = 2   # рисуем вдвое крупнее и уменьшаем — края мягче
    W, H = w * s, h * s
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    n = 60
    top, bot = [], []
    for i in range(n + 1):
        x = W * i / n
        taper = min(1.0, (i / n) / 0.06, (1 - i / n) / 0.09)
        taper = max(0.25, taper)
        mid = H / 2 + math.sin(i / n * math.pi) * H * tilt
        half = H * 0.42 * taper
        top.append((x, mid - half - rnd.uniform(0, H * 0.06)))
        bot.append((x, mid + half + rnd.uniform(0, H * 0.06)))
    d.polygon(top + bot[::-1], fill=255)
    # рваные концы
    for _ in range(40):
        x = rnd.choice([rnd.uniform(0, W * 0.07), rnd.uniform(W * 0.9, W)])
        y = rnd.uniform(0, H)
        r = rnd.uniform(3, 10)
        d.ellipse([x - r, y - r, x + r, y + r], fill=0)
    im = im.filter(ImageFilter.GaussianBlur(1.2)).resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), color)
    out.putalpha(im)
    return out


def halftone(w, h, color=WHITE, step=26, seed=0):
    """Полутоновые точки: крупные в углу, тают к краю (декор борда)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, h, step):
        for x in range(0, w, step):
            k = 1 - math.hypot(x / w, y / h) / 1.2
            r = step * 0.42 * k
            if r > 1.2:
                d.ellipse([x - r, y - r, x + r, y + r], fill=color)
    return im


def _grunge(alpha, seed=3, k=0.12):
    """Потёртость штампа: выбитые точки и царапины в альфе."""
    rnd = random.Random(seed)
    m = Image.new("L", alpha.size, 255)
    d = ImageDraw.Draw(m)
    w, h = alpha.size
    for _ in range(int(w * h * k / 400)):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(1, 4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rnd.randint(0, 120))
    for _ in range(6):
        y = rnd.uniform(0, h)
        d.line([(0, y), (w, y + rnd.uniform(-10, 10))], fill=150, width=2)
    return ImageChops.multiply(alpha, m)


# ---------------------------------------------------------------- фоны

def background(path, W, H, variant="plain", seed=0):
    """Глубокий чёрный. plain — лёгкая виньетка; dots — полутон в углу и
    жёлтая световая полоса; type — для типографики (крупный полутон)."""
    im = Image.new("RGBA", (W, H), BLACK)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-W * 0.3, H * 0.15, W * 0.6, H * 0.6], fill=(255, 230, 0, 26))
    gd.ellipse([W * 0.5, H * 0.45, W * 1.3, H * 0.95], fill=(255, 59, 48, 22))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    if variant in ("dots", "type"):
        ht = halftone(int(W * 0.55), int(H * 0.28), (255, 255, 255, 40 if variant == "dots" else 60))
        im.alpha_composite(ht.transpose(Image.FLIP_LEFT_RIGHT), (W - ht.width, 0))
    if variant == "type":
        ht = halftone(int(W * 0.5), int(H * 0.22), (255, 230, 0, 70), step=30)
        im.alpha_composite(ht.transpose(Image.FLIP_TOP_BOTTOM), (0, H - ht.height))
    im.save(path)
    return path


# ---------------------------------------------------------------- типографика

def headline(path, lines, w, size=96, align="left", lh=1.22):
    """Заголовок Unbounded капслоком. lines — список строк; строка — список
    кусков (текст, режим): 'w' белый, 'y' жёлтый, 'b' чёрный по жёлтому мазку,
    'r' белый по красному мазку."""
    f = font(F_HEAD, size)
    step = int(size * lh)
    pad = 24
    h = len(lines) * step + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = pad
    for li, line in enumerate(lines):
        segs = [(t.upper(), m) for t, m in line]
        full = sum(tw(t, f) for t, _ in segs) + tw(" ", f) * (len(segs) - 1)
        x = (w - full) / 2 if align == "center" else (w - full if align == "right" else 0)
        for si, (t, m) in enumerate(segs):
            bw = tw(t, f)
            if m in ("b", "r"):
                bb = tbox(t, f)
                br = brush(int(bw + size * 0.6), int((bb[3] - bb[1]) + size * 0.34),
                           YELLOW if m == "b" else RED, seed=li * 7 + si + len(t))
                im.alpha_composite(br, (int(x - size * 0.3), int(y + bb[1] - size * 0.17)))
            col = {"w": WHITE, "y": YELLOW, "b": BLACK, "r": WHITE}[m]
            d.text((x, y), t, font=f, fill=col)
            x += bw + tw(" ", f)
        y += step
    return _save(_shadow(im, blur=12, k=0.5), path)


def big_three(path, w):
    """Типографика на весь экран: огромная жёлтая «3», «признака» белым,
    «мошенника» чёрным по жёлтому мазку, жёлтая стрелка-росчерк."""
    fn, fh = font(F_HEAD, 760), font(F_HEAD, 96)
    h = 1250
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bb = tbox("3", fn)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], -bb[1]), "3", font=fn, fill=YELLOW)
    # искры вокруг цифры, как на борде
    cx, top = w / 2 + (bb[2] - bb[0]) / 2 + 30, 40
    for a, l in ((-60, 70), (-25, 90), (10, 60)):
        r = math.radians(a)
        d.line([(cx + 20 * math.cos(r), top + 120 + 20 * math.sin(r)),
                (cx + (20 + l) * math.cos(r), top + 120 + (20 + l) * math.sin(r))], fill=YELLOW, width=12)
    y = bb[3] - bb[1] + 50
    t1 = "ПРИЗНАКА"
    d.text(((w - tw(t1, fh)) / 2, y), t1, font=fh, fill=WHITE)
    y += 150
    t2 = "МОШЕННИКА"
    b2 = tbox(t2, fh)
    br = brush(int(tw(t2, fh) + 90), int(b2[3] - b2[1] + 70), YELLOW, seed=11)
    x2 = (w - tw(t2, fh)) / 2
    im.alpha_composite(br, (int(x2 - 45), int(y + b2[1] - 35)))
    d.text((x2, y), t2, font=fh, fill=BLACK)
    return _save(_shadow(im, blur=16, k=0.5), path)


def scribble_arrow(path, w=260, h=150, color=YELLOW, flip=False):
    """Жёлтая стрелка-росчерк от руки."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(10 + (w - 60) * t, h - 30 - (h - 70) * (t ** 1.8) + 18 * math.sin(t * 6)) for t in
           [i / 30 for i in range(31)]]
    d.line(pts, fill=color, width=12, joint="curve")
    ex, ey = pts[-1]
    d.line([(ex - 44, ey + 6), (ex, ey), (ex - 18, ey + 42)], fill=color, width=12, joint="curve")
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return _save(im, path)


# ---------------------------------------------------------------- штамп

def stamp(path, text, size=110, angle=-8, color=RED, seed=5):
    """Красный резиновый штамп: двойная рамка, потёртость, наклон."""
    f = font(F_STAMP, size)
    bb = tbox(text, f)
    tw_, th = bb[2] - bb[0], bb[3] - bb[1]
    px, py = int(size * 0.42), int(size * 0.3)
    w, h = tw_ + 2 * px, th + 2 * py
    a = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(a)
    lw = max(6, size // 13)
    d.rounded_rectangle([lw // 2, lw // 2, w - lw // 2, h - lw // 2], radius=size // 6, outline=255, width=lw)
    i = lw * 2 + 2
    d.rounded_rectangle([i, i, w - i, h - i], radius=size // 9, outline=255, width=max(3, lw // 2))
    d.text((px - bb[0], py - bb[1]), text, font=f, fill=255)
    a = _grunge(a, seed=seed)
    im = Image.new("RGBA", (w, h), color)
    im.putalpha(a)
    im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im, blur=8, k=0.45, dy=6), path)


# ---------------------------------------------------------------- иконки

def _handset_img(s, color, call=False):
    """Телефонная трубка из фигур (в шрифтах нет подходящего глифа):
    дуга-корпус и два «стакана» на концах. call=True — наклон «вызов»,
    иначе горизонтально («сброс»)."""
    S = s * 4
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    cx, cy, R, t = S / 2, S * 0.74, S * 0.40, S * 0.13
    a0, a1 = 212, 328
    d.arc([cx - R, cy - R, cx + R, cy + R], a0, a1, fill=255, width=int(t))
    for a in (a0, a1):
        r = math.radians(a)
        rm = R - t / 2
        ex, ey = cx + rm * math.cos(r), cy + rm * math.sin(r)
        ex -= math.cos(r) * S * 0.07
        ey -= math.sin(r) * S * 0.07
        cup = Image.new("L", (int(S * 0.30), int(S * 0.19)), 0)
        ImageDraw.Draw(cup).rounded_rectangle([0, 0, cup.width - 1, cup.height - 1], radius=int(S * 0.08), fill=255)
        cup = cup.rotate(-(a + 90), resample=Image.BICUBIC, expand=True)
        m.paste(255, (int(ex - cup.width / 2), int(ey - cup.height / 2)), cup)
    bb = m.getbbox()
    m = m.crop(bb)
    side = max(m.size)
    sq = Image.new("L", (side, side), 0)
    sq.paste(m, ((side - m.width) // 2, (side - m.height) // 2))
    if call:
        sq = sq.rotate(135, resample=Image.BICUBIC, expand=False)
    sq = sq.resize((s, s), Image.LANCZOS)
    out = Image.new("RGBA", (s, s), color)
    out.putalpha(sq)
    return out


def _handset(im, cx, cy, s, color, hang=False):
    h = _handset_img(int(s), color, call=not hang)
    im.alpha_composite(h, (int(cx - s / 2), int(cy - s / 2)))


def icon_from_black(src, size):
    """Иконка gpt-image-2 на чёрном фоне → RGBA (альфа по яркости)."""
    im = Image.open(src).convert("RGB").resize((size, size), Image.LANCZOS)
    r, g, b = im.split()
    a = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 0 if v < 30 else min(255, (v - 30) * 2))
    out = im.convert("RGBA")
    out.putalpha(a)
    return out


# ---------------------------------------------------------------- компоненты

def call_card(path, w=900):
    """Входящий звонок: тёмная карточка, «Служба безопасности банка»,
    красная и зелёная кнопки."""
    size = 56
    while size > 36 and tw("Служба безопасности", font(F_BODY, size)) > w - 260:
        size -= 2
    fk, fn, fs = font(F_BODY_S, 30), font(F_BODY, size), font(F_BODY_S, 30)
    h = 470
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=44, fill=(24, 24, 28, 240), outline=(255, 255, 255, 70), width=3)
    d.text((48, 40), "ВХОДЯЩИЙ ВЫЗОВ", font=fk, fill=GREY)
    d.ellipse([w - 80, 50, w - 56, 74], fill=RED)
    # аватар-кружок «нет фото»
    d.ellipse([48, 104, 188, 244], fill=(60, 60, 66, 255))
    d.ellipse([96, 128, 140, 172], fill=(140, 140, 148, 255))
    d.pieslice([72, 180, 164, 272], 180, 360, fill=(140, 140, 148, 255))
    y = 112
    for line in ["Служба безопасности", "банка"]:
        d.text((220, y), line, font=fn, fill=WHITE)
        y += int(size * 1.2)
    d.text((222, y + 6), "+7 9•• ••• •• ••", font=fs, fill=GREY)
    for cx, col, hang in ((w * 0.27, RED, True), (w * 0.73, GREEN, False)):
        cy, r = 375, 58
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        _handset(im, cx, cy, 72, WHITE, hang=hang)
    return _save(_shadow(im, blur=18, k=0.7), path)


def sticker(path, num, lines, icon=None, w=620, vertical=False):
    """Стикер-признак: тёмная карточка с белым контуром, жёлтый номер,
    иконка и крупный текст. vertical — иконка сверху, текст под ней."""
    ft, fn = font(F_BODY, 50 if not vertical else 46), font(F_HEAD, 46)
    lh = 60 if not vertical else 56
    ic = (150 if not vertical else 150) if icon else 0
    if vertical:
        h = 40 + ic + 16 + len(lines) * lh + 30
    else:
        h = max(ic + 60, 60 + len(lines) * lh + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=30, fill=CARD, outline=(255, 255, 255, 220), width=4)
    d.ellipse([-14, -14, 66, 66], fill=YELLOW)
    nb = tbox(str(num), fn)
    d.text((26 - (nb[2] - nb[0]) / 2 - nb[0], 26 - (nb[3] - nb[1]) / 2 - nb[1]), str(num), font=fn, fill=BLACK)
    if vertical:
        if icon:
            im.alpha_composite(icon_from_black(icon, ic), ((w - ic) // 2, 40))
        y = 40 + ic + 16
        for line in lines:
            d.text(((w - tw(line, ft)) / 2, y), line, font=ft, fill=WHITE)
            y += lh
        return _save(_shadow(im, blur=14, k=0.6), path)
    x = 36
    if icon:
        im.alpha_composite(icon_from_black(icon, ic), (24, (h - ic) // 2))
        x = 24 + ic + 18
    y = (h - len(lines) * lh) / 2 - 4
    for line in lines:
        d.text((x, y), line, font=ft, fill=WHITE)
        y += lh
    return _save(_shadow(im, blur=14, k=0.6), path)


def code_card(path, w=620, pill_lines=("БАНК НЕ СПРАШИВАЕТ",)):
    """Код из СМС «••••», перечёркнутый красным, + плашка «банк не спрашивает»."""
    fp = font(F_BODY, 40)
    bw, bh = min(400, w - 40), 150
    ph = 40 + len(pill_lines) * 50
    h = bh + 50 + ph + 10
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bx = (w - bw) // 2
    d.rounded_rectangle([bx, 0, bx + bw, bh], radius=26, fill=CARD, outline=WHITE, width=5)
    step = (bw - 100) / 3
    for i in range(4):
        cx = bx + 50 + i * step
        d.ellipse([cx - 20, bh / 2 - 20, cx + 20, bh / 2 + 20], fill=WHITE)
    d.line([(bx - 14, bh + 4), (bx + bw + 14, -4)], fill=RED, width=16)
    pw = max(tw(t, fp) for t in pill_lines) + 60
    px = (w - pw) / 2
    d.rounded_rectangle([px, bh + 50, px + pw, bh + 50 + ph], radius=34, fill=RED)
    y = bh + 50 + 20
    for t in pill_lines:
        pb = tbox(t, fp)
        d.text(((w - tw(t, fp)) / 2, y - pb[1] + 4), t, font=fp, fill=WHITE)
        y += 50
    return _save(_shadow(im, blur=14, k=0.6), path)


def viewfinder(path, size, color=YELLOW, rec=True):
    """Рамка-видоискатель: жёлтые уголки и «REC»."""
    pad = 20
    im = Image.new("RGBA", (size + 2 * pad, size + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    L, lw = size // 6, 12
    a, b = pad, pad + size
    for x, y, dx, dy in ((a, a, 1, 1), (b, a, -1, 1), (a, b, 1, -1), (b, b, -1, -1)):
        d.line([(x, y + dy * L), (x, y), (x + dx * L, y)], fill=color, width=lw, joint="curve")
    if rec:
        f = font(F_BODY, 34)
        d.ellipse([b - 150, a + 36, b - 126, a + 60], fill=RED)
        d.text((b - 116, a + 28), "REC", font=f, fill=WHITE)
    return _save(im, path)


def icon_tile(path, icon, size=220):
    """Отдельная иконка (без карточки) — для сцены с крупным заголовком."""
    return _save(_shadow(icon_from_black(icon, size), blur=10, k=0.4), path)


def action_button(path, label_lines, color, hang, w=None):
    """Круглая кнопка звонка + крупная подпись Unbounded."""
    fl = font(F_HEAD, 50)
    r = 82
    lh = 62
    w = w or int(2 * r + 34 + max(tw(l.upper(), fl) for l in label_lines) + 10)
    h = max(2 * r, len(label_lines) * lh) + 10
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = h / 2
    d.ellipse([0, cy - r, 2 * r, cy + r], fill=color)
    _handset(im, r, cy, 96, WHITE if hang else BLACK, hang=hang)
    y = cy - len(label_lines) * lh / 2
    for line in label_lines:
        d.text((2 * r + 34, y), line.upper(), font=fl, fill=WHITE)
        y += lh
    return _save(_shadow(im, blur=12, k=0.6), path)


def card_back(path, w=600, _base=True):
    """Оборот банковской карты: полоса, подпись, номер телефона банка в
    жёлтом росчерке-овале. Номер — заглушка, без реальных банков."""
    if _base and w != 600:
        card_back(path, 600, _base=False)
        im = Image.open(path)
        k = w / 600
        im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS).save(path)
        return path
    fs, fn = font(F_BODY_S, 26), font(F_BODY, 44)
    h = int(w * 0.63)
    pad = 40
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], radius=30, fill=(46, 46, 52, 255),
                        outline=(255, 255, 255, 60), width=2)
    d.rectangle([pad, pad + 40, pad + w, pad + 110], fill=(10, 10, 12, 255))
    d.rectangle([pad + 36, pad + 140, pad + w * 0.62, pad + 190], fill=(230, 230, 230, 255))
    d.text((pad + 36, pad + 214), "Телефон банка", font=fs, fill=GREY)
    num = "8 800 •••-••-••"
    d.text((pad + 36, pad + 262), num, font=fn, fill=WHITE)
    nb = tbox(num, fn)
    ex0, ey0 = pad + 36 + nb[0] - 26, pad + 262 + nb[1] - 22
    ex1, ey1 = pad + 36 + nb[2] + 26, pad + 262 + nb[3] + 22
    d.ellipse([ex0, ey0, ex1, ey1], outline=YELLOW, width=8)
    d.ellipse([ex0 + 8, ey0 - 6, ex1 - 4, ey1 + 4], outline=YELLOW, width=4)
    im = im.rotate(-5, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im, blur=16, k=0.7), path)


# ---------------------------------------------------------------- субтитры

CAP_F = 60


def caption_layout(words, w):
    """Раскладка чанка субтитров: строки слов в пределах ширины плашки."""
    f = font(F_BODY, CAP_F)
    lines, cur = [], []
    for i, word in enumerate(words):
        if cur and tw(" ".join(words[j] for j in cur + [i]), f) > w - 90:
            lines.append(cur)
            cur = [i]
        else:
            cur.append(i)
    if cur:
        lines.append(cur)
    # баланс: не оставлять одинокое короткое слово на второй строке
    if len(lines) == 2 and len(lines[1]) == 1 and len(lines[0]) > 2:
        lines[1].insert(0, lines[0].pop())
    return lines


def caption(path, words, hi, w):
    """Крупный субтитр: чёрная плашка, белый Montserrat ExtraBold; слово hi
    (индекс) — чёрным по жёлтой плашке. hi=None — без подсветки."""
    f = font(F_BODY, CAP_F)
    lines = caption_layout(words, w)
    lh = 80
    h = 36 + len(lines) * lh + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(14, 14, 16, 230))
    y = 34
    sp = tw(" ", f)
    for line in lines:
        full = sum(tw(words[i], f) for i in line) + sp * (len(line) - 1)
        x = (w - full) / 2
        for i in line:
            bw = tw(words[i], f)
            if i == hi:
                bb = tbox(words[i], f)
                d.rounded_rectangle([x - 12, y + bb[1] - 10, x + bw + 12, y + bb[3] + 12], radius=12, fill=YELLOW)
                d.text((x, y), words[i], font=f, fill=BLACK)
            else:
                d.text((x, y), words[i], font=f, fill=WHITE)
            x += bw + sp
        y += lh
    im.save(path)
    return path


def swipe(path, W, H):
    """Переход: широкий жёлтый мазок по диагонали."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    br = brush(int(W * 1.7), int(H * 0.5), YELLOW, seed=21).rotate(58, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(br, ((W - br.width) // 2, (H - br.height) // 2)) if br.width <= W else None
    if br.width > W:
        cx, cy = (br.width - W) // 2, (br.height - H) // 2
        im = br.crop((cx, cy, cx + W, cy + H))
    im.save(path)
    return path


# ---------------------------------------------------------------- 16:9

def photo_bg(path, photo, W, H, rect=None, dark=0.3, fade_side=None, ax=0.5, ay=0.5):
    """Фон-кадр: чёрный + фото (cover-кроп) в прямоугольнике rect (x, y, w, h),
    затемнённое на dark; fade_side='right'|'left' — фото уходит в черноту."""
    im = Image.open(background(path, W, H, "plain")).convert("RGBA")
    x, y, w, h = rect or (0, 0, W, H)
    ph = Image.open(photo).convert("RGB")
    k = max(w / ph.width, h / ph.height)
    ph = ph.resize((round(ph.width * k), round(ph.height * k)), Image.LANCZOS)
    ox, oy = int((ph.width - w) * ax), int((ph.height - h) * ay)
    ph = ph.crop((ox, oy, ox + w, oy + h))
    ph = Image.blend(ph, Image.new("RGB", ph.size, BLACK[:3]), dark).convert("RGBA")
    if fade_side:
        a = Image.new("L", (w, h), 255)
        d = ImageDraw.Draw(a)
        band = int(w * 0.4)
        for i in range(band):
            v = int(255 * (i / band) ** 1.5)
            xx = w - band + i if fade_side == "right" else band - i
            d.line([(xx, 0), (xx, h)], fill=255 - v)
        ph.putalpha(a)
    im.alpha_composite(ph, (x, y))
    im.save(path)
    return path


def tag(path, text, color=YELLOW, size=44):
    """Плашка-метка Unbounded: «01 · ДАВЛЕНИЕ»."""
    f = font(F_HEAD, size)
    bb = tbox(text.upper(), f)
    w, h = int(bb[2] - bb[0] + 56), int(bb[3] - bb[1] + 40)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=color)
    d.text((28 - bb[0], 20 - bb[1]), text.upper(), font=f, fill=BLACK if color == YELLOW else WHITE)
    im = im.rotate(-2, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im, blur=10, k=0.5), path)


def quote_card(path, lines, w=720, size=58, color=WHITE, ink=BLACK):
    """Реплика собеседника: белая карточка-«пузырь» с жёлтой кавычкой,
    кавычка — отдельной строкой над текстом (ничего не наезжает)."""
    f, fq = font(F_BODY, size), font(F_HEAD, int(size * 1.7))
    lh = int(size * 1.22)
    qb = tbox("“", fq)
    qh = qb[3] - qb[1]
    h = 40 + qh + 16 + len(lines) * lh + 46
    im = Image.new("RGBA", (w, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=color)
    d.polygon([(70, h - 2), (150, h - 2), (60, h + 38)], fill=color)
    d.text((44 - qb[0], 40 - qb[1]), "“", font=fq, fill=YELLOW if color == WHITE else BLACK)
    y = 40 + qh + 16
    for line in lines:
        d.text((44, y), line, font=f, fill=ink)
        y += lh
    im = im.rotate(2, resample=Image.BICUBIC, expand=True)
    return _save(_shadow(im, blur=16, k=0.6), path)


def step_row(path, num, text, w=760, done=False):
    """Шаг «что делать»: жёлтый квадрат с цифрой + крупный текст."""
    fn, ft = font(F_HEAD, 54), font(F_BODY, 56)
    s = 96
    h = s + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 4, s, 4 + s], radius=18, fill=YELLOW)
    nb = tbox(str(num), fn)
    d.text(((s - (nb[2] - nb[0])) / 2 - nb[0], 4 + (s - (nb[3] - nb[1])) / 2 - nb[1]), str(num), font=fn, fill=BLACK)
    tb = tbox(text, ft)
    d.text((s + 30, 4 + (s - (tb[3] - tb[1])) / 2 - tb[1]), text, font=ft, fill=WHITE)
    return _save(_shadow(im, blur=10, k=0.6), path)


def icon_text(path, icon, lines, w=760, ic=170, size=56, color=WHITE):
    """Иконка слева + крупный текст справа (без карточки)."""
    f = font(F_BODY, size)
    lh = int(size * 1.2)
    h = max(ic, len(lines) * lh) + 10
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    im.alpha_composite(icon_from_black(icon, ic), (0, (h - ic) // 2))
    y = (h - len(lines) * lh) / 2
    for line in lines:
        d.text((ic + 28, y), line, font=f, fill=color)
        y += lh
    return _save(_shadow(im, blur=10, k=0.6), path)
