"""
COMPONENTS — типографика-ориентированные renderer'ы. Каждый возвращает
RGBA PIL.Image, обрезанное по фактическому контенту (bbox с небольшим
паддингом), плюс anchor-точку выравнивания ("left"/"right") — layout.py
решает, где именно на кадре это разместить, компонент сам о позиции на
кадре не знает.

Никаких заливок-карточек/pill/иконок. Единственные графические элементы,
кроме текста: тонкая акцентная линия (blockquote-марка / коннектор
процесса) и маркер списка (номер или чекбокс-квадрат) — оба тонкие,
некрупные, служебные.
"""
from PIL import Image, ImageDraw, ImageFilter
from . import style as S

PAD = 28  # общий паддинг вокруг контента внутри своего PNG (место под shadow blur)


def _wrap(draw, text, fnt, max_width):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _measure_block(lines, fnt, line_height):
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    w = max((d.textlength(l, font=fnt) for l in lines), default=0)
    h = line_height * len(lines)
    return w, h


def _draw_text_shadow(draw, xy, text, fnt, fill, shadow=True):
    x, y = xy
    if shadow:
        draw.text((x, y + 2), text, font=fnt, fill=S.SHADOW)
    draw.text((x, y), text, font=fnt, fill=fill)


def _new_canvas(w, h):
    return Image.new("RGBA", (int(w) + PAD * 2, int(h) + PAD * 2), (0, 0, 0, 0))


def _finish(img):
    """Лёгкий blur-проход по отдельному теневому слою уже встроен через
    offset text; здесь просто возвращаем готовый RGBA."""
    return img


def render_kicker_word(kicker, word, max_width, align="left"):
    """KEYWORD_EMPHASIS, стадия 1: маленький киккер + огромное слово.
    Слово — одно, непереносимое; если на базовом размере оно шире колонки,
    размер уменьшается (last resort по п.22 мастер-промпта), пока не
    впишется, вместо переноса/обрезки/вылезания за safe zone."""
    f_kick = S.font(S.F_SEMIBOLD, S.SIZE_KICKER)
    size = S.SIZE_KEYWORD
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    while True:
        f_word = S.font(S.F_BLACK, size)
        w = d.textlength(word, font=f_word)
        if w <= max_width or size <= 40:
            break
        size -= 4
    f_word = S.font(S.F_BLACK, size)

    kick_spaced = (" " * 1).join(list(kicker)) if kicker else ""
    kick_w = d.textlength(kick_spaced, font=f_kick) if kicker else 0
    lines = _wrap(d, word, f_word, max_width)
    word_w, word_h = _measure_block(lines, f_word, int(size * 1.05))

    content_w = max(kick_w, word_w)
    content_h = (S.SIZE_KICKER + 16 if kicker else 0) + word_h
    canvas = _new_canvas(content_w, content_h)
    draw = ImageDraw.Draw(canvas)

    y = PAD
    if kicker:
        kx = PAD if align == "left" else PAD + content_w - kick_w
        draw.rectangle([kx - 18, y + 6, kx - 12, y + S.SIZE_KICKER + 2], fill=S.ACCENT)
        _draw_text_shadow(draw, (kx, y), kick_spaced, f_kick, S.ACCENT, shadow=False)
        y += S.SIZE_KICKER + 16

    for line in lines:
        lw = d.textlength(line, font=f_word)
        lx = PAD if align == "left" else PAD + content_w - lw
        _draw_text_shadow(draw, (lx, y), line, f_word, S.WHITE)
        y += int(size * 1.05)

    return _finish(canvas)


