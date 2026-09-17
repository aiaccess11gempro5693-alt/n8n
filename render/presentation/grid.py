"""
Единая сетка кадра (design-system.md, "13. GRID"). Все компоненты берут
геометрию/цвета/шрифт отсюда — новых magic numbers в components.py или
compose_scene.py быть не должно.
"""
import os

RENDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = f"{RENDER}/fonts/Inter-Bold.otf"
ICONS_DIR = "/home/user/n8n/scratch"

FRAME_W, FRAME_H = 1920, 1080

SAFE_MARGIN = 60
CONTENT_MAX_W = FRAME_W - 2 * SAFE_MARGIN

COLUMN_GAP = 48      # между двумя колонками (comparison, cards left/right)
CARD_GAP = 32        # между карточками внутри одной колонки/сетки
TITLE_GAP = 28       # между заголовком блока и его содержимым
ROW_GAP = 18         # между строками чек-листа/списка

CHECKLIST_ROW_H = 84
CHECKLIST_ICON = 56

ICON_SIZE = {"sm": 64, "md": 120, "lg": 170}

# Калибровано по кадрам v29/v30 (аватар "Pharmacist Landscape" в кадре 1920x1080,
# см. проверку purple-фреймов сцен 2/3/5/6) — используется, чтобы контент не лез
# на фигуру, а не чтобы обходить свободные углы по одному и тому же шаблону.
AVATAR_SAFE_ZONE = {"x0": 640, "x1": 1290, "y0": 0, "y1": 1080}

LEFT_ZONE_X0, LEFT_ZONE_X1 = SAFE_MARGIN, AVATAR_SAFE_ZONE["x0"] - COLUMN_GAP // 2
RIGHT_ZONE_X0, RIGHT_ZONE_X1 = AVATAR_SAFE_ZONE["x1"] + COLUMN_GAP // 2, FRAME_W - SAFE_MARGIN

# Хромакей-фон Nano Banana иконок (измерено 17.09.2026 на реальных PNG: 0xE91E8F)
KEY_COLOR = (233, 30, 143)
KEY_SIMILARITY = 0.35
KEY_BLEND = 0.12

# Палитра — design-system.md, раздел 1 ("на живом видео — тёмная/насыщенная пара")
TEAL = (33, 110, 113, 255)
CORAL = (224, 93, 66, 255)
INK = (43, 47, 51, 255)
PAPER = (247, 249, 251, 255)
WHITE = (255, 255, 255, 255)

TITLE_FS = 40
EYEBROW_FS = 24
CARD_LABEL_FS = 30
CHECKLIST_FS = 30
COMPARISON_LABEL_FS = 32
HIGHLIGHT_FS = 52
