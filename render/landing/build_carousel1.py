"""Пост-карусель Instagram «Зачем вам ИИ-ведущий» — без видео и без аватара.

Все слайды и иконки нарисованы кодом (PIL), без генерации картинок нейросетью.
Стиль — графит/оранжевый сайта ИИАВАТАР (theme_brand.py): Oswald Bold капслоком,
Montserrat для текста. Формат 4:5 (1080×1350) — максимум места в ленте.

python3 render/landing/build_carousel1.py  →  docs/landing/insta/carousel-1/slide-NN.jpg
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
OUT = f"{ROOT}/docs/landing/insta/carousel-1"
W, H = 1080, 1350
M = 84                                   # поля

BG = (17, 19, 17)
CARD = (30, 33, 30)
CARD2 = (40, 43, 40)
OR = (243, 83, 27)
OR_DIM = (120, 48, 22)
CREAM = (244, 241, 236)
GREY = (150, 150, 146)
DIM = (95, 97, 93)

_fc = {}


def F(name, size):
    path = {"head": "Oswald-Bold.ttf", "headm": "Oswald-Medium.ttf", "b": "Montserrat-ExtraBold.ttf",
            "bb": "Montserrat-Bold.ttf", "s": "Montserrat-SemiBold.ttf"}[name]
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(f"{FONTS}/{path}", size)
    return _fc[(path, size)]


def tl(d, text, f):
    return d.textlength(text, font=f)


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        c = (cur + " " + w).strip()
        if tl(d, c, f) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = c
    lines.append(cur)
    return lines


def text_block(d, xy, text, f, fill, maxw, lh=1.3):
    x, y = xy
    for ln in wrap(d, text, f, maxw):
        d.text((x, y), ln, font=f, fill=fill)
        y += f.size * lh
    return y


# ---------- фон и рамка слайда ----------

def canvas(n, total):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 54):                      # едва заметная сетка
        d.line([(x, 0), (x, H)], fill=(23, 25, 23))
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=(23, 25, 23))
    glow = Image.new("L", (W, H), 0)               # тёплое свечение в углу
    ImageDraw.Draw(glow).ellipse([W - 520, -420, W + 380, 380], fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    im = Image.composite(Image.new("RGB", (W, H), OR), im, glow)
    d = ImageDraw.Draw(im)
    # логотип и номер
    d.rounded_rectangle([M, 64, M + 26, 90], 6, fill=OR)
    d.text((M + 40, 77), "ИИАВАТАР", font=F("head", 30), fill=CREAM, anchor="lm")
    d.text((W - M, 77), f"{n:02d} / {total:02d}", font=F("headm", 28), fill=GREY, anchor="rm")
    # полоса прогресса снизу
    seg = (W - 2 * M - (total - 1) * 10) / total
    for i in range(total):
        x0 = M + i * (seg + 10)
        d.rounded_rectangle([x0, H - 58, x0 + seg, H - 52], 3, fill=OR if i < n else (45, 48, 45))
    return im, d


def kicker(d, y, text):
    f = F("bb", 30)
    w = tl(d, text, f)
    d.rounded_rectangle([M, y, M + w + 36, y + 52], 26, outline=OR, width=3)
    d.text((M + 18, y + 26), text, font=f, fill=OR, anchor="lm")
    return y + 52


def headline(d, y, parts, size=104, lh=1.04):
    """parts: список строк; слово в [скобках] — на оранжевой плашке."""
    f = F("head", size)
    for line in parts:
        x = M
        for tok in line.split(" "):
            hl = tok.startswith("[") and tok.endswith("]")
            word = tok.strip("[]")
            w = tl(d, word, f)
            if hl:
                bb = d.textbbox((x, y), word, font=f)
                d.rectangle([x - 12, bb[1] - 10, x + w + 12, bb[3] + 12], fill=OR)
            d.text((x, y), word, font=f, fill=CREAM)
            x += w + tl(d, " ", f) + (14 if hl else 0)
        y += size * lh
    return y + 24


def swipe_hint(d, text="листайте"):
    f = F("bb", 30)
    x1 = W - M
    d.text((x1 - 70, H - 118), text, font=f, fill=CREAM, anchor="rm")
    ax = x1 - 52
    d.line([(ax, H - 118), (x1, H - 118)], fill=OR, width=5)
    d.line([(x1 - 16, H - 132), (x1, H - 118), (x1 - 16, H - 104)], fill=OR, width=5, joint="curve")


# ---------- иконки (линейные, рисуются кодом) ----------

def ic_frame(d, cx, cy, r=54, fill=CARD2):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def icon(d, name, cx, cy, s=1.0, col=OR, lw=6, bg=True):
    if bg:
        ic_frame(d, cx, cy, int(54 * s))
    k = s
    L = lambda pts, w=lw: d.line([(cx + x * k, cy + y * k) for x, y in pts], fill=col, width=w, joint="curve")
    R = lambda x0, y0, x1, y1, r=6, w=lw: d.rounded_rectangle(
        [cx + x0 * k, cy + y0 * k, cx + x1 * k, cy + y1 * k], int(r * k), outline=col, width=w)
    E = lambda x0, y0, x1, y1, w=lw, fill=None: d.ellipse(
        [cx + x0 * k, cy + y0 * k, cx + x1 * k, cy + y1 * k], outline=col, width=w, fill=fill)
    A = lambda x0, y0, x1, y1, a0, a1, w=lw: d.arc(
        [cx + x0 * k, cy + y0 * k, cx + x1 * k, cy + y1 * k], a0, a1, fill=col, width=w)
    if name == "doc":
        R(-20, -27, 20, 27, 5)
        for yy in (-12, 0, 12):
            L([(-10, yy), (10 if yy < 12 else 2, yy)], 4)
    elif name == "mic":
        R(-10, -28, 10, 6, 10)
        A(-20, -14, 20, 18, 0, 180)
        L([(0, 18), (0, 28)])
        L([(-11, 28), (11, 28)])
    elif name == "person":
        E(-11, -28, 11, -6)
        A(-24, 0, 24, 48, 180, 360)
        L([(-24, 24), (24, 24)])
    elif name == "play":
        R(-30, -22, 30, 22, 7)
        d.polygon([(cx - 7 * k, cy - 10 * k), (cx - 7 * k, cy + 10 * k), (cx + 11 * k, cy)], fill=col)
    elif name == "team":
        E(-26, -20, -8, -2, 5)
        E(8, -20, 26, -2, 5)
        A(-36, 4, 2, 40, 180, 360, 5)
        A(-2, 4, 36, 40, 180, 360, 5)
    elif name == "folder":
        L([(-28, -16), (-28, 22), (28, 22), (28, -10), (2, -10), (-6, -18), (-28, -18), (-28, -16)])
        L([(-12, 6), (-4, 13), (12, -2)], 5)
    elif name == "cap":
        d.polygon([(cx - 32 * k, cy - 6 * k), (cx, cy - 20 * k), (cx + 32 * k, cy - 6 * k), (cx, cy + 8 * k)],
                  outline=col, width=lw)
        L([(-18, 1), (-18, 16), (0, 24), (18, 16), (18, 1)], 5)
        L([(28, -4), (28, 14)], 4)
    elif name == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 28 if i % 2 == 0 else 12
            pts.append((r * math.cos(a), r * math.sin(a)))
        L(pts + [pts[0]], 5)
    elif name == "cart":
        L([(-30, -18), (-20, -18), (-12, 12), (22, 12), (28, -8), (-16, -8)], 5)
        E(-14, 16, -4, 26, 4)
        E(12, 16, 22, 26, 4)
    elif name == "globe":
        E(-27, -27, 27, 27, 5)
        E(-11, -27, 11, 27, 4)
        L([(-27, 0), (27, 0)], 4)
    elif name == "pod":
        A(-26, -26, 26, 26, 180, 360, 5)
        R(-30, -2, -16, 22, 5, 5)
        R(16, -2, 30, 22, 5, 5)
    elif name == "clock":
        E(-27, -27, 27, 27, 5)
        L([(0, -14), (0, 0), (12, 8)], 5)
    elif name == "coin":
        E(-27, -27, 27, 27, 5)
        d.text((cx, cy + 1), "₽", font=F("b", int(32 * k)), fill=col, anchor="mm")
    elif name == "pen":
        L([(-20, 20), (14, -14)], 9)
        L([(-24, 26), (-14, 24)], 4)
        L([(10, -22), (22, -10)], 5)
    elif name == "ratio":
        R(-30, -18, 4, 18, 5, 5)
        R(12, -26, 30, 26, 5, 5)
    elif name == "check":
        L([(-18, 0), (-5, 13), (20, -14)], 8)
    elif name == "cross":
        L([(-14, -14), (14, 14)], 7)
        L([(14, -14), (-14, 14)], 7)
    elif name == "chat":
        R(-28, -22, 28, 14, 10, 5)
        L([(-12, 14), (-18, 26), (2, 14)], 5)
    elif name == "camera":
        R(-30, -16, 14, 18, 6, 5)
        L([(14, -2), (30, -12), (30, 12), (14, 4)], 5)


# ---------- слайды ----------

TOTAL = 8


def s1():
    im, d = canvas(1, TOTAL)
    kicker(d, 210, "без съёмок, студии и актёров")
    y = headline(d, 300, ["ЗАЧЕМ ВАМ", "[ИИ-ВЕДУЩИЙ]", "И КАК ОН", "РАБОТАЕТ"], size=124)
    text_block(d, (M, y + 36), "Ролик с живым ведущим — из обычного текста. Разбираем за 8 слайдов: "
               "что это, как устроено и где пригодится.", F("s", 38), GREY, W - 2 * M)
    # маленький «конвейер» внизу
    y0 = 1080
    xs = [M + 54, M + 54 + 225, M + 54 + 450, M + 54 + 675]
    for i, (x, n) in enumerate(zip(xs, ["doc", "mic", "person", "play"])):
        icon(d, n, x, y0, 0.9)
        if i < 3:
            for dx in range(62, 170, 22):
                d.line([(x + dx, y0), (x + dx + 10, y0)], fill=OR_DIM, width=4)
    swipe_hint(d)
    return im


def s2():
    im, d = canvas(2, TOTAL)
    kicker(d, 190, "как обычно")
    y = headline(d, 280, ["ОДИН РОЛИК —", "[ЦЕЛАЯ] СЪЁМКА"], size=96)
    rows = [("camera", "Студия, свет, оператор", "аренда и бронь на конкретный день"),
            ("person", "Спикер или актёр", "дубли, волнение, «давайте ещё раз»"),
            ("pen", "Нашли ошибку в тексте", "переснимать заново"),
            ("globe", "Нужен второй язык", "ещё одна съёмка или дубляж")]
    y += 50
    for ic, t, sub in rows:
        d.rounded_rectangle([M, y, W - M, y + 150], 22, fill=CARD)
        icon(d, ic, M + 82, y + 75, 0.85)
        d.text((M + 168, y + 40), t, font=F("b", 38), fill=CREAM)
        d.text((M + 168, y + 92), sub, font=F("s", 30), fill=GREY)
        y += 166
    d.text((M, y + 6), "Итог: недели и бюджет, который есть не у всех.", font=F("bb", 34), fill=OR)
    return im


def s3():
    im, d = canvas(3, TOTAL)
    kicker(d, 190, "что такое ИИ-ведущий")
    y = headline(d, 280, ["ЦИФРОВОЙ", "[ЧЕЛОВЕК] В КАДРЕ"], size=100)
    y = text_block(d, (M, y + 30), "Лицо, мимика и голос созданы нейросетью. Он говорит ровно ваш текст — "
                   "спокойно, без запинок и с первого дубля.", F("s", 38), GREY, W - 2 * M)
    # схема: лицо + голос + текст = ведущий
    y += 60
    items = [("person", "лицо"), ("mic", "голос"), ("doc", "ваш текст")]
    cw = (W - 2 * M - 2 * 70) / 3
    for i, (ic, lab) in enumerate(items):
        x0 = M + i * (cw + 70)
        d.rounded_rectangle([x0, y, x0 + cw, y + 230], 26, fill=CARD)
        icon(d, ic, x0 + cw / 2, y + 95, 1.05)
        d.text((x0 + cw / 2, y + 188), lab, font=F("b", 34), fill=CREAM, anchor="mm")
        if i < 2:
            d.text((x0 + cw + 35, y + 115), "+", font=F("head", 80), fill=OR, anchor="mm")
    y += 270
    d.rounded_rectangle([M, y, W - M, y + 130], 26, fill=OR)
    icon(d, "play", M + 80, y + 65, 0.9, col=CREAM, bg=False)
    d.text((M + 150, y + 65), "= готовый ведущий ролика", font=F("b", 44), fill=CREAM, anchor="lm")
    return im


def s4():
    im, d = canvas(4, TOTAL)
    kicker(d, 190, "как это работает")
    y = headline(d, 280, ["ОТ ТЕКСТА", "ДО [РОЛИКА]"], size=104)
    steps = [("doc", "Вы присылаете текст", "регламент, урок, пост, сценарий — что есть"),
             ("pen", "Пишем сценарий", "разбиваем на сцены, ставим интонации"),
             ("mic", "Озвучка и ведущий", "голос, лицо, проверка ударений"),
             ("play", "Монтаж и готовый ролик", "графика, субтитры, музыка, обложка")]
    y += 50
    for i, (ic, t, sub) in enumerate(steps):
        cy = y + 70
        if i < 3:
            d.line([(M + 54, cy + 58), (M + 54, cy + 170 - 58)], fill=OR_DIM, width=5)
        icon(d, ic, M + 54, cy, 0.95)
        d.text((M + 140, cy - 34), f"0{i + 1}", font=F("head", 34), fill=OR)
        d.text((M + 196, cy - 34), t, font=F("b", 38), fill=CREAM)
        d.text((M + 140, cy + 18), sub, font=F("s", 29), fill=GREY)
        y += 160
    d.text((M, y + 10), "Правка — это правка текста, а не новая съёмка.", font=F("bb", 34), fill=OR)
    return im


def s5():
    im, d = canvas(5, TOTAL)
    kicker(d, 190, "где пригодится")
    headline(d, 280, ["7 [ФОРМАТОВ]"], size=104)
    tiles = [("team", "Обучение", "персонала"), ("folder", "Оцифровка", "регламентов"),
             ("cap", "Онлайн-", "курсы и уроки"), ("star", "Экспертный", "контент"),
             ("cart", "Продукт", "и продажи"), ("globe", "Локализация", "на другие языки"),
             ("pod", "Подкасты", "и дайджесты")]
    gap = 22
    cw = (W - 2 * M - gap) / 2
    ch = 172
    y0 = 430
    for i, (ic, t, sub) in enumerate(tiles):
        r, c = divmod(i, 2)
        x0 = M + c * (cw + gap)
        yy = y0 + r * (ch + gap)
        if i == 6:                                   # последняя — во всю ширину
            x1 = W - M
        else:
            x1 = x0 + cw
        d.rounded_rectangle([x0, yy, x1, yy + ch], 24, fill=CARD)
        icon(d, ic, x0 + 74, yy + ch / 2, 0.8)
        d.text((x0 + 140, yy + 50), t, font=F("b", 34), fill=CREAM)
        d.text((x0 + 140, yy + 98), sub, font=F("s", 28), fill=GREY)
    return im


def s6():
    im, d = canvas(6, TOTAL)
    kicker(d, 190, "было → стало")
    y = headline(d, 280, ["СЪЁМКА", "ПРОТИВ [ТЕКСТА]"], size=100)
    rows = [("Подготовка", "студия и люди", "только текст"),
            ("Ошибка", "переснять", "поправить слово"),
            ("Другой язык", "новая съёмка", "тот же ведущий"),
            ("Серия", "каждый с нуля", "единый стиль")]
    y += 50
    cx = M + 250                     # колонка «съёмка»
    mid = M + 540                    # колонка «ИИ-ведущий»
    d.text((cx + 20, y), "съёмка", font=F("bb", 28), fill=DIM)
    d.text((mid + 30, y), "ИИ-ведущий", font=F("bb", 28), fill=OR)
    y += 54
    for name, bad, good in rows:
        d.rounded_rectangle([M, y, W - M, y + 128], 22, fill=CARD)
        d.rounded_rectangle([mid, y, W - M, y + 128], 22, fill=CARD2)
        d.text((M + 28, y + 64), name, font=F("b", 29), fill=CREAM, anchor="lm")
        icon(d, "cross", cx + 22, y + 64, 0.5, col=DIM, bg=False, lw=5)
        d.text((cx + 46, y + 64), bad, font=F("s", 25), fill=GREY, anchor="lm")
        icon(d, "check", mid + 36, y + 64, 0.6, col=OR, bg=False)
        d.text((mid + 66, y + 64), good, font=F("bb", 27), fill=CREAM, anchor="lm")
        assert d.textlength(good, font=F("bb", 27)) < W - M - mid - 80, good
        assert d.textlength(bad, font=F("s", 25)) < mid - cx - 60, bad
        y += 146
    return im


def s7():
    im, d = canvas(7, TOTAL)
    kicker(d, 190, "что вы получаете")
    y = headline(d, 280, ["ГОТОВЫЙ", "[РОЛИК] ПОД ЗАДАЧУ"], size=100)
    items = [("ratio", "Горизонталь и вертикаль", "16:9 для сайта и курса, 9:16 для соцсетей"),
             ("person", "Свой ведущий и голос", "под тон бренда — строгий, тёплый, яркий"),
             ("chat", "Субтитры и графика", "смотрят и без звука"),
             ("globe", "Любой язык", "один ведущий говорит на нескольких")]
    y += 50
    for ic, t, sub in items:
        icon(d, ic, M + 54, y + 60, 0.9)
        d.text((M + 140, y + 22), t, font=F("b", 38), fill=CREAM)
        text_block(d, (M + 140, y + 74), sub, F("s", 29), GREY, W - 2 * M - 140, 1.25)
        y += 168
    return im


def s8():
    im, d = canvas(8, TOTAL)
    kicker(d, 190, "сколько стоит")
    y = headline(d, 280, ["ДВА [ВАРИАНТА]"], size=104)
    cards = [("Производство роликов", "делаем ролики под вашу задачу", "от 1 000 ₽", "за минуту"),
             ("Конвейер под ключ", "настраиваем — генерируете сами", "от 100 000 ₽", "разово")]
    y += 40
    for i, (t, sub, price, unit) in enumerate(cards):
        fill = OR if i == 0 else CARD
        d.rounded_rectangle([M, y, W - M, y + 230], 28, fill=fill)
        d.text((M + 40, y + 40), t, font=F("b", 40), fill=CREAM)
        d.text((M + 40, y + 96), sub, font=F("s", 29), fill=CREAM if i == 0 else GREY)
        d.text((M + 40, y + 140), price, font=F("head", 64), fill=CREAM)
        pw = tl(d, price, F("head", 64))
        d.text((M + 60 + pw, y + 178), unit, font=F("bb", 30), fill=CREAM if i == 0 else GREY)
        y += 256
    y += 20
    d.text((M, y), "Напишите «ВИДЕО» в директ —", font=F("b", 42), fill=CREAM)
    d.text((M, y + 58), "покажем примеры и посчитаем ваш ролик.", font=F("s", 34), fill=GREY)
    d.text((M, y + 130), "iiavatar.ru", font=F("head", 46), fill=OR)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, fn in enumerate([s1, s2, s3, s4, s5, s6, s7, s8], 1):
        p = f"{OUT}/slide-{i:02d}.jpg"
        fn().save(p, quality=93)
        print(p)


if __name__ == "__main__":
    main()