def render_headline(label, max_width, kicker="", sublabel="", align="left", accent_bar=True):
    """TYPOGRAPHY_ONLY / KEYWORD_EMPHASIS стадия 2: заголовок с
    тонкой акцентной блокквот-линией слева (не карточка)."""
    f_kick = S.font(S.F_SEMIBOLD, S.SIZE_KICKER)
    f_head = S.font(S.F_BLACK, S.SIZE_HEADLINE)
    f_sub = S.font(S.F_MEDIUM, S.SIZE_SUBLABEL)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    text_max_w = max_width - (28 if accent_bar else 0)
    head_lines = _wrap(d, label, f_head, text_max_w)
    head_w, head_h = _measure_block(head_lines, f_head, int(S.SIZE_HEADLINE * 1.12))
    sub_lines = _wrap(d, sublabel, f_sub, text_max_w) if sublabel else []
    sub_w, sub_h = _measure_block(sub_lines, f_sub, int(S.SIZE_SUBLABEL * 1.35))

    kick_h = (S.SIZE_KICKER + 14) if kicker else 0
    content_w = max(head_w, sub_w) + (28 if accent_bar else 0)
    content_h = kick_h + head_h + (14 + sub_h if sublabel else 0)
    canvas = _new_canvas(content_w, content_h)
    draw = ImageDraw.Draw(canvas)

    right = align == "right"
    text_x = PAD if not right else PAD
    text_span = content_w - (28 if accent_bar else 0)
    bar_x0 = PAD if not right else PAD + content_w - 6

    def line_x(line_w):
        if not right:
            return text_x + (28 if accent_bar else 0)
        return text_x + text_span - line_w

    y = PAD
    if kicker:
        kw = d.textlength(kicker.upper(), font=f_kick)
        _draw_text_shadow(draw, (line_x(kw), y), kicker.upper(), f_kick, S.ACCENT, shadow=False)
        y += kick_h
    head_top = y
    for line in head_lines:
        lw = d.textlength(line, font=f_head)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_head, S.WHITE)
        y += int(S.SIZE_HEADLINE * 1.12)
    if sublabel:
        y += 10
        for line in sub_lines:
            lw = d.textlength(line, font=f_sub)
            _draw_text_shadow(draw, (line_x(lw), y), line, f_sub, S.MUTED)
            y += int(S.SIZE_SUBLABEL * 1.35)

    if accent_bar:
        draw.rectangle([bar_x0, head_top + 4, bar_x0 + 5, y - 6], fill=S.ACCENT)

    return _finish(canvas)


def render_list_item(marker_text, label, max_width, sublabel="", marker_style="number", align="left"):
    """Один пункт вертикального списка (sequence / grid-as-column /
    checklist) — различаются только `marker_style`:
      - "number": плоский номер (независимые альтернативы, options_grid)
      - "node":   номер в тонком круге + место под коннектор (process_sequence)
      - "check":  пустой квадрат-чекбокс, "включается" акцентной галочкой (checklist)
    """
    f_marker = S.font(S.F_SEMIBOLD, S.SIZE_MARKER)
    f_label = S.font(S.F_MEDIUM, S.SIZE_ITEM_LABEL)
    f_sub = S.font(S.F_MEDIUM, S.SIZE_SUBLABEL - 2)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    marker_col_w = 46
    text_max_w = max_width - marker_col_w
    label_lines = _wrap(d, label, f_label, text_max_w)
    label_w, label_h = _measure_block(label_lines, f_label, int(S.SIZE_ITEM_LABEL * 1.28))
    sub_lines = _wrap(d, sublabel, f_sub, text_max_w) if sublabel else []
    sub_w, sub_h = _measure_block(sub_lines, f_sub, int((S.SIZE_SUBLABEL - 2) * 1.3))

    content_w = marker_col_w + max(label_w, sub_w)
    content_h = max(label_h + (6 + sub_h if sublabel else 0), 34)
    canvas = _new_canvas(content_w, content_h)
    draw = ImageDraw.Draw(canvas)

    if align == "left":
        mx, tx = PAD, PAD + marker_col_w
    else:
        tx, mx = PAD, PAD + content_w - marker_col_w + 14

    my = PAD + 2
    if marker_style == "check":
        box = 24
        draw.rectangle([mx, my, mx + box, my + box], outline=S.ACCENT, width=3)
        draw.line([mx + 5, my + 12, mx + 10, my + 18], fill=S.ACCENT, width=3)
        draw.line([mx + 10, my + 18, mx + 19, my + 6], fill=S.ACCENT, width=3)
    elif marker_style == "node":
        r = 18
        cx, cy = mx + r, my + r - 2
        f_node = S.font(S.F_SEMIBOLD, 20)
        bbox = d.textbbox((0, 0), marker_text, font=f_node)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=S.ACCENT, width=3)
        _draw_text_shadow(draw, (cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), marker_text, f_node, S.ACCENT,
                           shadow=False)
    else:  # "number"
        _draw_text_shadow(draw, (mx, my), marker_text, f_marker, S.ACCENT, shadow=False)

    ty = PAD
    for line in label_lines:
        _draw_text_shadow(draw, (tx, ty), line, f_label, S.WHITE)
        ty += int(S.SIZE_ITEM_LABEL * 1.28)
    if sublabel:
        ty += 6
        for line in sub_lines:
            _draw_text_shadow(draw, (tx, ty), line, f_sub, S.MUTED)
            ty += int((S.SIZE_SUBLABEL - 2) * 1.3)

    return _finish(canvas)


def render_connector(height, accent=None):
    """Тонкая вертикальная линия-коннектор между шагами process_sequence."""
    w = 6
    canvas = Image.new("RGBA", (w + PAD * 2, int(height) + PAD * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.line([PAD + w // 2, PAD, PAD + w // 2, PAD + int(height)], fill=(accent or S.ACCENT), width=3)
    return canvas
