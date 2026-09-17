"""
Переиспользуемые presentation-компоненты (design-system.md, "12. DESIGN
SYSTEM"). Editorial-стиль (редизайн 17.09.2026 по прямой жалобе "выглядит
как UI dashboard/набор стикеров"): текст ложится прямо на видео с мягким
scrim-градиентом для читаемости, а не в закрашенную рамку с рамкой-бордером.
Иконка используется, только если она реально помогает считывать смысл
(конкретные разные сценарии в сетке причин) — не как обязательный элемент
каждого компонента.

compose_scene.py только расставляет готовые изображения компонентов по
слотам выбранного layout — сам не рисует текст/иконки.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import grid as G

_font_cache = {}


def font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(G.FONT_PATH, size)
    return _font_cache[size]


def text_size(draw, text, fs):
    l, t, r, b = draw.textbbox((0, 0), text, font=font(fs))
    return r - l, b - t


def wrap_text(draw, text, fs, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if text_size(draw, trial, fs)[0] <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rounded_rect(w, h, radius, fill, outline=None, outline_w=0, ss=4):
    W, H, R = w * ss, h * ss, radius * ss
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=fill,
                         outline=outline, width=outline_w * ss if outline else 0)
    return canvas.resize((w, h), Image.LANCZOS)


def scrim(w, h, inset=26, alpha=140, blur=22, radius=18):
    """Мягкая градиентная подложка под текст — НЕ карточка. Края фейдятся
    блюром внутрь, нет ни рамки, ни ровного прямоугольника (design-system.md,
    '5. Новый visual language' — убрать 'dark translucent rectangle + border'
    как обязательный дефолт)."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([inset, inset, w - inset, h - inset], radius=radius, fill=(*G.SCRIM, alpha))
    return img.filter(ImageFilter.GaussianBlur(blur))


def text_shadow(img, xy, text, fs, fill, shadow_alpha=170, blur=3, offset=(0, 2)):
    """Текст прямо на видео должен быть читаем без сплошного фона — мягкая
    тень под буквами вместо жёсткой панели."""
    x, y = xy
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    sd.text((x + offset[0], y + offset[1]), text, font=font(fs), fill=(0, 0, 0, shadow_alpha))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(shadow_layer)
    ImageDraw.Draw(img).text((x, y), text, font=font(fs), fill=fill)


def load_icon(filename, size):
    """Chroma-key -> альфа -> ресайз. Файлы *-norm.png уже нормализованы по
    bbox/заполнению (см. лог 17.09.2026 (2))."""
    path = f"{G.ICONS_DIR}/{filename}"
    rgb = np.array(Image.open(path).convert("RGB"), dtype=np.float32)
    dist = np.sqrt(((rgb - np.array(G.KEY_COLOR, dtype=np.float32)) ** 2).sum(axis=2))
    dist /= (255.0 * (3 ** 0.5))
    alpha = np.clip((dist - G.KEY_SIMILARITY) / max(G.KEY_BLEND, 1e-6), 0, 1)
    alpha = (alpha * 255).astype(np.uint8)
    rgba = np.dstack([rgb.astype(np.uint8), alpha])
    img = Image.fromarray(rgba, "RGBA")
    return img.resize((size, size), Image.LANCZOS)


def sticker(icon_rgba, outline_px=5, shadow_px=8, blur=5, shadow_alpha=110, shadow_off=(6, 8)):
    """Иконка-стикер (обводка+тень) — остаётся единственным "тяжёлым"
    визуальным приёмом, и только там, где иконка реально нужна (annotated
    grid), не как часть каждого компонента."""
    pad = shadow_px + blur + max(shadow_off) + outline_px + 4
    base = Image.new("RGBA", (icon_rgba.width + 2 * pad, icon_rgba.height + 2 * pad), (0, 0, 0, 0))
    base.paste(icon_rgba, (pad, pad), icon_rgba)
    alpha = base.split()[3]

    outline_mask = alpha.filter(ImageFilter.MaxFilter(2 * outline_px + 1))
    outline_layer = Image.new("RGBA", base.size, G.WHITE)
    outline_layer.putalpha(outline_mask)

    shadow_mask = alpha.filter(ImageFilter.MaxFilter(2 * shadow_px + 1)).filter(ImageFilter.GaussianBlur(blur))
    shadow_layer = Image.new("RGBA", base.size, (0, 0, 0, shadow_alpha))
    shadow_layer.putalpha(Image.eval(shadow_mask, lambda a: int(a * shadow_alpha / 255)))
    shadow_shifted = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow_shifted.paste(shadow_layer, shadow_off, shadow_layer)

    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out = Image.alpha_composite(out, shadow_shifted)
    out = Image.alpha_composite(out, outline_layer)
    out = Image.alpha_composite(out, base)
    return out


