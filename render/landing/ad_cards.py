"""Карточки рекламных Reels №20–21 в стиле сайта ИИАВАТАР (графит #111311, оранжевый #F3531B,
тёплый белый #F4F1EC; Oswald для заголовков и сумм — в нём есть «₽», Montserrat для текста).

Каждая функция рисует полноразмерный прозрачный кадр 1080×1920 (RGBA PNG) и возвращает
(путь, (верх, низ)) — вертикальные границы нарисованного, чтобы движок проверил безопасную зону
250–1500 и то, что карточка не заходит на субтитры. Состояния одной карточки рисуются одной
функцией с параметром — меняются на месте без угасания (правило «ничего не мелькает»).
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
OSW = f"{FONTS}/Oswald-Bold.ttf"
OSW_M = f"{FONTS}/Oswald-Medium.ttf"
MON = f"{FONTS}/Montserrat-ExtraBold.ttf"
MON_S = f"{FONTS}/Montserrat-SemiBold.ttf"
W, H = 1080, 1920
GRAPH = (17, 19, 17)
ORANGE = (243, 83, 27)
CREAM = (244, 241, 236)
INK = (34, 34, 32)
GREY = (120, 118, 112)
GREEN = (46, 160, 92)

_fc = {}


def F(path, size):
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def _shadowed(card, x, y):
    """Холст кадра с карточкой и мягкой тенью под ней."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = card.split()[3].point(lambda a: 150 if a > 0 else 0)
    sh.paste((0, 0, 0, 255), (x + 10, y + 22), m)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    im.alpha_composite(card, (x, y))
    return im


