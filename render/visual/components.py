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
  - render_chain_step   -- ONE step (own card) of a process_flow /
                            cause_effect chain — a numbered node badge
                            carries the order, no line/arrow between
                            steps (see below, 21.09.2026 (13)).
  - render_list_item    -- ONE row (own card) of an UNCONNECTED numbered
                            list for structured_alternatives.
  - render_checklist_item -- ONE checkbox row (own card) of a checklist.
  - render_comparison_side -- one half of a comparison, with a chevron
                            pointing toward the avatar (the shared "axis"),
                            since a literal center divider is impossible —
                            AVATAR_ZONE spans the full frame height (see
                            safe_zones.py), there is no safe center gap to
                            draw a real vs-marker in.
  - render_qa_question / render_headline -- a muted question card, then
                            (separately) a bold answer card for
                            qa_structure.
  - render_headline / render_kicker_word -- unchanged, for strong_typography
                            (a single message IS legitimately just typography
                            — this is not the old bug, this is a real
                            asset_strategy="typography" decision made per
                            scene by semantic_analysis, not a default).

21.09.2026 (13) — render_flow_chain / render_item_list / render_checklist
(one combined image for a whole list, ONE shared trigger) were replaced
by the per-item render_chain_step / render_list_item / render_checklist_item
above, each its own card with its own trigger. Direct complaint from the
project lead forwarded via chat: the combined version made every element
of a scene pop onto the screen together at the scene's first trigger
word — so the viewer saw later bullets/steps before the narrator had
actually said them ("диктор говорит одно, а там уже а-ля спойлер к
следующему"). composition.py now computes a real per-element trigger
(from `VisualElement.trigger_phrase`, an LLM-supplied narration anchor —
see semantic_analysis.py) and calls these per-item renderers once per
element instead of once per scene. The old connecting line/arrow between
chain nodes is gone: it can't be drawn sensibly between cards that appear
on screen at different times, so order is carried by the numbered node
badge alone.

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

21.09.2026 (7) — the flat CARD_TEXT_FILL colour (tried near-black, warm
brown, teal, solid accent-coral — each rejected in turn) is replaced by a
GENERATED texture (`assets/card_texture.png`, produced once via the real
Nano Banana pipeline with a proper design brief — see git log — not
regenerated per scene/per render, a one-time approved "design system"
asset like the project's original Step 0). Direct user instruction: card
plates should themselves be generated, matching the same "kit" as the
photorealistic illustrations, not a flat programmatic colour. The border
is now semi-transparent per the same instruction ("полупрозрачная
окантовка"). Text itself (the words) is still drawn by code, not baked
into the generated image — the project's own ТЗ п.4 rule ("текст не
рисуется заранее на изображениях") and avoids generative text-garbling
risk; only the card's BACKGROUND texture is generated.
"""
import os

from PIL import Image, ImageDraw, ImageFilter
from . import style as S

PAD = 28  # padding around content inside each PNG (room for card border/shadow), at scale=1.0
CARD_RADIUS = 26
CARD_BORDER = 4
CARD_SHADOW_BLUR = 22
CARD_SHADOW_OFFSET = 12
CARD_SHADOW_COLOR = (5, 6, 8, 150)

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_CARD_TEXTURE = Image.open(os.path.join(_ASSETS_DIR, "card_texture.png")).convert("RGBA")

CARD_TEXT_INSET = 10                     # gap from the PAD-bounded canvas edge to the card's own edge — stays inside the existing PAD reserve, canvas size unchanged
CARD_TEXT_BORDER = 3
CARD_TEXT_BORDER_COLOR = (255, 255, 255, 130)   # semi-transparent white ring, per direct instruction
CARD_TEXT_SHADOW_BLUR = 10
CARD_TEXT_SHADOW_OFFSET = 5
CARD_TEXT_SHADOW_COLOR = (5, 6, 8, 130)


def _texture_fill(w, h):
    """Crops/resizes the generated card texture to exactly (w, h). The
    source is a smooth low-frequency gradient (no sharp detail), so a
    plain resize holds up at any target aspect ratio without visible
    stretch artifacts — unlike a sharp-edged design, which would need
    9-slice scaling."""
    tw, th = _CARD_TEXTURE.size
    src_ratio, dst_ratio = tw / th, w / h
    if src_ratio > dst_ratio:
        new_w = int(th * dst_ratio)
        x0 = (tw - new_w) // 2
        crop = _CARD_TEXTURE.crop((x0, 0, x0 + new_w, th))
    else:
        new_h = int(tw / dst_ratio)
        y0 = (th - new_h) // 2
        crop = _CARD_TEXTURE.crop((0, y0, tw, y0 + new_h))
    return crop.resize((int(w), int(h)))


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


def _wrap_fit(draw, text, font_path, start_size, max_width, min_size=18, step=2):
    """`_wrap()` alone can't stop a single WORD from itself being wider
    than `max_width` — it never breaks mid-word, so a long unbroken word
    (e.g. a long Russian compound) just overflows as its own oversized
    line. That's exactly what crashed a real production render
    (validate.py correctly caught a card overflowing AVATAR_ZONE because
    of this — see CLAUDE.md, 21.09.2026). This shrinks the font size
    until every wrapped line actually fits within `max_width`, or floors
    at `min_size`. Returns (lines, font, size)."""
    size = start_size
    while True:
        fnt = S.font(font_path, size)
        lines = _wrap(draw, text, fnt, max_width)
        widest = max((draw.textlength(l, font=fnt) for l in lines), default=0)
        if widest <= max_width or size <= min_size:
            return lines, fnt, size
        size -= step


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

    card_w, card_h = w - 2 * inset, h - 2 * inset
    tex = _texture_fill(card_w, card_h)
    mask = _rounded_mask((int(card_w), int(card_h)), radius)
    base.paste(tex, (int(inset), int(inset)), mask)
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
        draw.rectangle([kx - _sz(18, scale), y + _sz(6, scale), kx - _sz(12, scale), y + _fs(S.SIZE_KICKER, scale) + _sz(2, scale)], fill=S.ACCENT)
        _draw_text_shadow(draw, (kx, y), kick_spaced, f_kick, S.ACCENT, shadow=False)
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
    f_sub = S.font(S.F_MEDIUM, _fs(S.SIZE_SUBLABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    text_max_w = max_width - bar_w
    head_lines, f_head, head_size = _wrap_fit(d, label, S.F_BLACK, _fs(S.SIZE_HEADLINE, scale), text_max_w, min_size=_fs(28, scale, floor=18))
    head_w, head_h = _measure_block(head_lines, f_head, int(head_size * 1.12))
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
        _draw_text_shadow(draw, (line_x(kw), y), kicker.upper(), f_kick, S.ACCENT, shadow=False)
        y += kick_h
    head_top = y
    for line in head_lines:
        lw = d.textlength(line, font=f_head)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_head, S.WHITE)
        y += int(head_size * 1.12)
    if sublabel:
        y += _sz(10, scale)
        for line in sub_lines:
            lw = d.textlength(line, font=f_sub)
            _draw_text_shadow(draw, (line_x(lw), y), line, f_sub, S.MUTED)
            y += int(_fs(S.SIZE_SUBLABEL, scale) * 1.35)

    if accent_bar:
        draw.rectangle([bar_x0, head_top + _sz(4, scale), bar_x0 + _sz(5, scale), y - _sz(6, scale)], fill=S.ACCENT)

    return _finish(_wrap_in_card(canvas, scale))


def render_chain_step(kicker, label, index, is_final, max_width, scale=1.0):
    """ONE step of a process_flow/cause_effect chain, as its own
    self-contained card. 21.09.2026 (13) — split from the old
    render_flow_chain (which baked the whole chain into a single image
    with a single trigger) per a direct complaint from the project lead:
    every element used to pop onto the screen together, at the scene's
    very first trigger word, so the viewer saw later steps before the
    narrator had said them ("диктор говорит одно, а там уже а-ля спойлер
    к следующему"). Each step now gets its OWN card and its OWN trigger,
    computed from a real narration anchor (see composition.py). The old
    node-to-node connecting line/arrow is dropped — it can't be drawn
    sensibly between two cards that appear on screen at different times —
    order is instead carried by the numbered node badge alone."""
    pad = _sz(PAD, scale)
    f_kick = S.font(S.F_SEMIBOLD, _fs(S.SIZE_KICKER - 2, scale))
    f_label = S.font(S.F_MEDIUM, _fs(S.SIZE_ITEM_LABEL, scale))
    f_num = S.font(S.F_SEMIBOLD, _fs(18, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    node_r = _sz(16, scale)
    node_col_w = node_r * 2 + _sz(16, scale)
    text_max_w = max_width - node_col_w

    kick_lines = _wrap(d, kicker.upper(), f_kick, text_max_w) if kicker else []
    label_lines = _wrap(d, label, f_label, text_max_w)
    kh = len(kick_lines) * int(_fs(S.SIZE_KICKER - 2, scale) * 1.3)
    lh = len(label_lines) * int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.3)
    content_h = max(kh + lh, node_r * 2)
    content_w = max_width

    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    node_cx, node_cy = pad + node_r, pad + content_h / 2
    if is_final:
        draw.ellipse([node_cx - node_r, node_cy - node_r, node_cx + node_r, node_cy + node_r], fill=S.ACCENT)
        num_col = S.WHITE
    else:
        draw.ellipse([node_cx - node_r, node_cy - node_r, node_cx + node_r, node_cy + node_r], outline=S.ACCENT, width=max(1, _sz(3, scale)))
        num_col = S.ACCENT
    num_text = str(index + 1)
    bbox = d.textbbox((0, 0), num_text, font=f_num)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    _draw_text_shadow(draw, (node_cx - tw / 2 - bbox[0], node_cy - th / 2 - bbox[1]), num_text, f_num, num_col, shadow=False)

    tx, ty = pad + node_col_w, pad + (content_h - (kh + lh)) / 2
    for line in kick_lines:
        _draw_text_shadow(draw, (tx, ty), line, f_kick, S.ACCENT, shadow=False)
        ty += int(_fs(S.SIZE_KICKER - 2, scale) * 1.3)
    for line in label_lines:
        _draw_text_shadow(draw, (tx, ty), line, f_label, S.WHITE)
        ty += int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.3)

    return _finish(_wrap_in_card(canvas, scale))


def render_list_item(index, label, max_width, scale=1.0):
    """ONE row of a structured_alternatives list, as its own card — see
    render_chain_step's docstring (21.09.2026 (13), per-item timing)."""
    pad = _sz(PAD, scale)
    f_marker = S.font(S.F_SEMIBOLD, _fs(S.SIZE_MARKER, scale))
    f_label = S.font(S.F_MEDIUM, _fs(S.SIZE_ITEM_LABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    marker_col_w = _sz(46, scale)
    text_max_w = max_width - marker_col_w

    lines = _wrap(d, label, f_label, text_max_w)
    content_w = max_width
    content_h = len(lines) * int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    _draw_text_shadow(draw, (pad, pad), f"{index + 1:02d}", f_marker, S.ACCENT, shadow=False)
    ty = pad
    for line in lines:
        _draw_text_shadow(draw, (pad + marker_col_w, ty), line, f_label, S.WHITE)
        ty += int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28)

    return _finish(_wrap_in_card(canvas, scale))


def render_checklist_item(label, max_width, scale=1.0):
    """ONE checkbox row of a checklist, as its own card. Drops the shared
    left "spine" bracket the old combined render_checklist drew across
    the whole group — each item now appears independently, so there is no
    single moment where a spanning spine would be fully visible. See
    render_chain_step's docstring (21.09.2026 (13), per-item timing)."""
    pad = _sz(PAD, scale)
    f_label = S.font(S.F_MEDIUM, _fs(S.SIZE_ITEM_LABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    box_col_w = _sz(46, scale)
    text_max_w = max_width - box_col_w
    box = _sz(22, scale)

    lines = _wrap(d, label, f_label, text_max_w)
    content_w = max_width
    content_h = max(len(lines) * int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28), box)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    by = pad + (content_h - box) / 2
    radius = max(2, _sz(6, scale))
    draw.rounded_rectangle([pad, by, pad + box, by + box], radius=radius, fill=S.ACCENT)
    ty = pad
    for line in lines:
        _draw_text_shadow(draw, (pad + box_col_w, ty), line, f_label, S.WHITE)
        ty += int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28)

    return _finish(_wrap_in_card(canvas, scale))


THUMB_SIZE = 72  # per-item bullet thumbnail side, at scale=1.0


def _draw_thumb(canvas, x, y, size, thumb):
    """Pastes a per-item generated illustration (`thumb`, a real photo
    from illustration.py — see composition.py) as a small rounded,
    accent-bordered square at (x, y) directly onto `canvas`. Shared by
    render_list_item_with_image/render_checklist_item_with_image below —
    21.09.2026 (13): direct user instruction, each concrete bullet in a
    list gets its OWN picture ('после ОРВИ одна картинка, после этого
    другая. БАДы, например'), not one shared illustration for the whole
    scene."""
    img = thumb.convert("RGBA")
    ratio = size / max(img.width, img.height)
    img = img.resize((max(1, round(img.width * ratio)), max(1, round(img.height * ratio))))
    # center-crop to a square if the source isn't already ~1:1
    if img.width != img.height:
        side = min(img.width, img.height)
        left = (img.width - side) // 2
        top = (img.height - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((size, size))
    mask = _rounded_mask((size, size), size // 5)
    canvas.paste(img, (int(x), int(y)), mask)
    ImageDraw.Draw(canvas).rounded_rectangle(
        [x, y, x + size, y + size], radius=size // 5, outline=S.ACCENT, width=2,
    )


def render_list_item_with_image(index, label, thumb, max_width, scale=1.0):
    """Like render_list_item, but with a small per-item photo (`thumb`)
    to the left of the marker+text — see _draw_thumb's docstring."""
    pad = _sz(PAD, scale)
    thumb_sz = _sz(THUMB_SIZE, scale)
    thumb_gap = _sz(16, scale)
    f_marker = S.font(S.F_SEMIBOLD, _fs(S.SIZE_MARKER, scale))
    f_label = S.font(S.F_MEDIUM, _fs(S.SIZE_ITEM_LABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    marker_col_w = _sz(46, scale)
    text_max_w = max_width - thumb_sz - thumb_gap - marker_col_w

    lines = _wrap(d, label, f_label, text_max_w)
    content_w = max_width
    content_h = max(len(lines) * int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28), thumb_sz)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    _draw_thumb(canvas, pad, pad + (content_h - thumb_sz) / 2, thumb_sz, thumb)

    mx = pad + thumb_sz + thumb_gap
    _draw_text_shadow(draw, (mx, pad), f"{index + 1:02d}", f_marker, S.ACCENT, shadow=False)
    tx, ty = mx + marker_col_w, pad
    for line in lines:
        _draw_text_shadow(draw, (tx, ty), line, f_label, S.WHITE)
        ty += int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28)

    return _finish(_wrap_in_card(canvas, scale))


def render_checklist_item_with_image(label, thumb, max_width, scale=1.0):
    """Like render_checklist_item, but with a small per-item photo
    (`thumb`) to the left of the checkbox+text — see _draw_thumb's
    docstring."""
    pad = _sz(PAD, scale)
    thumb_sz = _sz(THUMB_SIZE, scale)
    thumb_gap = _sz(16, scale)
    f_label = S.font(S.F_MEDIUM, _fs(S.SIZE_ITEM_LABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    box_col_w = _sz(46, scale)
    box = _sz(22, scale)
    text_max_w = max_width - thumb_sz - thumb_gap - box_col_w

    lines = _wrap(d, label, f_label, text_max_w)
    content_w = max_width
    content_h = max(len(lines) * int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28), thumb_sz)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    _draw_thumb(canvas, pad, pad + (content_h - thumb_sz) / 2, thumb_sz, thumb)

    mx = pad + thumb_sz + thumb_gap
    by = pad + (content_h - box) / 2
    radius = max(2, _sz(6, scale))
    draw.rounded_rectangle([mx, by, mx + box, by + box], radius=radius, fill=S.ACCENT)
    tx, ty = mx + box_col_w, pad
    for line in lines:
        _draw_text_shadow(draw, (tx, ty), line, f_label, S.WHITE)
        ty += int(_fs(S.SIZE_ITEM_LABEL, scale) * 1.28)

    return _finish(_wrap_in_card(canvas, scale))


def render_qa_question(question, max_width, scale=1.0):
    """The question half of qa_structure, as its own small card — appears
    when the narrator poses the question; the answer (rendered via
    render_headline) appears separately, later, when it's actually
    answered. See render_chain_step's docstring (21.09.2026 (13))."""
    pad = _sz(PAD, scale)
    f_q = S.font(S.F_MEDIUM, _fs(S.SIZE_SUBLABEL + 2, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    lines = _wrap(d, question, f_q, max_width)
    content_w = max_width
    content_h = len(lines) * int(_fs(S.SIZE_SUBLABEL + 2, scale) * 1.3)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)
    y = pad
    for line in lines:
        _draw_text_shadow(draw, (pad, y), line, f_q, S.MUTED, shadow=False)
        y += int(_fs(S.SIZE_SUBLABEL + 2, scale) * 1.3)
    return _finish(_wrap_in_card(canvas, scale))


def render_comparison_side(label, sublabel, side, max_width, scale=1.0):
    """One half of a comparison. `side` ("left"|"right") determines which
    edge is "inner" (facing the avatar) — a small chevron on that edge
    points toward the avatar, giving both halves a shared visual axis
    without drawing anything over AVATAR_ZONE (which spans the full frame
    height in this design — see safe_zones.py — so a literal centered
    divider/VS mark is not placeable without violating that zone)."""
    pad = _sz(PAD, scale)
    f_sub = S.font(S.F_MEDIUM, _fs(S.SIZE_SUBLABEL, scale))
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    chevron_w = _sz(24, scale)
    gap = _sz(18, scale)  # breathing room between the chevron and the text — without this the text (right-aligned in the "else" branch) sat flush against the chevron's own edge regardless of chevron_w, reading as "stuck together"
    text_max_w = max_width - chevron_w - gap
    head_lines, f_head, head_size = _wrap_fit(d, label, S.F_BLACK, _fs(S.SIZE_HEADLINE, scale), text_max_w, min_size=_fs(28, scale, floor=18))
    head_w, head_h = _measure_block(head_lines, f_head, int(head_size * 1.12))
    sub_lines = _wrap(d, sublabel, f_sub, text_max_w) if sublabel else []
    sub_w, sub_h = _measure_block(sub_lines, f_sub, int(_fs(S.SIZE_SUBLABEL, scale) * 1.35))

    content_w = max(max(head_w, sub_w) + chevron_w + gap, max_width)
    content_h = head_h + (_sz(14, scale) + sub_h if sublabel else 0)
    canvas = _new_canvas(content_w, content_h, pad)
    draw = ImageDraw.Draw(canvas)

    inner_right = side == "right"  # right-side block's inner (avatar-facing) edge is its LEFT
    text_x = pad + chevron_w + gap if inner_right else pad
    text_span = content_w - chevron_w - gap

    def line_x(lw):
        return text_x if inner_right else text_x + text_span - lw

    y = pad
    for line in head_lines:
        lw = d.textlength(line, font=f_head)
        _draw_text_shadow(draw, (line_x(lw), y), line, f_head, S.WHITE)
        y += int(head_size * 1.12)
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
    ], fill=S.ACCENT)

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




def render_top_title(text, max_width, scale=1.0):
    """Short scene-topic banner across the very top of frame, centered
    above the avatar's head — a new persistent element (21.09.2026 (4),
    direct user instruction), present in EVERY scene in addition to the
    existing side-column content, not a replacement for it. Sized for
    safe_zones.TOP_TITLE_ZONE (measured real headroom above the avatar's
    hair, see that module's docstring).

    21.09.2026 (10) — restyled per direct feedback ("более современные,
    в стиле остальных плашек и текста"): the tight pad (14px) made the
    card's own border sit right against the letters, reading as a thick
    outline around the text rather than a plate the text sits on. Padding
    widened to match the breathing room side-cards get, and a slim accent
    underline replaces that cramped-outline look with the same
    kicker/accent-bar visual language `render_headline` already uses —
    the texture plate itself (the part already "in the style of the
    other plates") is unchanged."""
    pad = _sz(16, scale)
    size = _fs(40, scale, floor=22)
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
    bar_h = _sz(4, scale)
    bar_gap = _sz(6, scale)
    canvas = Image.new("RGBA", (int(text_w) + pad * 2, size + bar_gap + bar_h + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, pad), upper, font=f, fill=S.WHITE)
    bar_y = pad + size + bar_gap
    draw.rounded_rectangle([pad, bar_y, pad + text_w, bar_y + bar_h], radius=bar_h / 2, fill=S.ACCENT)
    return _finish(_wrap_in_card(canvas, scale))
