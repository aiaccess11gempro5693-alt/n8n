"""Стиль «Блокнот» для Instagram Reels ИИАВАТАР №5 «Почему вы не можете бросить сериал»
(борд scratch/img/ig5_board_notepad.png, 27.10.2026): бумага в клетку #FAF6EC, графит
#2B2B2B, красный карандаш #D7263D, жёлтый маркер #FFD447. Заголовки — Unbounded Black,
текст — Montserrat ExtraBold, пометки «от руки» — Caveat Bold. Язык: листки бумаги на
скотче, жёлтый маркер под ключевым словом, обводка красным карандашом, зачёркивание,
открытая петля, которая замыкается в конце.

Только оформление: компонент рисует RGBA PNG и возвращает путь.
Раскладку и тайминги задаёт скрипт ролика (build_ig5.py).
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
F_HEAD = f"{FONTS}/Unbounded-Black.ttf"
F_BODY = f"{FONTS}/Montserrat-ExtraBold.ttf"
F_HAND = f"{FONTS}/Caveat-Bold.ttf"

PAPER = (250, 246, 236, 255)
SHEET = (255, 253, 247, 255)
INK = (43, 43, 43, 255)
RED = (215, 38, 61, 255)
YELLOW = (255, 212, 71, 255)
GREY = (150, 146, 138, 255)
GRID = (120, 140, 160, 38)
TAPE = (255, 236, 160, 190)
WHITE = (255, 255, 255, 255)
PAD_COLOR = "0xFAF6EC"
PROGRESS_COLOR = "0xD7263D"
CAP_F = 58
CPAD = 34          # отступ вокруг слова, обведённого карандашом

_fc = {}


def font(path, size):
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def tw(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(text, font=f)


def tbox(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textbbox((0, 0), text, font=f)


def _shadow(im, blur=14, k=0.28, dy=8, pad=30):
    """Мягкая тень листка на бумаге."""
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (60, 50, 30, 255))
    sh.putalpha(im.getchannel("A").point(lambda v: v * k))
    out.alpha_composite(sh, (pad, pad + dy))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def _save(im, path):
    im.save(path)
    return path


def _wobble(pts, rnd, amp=2.5):
    return [(x + rnd.uniform(-amp, amp), y + rnd.uniform(-amp, amp)) for x, y in pts]


def _pencil_line(d, a, b, color=RED, width=7, seed=1, passes=2):
    """Линия «карандашом»: два чуть разных прохода."""
    rnd = random.Random(seed)
    for k in range(passes):
        n = 12
        pts = [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
        d.line(_wobble(pts, rnd, 2.0 + k), fill=color[:3] + (230 - 60 * k,), width=width - 2 * k, joint="curve")


def _marker(d, box, seed=1, color=YELLOW):
    """Мазок жёлтого маркера под словом — неровные края."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    top = [(x0 + (x1 - x0) * i / 10, y0 + rnd.uniform(-5, 5)) for i in range(11)]
    bot = [(x1 - (x1 - x0) * i / 10, y1 + rnd.uniform(-5, 5)) for i in range(11)]
    d.polygon(top + bot, fill=color[:3] + (235,))


def _tape(im, cx, cy, w=150, h=46, angle=-8):
    t = Image.new("RGBA", (w, h), TAPE)
    td = ImageDraw.Draw(t)
    for x in range(0, w, 9):
        td.line([(x, 0), (x, h)], fill=(255, 255, 255, 30), width=2)
    t = t.rotate(angle, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))


def _sheet(w, h, tape=True, seed=3):
    """Листок бумаги (чуть светлее фона) в клетку, со скотчем сверху."""
    im = Image.new("RGBA", (w, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 30, w - 1, h + 29], radius=10, fill=SHEET, outline=(225, 218, 200, 255), width=2)
    for x in range(40, w, 44):
        d.line([(x, 34), (x, h + 25)], fill=GRID, width=1)
    for y in range(74, h + 26, 44):
        d.line([(4, y), (w - 5, y)], fill=GRID, width=1)
    if tape:
        rnd = random.Random(seed)
        _tape(im, w * 0.5 + rnd.uniform(-60, 60), 34, angle=rnd.uniform(-9, 9))
    return im


# ---------------------------------------------------------------- фон

