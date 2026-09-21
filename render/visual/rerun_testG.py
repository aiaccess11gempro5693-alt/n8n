"""One-off: re-run composition/layout/validate for testG using the ALREADY
committed Gemini analysis (scratch/semantic-analysis-forcing-test.json) —
deliberately not re-calling Gemini, so this is a controlled test of the
build_comparison illustration-dispatch fix against the exact same decision,
not a chance at a different LLM answer this time."""
import json
import os
import time

from . import semantic_analysis as SA
from . import composition as CMP
from . import layout as L
from . import validate as V
from . import gh_bridge
from .test_pipeline import _neutral_frame

R = os.path.dirname(os.path.abspath(__file__)) + "/.."
OUT_DIR = f"{R}/visual_test_previews_assets"

with open(f"{gh_bridge.REPO_ROOT}/scratch/semantic-analysis-forcing-test.json", encoding="utf-8") as f:
    raw = json.load(f)["results"][0]

sem = SA._parse_one(raw["analysis"], raw["id"], raw["text"], 13)
print(f"asset_required={sem.asset_required} asset_brief={sem.asset_brief!r}")
print(">>> dispatching call-image-pipeline.yml for real via the FIXED build_comparison...")
t0 = time.time()
groups = CMP.compose(sem)
elapsed = time.time() - t0
all_placed = []
for group in groups:
    all_placed.extend(L.place_group(group))
V.validate_scene(sem.scene_id, all_placed, sem.duration)
print(f"COMPOSITION done in {elapsed:.1f}s: {len(groups)} group(s), {len(all_placed)} element(s) — VALIDATION PASSED")
for pi in all_placed:
    print(f"  asset {pi.image.width}x{pi.image.height} at ({pi.x},{pi.y}) trigger={pi.trigger:.2f}s")

frame = _neutral_frame()
for pi in all_placed:
    frame.alpha_composite(pi.image, (int(pi.x), int(pi.y)))
preview_path = f"{OUT_DIR}/testG-preview-fixed.png"
frame.convert("RGB").save(preview_path)
print(f"FINAL FRAME: {preview_path}")
