"""
Re-test of the layout solver against Test D2 (saved analysis, saved
asset — no new Gemini call, no new image-pipeline dispatch) and Test G-v2
(saved analysis, saved asset), per the follow-up instruction after the
solver rewrite in layout.py.

`illustration.get_or_generate` is monkeypatched to load the ALREADY
generated PNG from scratch/ instead of dispatching a new run — this is a
test-harness substitution, not a change to illustration.py itself (that
module is untouched, as instructed).
"""
import json
import os

from PIL import Image

from . import semantic_analysis as SA
from . import composition as CMP
from . import layout as L
from . import validate as V
from . import illustration as ILL
from . import gh_bridge
from .test_pipeline import _neutral_frame

R = os.path.dirname(os.path.abspath(__file__)) + "/.."
OUT_DIR = f"{R}/visual_test_previews_assets"


def _load_cached(scene_id, path):
    def _fake_get_or_generate(sid, brief, narration_text="", max_width=400, aspect_ratio="1:1", ref="main"):
        assert sid == scene_id, f"test harness only stubs scene_id={scene_id!r}, got {sid!r}"
        img = Image.open(path).convert("RGBA")
        ratio = max_width / img.width
        return img.resize((int(img.width * ratio), int(img.height * ratio)))
    return _fake_get_or_generate


def _run_one(scene_id, analysis_path, asset_path, out_name):
    with open(analysis_path, encoding="utf-8") as f:
        raw = json.load(f)
    results = raw["results"] if "results" in raw else [raw]
    entry = next(r for r in results if r["id"] == scene_id)
    sem = SA._parse_one(entry["analysis"], entry["id"], entry["text"], 13)

    print(f"=== {scene_id} ===")
    print(f"visual_concept={sem.visual_concept} asset_required={sem.asset_required}")
    print(f"elements: {[(e.role, e.label, e.order) for e in sem.elements]}")

    ILL.get_or_generate = _load_cached(scene_id, asset_path)

    groups = CMP.compose(sem)
    all_placed = []
    try:
        for group in groups:
            print(f"--- solving column={group.column} ({len(group.items)} item(s)) ---")
            for it in group.items:
                print(f"  input item: kind={it.kind} size={it.image.size} "
                      f"{'render_fn=' + repr(it.render_fn is not None) if it.kind=='text' else 'min_px=' + str(it.min_px)}")
            placed = L.place_group(group)
            all_placed.extend(placed)
            for pi in placed:
                print(f"  placed: {pi.image.width}x{pi.image.height} at ({pi.x},{pi.y})")
    except L.LayoutSolveError as e:
        print(f"LAYOUT SOLVE FAILED: {e}")
        print("candidates tried:")
        for c in e.candidates:
            print(f"  {c}")
        raise

    V.validate_scene(sem.scene_id, all_placed, sem.duration)
    print("validate_scene: PASS")

    frame = _neutral_frame()
    for pi in all_placed:
        frame.alpha_composite(pi.image, (int(pi.x), int(pi.y)))
    preview_path = f"{OUT_DIR}/{out_name}.png"
    frame.convert("RGB").save(preview_path)
    print(f"FINAL FRAME: {preview_path}\n")
    return all_placed


if __name__ == "__main__":
    _run_one("testD2", f"{gh_bridge.REPO_ROOT}/scratch/semantic-analysis-recheck-acd.json",
              f"{gh_bridge.REPO_ROOT}/scratch/illustration-testD2.png", "testD2-preview-solved")
    _run_one("testG", f"{gh_bridge.REPO_ROOT}/scratch/semantic-analysis-forcing-test.json",
              f"{gh_bridge.REPO_ROOT}/scratch/illustration-testG.png", "testG-preview-solver-v2")
