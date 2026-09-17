"""
Оркестратор: CONTENT (content_model) -> LAYOUT (layout_rules) -> COMPONENTS
(components.py) -> GEOMETRY (этот файл расставляет готовые изображения по
слотам, компоненты сами себя не позиционируют). Ffmpeg дальше просто
накладывает готовые PNG по (x, y, start) — тот же приём, что уже работает
для pill/headline в build_trend_video.py, но теперь один слой на компонент,
а не два синхронизируемых слоя (иконка + отдельная pill).

Каждый layout явно проверяется на пересечение с AVATAR_SAFE_ZONE — компонент
не размещается поверх фигуры (design-system.md, "8. AVATAR — часть
composition").
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

    def assert_in_bounds(self):
        x1, y1 = self.x + self.image.width, self.y + self.image.height
        assert self.x >= 0 and self.y >= 0 and x1 <= G.FRAME_W and y1 <= G.FRAME_H, \
            f"layer выходит за пределы кадра: ({self.x},{self.y})-({x1},{y1})"

    def overlaps_avatar(self):
        z = G.AVATAR_SAFE_ZONE
        x1, y1 = self.x + self.image.width, self.y + self.image.height
        return not (x1 <= z["x0"] or self.x >= z["x1"] or y1 <= z["y0"] or self.y >= z["y1"])


def _accent(name):
    return M.ACCENT[name]


def _scene_headline_layer(structure):
    """Заголовок сцены (design-system.md '5. Заголовок') — верхний левый угол
    ТОЛЬКО для layout'ов, где этот угол ничем больше не занят (совпадает с
    прежним правилом v16/17, теперь явно проверяется, а не предполагается)."""
    text = structure.get("eyebrow")
    if not text:
        return None
    accent = _accent(structure.get("accent", "teal"))
    avail_w = G.AVATAR_SAFE_ZONE["x0"] - G.SAFE_MARGIN - 40  # не залезать под аватара текстом заголовка
    img = C.headline(title=text, eyebrow=None, accent=accent, max_width=avail_w)
    layer = Layer(img, G.SAFE_MARGIN, G.SAFE_MARGIN,
                  start=structure.get("eyebrow_start", 0.3),
                  end=structure.get("eyebrow_end"))
    assert not layer.overlaps_avatar(), "заголовок сцены задевает безопасную зону аватара"
    return layer


def compose_highlight_center(structure):
    layers = []
    for seg in structure["segments"]:
        img = C.highlight(seg["title"], accent=_accent(seg.get("accent", "teal")))
        x = (G.FRAME_W - img.width) // 2
        y = G.SAFE_MARGIN + 30
        layers.append(Layer(img, x, y, seg["start"], seg.get("end")))
    return layers


def compose_key_point(structure):
    layers = []
    hl = _scene_headline_layer(structure)
    if hl:
        layers.append(hl)
    item = structure["items"][0]
    accent = _accent(item.get("accent", structure.get("accent", "coral")))
    block = C.card(item["icon"], item["label"], w=460, h=280, accent=accent, icon_size=170)
    x = G.RIGHT_ZONE_X1 - block.width
    y = (G.FRAME_H - block.height) // 2
    layer = Layer(block, x, y, item["start"])
    assert not layer.overlaps_avatar()
    layers.append(layer)
    return layers


def _uniform_card_size(items, icon_size, fs, width, pad=32, gap=16):
    """Измеряет содержимое ВСЕХ карточек группы заранее и возвращает один
    height, которого хватит для самой крупной подписи — чтобы карточки были
    РЕАЛЬНО одного размера (не 'одинаково запрошенного', который потом
    молча растягивается только у одной из них)."""
    max_h = 0
    for it in items:
        _, bh = C.measure_icon_label(it["icon"], it["label"], icon_size, fs,
                                      max_text_w=width - 2 * pad, gap=gap)
        max_h = max(max_h, bh + 2 * pad)
    return width, max_h


def compose_cards_grid(structure):
    layers = []
    hl = _scene_headline_layer(structure)
    if hl:
        layers.append(hl)
    items = structure["items"]
    zone_w = min(G.LEFT_ZONE_X1 - G.LEFT_ZONE_X0, G.RIGHT_ZONE_X1 - G.RIGHT_ZONE_X0)
    icon_size = 140
    card_w, card_h = _uniform_card_size(items, icon_size, G.CARD_LABEL_FS, zone_w)
    y0 = G.SAFE_MARGIN
    y1 = y0 + card_h + G.CARD_GAP
    slots = [
        (G.LEFT_ZONE_X0, y0), (G.RIGHT_ZONE_X1 - card_w, y0),
        (G.LEFT_ZONE_X0, y1), (G.RIGHT_ZONE_X1 - card_w, y1),
    ]
    for item, (x, y) in zip(items, slots):
        accent = _accent(item.get("accent", "teal"))
        img = C.card(item["icon"], item["label"], card_w, card_h, accent=accent, icon_size=icon_size)
        assert img.height == card_h, "карточка не должна самовосстанавливаться, если размер уже измерен верно"
        layer = Layer(img, x, y, item["start"])
        assert not layer.overlaps_avatar(), f"карточка {item['label']!r} задевает аватара"
        layers.append(layer)
    return layers


def compose_checklist_block(structure):
    layers = []
    hl = _scene_headline_layer(structure)
    persistent_heading = hl is not None and hl.end is None
    if hl:
        layers.append(hl)
    items = structure["items"]
    width = G.RIGHT_ZONE_X1 - G.RIGHT_ZONE_X0
    icon_files = [it["icon"] for it in items]
    labels = [it["label"] for it in items]
    # если заголовок сцены держится всю сцену — не дублируем текст внутри
    # панели чек-листа; если гаснет заранее — панель получает свой заголовок.
    panel_title = None if persistent_heading else structure.get("eyebrow")
    img = C.checklist(panel_title, labels, width, icon_files=icon_files,
                       accent=_accent(structure.get("accent", "teal")))
    x = G.RIGHT_ZONE_X0
    y = (G.FRAME_H - img.height) // 2
    block_layer = Layer(img, x, y, items[0]["start"])
    assert not block_layer.overlaps_avatar()
    layers.append(block_layer)
    return layers


def compose_comparison_pair(structure):
    layers = []
    hl = _scene_headline_layer(structure)
    if hl:
        layers.append(hl)
    left, right = structure["left"], structure["right"]
    w = 460
    icon_size = min(w, 520) // 2
    _, h = _uniform_card_size([left, right], icon_size, G.COMPARISON_LABEL_FS, w)
    y = (G.FRAME_H - h) // 2
    l_img = C.comparison_side(left["icon"], left["label"], w, h, accent=_accent(left.get("accent", "coral")), icon_size=icon_size)
    r_img = C.comparison_side(right["icon"], right["label"], w, h, accent=_accent(right.get("accent", "teal")), icon_size=icon_size)
    l_layer = Layer(l_img, G.LEFT_ZONE_X1 - w, y, left["start"])
    r_layer = Layer(r_img, G.RIGHT_ZONE_X0, y, right["start"])
    assert not l_layer.overlaps_avatar() and not r_layer.overlaps_avatar()
    layers += [l_layer, r_layer]
    return layers


COMPOSERS = {
    "highlight_center": compose_highlight_center,
    "key_point_accent": compose_key_point,
    "cards_grid": compose_cards_grid,
    "checklist_block": compose_checklist_block,
    "comparison_pair": compose_comparison_pair,
}


def compose_scene(scene_n):
    structure = M.get_structure(scene_n)
    layout = select_layout(structure)
    layers = COMPOSERS[layout](structure)
    for l in layers:
        l.assert_in_bounds()
    return layout, layers
