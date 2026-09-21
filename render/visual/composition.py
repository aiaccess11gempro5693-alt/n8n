"""
SEMANTIC RESULT (computed) -> COMPOSITION.

Each builder takes a `SceneSemantics` (from `semantic_analysis.py` — a
runtime LLM analysis of arbitrary scene text, not a hand-authored record)
and returns a list of `ColumnGroup`. Dispatch is by `sem.visual_concept`,
a value the LLM chose from `semantic_analysis.VISUAL_CONCEPTS` based on
THIS scene's actual text — there is no `sem.scene_id` branch anywhere in
this file, and no per-scene-id lookup table. A 9th scene, or a synthetic
test sentence that has never been seen before, dispatches through the same
`BUILDERS` dict as scene 1-8 always did.

If `sem.asset_strategy` calls for something beyond typography
(illustration/diagram/icon/image/data_visualization/combination) and the
LLM supplied an `asset_brief`, the builder asks `illustration.py` to
generate/fetch that asset (through the project's existing image pipeline)
and includes it as an additional item — typography is never assumed to be
the only possible output.
"""
from dataclasses import dataclass, field

from . import components as C
from .safe_zones import column_width, LEFT_COLUMN, RIGHT_COLUMN
from .timing import trigger_time, enforce_min_gap
from . import illustration as ILL

MIN_ASSET_PX = 260  # floor on an illustration's smaller dimension — below this it stops being "a diagram you can read", per layout.py's solver


@dataclass
class Item:
    image: object            # the default (scale=1.0) render
    trigger: float
    kind: str = "text"        # "text" (a components.py render, resizable via render_fn) | "asset" (a generated illustration, resizable via plain resize)
    render_fn: object = None  # for kind="text": Callable[[float scale], Image] — lets layout.py ask for a crisp re-render at a smaller font size, not a blurry raster downscale
    min_scale: float = 0.82   # for kind="text": floor scale layout.py won't go below
    min_px: int = MIN_ASSET_PX  # for kind="asset": floor on the smaller dimension


@dataclass
class ColumnGroup:
    column: str          # "left" | "right"
    mode: str             # "accumulate" | "replace"
    align: str = "left"
    items: list = field(default_factory=list)


def _col_geom(column):
    return LEFT_COLUMN if column == "left" else RIGHT_COLUMN


def _by_role(sem, role):
    return [e for e in sem.elements if e.role == role]


def _ordered(elements):
    return sorted(elements, key=lambda e: e.order or 0)


def _first_trigger(sem, default=0.3):
    """Best-effort trigger time for the whole composite asset: anchor to
    the first content word of the scene if real word timing exists for
    this scene_id (production scenes), otherwise fall back to a fixed
    early offset (used by the synthetic test harness, which has no
    word_layout.json for made-up sentences)."""
    try:
        return trigger_time(sem.scene_id, sem.text.split(" ")[0])
    except Exception:
        return default


def _split_with_asset(column, items, asset_column, extra):
    """If `extra` (a generated illustration Item) exists, place it ALONE
    in `asset_column` (the side opposite `column`) so the scene's image
    and its text spread across BOTH sides of the avatar instead of
    stacking together on one side — direct user instruction: a
    single-column stack reads as "скомкано" (crammed) with the other
    half of the frame left empty. Falls back to the single column when
    there's no asset (nothing to balance against)."""
    if not extra:
        return [ColumnGroup(column=column, mode="accumulate", items=items)]
    align = "right" if asset_column == "left" else "left"
    return [
        ColumnGroup(column=asset_column, mode="accumulate", align=align, items=[extra]),
        ColumnGroup(column=column, mode="accumulate", items=items),
    ]


