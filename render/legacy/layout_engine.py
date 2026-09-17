"""
Композиционный движок (design-system.md, раздел "4.1 Композиционный движок").

Реализует стадии LAYOUT -> COMPONENTS из пайплайна
CONTENT -> VISUAL HIERARCHY -> LAYOUT -> COMPONENTS -> RENDER: по паттерну
композиции и числу элементов считает координаты процедурно (единая сетка,
симметричные отступы, одинаковый размер внутри группы), вместо того чтобы
задавать x/y на каждую иконку вручную.

Контент (сколько элементов, какой текст, на каком слове появляется) сюда не
входит — это остаётся в сценарии/`compute_word_layout.py`. Этот модуль знает
только "как разместить N элементов данного паттерна", не "что в них написано".
"""

FRAME_W, FRAME_H = 1920, 1080


def single_accent(size, top, margin=60, side="right"):
    """Один главный объект сцены — крупный, у безопасного края кадра."""
    x = margin if side == "left" else FRAME_W - margin - size
    return [{"x": x, "y": top}]


def grid_2x2(size, top, margin=60, row_gap=70):
    """Независимые/альтернативные варианты (v16) — сетка 2x2, симметричная
    по обеим осям: одинаковый отступ margin от левого и правого края,
    одинаковый размер и одинаковый row_gap между строками."""
    xl = margin
    xr = FRAME_W - margin - size
    y0 = top
    y1 = top + size + row_gap
    assert xr + size + margin == FRAME_W, "сетка должна быть симметрична по горизонтали"
    return [
        {"x": xl, "y": y0},
        {"x": xr, "y": y0},
        {"x": xl, "y": y1},
        {"x": xr, "y": y1},
    ]


def vertical_list(n, size, x, top, row_gap=60):
    """Последовательность/чек-лист (v16) — одна вертикальная колонка,
    одинаковый x, одинаковый размер, одинаковый шаг между строками."""
    return [{"x": x, "y": top + i * (size + row_gap)} for i in range(n)]


def comparison_pair(size, top, margin=80):
    """Сравнение двух противоположностей (v16) — пара строго симметрична
    относительно центра кадра: одинаковый отступ margin слева и справа."""
    xl = margin
    xr = FRAME_W - margin - size
    assert xr + size + margin == FRAME_W, "пара должна быть симметрична по горизонтали"
    return [{"x": xl, "y": top}, {"x": xr, "y": top}]


def below_pos(icon_x, icon_sz, pill_w, safe_margin=20):
    """Подпись под иконкой, центрированная относительно неё (п.4), с clamp
    по безопасным полям кадра."""
    center = icon_x + icon_sz / 2
    lo, hi = safe_margin, FRAME_W - safe_margin - pill_w
    return round(max(lo, min(center - pill_w / 2, hi)))


def beside_pos(icon_x, icon_y, icon_sz, pill_h, gap=30):
    """Подпись сбоку от иконки (чек-лист/вертикальный список), центрированная
    по вертикали относительно иконки."""
    return icon_x + icon_sz + gap, round(icon_y + (icon_sz - pill_h) / 2)


def build_group(pattern_geometry, size, defs, label_mode="below"):
    """Собирает список компонентов (иконка+подпись) из geometry (LAYOUT) +
    defs (CONTENT: png/start/label/pill для каждого элемента, в том же
    порядке) — стадия COMPONENTS. Не меняет геометрию, только соединяет её
    с содержанием конкретного элемента."""
    assert len(pattern_geometry) == len(defs), "число элементов паттерна и содержания должно совпадать"
    return [{"sz": size, **geo, **content} for geo, content in zip(pattern_geometry, defs)]
