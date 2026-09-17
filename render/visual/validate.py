"""VALIDATION — последний шаг перед рендером. Никакой автогенерации не
считается готовой, пока не прошла эти проверки; при провале — исключение
(никакого тихого fallback на старый layout, п.23 мастер-промпта)."""
from .safe_zones import AVATAR_ZONE, SUBTITLE_ZONE, FRAME_W, FRAME_H, SAFE_PAD
from .timing import scene_duration


def _rect(x, y, w, h):
    return {"x0": x, "y0": y, "x1": x + w, "y1": y + h}


def _overlap(a, b):
    return not (a["x1"] <= b["x0"] or b["x1"] <= a["x0"] or a["y1"] <= b["y0"] or b["y1"] <= a["y0"])


def validate_scene(scene, placed_items):
    dur = scene_duration(scene)
    errors = []
    for pi in placed_items:
        r = _rect(pi.x, pi.y, pi.image.width, pi.image.height)
        if r["x0"] < -2 or r["y0"] < -2 or r["x1"] > FRAME_W + 2 or r["y1"] > FRAME_H + 2:
            errors.append(f"scene {scene}: element at ({pi.x},{pi.y}) size {pi.image.width}x{pi.image.height} "
                           f"escapes frame bounds")
        if _overlap(r, AVATAR_ZONE):
            errors.append(f"scene {scene}: element at ({pi.x},{pi.y}) overlaps AVATAR_ZONE")
        if _overlap(r, SUBTITLE_ZONE):
            errors.append(f"scene {scene}: element at ({pi.x},{pi.y}) overlaps SUBTITLE_ZONE")
        if pi.trigger < 0 or pi.trigger > dur:
            errors.append(f"scene {scene}: trigger {pi.trigger:.2f}s outside scene duration {dur:.2f}s")
        visible_until = pi.fade_out if pi.fade_out is not None else dur
        if visible_until - pi.trigger < 0.9:
            errors.append(f"scene {scene}: element visible only {visible_until - pi.trigger:.2f}s "
                           f"(<0.9s, would flash) trigger={pi.trigger:.2f} fade_out={pi.fade_out}")
    if errors:
        raise SystemExit("VISUAL LAYER VALIDATION FAILED:\n" + "\n".join(errors))
    return True
