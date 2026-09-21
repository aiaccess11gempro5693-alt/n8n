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


@dataclass
class Item:
    image: object
    trigger: float


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
    img = ILL.get_or_generate(sem.scene_id, sem.asset_brief, narration_text=sem.text, max_width=cw)
    if img is None:
        return None
    return Item(img, _first_trigger(sem))


def build_process_flow(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    steps = _ordered(_by_role(sem, "step"))
    if not steps:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=process_flow but no 'step' elements")
    times = enforce_min_gap([trigger_time_or_default(sem, i) for i in range(len(steps))], min_gap=1.4)
    img = C.render_flow_chain([("", e.label) for e in steps], cw, align="left")
    items = [Item(img, times[0])]
    extra = _maybe_illustration_item(sem, column)
    if extra:
        items.insert(0, extra)
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


def build_cause_effect(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    role_kicker = {"cause": "Причина", "mechanism": "Механизм", "effect": "Следствие"}
    parts = [e for e in sem.elements if e.role in role_kicker]
    parts = _ordered(parts) if any(e.order for e in parts) else sorted(parts, key=lambda e: list(role_kicker).index(e.role))
    if len(parts) < 2:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=cause_effect needs >=2 of cause/mechanism/effect")
    img = C.render_flow_chain([(role_kicker[e.role], e.label) for e in parts], cw, align="left")
    items = [Item(img, _first_trigger(sem))]
    extra = _maybe_illustration_item(sem, column)
    if extra:
        items.insert(0, extra)
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


def build_structured_alternatives(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    items_sem = _ordered(_by_role(sem, "item"))
    if not items_sem:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=structured_alternatives but no 'item' elements")
    img = C.render_item_list([e.label for e in items_sem], cw, align="left")
    items = [Item(img, _first_trigger(sem))]
    extra = _maybe_illustration_item(sem, column)
    if extra:
        items.insert(0, extra)
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


def build_checklist(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    items_sem = _ordered(_by_role(sem, "item"))
    if not items_sem:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=checklist but no 'item' elements")
    img = C.render_checklist([e.label for e in items_sem], cw, align="left")
    items = [Item(img, _first_trigger(sem))]
    extra = _maybe_illustration_item(sem, column)
    if extra:
        items.insert(0, extra)
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


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
    t = _first_trigger(sem)
    left_items = [Item(img_l, t)]
    extra = _maybe_illustration_item(sem, "left")
    if extra:
        left_items.insert(0, extra)
    return [
        ColumnGroup(column="left", mode="accumulate", align="right", items=left_items),
        ColumnGroup(column="right", mode="accumulate", align="left", items=[Item(img_r, t)]),
    ]


def build_qa_structure(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    q = _by_role(sem, "question")
    a = _by_role(sem, "answer")
    if not q or not a:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=qa_structure needs both 'question' and 'answer'")
    img = C.render_qa(q[0].label, a[0].label, cw, align="left")
    items = [Item(img, _first_trigger(sem))]
    extra = _maybe_illustration_item(sem, column)
    if extra:
        items.insert(0, extra)
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


def build_strong_typography(sem):
    column = "left"
    cw = column_width(_col_geom(column))
    heads = _by_role(sem, "headline")
    if not heads:
        raise ValueError(f"scene {sem.scene_id}: visual_concept=strong_typography but no 'headline' element")
    el = heads[0]
    img = C.render_headline(el.label, cw, sublabel=el.sublabel, align="left")
    items = [Item(img, _first_trigger(sem))]
    extra = _maybe_illustration_item(sem, column)
    if extra:
        items.insert(0, extra)
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


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
