"""
ASSET STRESS TEST — 6 synthetic scenes (A-F), chosen to plausibly need
different asset strategies (illustration/diagram/combination/metaphor/
data/none). None of these texts are hardcoded to a strategy anywhere in
this file or in semantic_analysis.py — the LLM decides asset_required and
asset_type per scene from the text alone.

For any scene where Gemini sets asset_required=true, this actually
dispatches the EXISTING call-image-pipeline.yml (via illustration.py ->
gh_bridge.py) and waits for a real Nano Banana asset — no simulated/fake
PNGs. If that dispatch fails, this script surfaces the real error and
does not substitute a placeholder.

Does not touch build_trend_video.py or ffmpeg.
"""
import json
import os
import time

from PIL import Image

from . import semantic_analysis as SA
from . import composition as CMP
from . import layout as L
from . import validate as V
from .test_pipeline import _neutral_frame

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = f"{R}/visual_test_previews_assets"

TESTS = [
    {
        "id": "testA",
        "text": ("Представьте аптечку дома: обезболивающее, средство от температуры и антисептик "
                  "лежат отдельно, чтобы нужный препарат можно было быстро найти."),
        "duration": 12,
        "label": "A — illustration?",
    },
    {
        "id": "testB",
        "text": ("При недостатке воды организм сначала испытывает жажду, затем уменьшается объём "
                  "жидкости в организме, а при дальнейшем ухудшении появляется слабость и головокружение."),
        "duration": 13,
        "label": "B — diagram/process/cause-effect?",
    },
    {
        "id": "testC",
        "text": ("Покупатель спрашивает средство от насморка. Сначала нужно уточнить возраст, затем "
                  "длительность симптомов и только после этого выбрать подходящую категорию препарата."),
        "duration": 13,
        "label": "C — text + process + visual support (combination)?",
    },
    {
        "id": "testD",
        "text": "Один и тот же симптом может иметь разные причины, поэтому нельзя выбирать препарат только по одному признаку.",
        "duration": 10,
        "label": "D — visual metaphor, NOT a magnifying glass?",
    },
    {
        "id": "testE",
        "text": "Чем больше факторов нужно учитывать одновременно, тем выше риск ошибиться, если решение принимается только по одному признаку.",
        "duration": 10,
        "label": "E — data/relationship visualization?",
    },
    {
        "id": "testF",
        "text": "Перед тем как дать рекомендацию, внимательно выслушайте человека.",
        "duration": 6,
        "label": "F — typography-only is a valid answer here",
    },
]


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    scenes_input = [{"id": t["id"], "text": t["text"], "duration": t["duration"]} for t in TESTS]

    t0 = time.time()
    print(f"=== dispatching semantic analysis for {len(scenes_input)} asset-stress scenes ===")
    results = SA.analyze_scenes(scenes_input, output_name="semantic-analysis-asset-stress-test")
    t_analysis = time.time() - t0
    print(f"=== semantic analysis done in {t_analysis:.1f}s ===\n")

    report = []
    for test, sem in zip(TESTS, results):
        t1 = time.time()
        print(f"--- {test['id']} ({test['label']}) ---")
        print(f"INPUT TEXT: {test['text']}")
        print(f"main_message: {sem.main_message!r}")
        print(f"information_structure (free text): {sem.information_structure!r}")
        print(f"visual_goal: {sem.visual_goal!r}")
        print(f"asset_required: {sem.asset_required}")
        print(f"asset_type_raw (Gemini's own word): {sem.asset_type_raw!r}")
        print(f"asset_strategy (normalized, technical): {sem.asset_strategy!r}")
        print(f"asset_brief: {sem.asset_brief!r}")
        print(f"no_asset_reason: {sem.no_asset_reason!r}")
        print(f"composition_intent: {sem.composition_intent!r}")
        print(f"motion_intent: {sem.motion_intent!r}")
        print(f"visual_concept (technical): {sem.visual_concept!r}")
        print(f"elements: {[(e.role, e.label, e.order) for e in sem.elements]}")
        print(f"avoid: {sem.avoid}")

        illustration_dispatched = sem.asset_required and bool(sem.asset_brief)
        if illustration_dispatched:
            print(f">>> asset_required=True — dispatching call-image-pipeline.yml for real (this takes a while: "
                  f"Gemini prompt refine -> Nano Banana -> Gemini QA)...")

        groups = CMP.compose(sem)   # this is where illustration.get_or_generate() actually fires, if needed
        all_placed = []
        for group in groups:
            all_placed.extend(L.place_group(group))
        V.validate_scene(sem.scene_id, all_placed, sem.duration)
        print(f"COMPOSITION: {len(groups)} group(s), {len(all_placed)} placed element(s) — VALIDATION PASSED")

        illustration_asset = None
        for pi in all_placed:
            is_photo = pi.image.width > 200 and pi.image.height > 200 and _looks_like_photo(pi.image)
            print(f"  asset {pi.image.width}x{pi.image.height} at ({pi.x},{pi.y}) trigger={pi.trigger:.2f}s"
                  f"{' [LIKELY GENERATED ILLUSTRATION]' if is_photo else ''}")
            if is_photo:
                illustration_asset = pi

        frame = _neutral_frame()
        for pi in all_placed:
            frame.alpha_composite(pi.image, (int(pi.x), int(pi.y)))
        preview_path = f"{OUT_DIR}/{test['id']}-preview.png"
        frame.convert("RGB").save(preview_path)
        elapsed = time.time() - t1
        print(f"FINAL FRAME: {preview_path} (elapsed {elapsed:.1f}s)\n")

        report.append({
            "id": test["id"], "text": test["text"],
            "main_message": sem.main_message, "information_structure": sem.information_structure,
            "visual_goal": sem.visual_goal, "asset_required": sem.asset_required,
            "asset_type_raw": sem.asset_type_raw, "asset_strategy": sem.asset_strategy,
            "asset_brief": sem.asset_brief, "no_asset_reason": sem.no_asset_reason,
            "composition_intent": sem.composition_intent, "motion_intent": sem.motion_intent,
            "visual_concept": sem.visual_concept,
            "elements": [{"role": e.role, "label": e.label, "order": e.order} for e in sem.elements],
            "avoid": sem.avoid, "illustration_dispatched": illustration_dispatched,
            "illustration_present_in_frame": illustration_asset is not None,
            "n_assets": len(all_placed), "preview": preview_path, "seconds": round(elapsed, 1),
        })

    with open(f"{OUT_DIR}/report.json", "w", encoding="utf-8") as f:
        json.dump({"analysis_seconds": round(t_analysis, 1), "tests": report}, f, ensure_ascii=False, indent=2)
    print(f"=== all {len(TESTS)} tests passed validation. report: {OUT_DIR}/report.json ===")
    return report


def _looks_like_photo(img):
    """Cheap heuristic to flag a placed asset as "probably a generated
    illustration, not a typography PNG we drew ourselves": our own PIL
    text components are RGBA with huge areas of fully-transparent alpha=0
    background; a real generated PNG/JPEG (even converted to RGBA) is
    mostly opaque everywhere."""
    alpha = img.split()[-1]
    hist = alpha.histogram()
    opaque_frac = sum(hist[200:]) / max(1, sum(hist))
    return opaque_frac > 0.6


if __name__ == "__main__":
    run()