def _check(d, cx, cy, r, color=GREEN):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.line([(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)],
           fill=(255, 255, 255), width=max(4, r // 4), joint="curve")


# ---------- №20: чек ----------
RECEIPT_ROWS = [("Студия", "0 ₽"), ("Оператор", "0 ₽"), ("Свет", "0 ₽"), ("Гримёр", "0 ₽"), ("Попытки ×20", "0 ₽")]


def receipt(path, n_rows, total=False, stamp=False):
    cw, ch = 760, 800
    card = Image.new("RGBA", (cw, ch + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, cw, ch], fill=CREAM + (255,))
    # зубчатый низ
    for i in range(0, cw, 30):
        d.polygon([(i, ch), (i + 15, ch + 24), (i + 30, ch)], fill=CREAM + (255,))
    d.text((cw / 2, 70), "КАССОВЫЙ ЧЕК", font=F(OSW, 58), fill=INK, anchor="mm")
    d.text((cw / 2, 128), "съёмка одного ролика", font=F(MON_S, 30), fill=GREY, anchor="mm")
    for x in range(40, cw - 40, 22):
        d.line([(x, 172), (x + 11, 172)], fill=GREY, width=3)
    y = 222
    for i, (name, price) in enumerate(RECEIPT_ROWS[:n_rows]):
        d.text((50, y), name, font=F(MON, 40), fill=INK, anchor="lm")
        pw = d.textlength(price, font=F(OSW, 46))
        nw = d.textlength(name, font=F(MON, 40))
        for x in range(int(70 + nw), int(cw - 70 - pw), 16):
            d.ellipse([x, y + 8, x + 5, y + 13], fill=GREY)
        d.text((cw - 50, y), price, font=F(OSW, 46), fill=INK, anchor="rm")
        y += 84
    if total:
        for x in range(40, cw - 40, 22):
            d.line([(x, 650), (x + 11, 650)], fill=GREY, width=3)
        d.text((50, 722), "ИТОГО", font=F(OSW, 72), fill=INK, anchor="lm")
        d.text((cw - 50, 722), "0 ₽", font=F(OSW, 96), fill=ORANGE, anchor="rm")
    x0, y0 = (W - cw) // 2, 262
    im = _shadowed(card, x0, y0)
    if stamp:
        st = Image.new("RGBA", (720, 230), (0, 0, 0, 0))
        s = ImageDraw.Draw(st)
        s.rounded_rectangle([6, 6, 714, 224], radius=26, outline=ORANGE + (245,), width=12)
        s.text((360, 80), "ВЕДУЩЕЙ", font=F(OSW, 82), fill=ORANGE + (245,), anchor="mm")
        s.text((360, 165), "НЕ СУЩЕСТВУЕТ", font=F(OSW, 82), fill=ORANGE + (245,), anchor="mm")
        st = st.rotate(-12, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(st, ((W - st.width) // 2, 450))
    im.save(path)
    return path, (y0, y0 + ch + 30)


# ---------- общие ----------
def price(path, chips_level=0):
    cw, ch = 860, 380 + 90 * chips_level
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw, ch], radius=40, fill=GRAPH + (245,), outline=ORANGE + (255,), width=4)
    d.text((cw / 2, 70), "ТАКОЕ ВИДЕО ДЛЯ ВАС", font=F(OSW_M, 46), fill=CREAM, anchor="mm")
    big, small = F(OSW, 140), F(OSW_M, 64)
    t1, t2 = "ОТ 1 000 ₽", " / МИН"
    w1, w2 = d.textlength(t1, font=big), d.textlength(t2, font=small)
    x = (cw - w1 - w2) / 2
    d.text((x, 270), t1, font=big, fill=ORANGE, anchor="ls")
    d.text((x + w1, 270), t2, font=small, fill=CREAM, anchor="ls")
    rows = [["без съёмок", "без студии", "без актёров"], ["реклама", "обучение", "блог"]]
    y = 370
    for lvl in range(chips_level):
        chips = rows[lvl]
        f = F(MON, 34)
        widths = [d.textlength(c, font=f) + 54 for c in chips]
        x = (cw - sum(widths) - 16 * (len(chips) - 1)) / 2
        for c, w_ in zip(chips, widths):
            fill = ORANGE if lvl == 0 else (60, 62, 58)
            d.rounded_rectangle([x, y, x + w_, y + 66], radius=33, fill=fill)
            d.text((x + w_ / 2, y + 33), c, font=f, fill=(255, 255, 255), anchor="mm")
            x += w_ + 16
        y += 86
    x0, y0 = (W - cw) // 2, 330
    _shadowed(card, x0, y0).save(path)
    return path, (y0, y0 + ch)


def cta(path, word):
    """Призыв в две строки: «НАПИШИТЕ В ДИРЕКТ» + крупно «СЛОВО»."""
    f1, f2 = F(OSW_M, 48), F(OSW, 96)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    big = f"«{word}»"
    cw = int(max(tmp.textlength("НАПИШИТЕ В ДИРЕКТ", font=f1), tmp.textlength(big, font=f2)) + 120)
    ch = 210
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw, ch], radius=44, fill=ORANGE + (255,))
    d.text((cw / 2, 58), "НАПИШИТЕ В ДИРЕКТ", font=f1, fill=(255, 238, 228), anchor="mm")
    d.text((cw / 2, 140), big, font=f2, fill=(255, 255, 255), anchor="mm")
    assert cw <= W - 60, "CTA не помещается по ширине"
    x0, y0 = (W - cw) // 2, 900
    _shadowed(card, x0, y0).save(path)
    return path, (y0, y0 + ch)


# ---------- №21: регламент ----------
MEMO_ROWS = ["Встречаем за 10 секунд", "«Подешевле?» — 2 варианта", "Улыбаемся, даже если тяжело"]


def memo(path, n_checked):
    cw, ch = 860, 600
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw, ch], radius=34, fill=(255, 255, 255, 255))
    d.rounded_rectangle([0, 0, cw, 130], radius=34, fill=GRAPH + (255,))
    d.rectangle([0, 96, cw, 130], fill=GRAPH + (255,))
    d.text((48, 66), "РЕГЛАМЕНТ", font=F(OSW, 64), fill=CREAM, anchor="lm")
    d.text((cw - 48, 66), "с понедельника", font=F(MON_S, 32), fill=ORANGE, anchor="rm")
    y = 210
    for i, row in enumerate(MEMO_ROWS):
        done = i < n_checked
        if done:
            _check(d, 92, y, 38)
        else:
            d.ellipse([54, y - 38, 130, y + 38], outline=(200, 198, 192), width=5)
            d.text((92, y), str(i + 1), font=F(OSW, 40), fill=GREY, anchor="mm")
        d.text((160, y), row, font=F(MON, 38), fill=INK if done else GREY, anchor="lm")
        y += 140
    x0, y0 = (W - cw) // 2, 330
    _shadowed(card, x0, y0).save(path)
    return path, (y0, y0 + ch)


