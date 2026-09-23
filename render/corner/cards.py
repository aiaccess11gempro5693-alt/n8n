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