def _maybe_illustration_item(sem, column):
    """If Gemini's semantic analysis set asset_required=true, fetch/
    generate that asset and return it as an extra Item to prepend — a
    real call (through illustration.py -> the existing image pipeline),
    not a placeholder. Returns None if no asset was required, or if
    generation wasn't available (never falls back to inventing one some
    other way)."""
    if not sem.asset_required or not sem.asset_brief:
        return None
    cw = column_width(_col_geom(column))
    # render_image_card wraps the raw photo in its own border+shadow
    # margin (components.PAD + CARD_SHADOW_BLUR on each side) — request
    # the photo narrower by exactly that much so the FINISHED card (not
    # just the raw photo) ends up card.width == cw, matching how the text
    # components already size themselves to the column.
    card_margin = 2 * (C.CARD_SHADOW_BLUR + C.PAD)
    photo_w = max(220, cw - card_margin)
    img = ILL.get_or_generate(sem.scene_id, sem.asset_brief, narration_text=sem.text, max_width=photo_w)
    if img is None:
        return None
    card = C.render_image_card(img, caption=sem.asset_caption)
    return Item(card, _first_trigger(sem), kind="asset", min_px=MIN_ASSET_PX)


def build_process_flow(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    steps = _ordered(_by_role(sem, "step"))
    if not steps:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=process_flow but no 'step' elements")
    times = enforce_min_gap([trigger_time_or_default(sem, i) for i in range(len(steps))], min_gap=1.4)
    chain = [("", e.label) for e in steps]
    img = C.render_flow_chain(chain, cw, align="left")
    render_fn = lambda s, _chain=chain, _cw=cw: C.render_flow_chain(_chain, _cw, align="left", scale=s)
    items = [Item(img, times[0], kind="text", render_fn=render_fn)]
    extra = _maybe_illustration_item(sem, "left")
    return _split_with_asset(column, items, "left", extra)


def build_cause_effect(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    role_kicker = {"cause": "Причина", "mechanism": "Механизм", "effect": "Следствие"}
    parts = [e for e in sem.elements if e.role in role_kicker]
    parts = _ordered(parts) if any(e.order for e in parts) else sorted(parts, key=lambda e: list(role_kicker).index(e.role))
    if len(parts) < 2:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=cause_effect needs >=2 of cause/mechanism/effect")
    chain = [(role_kicker[e.role], e.label) for e in parts]
    img = C.render_flow_chain(chain, cw, align="left")
    render_fn = lambda s, _chain=chain, _cw=cw: C.render_flow_chain(_chain, _cw, align="left", scale=s)
    items = [Item(img, _first_trigger(sem), kind="text", render_fn=render_fn)]
    extra = _maybe_illustration_item(sem, "left")
    return _split_with_asset(column, items, "left", extra)


def build_structured_alternatives(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    items_sem = _ordered(_by_role(sem, "item"))
    if not items_sem:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=structured_alternatives but no 'item' elements")
    labels = [e.label for e in items_sem]
    img = C.render_item_list(labels, cw, align="left")
    render_fn = lambda s, _labels=labels, _cw=cw: C.render_item_list(_labels, _cw, align="left", scale=s)
    items = [Item(img, _first_trigger(sem), kind="text", render_fn=render_fn)]
    extra = _maybe_illustration_item(sem, "left")
    return _split_with_asset(column, items, "left", extra)


def build_checklist(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    items_sem = _ordered(_by_role(sem, "item"))
    if not items_sem:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=checklist but no 'item' elements")
    labels = [e.label for e in items_sem]
    img = C.render_checklist(labels, cw, align="left")
    render_fn = lambda s, _labels=labels, _cw=cw: C.render_checklist(_labels, _cw, align="left", scale=s)
    items = [Item(img, _first_trigger(sem), kind="text", render_fn=render_fn)]
    extra = _maybe_illustration_item(sem, "left")
    return _split_with_asset(column, items, "left", extra)


def build_comparison(sem):
    """NOTE on illustration placement: when asset_required, Gemini's brief
    typically describes ONE combined side-by-side image (both cases in one
    frame) — but there is no safe region wide enough to place a single
    image spanning both columns (AVATAR_ZONE sits between them, full
    frame height). The generated illustration is placed in the LEFT
    column (paired with the left-hand case) as the best available
    compromise, not a perfect rendering of "side by side"; this is a real
    geometric constraint, not an oversight — same reasoning as the
    chevron-instead-of-center-divider decision in render_comparison_side."""
    left_els = _by_role(sem, "left")
    right_els = _by_role(sem, "right")
    if not left_els or not right_els:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=comparison needs both 'left' and 'right' elements")
    left_el, right_el = left_els[0], right_els[0]
    cw_l, cw_r = column_width(LEFT_COLUMN), column_width(RIGHT_COLUMN)
    img_l = C.render_comparison_side(left_el.label, left_el.sublabel, "left", cw_l)
    img_r = C.render_comparison_side(right_el.label, right_el.sublabel, "right", cw_r)
    render_fn_l = lambda s, _e=left_el, _cw=cw_l: C.render_comparison_side(_e.label, _e.sublabel, "left", _cw, scale=s)
    render_fn_r = lambda s, _e=right_el, _cw=cw_r: C.render_comparison_side(_e.label, _e.sublabel, "right", _cw, scale=s)
    t = _first_trigger(sem)
    left_items = [Item(img_l, t, kind="text", render_fn=render_fn_l)]
    extra = _maybe_illustration_item(sem, "left")
    if extra:
        left_items.insert(0, extra)
    return [
        ColumnGroup(column="left", mode="accumulate", align="right", items=left_items),
        ColumnGroup(column="right", mode="accumulate", align="left", items=[Item(img_r, t, kind="text", render_fn=render_fn_r)]),
    ]


def build_qa_structure(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    q = _by_role(sem, "question")
    a = _by_role(sem, "answer")
    if not q or not a:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=qa_structure needs both 'question' and 'answer'")
    img = C.render_qa(q[0].label, a[0].label, cw, align="left")
    render_fn = lambda s, _q=q[0].label, _a=a[0].label, _cw=cw: C.render_qa(_q, _a, _cw, align="left", scale=s)
    items = [Item(img, _first_trigger(sem), kind="text", render_fn=render_fn)]
    extra = _maybe_illustration_item(sem, "left")
    return _split_with_asset(column, items, "left", extra)


def build_strong_typography(sem):
    column = "left"
    cw = column_width(_col_geom(column))
    heads = _by_role(sem, "headline")
    if not heads:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=strong_typography but no 'headline' element")
    el = heads[0]
    img = C.render_headline(el.label, cw, sublabel=el.sublabel, align="left")
    render_fn = lambda s, _el=el, _cw=cw: C.render_headline(_el.label, _cw, sublabel=_el.sublabel, align="left", scale=s)
    items = [Item(img, _first_trigger(sem), kind="text", render_fn=render_fn)]
    extra = _maybe_illustration_item(sem, "right")
    return _split_with_asset(column, items, "right", extra)


def build_none(sem):
    """The system's answer for text where no STRUCTURAL text layout adds
    anything — a real, exercised path (not a fallback): semantic analysis
    decided this, not a missing case. Still checks for a required
    illustration: visual_concept="none" only means "no headline/list/etc
    needed", it does NOT mean asset_required is false — an image can
    carry the whole scene by itself with no text overlay at all."""
    column = "right"
    extra = _maybe_illustration_item(sem, column)
    if extra:
        return [ColumnGroup(column=column, mode="accumulate", items=[extra])]
    return []


def trigger_time_or_default(sem, index, default_step=1.5):
    try:
        return trigger_time(sem.scene_id, sem.elements[index].label.split(" ")[0])
    except Exception:
        return 0.3 + index * default_step


BUILDERS = {
    "process_flow": build_process_flow,
    "cause_effect": build_cause_effect,
    "structured_alternatives": build_structured_alternatives,
    "checklist": build_checklist,
    "comparison": build_comparison,
    "qa_structure": build_qa_structure,
    "strong_typography": build_strong_typography,
    "none": build_none,
}


def compose(sem):
    builder = BUILDERS.get(sem.visual_concept)
    if builder is None:
        raise SystemExit(
            f"NO VISUAL CONCEPT GENERATED FOR SCENE {sem.scene_id}: unknown concept "
            f"{sem.visual_concept!r} (no legacy fallback allowed)"
        )
    return builder(sem)
