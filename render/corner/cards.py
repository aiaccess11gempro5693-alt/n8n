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


def icon_trio(path, items, w=540, isz=120):
    """Одна карточка с 2-3 иконками в ряд и короткой подписью под каждой —
    вместо нескольких отдельных строк, всплывающих по одной (меньше мелькания)."""
    f = S.font(S.F_SEMIBOLD, 30)
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
