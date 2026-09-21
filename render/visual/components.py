"""
COMPONENTS — information-shaped renderers. Each returns an RGBA PIL.Image
cropped to its content (bbox + padding for shadow blur); layout.py decides
where on the frame it goes, components don't know about frame position.

Rewritten 21.09.2026 after a forensic audit found that `render_list_item`
(the old component) was reused, with only a marker-glyph swap, for THREE
different information structures (process/alternatives/checklist) — i.e.
they were visually identical except for a circle vs a plain number vs a
checkbox. That's cosmetic variation, not distinct visual explanation.

This version has ONE component per genuinely distinct structure:
  - render_flow_chain   -- a CONNECTED chain (arrows between nodes) for
                            process_flow / cause_effect. The only component
                            for which order + connection is the point.
  - render_item_list    -- an UNCONNECTED numbered list for
                            structured_alternatives. No arrows: the whole
                            point is that the items are independent.
  - render_checklist    -- checkbox rows + a left "spine" bracket that
                            visually groups them as one set to go through —
                            distinct from render_item_list's plain rows.
  - render_comparison_side -- one half of a comparison, with a chevron
                            pointing toward the avatar (the shared "axis"),
                            since a literal center divider is impossible —
                            AVATAR_ZONE spans the full frame height (see
                            safe_zones.py), there is no safe center gap to
                            draw a real vs-marker in.
  - render_qa           -- a muted question line above a bold answer.
  - render_headline / render_kicker_word -- unchanged, for strong_typography
                            (a single message IS legitimately just typography
                            — this is not the old bug, this is a real
                            asset_strategy="typography" decision made per
                            scene by semantic_analysis, not a default).

21.09.2026 (2) — every render_* below now takes a `scale` parameter
(default 1.0). This exists for layout.py's solver (see its module
docstring): when a scene combines a generated illustration with one of
these text components and the pair doesn't fit the safe column at full
size, the solver can ask for a genuinely re-rendered smaller version —
crisp at the new font size, not a blurry raster downscale of the
original. `scale` has a floor enforced by the CALLER (layout.py), not
here; this module will happily render at scale=0.1 if asked; it is not
the readability gate.

21.09.2026 (3) — REVERSED: text no longer relies on shadow-only
legibility. Direct user instruction: no half/empty text floating on raw
video — every text component gets a filled, symmetric card background,
the same visual language as `render_image_card`. `_wrap_in_card()` draws
that card (opaque fill + accent border ring + soft shadow, equal inset on
all 4 sides) behind whatever a render_* function already drew on its
PAD-bounded transparent canvas — reusing that existing PAD reserve, not
growing the canvas, so no caller/layout math changes. `_draw_text_shadow`
still runs first (harmless now that it lands on an opaque fill, kept so
components don't need a separate code path) but is no longer what makes
text legible — the card is.
"""
from PIL import Image, ImageDraw, ImageFilter
from . import style as S

PAD = 28  # padding around content inside each PNG (room for card border/shadow), at scale=1.0
CARD_RADIUS = 26
CARD_BORDER = 4
CARD_SHADOW_BLUR = 22
CARD_SHADOW_OFFSET = 12
CARD_SHADOW_COLOR = (5, 6, 8, 150)

CARD_TEXT_FILL = S.ACCENT                # 21.09.2026 (6): "в стиле картинок" — reuse the SAME solid coral the image caption chip already uses (render_image_card's chip: ACCENT fill + white text), instead of inventing a separate card color. One accent color for the whole system, not two.
CARD_TEXT_INSET = 10                     # gap from the PAD-bounded canvas edge to the card's own edge — stays inside the existing PAD reserve, canvas size unchanged
CARD_TEXT_BORDER = 3
CARD_TEXT_BORDER_COLOR = (255, 255, 255, 220)  # white ring — an accent-colored border would vanish against the now-accent-colored fill
CARD_TEXT_SHADOW_BLUR = 10
CARD_TEXT_SHADOW_OFFSET = 5
CARD_TEXT_SHADOW_COLOR = (5, 6, 8, 130)


def _sz(v, scale):
    """Scale a pixel dimension, floor at 1px."""
    return max(1, round(v * scale))


def _fs(v, scale, floor=10):
    """Scale a font size, floor so PIL never gets an invalid/degenerate size."""
    return max(floor, round(v * scale))


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


def _new_canvas(w, h, pad):
    return Image.new("RGBA", (int(w) + pad * 2, int(h) + pad * 2), (0, 0, 0, 0))