def background(path, W, H, variant="plain"):
    """Бумага в клетку; grid — с красной линией поля слева и тенью-виньеткой."""
    im = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=GRID, width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=GRID, width=2)
    if variant == "grid":
        d.line([(92, 0), (92, H)], fill=(215, 38, 61, 90), width=3)
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    vd.rectangle([0, 0, W, H], outline=(120, 100, 60, 50), width=90)
    im.alpha_composite(vig.filter(ImageFilter.GaussianBlur(80)))
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
        m = ImageChops.multiply(m, s)
    m.save(path)
    return path


def circle_mask(path, size):
    m = Image.new("L", (size * 2, size * 2), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 2 - 1, size * 2 - 1], fill=255)
    m.resize((size, size), Image.LANCZOS).save(path)
    return path


def ring(path, size, width=10):
    """Обводка круглого кадра ведущей красным карандашом в два прохода."""
    s = size + 2 * width + 8
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    c, r = s / 2, s / 2 - width
    for k in range(2):
        pts = []
        for i in range(0, 371, 4):
            a = math.radians(i - 100)
            rr = r - k * 5 + rnd.uniform(-2.5, 2.5)
            pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
        d.line(pts, fill=RED[:3] + (240 - 70 * k,), width=width - 3 * k, joint="curve")
    return _save(im, path)


# ---------------------------------------------------------------- типографика

def headline(path, lines, w, size=96, align="center", lh=1.22):
    """Заголовок Unbounded Black капслоком. Строка — список кусков (текст, режим):
    'w' графит, 'o' красный, 'box' графит на жёлтом маркере, 'c' обведено красным
    карандашом, 'g' серый, 's' зачёркнуто красным."""
    def widest(sz):
        ff = font(F_HEAD, sz)
        return max(sum(tw(t.upper(), ff) + (CPAD * 2 if m == "c" else 0) for t, m in ln)
                   + tw(" ", ff) * (len(ln) - 1) for ln in lines)
    while size > 40 and widest(size) > w - 60:   # широкий Unbounded — ужимаем под ширину
        size -= 2
    f = font(F_HEAD, size)
    step = int(size * lh)
    pad = 34
    h = len(lines) * step + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = pad
    sp = tw(" ", f)
    for li, line in enumerate(lines):
        segs = [(t.upper(), m) for t, m in line]
        full = sum(tw(t, f) + (CPAD * 2 if m == "c" else 0) for t, m in segs) + sp * (len(segs) - 1)
        if full > w - 20:
            raise ValueError(f"headline: строка «{' '.join(t for t, _ in segs)}» шире {w}")
        x = (w - full) / 2 if align == "center" else 0
        for si, (t, m) in enumerate(segs):
            bw = tw(t, f)
            bb = tbox(t, f)
            if m == "c":
                x += CPAD
            if m == "box":
                _marker(d, (x - 14, y + bb[1] - 4, x + bw + 14, y + bb[3] + 8), seed=li * 7 + si)
            d.text((x, y), t, font=f, fill={"w": INK, "o": RED, "box": INK, "c": INK, "g": GREY, "s": GREY}[m])
            if m == "c":
                _ellipse(d, (x - 26, y + bb[1] - 18, x + bw + 26, y + bb[3] + 18), seed=li + si)
            if m == "s":
                ym = y + (bb[1] + bb[3]) / 2
                _pencil_line(d, (x - 10, ym + 6), (x + bw + 10, ym - 6), width=10, seed=li + si)
            x += bw + sp + (CPAD if m == "c" else 0)
        y += step
    return _save(im, path)


