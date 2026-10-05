"""Стиль «Графит и красный» (борд scratch/img/l1c_board_graphite.png, выбран
05.10.2026): графит #22252B, сигнальный красный #E63B2E, молочно-белый #F2F0EB,
сталь #9AA3AE, чёрный #101114. Заголовки — Oswald Bold (узкий, капслок),
текст — Inter. Строгий журнальный вид: красные диагонали, тонкие линии,
крупные красные цифры, чек-листы с квадратными галочками.

Только оформление: каждый компонент рисует RGBA PNG и возвращает путь.
Раскладку кадров и тайминги задаёт скрипт ролика (build_l1_v3.py).
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
F_HEAD = f"{FONTS}/Oswald-Bold.ttf"
F_HEAD_M = f"{FONTS}/Oswald-Medium.ttf"
F_BODY = f"{FONTS}/Inter-SemiBold.otf"
F_BODY_B = f"{FONTS}/Inter-Bold.otf"

GRAPHITE = (34, 37, 43, 255)
RED = (230, 59, 46, 255)
MILK = (242, 240, 235, 255)
STEEL = (154, 163, 174, 255)
BLACK = (16, 17, 20, 255)
WHITE = (255, 255, 255, 255)

_fc = {}


def font(path, size):
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def tw(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(text, font=f)


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


# ---------------------------------------------------------------- фоны

def background(path, W, H, variant="diag"):
    """Графитовый фон. diag — красные диагонали справа (как на фото Анны),
    split — тёмная правая половина под ведущую, plain — без декора."""
    im = Image.new("RGBA", (W, H), GRAPHITE)
    d = ImageDraw.Draw(im)
    # тонкие вертикальные панели, как стена студии
    for x in range(0, W, 216):
        d.line([(x, 0), (x, H)], fill=(40, 43, 50, 255), width=3)
    if variant == "diag":
        d.polygon([(W * 0.62, H * 0.62), (W * 1.05, H * 0.36), (W * 1.05, H * 0.50), (W * 0.62, H * 0.76)], fill=RED)
        d.polygon([(-20, H * 0.98), (W * 0.42, H * 0.70), (W * 0.42, H * 0.78), (-20, H * 1.06)], fill=RED)
    elif variant == "type":
        d.polygon([(0, H * 0.70), (W, H * 0.46), (W, H * 0.53), (0, H * 0.77)], fill=RED)
        for i in range(6):
            for j in range(4):
                d.rectangle([60 + i * 22, 120 + j * 22, 66 + i * 22, 126 + j * 22], fill=STEEL)
    elif variant == "split":
        d.polygon([(W * 0.45, 0), (W, 0), (W, H), (W * 0.43, H)], fill=(26, 28, 33, 255))
        d.polygon([(W * 0.42, 0), (W * 0.45, 0), (W * 0.43, H), (W * 0.40, H)], fill=RED)
    im.save(path)
    return path


def circle_mask(path, size):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
    m.save(path)
    return path


def circle_ring(path, size, ring=12):
    im = Image.new("RGBA", (size + 2 * ring, size + 2 * ring), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, size + 2 * ring - 1, size + 2 * ring - 1], outline=RED, width=ring)
    im.save(path)
    return path


# ---------------------------------------------------------------- элементы

def headline(path, lines, w, size=110, red_words=(), kicker=None):
    """Крупный заголовок Oswald капслоком; слова из red_words — красные.
    lines — уже разбитые строки (заголовок — дизайн, перенос задаём сами)."""
    f, fk = font(F_HEAD, size), font(F_BODY_B, 34)
    lh = int(size * 1.08)
    top = 64 if kicker else 0
    h = top + len(lines) * lh + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kicker:
        kw = tw(kicker.upper(), fk) + 36
        d.rectangle([0, 0, kw, 50], fill=RED)
        d.text((18, 6), kicker.upper(), font=fk, fill=WHITE)
    y = top
    reds = {r.upper() for r in red_words}
    for line in lines:
        x = 0
        for word in line.upper().split():
            col = RED if word.strip(",.—") in reds else WHITE
            d.text((x, y), word, font=f, fill=col)
            x += tw(word + " ", f)
        y += lh
    # лёгкая тень для читаемости поверх фото
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: v * 0.55))
    out = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    out.alpha_composite(sh, (10, 14))
    out.alpha_composite(im, (0, 0))
    out.save(path)
    return path


def big_number(path, num, title, sub, w):
    """Типографика на весь экран: огромная красная цифра + подпись."""
    fn, ft, fs = font(F_HEAD, 560), font(F_HEAD, 128), font(F_BODY, 44)
    h = 1180
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text(((w - tw(num, fn)) / 2, -60), num, font=fn, fill=RED)
    y = 640
    for line in title:
        d.text(((w - tw(line, ft)) / 2, y), line, font=ft, fill=WHITE)
        y += 138
    d.rectangle([(w - 120) / 2, y + 20, (w + 120) / 2, y + 28], fill=RED)
    d.text(((w - tw(sub, fs)) / 2, y + 56), sub, font=fs, fill=STEEL)
    im.save(path)
    return path


def step_card(path, num, title, desc, w, icon=None):
    """Карточка шага: молочная, красная метка «ШАГ N», заголовок Oswald."""
    fk, ft, fd = font(F_BODY_B, 30), font(F_HEAD, 84), font(F_BODY, 38)
    t_lines = wrap(title.upper(), ft, w - 100 - (150 if icon else 0))
    d_lines = wrap(desc, fd, w - 100 - (150 if icon else 0))
    h = 50 + 52 + 20 + len(t_lines) * 92 + 16 + len(d_lines) * 50 + 50
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=MILK)
    d.polygon([(w - 140, 0), (w, 0), (w, 140)], fill=RED)
    x, y = 50, 50
    label = f"ШАГ {num}"
    d.rectangle([x, y, x + tw(label, fk) + 32, y + 52], fill=RED)
    d.text((x + 16, y + 8), label, font=fk, fill=WHITE)
    y += 72
    for line in t_lines:
        d.text((x, y), line, font=ft, fill=BLACK)
        y += 92
    y += 16
    for line in d_lines:
        d.text((x, y), line, font=fd, fill=GRAPHITE)
        y += 50
    if icon:
        ic = Image.open(icon).convert("RGBA").resize((130, 130))
        im.alpha_composite(ic, (w - 180, h - 180))
    im.save(path)
    return path


def note(path, kicker, text, w):
    """Плашка-подсказка: красная полоса слева, графит, белый текст."""
    fk, ft = font(F_BODY_B, 30), font(F_HEAD_M, 60)
    lines = wrap(text.upper(), ft, w - 90)
    h = 40 + 44 + len(lines) * 70 + 34
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=BLACK)
    d.rectangle([0, 0, 14, h], fill=RED)
    x, y = 50, 36
    d.text((x, y), kicker.upper(), font=fk, fill=RED)
    y += 48
    for line in lines:
        d.text((x, y), line, font=ft, fill=WHITE)
        y += 70
    im.save(path)
    return path


def check_row(path, text, w, done=True):
    """Строка чек-листа: квадрат с красной галочкой + текст Oswald."""
    ft = font(F_HEAD_M, 70)
    h = 110
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 18, 74, 92], outline=RED, width=6)
    if done:
        d.line([(14, 54), (32, 74), (64, 30)], fill=RED, width=10)
    d.text((104, 8), text.upper(), font=ft, fill=WHITE)
    im.save(path)
    return path


def panel_title(path, num, title, w):
    fk, ft = font(F_BODY_B, 30), font(F_HEAD, 72)
    lines = wrap(title.upper(), ft, w)
    h = 64 + len(lines) * 104 + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    label = f"ШАГ {num}"
    d.rectangle([0, 0, tw(label, fk) + 32, 50], fill=RED)
    d.text((16, 6), label, font=fk, fill=WHITE)
    y = 64
    for line in lines:
        d.text((0, y), line, font=ft, fill=WHITE)
        y += 104
    im.save(path)
    return path


def statement(path, top, bottom, w):
    """Финал: «СЕГОДНЯ — …» белым, «ЗАВТРА — …» на красной плашке."""
    fk, ft = font(F_BODY_B, 32), font(F_HEAD, 92)
    t1, t2 = wrap(top.upper(), ft, w - 80), wrap(bottom.upper(), ft, w - 80)
    h1 = 30 + 44 + len(t1) * 100 + 20
    h2 = 30 + 44 + len(t2) * 100 + 30
    im = Image.new("RGBA", (w, h1 + h2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h1], fill=BLACK)
    d.rectangle([0, h1, w, h1 + h2], fill=RED)
    y = 30
    d.text((40, y), "СЕГОДНЯ", font=fk, fill=RED)
    y += 46
    for line in t1:
        d.text((40, y), line, font=ft, fill=WHITE)
        y += 100
    y = h1 + 30
    d.text((40, y), "ЗАВТРА", font=fk, fill=BLACK)
    y += 46
    for line in t2:
        d.text((40, y), line, font=ft, fill=WHITE)
        y += 100
    im.save(path)
    return path


def slash(path, W, H):
    """Красная диагональная полоса для перехода между раскладками."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(W * 0.25, 0), (W * 0.75, 0), (W * 0.5, H), (0, H)], fill=RED)
    im.save(path)
    return path


