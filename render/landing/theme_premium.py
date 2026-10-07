"""Стиль ролика 5 «Приветствие директора: русский и английский».

Дизайн-система A «Премиальный корпоративный» (борд scratch/img/l5_board_a.png,
выбран 07.10.2026): слоновая кость #F6F1E7, графит #2B2D33, приглушённое золото
#B8935A, глубокое бордо #6E1F2B, тёплый серый #A39E96. Шрифты — Playfair Display
(заголовки, засечки) и Manrope (текст, субтитры).

Язык компонентов — спокойный, «журнальный»: кадр с полями (паспарту) и тонкими
золотыми линиями, уголки-засечки, плашка «имя — должность» с золотой чертой,
чипы языков RU / EN, переключатель языка, без мультяшных стикеров и жёстких
теней. Компоненты рисуют RGBA PNG; монтажный движок — render/landing/build_l3.py
(через build_l4.py).
"""
import os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
F_HEAD = f"{FONTS}/PlayfairDisplay-Bold.ttf"
F_HEAD_S = f"{FONTS}/PlayfairDisplay-SemiBold.ttf"
F_BODY = f"{FONTS}/Manrope-Bold.ttf"
F_BODY_X = f"{FONTS}/Manrope-ExtraBold.ttf"
F_BODY_M = f"{FONTS}/Manrope-Medium.ttf"

IVORY = (246, 241, 231, 255)
PAPER = (251, 248, 242, 255)
GRAPHITE = (43, 45, 51, 255)
GOLD = (184, 147, 90, 255)
GOLD_L = (233, 217, 184, 255)
BORDO = (110, 31, 43, 255)
WGREY = (163, 158, 150, 255)
WHITE = (255, 255, 255, 255)
PAD_COLOR = "0xF6F1E7"   # фон под тряской кадра

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


text_w = tw


def _save(im, path):
    im.save(path)
    return path


def _shadow(im, blur=22, k=0.16, dy=14, pad=40):
    """Мягкая, едва заметная тень (премиально, без «стикерности»)."""
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (60, 45, 30, 255))
    sh.putalpha(im.getchannel("A").point(lambda v: v * k))
    out.alpha_composite(sh, (pad, pad + dy))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def star(d, cx, cy, r, color=GOLD):
    """Четырёхлучевая звезда-«меридиан» (как на борде)."""
    k = r * 0.22
    d.polygon([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
               (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], fill=color)


def ticks(d, x0, y0, x1, y1, L=46, color=GOLD, w=3):
    """Уголки-засечки по углам прямоугольника."""
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(x, y), (x + sx * L, y)], fill=color, width=w)
        d.line([(x, y), (x, y + sy * L)], fill=color, width=w)


# ---------------------------------------------------------------- фоны

