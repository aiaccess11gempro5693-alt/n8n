"""
CONTENT + VISUAL_CONCEPT -> COMPOSITION.

Каждый builder получает SceneSemantics и возвращает список ColumnGroup —
это ещё НЕ пиксели (тем занимается layout.py), а решение о том:
- в какую колонку идёт группа (left/right/both — avatar их естественно
  разделяет, ни одна группа никогда не претендует на обе одновременно,
  кроме comparison_pair, где это две независимые группы по одной в
  каждой колонке);
- как элементы группы появляются относительно друг друга —
  "accumulate" (список копится, ничего не пропадает) или "replace"
  (следующий сменяет предыдущий — только для двухфазных keyword/headline);
- когда (локальный триггер сцены, уже прошедший через enforce_min_gap).

Диспетчеризация — по `sem.visual_concept` (строка = классификация
информационной структуры контента), НЕ по `sem.scene`. Один и тот же
concept на двух разных сценах проходит через один и тот же builder.
"""
from dataclasses import dataclass, field

from . import components as C
from .safe_zones import column_width, LEFT_COLUMN, RIGHT_COLUMN
from .timing import trigger_time, enforce_min_gap


@dataclass
class Item:
    image: object
    trigger: float


@dataclass
class ColumnGroup:
    column: str          # "left" | "right"
    mode: str             # "accumulate" | "replace"
    align: str = "left"   # "left" -> content hugs column's outer edge; "right" -> hugs the avatar-facing edge
    items: list = field(default_factory=list)   # list[Item]


def _col_geom(column):
    return LEFT_COLUMN if column == "left" else RIGHT_COLUMN


def _align_for(column):
    # список/заголовок читается от аватара наружу, кроме comparison (см. build_comparison_pair)
    return "left" if column == "right" else "right"


def build_keyword_emphasis(sem):
    column = "left"
    cw = column_width(_col_geom(column))
    align = "left"
    stage1, stage2 = sem.elements[0], sem.elements[1]
    t1 = trigger_time(sem.scene, stage1.trigger_phrase)
    t2 = trigger_time(sem.scene, stage2.trigger_phrase)
    t1, t2 = enforce_min_gap([t1, t2], min_gap=1.6)
    img1 = C.render_kicker_word(stage1.kicker, stage1.label, cw, align=align)
    img2 = C.render_headline(stage2.label, cw, sublabel=stage2.sublabel, align=align)
    return [ColumnGroup(column=column, mode="replace", items=[Item(img1, t1), Item(img2, t2)])]


def build_typography_only(sem):
    column = "left"
    cw = column_width(_col_geom(column))
    el = sem.elements[0]
    t = trigger_time(sem.scene, el.trigger_phrase)
    img = C.render_headline(el.label, cw, kicker=el.kicker, sublabel=el.sublabel, align="left")
    return [ColumnGroup(column=column, mode="accumulate", items=[Item(img, t)])]


def build_process_sequence(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    times = enforce_min_gap([trigger_time(sem.scene, e.trigger_phrase) for e in sem.elements], min_gap=1.4)
    items = []
    for i, (el, t) in enumerate(zip(sem.elements, times), start=1):
        img = C.render_list_item(f"{i:02d}", el.label, cw, marker_style="node", align="left")
        items.append(Item(img, t))
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


def build_options_grid(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    times = enforce_min_gap([trigger_time(sem.scene, e.trigger_phrase) for e in sem.elements], min_gap=1.0)
    items = []
    for i, (el, t) in enumerate(zip(sem.elements, times), start=1):
        img = C.render_list_item(f"{i:02d}", el.label, cw, marker_style="number", align="left")
        items.append(Item(img, t))
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


def build_checklist_vertical(sem):
    column = "right"
    cw = column_width(_col_geom(column))
    times = enforce_min_gap([trigger_time(sem.scene, e.trigger_phrase) for e in sem.elements], min_gap=1.0)
    items = []
    for el, t in zip(sem.elements, times):
        img = C.render_list_item("", el.label, cw, marker_style="check", align="left")
        items.append(Item(img, t))
    return [ColumnGroup(column=column, mode="accumulate", items=items)]


def build_comparison_pair(sem):
    left_el, right_el = sem.elements[0], sem.elements[1]
    t_left = trigger_time(sem.scene, left_el.trigger_phrase)
    t_right = trigger_time(sem.scene, right_el.trigger_phrase)
    t_left, t_right = enforce_min_gap([t_left, t_right], min_gap=1.6)

    cw_l = column_width(LEFT_COLUMN)
    cw_r = column_width(RIGHT_COLUMN)
    # мирроринг: обе половины "смотрят" друг на друга через аватар —
    # левая прижата к правому краю своей колонки, правая к левому краю своей.
    img_l = C.render_headline(left_el.label, cw_l, sublabel=left_el.sublabel, align="right", accent_bar=True)
    img_r = C.render_headline(right_el.label, cw_r, sublabel=right_el.sublabel, align="left", accent_bar=True)
    return [
        ColumnGroup(column="left", mode="accumulate", align="right", items=[Item(img_l, t_left)]),
        ColumnGroup(column="right", mode="accumulate", align="left", items=[Item(img_r, t_right)]),
    ]


BUILDERS = {
    "keyword_emphasis": build_keyword_emphasis,
    "typography_only": build_typography_only,
    "process_sequence": build_process_sequence,
    "options_grid": build_options_grid,
    "checklist_vertical": build_checklist_vertical,
    "comparison_pair": build_comparison_pair,
}


def compose(sem):
    builder = BUILDERS.get(sem.visual_concept)
    if builder is None:
        raise SystemExit(
            f"NO VISUAL CONCEPT GENERATED FOR SCENE {sem.scene}: unknown concept "
            f"{sem.visual_concept!r} (no legacy fallback allowed)"
        )
    return builder(sem)