def _ellipse(d, box, seed=1, color=RED, width=7):
    """Овал «от руки» — незамкнутый, с нахлёстом."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    pts = []
    for i in range(0, 390, 6):
        a = math.radians(i + 200)
        k = 1 + rnd.uniform(-0.02, 0.02) + 0.04 * (i > 360)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    d.line(pts, fill=color, width=width, joint="curve")


def note(path, text, size=74, color=RED, angle=-4, arrow=None):
    """Пометка от руки (Caveat) красным карандашом; arrow — 'left'/'right'/'down'."""
    f = font(F_HAND, size)
    bb = tbox(text, f)
    w, h = int(bb[2] - bb[0] + 40), int(bb[3] - bb[1] + 40)
    aw = 120 if arrow in ("left", "right") else 0
    ah = 110 if arrow == "down" else 0
    im = Image.new("RGBA", (w + aw, h + ah), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tx = 20 - bb[0] + (aw if arrow == "left" else 0)
    d.text((tx, 20 - bb[1]), text, font=f, fill=color)
    if arrow == "right":
        a, b = (w - 10, h / 2), (w + aw - 14, h / 2 + 10)
    elif arrow == "left":
        a, b = (aw + 10, h / 2), (14, h / 2 + 10)
    elif arrow == "down":
        a, b = (w / 2, h - 6), (w / 2 + 14, h + ah - 10)
    if arrow:
        _pencil_line(d, a, b, color=color, width=6, seed=3, passes=1)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (2.6, -2.6):
            d.line([b, (b[0] + 34 * math.cos(ang + s), b[1] + 34 * math.sin(ang + s))], fill=color, width=6)
    im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(im, path)


def tag(path, text, size=48):
    """Метка: графит на жёлтом маркере."""
    f = font(F_HEAD, size)
    bb = tbox(text.upper(), f)
    w, h = int(bb[2] - bb[0] + 60), int(bb[3] - bb[1] + 44)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _marker(d, (6, 8, w - 6, h - 8), seed=len(text))
    d.text((30 - bb[0], 22 - bb[1]), text.upper(), font=f, fill=INK)
    return _save(im, path)


def cta_card(path, w=1000, word="ПЕТЛЯ", k=1.0):
    """Листок «НАПИШИТЕ «СЛОВО» В ДИРЕКТ» на скотче + @iiavatar.video; k — масштаб шрифта."""
    f1, f2 = font(F_HEAD, int(96 * k)), font(F_HAND, int(74 * k))
    step = int(132 * k)
    lines = (("НАПИШИТЕ", "w"), (f"«{word}»", "box"), ("В ДИРЕКТ", "w"))
    h = int(50 * k) + len(lines) * step + int(100 * k)
    im = _sheet(w, h, seed=9)
    d = ImageDraw.Draw(im)
    y = 30 + int(50 * k)
    for t, m in lines:
        bb = tbox(t, f1)
        x = (w - (bb[2] - bb[0])) / 2 - bb[0]
        if m == "box":
            _marker(d, (x + bb[0] - 22, y + bb[1] - 10, x + bb[2] + 22, y + bb[3] + 14), seed=11)
        d.text((x, y), t, font=f1, fill=INK)
        y += step
    h2 = "@iiavatar.video"
    bb = tbox(h2, f2)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], y), h2, font=f2, fill=RED)
    return _save(_shadow(im.rotate(-1.2, resample=Image.BICUBIC, expand=True)), path)


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
    """Субтитр: белая полоска бумаги, графитовый текст; слово hi — на жёлтом маркере."""
    f = font(F_BODY, CAP_F)
    lines = caption_layout(words, w)
    lh = 78
    h = 34 + len(lines) * lh + 28
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=(255, 255, 255, 240), outline=(43, 43, 43, 60),
                        width=3)
    y = 32
    sp = tw(" ", f)
    for line in lines:
        full = sum(tw(words[i], f) for i in line) + sp * (len(line) - 1)
        x = (w - full) / 2
        for i in line:
            bw = tw(words[i], f)
            if i == hi:
                bb = tbox(words[i], f)
                _marker(d, (x - 10, y + bb[1] - 8, x + bw + 10, y + bb[3] + 10), seed=i)
            d.text((x, y), words[i], font=f, fill=INK)
            x += bw + sp
        y += lh
    im.save(path)
    return path


def caption_height(words, w):
    return 34 + len(caption_layout(words, w)) * 78 + 28


# ---------------------------------------------------------------- эффекты

def swipe(path, W, H):
    """Переход: широкий мазок жёлтого маркера по диагонали."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(W * 0.15, 0), (W * 0.85, 0), (W * 0.55, H), (-W * 0.15, H)], fill=YELLOW)
    im.save(path)
    return path


def scanlines(path, W, H):
    """Кадр раскрытия «я нейросеть»: сбой — полосы и смещённые клетки."""
    rnd = random.Random(7)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 6):
        d.line([(0, y), (W, y)], fill=(43, 43, 43, 50), width=2)
    for _ in range(14):
        y = rnd.uniform(0, H)
        hh = rnd.uniform(6, 40)
        col = rnd.choice([(215, 38, 61, 110), (255, 212, 71, 120), (43, 43, 43, 80)])
        d.rectangle([0, y, W, y + hh], fill=col)
    im.save(path)
    return path


def flash(path, W, H, color="orange"):
    c = {"orange": (255, 212, 71, 120), "white": (255, 255, 255, 160), "red": (215, 38, 61, 90)}[color]
    Image.new("RGBA", (W, H), c).save(path)
    return path


# ---------------------------------------------------------------- компоненты ролика

