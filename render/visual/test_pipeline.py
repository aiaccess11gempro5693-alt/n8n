"""
CRITICAL TEST — synthetic scenes, NOT tied to any production scene_id, per
the master prompt's §16-19. Proves (or disproves) that the new architecture
is genuinely content-driven: these 5 texts have never been seen by any
Python code in this repository. If the system needs a code change to
handle them, it is not content-driven.

Does NOT touch build_trend_video.py, ffmpeg, or any production render —
only produces static preview PNGs (avatar-less: a neutral frame proxy,
since these sentences have no real HeyGen clip) for visual inspection.
"""
import json
import os
import time

from PIL import Image, ImageDraw

from . import semantic_analysis as SA
from . import composition as CMP
from . import layout as L
from . import validate as V
from .safe_zones import FRAME_W, FRAME_H, AVATAR_ZONE, SUBTITLE_ZONE, LEFT_COLUMN, RIGHT_COLUMN

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = f"{R}/visual_test_previews"

TESTS = [
    {
        "id": "test1",
        "text": ("Чтобы подобрать средство, сначала выясните, что именно беспокоит человека, "
                  "затем уточните длительность симптомов и только после этого предложите решение."),
        "duration": 14,
        "expect": "process_flow",
    },
    {
        "id": "test2",
        "text": ("Перед рекомендацией уточните четыре вещи: что беспокоит, как давно, "
                  "что уже принимает, есть ли хронические заболевания."),
        "duration": 12,
        "expect": "checklist",
    },
    {
        "id": "test3",
        "text": "Клиент может прийти с готовым мнением, но ваша задача — выяснить реальную потребность.",
        "duration": 9,
        "expect": "process_flow (opinion -> clarify -> need), NOT a magnifying glass",
    },
    {
        "id": "test4",
        "text": ("Если симптом появился впервые, подход отличается от ситуации, "
                  "когда он повторяется регулярно."),
        "duration": 10,
        "expect": "comparison",
    },
    {
        "id": "test5",
        "text": "Недостаток информации → неверная рекомендация → риск для клиента.",
        "duration": 9,
        "expect": "cause_effect",
    },
]


def _neutral_frame():
    """A flat placeholder frame standing in for the avatar clip these
    synthetic sentences don't have — draws the same safe zones the real
    validator enforces, so a reviewer can see whether elements respect
    them, without needing a real HeyGen clip for text nobody has voiced."""
    img = Image.new("RGB", (FRAME_W, FRAME_H), (58, 61, 66))
    d = ImageDraw.Draw(img)
    az = AVATAR_ZONE
    d.rectangle([az["x0"], az["y0"], az["x1"], az["y1"]], fill=(90, 94, 100))
    d.text((az["x0"] + 40, FRAME_H // 2 - 10), "AVATAR ZONE", fill=(160, 163, 168))
    sz = SUBTITLE_ZONE
    d.rectangle([sz["x0"], sz["y0"], sz["x1"], sz["y1"]], fill=(247, 249, 251))
    d.text((sz["x0"] + 20, sz["y0"] + 20), "subtitle zone (not rendered in this preview)", fill=(80, 80, 80))
    return img.convert("RGBA")


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    scenes_input = [{"id": t["id"], "text": t["text"], "duration": t["duration"]} for t in TESTS]

    t0 = time.time()
    print(f"=== dispatching semantic analysis for {len(scenes_input)} synthetic test scenes ===")
    results = SA.analyze_scenes(scenes_input, output_name="semantic-analysis-critical-test")
    t_analysis = time.time() - t0
    print(f"=== semantic analysis done in {t_analysis:.1f}s ===")

    report = []
    for test, sem in zip(TESTS, results):
        t1 = time.time()
        print(f"\n--- {test['id']} ---")
        print(f"INPUT TEXT: {test['text']}")
        print(f"EXPECTED: {test['expect']}")
        print(f"SEMANTIC ANALYSIS: main_message={sem.main_message!r}")
        print(f"  information_structure={sem.information_structure!r}")
        print(f"  visual_concept={sem.visual_concept!r}")
        print(f"  asset_strategy={sem.asset_strategy!r} asset_brief={sem.asset_brief!r}")
        print(f"  elements={[(e.role, e.label, e.order) for e in sem.elements]}")
        print(f"  elements_to_omit={sem.elements_to_omit}")

        groups = CMP.compose(sem)
        all_placed = []
        for group in groups:
            all_placed.extend(L.place_group(group))
        V.validate_scene(sem.scene_id, all_placed, sem.duration)
        print(f"COMPOSITION: {len(groups)} group(s), {len(all_placed)} placed element(s) — VALIDATION PASSED")
        for pi in all_placed:
            print(f"  asset {pi.image.width}x{pi.image.height} at ({pi.x},{pi.y}) trigger={pi.trigger:.2f}s")

        frame = _neutral_frame()
        for pi in all_placed:
            frame.alpha_composite(pi.image, (int(pi.x), int(pi.y)))
        preview_path = f"{OUT_DIR}/{test['id']}-preview.png"
        frame.convert("RGB").save(preview_path)
        elapsed = time.time() - t1
        print(f"FINAL FRAME: {preview_path} (render {elapsed:.2f}s)")

        report.append({
            "id": test["id"], "text": test["text"], "expect": test["expect"],
            "main_message": sem.main_message, "information_structure": sem.information_structure,
            "visual_concept": sem.visual_concept, "asset_strategy": sem.asset_strategy,
            "asset_brief": sem.asset_brief,
            "elements": [{"role": e.role, "label": e.label, "sublabel": e.sublabel, "order": e.order} for e in sem.elements],
            "elements_to_omit": sem.elements_to_omit,
            "n_assets": len(all_placed), "preview": preview_path, "seconds": round(elapsed, 2),
        })

    with open(f"{OUT_DIR}/report.json", "w", encoding="utf-8") as f:
        json.dump({"analysis_seconds": round(t_analysis, 1), "tests": report}, f, ensure_ascii=False, indent=2)
    print(f"\n=== all {len(TESTS)} tests passed validation. report: {OUT_DIR}/report.json ===")
    return report


if __name__ == "__main__":
    run()
