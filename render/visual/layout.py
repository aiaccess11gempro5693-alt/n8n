"""
COMPOSITION -> GEOMETRY. Единственное место, где считаются пиксели x/y.

21.09.2026 — переписан после Test D2 (illustration + 3-item text chain
переполнял колонку и заходил в SUBTITLE_ZONE). Раньше `place_group` умела
только одно: сжимать зазор между уже отрендеренными PNG вплоть до 0px —
если и это не помогало, элемент всё равно размещался, переполняя колонку
(итоговый overflow ловил только validate.py постфактум).

Теперь это настоящий layout solver: пробует несколько валидных
композиций по порядку приоритета, каждая проверяется ДО размещения (не
после), и только первая подходящая реально используется:

  1. stack, всё в полный размер
  2. stack, asset уменьшается пошагово — текст остаётся чётким, полного
     размера
  3. stack, текст уменьшается пошагово (до MIN_TEXT_SCALE=0.82) —
     перерендер компонентом на меньшем font size (не блюр растра), asset
     остаётся полного размера
  4. stack, asset И текст уменьшаются вместе пропорционально
  5. side-by-side (asset слева, текст справа) — только для пары
     "1 asset + 1 текст", и только если уже отрендеренный текст физически
     умещается по ширине в оставшееся место (компонент не умеет
     перерендериться на новую ширину — честное ограничение,
     задокументировано, не скрыто)

Если НИ ОДИН кандидат не проходит — `LayoutSolveError` с полным списком
попыток и причин. Никакого молчаливого overflow, никакого удаления
asset, никакого scene-specific исключения: всё это работает по kind
("text" | "asset") элемента, не по content/scene_id.
"""
from dataclasses import dataclass

from .components import PAD
from .safe_zones import LEFT_COLUMN, RIGHT_COLUMN, column_height, column_width

GAP = 14                 # предпочтительный зазор между элементами колонки
GAP_MIN = 0               # зазор пробуется вплоть до нуля на каждом шаге масштаба, прежде чем шаг считается неудачным
TEXT_SCALE_STEPS = [1.0, 0.94, 0.88, 0.82]      # MIN_TEXT_SCALE = 0.82 — floor "минимально читаемого" font size
ASSET_SCALE_STEPS = [1.0, 0.88, 0.76, 0.64]      # дальше ограничен item.min_px, не только шагом


@dataclass
class PlacedItem:
    image: object
    x: int
    y: int
    trigger: float
    fade_out: float | None = None   # для "replace"-групп: когда этот item должен погаснуть


class LayoutSolveError(Exception):
    """Composition must fail explicitly — см. докстринг файла, п.23 общего
    правила проекта (никакого тихого fallback). `.candidates` — полный
    список того, что solver пробовал и почему каждый вариант не подошёл."""
    def __init__(self, message, candidates):
        super().__init__(message)
        self.candidates = candidates


def _col_geom(column):
    return LEFT_COLUMN if column == "left" else RIGHT_COLUMN


def _frame_x(column, align, img_width):
    col = _col_geom(column)
    if align == "left":
        return col["x0"] - PAD
    return col["x1"] - img_width + PAD


def _render_at(item, scale):
    """Returns the Image for `item` at `scale`. For kind="text" this is a
    genuine re-render (crisp at the new font size) via item.render_fn; for
    kind="asset" this is a plain resize (a generated illustration
    tolerates modest downscaling far better than text does — that's the
    whole reason text gets render_fn and assets don't)."""
    if item.kind == "asset":
        if scale >= 1.0:
            return item.image
        w = max(item.min_px, round(item.image.width * scale))
        ratio = w / item.image.width
        h = max(1, round(item.image.height * ratio))
        return item.image.resize((w, h))
    if item.render_fn is None or scale >= 1.0:
        return item.image
    return item.render_fn(scale)


def _asset_floor_scale(item):
    """The smallest scale that still keeps an asset >= its min_px."""
    if item.kind != "asset" or item.image.width <= 0:
        return 1.0
    return item.min_px / item.image.width


def _fits(col, images, gap):
    """Height-only check for a VERTICAL stack, matching the original
    pre-solver `place_group` exactly (it never checked width either).
    Width isn't a stacking concern: every text component is already
    wrapped to its column's max_width at render time (each component
    decides its own canvas padding — render_checklist's spine adds a few
    extra px beyond render_flow_chain's, for instance — so there's no
    single correct fixed width-budget constant to compare against here).
    The real, accurate width/avatar-zone/frame-bounds safety check is
    validate.py's job, same as it always was; this solver's width
    awareness is only needed where two items sit side by side (see
    _try_side_by_side), because THAT is a case single-column stacking
    never had to consider."""
    total_h = sum(im.height for im in images) + gap * max(0, len(images) - 1)
    max_w = max((im.width for im in images), default=0)
    return total_h <= column_height(col), total_h, max_w


