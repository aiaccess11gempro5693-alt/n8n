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

21.09.2026 (9): `prefetch_all()` added — direct user instruction, a
sequential (one scene at a time) production render was taking ~50
minutes, almost entirely spent waiting on Nano Banana one scene after
another. `_fetch_raw()` now caches the RAW generated image per scene_id
(not the resized one, since two callers could legitimately want different
max_width for the same scene); `prefetch_all()` dispatches every scene's
generation on its own thread so the several-minutes-long waits overlap
instead of stacking up, and populates that same cache — so the ordinary
per-scene `get_or_generate()` calls composition.py already makes just hit
the cache afterwards, no caller changes needed there. `gh_bridge`'s own
locking (see that module) keeps concurrent dispatches from mis-identifying
each other's runs.
"""
import concurrent.futures
import os
import re
import threading

from PIL import Image

from . import gh_bridge

WORKFLOW_FILE = "call-image-pipeline.yml"

_raw_cache = {}
_raw_cache_lock = threading.Lock()


def _safe_name(scene_id):
    return "illustration-" + re.sub(r"[^a-zA-Z0-9_-]+", "-", str(scene_id)).strip("-")


def _fetch_raw(scene_id, asset_brief, narration_text="", aspect_ratio="1:1", ref="main"):
    """Dispatches generation for `scene_id` (or returns the cached result
    if already fetched this process) and returns the raw, full-size RGBA
    image, or None on failure. Not resized — `get_or_generate()` does
    that per-call so the cache is shared regardless of what max_width a
    particular caller needs."""
    with _raw_cache_lock:
        if scene_id in _raw_cache:
            return _raw_cache[scene_id]

    name = _safe_name(scene_id)
    inputs = {
        "narration_line": narration_text or asset_brief,
        "scene_description": asset_brief,
        "caption_count": "1",
        "aspect_ratio": aspect_ratio,
        "output_name": name,
    }
    img = None
    try:
        # timeout_s generous on purpose: prefetch_all() queues several of
        # these behind gh_bridge's dispatch lock, so a late-queued
        # thread's own deadline clock is already ticking before its
        # actual generation wait even starts.
        gh_bridge.dispatch_and_wait(WORKFLOW_FILE, inputs, ref=ref, timeout_s=480, label=f"illustration for scene {scene_id!r}")
        gh_bridge.git_pull()
        for ext in ("png", "jpg"):
            path = f"{gh_bridge.REPO_ROOT}/scratch/{name}.{ext}"
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                break
        if img is None:
            print(f"[illustration] run for scene {scene_id!r} completed but no scratch/{name}.(png|jpg) found")
    except Exception as e:
        print(f"[illustration] generation failed for scene {scene_id!r}: {e}")

    with _raw_cache_lock:
        _raw_cache[scene_id] = img
    return img


def prefetch_all(requests, ref="main", max_workers=8):
    """requests: list of (scene_id, asset_brief, narration_text,
    aspect_ratio) tuples. Dispatches all of them concurrently (each is an
    independent GitHub Actions run) instead of the default one-at-a-time
    path. Call this before the normal per-scene `get_or_generate()` loop
    to cut a multi-scene render's wall-clock time down to roughly the
    slowest single generation instead of their sum."""
    if not requests:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_fetch_raw, sid, brief, narr, ar, ref): sid for sid, brief, narr, ar in requests}
        for fut in concurrent.futures.as_completed(futs):
            sid = futs[fut]
            fut.result()  # _fetch_raw itself never raises — this just surfaces a bug loudly if one ever does
            print(f"[illustration] prefetch done: scene {sid!r}")


def get_or_generate(scene_id, asset_brief, narration_text="", max_width=400, aspect_ratio="1:1", ref="main"):
    """Generates (via the existing image pipeline) an illustration for
    this scene and returns it as an RGBA PIL.Image scaled to fit
    max_width, or None if generation isn't possible/fails — callers treat
    None as "no illustration this time", they do not fall back to
    inventing one some other way. Transparently reuses `prefetch_all()`'s
    cache when that ran first; dispatches on demand (synchronously) when
    it didn't."""
    img = _fetch_raw(scene_id, asset_brief, narration_text, aspect_ratio, ref)
    if img is None:
        return None
    ratio = max_width / img.width
    return img.resize((int(img.width * ratio), int(img.height * ratio)))
