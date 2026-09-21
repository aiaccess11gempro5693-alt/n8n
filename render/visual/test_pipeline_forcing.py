"""
CRITICAL TEST (master prompt §8): a scene text specifically chosen because
its content is inherently visual/appearance-based — information that is
genuinely hard to convey through typography alone, unlike the 6 scenes in
test_pipeline_assets.py, all 6 of which Gemini legitimately (and
defensibly) declined to illustrate.

Not designed to force a predetermined answer — designed so that
"typography is enough" is a much harder position for the analysis to
take, to see whether the real image pipeline (illustration.py ->
call-image-pipeline.yml -> Nano Banana -> Gemini QA) actually fires when
warranted.
"""
import json
import os
import time

from . import semantic_analysis as SA
from . import composition as CMP
from . import layout as L
from . import validate as V
from .test_pipeline import _neutral_frame

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = f"{R}/visual_test_previews_assets"

TEST = {
    "id": "testG",
    "text": ("Обратите внимание на упаковку: у подделки шрифт названия смазанный и нечёткий, "
              "а зелёный цвет коробки блёклый и голубоватый вместо насыщенного тёмно-зелёного, "
              "как у оригинала."),
    "duration": 13,
}


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    print(f"=== dispatching semantic analysis for testG ===")
    sem = SA.analyze_scenes([{"id": TEST["id"], "text": TEST["text"], "duration": TEST["duration"]}],
                             output_name="semantic-analysis-forcing-test")[0]
    t_analysis = time.time() - t0
    print(f"=== semantic analysis done in {t_analysis:.1f}s ===\n")

    print(f"INPUT TEXT: {TEST['text']}")
    print(f"main_message: {sem.main_message!r}")
    print(f"information_structure: {sem.information_structure!r}")
    print(f"visual_goal: {sem.visual_goal!r}")
    print(f"asset_required: {sem.asset_required}")
    print(f"asset_type_raw: {sem.asset_type_raw!r}")
    print(f"asset_strategy (normalized): {sem.asset_strategy!r}")
    print(f"asset_brief: {sem.asset_brief!r}")
    print(f"no_asset_reason: {sem.no_asset_reason!r}")
    print(f"composition_intent: {sem.composition_intent!r}")
    print(f"visual_concept: {sem.visual_concept!r}")
    print(f"elements: {[(e.role, e.label, e.order) for e in sem.elements]}")
    print(f"avoid: {sem.avoid}")

    result = {
        "id": TEST["id"], "text": TEST["text"], "seconds_analysis": round(t_analysis, 1),
        "asset_required": sem.asset_required, "asset_type_raw": sem.asset_type_raw,
        "asset_strategy": sem.asset_strategy, "asset_brief": sem.asset_brief,
        "no_asset_reason": sem.no_asset_reason, "visual_concept": sem.visual_concept,
    }

    if not sem.asset_required:
        print("\n>>> Gemini declined an asset even for this scene. Reporting honestly — no illustration "
              "pipeline call to make. NOT forcing one.")
        with open(f"{OUT_DIR}/testG-report.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result

    print(f"\n>>> asset_required=True. Dispatching call-image-pipeline.yml for real "
          f"(Gemini prompt refine -> Nano Banana -> Gemini QA)...")
    t1 = time.time()
    groups = CMP.compose(sem)
    t_illustration = time.time() - t1
    all_placed = []
    for group in groups:
        all_placed.extend(L.place_group(group))
    V.validate_scene(sem.scene_id, all_placed, sem.duration)
    print(f"COMPOSITION done in {t_illustration:.1f}s: {len(groups)} group(s), {len(all_placed)} element(s) "
          f"— VALIDATION PASSED")
    for pi in all_placed:
        print(f"  asset {pi.image.width}x{pi.image.height} at ({pi.x},{pi.y}) trigger={pi.trigger:.2f}s")

    frame = _neutral_frame()
    for pi in all_placed:
        frame.alpha_composite(pi.image, (int(pi.x), int(pi.y)))
    preview_path = f"{OUT_DIR}/testG-preview.png"
    frame.convert("RGB").save(preview_path)
    print(f"FINAL FRAME: {preview_path}")

    result["seconds_illustration"] = round(t_illustration, 1)
    result["n_assets"] = len(all_placed)
    result["preview"] = preview_path
    with open(f"{OUT_DIR}/testG-report.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    run()
