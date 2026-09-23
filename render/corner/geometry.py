"""Геометрия формата "аватар уезжает в угол + плашка" (23.09.2026,
прямое ТЗ с созвона — см. CLAUDE.md). Кадр 1920x1080.

Механика подтверждена и переиспользована из
render/experiments/build_pip_test.py (22.09.2026) — там же анимированный
scale/overlay с eval=frame уже был опробован на реальном рендере. Отличия
от того прототипа: угол — правый НИЖНИЙ (Олег на созвоне: "лучше в
правый нижний"), а не правый верхний (более позднего фидбэка по PIP-
экспериментам это не касалось — тот трек проверял другую композицию
целиком, см. CLAUDE.md 22.09.2026 (1)-(10)).
"""

FRAME_W, FRAME_H = 1920, 1080

# Полноэкранная фаза — аватар говорит, ничего не отвлекает.
FULL_W, FULL_H = FRAME_W, FRAME_H
FULL_X, FULL_Y = 0, 0

# Угловая фаза — правый нижний угол, небольшой отступ от края.
CORNER_MARGIN = 40
CORNER_W, CORNER_H = 480, 270  # 16:9, ~25% ширины кадра
CORNER_X = FRAME_W - CORNER_W - CORNER_MARGIN
CORNER_Y = FRAME_H - CORNER_H - CORNER_MARGIN

# Субтитры: в полноэкранной фазе — по центру (как в старой системе,
# render/visual/safe_zones.py SUBTITLE_ZONE). В угловой фазе — прямое
# указание Олега "сдвигаются чуть-чуть, просто не по центру" (не
# просчитано точно им самим) — сдвигаем влево РОВНО настолько, чтобы
# плашка не заехала под уехавший в угол аватар (считаем от CORNER_X, а
# не гадаем фиксированный сдвиг — при другом размере угла остаётся
# корректным).
SUBTITLE_W = 1300
SUBTITLE_H = 150
SUBTITLE_Y = 900
SUBTITLE_X_CENTERED = (FRAME_W - SUBTITLE_W) // 2          # полноэкранная фаза
SUBTITLE_CORNER_GAP = 30                                     # зазор между плашкой и углом аватара
SUBTITLE_X_CORNER = min(
    SUBTITLE_X_CENTERED,
    CORNER_X - SUBTITLE_W - SUBTITLE_CORNER_GAP,
)

assert SUBTITLE_X_CORNER >= 20, "субтитровая плашка в угловой фазе выходит за левый край кадра"
assert SUBTITLE_X_CORNER + SUBTITLE_W + SUBTITLE_CORNER_GAP <= CORNER_X, (
    "субтитровая плашка в угловой фазе заезжает под уехавший в угол аватар"
)

# Плашка (универсальный фон + инфографика/булиты) — освободившееся место:
# весь кадр за вычетом (а) угла с аватаром и (б) субтитровой плашки внизу.
# Даём равные отступы от левого/верхнего края и от субтитров/аватара.
PLASHKA_PAD = 60
PLASHKA_ZONE = {
    "x0": PLASHKA_PAD,
    "y0": PLASHKA_PAD,
    "x1": FRAME_W - PLASHKA_PAD,
    "y1": SUBTITLE_Y - PLASHKA_PAD,
}


def transition_exprs(t0, t1, corner_x=CORNER_X, corner_y=CORNER_Y,
                      corner_w=CORNER_W, corner_h=CORNER_H):
    """ffmpeg-выражения (scale w/h, overlay x/y) для анимированного
    сжатия аватара с полного кадра в угол между t0 и t1 (секунды),
    та же техника eval=frame, что в build_pip_test.py."""
    w_expr = (
        f"if(lt(t\\,{t0})\\,{FULL_W}\\,"
        f"if(lt(t\\,{t1})\\,{FULL_W}+({corner_w}-{FULL_W})*(t-{t0})/({t1}-{t0})\\,{corner_w}))"
    )
    h_expr = (
        f"if(lt(t\\,{t0})\\,{FULL_H}\\,"
        f"if(lt(t\\,{t1})\\,{FULL_H}+({corner_h}-{FULL_H})*(t-{t0})/({t1}-{t0})\\,{corner_h}))"
    )
    x_expr = (
        f"if(lt(t\\,{t0})\\,0\\,"
        f"if(lt(t\\,{t1})\\,{corner_x}*(t-{t0})/({t1}-{t0})\\,{corner_x}))"
    )
    y_expr = (
        f"if(lt(t\\,{t0})\\,0\\,"
        f"if(lt(t\\,{t1})\\,{corner_y}*(t-{t0})/({t1}-{t0})\\,{corner_y}))"
    )
    return w_expr, h_expr, x_expr, y_expr
