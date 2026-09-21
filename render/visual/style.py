"""Единый визуальный язык (design tokens) — один набор шрифтов/цветов/
отступов, которым пользуются ВСЕ компоненты. Ни один компонент не имеет
права завести свой цвет или шрифт в обход этого файла — так "разные
композиции" остаются "единым design language" (п.24 мастер-промпта)."""
import os
from PIL import ImageFont

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = f"{R}/fonts"

F_BLACK = f"{FONTS}/InterDisplay-Black.otf"     # headline / keyword — primary
F_SEMIBOLD = f"{FONTS}/Inter-SemiBold.otf"       # kickers, markers, numbers
F_MEDIUM = f"{FONTS}/InterDisplay-Medium.otf"    # supporting / sublabel / list text

WHITE = (255, 255, 255, 255)
MUTED = (255, 255, 255, 200)          # sublabel / supporting text
ACCENT = (255, 107, 74, 255)          # #FF6B4A — единственный акцентный цвет всей системы
ACCENT_SOFT = (255, 107, 74, 150)
SHADOW = (10, 12, 14, 165)
# 21.09.2026 (6): текстовые карточки теперь залиты самим ACCENT (см.
# components.CARD_TEXT_FILL, "в стиле картинок" — тот же цвет, что у
# подписи-чипа под картинкой). Внутренние акцентные детали (киккеры,
# номера, чек-боксы, разделительные полосы), которые раньше рисовались
# тем же ACCENT для контраста с тёмным фоном, на акцентном фоне стали бы
# невидимыми — им нужен свой цвет, который контрастирует именно с ACCENT.
ON_ACCENT = (46, 18, 12, 255)          # тёмный тёпло-бордовый — читается и на ACCENT, и держит ту же тёплую палитру

# размеры типографики (px, canvas 1920x1080)
SIZE_KEYWORD = 108
SIZE_HEADLINE = 54
SIZE_ITEM_LABEL = 33
SIZE_SUBLABEL = 26
SIZE_KICKER = 23
SIZE_MARKER = 27

LETTER_SPACING_KICKER = 3  # px между буквами для uppercase-киккеров

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]