def player(path, state, w=1000, h=600):
    """Плеер серии: тёмный экран, красный прогресс-бар. state 0 — идёт серия
    (прогресс ~62%), 1 — серия оборвалась: «Следующая серия через 5…»."""
    im = _sheet(w, h, seed=21)
    d = ImageDraw.Draw(im)
    sx0, sy0, sx1, sy1 = 40, 80, w - 40, h - 20
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=18, fill=(28, 28, 30, 255))
    by = sy1 - 70
    d.rounded_rectangle([sx0 + 40, by, sx1 - 40, by + 14], radius=7, fill=(90, 90, 94, 255))
    px = sx0 + 40 + (sx1 - sx0 - 80) * (0.62 if state == 0 else 0.98)
    d.rounded_rectangle([sx0 + 40, by, px, by + 14], radius=7, fill=RED)
    d.ellipse([px - 16, by - 9, px + 16, by + 23], fill=RED)
    fh = font(F_HEAD, 64)
    if state == 0:
        cx, cy = (sx0 + sx1) / 2, (sy0 + by) / 2
        d.polygon([(cx - 40, cy - 56), (cx - 40, cy + 56), (cx + 60, cy)], fill=(255, 255, 255, 230))
    else:
        f2, f3 = font(F_BODY, 46), font(F_HEAD, 150)
        t1 = "Следующая серия через"
        b1 = tbox(t1, f2)
        d.text(((w - (b1[2] - b1[0])) / 2 - b1[0], sy0 + 70 - b1[1]), t1, font=f2, fill=(230, 230, 230, 255))
        b2 = tbox("5", f3)
        d.text(((w - (b2[2] - b2[0])) / 2 - b2[0], sy0 + 150 - b2[1]), "5", font=f3, fill=RED)
    del fh
    return _save(_shadow(im.rotate(1.0, resample=Image.BICUBIC, expand=True)), path)


def order_pad(path, state, w=760):
    """Блокнот официанта: 4 заказа. state 0 — все записаны; 1 — два оплачены
    (зачёркнуты); 2 — оплаченные исчезли, остались только неоплаченные."""
    items = ["Кофе", "Штрудель", "Чай", "Омлет"]
    paid = {0, 2}
    f, fh = font(F_HAND, 92), font(F_HAND, 70)
    row = 112
    h = 150 + len(items) * row + 40
    im = _sheet(w, h, seed=31)
    d = ImageDraw.Draw(im)
    d.text((60, 52), "Столик 7", font=fh, fill=GREY)
    y = 160
    for i, t in enumerate(items):
        if state == 2 and i in paid:
            d.line([(60, y + 70), (w - 60, y + 70)], fill=GRID, width=2)
            y += row
            continue
        d.text((70, y), f"— {t}", font=f, fill=INK)
        if state >= 1 and i in paid:
            bb = tbox(f"— {t}", f)
            _pencil_line(d, (60, y + 64), (90 + bb[2], y + 50), width=9, seed=i)
            d.text((w - 230, y + 14), "оплачено", font=font(F_HAND, 54), fill=RED)
        y += row
    return _save(_shadow(im.rotate(-2.0, resample=Image.BICUBIC, expand=True)), path)


def bars_card(path, state, w=1000):
    """Сравнение памяти: законченные (короткий серый столбец) и незаконченные
    (красный, почти вдвое длиннее). state 0 — только законченные, 1 — оба + «почти ×2»."""
    h = 560
    im = _sheet(w, h, seed=41)
    d = ImageDraw.Draw(im)
    ft, fl, fx = font(F_HEAD, 52), font(F_BODY, 44), font(F_HAND, 110)
    t = "ЧТО ПОМНЯТ"
    bb = tbox(t, ft)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], 76 - bb[1]), t, font=ft, fill=INK)
    x0, maxw = 60, w - 300
    rows = [("Законченные дела", 0.5, GREY), ("Незаконченные", 0.95, RED)]
    y = 200
    for i, (lab, k, col) in enumerate(rows):
        d.text((x0, y), lab, font=fl, fill=INK)
        if i == 1 and state == 0:
            d.rounded_rectangle([x0, y + 64, x0 + maxw * k, y + 134], radius=14, outline=GREY, width=3)
        else:
            d.rounded_rectangle([x0, y + 64, x0 + maxw * k, y + 134], radius=14, fill=col)
        y += 170
    if state == 1:
        d.text((x0 + maxw * 0.95 + 24, 340), "×2", font=fx, fill=RED)
    return _save(_shadow(im.rotate(1.2, resample=Image.BICUBIC, expand=True)), path)