# ---------------------------------------------------------------------------
# Компоненты
# ---------------------------------------------------------------------------

def editorial_headline(title, eyebrow=None, accent=G.TEAL, title_fs=G.TITLE_FS,
                        eyebrow_fs=G.EYEBROW_FS, max_width=560):
    """H1 прямо на видео — НЕ pill (design-system.md, '11. Headline'). Eyebrow
    (маленький акцентный лейбл) + короткая акцентная черта + заголовок,
    единая типографическая иерархия, scrim только под текстом, без рамки."""
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    title_lines = wrap_text(d, title, title_fs, max_width)
    line_h = title_fs + 14
    title_w = max(text_size(d, ln, title_fs)[0] for ln in title_lines)
    title_h = line_h * len(title_lines)

    eyebrow_h = (eyebrow_fs + 14) if eyebrow else 0
    eyebrow_w = text_size(d, eyebrow.upper(), eyebrow_fs)[0] if eyebrow else 0

    pad = 22
    w = max(title_w, eyebrow_w) + 2 * pad
    h = eyebrow_h + title_h + 14 + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.alpha_composite(scrim(w, h, alpha=125))
    y = pad
    if eyebrow:
        text_shadow(img, (pad, y), eyebrow.upper(), eyebrow_fs, (*accent[:3], 255))
        y += eyebrow_h
    for ln in title_lines:
        text_shadow(img, (pad, y), ln, title_fs, G.WHITE, blur=4)
        y += line_h
    ImageDraw.Draw(img).rounded_rectangle([pad, y + 2, pad + 48, y + 7], radius=2, fill=accent)
    return img


def bullet_list(items, accent=G.TEAL, title=None, fs=G.BULLET_FS, max_width=620, row_gap=16):
    """Короткие тезисы (НЕ дословные фразы из narration), маркер — короткое
    тире акцентного цвета, без отдельной рамки на каждый пункт (design-
    system.md, '6. Bullets/themes') — единая группа на одном scrim."""
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    marker_w = 34
    rows = []
    for text in items:
        lines = wrap_text(d, text, fs, max_width - marker_w)
        rows.append(lines)
    line_h = fs + 10
    title_h = (G.TITLE_FS + 16) if title else 0
    content_h = sum(len(r) * line_h for r in rows) + row_gap * (len(rows) - 1)
    pad = 26
    w = max_width + 2 * pad
    h = title_h + content_h + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.alpha_composite(scrim(w, h, alpha=130))
    y = pad
    if title:
        text_shadow(img, (pad, y), title, G.TITLE_FS, G.WHITE, blur=4)
        y += title_h
    for lines in rows:
        ImageDraw.Draw(img).ellipse([pad + 2, y + 10, pad + 10, y + 18], fill=accent)
        for li, ln in enumerate(lines):
            text_shadow(img, (pad + marker_w, y), ln, fs, G.WHITE)
            y += line_h
        y += row_gap - (line_h - fs)
    return img


