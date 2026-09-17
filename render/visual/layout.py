"""
COMPOSITION -> GEOMETRY. Единственное место, где считаются пиксели x/y.
Ничего здесь не знает о смысле контента — только о геометрии колонки,
размерах уже отрендеренных PNG и правилах отступов/центрирования.
"""
from dataclasses import dataclass

from .components import PAD
from .safe_zones import LEFT_COLUMN, RIGHT_COLUMN, column_height

GAP = 14  # доп. зазор между слотами поверх собственного PAD каждого PNG


@dataclass
class PlacedItem:
    image: object
    x: int
    y: int
    trigger: float
    fade_out: float | None = None   # для "replace"-групп: когда этот item должен погаснуть


def _col_geom(column):
    return LEFT_COLUMN if column == "left" else RIGHT_COLUMN


def _frame_x(column, align, img_width):
    col = _col_geom(column)
    if align == "left":
        return col["x0"] - PAD
    return col["x1"] - img_width + PAD


def place_group(group):
    """Возвращает список PlacedItem для одной ColumnGroup, вертикально
    центрированной в безопасной высоте колонки."""
    col = _col_geom(group.column)
    heights = [it.image.height for it in group.items]
    total_h = sum(heights) + GAP * (len(heights) - 1)
    avail_h = column_height(col)
    if total_h > avail_h:
        # last-resort: сжимаем межстрочный зазор, не шрифт (п.22 мастер-промпта)
        shrink_gap = max(0, (avail_h - sum(heights)) // max(1, len(heights) - 1))
        total_h = sum(heights) + shrink_gap * (len(heights) - 1)
        gap = shrink_gap
        print(f"WARNING: column {group.column} overflow, gap shrunk to {gap}px")
    else:
        gap = GAP

    y = col["y0"] + max(0, (avail_h - total_h) // 2)
    placed = []
    for i, item in enumerate(group.items):
        x = _frame_x(group.column, group.align, item.image.width)
        placed.append(PlacedItem(image=item.image, x=x, y=y, trigger=item.trigger))
        y += item.image.height + gap

    if group.mode == "replace":
        # каждая стадия гаснет ровно в момент, когда должна появиться следующая
        for i in range(len(placed) - 1):
            placed[i].fade_out = placed[i + 1].trigger
        # все стадии занимают одно и то же место (стек, не список) -> пересчитать
        # позицию: каждая стадия центрируется в колонке САМА ПО СЕБЕ (не как часть стопки)
        placed = []
        for item in group.items:
            x = _frame_x(group.column, group.align, item.image.width)
            y = col["y0"] + max(0, (avail_h - item.image.height) // 2)
            placed.append(PlacedItem(image=item.image, x=x, y=y, trigger=item.trigger))
        for i in range(len(placed) - 1):
            placed[i].fade_out = placed[i + 1].trigger

    return placed
