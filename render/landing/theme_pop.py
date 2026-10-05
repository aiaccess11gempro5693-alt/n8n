"""Стиль «Поп-ритейл» (борд scratch/img/l1b_board_pop.png, выбран 05.10.2026).

Яркие плоские цветовые блоки (кобальт / мандарин / лайм / чернила), жирный
округлый Rubik ExtraBold + Golos Text, карточки-ценники с дыркой, крупные
цифры шагов, жёсткая смещённая тень вместо мягкой. Совсем не похоже на
корпоративный стиль фармы (render/corner, Inter, белые карточки с мягкой тенью).

Модуль задаёт только оформление: компоненты возвращают (png, pad) как
render.corner.cards, а setup() подменяет фон кадра, рамку угла и вид субтитров.
Раскладку сцен и тайминги задаёт скрипт ролика.
"""
import functools
import os

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
F_HEAD = f"{FONTS}/Rubik-ExtraBold.ttf"
F_SEMI = f"{FONTS}/Rubik-SemiBold.ttf"
F_BODY = f"{FONTS}/GolosText-Medium.ttf"
F_BODY_B = f"{FONTS}/GolosText-Bold.ttf"

COBALT = (47, 75, 255, 255)      # #2F4BFF
TANGERINE = (255, 122, 26, 255)  # #FF7A1A
LIME = (198, 244, 50, 255)       # #C6F432
INK = (17, 20, 51, 255)          # #111433
WHITE = (255, 255, 255, 255)
GREY = (233, 235, 245, 255)
GREY_TXT = (150, 154, 180, 255)
STEP_COLORS = [COBALT, TANGERINE, LIME, INK]

PAD = 30        # поле вокруг видимой части (под смещённую тень)
SHADOW = 10     # смещение жёсткой тени

ICONS = {"listen": "l1p_ic_listen", "check": "l1p_ic_check", "form": "l1p_ic_form",
         "refund": "l1p_ic_refund", "bank": "l1p_ic_bank", "loyal": "l1p_ic_loyal"}
ILL = "l1p_ill_counter"

_fonts = {}


def font(path, size):
    from PIL import ImageFont
    if (path, size) not in _fonts:
        _fonts[(path, size)] = ImageFont.truetype(path, size)
    return _fonts[(path, size)]


def _tw(text, f):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(text, font=f)


def wrap(text, f, max_w):
    lines, cur = [], []
    for word in text.split():
        trial = " ".join(cur + [word])
        if cur and _tw(trial, f) > max_w:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    return lines + [" ".join(cur)] if cur else lines


def _canvas(w, h):
    return Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))


def _block(w, h, fill, radius=26, outline=None, shadow=INK):
    """Плоский блок с жёсткой смещённой тенью (поп-стикер)."""
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    if shadow:
        d.rounded_rectangle([PAD + SHADOW, PAD + SHADOW, PAD + w + SHADOW, PAD + h + SHADOW], radius, fill=shadow)
    d.rounded_rectangle([PAD, PAD, PAD + w, PAD + h], radius, fill=fill,
                        outline=outline, width=4 if outline else 0)
    return im


def _icon(src, size):
    """Иконка в цветном круге: обрезаем белые поля до круга, вписываем в маску."""
    from render.corner import cards as K
    return K._icon(src, size)


def _arrow(d, x, y, w, color, t=8):
    d.line([(x, y), (x + w - 14, y)], fill=color, width=t)
    d.polygon([(x + w, y), (x + w - 22, y - 14), (x + w - 22, y + 14)], fill=color)


# ---------------------------------------------------------------- компоненты