def caption(path, lines, w):
    """Субтитр: чёрная плашка, красная полоса слева, белый Inter Bold."""
    f = font(F_BODY_B, 46)
    lh = 60
    h = 34 + len(lines) * lh + 26
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(16, 17, 20, 235))
    d.rectangle([0, 0, 10, h], fill=RED)
    y = 30
    for line in lines:
        d.text(((w - tw(line, f)) / 2 + 5, y), line, font=f, fill=WHITE)
        y += lh
    im.save(path)
    return path


# ---------------------------------------------------------------- 16:9 (виток 3)

def photo_bg(path, photo, W, H, rect=None, dark=0.35, fade_side=None, ax=0.5):
    """Фон-кадр: графит + фото (cover-кроп) в прямоугольнике rect (x, y, w, h),
    затемнённое на dark; fade_side='right'|'left' — фото уходит в графит."""
    im = Image.open(background(path, W, H, "plain")).convert("RGBA")
    x, y, w, h = rect or (0, 0, W, H)
    ph = Image.open(photo).convert("RGB")
    k = max(w / ph.width, h / ph.height)
    ph = ph.resize((round(ph.width * k), round(ph.height * k)), Image.LANCZOS)
    ox = int((ph.width - w) * ax)
    ph = ph.crop((ox, (ph.height - h) // 2, ox + w, (ph.height - h) // 2 + h))
    ph = Image.blend(ph, Image.new("RGB", ph.size, GRAPHITE[:3]), dark).convert("RGBA")
    if fade_side:
        a = Image.new("L", (w, h), 255)
        d = ImageDraw.Draw(a)
        band = int(w * 0.35)
        for i in range(band):
            v = int(255 * i / band)
            xx = w - band + i if fade_side == "right" else band - i
            d.line([(xx, 0), (xx, h)], fill=255 - v)
        ph.putalpha(a)
    im.alpha_composite(ph, (x, y))
    im.save(path)
    return path


def strike_word(path, text, w_max=900, size=120):
    """Слово капслоком сталью, перечёркнутое красной полосой («скандал»)."""
    f = font(F_HEAD, size)
    t = text.upper()
    l, tt, r, b = f.getbbox(t)
    w, h = r - l + 40, b - tt + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((20 - l, 20 - tt), t, font=f, fill=STEEL)
    d.polygon([(0, h * 0.50), (w, h * 0.38), (w, h * 0.50), (0, h * 0.62)], fill=RED)
    im.save(path)
    return path


def roadmap(path, items, w, title=None):
    """Оглавление: строки «01  Разговор» с красными номерами, тонкие разделители."""
    fn, ft, fk = font(F_HEAD, 64), font(F_HEAD_M, 64), font(F_BODY_B, 32)
    top = 76 if title else 0
    rh = 104
    h = top + len(items) * rh + 6
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if title:
        d.rectangle([0, 0, tw(title.upper(), fk) + 36, 52], fill=RED)
        d.text((18, 7), title.upper(), font=fk, fill=WHITE)
    y = top
    for i, it in enumerate(items):
        d.text((0, y + 8), f"{i + 1:02d}", font=fn, fill=RED)
        d.text((130, y + 8), it.upper(), font=ft, fill=WHITE)
        d.line([(0, y + rh - 2), (w, y + rh - 2)], fill=(70, 74, 82, 255), width=2)
        y += rh
    im.save(path)
    return path


def nameplate(path, name, role):
    """Плашка «имя — должность»: красный блок с именем + чёрный с должностью."""
    fn, fr = font(F_HEAD, 58), font(F_BODY, 34)
    w1, w2 = int(tw(name.upper(), fn)) + 60, int(tw(role, fr)) + 60
    h = 90
    im = Image.new("RGBA", (w1 + w2, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w1, h], fill=RED)
    d.text((30, 6), name.upper(), font=fn, fill=WHITE)
    d.rectangle([w1, 0, w1 + w2, h], fill=BLACK)
    d.text((w1 + 30, 24), role, font=fr, fill=MILK)
    im.save(path)
    return path


def step_label(path, num, title):
    """«02 ОСМОТР»: огромный красный номер + слово Oswald."""
    fn, ft = font(F_HEAD, 150), font(F_HEAD, 96)
    w = int(tw(f"{num:02d}", fn) + 30 + tw(title.upper(), ft)) + 20
    h = 190
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, -10), f"{num:02d}", font=fn, fill=RED)
    d.text((tw(f"{num:02d}", fn) + 30, 46), title.upper(), font=ft, fill=WHITE)
    im.save(path)
    return path