def loop_icon(path, closed=False, size=420, label=None):
    """Открытая петля красным карандашом (незамкнутый круг со стрелкой);
    closed — круг замкнут и внутри галочка."""
    lab_h = 110 if label else 0
    fl = font(F_HAND, 84)
    W_ = max(size, int(tw(label, fl)) + 40) if label else size
    im = Image.new("RGBA", (W_, size + lab_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = size / 2 - 30
    c = size / 2
    ox = (W_ - size) / 2
    end = 360 if closed else 300
    rnd = random.Random(2)
    for k in range(2):
        pts = [(ox + c + (r - 4 * k) * math.cos(math.radians(a - 90)) + rnd.uniform(-1.5, 1.5),
                c + (r - 4 * k) * math.sin(math.radians(a - 90)) + rnd.uniform(-1.5, 1.5))
               for a in range(0, end + 1, 4)]
        d.line(pts, fill=RED[:3] + (240 - 70 * k,), width=16 - 5 * k, joint="curve")
    if closed:
        d.line([(ox + c - 80, c), (ox + c - 20, c + 64), (ox + c + 92, c - 70)], fill=RED, width=20, joint="curve")
    else:
        a = math.radians(end - 90)
        tip = (ox + c + r * math.cos(a), c + r * math.sin(a))
        tang = a + math.pi / 2
        for s in (2.5, -2.5):
            d.line([tip, (tip[0] + 54 * math.cos(tang + math.pi + s * 0.3 * (1 if s > 0 else 1)),
                          tip[1] + 54 * math.sin(tang + math.pi + s * 0.3))], fill=RED, width=14)
    if label:
        bb = tbox(label, fl)
        d.text(((W_ - (bb[2] - bb[0])) / 2 - bb[0], size + 6 - bb[1]), label, font=fl, fill=INK)
    return _save(im, path)


def timer_card(path, w=760):
    """Таймер «5 минут» — листок с циферблатом и красным сектором."""
    h = 520
    im = _sheet(w, h, seed=51)
    d = ImageDraw.Draw(im)
    cx, cy, r = 200, 30 + h / 2 + 10, 170
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=10)
    d.pieslice([cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18], -90, -60, fill=RED)
    d.line([(cx, cy), (cx, cy - r + 40)], fill=INK, width=10)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=INK)
    f1, f2 = font(F_HEAD, 120), font(F_HAND, 76)
    d.text((410, cy - 150), "5", font=f1, fill=RED)
    d.text((410, cy - 10), "минут —", font=f2, fill=INK)
    d.text((410, cy + 70), "и вы в деле", font=f2, fill=INK)
    return _save(_shadow(im.rotate(-1.5, resample=Image.BICUBIC, expand=True)), path)


def photo_card(path, src, w=980, h=None, caption=None, angle=1.5):
    """Скетч-иллюстрация как вклеенный листок: белая рамка, скотч сверху;
    caption — пометка от руки на жёлтом маркере снизу."""
    ph = Image.open(src).convert("RGBA")
    h = h or int(w * ph.height / ph.width)
    k = max(w / ph.width, h / ph.height)
    ph = ph.resize((int(ph.width * k) + 1, int(ph.height * k) + 1), Image.LANCZOS)
    ph = ph.crop(((ph.width - w) // 2, (ph.height - h) // 2, (ph.width - w) // 2 + w, (ph.height - h) // 2 + h))
    b = 22
    im = Image.new("RGBA", (w + 2 * b, h + 2 * b + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 30, w + 2 * b - 1, h + 2 * b + 29], fill=SHEET, outline=(225, 218, 200, 255), width=2)
    im.alpha_composite(ph, (b, 30 + b))
    _tape(im, (w + 2 * b) * 0.3, 40, angle=-10)
    _tape(im, (w + 2 * b) * 0.72, 40, angle=8)
    if caption:
        fc = font(F_HAND, 84)
        bb = tbox(caption, fc)
        cw, ch = bb[2] - bb[0] + 60, bb[3] - bb[1] + 36
        x0, y0 = (im.width - cw) / 2, im.height - ch - 40
        _marker(d, (x0, y0, x0 + cw, y0 + ch), seed=len(caption))
        d.text((x0 + 30 - bb[0], y0 + 18 - bb[1]), caption, font=fc, fill=INK)
    return _save(_shadow(im.rotate(angle, resample=Image.BICUBIC, expand=True)), path)
