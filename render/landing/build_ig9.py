"""Reels №9 «5 черт редкой женщины» — формат «подкаст», ведущий-мужчина, голос Miron.

Как в референсе instagram.com/reel/DdHRRVisJ65: только ведущий в кресле и белые субтитры
(движок build_ig6), первая фраза — крупный заголовок заглавными.
Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig9.py   →  render/landing/ig9-9x16.mp4
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B   # выравнивание по whisper, нарезка фраз, рендер субтитров — общие

ROOT = B.ROOT
B.SCEN = f"{ROOT}/docs/scenarios/insta-9-five-traits.md"
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig9-full-trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig9-miron-whisper.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig9-host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig9-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig9"
HOOK_SIZE, HOOK_MAXW = 72, 960

chunks = B.chunks


def chunks_with_hook(words, total):
    """Первое предложение — крупный заголовок заглавными, дальше обычные субтитры."""
    k = next(i for i, (w, _) in enumerate(words) if w.endswith(".")) + 1
    hook = " ".join(w for w, _ in words[:k]).replace(" —", "").rstrip(".")
    rest = chunks(words[k:], total)
    rest[0]["t0"] = words[k][1]
    return [{"text": hook.upper(), "t0": 0.0, "t1": rest[0]["t0"]}] + rest


render_sub = B.render_sub


def render_any(path, text):
    if not text.isupper():
        return render_sub(path, text)
    f = ImageFont.truetype(B.FONT, HOOK_SIZE)
    im = Image.new("RGBA", (B.W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines, cur = [], ""
    for w in text.split():
        c = (cur + " " + w).strip()
        if d.textlength(c, font=f) > HOOK_MAXW and cur:
            lines.append(cur)
            cur = w
        else:
            cur = c
    lines.append(cur)
    lh = HOOK_SIZE * 1.08
    y = 130 - lh * len(lines) / 2
    for ln in lines:
        d.text((B.W / 2, y + lh / 2), ln, font=f, fill="white", anchor="mm",
               stroke_width=B.STROKE + 1, stroke_fill=(0, 0, 0, 240))
        y += lh
    im.save(path)
    assert len(lines) <= 3 and 250 <= B.CY - lh * len(lines) / 2 and B.CY + lh * len(lines) / 2 <= 1500, text


if __name__ == "__main__":
    B.chunks = chunks_with_hook
    B.render_sub = render_any
    B.main()