def topic_card(path, kicker, title, subtitle, w):
    f_k, f_t, f_s = font(F_BODY_B, 24), font(F_HEAD, 56), font(F_BODY, 28)
    t_lines, s_lines = wrap(title, f_t, w - 80), wrap(subtitle, f_s, w - 80)
    h = 40 + 46 + 18 + len(t_lines) * 62 + 30 + len(s_lines) * 36 + 40
    im = _block(w, h, COBALT)
    d = ImageDraw.Draw(im)
    x, y = PAD + 40, PAD + 40
    kw = _tw(kicker.upper(), f_k) + 36
    d.rounded_rectangle([x, y, x + kw, y + 42], 21, fill=LIME)
    d.text((x + 18, y + 7), kicker.upper(), font=f_k, fill=INK)
    y += 46 + 18
    for line in t_lines:
        d.text((x, y), line, font=f_t, fill=WHITE)
        y += 62
    d.rounded_rectangle([x, y + 4, x + 90, y + 14], 5, fill=TANGERINE)
    y += 30
    for line in s_lines:
        d.text((x, y), line, font=f_s, fill=(214, 222, 255, 255))
        y += 36
    im.save(path)
    return path, PAD


def headline(path, kicker, text, w, fill=LIME, fg=INK):
    f_k, f_t = font(F_BODY_B, 24), font(F_HEAD, 58)
    lines = wrap(text, f_t, w - 80)
    h = 38 + 34 + len(lines) * 64 + 34
    im = _block(w, h, fill)
    d = ImageDraw.Draw(im)
    x, y = PAD + 40, PAD + 38
    d.text((x, y), kicker.upper(), font=f_k, fill=fg)
    y += 40
    for line in lines:
        d.text((x, y), line, font=f_t, fill=fg)
        y += 64
    im.save(path)
    return path, PAD


def four_card(path, w):
    f_num, f_u, f_k = font(F_HEAD, 180), font(F_HEAD, 66), font(F_BODY_B, 28)
    h = 230
    im = _block(w, h, TANGERINE)
    d = ImageDraw.Draw(im)
    x = PAD + 40
    d.text((x, PAD + 2), "4", font=f_num, fill=WHITE)
    x += _tw("4", f_num) + 24
    d.text((x, PAD + 48), "шага", font=f_u, fill=WHITE)
    kw = _tw("ВСЁ РЕШАЮТ", f_k) + 34
    d.rounded_rectangle([x, PAD + 140, x + kw, PAD + 184], 22, fill=INK)
    d.text((x + 17, PAD + 147), "ВСЁ РЕШАЮТ", font=f_k, fill=LIME)
    im.save(path)
    return path, PAD


STEP_LABELS = ["Выслушать", "Проверить", "Оформить", "Вернуть"]


def stepper(path, active, w):
    """Четыре квадрата-номера: пройденные — свой цвет с галочкой, текущий —
    свой цвет крупнее, следующие — серые."""
    h = 170
    im = _block(w, h, WHITE, outline=INK)
    d = ImageDraw.Draw(im)
    n = 4
    colw = (w - 40) / n
    xs = [PAD + 20 + colw * (k + 0.5) for k in range(n)]
    cy = PAD + 62
    f_n, f_l = font(F_HEAD, 40), font(F_BODY_B, 26 if w > 900 else 24)
    for k in range(n - 1):
        col = STEP_COLORS[k] if k < active else GREY
        d.line([(xs[k] + 46, cy), (xs[k + 1] - 46, cy)], fill=col, width=8)
    for k, (x, lab) in enumerate(zip(xs, STEP_LABELS)):
        s = 40 if k == active else 32
        fill = STEP_COLORS[k] if k <= active else GREY
        d.rounded_rectangle([x - s, cy - s, x + s, cy + s], 16, fill=fill)
        fg = INK if fill in (LIME, GREY) else WHITE
        if k < active:
            d.line([(x - 13, cy + 1), (x - 3, cy + 12), (x + 15, cy - 11)], fill=fg, width=7)
        else:
            num = str(k + 1)
            d.text((x - _tw(num, f_n) / 2, cy - 26), num, font=f_n, fill=fg if k == active else GREY_TXT)
        col = INK if k <= active else GREY_TXT
        d.text((x - _tw(lab, f_l) / 2, cy + 52), lab, font=f_l, fill=col)
    im.save(path)
    return path, PAD