def background(path, W, H, variant="ivory"):
    """ivory — слоновая кость с тонкой золотой рамкой-паспарту и уголками;
    frame — то же, но с внутренним «окном» под ведущую (светлее, чем поля);
    bordo — глубокое бордо с золотыми уголками (для переключателя языка);
    map — слоновая кость с картой мира (scratch/img/l5_map.png) в верхней части."""
    m = int(W * 0.055)
    if variant == "bordo":
        im = Image.new("RGBA", (W, H), BORDO)
        d = ImageDraw.Draw(im)
        for i in range(H):   # лёгкий вертикальный градиент
            a = int(28 * i / H)
            d.line([(0, i), (W, i)], fill=(110 - a // 2, 31 - a // 4, 43 - a // 4, 255))
        d.rectangle([m, m, W - m, H - m], outline=GOLD, width=2)
        ticks(d, m - 14, m - 14, W - m + 14, H - m + 14, color=GOLD)
        return _save(im, path)
    im = Image.new("RGBA", (W, H), IVORY)
    d = ImageDraw.Draw(im)
    if variant == "frame":
        d.rectangle([m, m, W - m, H - m], fill=PAPER)
    d.rectangle([m, m, W - m, H - m], outline=GOLD, width=2)
    ticks(d, m - 14, m - 14, W - m + 14, H - m + 14)
    if variant == "map":
        mp = Image.open(os.path.join(os.path.dirname(HERE), "..", "scratch", "img", "l5_map.png")).convert("RGBA")
        mw = W - 2 * m - 40
        mh = int(mp.height * mw / mp.width)
        mp = mp.resize((mw, mh), Image.LANCZOS)
        im.alpha_composite(mp, (m + 20, int(H * 0.08)))
    return _save(im, path)


# ---------------------------------------------------------------- текст

def headline(path, lines, w, size=92, align="left", lh=1.22):
    """Заголовок Playfair Display. Части строки: (текст, стиль): k — графит,
    b — бордо, g — золото, w — слоновая кость, s — графит зачёркнутый бордо."""
    f = font(F_HEAD, size)
    col = {"k": GRAPHITE, "b": BORDO, "g": GOLD, "w": IVORY, "s": WGREY}
    rows = []
    for parts in lines:
        rw = sum(tw(t, f) for t, _ in parts) + tw(" ", f) * (len(parts) - 1)
        rows.append((parts, rw))
    w = max(w, int(max(r for _, r in rows)) + 12)
    asc = tbox("ЁЙАgy", f)
    h = int(size * lh * len(rows) + (asc[3] - asc[1]) * 0.35) + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 0
    for parts, rw in rows:
        x = {"left": 0, "center": (w - rw) / 2, "right": w - rw}[align]
        for t, st in parts:
            d.text((x, y), t, font=f, fill=col[st])
            if st == "s":
                bb = tbox(t, f)
                ym = y + (bb[1] + bb[3]) / 2
                d.line([(x - 6, ym), (x + tw(t, f) + 6, ym)], fill=BORDO, width=max(6, size // 12))
            x += tw(t, f) + tw(" ", f)
        y += size * lh
    return _save(im, path)


def kicker(path, text, color=GOLD, size=34, rule=True):
    """Капитель-подпись Manrope разрядкой + золотая черта слева."""
    f = font(F_BODY_X, size)
    spaced = " ".join(text.upper())
    bb = tbox(spaced, f)
    L = 70 if rule else 0
    w, h = int(tw(spaced, f) + L + 6), bb[3] + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if rule:
        d.line([(0, (bb[1] + bb[3]) // 2), (L - 22, (bb[1] + bb[3]) // 2)], fill=color, width=3)
    d.text((L, 0), spaced, font=f, fill=color)
    return _save(im, path)


def strike_word(path, text, size=78, angle=0):
    """Слово, перечёркнутое бордовой чертой (камера / студия / переводчик)."""
    f = font(F_HEAD_S, size)
    bb = tbox(text, f)
    w, h = int(tw(text, f)) + 40, bb[3] + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((20, 10), text, font=f, fill=WGREY)
    ym = 10 + (bb[1] + bb[3]) / 2
    d.line([(6, ym + 4), (w - 6, ym - 4)], fill=BORDO, width=max(6, size // 11))
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return _save(im, path)


def name_plate(path, name, role, w=720):
    """Плашка «имя — должность»: бумага, бордовая черта слева, золотая линия."""
    fn, fr = font(F_HEAD, 60), font(F_BODY_M, 34)
    h = 190
    w = max(w, int(tw(name, fn)) + 120, int(tw(role, fr)) + 120)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=PAPER)
    d.rectangle([0, 0, 12, h - 1], fill=BORDO)
    d.text((52, 22), name, font=fn, fill=GRAPHITE)
    d.line([(52, 112), (200, 112)], fill=GOLD, width=3)
    d.text((52, 128), role, font=fr, fill=GRAPHITE)
    return _save(_shadow(im), path)


def lang_chip(path, code, active=True, size=58):
    """Чип языка RU / EN: бордо с буквами слоновой кости (активный) или контур."""
    f = font(F_BODY_X, size)
    bb = tbox(code, f)
    w, h = int(tw(code, f) + size * 1.3), int((bb[3] - bb[1]) + size * 0.9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if active:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=BORDO)
        d.text(((w - tw(code, f)) / 2, (h - (bb[3] - bb[1])) / 2 - bb[1]), code, font=f, fill=IVORY)
    else:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=PAPER, outline=GOLD, width=3)
        d.text(((w - tw(code, f)) / 2, (h - (bb[3] - bb[1])) / 2 - bb[1]), code, font=f, fill=GRAPHITE)
    return _save(_shadow(im, k=0.12), path)


def lang_switch(path, state="RU", w=860):
    """Большой переключатель языка: капсула с двумя половинами RU / EN, активная
    половина — бордо, ползунок слоновой кости с золотой звездой."""
    h = int(w * 0.36)
    f = font(F_HEAD, int(h * 0.42))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=PAPER, outline=GOLD, width=4)
    half = w // 2
    left = state == "RU"
    x0 = 10 if left else half
    d.rounded_rectangle([x0, 10, x0 + half - 10, h - 11], radius=(h - 20) // 2, fill=BORDO)
    for code, cx, act in (("RU", half / 2, left), ("EN", half * 1.5, not left)):
        bb = tbox(code, f)
        d.text((cx - tw(code, f) / 2, (h - (bb[3] - bb[1])) / 2 - bb[1]), code, font=f,
               fill=IVORY if act else GRAPHITE)
    star(d, half, h / 2, h * 0.16)
    return _save(_shadow(im), path)


def word_logo(path, text="Меридиан", size=96):
    """Логотип-слово: Playfair графитом + золотая звезда-меридиан слева."""
    f = font(F_HEAD, size)
    bb = tbox(text, f)
    r = int(size * 0.42)
    w, h = int(tw(text, f) + r * 2 + 30), bb[3] + 16
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    star(d, r, (bb[1] + bb[3]) / 2, r)
    d.text((r * 2 + 24, 0), text, font=f, fill=GRAPHITE)
    return _save(im, path)


def note_card(path, kick, lines, w=880, size=58):
    """Карточка-заметка: золотая капитель сверху, текст Playfair, бумага."""
    fk, ft = font(F_BODY_X, 30), font(F_HEAD_S, size)
    lh = int(size * 1.25)
    h = 56 + 46 + lh * len(lines) + 40
    w = max(w, int(max(tw(t, ft) for t in lines)) + 110)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=PAPER, outline=GOLD_L, width=2)
    d.text((54, 44), " ".join(kick.upper()), font=fk, fill=GOLD)
    y = 44 + 56
    for t in lines:
        d.text((54, y), t, font=ft, fill=GRAPHITE)
        y += lh
    ticks(d, 14, 14, w - 15, h - 15, L=30, w=3)
    return _save(_shadow(im), path)


def frame(path, w, h, color=GOLD, wdt=3):
    """Тонкая золотая рамка с уголками (вокруг ведущей или блока)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([12, 12, w - 13, h - 13], outline=color, width=wdt)
    ticks(d, 0, 0, w - 1, h - 1, L=54, color=color, w=wdt + 2)
    return _save(im, path)


def lang_row(path, codes=("RU", "EN", "DE", "中文", "ES"), active=2, size=44):
    """Ряд чипов языков: первые `active` — бордо, остальные — контур."""
    from PIL import ImageFont   # noqa: F401
    chips = []
    for i, c in enumerate(codes):
        p = f"{path}.{i}.png"
        f = F_BODY_X
        if any(ord(ch) > 0x2E80 for ch in c):   # иероглифов в Manrope нет — пишем «ZH»
            c = "ZH"
        lang_chip(p, c, active=i < active, size=size)
        chips.append(Image.open(p))
    gap = -40
    w = sum(c.width for c in chips) + gap * (len(chips) - 1)
    h = max(c.height for c in chips)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for c in chips:
        im.alpha_composite(c, (x, (h - c.height) // 2))
        x += c.width + gap
    return _save(im, path)


def cta_button(path, text="Заказать ролик", w=640, size=48):
    f = font(F_BODY_X, size)
    bb = tbox(text, f)
    w = max(w, int(tw(text, f)) + 150)
    h = int((bb[3] - bb[1]) + size * 1.25)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=BORDO)
    d.rectangle([8, 8, w - 9, h - 9], outline=GOLD, width=2)
    d.text(((w - tw(text, f)) / 2, (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=IVORY)
    return _save(_shadow(im), path)


# ---------------------------------------------------------------- субтитры

CAP_F = 54


def caption_layout(words, w):
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
    if len(lines) == 2 and len(lines[1]) == 1 and len(lines[0]) > 2:
        lines[1].insert(0, lines[0].pop())
    return lines


def caption(path, words, hi, w):
    """Субтитр: плашка цвета бумаги с тонкой золотой рамкой, графитовый
    Manrope; текущее слово — светло-золотая подложка и бордовая черта под ним."""
    f = font(F_BODY, CAP_F)
    lines = caption_layout(words, w)
    lh = 74
    h = 34 + len(lines) * lh + 26
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(251, 248, 242, 246), outline=GOLD, width=2)
    y = 30
    sp = tw(" ", f)
    for line in lines:
        full = sum(tw(words[i], f) for i in line) + sp * (len(line) - 1)
        x = (w - full) / 2
        for i in line:
            bw = tw(words[i], f)
            if i == hi:
                bb = tbox(words[i], f)
                d.rectangle([x - 10, y + bb[1] - 8, x + bw + 10, y + bb[3] + 10], fill=GOLD_L)
                d.line([(x - 10, y + bb[3] + 10), (x + bw + 10, y + bb[3] + 10)], fill=BORDO, width=4)
            d.text((x, y), words[i], font=f, fill=GRAPHITE)
            x += bw + sp
        y += lh
    im.save(path)
    return path


# ---------------------------------------------------------------- переход и вспышки

def swipe(path, W, H):
    """Переход: панель слоновой кости с бордовой и золотой кромкой проезжает кадр."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1 = int(W * 0.18), int(W * 0.82)
    d.rectangle([x0, 0, x1, H], fill=IVORY)
    d.rectangle([x0 - 18, 0, x0, H], fill=BORDO)
    d.rectangle([x1, 0, x1 + 18, H], fill=BORDO)
    d.line([(x0 + 10, 0), (x0 + 10, H)], fill=GOLD, width=4)
    d.line([(x1 - 10, 0), (x1 - 10, H)], fill=GOLD, width=4)
    return _save(im, path)


def flash(path, W, H, color="gold"):
    c = {"gold": (233, 217, 184, 130), "yellow": (233, 217, 184, 130), "white": (255, 255, 255, 170),
         "bordo": (110, 31, 43, 90), "red": (110, 31, 43, 90), "green": (233, 217, 184, 130)}[color]
    Image.new("RGBA", (W, H), c).save(path)
    return path


def city_chip(path, text, size=40):
    """Подпись города на карте: бумажная пилюля с бордовой точкой и золотой обводкой."""
    f = font(F_BODY_X, size)
    bb = tbox(text, f)
    r = int(size * 0.28)
    h = int((bb[3] - bb[1]) + size * 0.9)
    w = int(tw(text, f) + size * 1.1 + r * 2 + 12)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=PAPER, outline=GOLD, width=3)
    cx0 = int(size * 0.55) + r
    d.ellipse([cx0 - r, h / 2 - r, cx0 + r, h / 2 + r], fill=BORDO)
    d.text((cx0 + r + 12, (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=GRAPHITE)
    return _save(_shadow(im, k=0.12), path)
