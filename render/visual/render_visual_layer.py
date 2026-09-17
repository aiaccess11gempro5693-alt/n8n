"""
Оркестратор: CONTENT -> SEMANTIC -> VISUAL_CONCEPT -> COMPOSITION ->
LAYOUT -> VALIDATION -> набор PNG-ассетов + манифест для монтажного кода
(`build_trend_video.py`). Ничего в этом файле не завязано на номер сцены
напрямую — весь диспетчинг идёт через `sem.visual_concept` в composition.py.
"""
import json
import os

from .semantic import SCENES
from .composition import compose
from .layout import place_group
from .validate import validate_scene

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = f"{R}/visual_assets"


def build_all(asset_dir=ASSET_DIR):
    os.makedirs(asset_dir, exist_ok=True)
    for f in os.listdir(asset_dir):
        if f.endswith(".png"):
            os.remove(os.path.join(asset_dir, f))

    manifest = {"scenes": {}}
    for scene, sem in sorted(SCENES.items()):
        groups = compose(sem)
        all_placed = []
        for gi, group in enumerate(groups):
            placed = place_group(group)
            all_placed.extend(placed)
        validate_scene(scene, all_placed)

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
    build_all()
