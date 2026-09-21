"""VALIDATION — последний шаг перед рендером. Никакой автогенерации не
считается готовой, пока не прошла эти проверки; при провале — исключение
(никакого тихого fallback на старый layout, п.23 мастер-промпта).

21.09.2026 — duration больше не читается из word_layout.json напрямую
(это ломалось на синтетических тестовых сценах, у которых нет записи в
production word_layout.json) — вызывающий код передаёт duration явно
(из `SceneSemantics.duration`, которое `semantic_analysis.py` берёт из
входных данных, реальных или тестовых, единообразно). Также добавлены
проверки, которых не было при первой реализации визуального слоя:
попарные коллизии между элементами ОДНОЙ сцены (раньше проверялось только
пересечение с AVATAR_ZONE/SUBTITLE_ZONE, не друг с другом), плотность
(не более 4 элементов на сцену) и эвристика читаемости (элемент, сжатый
меньше минимального читаемого размера, — брак, не тихо принимается)."""
from .safe_zones import AVATAR_ZONE, SUBTITLE_ZONE, FRAME_W, FRAME_H

MAX_ELEMENTS_PER_SCENE = 4
MIN_READABLE_HEIGHT = 28  # px; ниже — эвристически нечитаемо на 1920x1080


def _rect(x, y, w, h):
    return {"x0": x, "y0": y, "x1": x + w, "y1": y + h}


def _overlap(a, b):
    return not (a["x1"] <= b["x0"] or b["x1"] <= a["x0"] or a["y1"] <= b["y0"] or b["y1"] <= a["y0"])


def validate_scene(scene, placed_items, duration):
    errors = []

    if len(placed_items) > MAX_ELEMENTS_PER_SCENE:
        errors.append(
            f"scene {scene}: {len(placed_items)} elements exceeds density cap "
            f"({MAX_ELEMENTS_PER_SCENE}) — scene is overfilled"
        )

    rects = []
    for pi in placed_items:
        r = _rect(pi.x, pi.y, pi.image.width, pi.image.height)
        rects.append(r)
        if r["x0"] < -2 or r["y0"] < -2 or r["x1"] > FRAME_W + 2 or r["y1"] > FRAME_H + 2:
            errors.append(f"scene {scene}: element at ({pi.x},{pi.y}) size {pi.image.width}x{pi.image.height} "
                           f"escapes frame bounds")
        if _overlap(r, AVATAR_ZONE):
            errors.append(f"scene {scene}: element at ({pi.x},{pi.y}) overlaps AVATAR_ZONE")
        if _overlap(r, SUBTITLE_ZONE):
            errors.append(f"scene {scene}: element at ({pi.x},{pi.y}) overlaps SUBTITLE_ZONE")
        if pi.trigger < 0 or (duration and pi.trigger > duration):
            errors.append(f"scene {scene}: trigger {pi.trigger:.2f}s outside scene duration {duration:.2f}s")
        visible_until = pi.fade_out if pi.fade_out is not None else (duration or pi.trigger + 3.0)
        if visible_until - pi.trigger < 0.9:
            errors.append(f"scene {scene}: element visible only {visible_until - pi.trigger:.2f}s "
                           f"(<0.9s, would flash) trigger={pi.trigger:.2f} fade_out={pi.fade_out}")
        if pi.image.height < MIN_READABLE_HEIGHT:
            errors.append(f"scene {scene}: element at ({pi.x},{pi.y}) height {pi.image.height}px is below the "
                           f"minimum readable heuristic ({MIN_READABLE_HEIGHT}px) — likely shrunk past legibility")

    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            if _overlap(rects[i], rects[j]):
                errors.append(f"scene {scene}: element {i} and element {j} collide "
                               f"({rects[i]} vs {rects[j]})")

    if errors:
        raise SystemExit("VISUAL LAYER VALIDATION FAILED:\n" + "\n".join(errors))
    return True