def _finish(img):
    return img


def _wrap_in_card(canvas, scale=1.0):
    """Draws a filled rounded card (opaque fill + accent border ring +
    soft blurred shadow, equal inset on all 4 sides — symmetric by
    construction) BEHIND whatever a render_* function already drew on
    `canvas`, and returns the composited result. `canvas` is always sized
    content+2*PAD (see `_new_canvas`), so the card fits inside that
    existing margin with no change to the returned image's dimensions —
    callers (layout.py, composition.py) need no width-budget changes."""
    inset = _sz(CARD_TEXT_INSET, scale)
    radius = _sz(CARD_RADIUS, scale)
    border = max(1, _sz(CARD_TEXT_BORDER, scale))
    blur = max(1, _sz(CARD_TEXT_SHADOW_BLUR, scale))
    dy = _sz(CARD_TEXT_SHADOW_OFFSET, scale)
    w, h = canvas.size

    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow_layer).rounded_rectangle(
        [inset, inset + dy, w - inset, h - inset + dy], radius=radius, fill=CARD_TEXT_SHADOW_COLOR,
    )
    base.alpha_composite(shadow_layer.filter(ImageFilter.GaussianBlur(blur / 2)))

    ImageDraw.Draw(base).rounded_rectangle([inset, inset, w - inset, h - inset], radius=radius, fill=CARD_TEXT_FILL)
    ImageDraw.Draw(base).rounded_rectangle(
        [inset + border / 2, inset + border / 2, w - inset - border / 2, h - inset - border / 2],
        radius=radius, outline=CARD_TEXT_BORDER_COLOR, width=border,
    )
    base.alpha_composite(canvas)
    return base


def render_kicker_word(kicker, word, max_width, align="left", scale=1.0):
    """One oversized word + optional small kicker label above it. Used by
    strong_typography when the scene is literally about one word/theme."""
    pad = _sz(PAD, scale)
    f_kick = S.font(S.F_SEMIBOLD, _fs(S.SIZE_KICKER, scale))
    size = _fs(S.SIZE_KEYWORD, scale)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    while True:
        f_word = S.font(S.F_BLACK, size)
        w = d.textlength(word, font=f_word)
        if w <= max_width or size <= 40:
            break
        size -= 4
    f_word = S.font(S.F_BLACK, size)

    kick_spaced = " ".join(list(kicker)) if kicker else ""
    kick_w = d.textlength(kick_spaced, font=f_kick) if kicker else 0
    lines = _wrap(d, word, f_word, max_width)
    word_w, word_h = _measure_block(lines, f_word, int(size * 1.05))

    content_w = max(kick_w, word_w)
    content_h = (_fs(S.SIZE_KICKER, scale) + _sz(16, scale) if kicker else 0) + word_h
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    y = pad
    if kicker:
        kx = pad if align == "left" else pad + content_w - kick_w
        draw.rectangle([kx - _sz(18, scale), y + _sz(6, scale), kx - _sz(12, scale), y + _fs(S.SIZE_KICKER, scale) + _sz(2, scale)], fill=S.ON_ACCENT)
        _draw_text_shadow(draw, (kx, y), kick_spaced, f_kick, S.ON_ACCENT, shadow=False)
        y += _fs(S.SIZE_KICKER, scale) + _sz(16, scale)

    for line in lines:
        lw = d.textlength(line, font=f_word)
        lx = pad if align == "left" else pad + content_w - lw
        _draw_text_shadow(draw, (lx, y), line, f_word, S.WHITE)
        y += int(size * 1.05)

    return _finish(_wrap_in_card(canvas, scale))


