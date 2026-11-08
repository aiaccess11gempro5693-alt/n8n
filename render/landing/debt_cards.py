"""Графика мультсериала «Саша: 30 дней без долгов» — мультяшный игровой стиль под героя
(плоский вектор, жирный чёрный контур): кремовые карточки с толстой обводкой и «жёсткой» тенью,
горчичный (цвет худи Саши), красный — долг/опасность, зелёный — правильный шаг. Шрифт — Rubik ExtraBold.

Каждая функция рисует полный прозрачный кадр 1080×1920 и возвращает (путь, (верх, низ)) для ad_engine.
Состояния одной карточки — одна функция с параметром (меняются на месте, без мелькания).
"""
import os

from PIL import Image, ImageDraw, ImageFont

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
RUB = f"{FONTS}/Rubik-ExtraBold.ttf"
RUB_S = f"{FONTS}/Rubik-SemiBold.ttf"
W, H = 1080, 1920
INK = (24, 22, 20)
CREAM = (255, 248, 230)
MUSTARD = (232, 172, 36)
RED = (226, 64, 52)
GREEN = (52, 170, 92)
BLUE = (60, 120, 220)
GREY = (120, 112, 100)
OUT = 7                      # толщина контура

_fc = {}


def F(size, semi=False):
    k = (semi, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(RUB_S if semi else RUB, size)
    return _fc[k]


def _box(d, xy, fill, r=28, shadow=True):
    x0, y0, x1, y1 = xy
    if shadow:
        d.rounded_rectangle([x0 + 10, y0 + 12, x1 + 10, y1 + 12], r, fill=INK)
    d.rounded_rectangle(xy, r, fill=fill, outline=INK, width=OUT)


def _ctext(d, cx, cy, text, font, fill=INK):
    d.text((cx, cy), text, font=font, fill=fill, anchor="mm")


def _fit(text, size, maxw, semi=False):
    while F(size, semi).getlength(text) > maxw and size > 20:
        size -= 2
    return F(size, semi)


def _save(im, path, top, bot):
    im.save(path)
    return path, (top, bot)


# ---------- игровая панель (всегда сверху) ----------
def hud(path, day=1, debt="300 000 ₽", temptations=0, flash=False):
    """Три плашки в ряд: ДЕНЬ / ДОЛГ / СОБЛАЗНЫ. flash — счётчик соблазнов подсвечен красным."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y0, y1 = 262, 382
    cells = [(30, 300, "ДЕНЬ", f"{day}/30", MUSTARD, INK),
             (318, 762, "ДОЛГ", debt, RED, CREAM),
             (780, 1050, "СОБЛАЗНЫ", str(temptations), RED if flash else CREAM, CREAM if flash else INK)]
    for x0, x1, label, val, fill, vcol in cells:
        _box(d, (x0, y0, x1, y1), fill, r=24)
        _ctext(d, (x0 + x1) / 2, y0 + 34, label, F(28, True), vcol)
        _ctext(d, (x0 + x1) / 2, y0 + 80, val, _fit(val, 50, x1 - x0 - 30), vcol)
    return _save(im, path, y0, y1 + 12)


# ---------- список долгов ----------
DEBTS = [("Кредитка №1", "90 000 ₽", "29%"),
         ("Кредитка №2", "70 000 ₽", "34%"),
         ("Кредитка №3", "45 000 ₽", "39%"),
         ("Кредит на телефон", "80 000 ₽", "18%"),
         ("Микрозайм", "15 000 ₽", "292%")]


def debt_list(path, top, highlight=False):
    """Список: долг / сумма / ставка в год. highlight — микрозайм красным + штамп «ГАСИТЬ ПЕРВЫМ»."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1 = 70, 1010
    rh = 70
    y1 = top + 96 + rh * len(DEBTS) + 30
    _box(d, (x0, top, x1, y1), CREAM)
    d.rounded_rectangle([x0, top, x1, top + 84], 28, fill=MUSTARD, outline=INK, width=OUT)
    d.rectangle([x0 + OUT, top + 50, x1 - OUT, top + 80], fill=MUSTARD)
    d.line([(x0, top + 84), (x1, top + 84)], fill=INK, width=OUT)
    d.text((x0 + 34, top + 42), "МОИ ДОЛГИ", font=F(42), fill=INK, anchor="lm")
    d.text((x1 - 34, top + 42), "ставка/год", font=F(28, True), fill=INK, anchor="rm")
    for i, (name, s, rate) in enumerate(DEBTS):
        y = top + 96 + rh * i + rh / 2
        hot = highlight and name == "Микрозайм"
        if hot:
            d.rounded_rectangle([x0 + 18, y - rh / 2 + 4, x1 - 18, y + rh / 2 - 4], 18, fill=RED, outline=INK,
                                width=5)
        col = CREAM if hot else INK
        d.text((x0 + 40, y), name, font=F(38, True), fill=col, anchor="lm")
        d.text((x0 + 610, y), s, font=F(38), fill=col, anchor="rm")
        d.text((x1 - 40, y), rate, font=F(40), fill=col if hot else (RED if rate == "292%" else INK), anchor="rm")
    if highlight:
        st = Image.new("RGBA", (520, 120), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([6, 6, 514, 114], 20, fill=CREAM, outline=RED, width=9)
        sd.text((260, 60), "ГАСИТЬ ПЕРВЫМ", font=F(50), fill=RED, anchor="mm")
        st = st.rotate(-7, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(st, (x1 - st.width + 30, top - 70))
    return _save(im, path, top - (80 if highlight else 0), y1 + 12)


# ---------- уведомление-соблазн ----------
def notification(path, top):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1, y1 = 80, 1000, top + 250
    _box(d, (x0, top, x1, y1), (255, 255, 255), r=40)
    # иконка-наушники
    cx, cy = x0 + 110, top + 125
    d.rounded_rectangle([cx - 70, cy - 70, cx + 70, cy + 70], 30, fill=BLUE, outline=INK, width=6)
    d.arc([cx - 42, cy - 46, cx + 42, cy + 36], 180, 360, fill=CREAM, width=12)
    for sx in (-40, 40):
        d.rounded_rectangle([cx + sx - 14, cy - 6, cx + sx + 14, cy + 40], 10, fill=CREAM)
    d.text((x0 + 210, top + 60), "Только сегодня!", font=F(34, True), fill=GREY, anchor="lm")
    d.text((x0 + 210, top + 118), "Наушники −40%", font=F(56), fill=INK, anchor="lm")
    d.text((x0 + 210, top + 182), "рассрочка без переплаты", font=F(36, True), fill=RED, anchor="lm")
    return _save(im, path, top, y1 + 12)


# ---------- стикер-реплика ----------
def sticker(path, top, line1, line2="", fill=MUSTARD, tilt=-3):
    """Крупная наклейка: строка 1 — главное, строка 2 — пояснение."""
    w, h = 900, 230 if line2 else 150
    st = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    _box(d, (6, 6, w, h), fill, r=36)
    col = CREAM if fill in (RED, GREEN, BLUE) else INK
    _ctext(d, w / 2, 6 + (75 if line2 else h / 2 - 3), line1, _fit(line1, 76, w - 80), col)
    if line2:
        _ctext(d, w / 2, 160, line2, _fit(line2, 44, w - 80, True), col)
    st = st.rotate(tilt, expand=True, resample=Image.BICUBIC)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.alpha_composite(st, ((W - st.width) // 2, top))
    return _save(im, path, top, top + st.height)


# ---------- выбор зрителя ----------
def choice(path, top, level=3):
    """level 1 — только А, 2 — А и Б, 3 — + призыв «пишите А или Б»."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1 = 60, 1020
    _box(d, (x0 + 120, top, x1 - 120, top + 86), MUSTARD, r=43)
    _ctext(d, W / 2, top + 44, "ЗАВТРА РЕШАЕТЕ ВЫ", F(44))
    y = top + 110
    opts = [("А", "Наушники в рассрочку", "2 000 ₽ в месяц", BLUE),
            ("Б", "Гашу микрозайм", "эти 2 000 ₽ — в долг", GREEN)]
    for i, (letter, l1, l2, col) in enumerate(opts):
        if i >= level:
            break
        _box(d, (x0, y, x1, y + 140), CREAM, r=32)
        d.rounded_rectangle([x0 + 22, y + 18, x0 + 126, y + 122], 24, fill=col, outline=INK, width=6)
        _ctext(d, x0 + 74, y + 70, letter, F(72), CREAM)
        d.text((x0 + 160, y + 50), l1, font=_fit(l1, 50, x1 - x0 - 200), fill=INK, anchor="lm")
        d.text((x0 + 160, y + 102), l2, font=F(38, True), fill=GREY, anchor="lm")
        y += 162
    bot = y - 22 + 12
    if level >= 3:
        _box(d, (x0 + 60, y + 4, x1 - 60, y + 92), RED, r=44)
        _ctext(d, W / 2, y + 48, "ПИШИТЕ «А» ИЛИ «Б»", F(46), CREAM)
        bot = y + 104
    return _save(im, path, top, bot)


if __name__ == "__main__":
    tmp = "/tmp/claude-0/-home-user-n8n/ca43fb62-f768-5cf6-9a9d-32340ee1ec72/scratchpad/dc"
    os.makedirs(tmp, exist_ok=True)
    bg = Image.open(os.path.join(FONTS, "..", "..", "scratch/img/debt_host_a.png")).convert("RGBA")
    bg = bg.resize((1280, 1920)).crop((100, 0, 1180, 1920))
    for name, (p, box) in {"hud": hud(f"{tmp}/hud.png", temptations=1, flash=True),
                           "list": debt_list(f"{tmp}/list.png", 1010, True),
                           "note": notification(f"{tmp}/note.png", 1040),
                           "choice": choice(f"{tmp}/choice.png", 970, 3)}.items():
        fr = bg.copy()
        if name != "hud":
            fr.alpha_composite(Image.open(f"{tmp}/hud.png"))
        fr.alpha_composite(Image.open(p))
        fr.convert("RGB").resize((540, 960)).save(f"{tmp}/prev-{name}.jpg")
        print(name, box)
