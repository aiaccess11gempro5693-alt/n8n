"""PNG-компоненты визуального слоя в стиле брендбука (docs/references/
oleg-brand-board-*.jpg): тема ролика, современный заголовок с
выделенным словом, карточка-картинка с подписью, строка "иконка + текст",
пункт сравнения ✗/✓. Каждый компонент — отдельный RGBA PNG с запечённой
мягкой тенью; возвращает (путь, pad), где pad — отступ тени вокруг
видимой части (чтобы ставить видимую часть ровно в заданные x/y).
"""
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from . import brand_style as S

NAVY = (15, 45, 125, 255)
PALE_BLUE = (232, 240, 253, 255)
SHADOW = (20, 40, 90, 46)
PAD = 30


def _card(w, h, fill, radius=26):
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([PAD, PAD + 8, PAD + w, PAD + h + 8], radius, fill=SHADOW)
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(img).rounded_rectangle([PAD, PAD, PAD + w, PAD + h], radius, fill=fill)
    return img


def wrap(text, font, max_w):
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    lines, cur = [], []
    for word in text.split():
        trial = " ".join(cur + [word])
        if cur and d.textlength(trial, font=font) > max_w:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    return lines + [" ".join(cur)] if cur else lines


def topic_card(path, kicker, title, subtitle, w=540):
    """Как "Тема ролика" на брендборде: синяя карточка, белый заголовок."""
    f_k, f_t, f_s = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 50), S.font(S.F_MEDIUM, 28)
    t_lines = wrap(title, f_t, w - 80)
    s_lines = wrap(subtitle, f_s, w - 80)
    h = 40 + 30 + 20 + len(t_lines) * 60 + 22 + len(s_lines) * 38 + 40
    img = _card(w, h, S.BLUE)
    d = ImageDraw.Draw(img)
    x, y = PAD + 40, PAD + 40
    d.text((x, y), kicker.upper(), font=f_k, fill=(190, 212, 255, 255))
    y += 50
    for line in t_lines:
        d.text((x, y), line, font=f_t, fill=S.WHITE)
        y += 60
    d.rounded_rectangle([x, y + 6, x + 70, y + 12], 3, fill=S.GREEN)
    y += 26
    for line in s_lines:
        d.text((x, y), line, font=f_s, fill=(214, 226, 255, 255))
        y += 38
    img.save(path)
    return path, PAD


def headline(path, kicker, text, accent_words=(), size=64, w=560, bg=True):
    """Современный заголовок: зелёная вертикальная полоса + киккер +
    крупный тёмно-синий текст; accent_words подсвечены голубым маркером."""
    f_k, f_t = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, size)
    inner = w - 90
    lines = wrap(text, f_t, inner)
    lh = int(size * 1.18)
    h = 40 + 36 + len(lines) * lh + 34
    img = _card(w, h, (255, 255, 255, 245)) if bg else Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y = PAD + 36, PAD + 36
    d.rounded_rectangle([x0, y, x0 + 7, y + 36 + len(lines) * lh - 8], 3, fill=S.GREEN)
    x = x0 + 30
    d.text((x, y - 4), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y += 36
    accents = {a.lower() for a in accent_words}
    for line in lines:
        cx = x
        for word in line.split():
            ww = d.textlength(word, font=f_t)
            if word.strip("«»—,.!?").lower() in accents:
                d.rounded_rectangle([cx - 8, y + lh * 0.22, cx + ww + 8, y + lh * 0.95], 10, fill=PALE_BLUE)
                d.text((cx, y), word, font=f_t, fill=S.BLUE)
            else:
                d.text((cx, y), word, font=f_t, fill=NAVY)
            cx += ww + d.textlength(" ", font=f_t)
        y += lh
    img.save(path)
    return path, PAD


def image_card(path, src, w, label=None):
    """Картинка со скруглёнными углами в белой рамке; подпись — плашка
    под картинкой внутри той же карточки."""
    im = Image.open(src).convert("RGBA")
    iw = w - 24
    ih = int(iw * im.height / im.width)
    im = ImageOps.fit(im, (iw, ih))
    f = S.font(S.F_SEMIBOLD, 32)
    lab_lines = wrap(label, f, iw - 30) if label else []
    h = 12 + ih + 12 + (len(lab_lines) * 42 + 22 if lab_lines else 0)
    img = _card(w, h, S.WHITE, radius=24)
    mask = Image.new("L", (iw, ih), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, iw - 1, ih - 1], 16, fill=255)
    img.paste(im, (PAD + 12, PAD + 12), mask)
    d = ImageDraw.Draw(img)
    y = PAD + 12 + ih + 16
    for line in lab_lines:
        d.text((PAD + 22, y), line, font=f, fill=NAVY)
        y += 42
    img.save(path)
    return path, PAD