def icon_annotation(icon_file, label, icon_size, fs=G.ANNOTATION_FS, max_text_w=None, gap=14):
    """Иконка + подпись как один атомарный блок (design-system.md, п.4),
    БЕЗ карточки-рамки — контраст даёт сама обводка стикера + тень текста,
    не залитый прямоугольник позади всего блока."""
    icon = sticker(load_icon(icon_file, icon_size))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    lines = wrap_text(d, label, fs, max_text_w or 400)
    line_h = fs + 8
    text_w = max(text_size(d, ln, fs)[0] for ln in lines)
    text_h = line_h * len(lines)
    w = max(icon.width, text_w)
    h = icon.height + gap + text_h
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.paste(icon, ((w - icon.width) // 2, 0), icon)
    for i, ln in enumerate(lines):
        lw = text_size(d, ln, fs)[0]
        text_shadow(img, ((w - lw) // 2, icon.height + gap + i * line_h), ln, fs, G.WHITE)
    return img


def slim_checklist(items, accent=G.TEAL, title=None, fs=G.CHECKLIST_FS, width=520, row_h=70):
    """Настоящий чек-лист как ОДНА композиция (design-system.md, '3.
    Checklist'): тонкая акцентная линия слева + нумерованные строки на общем
    scrim, без тяжёлой панели-рамки вокруг каждого пункта."""
    n = len(items)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    title_h = (G.TITLE_FS + 14) if title else 0
    pad = 24
    rail_w = 40
    h = title_h + n * row_h + 2 * pad
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    img.alpha_composite(scrim(width, h, alpha=130))
    dd = ImageDraw.Draw(img)
    y0 = pad
    if title:
        text_shadow(img, (pad, y0), title, G.TITLE_FS, G.WHITE, blur=4)
        y0 += title_h
    dd.line([(pad + 4, y0 + 6), (pad + 4, y0 + n * row_h - 14)], fill=accent, width=3)
    for i, text in enumerate(items):
        row_top = y0 + i * row_h
        num = f"{i + 1:02d}"
        text_shadow(img, (pad + rail_w - 30, row_top + row_h // 2 - fs // 2 - 2), num, 22, (*accent[:3], 255))
        lines = wrap_text(d, text, fs, width - pad - rail_w - 20)
        line_h = fs + 6
        text_h = line_h * len(lines)
        ty = row_top + (row_h - text_h) // 2
        for li, ln in enumerate(lines):
            text_shadow(img, (pad + rail_w, ty + li * line_h), ln, fs, G.WHITE)
    return img


def split_comparison_side(text, accent, fs=G.COMPARISON_LABEL_FS, w=420, height=140, align="right"):
    """Одна половина сравнения (design-system.md, '4. Comparison'). Из-за
    жёсткого ограничения — аватар занимает ВСЮ высоту центра кадра (x
    640-1290), физически нарисовать разделитель/коннектор через центр
    нельзя, не закрыв лицо — поэтому 'единая композиция' достигается не
    физическим соединением, а зеркальной симметрией: одинаковая высота у
    обеих половин, общий верхний штрих-акцент (как будто одна линия,
    прерванная аватаром), текст развёрнут к центру (align к аватару)."""
    tmp = Image.new("RGBA", (10, 10))
    dt = ImageDraw.Draw(tmp)
    lines = wrap_text(dt, text, fs, w - 40)
    line_h = fs + 8
    total_h = line_h * len(lines)
    img = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    img.alpha_composite(scrim(w, height, alpha=125))
    d = ImageDraw.Draw(img)
    y = (height - total_h) // 2
    tick_x = w - 52 if align == "right" else 20
    d.rounded_rectangle([tick_x, y - 16, tick_x + 32, y - 11], radius=2, fill=accent)
    for ln in lines:
        lw = text_size(dt, ln, fs)[0]
        lx = (w - 20 - lw) if align == "right" else 20
        text_shadow(img, (lx, y), ln, fs, G.WHITE)
        y += line_h
    return img


def statement(title, eyebrow=None, accent=G.TEAL, fs=G.HIGHLIGHT_FS, eyebrow_fs=G.EYEBROW_FS, max_width=880):
    """Крупный editorial-тезис без карточки — для сцен-акцентов (design-
    system.md, '3. Scene 2': мысль должна восприниматься как устойчивая
    визуальная композиция, не как мелькнувшая иконка)."""
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    lines = wrap_text(d, title, fs, max_width)
    line_h = fs + 14
    eyebrow_h = (eyebrow_fs + 16) if eyebrow else 0
    pad = 30
    w = max([text_size(d, ln, fs)[0] for ln in lines] + [text_size(d, eyebrow.upper(), eyebrow_fs)[0] if eyebrow else 0]) + 2 * pad
    h = eyebrow_h + line_h * len(lines) + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.alpha_composite(scrim(w, h, alpha=130))
    y = pad
    if eyebrow:
        text_shadow(img, (pad, y), eyebrow.upper(), eyebrow_fs, (*accent[:3], 255))
        y += eyebrow_h
    for ln in lines:
        text_shadow(img, (pad, y), ln, fs, G.WHITE, blur=4)
        y += line_h
    return img
