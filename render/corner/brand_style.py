"""Design tokens for the NEW "avatar-corner + universal plashka" visual
system (23.09.2026, per Oleg's call + brand boards he sent — see
CLAUDE.md, запись 23.09.2026 (1)/(4), and docs/references/
oleg-brand-board-1-2026-09-23.jpg / oleg-brand-board-2-2026-09-23.jpg).

This is a DIFFERENT brand from render/visual/style.py (which is the old
teal/coral full-frame system, still canon for any video that doesn't use
the corner format). Do not mix the two palettes on one video.
"""
import os
from PIL import ImageFont

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = f"{R}/fonts"

# Брендбук просит "Inter / Manrope" — Manrope не входит в уже
# закупленный набор шрифтов проекта (render/fonts/), а Inter — входит и
# прямо назван вторым шрифтом брендбука, так что используем то, что уже
# есть, вместо того чтобы подключать новый файл шрифта ради одной буквы
# в названии.
F_HEADLINE = f"{FONTS}/InterDisplay-Black.otf"
F_SEMIBOLD = f"{FONTS}/Inter-SemiBold.otf"
F_MEDIUM = f"{FONTS}/InterDisplay-Medium.otf"
F_CAPTION = f"{FONTS}/Inter-Bold.otf"

# Палитра — дословно с oleg-brand-board-1-2026-09-23.jpg
BLUE = (30, 79, 191, 255)          # #1E4FBF — основной синий
LIGHT_BLUE = (47, 128, 237, 255)   # #2F80ED — голубой
GREEN = (39, 174, 96, 255)         # #27AE60 — зелёный
LIGHT_BG = (245, 248, 252, 255)    # #F5F8FC — светлый фон
GRAY = (107, 114, 128, 255)        # #6B7280 — серый (вспомогательный текст)
TEXT_DARK = (30, 34, 40, 255)      # тёмный текст на светлой плашке

WHITE = (255, 255, 255, 255)

ACCENT = BLUE
ACCENT_SECONDARY = GREEN

SIZE_TITLE = 46
SIZE_BODY = 32
SIZE_CAPTION = 40
SIZE_LABEL = 26

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]
