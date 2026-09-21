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

No cards/pills/background fills — legibility on live video comes from a
text shadow (`_draw_text_shadow`), not a backing plate.
"""
from PIL import Image, ImageDraw
from . import style as S

PAD = 28  # padding around content inside each PNG (room for shadow blur)


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
    return img


def render_kicker_word(kicker, word, max_width, align="left"):
    """One oversized word + optional small kicker label above it. Used by
    strong_typography when the scene is literally about one word/theme."""
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

    kick_spaced = " ".join(list(kicker)) if kicker else ""
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
    """A headline with a thin accent blockquote-line. Used by
    strong_typography — a single core message the scene doesn't need
    structure beyond."""
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
    text_x = PAD
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


def render_flow_chain(steps, max_width, align="left"):
    """steps: list[(kicker:str, label:str)], in order. A CONNECTED vertical
    chain — circle node, arrow down, next circle node, ... the final node
    is filled solid (the destination/result). This is the one component
    where connection/order is the visual point: used for process_flow
    (kicker="" or step label) and cause_effect (kicker="ПРИЧИНА"/
    "МЕХАНИЗМ"/"СЛЕДСТВИЕ"). Compare render_item_list, which is
    deliberately NOT connected."""
    f_kick = S.font(S.F_SEMIBOLD, S.SIZE_KICKER - 2)
    f_label = S.font(S.F_MEDIUM, S.SIZE_ITEM_LABEL)
    f_num = S.font(S.F_SEMIBOLD, 18)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    node_r = 16
    node_col_w = node_r * 2 + 16
    text_max_w = max_width - node_col_w
    ARROW_GAP = 28

    rows = []
    for kicker, label in steps:
        kick_lines = _wrap(d, kicker.upper(), f_kick, text_max_w) if kicker else []
        label_lines = _wrap(d, label, f_label, text_max_w)
        kh = len(kick_lines) * int((S.SIZE_KICKER - 2) * 1.3)
        lh = len(label_lines) * int(S.SIZE_ITEM_LABEL * 1.3)
        rows.append({"kick": kick_lines, "label": label_lines, "h": max(kh + lh, node_r * 2)})

    content_w = max_width
    content_h = sum(r["h"] for r in rows) + ARROW_GAP * max(0, len(rows) - 1)
    canvas = _new_canvas(content_w, content_h)
    draw = ImageDraw.Draw(canvas)

    node_cx = PAD + node_r
    centers, y = [], PAD
    for r in rows:
        centers.append(y + r["h"] / 2)
        y += r["h"] + ARROW_GAP

    y = PAD
    for i, r in enumerate(rows):
        cy = centers[i]
        is_last = i == len(rows) - 1
        if is_last:
            draw.ellipse([node_cx - node_r, cy - node_r, node_cx + node_r, cy + node_r], fill=S.ACCENT)
            num_col = S.WHITE
        else:
            draw.ellipse([node_cx - node_r, cy - node_r, node_cx + node_r, cy + node_r], outline=S.ACCENT, width=3)
            num_col = S.ACCENT
        num_text = str(i + 1)
        bbox = d.textbbox((0, 0), num_text, font=f_num)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        _draw_text_shadow(draw, (node_cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), num_text, f_num, num_col, shadow=False)

        tx, ty = PAD + node_col_w, y
        for line in r["kick"]:
            _draw_text_shadow(draw, (tx, ty), line, f_kick, S.ACCENT, shadow=False)
            ty += int((S.SIZE_KICKER - 2) * 1.3)
        for line in r["label"]:
            _draw_text_shadow(draw, (tx, ty), line, f_label, S.WHITE)
            ty += int(S.SIZE_ITEM_LABEL * 1.3)

        if not is_last:
            next_cy = centers[i + 1]
            top, bottom = cy + node_r + 4, next_cy - node_r - 4
            if bottom > top:
                draw.line([node_cx, top, node_cx, bottom], fill=S.ACCENT, width=3)
                draw.polygon([(node_cx - 6, bottom - 8), (node_cx + 6, bottom - 8), (node_cx, bottom + 2)], fill=S.ACCENT)

        y += r["h"] + ARROW_GAP

    return _finish(canvas)


def render_item_list(items, max_width, align="left"):
    """items: list[str]. A plain numbered list, deliberately WITHOUT
    connectors — for structured_alternatives, where the point is that the
    items are independent, not sequential. Compare render_flow_chain."""
    f_marker = S.font(S.F_SEMIBOLD, S.SIZE_MARKER)
    f_label = S.font(S.F_MEDIUM, S.SIZE_ITEM_LABEL)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    marker_col_w = 46
    text_max_w = max_width - marker_col_w
    GAP = 24

    rows = [_wrap(d, label, f_label, text_max_w) for label in items]
    content_w = max_width
    content_h = sum(len(r) * int(S.SIZE_ITEM_LABEL * 1.28) for r in rows) + GAP * max(0, len(rows) - 1)
    canvas = _new_canvas(content_w, content_h)
    draw = ImageDraw.Draw(canvas)

    y = PAD
    for i, lines in enumerate(rows):
        _draw_text_shadow(draw, (PAD, y), f"{i + 1:02d}", f_marker, S.ACCENT, shadow=False)
        ty = y
        for line in lines:
            _draw_text_shadow(draw, (PAD + marker_col_w, ty), line, f_label, S.WHITE)
            ty += int(S.SIZE_ITEM_LABEL * 1.28)
        y = ty + GAP

    return _finish(canvas)


def render_checklist(items, max_width, align="left"):
    """items: list[str]. Checkbox rows + a left "spine" bracket spanning
    the whole group — the spine is what visually says "this is one set to
    go through", distinct from render_item_list's unrelated independent
    rows."""
    f_label = S.font(S.F_MEDIUM, S.SIZE_ITEM_LABEL)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    box_col_w = 46
    text_max_w = max_width - box_col_w
    GAP = 22
    box = 22

    rows = [_wrap(d, label, f_label, text_max_w) for label in items]
    row_heights = [max(len(r) * int(S.SIZE_ITEM_LABEL * 1.28), box) for r in rows]
    content_w = max_width
    content_h = sum(row_heights) + GAP * max(0, len(rows) - 1)
    canvas = _new_canvas(content_w + 12, content_h)
    draw = ImageDraw.Draw(canvas)

    spine_x = PAD - 8
    draw.line([spine_x, PAD, spine_x, PAD + content_h], fill=S.ACCENT_SOFT, width=3)

    y = PAD
    for lines, row_h in zip(rows, row_heights):
        by = y + (row_h - box) / 2
        draw.rectangle([PAD, by, PAD + box, by + box], outline=S.ACCENT, width=3)
        ty = y
        for line in lines:
            _draw_text_shadow(draw, (PAD + box_col_w, ty), line, f_label, S.WHITE)
            ty += int(S.SIZE_ITEM_LABEL * 1.28)
        y += row_h + GAP

    return _finish(canvas)


def render_comparison_side(label, sublabel, side, max_width):
    """One half of a comparison. `side` ("left"|"right") determines which
    edge is "inner" (facing the avatar) — a small chevron on that edge
    points toward the avatar, giving both halves a shared visual axis
    without drawing anything over AVATAR_ZONE (which spans the full frame
    height in this design — see safe_zones.py — so a literal centered
    divider/VS mark is not placeable without violating that zone)."""
    f_head = S.font(S.F_BLACK, S.SIZE_HEADLINE)
    f_sub = S.font(S.F_MEDIUM, S.SIZE_SUBLABEL)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    chevron_w = 24
    text_max_w = max_width - chevron_w
    head_lines = _wrap(d, label, f_head, text_max_w)
    head_w, head_h = _measure_block(head_lines, f_head, int(S.SIZE_HEADLINE * 1.12))
    sub_lines = _wrap(d, sublabel, f_sub, text_max_w) if sublabel else []
    sub_w, sub_h = _measure_block(sub_lines, f_sub, int(S.SIZE_SUBLABEL * 1.35))

    content_w = max(head_w, sub_w) + chevron_w
    content_h = head_h + (14 + sub_h if sublabel else 0)
    canvas = _new_canvas(content_w, content_h)
    draw = ImageDraw.Draw(canvas)

    inner_right = side == "right"  # right-side block's inner (avatar-facing) edge is its LEFT
    text_x = PAD + chevron_w if inner_right else PAD
    text_span = content_w - chevron_w

    def line_x(lw):
        return text_x if inner_right else text_x + text_span - lw

    y = PAD
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

    cy = content_h / 2
    if inner_right:
        chevron_x, direction = PAD, -1
    else:
        chevron_x, direction = PAD + content_w - chevron_w, 1
    draw.polygon([
        (chevron_x, cy - 14), (chevron_x + 10 * direction, cy), (chevron_x, cy + 14),
    ], fill=S.ACCENT)

    return _finish(canvas)


def render_qa(question, answer, max_width, align="left"):
    """A muted question line above a bold answer headline with an accent
    bar — for qa_structure, where the text implies a question the scene
    then answers."""
    f_q = S.font(S.F_MEDIUM, S.SIZE_SUBLABEL + 2)
    f_a = S.font(S.F_BLACK, S.SIZE_HEADLINE)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    q_lines = _wrap(d, question, f_q, max_width)
    a_lines = _wrap(d, answer, f_a, max_width)
    q_w, q_h = _measure_block(q_lines, f_q, int((S.SIZE_SUBLABEL + 2) * 1.3))
    a_w, a_h = _measure_block(a_lines, f_a, int(S.SIZE_HEADLINE * 1.12))
    content_w = max(q_w, a_w) + 20
    content_h = q_h + 12 + a_h
    canvas = _new_canvas(content_w, content_h)
    draw = ImageDraw.Draw(canvas)

    right = align == "right"
    x0 = 20 if not right else 0

    def line_x(lw):
        return x0 if not right else content_w - 20 - lw

    y = PAD
    for line in q_lines:
        lw = d.textlength(line, font=f_q)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_q, S.MUTED, shadow=False)
        y += int((S.SIZE_SUBLABEL + 2) * 1.3)
    y += 12
    ay0 = y
    for line in a_lines:
        lw = d.textlength(line, font=f_a)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_a, S.WHITE)
        y += int(S.SIZE_HEADLINE * 1.12)

    bar_x = (x0 - 14) if not right else (content_w - 6)
    draw.rectangle([bar_x, ay0 + 4, bar_x + 5, y - 6], fill=S.ACCENT)

    return _finish(canvas)
