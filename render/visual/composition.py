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

MIN_GAP = 1.2  # минимальный разнос между появлениями двух элементов одной сцены — см. timing.enforce_min_gap

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


def _element_trigger(sem, element, index, default_step=1.5):
    """Real, narration-synced trigger time for ONE element — 21.09.2026
    (13), direct complaint: every element of a scene used to pop onto the
    screen together, at the scene's first trigger word, so the viewer saw
    bullets/steps the narrator hadn't reached yet ("диктор говорит одно,
    а там уже а-ля спойлер к следующему"). Prefers the LLM-supplied
    `element.trigger_phrase` (an exact narration substring — see
    semantic_analysis.py) resolved through timing.trigger_time(); falls
    back to a fixed offset from the scene's first trigger only when that
    phrase is missing/unmatched (synthetic test scenes with no
    word_layout.json, or a rare LLM phrase that doesn't match verbatim)."""
    if element.trigger_phrase:
        try:
            return trigger_time(sem.scene_id, element.trigger_phrase)
        except Exception:
            pass
    return _first_trigger(sem) + index * default_step


def _synced_triggers(sem, elements, min_gap=MIN_GAP):
    """Real per-element trigger times, in the SAME order as `elements`,
    with a minimum gap enforced between whichever two end up closest in
    ACTUAL narration time (not assumed list order — comparison's
    left/right pair, for instance, isn't guaranteed to be spoken in that
    order). Each element's own real trigger is respected; only
    near-simultaneous pops get nudged apart, and only forward in time,
    per timing.enforce_min_gap's 'appeared -> flashed -> gone' rule."""
    raw = [_element_trigger(sem, e, i) for i, e in enumerate(elements)]
    time_order = sorted(range(len(raw)), key=lambda i: raw[i])
    adjusted = enforce_min_gap([raw[i] for i in time_order], min_gap=min_gap)
    out = [0.0] * len(raw)
    for pos, i in enumerate(time_order):
        out[i] = adjusted[pos]
    return out


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
    trigger = _first_trigger(sem)
    if sem.asset_trigger_phrase:
        try:
            trigger = trigger_time(sem.scene_id, sem.asset_trigger_phrase)
        except Exception:
            pass
    return Item(card, trigger, kind="asset", min_px=MIN_ASSET_PX)


def _chain_items(sem, triples):
    """triples: list[(VisualElement, kicker:str, label:str)] in narration
    order. Returns one Item PER STEP, each its own card (render_chain_step)
    with its own real, narration-synced trigger — 21.09.2026 (13), see
    _element_trigger's docstring. Used by both process_flow and
    cause_effect, which differ only in whether steps carry a kicker
    label."""
    elements = [t[0] for t in triples]
    triggers = _synced_triggers(sem, elements)
    n = len(triples)
    items = []
    for i, ((_, kicker, label), t) in enumerate(zip(triples, triggers)):
        is_final = i == n - 1
        cw = column_width(_col_geom("right"))
        img = C.render_chain_step(kicker, label, i, is_final, cw)
        render_fn = lambda s, _k=kicker, _l=label, _i=i, _f=is_final, _cw=cw: C.render_chain_step(_k, _l, _i, _f, _cw, scale=s)
        items.append(Item(img, t, kind="text", render_fn=render_fn))
    return items


def build_process_flow(sem):
    column = "right"
    steps = _ordered(_by_role(sem, "step"))
    if not steps:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=process_flow but no 'step' elements")
    items = _chain_items(sem, [(e, "", e.label) for e in steps])
    extra = _maybe_illustration_item(sem, "left")
    return _split_with_asset(column, items, "left", extra)


def build_cause_effect(sem):
    column = "right"
    role_kicker = {"cause": "Причина", "mechanism": "Механизм", "effect": "Следствие"}
    parts = [e for e in sem.elements if e.role in role_kicker]
    parts = _ordered(parts) if any(e.order for e in parts) else sorted(parts, key=lambda e: list(role_kicker).index(e.role))
    if len(parts) < 2:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=cause_effect needs >=2 of cause/mechanism/effect")
    items = _chain_items(sem, [(e, role_kicker[e.role], e.label) for e in parts])
    extra = _maybe_illustration_item(sem, "left")
    return _split_with_asset(column, items, "left", extra)


