"""
Переиспользуемые presentation-компоненты (design-system.md, "12. DESIGN
SYSTEM"). Каждый компонент — чистая функция: контент + grid-константы ->
готовый RGBA PNG (собственная geometry/spacing/typography посчитаны внутри,
самостоятельно по реальным метрикам шрифта — не получены снаружи как пиксели).

compose_scene.py только расставляет готовые изображения компонентов по слотам
выбранного layout — сам не рисует текст/иконки.
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
    """Простой word-wrap по реальной ширине шрифта (в отличие от ffmpeg
    drawtext, который не умеет переносить строки сам)."""
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


def _pad(img, pad):
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    out.paste(img, (pad, pad), img)
    return out


def load_icon(filename, size):
    """Chroma-key (тот же ключ/similarity/blend, что и в ffmpeg colorkey
    прежнего пайплайна) -> альфа-канал -> ресайз до size x size. Файлы
    *-norm.png уже нормализованы по bbox/заполнению, повторно не центрируем."""
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
    """PIL-эквивалент прежнего ffmpeg-стикер-эффекта (dilation-обводка +
    смещённая мягкая тень) — считается один раз при генерации компонента,
    а не пересчитывается ffmpeg-графом на каждый прогон рендера."""
    pad = shadow_px + blur + max(shadow_off) + outline_px + 4
    base = _pad(icon_rgba, pad)
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


def icon_label(icon_file, label, icon_size, fs, text_color=G.WHITE, gap=18, orientation="row",
               max_text_w=None, sticker_fx=True):
    """Атомарный компонент: иконка + подпись как ОДИН блок (design-system.md,
    п.4 — 'icon+текст должны восприниматься как единый компонент'), а не
    иконка и pill, накладываемые двумя независимыми overlay."""
    icon = load_icon(icon_file, icon_size)
    if sticker_fx:
        icon = sticker(icon)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    lines = wrap_text(d, label, fs, max_text_w or 10 ** 6)
    line_h = fs + 8
    text_w = max(text_size(d, ln, fs)[0] for ln in lines)
    text_h = line_h * len(lines)

    if orientation == "row":
        w = icon.width + gap + text_w
        h = max(icon.height, text_h)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        img.paste(icon, (0, (h - icon.height) // 2), icon)
        dd = ImageDraw.Draw(img)
        ty = (h - text_h) // 2
        for i, ln in enumerate(lines):
            dd.text((icon.width + gap, ty + i * line_h), ln, font=font(fs), fill=text_color)
    else:  # column — иконка сверху, подпись по центру под ней (карточки)
        w = max(icon.width, text_w)
        h = icon.height + gap + text_h
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        img.paste(icon, ((w - icon.width) // 2, 0), icon)
        dd = ImageDraw.Draw(img)
        for i, ln in enumerate(lines):
            lw = text_size(dd, ln, fs)[0]
            dd.text(((w - lw) // 2, icon.height + gap + i * line_h), ln, font=font(fs), fill=text_color)
    return img


def headline(title, eyebrow=None, title_fs=G.TITLE_FS, eyebrow_fs=G.EYEBROW_FS,
             accent=G.TEAL, align="left", max_width=None):
    """Полноценный headline-компонент (design-system.md, '5. Заголовок'):
    eyebrow (section label) + H1 + акцентная плашка под текстом. Заменяет
    прежний единственный pill в (60,60) — позицию/выравнивание решает
    compose_scene в зависимости от layout, не сам компонент."""
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    title_lines = wrap_text(d, title, title_fs, max_width or 10 ** 6)
    line_h = title_fs + 10
    title_w = max(text_size(d, ln, title_fs)[0] for ln in title_lines)
    title_h = line_h * len(title_lines)

    eyebrow_h = 0
    eyebrow_w = 0
    if eyebrow:
        eyebrow_w, eyebrow_h = text_size(d, eyebrow.upper(), eyebrow_fs)
        eyebrow_h += 10

    accent_h = 6
    w = max(title_w, eyebrow_w) + 40
    h = eyebrow_h + title_h + accent_h + 18 + 24
    panel = rounded_rect(w, h, radius=16, fill=(20, 22, 24, 200))
    img = panel.copy()
    dd = ImageDraw.Draw(img)
    y = 16
    x0 = 20
    if eyebrow:
        dd.text((x0, y), eyebrow.upper(), font=font(eyebrow_fs), fill=(*accent[:3], 255))
        y += eyebrow_h
    for ln in title_lines:
        dd.text((x0, y), ln, font=font(title_fs), fill=G.WHITE)
        y += line_h
    y += 6
    dd.rounded_rectangle([x0, y, x0 + 56, y + accent_h], radius=accent_h // 2, fill=accent)
    return img


def panel_for(block, min_w=0, min_h=0, pad=32, accent=G.TEAL, radius=20):
    """Панель, размер которой считается ОТ реального содержимого (никогда не
    обрезает block), но не меньше min_w/min_h — так сетка карточек может
    задать общий размер, а одиночная карточка не обрежет длинную подпись."""
    w = max(min_w, block.width + 2 * pad)
    h = max(min_h, block.height + 2 * pad)
    panel = rounded_rect(w, h, radius=radius, fill=(20, 22, 24, 190), outline=(*accent[:3], 255), outline_w=2)
    img = panel.copy()
    img.paste(block, ((w - block.width) // 2, (h - block.height) // 2), block)
    return img


def measure_icon_label(icon_file, label, icon_size, fs, max_text_w, gap=16, orientation="column"):
    """Только размер (w,h) компонента иконка+подпись, без финальной отрисовки
    — используется, чтобы посчитать единый размер карточки ДО того, как её
    строить, а не подогнать по одной и надеяться, что остальные влезут."""
    return icon_label(icon_file, label, icon_size, fs, orientation=orientation,
                       max_text_w=max_text_w, gap=gap).size


def card(icon_file, label, w, h, accent=G.TEAL, icon_size=None, fs=G.CARD_LABEL_FS, pad=32):
    """Единый визуальный блок 'карточка' (design-system.md, '3. Плашки' +
    '4. Инфографика') — рамка/фон объединяет иконку и подпись в одну
    структуру, вместо floating иконки-стикера и отдельной pill. Размер
    самовосстанавливается по контенту (panel_for), если запрошенный w/h
    меньше, чем реально нужно тексту/иконке — не обрезает подпись молча."""
    icon_size = icon_size or min(w, h) // 2
    block = icon_label(icon_file, label, icon_size, fs, orientation="column",
                        max_text_w=w - 2 * pad, gap=16)
    return panel_for(block, min_w=w, min_h=h, pad=pad, accent=accent)


def checklist(title, items, width, row_h=G.CHECKLIST_ROW_H, fs=G.CHECKLIST_FS,
              accent=G.TEAL, icon_files=None):
    """Настоящий чек-лист — ОДИН композиционный блок (design-system.md, '5.
    Чек-листы'): общий заголовок, одинаковая высота/отступ/чекбокс у каждой
    строки, единая рамка, а не N независимых floating pill."""
    n = len(items)
    title_h = (G.TITLE_FS + 16) if title else 0
    h = title_h + n * row_h + G.TITLE_GAP
    panel = rounded_rect(width, h, radius=20, fill=(20, 22, 24, 190))
    img = panel.copy()
    d = ImageDraw.Draw(img)
    pad_x = 28
    y = 16
    if title:
        d.text((pad_x, y), title, font=font(G.TITLE_FS), fill=G.WHITE)
        y += title_h
    y += G.TITLE_GAP - 10
    box = G.CHECKLIST_ICON
    for i, text in enumerate(items):
        row_top = y + i * row_h
        cy = row_top + (row_h - box) // 2
        if icon_files and icon_files[i]:
            ic = load_icon(icon_files[i], box)
            img.paste(ic, (pad_x, cy), ic)
        else:
            d.rounded_rectangle([pad_x, cy, pad_x + box, cy + box], radius=10, outline=accent, width=3)
        lines = wrap_text(d, text, fs, width - pad_x * 2 - box - 20)
        line_h = fs + 6
        text_h = line_h * len(lines)
        ty = row_top + (row_h - text_h) // 2
        for li, ln in enumerate(lines):
            d.text((pad_x + box + 20, ty + li * line_h), ln, font=font(fs), fill=G.WHITE)
    return img


def comparison_side(icon_file, label, w, h, accent, icon_size=None):
    return card(icon_file, label, w, h, accent=accent, fs=G.COMPARISON_LABEL_FS, icon_size=icon_size)


def highlight(title, fs=G.HIGHLIGHT_FS, accent=G.TEAL, max_width=900):
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    lines = wrap_text(d, title, fs, max_width)
    line_h = fs + 12
    w = max(text_size(d, ln, fs)[0] for ln in lines) + 60
    h = line_h * len(lines) + 44
    panel = rounded_rect(w, h, radius=24, fill=(20, 22, 24, 200))
    img = panel.copy()
    dd = ImageDraw.Draw(img)
    y = 22
    for ln in lines:
        lw = text_size(dd, ln, fs)[0]
        dd.text(((w - lw) // 2, y), ln, font=font(fs), fill=G.WHITE)
        y += line_h
    dd.rounded_rectangle([(w - 70) // 2, h - 16, (w + 70) // 2, h - 10], radius=3, fill=accent)
    return img


def plain_list(items, width, row_h=72, fs=G.CHECKLIST_FS):
    """Список без чекбоксов (design-system.md 'List') — переиспользует
    checklist() без иконки/чекбокса."""
    return checklist(None, items, width, row_h=row_h, fs=fs, icon_files=None)


def process(steps, step_w=260, step_h=170, fs=26, accent=G.TEAL):
    """Горизонтальная цепочка шагов с номерами и соединительной линией
    (design-system.md 'Process') — пока не используется ни в одной сцене
    текущего сценария, но реализована как полноценный компонент, не заглушка."""
    n = len(steps)
    gap = 40
    w = n * step_w + (n - 1) * gap
    img = Image.new("RGBA", (w, step_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = 22
    cy = r + 10
    for i in range(n - 1):
        x0 = i * (step_w + gap) + step_w // 2
        x1 = (i + 1) * (step_w + gap) + step_w // 2
        d.line([(x0, cy), (x1, cy)], fill=accent, width=3)
    for i, text in enumerate(steps):
        cx = i * (step_w + gap) + step_w // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)
        num = str(i + 1)
        nw, nh = text_size(d, num, 24)
        d.text((cx - nw / 2, cy - nh / 2), num, font=font(24), fill=G.WHITE)
        lines = wrap_text(d, text, fs, step_w - 10)
        line_h = fs + 6
        ty = cy + r + 14
        for li, ln in enumerate(lines):
            lw = text_size(d, ln, fs)[0]
            d.text((cx - lw / 2, ty + li * line_h), ln, font=font(fs), fill=G.WHITE)
    return img


def section_label(text, accent=G.TEAL, fs=G.EYEBROW_FS):
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    w, h = text_size(d, text.upper(), fs)
    img = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4, 4), text.upper(), font=font(fs), fill=(*accent[:3], 255))
    return img


def section_navigation(sections, active_index, fs=24, accent=G.TEAL, gap=36):
    """Навигация по разделам обучения (design-system.md '6. Section/current
    topic') — активный раздел акцентирован, остальные приглушены. Не
    используется в текущем 8-сценном сценарии без подтверждения разбивки
    на разделы пользователем (см. чат), реализована для будущих сценариев."""
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    sizes = [text_size(d, s.upper(), fs) for s in sections]
    w = sum(s[0] for s in sizes) + gap * (len(sections) - 1) + 32
    h = max(s[1] for s in sizes) + 24
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(img)
    x = 16
    for i, s in enumerate(sections):
        color = (*accent[:3], 255) if i == active_index else (255, 255, 255, 130)
        dd.text((x, 12), s.upper(), font=font(fs), fill=color)
        if i == active_index:
            tw = sizes[i][0]
            dd.rounded_rectangle([x, h - 6, x + tw, h - 2], radius=2, fill=accent)
        x += sizes[i][0] + gap
    return img
