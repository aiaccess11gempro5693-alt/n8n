"""
ASSET STRATEGY (computed) -> real image asset, when semantic analysis
decides typography isn't enough for a given scene.

Reuses the EXISTING `.github/workflows/call-image-pipeline.yml` bridge
(Gemini prompt refinement -> Nano Banana -> Gemini coherence QA) — this
module does not duplicate that pipeline, it only drives it. The project's
own instruction for this rewrite was explicit: study the existing bridge,
don't build a second one.

`call-image-pipeline.yml`'s own contract additionally derives on-screen
`captions` from the narration — this system never uses those (on-screen
text is this system's own typography components, per ТЗ п.4: "текст не
рисуется заранее на изображениях"). Only the generated PNG is consumed
here; the `captions` field in that workflow's output is ignored.
"""
import os
import re

from PIL import Image

from . import gh_bridge

WORKFLOW_FILE = "call-image-pipeline.yml"


def _safe_name(scene_id):
    return "illustration-" + re.sub(r"[^a-zA-Z0-9_-]+", "-", str(scene_id)).strip("-")


def get_or_generate(scene_id, asset_brief, narration_text="", max_width=400, aspect_ratio="1:1", ref="main"):
    """Generates (via the existing image pipeline) an illustration for
    this scene and returns it as an RGBA PIL.Image scaled to fit
    max_width, or None if generation isn't possible/fails — callers treat
    None as "no illustration this time", they do not fall back to
    inventing one some other way."""
    name = _safe_name(scene_id)
    inputs = {
        "narration_line": narration_text or asset_brief,
        "scene_description": asset_brief,
        "caption_count": "1",
        "aspect_ratio": aspect_ratio,
        "output_name": name,
    }
    try:
        gh_bridge.dispatch_and_wait(WORKFLOW_FILE, inputs, ref=ref, label=f"illustration for scene {scene_id!r}")
    except Exception as e:
        print(f"[illustration] generation failed for scene {scene_id!r}: {e}")
        return None

    exit_code = os.system(f"cd {gh_bridge.REPO_ROOT} && git pull --quiet origin main") >> 8
    for ext in ("png", "jpg"):
        path = f"{gh_bridge.REPO_ROOT}/scratch/{name}.{ext}"
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
            ratio = max_width / img.width
            img = img.resize((int(img.width * ratio), int(img.height * ratio)))
            return img
    print(f"[illustration] run for scene {scene_id!r} completed but no scratch/{name}.(png|jpg) found (git pull exit={exit_code})")
    return None