def _icon(src, size):
    """Иконка из генерации: обрезаем белые поля до нарисованного круга
    (Nano Banana рисует круг разного размера/смещения), потом вписываем
    в круглую маску нужного размера."""
    im = Image.open(src).convert("RGBA")
    # иногда генерация оставляет чёрные углы вокруг светлого круга — заливаем их белым
    for c in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
        if sum(im.getpixel(c)[:3]) < 120:
            ImageDraw.floodfill(im, c, (255, 255, 255, 255), thresh=60)
    gray = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 14 else 0)
    bbox = gray.getbbox()
    if bbox:
        cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
        r = max(bbox[2] - bbox[0], bbox[3] - bbox[1]) / 2 + 4
        im = im.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))
    im = ImageOps.fit(im, (size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def icon_row(path, icon_src, text, w=540, h=110, num=None, num_color=None, text_size=36, dim=False,
             outline=None):
    """Белая строка: круглая иконка + текст (опционально номер-кружок).
    dim — приглушённая строка (этап, до которого ещё не дошли);
    outline — цвет рамки-акцента (выделенный пункт)."""
    img = _card(w, h, S.WHITE, radius=22)
    if outline:
        ImageDraw.Draw(img).rounded_rectangle([PAD, PAD, PAD + w, PAD + h], 22, outline=outline, width=4)
    d = ImageDraw.Draw(img)
    x = PAD + 18
    if num:
        d.ellipse([x, PAD + h // 2 - 22, x + 44, PAD + h // 2 + 22], fill=num_color or S.BLUE)
        f_n = S.font(S.F_SEMIBOLD, 22)
        tw = d.textlength(num, font=f_n)
        d.text((x + 22 - tw / 2, PAD + h // 2 - 14), num, font=f_n, fill=S.WHITE)
        x += 58
    isz = h - 22
    img.alpha_composite(_icon(icon_src, isz), (x, PAD + 11))
    x += isz + 22
    f = S.font(S.F_SEMIBOLD, text_size)
    lines = wrap(text, f, w - (x - PAD) - 20)
    lh = int(text_size * 1.25)
    y = PAD + (h - len(lines) * lh) // 2
    for line in lines:
        d.text((x, y), line, font=f, fill=S.TEXT_DARK)
        y += lh
    if dim:
        a = img.getchannel("A").point(lambda v: v * 45 // 100)
        img.putalpha(a)
    img.save(path)
    return path, PAD


def step_card(path, icon_src, text, w=400, num=None, num_color=None, kicker=None, text_size=34):
    """Вертикальная карточка: крупная иконка сверху, (номер), текст снизу —
    для цепочек шагов и пар сравнения."""
    f = S.font(S.F_SEMIBOLD, text_size)
    lines = wrap(text, f, w - 56)
    lh = int(text_size * 1.25)
    isz = 120
    h = 30 + isz + 22 + (34 if kicker else 0) + len(lines) * lh + 30
    img = _card(w, h, S.WHITE, radius=24)
    d = ImageDraw.Draw(img)
    img.alpha_composite(_icon(icon_src, isz), (PAD + 28, PAD + 30))
    if num:
        cx, cy = PAD + 28 + isz - 6, PAD + 36
        d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=num_color or S.BLUE, outline=S.WHITE, width=3)
        f_n = S.font(S.F_SEMIBOLD, 22)
        tw = d.textlength(num, font=f_n)
        d.text((cx - tw / 2, cy - 14), num, font=f_n, fill=S.WHITE)
    y = PAD + 30 + isz + 22
    if kicker:
        d.text((PAD + 28, y), kicker.upper(), font=S.font(S.F_SEMIBOLD, 24), fill=S.LIGHT_BLUE)
        y += 34
    for line in lines:
        d.text((PAD + 28, y), line, font=f, fill=S.TEXT_DARK)
        y += lh
    img.save(path)
    return path, PAD


def arrow(path, color=S.LIGHT_BLUE, w=44, h=44):
    """Шеврон-стрелка между шагами цепочки."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).line([(12, 6), (32, h // 2), (12, h - 6)], fill=color, width=7, joint="curve")
    img.save(path)
    return path, 0


def compare_row(path, icon_src, text, good, w=540, h=110):
    """Пункт сравнения: ✗ — серый зачёркнутый текст, ✓ — зелёная рамка."""
    img = _card(w, h, S.WHITE, radius=22)
    d = ImageDraw.Draw(img)
    if good:
        d.rounded_rectangle([PAD, PAD, PAD + w, PAD + h], 22, outline=S.GREEN, width=4)
    isz = h - 22
    icon = _icon(icon_src, isz)
    if not good:
        icon = Image.blend(Image.new("RGBA", icon.size, (0, 0, 0, 0)), icon, 0.55)
    img.alpha_composite(icon, (PAD + 16, PAD + 11))
    x = PAD + 16 + isz + 22
    col = S.TEXT_DARK if good else S.GRAY
    # крупно, если влезает в строку; иначе мельче, чтобы 2 строки уместились в карточку
    for size in (38, 32, 28):
        f = S.font(S.F_SEMIBOLD, size)
        lines = wrap(text, f, w - (x - PAD) - 90)
        lh = int(size * 1.2)
        if len(lines) * lh <= h - 16 and (len(lines) == 1 or size < 38):
            break
    y = PAD + (h - len(lines) * lh) // 2
    for line in lines:
        d.text((x, y), line, font=f, fill=col)
        if not good:
            tw = d.textlength(line, font=f)
            d.line([x - 4, y + lh * 0.55, x + tw + 4, y + lh * 0.55], fill=(214, 69, 65, 255), width=4)
        y += lh
    # значок справа
    cx, cy, r = PAD + w - 50, PAD + h // 2, 24
    if good:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=S.GREEN)
        d.line([cx - 11, cy + 1, cx - 3, cy + 9, cx + 12, cy - 9], fill=S.WHITE, width=6, joint="curve")
    else:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(253, 232, 231, 255))
        for s in (1, -1):
            d.line([cx - 9, cy - 9 * s, cx + 9, cy + 9 * s], fill=(214, 69, 65, 255), width=5)
    img.save(path)
    return path, PAD


def icon_trio(path, items, w=540, isz=110):
    """Одна карточка с 2-3 иконками в ряд и короткой подписью под каждой —
    вместо нескольких отдельных строк, всплывающих по одной (меньше мелькания)."""
    f = S.font(S.F_SEMIBOLD, 26)
    n = len(items)
    cell = (w - 40) // n
    h = 30 + isz + 16 + 40 + 26
    img = _card(w, h, S.WHITE, radius=24)
    d = ImageDraw.Draw(img)
    for k, (src, label) in enumerate(items):
        cx = PAD + 20 + cell * k + cell // 2
        img.alpha_composite(_icon(src, isz), (cx - isz // 2, PAD + 30))
        tw = d.textlength(label, font=f)
        d.text((cx - tw / 2, PAD + 30 + isz + 16), label, font=f, fill=S.TEXT_DARK)
    img.save(path)
    return path, PAD


# ---------------------------------------------------------------- приёмы сценария 6
# (другой набор подачи, чем в сценарии 5: реплики-пузыри, опоры-колонны,
# крупная цифра, картинки с отметкой ✗/✓, крупная нумерация порядка)

def _mark(d, cx, cy, r, good):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=S.GREEN if good else (224, 86, 86, 255))
    k = r * 0.45
    if good:
        d.line([(cx - k, cy + 0.05 * r), (cx - 0.1 * r, cy + k), (cx + k * 1.2, cy - k)], fill=S.WHITE,
               width=max(4, r // 5), joint="curve")
    else:
        d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=S.WHITE, width=max(4, r // 5))
        d.line([(cx - k, cy + k), (cx + k, cy - k)], fill=S.WHITE, width=max(4, r // 5))


def speech_bubble(path, text, w=620, size=48, color=S.BLUE, tail="left"):
    """Реплика-пузырь: цветной пузырь с хвостиком, белый крупный текст."""
    f = S.font(S.F_HEADLINE, size)
    lines = wrap(text, f, w - 80)
    lh = int(size * 1.2)
    h = 44 + len(lines) * lh + 30
    tail_h = 34
    img = Image.new("RGBA", (w + 2 * PAD, h + tail_h + 2 * PAD), (0, 0, 0, 0))
    shape = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shape)
    ds.rounded_rectangle([PAD, PAD, PAD + w, PAD + h], 40, fill=color)
    tx = PAD + 70 if tail == "left" else PAD + w - 70
    ds.polygon([(tx - 22, PAD + h - 2), (tx + 22, PAD + h - 2),
                (tx - 30 if tail == "left" else tx + 30, PAD + h + tail_h)], fill=color)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.paste((20, 40, 90, 50), (0, 8), shape.split()[3])
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    img = Image.alpha_composite(img, shape)
    d = ImageDraw.Draw(img)
    y = PAD + 36
    for line in lines:
        d.text((PAD + 40, y), line, font=f, fill=S.WHITE)
        y += lh
    img.save(path)
    return path, PAD


def pillars(path, items, w=1000, h=330, isz=130):
    """Опоры-колонны: N белых колонн рядом, в каждой иконка + номер + подпись."""
    n, gap = len(items), 28
    cw = (w - gap * (n - 1)) // n
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    f_n = S.font(S.F_SEMIBOLD, 24)
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    size = 34                         # общий размер подписей: самое длинное слово влезает в колонку
    while size > 22 and max(d0.textlength(wd, font=S.font(S.F_HEADLINE, size))
                            for _, lab in items for wd in lab.split()) > cw - 30:
        size -= 1
    f_t = S.font(S.F_HEADLINE, size)
    for i, (icon, label) in enumerate(items):
        x = PAD + i * (cw + gap)
        col = _card(cw, h, S.WHITE, radius=26)
        d = ImageDraw.Draw(col)
        d.rounded_rectangle([PAD, PAD, PAD + cw, PAD + 10], 5, fill=S.GREEN)
        col.alpha_composite(_icon(icon, isz), (PAD + (cw - isz) // 2, PAD + 38))
        num = f"0{i + 1}"
        d.text((PAD + (cw - d.textlength(num, font=f_n)) / 2, PAD + 38 + isz + 16), num, font=f_n, fill=S.LIGHT_BLUE)
        y = PAD + 38 + isz + 52
        for line in wrap(label, f_t, cw - 36):
            d.text((PAD + (cw - d.textlength(line, font=f_t)) / 2, y), line, font=f_t, fill=NAVY)
            y += 42
        img.alpha_composite(col, (x - PAD, 0))
    img.save(path)
    return path, PAD


def big_metric(path, number, unit, caption, w=1000):
    """Крупная цифра: огромное число + единица слева, пояснение справа."""
    f_num, f_unit, f_c = S.font(S.F_HEADLINE, 190), S.font(S.F_HEADLINE, 64), S.font(S.F_HEADLINE, 44)
    h = 230
    img = _card(w, h, S.BLUE, radius=30)
    d = ImageDraw.Draw(img)
    x = PAD + 50
    d.text((x, PAD - 18), number, font=f_num, fill=S.WHITE)
    x += d.textlength(number, font=f_num) + 16
    d.text((x, PAD + 110), unit, font=f_unit, fill=(214, 230, 255, 255))
    x += d.textlength(unit, font=f_unit) + 50
    d.rounded_rectangle([x, PAD + 50, x + 6, PAD + h - 50], 3, fill=S.GREEN)
    lines = wrap(caption, f_c, w - (x - PAD) - 60)
    y = PAD + (h - len(lines) * 54) / 2
    for line in lines:
        d.text((x + 34, y), line, font=f_c, fill=S.WHITE)
        y += 54
    img.save(path)
    return path, PAD


def marked_image(path, src, w, label, good):
    """Картинка с отметкой ✗/✓ в углу и подписью; «плохой» вариант приглушён."""
    im = Image.open(src).convert("RGBA")
    iw = w - 24
    ih = int(iw * im.height / im.width)
    im = ImageOps.fit(im, (iw, ih))
    if not good:
        im = Image.blend(im, ImageOps.grayscale(im).convert("RGBA"), 0.6)
    f = S.font(S.F_HEADLINE, 38)
    lines = wrap(label, f, iw - 30)
    h = 12 + ih + 18 + len(lines) * 48 + 16
    img = _card(w, h, S.WHITE, radius=24)
    mask = Image.new("L", (iw, ih), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, iw - 1, ih - 1], 16, fill=255)
    img.paste(im, (PAD + 12, PAD + 12), mask)
    d = ImageDraw.Draw(img)
    _mark(d, PAD + w - 50, PAD + 50, 34, good)
    y = PAD + 12 + ih + 16
    for line in lines:
        d.text((PAD + 22, y), line, font=f, fill=NAVY if good else S.GRAY)
        y += 48
    img.save(path)
    return path, PAD


def big_number(path, num, kicker, text, w=540, dim=False):
    """Крупная нумерация порядка: огромный номер + киккер + фраза, без карточки."""
    f_num, f_k, f_t = S.font(S.F_HEADLINE, 150), S.font(S.F_SEMIBOLD, 26), S.font(S.F_HEADLINE, 48)
    lines = wrap(text, f_t, w - 40)
    h = 150 + 44 + len(lines) * 58 + 30
    img = _card(w, h, (255, 255, 255, 235 if not dim else 170), radius=28)
    d = ImageDraw.Draw(img)
    col = S.BLUE if not dim else (170, 185, 210, 255)
    d.text((PAD + 34, PAD - 6), num, font=f_num, fill=col)
    d.text((PAD + 38, PAD + 160), kicker.upper(), font=f_k, fill=S.GREEN if not dim else S.GRAY)
    y = PAD + 198
    for line in lines:
        d.text((PAD + 36, y), line, font=f_t, fill=NAVY if not dim else S.GRAY)
        y += 58
    img.save(path)
    return path, PAD


def order_card(path, first, second, w=540):
    """Порядок «сначала → потом»: две строки с крупными номерами и стрелкой
    вниз между ними; вторая — спокойнее (она вторична)."""
    f_n, f_t = S.font(S.F_HEADLINE, 64), S.font(S.F_HEADLINE, 40)
    h = 300
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    for i, (num, text, col) in enumerate((("01", first, S.BLUE), ("02", second, S.GRAY))):
        y = PAD + 36 + i * 150
        d.text((PAD + 34, y - 8), num, font=f_n, fill=col)
        lines = wrap(text, f_t, w - 190)
        ty = y + (64 - len(lines) * 46) / 2
        for line in lines:
            d.text((PAD + 150, ty), line, font=f_t, fill=NAVY if i == 0 else S.GRAY)
            ty += 46
    ax, ay = PAD + 66, PAD + 128
    d.line([(ax, ay), (ax, ay + 44)], fill=S.GREEN, width=6)
    d.polygon([(ax - 14, ay + 36), (ax + 14, ay + 36), (ax, ay + 56)], fill=S.GREEN)
    img.save(path)
    return path, PAD


# ---------------------------------------------------------------- приёмы сценария 7
# (метки-ситуации, «ситуация → что делать», готовая фраза-скрипт, счётчик)

def tag_chips(path, items, w=540, isz=64, cols=2):
    """Метки-ситуации: плашки «иконка + короткое слово» сеткой в cols колонок."""
    gap, ch = 16, isz + 28
    cw = (w - gap * (cols - 1)) // cols
    rows = (len(items) + cols - 1) // cols
    h = rows * ch + (rows - 1) * gap
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    f = S.font(S.F_HEADLINE, 30)
    for i, (icon, label) in enumerate(items):
        x, y = PAD + (i % cols) * (cw + gap), PAD + (i // cols) * (ch + gap)
        chip = _card(cw, ch, S.WHITE, radius=ch // 2)
        chip.alpha_composite(_icon(icon, isz), (PAD + 14, PAD + 14))
        d = ImageDraw.Draw(chip)
        lines = wrap(label, f, cw - isz - 50)
        ty = PAD + (ch - len(lines) * 36) / 2
        for line in lines:
            d.text((PAD + isz + 30, ty), line, font=f, fill=NAVY)
            ty += 36
        img.alpha_composite(chip, (x - PAD, y - PAD))
    img.save(path)
    return path, PAD


def case_card(path, icon_src, situation, action, w=1000):
    """«Ситуация → что делать»: слева серая ситуация с иконкой, стрелка,
    справа синий блок с действием."""
    f_k, f_t = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 38)
    left_w = int(w * 0.44)
    right_w = w - left_w - 70
    ll, rl = wrap(situation, f_t, left_w - 150), wrap(action, f_t, right_w - 60)
    h = max(len(ll), len(rl)) * 46 + 110
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    img.alpha_composite(_icon(icon_src, 96), (PAD + 26, PAD + (h - 96) // 2))
    d.text((PAD + 140, PAD + 26), "СИТУАЦИЯ", font=f_k, fill=S.GRAY)
    y = PAD + 62
    for line in ll:
        d.text((PAD + 140, y), line, font=f_t, fill=NAVY)
        y += 46
    ax = PAD + left_w + 12
    d.polygon([(ax, PAD + h / 2 - 18), (ax + 30, PAD + h / 2), (ax, PAD + h / 2 + 18)], fill=S.GREEN)
    rx = PAD + left_w + 60
    d.rounded_rectangle([rx, PAD + 12, PAD + w - 12, PAD + h - 12], 22, fill=S.BLUE)
    d.text((rx + 30, PAD + 26), "ЧТО ДЕЛАТЬ", font=f_k, fill=(214, 230, 255, 255))
    y = PAD + 62
    for line in rl:
        d.text((rx + 30, y), line, font=f_t, fill=S.WHITE)
        y += 46
    img.save(path)
    return path, PAD


def script_card(path, label, text, w=1000, size=44):
    """Готовая фраза: белая карточка, зелёная полоса, метка «Скажите», текст
    фразы крупно в кавычках."""
    f_k, f_t = S.font(S.F_SEMIBOLD, 26), S.font(S.F_HEADLINE, size)
    lines = wrap(text, f_t, w - 150)
    lh = int(size * 1.25)
    h = 40 + 40 + len(lines) * lh + 34
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PAD, PAD, PAD + 12, PAD + h], 6, fill=S.GREEN)
    d.text((PAD + 50, PAD + 30), label.upper(), font=f_k, fill=S.GREEN)
    d.text((PAD + w - 110, PAD - 10), "”", font=S.font(S.F_HEADLINE, 150), fill=PALE_BLUE)
    y = PAD + 76
    for line in lines:
        d.text((PAD + 50, y), line, font=f_t, fill=NAVY)
        y += lh
    img.save(path)
    return path, PAD


def counter(path, big, small, w=540):
    """Счётчик: огромное «×100» и подпись под ним, без плашки-фона, в светлой карточке."""
    f_b, f_s = S.font(S.F_HEADLINE, 150), S.font(S.F_HEADLINE, 38)
    lines = wrap(small, f_s, w - 70)
    h = 170 + len(lines) * 48 + 40
    img = _card(w, h, (255, 255, 255, 240), radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 36, PAD + 4), big, font=f_b, fill=S.BLUE)
    y = PAD + 180
    for line in lines:
        d.text((PAD + 38, y), line, font=f_s, fill=NAVY)
        y += 48
    img.save(path)
    return path, PAD


# ---------------------------------------------------------------- приёмы сценария 8
# (размытые запросы, карточка вопросов, граница «фармацевт / врач», развилка,
# зачёркивание «не это — а это», итог галочками)

def _dashed_rrect(d, box, r, color, width=3, dash=14, gap=10):
    """Пунктирный скруглённый прямоугольник (прямые участки пунктиром, углы — дугами)."""
    x0, y0, x1, y1 = box
    for a, b, fixed, horiz in ((x0 + r, x1 - r, y0, True), (x0 + r, x1 - r, y1, True),
                               (y0 + r, y1 - r, x0, False), (y0 + r, y1 - r, x1, False)):
        p = a
        while p < b:
            q = min(p + dash, b)
            d.line([(p, fixed), (q, fixed)] if horiz else [(fixed, p), (fixed, q)], fill=color, width=width)
            p = q + gap
    for cx, cy, st in ((x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90)):
        d.arc([cx - r, cy - r, cx + r, cy + r], st, st + 90, fill=color, width=width)


def fuzzy_chips(path, items, w=540, isz=72):
    """Расплывчатые запросы: реплики в кавычках на полупрозрачных плашках с
    пунктирной рамкой — «неточно», в отличие от чётких белых карточек."""
    size = 36
    while size > 24 and max(d0_len(f"«{t}»", S.font(S.F_HEADLINE, size)) for _, t in items) > w - isz - 70:
        size -= 1
    f = S.font(S.F_HEADLINE, size)
    ch, gap = isz + 32, 18
    h = len(items) * ch + (len(items) - 1) * gap
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    for i, (icon, text) in enumerate(items):
        y = PAD + i * (ch + gap)
        chip = Image.new("RGBA", (w, ch), (0, 0, 0, 0))
        d = ImageDraw.Draw(chip)
        d.rounded_rectangle([0, 0, w - 1, ch - 1], ch // 2, fill=(255, 255, 255, 205))
        _dashed_rrect(d, [2, 2, w - 3, ch - 3], ch // 2 - 2, (140, 160, 195, 255))
        ic = _icon(icon, isz)
        ic.putalpha(ic.getchannel("A").point(lambda v: v * 80 // 100))
        chip.alpha_composite(ic, (16, 16))
        d.text((isz + 40, (ch - size * 1.2) // 2), f"«{text}»", font=f, fill=(88, 100, 125, 255))
        img.alpha_composite(chip, (PAD, y))
    img.save(path)
    return path, PAD


def question_card(path, kicker, items, w=640, isz=86):
    """Карточка вопросов: киккер + строки «иконка + вопрос?» с зелёной меткой «?»
    слева — перечень вопросов одной волной."""
    f_k, f_q = S.font(S.F_SEMIBOLD, 26), S.font(S.F_HEADLINE, 40)
    row = isz + 26
    h = 36 + 40 + len(items) * row + 20
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 36, PAD + 30), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y = PAD + 80
    for icon, q in items:
        cy = y + isz // 2
        d.ellipse([PAD + 30, cy - 22, PAD + 74, cy + 22], fill=S.GREEN)
        f_m = S.font(S.F_HEADLINE, 30)
        d.text((PAD + 52 - d.textlength("?", font=f_m) / 2, cy - 19), "?", font=f_m, fill=S.WHITE)
        img.alpha_composite(_icon(icon, isz), (PAD + 92, y))
        d.text((PAD + 92 + isz + 24, cy - 26), q, font=f_q, fill=NAVY)
        y += row
    img.save(path)
    return path, PAD


def boundary_card(path, left_icon, left_kicker, left_text, right_icon, right_kicker, right_text, w=1200):
    """Граница ответственности: слева — зона «ваше» (синяя), справа за
    вертикальной чертой — «не ваше» (серая, зачёркнутый значок)."""
    f_k, f_t = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 38)
    half = (w - 60) // 2
    ll, rl = wrap(left_text, f_t, half - 170), wrap(right_text, f_t, half - 170)
    h = max(len(ll), len(rl)) * 46 + 110
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PAD + 12, PAD + 12, PAD + half, PAD + h - 12], 22, fill=PALE_BLUE)
    for x, icon, kick, lines, col, kcol in ((PAD + 12, left_icon, left_kicker, ll, NAVY, S.BLUE),
                                            (PAD + half + 60, right_icon, right_kicker, rl, S.GRAY, S.GRAY)):
        ic = _icon(icon, 96)
        if col == S.GRAY:
            ic = Image.blend(Image.new("RGBA", ic.size, (0, 0, 0, 0)), ic, 0.55)
        img.alpha_composite(ic, (x + 24, PAD + (h - 96) // 2))
        d.text((x + 140, PAD + 28), kick.upper(), font=f_k, fill=kcol)
        y = PAD + 64
        for line in lines:
            d.text((x + 140, y), line, font=f_t, fill=col)
            y += 46
    # черта-граница
    bx = PAD + half + 30
    for yy in range(PAD + 18, PAD + h - 18, 22):
        d.line([(bx, yy), (bx, min(yy + 12, PAD + h - 18))], fill=(214, 69, 65, 255), width=5)
    # перечёркнутый кружок на правой иконке
    cx, cy = PAD + half + 60 + 24 + 48, PAD + h // 2
    d.ellipse([cx - 52, cy - 52, cx + 52, cy + 52], outline=(214, 69, 65, 255), width=6)
    d.line([(cx - 36, cy + 36), (cx + 36, cy - 36)], fill=(214, 69, 65, 255), width=6)
    img.save(path)
    return path, PAD


def fork_card(path, root, left, right, w=1200):
    """Развилка: сверху корень (синяя плашка), от него две ветки вниз —
    left/right = (icon, kicker, text, color)."""
    f_r, f_k, f_t = S.font(S.F_HEADLINE, 38), S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 36)
    bw = (w - 60) // 2
    lines = [wrap(t, f_t, bw - 170) for _, _, t, _ in (left, right)]
    bh = max(len(x) for x in lines) * 44 + 100
    rw = int(d0_len(root, f_r)) + 100
    rh, gap = 84, 70
    h = rh + gap + bh
    img = Image.new("RGBA", (w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    rx = PAD + (w - rw) // 2
    img.alpha_composite(_card(rw, rh, S.BLUE, radius=rh // 2), (rx - PAD, 0))
    d = ImageDraw.Draw(img)
    d.text((rx + 50, PAD + (rh - 46) // 2), root, font=f_r, fill=S.WHITE)
    # ветки: от низа корня вниз, затем в стороны
    cx, y0, ym = PAD + w // 2, PAD + rh, PAD + rh + gap // 2
    lx, rx2 = PAD + bw // 2, PAD + w - bw // 2
    for a, b in (((cx, y0), (cx, ym)), ((lx, ym), (rx2, ym)), ((lx, ym), (lx, PAD + rh + gap)),
                 ((rx2, ym), (rx2, PAD + rh + gap))):
        d.line([a, b], fill=S.LIGHT_BLUE, width=5)
    for k, ((icon, kick, _, col), ls) in enumerate(zip((left, right), lines)):
        x = PAD + k * (bw + 60)
        box = _card(bw, bh, S.WHITE, radius=26)
        db = ImageDraw.Draw(box)
        db.rounded_rectangle([PAD, PAD, PAD + bw, PAD + bh], 26, outline=col, width=4)
        box.alpha_composite(_icon(icon, 100), (PAD + 22, PAD + (bh - 100) // 2))
        db.text((PAD + 144, PAD + 24), kick.upper(), font=f_k, fill=col)
        y = PAD + 58
        for line in ls:
            db.text((PAD + 144, y), line, font=f_t, fill=NAVY)
            y += 44
        img.alpha_composite(box, (x - PAD, rh + gap))
    img.save(path)
    return path, PAD


def d0_len(text, font):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(text, font=font)


def strike_card(path, wrong, right, w=540):
    """«Не это — а это»: зачёркнутые серые слова столбиком, под ними — верное
    слово крупно зелёным на светло-зелёной плашке."""
    f_w, f_r = S.font(S.F_HEADLINE, 46), S.font(S.F_HEADLINE, 64)
    h = 40 + len(wrong) * 64 + 20 + 110 + 36
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    y = PAD + 36
    for word in wrong:
        d.text((PAD + 44, y), word, font=f_w, fill=S.GRAY)
        tw = d.textlength(word, font=f_w)
        d.line([(PAD + 36, y + 38), (PAD + 52 + tw, y + 34)], fill=(214, 69, 65, 255), width=6)
        y += 64
    y += 20
    d.rounded_rectangle([PAD + 28, y, PAD + w - 28, y + 110], 22, fill=(226, 245, 234, 255))
    _mark(d, PAD + 84, y + 55, 30, True)
    d.text((PAD + 136, y + 18), right, font=f_r, fill=S.GREEN)
    img.save(path)
    return path, PAD


def ticks_card(path, kicker, items, w=640):
    """Итог галочками: киккер и 2-4 строки с зелёной галочкой — одной волной."""
    f_k, f_t = S.font(S.F_SEMIBOLD, 26), S.font(S.F_HEADLINE, 38)
    rows = [wrap(t, f_t, w - 150) for t in items]
    h = 36 + 44 + sum(len(r) * 46 + 22 for r in rows) + 20
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 36, PAD + 30), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y = PAD + 84
    for r in rows:
        _mark(d, PAD + 62, y + 23, 22, True)
        for line in r:
            d.text((PAD + 104, y), line, font=f_t, fill=NAVY)
            y += 46
        y += 22
    img.save(path)
    return path, PAD


# ---------------------------------------------------------------- приёмы сценария 9
# (воронка из уровней с пояснениями «зачем», пара «вопрос о человеке / о товаре»,
# карточка тревожных признаков, формула «3 вопроса + полминуты = точная помощь»)

AMBER = (230, 140, 30, 255)
PALE_AMBER = (253, 241, 222, 255)


def _fit_font(text, path, sizes, max_w):
    for size in sizes:
        f = S.font(path, size)
        if d0_len(text, f) <= max_w:
            return f
    return S.font(path, sizes[-1])


def funnel_level(path, num, top_w, bot_w, h, icon_src, kicker, text, color):
    """Уровень воронки: цветная трапеция (сужается книзу), номер, иконка,
    киккер и вопрос-цитата белым. Уровни ставятся друг под другом по центру."""
    img = Image.new("RGBA", (top_w + 2 * PAD, h + 2 * PAD), (0, 0, 0, 0))
    cx = PAD + top_w / 2
    poly = [(cx - top_w / 2, PAD), (cx + top_w / 2, PAD), (cx + bot_w / 2, PAD + h), (cx - bot_w / 2, PAD + h)]
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x, y + 8) for x, y in poly], fill=SHADOW)
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.polygon(poly, fill=color)
    inset = (top_w - bot_w) / 2 + 26
    x = PAD + inset
    isz = h - 56
    d.ellipse([x - 4, PAD + 24, x + isz + 4, PAD + 32 + isz], fill=S.WHITE)
    img.alpha_composite(_icon(icon_src, isz), (int(x), PAD + 28))
    # номер на иконке
    ncx, ncy = int(x + isz - 4), PAD + 34
    d.ellipse([ncx - 20, ncy - 20, ncx + 20, ncy + 20], fill=NAVY, outline=S.WHITE, width=3)
    f_n = S.font(S.F_SEMIBOLD, 22)
    d.text((ncx - d.textlength(num, font=f_n) / 2, ncy - 14), num, font=f_n, fill=S.WHITE)
    tx = x + isz + 26
    max_w = PAD + top_w - inset - tx
    d.text((tx, PAD + 30), kicker.upper(), font=S.font(S.F_SEMIBOLD, 22), fill=(225, 236, 255, 255))
    f_t = _fit_font(text, S.F_HEADLINE, (38, 34, 30, 28), max_w)
    d.text((tx, PAD + 64), text, font=f_t, fill=S.WHITE)
    img.save(path)
    return path, PAD


def why_note(path, text, w=440, h=110, color=S.BLUE):
    """Пояснение «зачем» к уровню воронки: стрелка-треугольник слева
    указывает на уровень, белая плашка с текстом."""
    img = _card(w, h, S.WHITE, radius=22)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PAD, PAD, PAD + 10, PAD + h], 5, fill=color)
    d.polygon([(PAD + 30, PAD + h // 2 - 14), (PAD + 30, PAD + h // 2 + 14), (PAD + 48, PAD + h // 2)],
              fill=color)
    f = S.font(S.F_SEMIBOLD, 32)
    lines = wrap(text, f, w - 90)
    if len(lines) > 2:
        f = S.font(S.F_SEMIBOLD, 28)
        lines = wrap(text, f, w - 90)
    lh = int(f.size * 1.22)
    y = PAD + (h - len(lines) * lh) // 2
    for line in lines:
        d.text((PAD + 66, y), line, font=f, fill=NAVY)
        y += lh
    img.save(path)
    return path, PAD


def ask_type_card(path, icon_src, kicker, question, result, good, w=540):
    """Тип вопроса: иконка + киккер, вопрос в пузыре, стрелка вниз и итог —
    зелёный «✓» (помогает) или серый (не про человека)."""
    col = S.GREEN if good else S.GRAY
    f_k, f_q, f_r = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 40), S.font(S.F_HEADLINE, 34)
    q_lines = wrap(question, f_q, w - 100)
    r_lines = wrap(result, f_r, w - 150)
    isz = 84
    bub_h = len(q_lines) * 48 + 40
    res_h = max(86, len(r_lines) * 42 + 36)
    h = 30 + isz + 22 + bub_h + 60 + res_h + 28
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    icon = _icon(icon_src, isz)
    if not good:
        icon = Image.blend(Image.new("RGBA", icon.size, (0, 0, 0, 0)), icon, 0.6)
    img.alpha_composite(icon, (PAD + 30, PAD + 30))
    d.text((PAD + 30 + isz + 20, PAD + 30 + isz // 2 - 16), kicker.upper(), font=f_k,
           fill=S.BLUE if good else S.GRAY)
    y = PAD + 30 + isz + 22
    bub = PALE_BLUE if good else (238, 240, 243, 255)
    d.rounded_rectangle([PAD + 30, y, PAD + w - 30, y + bub_h], 22, fill=bub)
    d.polygon([(PAD + 60, y), (PAD + 90, y), (PAD + 66, y - 18)], fill=bub)
    yy = y + 20
    for line in q_lines:
        d.text((PAD + 54, yy), line, font=f_q, fill=NAVY if good else S.GRAY)
        yy += 48
    y += bub_h
    # стрелка вниз
    ax = PAD + w // 2
    d.line([(ax, y + 10), (ax, y + 46)], fill=col, width=6)
    d.polygon([(ax - 14, y + 40), (ax + 14, y + 40), (ax, y + 56)], fill=col)
    y += 60
    d.rounded_rectangle([PAD + 30, y, PAD + w - 30, y + res_h], 22,
                        fill=(226, 245, 234, 255) if good else (238, 240, 243, 255))
    if good:
        _mark(d, PAD + 76, y + res_h // 2, 26, True)
    else:
        d.ellipse([PAD + 50, y + res_h // 2 - 26, PAD + 102, y + res_h // 2 + 26], fill=(205, 209, 216, 255))
        d.text((PAD + 76 - d.textlength("₽", font=f_r) / 2, y + res_h // 2 - 22), "₽", font=f_r, fill=S.WHITE)
    yy = y + (res_h - len(r_lines) * 42) // 2 - 2
    for line in r_lines:
        d.text((PAD + 124, yy), line, font=f_r, fill=S.GREEN if good else S.GRAY)
        yy += 42
    img.save(path)
    return path, PAD


def alert_card(path, items, w=640):
    """Тревожные признаки: янтарная карточка, строки с восклицательным знаком
    в треугольнике — одной волной."""
    f_t = S.font(S.F_HEADLINE, 38)
    rows = [wrap(t, f_t, w - 150) for t in items]
    h = 34 + sum(len(r) * 46 + 26 for r in rows) + 8
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PAD, PAD, PAD + w, PAD + h], 28, outline=AMBER, width=4)
    d.rounded_rectangle([PAD, PAD, PAD + 14, PAD + h], 7, fill=AMBER)
    y = PAD + 34
    for r in rows:
        cx, cy = PAD + 70, y + 23
        d.polygon([(cx, cy - 24), (cx + 26, cy + 20), (cx - 26, cy + 20)], fill=PALE_AMBER, outline=AMBER)
        d.polygon([(cx, cy - 22), (cx + 24, cy + 19), (cx - 24, cy + 19)], outline=AMBER, width=4)
        d.line([(cx, cy - 8), (cx, cy + 6)], fill=AMBER, width=5)
        d.ellipse([cx - 3, cy + 10, cx + 3, cy + 16], fill=AMBER)
        for line in r:
            d.text((PAD + 116, y), line, font=f_t, fill=NAVY)
            y += 46
        y += 26
    img.save(path)
    return path, PAD


def formula_card(path, terms, result, w=540):
    """Формула столбиком: слагаемые «крупное + подпись» и итог «= …» на
    зелёной плашке — вывод одной карточкой."""
    f_big, f_sm, f_op = S.font(S.F_HEADLINE, 64), S.font(S.F_SEMIBOLD, 34), S.font(S.F_HEADLINE, 50)
    f_r = S.font(S.F_HEADLINE, 44)
    row = 84
    res_h = 104
    h = 30 + len(terms) * row + 16 + res_h + 30
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    y = PAD + 30
    for k, (big, small) in enumerate(terms):
        if k:
            d.text((PAD + 36, y + 6), "+", font=f_op, fill=S.LIGHT_BLUE)
        d.text((PAD + 90, y), big, font=f_big, fill=S.BLUE)
        bw = d.textlength(big, font=f_big)
        d.text((PAD + 90 + bw + 18, y + 24), small, font=f_sm, fill=NAVY)
        y += row
    y += 16
    d.rounded_rectangle([PAD + 24, y, PAD + w - 24, y + res_h], 24, fill=S.GREEN)
    d.text((PAD + 44, y + 22), "=", font=f_op, fill=S.WHITE)
    d.text((PAD + 100, y + 26), result, font=f_r, fill=S.WHITE)
    img.save(path)
    return path, PAD


# ---------------------------------------------------------------- приёмы сценария 10
# («кажется / на деле», фраза с разметкой частей, «поток вопросов / по одному»,
# ползунки тона для деликатных тем)

PALE_GREEN = (226, 245, 234, 255)
PALE_GRAY = (238, 240, 243, 255)
RED = (214, 69, 65, 255)


def myth_fact(path, fact, text, w=540):
    """Строка «кажется / на деле»: метка-плашка сверху и крупный текст.
    fact=False — серая «Кажется» (ложное впечатление), True — зелёная «На деле»."""
    tag = "На деле" if fact else "Кажется"
    f_tag, f_t = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 44 if fact else 40)
    lines = wrap(text, f_t, w - 90)
    lh = int(f_t.size * 1.18)
    h = 30 + 42 + 18 + len(lines) * lh + 30
    img = _card(w, h, S.WHITE if fact else (250, 251, 252, 255), radius=26)
    d = ImageDraw.Draw(img)
    col = S.GREEN if fact else S.GRAY
    if fact:
        d.rounded_rectangle([PAD, PAD, PAD + w, PAD + h], 26, outline=S.GREEN, width=4)
    tw = d.textlength(tag.upper(), font=f_tag)
    d.rounded_rectangle([PAD + 36, PAD + 30, PAD + 36 + tw + 36, PAD + 72], 21,
                        fill=PALE_GREEN if fact else PALE_GRAY)
    d.text((PAD + 54, PAD + 38), tag.upper(), font=f_tag, fill=col)
    y = PAD + 30 + 42 + 18
    for line in lines:
        d.text((PAD + 40, y), line, font=f_t, fill=NAVY if fact else S.GRAY)
        y += lh
    img.save(path)
    return path, PAD


def annotated_phrase(path, kicker, segments, w=640):
    """Готовая фраза, разобранная на части: каждая часть — своя строка
    с цветным подчёркиванием и подписью «что это даёт» под ним."""
    f_k, f_t, f_l = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 40), S.font(S.F_SEMIBOLD, 26)
    blocks = [(wrap(t, f_t, w - 80), lab, col) for t, lab, col in segments]
    h = 34 + 40 + sum(len(ls) * 50 + 14 + 40 + 22 for ls, _, _ in blocks) + 14
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 40, PAD + 32), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y = PAD + 34 + 40
    for lines, lab, col in blocks:
        maxw = 0
        for line in lines:
            d.text((PAD + 40, y), line, font=f_t, fill=NAVY)
            maxw = max(maxw, d.textlength(line, font=f_t))
            y += 50
        d.rounded_rectangle([PAD + 40, y + 2, PAD + 40 + maxw, y + 10], 4, fill=col)
        y += 14
        tw = d.textlength(lab, font=f_l)
        pale = PALE_GREEN if col == S.GREEN else PALE_BLUE
        d.rounded_rectangle([PAD + 40, y, PAD + 40 + tw + 32, y + 40], 20, fill=pale)
        d.text((PAD + 56, y + 5), lab, font=f_l, fill=col)
        y += 40 + 22
    img.save(path)
    return path, PAD


def _qdot(d, cx, cy, r, fill, text="?", size=None, color=S.WHITE):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=S.WHITE, width=3)
    f = S.font(S.F_HEADLINE, size or int(r * 1.2))
    d.text((cx - d.textlength(text, font=f) / 2, cy - f.size * 0.62), text, font=f, fill=color)


def flood_card(path, count, label, w=620):
    """«Поток вопросов подряд»: count кружков «?» налезают друг на друга,
    перечёркнуты; справа — к чему это приводит (серым)."""
    h = 150
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    r, step = 30, 40
    x0, cy = PAD + 36 + r, PAD + h // 2
    for k in range(count):
        _qdot(d, x0 + k * step, cy + (-10 if k % 2 else 10), r, (150, 160, 178, 255))
    x_end = x0 + (count - 1) * step + r
    d.line([(x0 - r - 6, cy + 30), (x_end + 6, cy - 30)], fill=RED, width=7)
    f = S.font(S.F_HEADLINE, 36)
    tx = x_end + 32
    lines = wrap(label, f, PAD + w - 30 - tx)
    y = cy - len(lines) * 24
    for line in lines:
        d.text((tx, y), line, font=f, fill=S.GRAY)
        y += 48
    img.save(path)
    return path, PAD


def beat_line(path, beats, w=620):
    """Ритм разговора по одному: узлы на линии времени (вопрос → пауза →
    ответ → второй вопрос); пауза — пустое кольцо, вопрос/ответ — кружки."""
    f_l = S.font(S.F_SEMIBOLD, 26)
    h = 200
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    n = len(beats)
    x0, x1, cy = PAD + 80, PAD + w - 80, PAD + 78
    d.line([(x0, cy), (x1, cy)], fill=(210, 222, 240, 255), width=6)
    for k, (kind, label) in enumerate(beats):
        cx = x0 + (x1 - x0) * k / (n - 1)
        if kind == "pause":
            d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=S.WHITE, outline=S.LIGHT_BLUE, width=5)
            for j in (-9, 0, 9):
                d.ellipse([cx + j - 3, cy - 3, cx + j + 3, cy + 3], fill=S.LIGHT_BLUE)
        elif kind == "answer":
            _qdot(d, cx, cy, 36, S.GREEN, "…", 44)
        else:
            _qdot(d, cx, cy, 36, S.BLUE if kind == "q" else S.LIGHT_BLUE)
        tw = d.textlength(label, font=f_l)
        d.text((cx - tw / 2, cy + 54), label, font=f_l, fill=NAVY if kind != "pause" else S.LIGHT_BLUE)
    img.save(path)
    return path, PAD


def tone_sliders(path, kicker, rows, w=540):
    """Настройка тона: строки «параметр — ползунок — значение»; ручка ползунка
    стоит на нужной отметке (pos 0..1), значение — зелёным."""
    f_k, f_n, f_v = S.font(S.F_SEMIBOLD, 24), S.font(S.F_SEMIBOLD, 28), S.font(S.F_HEADLINE, 36)
    row_h = 118
    h = 34 + 40 + len(rows) * row_h + 10
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 36, PAD + 32), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y = PAD + 34 + 40
    for name, value, pos in rows:
        d.text((PAD + 36, y + 4), name, font=f_n, fill=S.GRAY)
        vw = d.textlength(value, font=f_v)
        d.text((PAD + w - 36 - vw, y - 2), value, font=f_v, fill=S.GREEN)
        ty = y + 70
        tx0, tx1 = PAD + 36, PAD + w - 36
        d.rounded_rectangle([tx0, ty - 5, tx1, ty + 5], 5, fill=(222, 230, 242, 255))
        kx = tx0 + (tx1 - tx0) * pos
        d.rounded_rectangle([tx0, ty - 5, kx, ty + 5], 5, fill=S.LIGHT_BLUE)
        d.ellipse([kx - 17, ty - 17, kx + 17, ty + 17], fill=S.WHITE, outline=S.BLUE, width=6)
        y += row_h
    img.save(path)
    return path, PAD


# ---------------------------------------------------------------- приёмы сценария 11
# (две роли «продавец / фармацевт», пары «средство + дополнение», шкала
# «половина / полное решение», правило-таймлайн, «человек слышит», «≠»)

def _pill(d, x, y, text, font, fill, color, pad_x=22, h=48):
    tw = d.textlength(text, font=font)
    d.rounded_rectangle([x, y, x + tw + 2 * pad_x, y + h], h // 2, fill=fill)
    d.text((x + pad_x, y + (h - font.size) / 2 - 3), text, font=font, fill=color)
    return tw + 2 * pad_x


def role_card(path, icon_src, role, text, chips=(), accent=False, w=540, isz=120):
    """Карточка роли: иконка + метка роли + крупная фраза; у акцентной роли —
    синяя рамка и зелёные чипы (что именно она делает)."""
    f_r, f_t, f_c = S.font(S.F_SEMIBOLD, 26), S.font(S.F_HEADLINE, 40), S.font(S.F_SEMIBOLD, 28)
    x_t = 36 + isz + 26
    lines = wrap(text, f_t, w - x_t - 30)
    lh = 50
    top = max(isz, 44 + len(lines) * lh)
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    chip_rows, cur, cw = [], [], 0
    for c in chips:
        pw = d0.textlength(c, font=f_c) + 44
        if cur and cw + pw > w - 72:
            chip_rows.append(cur)
            cur, cw = [], 0
        cur.append(c)
        cw += pw + 12
    if cur:
        chip_rows.append(cur)
    h = 34 + top + (30 + len(chip_rows) * 60 - 12 if chips else 0) + 34
    img = _card(w, h, S.WHITE if accent else (250, 251, 252, 255), radius=28)
    d = ImageDraw.Draw(img)
    if accent:
        d.rounded_rectangle([PAD, PAD, PAD + w, PAD + h], 28, outline=S.BLUE, width=4)
    ic = _icon(icon_src, isz)
    if not accent:
        ic = ImageOps.grayscale(ic.convert("RGB")).convert("RGBA")
        ic.putalpha(_icon(icon_src, isz).getchannel("A"))
    img.alpha_composite(ic, (PAD + 36, PAD + 34))
    x, y = PAD + x_t, PAD + 34
    d.text((x, y), role.upper(), font=f_r, fill=S.BLUE if accent else S.GRAY)
    y += 44
    for line in lines:
        d.text((x, y), line, font=f_t, fill=NAVY if accent else S.GRAY)
        y += lh
    cy = PAD + 34 + top + 30
    for row in chip_rows:
        cx = PAD + 36
        for c in row:
            cx += _pill(d, cx, cy, c, f_c, PALE_GREEN, S.GREEN) + 12
        cy += 60
    img.save(path)
    return path, PAD


def stamp(path, text, size=34):
    """Зелёная плашка-итог с галочкой (вывод к карточке над ней)."""
    f = S.font(S.F_HEADLINE, size)
    tw = d0_len(text, f)
    h = size + 44
    w = int(tw + h + 60)
    img = _card(w, h, S.GREEN, radius=h // 2)
    d = ImageDraw.Draw(img)
    r = h // 2 - 12
    d.ellipse([PAD + 12, PAD + 12, PAD + 12 + 2 * r, PAD + 12 + 2 * r], fill=S.WHITE)
    k = r * 0.45
    cx, cy = PAD + 12 + r, PAD + 12 + r
    d.line([(cx - k, cy + 0.05 * r), (cx - 0.1 * r, cy + k), (cx + k * 1.2, cy - k)], fill=S.GREEN, width=5,
           joint="curve")
    d.text((PAD + h + 14, PAD + (h - size) / 2 - 5), text, font=f, fill=S.WHITE)
    img.save(path)
    return path, PAD


def plus_combo(path, left, right, w=640, isz=96):
    """Пара «основное + дополнение»: две половины с иконкой и подписью,
    между ними зелёный «+»; левая — серо-голубая (то, что попросили),
    правая — с зелёной рамкой (то, что добавил фармацевт)."""
    f_t = S.font(S.F_SEMIBOLD, 28)
    gap = 70
    cw = (w - 40 - gap) // 2
    ls = [wrap(t, f_t, cw - 20) for _, t in (left, right)]
    h = 24 + isz + 14 + max(len(x) for x in ls) * 36 + 24
    img = _card(w, h, S.WHITE, radius=26)
    d = ImageDraw.Draw(img)
    for k, ((src, _), lines) in enumerate(zip((left, right), ls)):
        x0 = PAD + 20 + k * (cw + gap)
        if k:
            d.rounded_rectangle([x0 - 6, PAD + 12, x0 + cw + 6, PAD + h - 12], 20, fill=PALE_GREEN)
        else:
            d.rounded_rectangle([x0 - 6, PAD + 12, x0 + cw + 6, PAD + h - 12], 20, fill=PALE_BLUE)
        img.alpha_composite(_icon(src, isz), (int(x0 + (cw - isz) / 2), PAD + 24))
        y = PAD + 24 + isz + 14
        for line in lines:
            tw = d.textlength(line, font=f_t)
            d.text((x0 + (cw - tw) / 2, y), line, font=f_t, fill=NAVY if not k else S.GREEN)
            y += 36
    cx, cy = PAD + 20 + cw + gap // 2, PAD + h // 2
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=S.GREEN)
    d.line([(cx - 12, cy), (cx + 12, cy)], fill=S.WHITE, width=7)
    d.line([(cx, cy - 12), (cx, cy + 12)], fill=S.WHITE, width=7)
    img.save(path)
    return path, PAD


def completeness_bars(path, rows, w=640):
    """Шкалы полноты: строки (подпись, доля 0..1, хорошая?, пометка справа).
    Неполная — серая наполовину пустая полоса, полная — зелёная до конца."""
    f_l, f_n = S.font(S.F_HEADLINE, 38), S.font(S.F_SEMIBOLD, 28)
    row_h = 136
    h = 30 + sum(row_h + (42 if r[3] else 0) for r in rows) + 6
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    y = PAD + 30
    for label, frac, good, note in rows:
        col = S.GREEN if good else S.GRAY
        d.text((PAD + 36, y), label, font=f_l, fill=NAVY if good else S.GRAY)
        by = y + 64
        x0, x1 = PAD + 36, PAD + w - 36
        d.rounded_rectangle([x0, by, x1, by + 30], 15, fill=(230, 235, 242, 255))
        d.rounded_rectangle([x0, by, x0 + (x1 - x0) * frac, by + 30], 15, fill=col)
        if not good:
            xm = x0 + (x1 - x0) * frac
            for xx in range(int(xm) + 14, int(x1) - 6, 22):
                d.line([(xx, by + 6), (xx + 8, by + 24)], fill=(205, 212, 222, 255), width=3)
        if note:
            nw = d.textlength(note, font=f_n)
            d.text((PAD + w - 36 - nw, by + 44), note, font=f_n, fill=col)
        y += row_h + (42 if note else 0)
    img.save(path)
    return path, PAD


def rule_timeline(path, kicker, steps, w=1200, isz=110):
    """Правило-порядок: узлы-иконки на линии слева направо, под каждым —
    номер и подпись; первый узел — «замок» порядка (зелёная рамка)."""
    f_k, f_t, f_n = S.font(S.F_SEMIBOLD, 24), S.font(S.F_SEMIBOLD, 30), S.font(S.F_SEMIBOLD, 22)
    n = len(steps)
    colw = (w - 80) / n
    ls = [wrap(t, f_t, colw - 30) for _, t in steps]
    h = 30 + 36 + isz + 20 + 34 + max(len(x) for x in ls) * 38 + 26
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 40, PAD + 28), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    cy = PAD + 30 + 36 + isz // 2
    xs = [PAD + 40 + colw * (k + 0.5) for k in range(n)]
    d.line([(xs[0], cy), (xs[-1], cy)], fill=(210, 222, 240, 255), width=6)
    for k in range(n - 1):
        ax = (xs[k] + xs[k + 1]) / 2
        d.polygon([(ax + 12, cy), (ax - 8, cy - 12), (ax - 8, cy + 12)], fill=S.LIGHT_BLUE)
    for k, ((src, _), lines) in enumerate(zip(steps, ls)):
        x = xs[k]
        ring = S.GREEN if k == 0 else S.WHITE
        d.ellipse([x - isz / 2 - 7, cy - isz / 2 - 7, x + isz / 2 + 7, cy + isz / 2 + 7], fill=ring)
        img.alpha_composite(_icon(src, isz), (int(x - isz / 2), int(cy - isz / 2)))
        y = cy + isz / 2 + 20
        num = f"{k + 1}"
        d.ellipse([x - 17, y, x + 17, y + 34], fill=S.GREEN if k == 0 else S.BLUE)
        d.text((x - d.textlength(num, font=f_n) / 2, y + 4), num, font=f_n, fill=S.WHITE)
        y += 46
        for line in lines:
            d.text((x - d.textlength(line, font=f_t) / 2, y), line, font=f_t, fill=NAVY)
            y += 38
    img.save(path)
    return path, PAD


def heard_as(path, icon_src, kicker, good, bad, w=640, isz=110):
    """«Как это слышит человек»: иконка + киккер, крупно зелёным — верное
    восприятие, ниже серым зачёркнутым — то, как звучать не должно."""
    f_k, f_g, f_b = S.font(S.F_SEMIBOLD, 26), S.font(S.F_HEADLINE, 46), S.font(S.F_HEADLINE, 36)
    x_t = 36 + isz + 26
    g_lines = wrap(good, f_g, w - x_t - 30)
    h = 30 + 40 + len(g_lines) * 56 + 20 + 50 + 30
    h = max(h, isz + 60)
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    img.alpha_composite(_icon(icon_src, isz), (PAD + 36, PAD + (h - isz) // 2))
    x, y = PAD + x_t, PAD + 30
    d.text((x, y), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y += 40
    for line in g_lines:
        d.text((x, y), line, font=f_g, fill=S.GREEN)
        y += 56
    y += 20
    d.text((x, y), bad, font=f_b, fill=S.GRAY)
    tw = d.textlength(bad, font=f_b)
    d.line([(x - 6, y + 26), (x + tw + 6, y + 22)], fill=RED, width=5)
    img.save(path)
    return path, PAD


def not_equal(path, icon_src, left, right, result, w=540, isz=96):
    """«A ≠ B» крупно (A с иконкой), под чертой — «= на самом деле» янтарным."""
    f_w, f_op, f_r = S.font(S.F_HEADLINE, 44), S.font(S.F_HEADLINE, 60), S.font(S.F_HEADLINE, 38)
    amber = (224, 138, 30, 255)
    r_lines = wrap(result, f_r, w - 150)
    h = 30 + isz + 10 + 70 + 24 + len(r_lines) * 48 + 40
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    y = PAD + 30
    img.alpha_composite(_icon(icon_src, isz), (PAD + 36, y))
    d.text((PAD + 36 + isz + 24, y + isz / 2 - 30), left, font=f_w, fill=NAVY)
    y += isz + 10
    d.text((PAD + 44, y - 4), "≠", font=f_op, fill=RED)
    d.text((PAD + 120, y + 8), right, font=f_w, fill=S.GRAY)
    y += 70 + 12
    d.rounded_rectangle([PAD + 24, y, PAD + w - 24, y + len(r_lines) * 48 + 28], 22, fill=(253, 240, 222, 255))
    d.text((PAD + 44, y + 6), "=", font=f_op, fill=amber)
    yy = y + 14
    for line in r_lines:
        d.text((PAD + 110, yy), line, font=f_r, fill=amber)
        yy += 48
    img.save(path)
    return path, PAD


def word_chips(path, kicker, words, w=540):
    """Киккер + ряд крупных чипов-наречий («смело · по-доброму · через пользу»)."""
    f_k, f_c = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 34)
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    rows, cur, cw = [], [], 0
    for wd in words:
        pw = d.textlength(wd, font=f_c) + 48
        if cur and cw + pw > w - 60:
            rows.append(cur)
            cur, cw = [], 0
        cur.append(wd)
        cw += pw + 14
    rows.append(cur)
    h = 30 + 40 + len(rows) * 74 + 16
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 36, PAD + 28), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y = PAD + 30 + 40
    for k, row in enumerate(rows):
        x = PAD + 36
        for j, wd in enumerate(row):
            green = (k + j) % 2 == 1
            x += _pill(d, x, y, wd, f_c, PALE_GREEN if green else PALE_BLUE, S.GREEN if green else S.BLUE,
                       pad_x=24, h=60) + 14
        y += 74
    img.save(path)
    return path, PAD


# ---------------------------------------------------------------- приёмы сценария 12
# (сквозная схема «основное → дополнение → польза»: ячейки-колонки, которые
# в примерах заполняются тем же цветом; операторы «+ / =»; замена слова;
# карточка приёма; вертикальная схема-итог)

SCHEME_COLORS = {"main": S.LIGHT_BLUE, "add": S.BLUE, "benefit": S.GREEN}


def scheme_cell(path, kind, label, icon_src, text, w=360, h=330, isz=112, text_size=30, dim=False):
    """Ячейка схемы: цветная шапка с меткой колонки (ОСНОВНОЕ / ДОПОЛНЕНИЕ /
    ПОЛЬЗА), иконка по центру, подпись под ней. Цвет колонки один и тот же
    во всех сценах ролика — зритель узнаёт схему в примерах."""
    col = SCHEME_COLORS[kind]
    f_l, f_t = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, text_size)
    img = _card(w, h, S.WHITE, radius=26)
    d = ImageDraw.Draw(img)
    band = 58
    d.rounded_rectangle([PAD, PAD, PAD + w, PAD + band + 26], 26, fill=col)
    d.rectangle([PAD, PAD + band, PAD + w, PAD + band + 26], fill=S.WHITE)
    lw = d.textlength(label.upper(), font=f_l)
    d.text((PAD + (w - lw) / 2, PAD + 15), label.upper(), font=f_l, fill=S.WHITE)
    ic = _icon(icon_src, isz)
    img.alpha_composite(ic, (PAD + (w - isz) // 2, PAD + band + 22))
    y = PAD + band + 22 + isz + 18
    lh = int(text_size * 1.22)
    for line in wrap(text, f_t, w - 44):
        tw = d.textlength(line, font=f_t)
        d.text((PAD + (w - tw) / 2, y), line, font=f_t, fill=NAVY)
        y += lh
    if dim:
        img.putalpha(img.getchannel("A").point(lambda v: int(v * 0.45)))
    img.save(path)
    return path, PAD


def op_badge(path, sym, color=S.GREEN, size=64):
    """Круглый оператор между ячейками схемы: «+», «=» или «→»."""
    img = Image.new("RGBA", (size + 2 * PAD, size + 2 * PAD), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([PAD, PAD + 5, PAD + size, PAD + size + 5], fill=SHADOW)
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.ellipse([PAD, PAD, PAD + size, PAD + size], fill=color)
    c, k, t = PAD + size / 2, size * 0.2, max(5, size // 11)
    if sym == "+":
        d.line([(c - k, c), (c + k, c)], fill=S.WHITE, width=t)
        d.line([(c, c - k), (c, c + k)], fill=S.WHITE, width=t)
    elif sym == "=":
        d.line([(c - k, c - k * 0.45), (c + k, c - k * 0.45)], fill=S.WHITE, width=t)
        d.line([(c - k, c + k * 0.45), (c + k, c + k * 0.45)], fill=S.WHITE, width=t)
    else:
        d.line([(c - k, c), (c + k * 0.7, c)], fill=S.WHITE, width=t)
        d.polygon([(c + k * 1.15, c), (c + k * 0.3, c - k * 0.7), (c + k * 0.3, c + k * 0.7)], fill=S.WHITE)
    img.save(path)
    return path, PAD


def word_swap(path, kicker, old, news, w=540):
    """Замена слова: старое слово серым в плашке, зачёркнуто; стрелка вниз;
    новые слова — зелёные чипы (переносятся на следующую строку, если не
    влезают). «взять» → «показать» / «взглянуть»."""
    f_k, f_o, f_n = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 44), S.font(S.F_HEADLINE, 40)
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    rows, cur, cw = [], [], 0
    for wd in news:
        pw = d0.textlength(f"«{wd}»", font=f_n) + 48
        if cur and cw + pw > w - 72:
            rows.append(cur)
            cur, cw = [], 0
        cur.append(wd)
        cw += pw + 14
    rows.append(cur)
    h = 30 + 40 + 76 + 70 + len(rows) * 80 + 24
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 36, PAD + 28), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y = PAD + 30 + 40
    ow = _pill(d, PAD + 36, y, f"«{old}»", f_o, PALE_GRAY, S.GRAY, pad_x=26, h=72)
    d.line([(PAD + 48, y + 38), (PAD + 24 + ow, y + 38)], fill=RED, width=6)
    ax = PAD + 36 + ow / 2
    y += 76 + 10
    d.line([(ax, y), (ax, y + 38)], fill=S.GREEN, width=6)
    d.polygon([(ax - 16, y + 34), (ax + 16, y + 34), (ax, y + 54)], fill=S.GREEN)
    y += 60
    for row in rows:
        x = PAD + 36
        for wd in row:
            x += _pill(d, x, y, f"«{wd}»", f_n, PALE_GREEN, S.GREEN, pad_x=24, h=68) + 14
        y += 80
    img.save(path)
    return path, PAD


def technique_card(path, num, icon_src, kicker, title, quote, w=540, isz=100):
    """Карточка приёма: номер-кружок + киккер «приём N», крупное название,
    иконка; ниже — голубая плашка-цитата с примером из речи."""
    f_k, f_t, f_q = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 42), S.font(S.F_MEDIUM, 32)
    x_t = 36 + isz + 24
    t_lines = wrap(title, f_t, w - x_t - 30)
    q_lines = wrap(f"«{quote}»", f_q, w - 110)
    top = max(isz, 40 + len(t_lines) * 50)
    h = 32 + top + 24 + len(q_lines) * 42 + 40 + 30
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    img.alpha_composite(_icon(icon_src, isz), (PAD + 36, PAD + 32))
    d.ellipse([PAD + 36 + isz - 34, PAD + 26, PAD + 36 + isz + 6, PAD + 66], fill=S.GREEN)
    ns = str(num)
    d.text((PAD + 36 + isz - 14 - d.textlength(ns, font=f_k) / 2, PAD + 32), ns, font=f_k, fill=S.WHITE)
    x, y = PAD + x_t, PAD + 32
    d.text((x, y), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y += 40
    for line in t_lines:
        d.text((x, y), line, font=f_t, fill=NAVY)
        y += 50
    y = PAD + 32 + top + 24
    d.rounded_rectangle([PAD + 30, y, PAD + w - 30, y + len(q_lines) * 42 + 40], 20, fill=PALE_BLUE)
    d.rounded_rectangle([PAD + 30, y, PAD + 38, y + len(q_lines) * 42 + 40], 4, fill=S.BLUE)
    yy = y + 18
    for line in q_lines:
        d.text((PAD + 60, yy), line, font=f_q, fill=S.BLUE)
        yy += 42
    img.save(path)
    return path, PAD


def scheme_stack(path, kicker, rows, w=540, isz=84):
    """Схема-итог вертикально: строки (kind, icon, слово) цветами колонок
    схемы, соединены стрелками вниз; kind — ключ SCHEME_COLORS."""
    f_k, f_t = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 44)
    row_h, gap = isz + 24, 34
    h = 30 + 40 + len(rows) * row_h + (len(rows) - 1) * gap + 30
    img = _card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(img)
    d.text((PAD + 36, PAD + 28), kicker.upper(), font=f_k, fill=S.LIGHT_BLUE)
    y = PAD + 30 + 40
    for k, (kind, src, word) in enumerate(rows):
        col = SCHEME_COLORS[kind]
        d.rounded_rectangle([PAD + 28, y, PAD + w - 28, y + row_h], 22, fill=PALE_BLUE)
        d.rounded_rectangle([PAD + 28, y, PAD + 40, y + row_h], 6, fill=col)
        img.alpha_composite(_icon(src, isz), (PAD + 56, y + 12))
        d.text((PAD + 56 + isz + 24, y + (row_h - 44) / 2 - 6), word, font=f_t, fill=NAVY)
        y += row_h
        if k < len(rows) - 1:
            ax = PAD + 56 + isz / 2
            d.polygon([(ax - 14, y + 8), (ax + 14, y + 8), (ax, y + gap - 6)], fill=SCHEME_COLORS[rows[k + 1][0]])
            y += gap
    img.save(path)
    return path, PAD
