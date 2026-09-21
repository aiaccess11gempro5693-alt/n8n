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
# 21.09.2026 (8): "сделай не оранжевый" — акцент сменён с коралла на
# приглушённый тил #2A7F82, тот же оттенок, что уже используется как
# акцентная полоса плашки субтитров (build_trend_video.py) — теперь во
# всём видео один и тот же акцентный цвет, а не два разных.
ACCENT = (42, 127, 130, 255)          # #2A7F82 — единственный акцентный цвет всей системы
ACCENT_SOFT = (42, 127, 130, 150)
SHADOW = (10, 12, 14, 165)

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