def _item_illustration(sem, element, index):
    """Per-BULLET illustration (not a shared scene-level image) — direct
    user instruction (21.09.2026 (13)): 'после ОРВИ одна картинка, после
    этого другая. БАДы, например' — each concrete list item gets its own
    small photo, keyed by a composite id so illustration.py's per-scene
    cache doesn't collide across items or across scenes."""
    if not element.asset_brief:
        return None
    return ILL.get_or_generate(
        f"{sem.scene_id}-item{index}", element.asset_brief,
        narration_text=element.label, max_width=300, aspect_ratio="1:1",
    )


def build_structured_alternatives(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    items_sem = _ordered(_by_role(sem, "item"))
    if not items_sem:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=structured_alternatives but no 'item' elements")
    triggers = _synced_triggers(sem, items_sem)
    items = []
    for i, (e, t) in enumerate(zip(items_sem, triggers)):
        thumb = _item_illustration(sem, e, i)
        if thumb is not None:
            img = C.render_list_item_with_image(i, e.label, thumb, cw)
            render_fn = lambda s, _i=i, _l=e.label, _th=thumb, _cw=cw: C.render_list_item_with_image(_i, _l, _th, _cw, scale=s)
        else:
            img = C.render_list_item(i, e.label, cw)
            render_fn = lambda s, _i=i, _l=e.label, _cw=cw: C.render_list_item(_i, _l, _cw, scale=s)
        items.append(Item(img, t, kind="text", render_fn=render_fn))
    extra = _maybe_illustration_item(sem, "left")
    return _split_with_asset(column, items, "left", extra)


def build_checklist(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    items_sem = _ordered(_by_role(sem, "item"))
    if not items_sem:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=checklist but no 'item' elements")
    triggers = _synced_triggers(sem, items_sem)
    items = []
    for i, (e, t) in enumerate(zip(items_sem, triggers)):
        thumb = _item_illustration(sem, e, i)
        if thumb is not None:
            img = C.render_checklist_item_with_image(e.label, thumb, cw)
            render_fn = lambda s, _l=e.label, _th=thumb, _cw=cw: C.render_checklist_item_with_image(_l, _th, _cw, scale=s)
        else:
            img = C.render_checklist_item(e.label, cw)
            render_fn = lambda s, _l=e.label, _cw=cw: C.render_checklist_item(_l, _cw, scale=s)
        items.append(Item(img, t, kind="text", render_fn=render_fn))
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
    # 21.09.2026 (13): each side gets its OWN real trigger — the two used
    # to share one (the scene's first trigger word), so both halves popped
    # in together even when the narrator describes them one after the
    # other. _synced_triggers sorts by actual narration time, not by
    # left/right position, so whichever side is spoken first appears
    # first regardless of its on-screen column.
    t_l, t_r = _synced_triggers(sem, [left_el, right_el])
    left_items = [Item(img_l, t_l, kind="text", render_fn=render_fn_l)]
    extra = _maybe_illustration_item(sem, "left")
    if extra:
        left_items.insert(0, extra)
    return [
        ColumnGroup(column="left", mode="accumulate", align="right", items=left_items),
        ColumnGroup(column="right", mode="accumulate", align="left", items=[Item(img_r, t_r, kind="text", render_fn=render_fn_r)]),
    ]


def build_qa_structure(sem):
    """21.09.2026 (13): question and answer now get their OWN cards and
    their OWN real triggers instead of being baked into one combined
    image at a single trigger — a question is usually posed, then
    answered somewhat LATER in the narration; showing the answer at the
    same moment as the question was exactly the "spoiler" complaint."""
    column = "right"
    cw = column_width(_col_geom(column))
    q = _by_role(sem, "question")
    a = _by_role(sem, "answer")
    if not q or not a:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=qa_structure needs both 'question' and 'answer'")
    q_el, a_el = q[0], a[0]
    t_q, t_a = _synced_triggers(sem, [q_el, a_el])
    img_q = C.render_qa_question(q_el.label, cw)
    render_fn_q = lambda s, _l=q_el.label, _cw=cw: C.render_qa_question(_l, _cw, scale=s)
    img_a = C.render_headline(a_el.label, cw, align="left")
    render_fn_a = lambda s, _l=a_el.label, _cw=cw: C.render_headline(_l, _cw, align="left", scale=s)
    items = [
        Item(img_q, t_q, kind="text", render_fn=render_fn_q),
        Item(img_a, t_a, kind="text", render_fn=render_fn_a),
    ]
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
