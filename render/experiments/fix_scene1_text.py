import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from visual import illustration as ILL

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BRIEF0 = (
    "Editorial photo of a modern bright TV screen or billboard displaying a "
    "vibrant health and wellness vitamin commercial in a home setting, natural "
    "lighting, documentary style, realistic., warm golden-hour color palette, "
    "amber and honeyed tones, warm natural light, NOT cool-toned, NOT blue-toned. "
    "The commercial screen shows a short Russian text overlay reading exactly "
    '"ЭНЕРГИЯ И ЗДОРОВЬЕ" in bold Cyrillic letters, correctly spelled, large and '
    "legible, NOT English, NOT Latin script, NOT garbled letters."
)
BRIEF1 = (
    "Close-up realistic photo of hands holding a smartphone, reading a health "
    "blog article about vitamins and immune system, warm natural light, "
    "documentary lifestyle photography., warm golden-hour color palette, amber "
    "and honeyed tones, warm natural light, NOT cool-toned, NOT blue-toned. The "
    "phone screen shows a Russian-language blog article with the exact headline "
    'text "Витамины и иммунитет" in bold Cyrillic letters, correctly spelled, '
    "legible, NOT English, NOT Latin script, NOT garbled letters."
)

print("dispatching item0 fix...")
img0 = ILL.get_or_generate("1-item0", BRIEF0, narration_text="Реклама и медиа", max_width=300, aspect_ratio="1:1")
print("item0 ->", "OK" if img0 else "FAILED")

print("dispatching item1 fix...")
img1 = ILL.get_or_generate("1-item1", BRIEF1, narration_text="Интернет и статьи", max_width=300, aspect_ratio="1:1")
print("item1 ->", "OK" if img1 else "FAILED")

sem_path = f"{REPO}/scratch/semantic-analysis-production-scenario4.json"
d = json.load(open(sem_path, encoding="utf-8"))
for r in d["results"]:
    if r["id"] == 1:
        r["analysis"]["elements"][0]["asset_brief"] = BRIEF0
        r["analysis"]["elements"][1]["asset_brief"] = BRIEF1
json.dump(d, open(sem_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("semantic-analysis JSON updated")
