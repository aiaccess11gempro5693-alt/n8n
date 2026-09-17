"""
Геометрия кадра 1920x1080 и реальные safe zones, измеренные по кадрам
канонических клипов аватара (все 8 сцен: /tmp/final-scenes/scene-N.mp4,
кадр из середины каждой сцены, см. отчёт в чате) — аватар везде в одной и
той же статичной поясной рамке по центру кадра, поэтому одна геометрия
общая для всех сцен, а не подбирается на глаз под каждую отдельно.

Все visual-компоненты обязаны укладываться в LEFT_COLUMN или
RIGHT_COLUMN. Ни один элемент не может быть помещён в AVATAR_ZONE или
SUBTITLE_ZONE — это проверяется в validate.py, а не только соблюдается
по договорённости.
"""

FRAME_W, FRAME_H = 1920, 1080
SAFE_PAD = 20  # минимальный отступ от края кадра

# Аватар: плечи/голова говорящего, измерено по фактическим кадрам — везде
# в одном и том же месте (позиция не меняется по ходу сцены, только лёгкий
# Ken Burns zoom +3.5% максимум, что не меняет эту зону значимо).
AVATAR_ZONE = {"x0": 600, "y0": 0, "x1": 1340, "y1": FRAME_H}

# Субтитровая плашка — из render/compute_word_layout.py (PANEL), тот же
# источник истины, не задаётся заново.
SUBTITLE_ZONE = {"x0": 290, "y0": 890, "x1": 1630, "y1": 1060}

TOP_SAFE_Y = 110      # выше — риск задеть верх кадра/голову на ближних планах
BOTTOM_SAFE_Y = 875   # ниже (до SUBTITLE_ZONE.y0 - зазор) — не оставляем visual-слою

LEFT_COLUMN = {"x0": SAFE_PAD + 50, "x1": AVATAR_ZONE["x0"] - 40, "y0": TOP_SAFE_Y, "y1": BOTTOM_SAFE_Y}
RIGHT_COLUMN = {"x0": AVATAR_ZONE["x1"] + 40, "x1": FRAME_W - SAFE_PAD - 50, "y0": TOP_SAFE_Y, "y1": BOTTOM_SAFE_Y}


def column_width(col):
    return col["x1"] - col["x0"]


def column_height(col):
    return col["y1"] - col["y0"]


def zones_overlap(a, b):
    return not (a["x1"] <= b["x0"] or b["x1"] <= a["x0"] or a["y1"] <= b["y0"] or b["y1"] <= a["y0"])


assert not zones_overlap(LEFT_COLUMN, AVATAR_ZONE)
assert not zones_overlap(RIGHT_COLUMN, AVATAR_ZONE)
assert not zones_overlap(LEFT_COLUMN, SUBTITLE_ZONE)
assert not zones_overlap(RIGHT_COLUMN, SUBTITLE_ZONE)
