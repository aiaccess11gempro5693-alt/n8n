"""STEP 1 of the follow-up audit: re-run semantic analysis (a fresh LLM
call, not reused) for scenes A, C, D only, to check whether Gemini is
defaulting to typography as the "safe" choice rather than a genuine
per-scene decision. No expected answer is supplied."""
import json
import os

from . import semantic_analysis as SA
from . import composition as CMP
from . import layout as L
from . import validate as V
from .test_pipeline import _neutral_frame

R = os.path.dirname(os.path.abspath(__file__)) + "/.."
OUT_DIR = f"{R}/visual_test_previews_assets"

TESTS = [
    {"id": "testA2", "text": ("Представьте аптечку дома: обезболивающее, средство от температуры и антисептик "
                               "лежат отдельно, чтобы нужный препарат можно было быстро найти."), "duration": 12},
    {"id": "testC2", "text": ("Покупатель спрашивает средство от насморка. Сначала нужно уточнить возраст, затем "
                               "длительность симптомов и только после этого выбрать подходящую категорию препарата."),
     "duration": 13},
    {"id": "testD2", "text": "Один и тот же симптом может иметь разные причины, поэтому нельзя выбирать препарат только по одному признаку.",
     "duration": 10},
]


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    results = SA.analyze_scenes(
        [{"id": t["id"], "text": t["text"], "duration": t["duration"]} for t in TESTS],
        output_name="semantic-analysis-recheck-acd",
    )

    report = []
    for test, sem in zip(TESTS, results):
        print(f"--- {test['id']} ---")
        print(f"INPUT TEXT: {test['text']}")
        print(f"main_message: {sem.main_message!r}")
        print(f"information_structure: {sem.information_structure!r}")
        print(f"visual_goal: {sem.visual_goal!r}")
        print(f"asset_required: {sem.asset_required}")
        print(f"asset_type_raw: {sem.asset_type_raw!r}")
        print(f"asset_brief: {sem.asset_brief!r}")
        print(f"no_asset_reason: {sem.no_asset_reason!r}")
        print(f"composition_intent: {sem.composition_intent!r}")
        print(f"visual_concept: {sem.visual_concept!r}")
        print()

        entry = {"id": test["id"], "text": test["text"], "main_message": sem.main_message,
                  "information_structure": sem.information_structure, "visual_goal": sem.visual_goal,
                  "asset_required": sem.asset_required, "asset_type_raw": sem.asset_type_raw,
                  "asset_brief": sem.asset_brief, "no_asset_reason": sem.no_asset_reason,
                  "composition_intent": sem.composition_intent, "visual_concept": sem.visual_concept}

        if sem.asset_required:
            print(f">>> asset_required=True for {test['id']} — dispatching real image pipeline...")
            groups = CMP.compose(sem)
            all_placed = []
            for group in groups:
                all_placed.extend(L.place_group(group))
            V.validate_scene(sem.scene_id, all_placed, sem.duration)
            frame = _neutral_frame()
            for pi in all_placed:
                frame.alpha_composite(pi.image, (int(pi.x), int(pi.y)))
            preview_path = f"{OUT_DIR}/{test['id']}-preview.png"
            frame.convert("RGB").save(preview_path)
            print(f"FINAL FRAME: {preview_path}")
            entry["preview"] = preview_path

        report.append(entry)

    with open(f"{OUT_DIR}/recheck-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


if __name__ == "__main__":
    run()