def _icon_circle(src, size):
    """Иконку gpt-image (белая линия в красном круге на графите) — вырезать круг."""
    ic = Image.open(src).convert("RGB")
    px = ic.load()
    xs, ys = [], []
    for y in range(0, ic.height, 4):
        for x in range(0, ic.width, 4):
            r, g, b = px[x, y]
            if r > 170 and g < 110 and b < 100:
                xs.append(x)
                ys.append(y)
    box = (min(xs), min(ys), max(xs), max(ys))
    ic = ic.crop(box).resize((size, size), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([6, 6, size * 4 - 7, size * 4 - 7], fill=255)
    ic.putalpha(m.resize((size, size), Image.LANCZOS))
    return ic


def icon_tile(path, icon, label, w=270, size=210):
    """Плитка: иконка в красном круге + подпись капслоком под ней."""
    ft = font(F_HEAD_M, 46)
    lines = wrap(label.upper(), ft, w - 20)
    h = size + 24 + len(lines) * 54
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.alpha_composite(_icon_circle(icon, size), ((w - size) // 2, 0))
    d = ImageDraw.Draw(im)
    y = size + 24
    for line in lines:
        d.text(((w - tw(line, ft)) / 2, y), line, font=ft, fill=WHITE)
        y += 54
    im.save(path)
    return path


def big_days(path, num, unit, sub):
    """«14 дней с покупки»: крупная красная цифра + подпись."""
    fn, fu, fs = font(F_HEAD, 220), font(F_HEAD, 90), font(F_BODY, 40)
    wn = tw(num, fn)
    w = int(wn + 30 + max(tw(unit.upper(), fu), tw(sub, fs))) + 10
    h = 250
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, -30), num, font=fn, fill=RED)
    d.text((wn + 30, 40), unit.upper(), font=fu, fill=WHITE)
    d.text((wn + 32, 160), sub, font=fs, fill=STEEL)
    im.save(path)
    return path


def form_card(path, title, rows, w, filled):
    """Бланк заявления: молочный лист, поля; filled — сколько полей заполнено
    (рисуем по картинке на каждое состояние и меняем их по таймингу)."""
    fk, ft, fr, fv = font(F_BODY_B, 30), font(F_HEAD, 64), font(F_HEAD_M, 50), font(F_BODY, 34)
    h = 140 + len(rows) * 120 + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=MILK)
    d.rectangle([0, 0, w, 14], fill=RED)
    d.text((50, 46), title.upper(), font=ft, fill=BLACK)
    y = 150
    for i, (label, value) in enumerate(rows):
        done = i < filled
        d.rectangle([50, y + 10, 104, y + 64], outline=RED if done else STEEL, width=5)
        if done:
            d.line([(60, y + 36), (74, y + 52), (98, y + 18)], fill=RED, width=8)
        d.text((130, y + 4), label.upper(), font=fr, fill=BLACK if done else (120, 124, 132, 255))
        lx = 130 + tw(label.upper(), fr) + 30
        d.line([(lx, y + 60), (w - 50, y + 60)], fill=STEEL, width=3)
        if done and value:
            d.text((lx + 10, y + 18), value, font=fv, fill=GRAPHITE)
        y += 120
    im.save(path)
    return path


