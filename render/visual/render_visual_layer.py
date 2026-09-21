"""
Оркестратор: SEMANTIC (computed, `semantic_analysis.analyze_scenes`) ->
VISUAL_CONCEPT -> COMPOSITION -> LAYOUT -> VALIDATION -> набор PNG-ассетов +
манифест для монтажного кода (`build_trend_video.py`). Ничего в этом файле
не завязано на номер сцены напрямую — весь диспетчинг идёт через
`sem.visual_concept` в composition.py, и сам список сцен передаётся
вызывающим кодом (никакого `SCENES: dict[int, ...]` здесь больше нет —
см. CLAUDE.md, 21.09.2026, forensic audit + переработка).
"""
import json
import os

from . import components as C
from . import illustration as ILL
from .composition import compose
from .layout import place_group, PlacedItem
from .safe_zones import TOP_TITLE_ZONE, column_width, column_height
from .validate import validate_scene

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = f"{R}/visual_assets"


def _place_top_title(sem):
    """Short scene-topic banner, centered in TOP_TITLE_ZONE above the
    avatar's head — present in EVERY scene alongside the existing
    side-column content (21.09.2026 (4), direct user instruction: a new
    element, not a replacement). Trigger is fixed-early (0.3s) and it
    stays for the whole scene (fade_out=None), same convention as the
    existing side-column headline components."""
    zw, zh = column_width(TOP_TITLE_ZONE), column_height(TOP_TITLE_ZONE)
    img = C.render_top_title(sem.scene_title, zw)
    x = TOP_TITLE_ZONE["x0"] + max(0, (zw - img.width) // 2)
    y = TOP_TITLE_ZONE["y0"] + max(0, (zh - img.height) // 2)
    return PlacedItem(image=img, x=x, y=y, trigger=0.3)


def build_all(scene_semantics, asset_dir=ASSET_DIR):
    """scene_semantics: list[SceneSemantics] — computed by
    `semantic_analysis.analyze_scenes()`, not authored by hand. `.scene_id`
    may be any string/int (a real production scene number, a test id,
    whatever the caller used when it built the input to analyze_scenes)."""
    os.makedirs(asset_dir, exist_ok=True)
    for f in os.listdir(asset_dir):
        if f.endswith(".png"):
            os.remove(os.path.join(asset_dir, f))

    # dispatch every scene's illustration generation concurrently instead
    # of the default one-at-a-time-inside-compose() path — cuts a
    # multi-scene production render's wall-clock time roughly to the
    # slowest single generation instead of their sum (direct user
    # instruction; see illustration.prefetch_all's docstring).
    prefetch_reqs = [
        (sem.scene_id, sem.asset_brief, sem.text, "1:1")
        for sem in scene_semantics if sem.asset_required and sem.asset_brief
    ]
    if prefetch_reqs:
        print(f"prefetching {len(prefetch_reqs)} illustration(s) concurrently...")
        ILL.prefetch_all(prefetch_reqs)

    manifest = {"scenes": {}}
    for sem in scene_semantics:
        scene = sem.scene_id
        groups = compose(sem)
        all_placed = []
        for gi, group in enumerate(groups):
            placed = place_group(group)
            all_placed.extend(placed)
        all_placed.append(_place_top_title(sem))
        validate_scene(scene, all_placed, sem.duration)

        scene_entries = []
        for ei, pi in enumerate(all_placed):
            fname = f"scene{scene}-el{ei}.png"
            pi.image.save(os.path.join(asset_dir, fname))
            scene_entries.append({
                "file": fname,
                "x": pi.x,
                "y": pi.y,
                "w": pi.image.width,
                "h": pi.image.height,
                "trigger": round(pi.trigger, 3),
                "fade_out": round(pi.fade_out, 3) if pi.fade_out is not None else None,
            })
        manifest["scenes"][scene] = {
            "concept": sem.visual_concept,
            "information_structure": sem.information_structure,
            "elements": scene_entries,
        }
        print(f"scene {scene}: concept={sem.visual_concept:20s} elements={len(scene_entries)}")

    with open(f"{asset_dir}/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"written {asset_dir}/manifest.json")
    return manifest


if __name__ == "__main__":
    raise SystemExit(
        "build_all() now takes computed scene_semantics (see semantic_analysis.analyze_scenes) "
        "— there is nothing to run standalone here. Use render/visual/test_pipeline.py for a "
        "synthetic test run, or the production entry point once one is wired up."
    )
