import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from visual import illustration as ILL

BRIEF = (
    "Photorealistic documentary editorial photography, a pharmacy shelf lined "
    "with many identical generic supplement boxes in a row, no customer or "
    "staff present in frame, impersonal generic feel, natural lighting, "
    "documentary editorial style, NOT illustration, NOT 3D render, NOT cartoon, "
    "warm golden-hour color palette, amber and honeyed tones, warm natural "
    "light, NOT cool-toned, NOT blue-toned."
)

print("dispatching scene4 duo-left generation...")
img = ILL.get_or_generate("4-left", BRIEF, narration_text="Шаблонный совет", max_width=300, aspect_ratio="1:1")
print("result ->", "OK" if img else "FAILED")