def doc_to_video(path, chips=False):
    cw, ch = 860, 560 if chips else 400
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw, ch], radius=40, fill=GRAPH + (245,), outline=ORANGE + (255,), width=4)
    # документ
    d.rounded_rectangle([110, 70, 290, 300], radius=16, fill=CREAM)
    for k in range(5):
        d.line([(140, 120 + k * 36), (260 - (k % 2) * 40, 120 + k * 36)], fill=(170, 166, 158), width=8)
    d.text((200, 345), "ИНСТРУКЦИЯ", font=F(OSW_M, 40), fill=CREAM, anchor="mm")
    # стрелка
    d.line([(345, 185), (500, 185)], fill=ORANGE, width=14)
    d.polygon([(500, 155), (550, 185), (500, 215)], fill=ORANGE)
    # видео
    d.rounded_rectangle([580, 80, 760, 290], radius=22, fill=ORANGE)
    d.polygon([(645, 140), (645, 230), (715, 185)], fill=(255, 255, 255))
    d.text((670, 345), "ВИДЕО", font=F(OSW_M, 40), fill=CREAM, anchor="mm")
    if chips:
        items = ["расскажу", "проверю", "повторю ×100"]
        f = F(MON, 34)
        widths = [d.textlength(c, font=f) + 54 for c in items]
        x = (cw - sum(widths) - 16 * 2) / 2
        for c, w_ in zip(items, widths):
            d.rounded_rectangle([x, 430, x + w_, 496], radius=33, fill=ORANGE)
            d.text((x + w_ / 2, 463), c, font=f, fill=(255, 255, 255), anchor="mm")
            x += w_ + 16
    x0, y0 = (W - cw) // 2, 330
    _shadowed(card, x0, y0).save(path)
    return path, (y0, y0 + ch)


def ai_stamp(path, l1="СДЕЛАНО", l2="НЕЙРОСЕТЬЮ"):
    st = Image.new("RGBA", (760, 250), (0, 0, 0, 0))
    s = ImageDraw.Draw(st)
    s.rounded_rectangle([6, 6, 754, 244], radius=28, fill=GRAPH + (200,), outline=ORANGE + (255,), width=12)
    s.text((380, 88), l1, font=F(OSW, 88), fill=ORANGE, anchor="mm")
    s.text((380, 178), l2, font=F(OSW, 88), fill=CREAM, anchor="mm")
    st = st.rotate(-8, expand=True, resample=Image.BICUBIC)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y0 = 760
    im.alpha_composite(st, ((W - st.width) // 2, y0))
    im.save(path)
    return path, (y0, y0 + st.height)


# ---------- №24: два варианта продукта ----------
def options(path, level=1):
    """Карточка «Два варианта»: 1 — делаем ролики за вас (с ценой и чипами), 2 — своя система.
    level=1 — только первый вариант, level=2 — оба (второй встаёт ниже на том же месте)."""
    cw = 880
    ch = 440 if level == 1 else 700
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw, ch], radius=40, fill=GRAPH + (245,), outline=ORANGE + (255,), width=4)
    # вариант 1
    d.ellipse([40, 44, 112, 116], fill=ORANGE)
    d.text((76, 80), "1", font=F(OSW, 50), fill=(255, 255, 255), anchor="mm")
    d.text((136, 62), "ДЕЛАЕМ ЗА ВАС", font=F(OSW, 54), fill=CREAM, anchor="lm")
    d.text((136, 112), "от 1 000 ₽ / мин", font=F(OSW_M, 44), fill=ORANGE, anchor="lm")
    chips = ["сценарий", "картинки", "музыка", "монтаж"]
    f = F(MON, 30)
    x, y = 44, 170
    for c in chips:
        w_ = d.textlength(c, font=f) + 46
        d.rounded_rectangle([x, y, x + w_, y + 58], radius=29, fill=(60, 62, 58))
        d.text((x + w_ / 2, y + 29), c, font=f, fill=(255, 255, 255), anchor="mm")
        x += w_ + 14
    d.text((44, 292), "всё согласуем с вами", font=F(MON_S, 32), fill=(200, 196, 188), anchor="lm")
    _check(d, cw - 76, 300, 30, ORANGE)
    if level >= 2:
        d.line([(44, 380), (cw - 44, 380)], fill=(70, 72, 68), width=3)
        d.ellipse([40, 420, 112, 492], fill=CREAM)
        d.text((76, 456), "2", font=F(OSW, 50), fill=GRAPH, anchor="mm")
        d.text((136, 438), "СВОЯ СИСТЕМА", font=F(OSW, 54), fill=CREAM, anchor="lm")
        d.text((136, 490), "делаете ролики сами", font=F(OSW_M, 44), fill=ORANGE, anchor="lm")
        d.text((44, 580), "настроим под вас,", font=F(MON_S, 32), fill=(200, 196, 188), anchor="lm")
        d.text((44, 626), "платите только за нейросети", font=F(MON_S, 32), fill=(200, 196, 188), anchor="lm")
    x0, y0 = (W - cw) // 2, 330
    _shadowed(card, x0, y0).save(path)
    return path, (y0, y0 + ch)
