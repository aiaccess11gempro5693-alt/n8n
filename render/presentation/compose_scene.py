"""
Оркестратор: CONTENT (content_model) -> LAYOUT (layout_rules) -> COMPONENTS
(components.py) -> GEOMETRY. Каждый layer проверяется на пересечение с
AVATAR_SAFE_ZONE и SUBTITLE_SAFE_ZONE (design-system.md, "17. Validation") —
это не просто аккуратное позиционирование "на глаз", а обязательный assert.
"""
from . import components as C
from . import content_model as M
from . import grid as G
from .layout_rules import select_layout


class Layer:
    def __init__(self, image, x, y, start, end=None):
        self.image = image
        self.x = int(x)
        self.y = int(y)
        self.start = start
        self.end = end

    def bbox(self):
        return self.x, self.y, self.x + self.image.width, self.y + self.image.height

    def assert_in_bounds(self):
        x0, y0, x1, y1 = self.bbox()
        assert x0 >= 0 and y0 >= 0 and x1 <= G.FRAME_W and y1 <= G.FRAME_H, \
            f"layer выходит за пределы кадра: {self.bbox()}"

    def _overlaps(self, zone):
        x0, y0, x1, y1 = self.bbox()
        return not (x1 <= zone["x0"] or x0 >= zone["x1"] or y1 <= zone["y0"] or y0 >= zone["y1"])

    def overlaps_avatar(self):
        return self._overlaps(G.AVATAR_SAFE_ZONE)

    def overlaps_subtitles(self):
        return self._overlaps(G.SUBTITLE_SAFE_ZONE)

    def validate(self, label=""):
        self.assert_in_bounds()
        assert not self.overlaps_avatar(), f"{label}: задевает safe zone аватара {self.bbox()}"
        assert not self.overlaps_subtitles(), f"{label}: задевает safe zone субтитров {self.bbox()}"


def _accent(name):
    return M.ACCENT[name] if name else G.TEAL


def _headline_layer(structure, max_width=None):
    text = structure.get("eyebrow")
    if not text:
        return None
    accent = _accent(structure.get("accent"))
    avail_w = max_width or (G.AVATAR_SAFE_ZONE["x0"] - G.SAFE_MARGIN - 44)
    img = C.editorial_headline(title=text, eyebrow=None, accent=accent, max_width=avail_w)
    layer = Layer(img, G.SAFE_MARGIN, G.SAFE_MARGIN,
                  start=structure.get("eyebrow_start", 0.3),
                  end=structure.get("eyebrow_end"))
    layer.validate("заголовок сцены")
    return layer


def compose_full_bleed_statement(structure):
    """1: сменяющие друг друга тезисы. Центр кадра недоступен (аватар
    занимает всю высоту), поэтому позиция — тот же верхний левый безопасный
    угол, что и у single_statement (согласованная позиция по всему ролику
    для этого уровня иерархии — п.11 design-system.md)."""
    layers = []
    avail_w = G.AVATAR_SAFE_ZONE["x0"] - G.SAFE_MARGIN - 60
    for seg in structure["segments"]:
        img = C.statement(seg["title"], accent=_accent(seg.get("accent")), max_width=avail_w)
        layer = Layer(img, G.SAFE_MARGIN, G.SAFE_MARGIN, seg["start"], seg.get("end"))
        layer.validate("statement")
        layers.append(layer)
    return layers


def compose_single_statement(structure):
    """2/4/7/8: один устойчивый тезис (eyebrow опционален)."""
    avail_w = G.AVATAR_SAFE_ZONE["x0"] - G.SAFE_MARGIN - 60
    img = C.statement(structure["title"], eyebrow=structure.get("eyebrow"),
                       accent=_accent(structure.get("accent")), max_width=avail_w)
    x = G.SAFE_MARGIN
    y = G.SAFE_MARGIN
    layer = Layer(img, x, y, structure["start"], structure.get("end"))
    layer.validate("statement")
    return [layer]


def compose_annotated_grid(structure):
    """3: N конкретных независимых причин — headline + icon_annotation в
    сетке, БЕЗ карточки-рамки вокруг каждой пары."""
    layers = []
    hl = _headline_layer(structure)
    if hl:
        layers.append(hl)
    items = structure["items"]
    zone_w = min(G.LEFT_ZONE_X1 - G.LEFT_ZONE_X0, G.RIGHT_ZONE_X1 - G.RIGHT_ZONE_X0)
    icon_size = 150
    slots_x = [G.LEFT_ZONE_X0, G.RIGHT_ZONE_X1 - zone_w]
    row_y = [G.SAFE_MARGIN, G.SAFE_MARGIN + icon_size + 40 + 60 + G.CARD_GAP]
    for i, item in enumerate(items):
        col, row = i % 2, i // 2
        img = C.icon_annotation(item["icon"], item["label"], icon_size, max_text_w=zone_w)
        x = slots_x[col] + (zone_w - img.width) // 2
        y = row_y[row]
        layer = Layer(img, x, y, item["start"])
        layer.validate(f"карточка {item['label']!r}")
        layers.append(layer)
    return layers


def compose_slim_checklist_block(structure):
    """5: один устойчивый чек-лист, показывается целиком одним блоком."""
    layers = []
    width = G.RIGHT_ZONE_X1 - G.RIGHT_ZONE_X0
    img = C.slim_checklist(structure["items"], accent=_accent(structure.get("accent")),
                            title=structure.get("title"), width=width)
    x = G.RIGHT_ZONE_X0
    y = (G.FRAME_H - img.height) // 2
    layer = Layer(img, x, y, structure["start"])
    layer.validate("чек-лист")
    layers.append(layer)
    return layers


def compose_split_comparison_layout(structure):
    """6: сравнение как единая симметричная композиция вокруг аватара —
    появляются ОБЕ половины одновременно (design-system.md, visual_goal
    сцены 6 в content_model.py: физический коннектор через центр невозможен,
    аватар занимает всю высоту центра кадра)."""
    layers = []
    hl = _headline_layer(structure)
    if hl:
        layers.append(hl)
    left, right = structure["left"], structure["right"]
    w = G.LEFT_ZONE_X1 - G.LEFT_ZONE_X0
    h = 150
    y = (G.FRAME_H - h) // 2
    l_img = C.split_comparison_side(left["label"], _accent(left["accent"]), w=w, height=h, align="right")
    r_img = C.split_comparison_side(right["label"], _accent(right["accent"]), w=w, height=h, align="left")
    l_layer = Layer(l_img, G.LEFT_ZONE_X0, y, structure["start"])
    r_layer = Layer(r_img, G.RIGHT_ZONE_X0, y, structure["start"])
    l_layer.validate("сравнение (слева)")
    r_layer.validate("сравнение (справа)")
    layers += [l_layer, r_layer]
    return layers


COMPOSERS = {
    "full_bleed_statement": compose_full_bleed_statement,
    "single_statement": compose_single_statement,
    "annotated_grid": compose_annotated_grid,
    "slim_checklist_block": compose_slim_checklist_block,
    "split_comparison_layout": compose_split_comparison_layout,
}


def compose_scene(scene_n):
    structure = M.get_structure(scene_n)
    layout = select_layout(structure)
    layers = COMPOSERS[layout](structure)
    return layout, layers