def _best_gap_for(col, images):
    """Prefer GAP; fall back to a shrunk gap (down to GAP_MIN) before
    declaring this scale step a failure — cheap and doesn't cost
    legibility, so it's tried at every scale step rather than being its
    own separate top-level candidate."""
    ok, total_h, max_w = _fits(col, images, GAP)
    if ok:
        return True, GAP, total_h, max_w
    if len(images) > 1:
        shrink_gap = max(GAP_MIN, (column_height(col) - sum(im.height for im in images)) // (len(images) - 1))
        ok2, total_h2, max_w2 = _fits(col, images, shrink_gap)
        if ok2:
            return True, shrink_gap, total_h2, max_w2
    return False, GAP, total_h, max_w


def _place_stack(col, group, items, images, gap):
    y = col["y0"] + max(0, (column_height(col) - (sum(im.height for im in images) + gap * max(0, len(images) - 1))) // 2)
    placed = []
    for item, img in zip(items, images):
        x = _frame_x(group.column, group.align, img.width)
        placed.append(PlacedItem(image=img, x=x, y=y, trigger=item.trigger))
        y += img.height + gap
    return placed


def _try_side_by_side(col, asset_item, text_item, candidates_tried):
    """Only for the 2-item "1 asset + 1 text" shape. Does NOT re-wrap the
    text at a new width (render_fn only takes a scale, not a width) —
    tries the text image as already rendered (optionally scaled down) and
    checks whether it actually fits the leftover width. A real, honest
    attempt: succeeds only when the content allows it, not simulated."""
    for a_scale in ASSET_SCALE_STEPS:
        if a_scale < _asset_floor_scale(asset_item) - 1e-6:
            continue
        asset_img = _render_at(asset_item, a_scale)
        # +40px tolerance matches the real gap this column already has to
        # AVATAR_ZONE (see safe_zones.py) — generous on purpose, since
        # component canvases carry a few px of their own padding that
        # varies per component (see _fits()); validate.py's real
        # frame/avatar-zone/collision checks are the final authority, not
        # this estimate.
        leftover_w = column_width(col) + 40 - asset_img.width - GAP
        if leftover_w < 80:
            candidates_tried.append({"label": f"side_by_side(asset_scale={a_scale})", "ok": False,
                                      "reason": f"leftover width {leftover_w}px too narrow for any text"})
            continue
        for t_scale in TEXT_SCALE_STEPS:
            text_img = _render_at(text_item, t_scale)
            fits_w = text_img.width <= leftover_w
            fits_h = max(asset_img.height, text_img.height) <= column_height(col)
            candidates_tried.append({
                "label": f"side_by_side(asset_scale={a_scale}, text_scale={t_scale})", "ok": fits_w and fits_h,
                "asset_wh": (asset_img.width, asset_img.height), "text_wh": (text_img.width, text_img.height),
                "leftover_w": leftover_w, "avail_h": column_height(col),
            })
            if fits_w and fits_h:
                return True, asset_img, text_img
    return False, None, None


def place_group(group):
    """Возвращает список PlacedItem для одной ColumnGroup. Пустая группа
    -> []. Одноэлементная группа без asset — по факту то же самое, что
    было раньше (кандидат 1 почти всегда проходит сразу). Solver
    по-настоящему перебирает варианты только когда есть что распределять
    (asset + текст, или несколько текстов, которые всё же не влезают)."""
    col = _col_geom(group.column)
    items = group.items
    if not items:
        return []

    if group.mode == "replace":
        placed = []
        for item in items:
            img = item.image
            x = _frame_x(group.column, group.align, img.width)
            y = col["y0"] + max(0, (column_height(col) - img.height) // 2)
            placed.append(PlacedItem(image=img, x=x, y=y, trigger=item.trigger))
        for i in range(len(placed) - 1):
            placed[i].fade_out = placed[i + 1].trigger
        return placed

    candidates_tried = []

    def try_stack(text_scale, asset_scale, label):
        images = [_render_at(it, asset_scale if it.kind == "asset" else text_scale) for it in items]
        fits, gap_used, total_h, max_w = _best_gap_for(col, images)
        candidates_tried.append({
            "label": label, "ok": fits, "gap": gap_used, "total_h": total_h, "max_w": max_w,
            "avail_h": column_height(col), "avail_w": column_width(col),
            "sizes": [(im.width, im.height) for im in images],
        })
        return fits, images, gap_used

    # 1. full size
    fits, images, gap_used = try_stack(1.0, 1.0, "stack_full")
    if fits:
        return _place_stack(col, group, items, images, gap_used)

    has_asset = any(it.kind == "asset" for it in items)
    has_scalable_text = any(it.kind == "text" and it.render_fn for it in items)

    # 2. shrink asset only
    if has_asset:
        for s in ASSET_SCALE_STEPS[1:]:
            fits, images, gap_used = try_stack(1.0, s, f"stack_asset_scale_{s}")
            if fits:
                return _place_stack(col, group, items, images, gap_used)

    # 3. shrink text only
    if has_scalable_text:
        for s in TEXT_SCALE_STEPS[1:]:
            fits, images, gap_used = try_stack(s, 1.0, f"stack_text_scale_{s}")
            if fits:
                return _place_stack(col, group, items, images, gap_used)

    # 4. shrink both together
    if has_asset and has_scalable_text:
        for ts, aS in zip(TEXT_SCALE_STEPS[1:], ASSET_SCALE_STEPS[1:]):
            fits, images, gap_used = try_stack(ts, aS, f"stack_both_text_{ts}_asset_{aS}")
            if fits:
                return _place_stack(col, group, items, images, gap_used)

    # 5. side-by-side, only for the canonical "1 asset + 1 text" pair
    asset_items = [it for it in items if it.kind == "asset"]
    text_items = [it for it in items if it.kind == "text"]
    if len(items) == 2 and len(asset_items) == 1 and len(text_items) == 1:
        fits, asset_img, text_img = _try_side_by_side(col, asset_items[0], text_items[0], candidates_tried)
        if fits:
            ax = col["x0"] - PAD
            tx = ax + asset_img.width + GAP
            top = col["y0"] + max(0, (column_height(col) - max(asset_img.height, text_img.height)) // 2)
            return [
                PlacedItem(image=asset_img, x=ax, y=top, trigger=asset_items[0].trigger),
                PlacedItem(image=text_img, x=tx, y=top, trigger=text_items[0].trigger),
            ]

    raise LayoutSolveError(
        f"scene {group.column} column: no layout candidate fit within safe bounds "
        f"(avail={column_width(col)}x{column_height(col)}px, tried {len(candidates_tried)} candidates)",
        candidates_tried,
    )