def render_headline(label, max_width, kicker="", sublabel="", align="left", accent_bar=True, scale=1.0):
    """A headline with a thin accent blockquote-line. Used by
    strong_typography — a single core message the scene doesn't need
    structure beyond."""
    pad = _sz(PAD, scale)
    bar_w = _sz(28, scale) if accent_bar else 0
    f_kick = S.font(S.F_SEMIBOLD, _fs(S.SIZE_KICKER, scale))
    f_head = S.font(S.F_BLACK, _fs(S.SIZE_HEADLINE, scale))
    f_sub = S.font(S.F_MEDIUM, _fs(S.SIZE_SUBLABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    text_max_w = max_width - bar_w
    head_lines = _wrap(d, label, f_head, text_max_w)
    head_w, head_h = _measure_block(head_lines, f_head, int(_fs(S.SIZE_HEADLINE, scale) * 1.12))
    sub_lines = _wrap(d, sublabel, f_sub, text_max_w) if sublabel else []
    sub_w, sub_h = _measure_block(sub_lines, f_sub, int(_fs(S.SIZE_SUBLABEL, scale) * 1.35))

    kick_h = (_fs(S.SIZE_KICKER, scale) + _sz(14, scale)) if kicker else 0
    # stretch to the full column width (not just the wrapped text's natural
    # width) so the card fills the side column instead of leaving a bare
    # gap beside a narrow card — direct user instruction, see CLAUDE.md.
    content_w = max(max(head_w, sub_w) + bar_w, max_width)
    content_h = kick_h + head_h + (_sz(14, scale) + sub_h if sublabel else 0)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    right = align == "right"
    text_x = pad
    text_span = content_w - bar_w
    bar_x0 = pad if not right else pad + content_w - _sz(6, scale)

    def line_x(line_w):
        if not right:
            return text_x + bar_w
        return text_x + text_span - line_w

    y = pad
    if kicker:
        kw = d.textlength(kicker.upper(), font=f_kick)
        _draw_text_shadow(draw, (line_x(kw), y), kicker.upper(), f_kick, S.ON_ACCENT, shadow=False)
        y += kick_h
    head_top = y
    for line in head_lines:
        lw = d.textlength(line, font=f_head)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_head, S.WHITE)
        y += int(_fs(S.SIZE_HEADLINE, scale) * 1.12)
    if sublabel:
        y += _sz(10, scale)
        for line in sub_lines:
            lw = d.textlength(line, font=f_sub)
            _draw_text_shadow(draw, (line_x(lw), y), line, f_sub, S.MUTED)
            y += int(_fs(S.SIZE_SUBLABEL, scale) * 1.35)

    if accent_bar:
        draw.rectangle([bar_x0, head_top + _sz(4, scale), bar_x0 + _sz(5, scale), y - _sz(6, scale)], fill=S.ON_ACCENT)

    return _finish(_wrap_in_card(canvas, scale))


def render_flow_chain(steps, max_width, align="left", scale=1.0):
    """steps: list[(kicker:str, label:str)], in order. A CONNECTED vertical
    chain — circle node, arrow down, next circle node, ... the final node
    is filled solid (the destination/result). This is the one component
    where connection/order is the visual point: used for process_flow
    (kicker="" or step label) and cause_effect (kicker="ПРИЧИНА"/
    "МЕХАНИЗМ"/"СЛЕДСТВИЕ"). Compare render_item_list, which is
    deliberately NOT connected."""
    pad = _sz(PAD, scale)
    f_kick = S.font(S.F_SEMIBOLD, _fs(S.SIZE_KICKER - 2, scale))
    f_label = S.font(S.F_MEDIUM, _fs(S.SIZE_ITEM_LABEL, scale))
    f_num = S.font(S.F_SEMIBOLD, _fs(18, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    node_r = _sz(16, scale)
    node_col_w = node_r * 2 + _sz(16, scale)
    text_max_w = max_width - node_col_w
    arrow_gap = _sz(28, scale)

    rows = []
    for kicker, label in steps:
        kick_lines = _wrap(d, kicker.upper(), f_kick, text_max_w) if kicker else []
        label_lines = _wrap(d, label, f_label, text_max_w)
        kh = len(kick_lines) * int(_fs(S.SIZE_KICKER - 2, scale) * 1.3)
        lh = len(label_lines) * int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.3)
        rows.append({"kick": kick_lines, "label": label_lines, "h": max(kh + lh, node_r * 2)})

    content_w = max_width
    content_h = sum(r["h"] for r in rows) + arrow_gap * max(0, len(rows) - 1)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    node_cx = pad + node_r
    centers, y = [], pad
    for r in rows:
        centers.append(y + r["h"] / 2)
        y += r["h"] + arrow_gap

    y = pad
    for i, r in enumerate(rows):
        cy = centers[i]
        is_last = i == len(rows) - 1
        if is_last:
            draw.ellipse([node_cx - node_r, cy - node_r, node_cx + node_r, cy + node_r], fill=S.ON_ACCENT)
            num_col = S.WHITE
        else:
            draw.ellipse([node_cx - node_r, cy - node_r, node_cx + node_r, cy + node_r], outline=S.ON_ACCENT, width=max(1, _sz(3, scale)))
            num_col = S.ON_ACCENT
        num_text = str(i + 1)
        bbox = d.textbbox((0, 0), num_text, font=f_num)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        _draw_text_shadow(draw, (node_cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), num_text, f_num, num_col, shadow=False)

        tx, ty = pad + node_col_w, y
        for line in r["kick"]:
            _draw_text_shadow(draw, (tx, ty), line, f_kick, S.ON_ACCENT, shadow=False)
            ty += int(_fs(S.SIZE_KICKER - 2, scale) * 1.3)
        for line in r["label"]:
            _draw_text_shadow(draw, (tx, ty), line, f_label, S.WHITE)
            ty += int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.3)

        if not is_last:
            next_cy = centers[i + 1]
            top, bottom = cy + node_r + _sz(4, scale), next_cy - node_r - _sz(4, scale)
            if bottom > top:
                draw.line([node_cx, top, node_cx, bottom], fill=S.ON_ACCENT, width=max(1, _sz(3, scale)))
                aw = _sz(6, scale)
                draw.polygon([(node_cx - aw, bottom - _sz(8, scale)), (node_cx + aw, bottom - _sz(8, scale)), (node_cx, bottom + _sz(2, scale))], fill=S.ON_ACCENT)

        y += r["h"] + arrow_gap

    return _finish(_wrap_in_card(canvas, scale))


def render_item_list(items, max_width, align="left", scale=1.0):
    """items: list[str]. A plain numbered list, deliberately WITHOUT
    connectors — for structured_alternatives, where the point is that the
    items are independent, not sequential. Compare render_flow_chain."""
    pad = _sz(PAD, scale)
    f_marker = S.font(S.F_SEMIBOLD, _fs(S.SIZE_MARKER, scale))
    f_label = S.font(S.F_MEDIUM, _fs(S.SIZE_ITEM_LABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    marker_col_w = _sz(46, scale)
    text_max_w = max_width - marker_col_w
    gap = _sz(24, scale)

    rows = [_wrap(d, label, f_label, text_max_w) for label in items]
    content_w = max_width
    content_h = sum(len(r) * int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28) for r in rows) + gap * max(0, len(rows) - 1)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    y = pad
    for i, lines in enumerate(rows):
        _draw_text_shadow(draw, (pad, y), f"{i + 1:02d}", f_marker, S.ON_ACCENT, shadow=False)
        ty = y
        for line in lines:
            _draw_text_shadow(draw, (pad + marker_col_w, ty), line, f_label, S.WHITE)
            ty += int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28)
        y = ty + gap

    return _finish(_wrap_in_card(canvas, scale))


def render_checklist(items, max_width, align="left", scale=1.0):
    """items: list[str]. Checkbox rows + a left "spine" bracket spanning
    the whole group — the spine is what visually says "this is one set to
    go through", distinct from render_item_list's unrelated independent
    rows."""
    pad = _sz(PAD, scale)
    f_label = S.font(S.F_MEDIUM, _fs(S.SIZE_ITEM_LABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    box_col_w = _sz(46, scale)
    text_max_w = max_width - box_col_w
    gap = _sz(22, scale)
    box = _sz(22, scale)

    rows = [_wrap(d, label, f_label, text_max_w) for label in items]
    row_heights = [max(len(r) * int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28), box) for r in rows]
    content_w = max_width
    content_h = sum(row_heights) + gap * max(0, len(rows) - 1)
    canvas = _new_canvas(content_w + _sz(12, scale), content_h, pad)
    draw = ImageDraw.Draw(canvas)

    spine_x = pad - _sz(8, scale)
    draw.line([spine_x, pad, spine_x, pad + content_h], fill=S.ACCENT_SOFT, width=max(1, _sz(3, scale)))

    y = pad
    for lines, row_h in zip(rows, row_heights):
        by = y + (row_h - box) / 2
        draw.rectangle([pad, by, pad + box, by + box], outline=S.ON_ACCENT, width=max(1, _sz(3, scale)))
        ty = y
        for line in lines:
            _draw_text_shadow(draw, (pad + box_col_w, ty), line, f_label, S.WHITE)
            ty += int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28)
        y += row_h + gap

    return _finish(_wrap_in_card(canvas, scale))


def render_comparison_side(label, sublabel, side, max_width, scale=1.0):
    """One half of a comparison. `side` ("left"|"right") determines which
    edge is "inner" (facing the avatar) — a small chevron on that edge
    points toward the avatar, giving both halves a shared visual axis
    without drawing anything over AVATAR_ZONE (which spans the full frame
    height in this design — see safe_zones.py — so a literal centered
    divider/VS mark is not placeable without violating that zone)."""
    pad = _sz(PAD, scale)
    f_head = S.font(S.F_BLACK, _fs(S.SIZE_HEADLINE, scale))
    f_sub = S.font(S.F_MEDIUM, _fs(S.SIZE_SUBLABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    chevron_w = _sz(24, scale)
    text_max_w = max_width - chevron_w
    head_lines = _wrap(d, label, f_head, text_max_w)
    head_w, head_h = _measure_block(head_lines, f_head, int(_fs(S.SIZE_HEADLINE, scale) * 1.12))
    sub_lines = _wrap(d, sublabel, f_sub, text_max_w) if sublabel else []
    sub_w, sub_h = _measure_block(sub_lines, f_sub, int(_fs(S.SIZE_SUBLABEL, scale) * 1.35))

    content_w = max(max(head_w, sub_w) + chevron_w, max_width)
    content_h = head_h + (_sz(14, scale) + sub_h if sublabel else 0)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    inner_right = side == "right"  # right-side block's inner (avatar-facing) edge is its LEFT
    text_x = pad + chevron_w if inner_right else pad
    text_span = content_w - chevron_w

    def line_x(lw):
        return text_x if inner_right else text_x + text_span - lw

    y = pad
    for line in head_lines:
        lw = d.textlength(line, font=f_head)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_head, S.WHITE)
        y += int(_fs(S.SIZE_HEADLINE, scale) * 1.12)
    if sublabel:
        y += _sz(10, scale)
        for line in sub_lines:
            lw = d.textlength(line, font=f_sub)
            _draw_text_shadow(draw, (line_x(lw), y), line, f_sub, S.MUTED)
            y += int(_fs(S.SIZE_SUBLABEL, scale) * 1.35)

    cy = content_h / 2
    if inner_right:
        chevron_x, direction = pad, -1
    else:
        chevron_x, direction = pad + content_w - chevron_w, 1
    cw2 = _sz(10, scale)
    draw.polygon([
        (chevron_x, cy - _sz(14, scale)), (chevron_x + cw2 * direction, cy), (chevron_x, cy + _sz(14, scale)),
    ], fill=S.ON_ACCENT)

    return _finish(_wrap_in_card(canvas, scale))


def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return mask


def render_image_card(image, caption="", scale=1.0):
    """Frames a generated Nano Banana illustration (`image`, already sized
    to the target column width by illustration.py) as a deliberate design
    object, not a bare rectangle floating on the video: rounded corners,
    a thin accent border ring, a soft blurred drop shadow, and an optional
    short caption chip underneath (an opaque accent pill — unlike the
    typography components in this file, a photo needs no shadow-only
    legibility trick, and neither does a caption sitting on its own
    opaque background). One shared treatment reused for every asset, not
    a per-scene design."""
    radius = _sz(CARD_RADIUS, scale)
    border = max(1, _sz(CARD_BORDER, scale))
    blur = max(1, _sz(CARD_SHADOW_BLUR, scale))
    shadow_dy = _sz(CARD_SHADOW_OFFSET, scale)

    img = image.convert("RGBA")
    mask = _rounded_mask(img.size, radius)
    framed = Image.new("RGBA", img.size, (0, 0, 0, 0))
    framed.paste(img, (0, 0), mask)
    border_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(border_layer).rounded_rectangle(
        [border / 2, border / 2, img.width - 1 - border / 2, img.height - 1 - border / 2],
        radius=radius, outline=S.ACCENT, width=border,
    )

    f_cap = S.font(S.F_SEMIBOLD, _fs(22, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    chip_pad_x, chip_pad_y = _sz(22, scale), _sz(11, scale)
    cap_lines = _wrap(d, caption.upper(), f_cap, img.width - chip_pad_x * 2) if caption else []
    line_h = int(_fs(22, scale) * 1.25)
    chip_w = (max((d.textlength(l, font=f_cap) for l in cap_lines), default=0) + chip_pad_x * 2) if cap_lines else 0
    chip_h = (line_h * len(cap_lines) + chip_pad_y * 2) if cap_lines else 0
    chip_gap = _sz(16, scale) if cap_lines else 0

    pad = _sz(PAD, scale) + blur
    content_w = max(img.width, chip_w)
    content_h = img.height + chip_gap + chip_h
    canvas = Image.new("RGBA", (int(content_w) + pad * 2, int(content_h) + pad * 2), (0, 0, 0, 0))

    img_x = pad + (content_w - img.width) / 2
    img_y = pad

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow_layer).rounded_rectangle(
        [int(img_x), int(img_y + shadow_dy), int(img_x + img.width), int(img_y + shadow_dy + img.height)],
        radius=radius, fill=CARD_SHADOW_COLOR,
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur / 2))
    canvas.alpha_composite(shadow_layer)
    canvas.alpha_composite(framed, (int(img_x), int(img_y)))
    canvas.alpha_composite(border_layer, (int(img_x), int(img_y)))

    if cap_lines:
        chip_x = pad + (content_w - chip_w) / 2
        chip_y = img_y + img.height + chip_gap
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle([int(chip_x), int(chip_y), int(chip_x + chip_w), int(chip_y + chip_h)],
                                radius=chip_h / 2, fill=S.ACCENT)
        ty = chip_y + chip_pad_y
        for line in cap_lines:
            lw = d.textlength(line, font=f_cap)
            lx = chip_x + (chip_w - lw) / 2
            draw.text((lx, ty), line, font=f_cap, fill=S.WHITE)
            ty += line_h

    return _finish(canvas)


def render_qa(question, answer, max_width, align="left", scale=1.0):
    """A muted question line above a bold answer headline with an accent
    bar — for qa_structure, where the text implies a question the scene
    then answers."""
    pad = _sz(PAD, scale)
    f_q = S.font(S.F_MEDIUM, _fs(S.SIZE_SUBLABEL + 2, scale))
    f_a = S.font(S.F_BLACK, _fs(S.SIZE_HEADLINE, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    q_lines = _wrap(d, question, f_q, max_width)
    a_lines = _wrap(d, answer, f_a, max_width)
    q_w, q_h = _measure_block(q_lines, f_q, int(_fs(S.SIZE_SUBLABEL + 2, scale) * 1.3))
    a_w, a_h = _measure_block(a_lines, f_a, int(_fs(S.SIZE_HEADLINE, scale) * 1.12))
    content_w = max(max(q_w, a_w) + _sz(20, scale), max_width)
    content_h = q_h + _sz(12, scale) + a_h
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    right = align == "right"
    x0 = _sz(20, scale) if not right else 0

    def line_x(lw):
        return x0 if not right else content_w - _sz(20, scale) - lw

    y = pad
    for line in q_lines:
        lw = d.textlength(line, font=f_q)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_q, S.MUTED, shadow=False)
        y += int(_fs(S.SIZE_SUBLABEL + 2, scale) * 1.3)
    y += _sz(12, scale)
    ay0 = y
    for line in a_lines:
        lw = d.textlength(line, font=f_a)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_a, S.WHITE)
        y += int(_fs(S.SIZE_HEADLINE, scale) * 1.12)

    bar_x = (x0 - _sz(14, scale)) if not right else (content_w - _sz(6, scale))
    draw.rectangle([bar_x, ay0 + _sz(4, scale), bar_x + _sz(5, scale), y - _sz(6, scale)], fill=S.ON_ACCENT)

    return _finish(_wrap_in_card(canvas, scale))


def render_top_title(text, max_width, scale=1.0):
    """Short scene-topic banner across the very top of frame, centered
    above the avatar's head — a new persistent element (21.09.2026 (4),
    direct user instruction), present in EVERY scene in addition to the
    existing side-column content, not a replacement for it. Sized for
    safe_zones.TOP_TITLE_ZONE (measured real headroom above the avatar's
    hair, see that module's docstring) — a single short line, small pad
    (not the full PAD used by side-column components, which would be
    taller than the zone allows). 21.09.2026 (5): enlarged per direct
    request ("крупно жирно") — TOP_TITLE_ZONE grew to match (see
    safe_zones.py), font weight was already F_BLACK (the boldest weight
    in this project's type system), so "жирно" only needed the size bump."""
    pad = _sz(14, scale)
    size = _fs(44, scale, floor=22)
    upper = text.upper()
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    while True:
        f = S.font(S.F_BLACK, size)
        w = d.textlength(upper, font=f)
        if w <= max_width - pad * 2 or size <= 22:
            break
        size -= 2
    f = S.font(S.F_BLACK, size)
    text_w = d.textlength(upper, font=f)
    canvas = Image.new("RGBA", (int(text_w) + pad * 2, size + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, pad), upper, font=f, fill=S.WHITE)
    return _finish(_wrap_in_card(canvas, scale))