def pay_card(path, icon, top, bottom, w=440):
    """Карточка способа оплаты: иконка, «КАРТОЙ», красная стрелка, «на карту»."""
    ft, fb = font(F_HEAD, 70), font(F_HEAD_M, 54)
    h = 520
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=BLACK)
    d.rectangle([0, h - 12, w, h], fill=RED)
    im.alpha_composite(_icon_circle(icon, 150), ((w - 150) // 2, 40))
    d.text(((w - tw(top.upper(), ft)) / 2, 210), top.upper(), font=ft, fill=WHITE)
    cx = w // 2
    d.line([(cx, 310), (cx, 370)], fill=RED, width=10)
    d.polygon([(cx - 26, 362), (cx + 26, 362), (cx, 394)], fill=RED)
    d.text(((w - tw(bottom.upper(), fb)) / 2, 410), bottom.upper(), font=fb, fill=MILK)
    im.save(path)
    return path


def quote(path, text, w, kicker=None):
    """Цитата: огромная красная кавычка + фраза Oswald."""
    fq, ft, fk = font(F_HEAD, 220), font(F_HEAD_M, 78), font(F_BODY_B, 32)
    lines = wrap(text.upper(), ft, w - 40)
    top = 200
    h = top + len(lines) * 90 + (70 if kicker else 20)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, -20), "«", font=fq, fill=RED)
    y = top
    for line in lines:
        d.text((0, y), line, font=ft, fill=WHITE)
        y += 90
    if kicker:
        d.text((0, y + 16), kicker.upper(), font=fk, fill=STEEL)
    im.save(path)
    return path