def _tag(w, h, color):
    """Карточка-ценник: белая, с цветной «шапкой» слева, дыркой и обводкой."""
    im = _block(w, h, WHITE, outline=INK)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([PAD, PAD, PAD + 70, PAD + h], 26, fill=color)
    d.rectangle([PAD + 40, PAD + 2, PAD + 70, PAD + h - 2], fill=color)
    d.line([(PAD + 70, PAD + 2), (PAD + 70, PAD + h - 2)], fill=INK, width=4)
    d.rounded_rectangle([PAD, PAD, PAD + w, PAD + h], 26, outline=INK, width=4)
    cx, cy = PAD + 35, PAD + h // 2
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=WHITE, outline=INK, width=4)
    return im


def step_detail(path, icon_src, num, title, keys, w, isz=130):
    color = STEP_COLORS[num - 1]
    f_k, f_t, f_c = font(F_BODY_B, 24), font(F_HEAD, 44), font(F_BODY_B, 28)
    tx = 70 + 30 + isz + 30
    t_lines = wrap(title, f_t, w - tx - 30)
    rows, cur, cw = [], [], 0
    for kword in keys:
        kw = _tw(kword, f_c) + 40
        if cur and cw + kw > w - tx - 30:
            rows.append(cur)
            cur, cw = [], 0
        cur.append((kword, kw))
        cw += kw + 10
    if cur:
        rows.append(cur)
    h = max(40 + isz + 40, 36 + 44 + len(t_lines) * 52 + 14 + len(rows) * 58 + 30)
    im = _tag(w, h, color)
    d = ImageDraw.Draw(im)
    im.alpha_composite(_icon(icon_src, isz), (PAD + 100, PAD + (h - isz) // 2))
    x, y = PAD + tx, PAD + 34
    label = f"ШАГ {num}"
    lw = _tw(label, f_k) + 30
    d.rounded_rectangle([x, y, x + lw, y + 38], 19, fill=color)
    d.text((x + 15, y + 5), label, font=f_k, fill=INK if color == LIME else WHITE)
    y += 50
    for line in t_lines:
        d.text((x, y), line, font=f_t, fill=INK)
        y += 52
    y += 14
    for row in rows:
        cx = x
        for kword, kw in row:
            d.rounded_rectangle([cx, y, cx + kw, y + 46], 23, fill=GREY)
            d.text((cx + 20, y + 7), kword, font=f_c, fill=INK)
            cx += kw + 10
        y += 58
    im.save(path)
    return path, PAD


def note_card(path, icon_src, kicker, text, w, isz=90):
    f_k, f_t = font(F_BODY_B, 24), font(F_HEAD, 38)
    lines = wrap(text, f_t, w - isz - 90)
    h = max(isz + 40, 30 + 34 + len(lines) * 46 + 26)
    im = _block(w, h, LIME)
    d = ImageDraw.Draw(im)
    im.alpha_composite(_icon(icon_src, isz), (PAD + 22, PAD + (h - isz) // 2))
    x, y = PAD + isz + 46, PAD + 28
    d.text((x, y), kicker.upper(), font=f_k, fill=INK)
    y += 36
    for line in lines:
        d.text((x, y), line, font=f_t, fill=INK)
        y += 46
    im.save(path)
    return path, PAD


def verbs_card(path, w):
    f_k, f_v, f_n = font(F_BODY_B, 24), font(F_HEAD, 42), font(F_HEAD, 30)
    h = 30 + 40 + 4 * 70 + 20
    im = _block(w, h, INK, shadow=COBALT)
    d = ImageDraw.Draw(im)
    x, y = PAD + 36, PAD + 30
    d.text((x, y), "ЗАПОМНИТЕ ПОРЯДОК", font=f_k, fill=LIME)
    y += 46
    for k, v in enumerate(STEP_LABELS):
        c = STEP_COLORS[k] if k < 3 else WHITE
        d.rounded_rectangle([x, y, x + 52, y + 52], 14, fill=c)
        num = str(k + 1)
        d.text((x + 26 - _tw(num, f_n) / 2, y + 7), num, font=f_n, fill=INK if c in (LIME, WHITE) else WHITE)
        d.text((x + 72, y + 2), v, font=f_v, fill=WHITE)
        y += 70
    im.save(path)
    return path, PAD


def today_tomorrow(path, w, loyal_icon):
    f_k, f_t = font(F_BODY_B, 24), font(F_HEAD, 42)
    l1 = wrap("Спокойный возврат", f_t, w - 80)
    l2 = wrap("Постоянный покупатель", f_t, w - 200)
    h1 = 30 + 34 + len(l1) * 50 + 28
    h2 = 30 + 34 + len(l2) * 50 + 30
    h = h1 + h2
    im = _block(w, h, COBALT)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([PAD, PAD + h1, PAD + w, PAD + h], 26, fill=TANGERINE)
    d.rectangle([PAD, PAD + h1, PAD + w, PAD + h1 + 30], fill=TANGERINE)
    x, y = PAD + 40, PAD + 30
    d.text((x, y), "СЕГОДНЯ", font=f_k, fill=LIME)
    y += 34
    for line in l1:
        d.text((x, y), line, font=f_t, fill=WHITE)
        y += 50
    y = PAD + h1 + 30
    d.text((x, y), "ЗАВТРА", font=f_k, fill=INK)
    y += 34
    for line in l2:
        d.text((x, y), line, font=f_t, fill=WHITE)
        y += 50
    im.alpha_composite(_icon(loyal_icon, 110), (PAD + w - 140, PAD + h - 136))
    im.save(path)
    return path, PAD


def image_card(path, src, w):
    """Иллюстрация в толстой чернильной рамке с лаймовой смещённой тенью."""
    from PIL import ImageOps
    pic = Image.open(src).convert("RGBA")
    iw, ih = w, int(w * pic.height / pic.width)
    pic = ImageOps.fit(pic, (iw, ih))
    im = _block(w, ih, WHITE, shadow=LIME)
    mask = Image.new("L", (iw, ih), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, iw - 1, ih - 1], 26, fill=255)
    im.paste(pic, (PAD, PAD), mask)
    ImageDraw.Draw(im).rounded_rectangle([PAD, PAD, PAD + iw, PAD + ih], 26, outline=INK, width=5)
    im.save(path)
    return path, PAD


# ---------------------------------------------------------------- кадр и субтитры

def setup(G, S, M, C):
    """Подменяет фон угловой сцены, цвет вокруг рамки угла и вид субтитров."""
    S.LIGHT_BG = WHITE
    S.BLUE = INK

    def make_background(path):
        W, H = G.FRAME_W, G.FRAME_H
        bg = Image.new("RGBA", (W, H), WHITE)
        d = ImageDraw.Draw(bg)
        if W > H:   # 16:9 — правый верх свободен (угол аватара — правый низ)
            d.ellipse([W - 330, -230, W + 230, 330], fill=COBALT)
            d.ellipse([W - 470, 300, W - 400, 370], fill=LIME)
            d.rounded_rectangle([-60, H - 150, 140, H + 50], 40, fill=LIME)
            for i in range(4):
                for j in range(3):
                    d.ellipse([W - 520 + i * 26, 470 + j * 26, W - 512 + i * 26, 478 + j * 26], fill=TANGERINE)
        else:       # 9:16
            d.ellipse([W - 260, -200, W + 200, 260], fill=COBALT)
            d.rounded_rectangle([-80, H - 260, 120, H - 60], 40, fill=LIME)
            d.ellipse([60, 1180, 120, 1240], fill=TANGERINE)
        bg.save(path)
        return path

    M.make_background = make_background

    C.FONT_PATH = F_BODY_B
    C._font = TTFont(F_BODY_B)
    C._cmap = C._font.getBestCmap()
    C._hmtx = C._font["hmtx"]
    C._upm = C._font["head"].unitsPerEm
    C._SPACE_W = C._text_width(" ")
    C.build_filter = functools.partial(C.build_filter, panel_color="0x111433FF", text_color="0xFFFFFF",
                                       accent_color="0xC6F432")
