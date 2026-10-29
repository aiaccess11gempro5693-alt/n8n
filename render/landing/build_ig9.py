"""Reels №9 «5 черт редкой женщины» — формат «подкаст», ведущий-мужчина, голос Miron.

Как в референсе instagram.com/reel/DdHRRVisJ65: ведущий в кресле и белые субтитры
(движок build_ig6), первая фраза — крупный заголовок заглавными. Поверх — шесть тёплых
кинокадров gpt-image-2 (вступление + по одному на черту, ~4 с с медленным наездом) и тихая
фортепианная музыка из библиотеки HeyGen, приглушаемая под голос.
Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig9.py   →  render/landing/ig9-9x16.mp4
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B   # выравнивание по whisper, нарезка фраз, рендер субтитров — общие
import sfx as SFX

ROOT = B.ROOT
B.SCEN = f"{ROOT}/docs/scenarios/insta-9-five-traits.md"
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig9-full-trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig9-miron-whisper.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig9-host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig9-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig9"
HOOK_SIZE, HOOK_MAXW = 72, 960
IMG = f"{ROOT}/scratch/img"
MUSIC = f"{ROOT}/scratch/music/ig9-music-full.mp3"
MUSIC_GAIN = 0.10
# (картинка, слово-триггер, длительность): вступление и по кадру на каждую черту
BROLLS = [("ig9_b0", "большинство", 3.9), ("ig9_b1", "Не", 3.9), ("ig9_b2", "Напишешь", 4.2),
          ("ig9_b3", "Как", 4.2), ("ig9_b4", "Перейдёшь", 4.2), ("ig9_b5", "И", 4.2)]
AFTER = {"ig9_b1": "Первая.", "ig9_b5": "Пятая."}   # искать слово после этого маркера

chunks = B.chunks


def finder(words):
    def F(needle, after=0.0):
        for w, t in words:
            if t >= after - 0.01 and B.norm(w) == B.norm(needle):
                return t
        raise KeyError(needle)
    return F


def broll_filter(idx, start, dur, label):
    """Картинка 1024×1536 → cover 1080×1920 с наездом 1.0→1.08 и мягким появлением (как в build_ig8)."""
    return (f"[{idx}:v]scale=1280:1920,setsar=1,fps=30,format=rgba,"
            f"scale=w='trunc(1280*(1+0.08*t/{dur:.2f})/2)*2':h='trunc(1920*(1+0.08*t/{dur:.2f})/2)*2':eval=frame,"
            f"crop=1080:1920:'(iw-1080)/2':'(ih-1920)/2',"
            f"fade=in:st=0:d=0.35:alpha=1,fade=out:st={dur - 0.35:.2f}:d=0.35:alpha=1,"
            f"setpts=PTS+{start:.3f}/TB[{label}]")


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


def main():
    os.makedirs(B.TMP, exist_ok=True)
    words, last = B.timed_words()
    F = finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    subs = chunks_with_hook(words, min(total, last + 0.6))
    brolls = []
    for img, w, dur in BROLLS:
        after = F(AFTER[img]) if img in AFTER else (brolls[-1][1] + brolls[-1][2] if brolls else 0.0)
        brolls.append((img, F(w, after), dur))
    for (a, ta, da), (b, tb, db) in zip(brolls, brolls[1:]):
        assert ta + da <= tb, f"картинки {a}/{b} перекрываются"
    assert brolls[0][1] >= subs[0]["t1"] - 0.01, "вступительный кадр не должен закрывать заголовок"
    json.dump({"subs": subs, "brolls": brolls}, open(f"{B.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [], audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={B.W}:{B.H}:force_original_aspect_ratio=increase,crop={B.W}:{B.H},setsar=1,fps=30,format=yuv420p[v0]"]
    prev, n = "[v0]", 2
    for i, (img, t0, dur) in enumerate(brolls):
        inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", f"{IMG}/{img}.png"]
        filt.append(broll_filter(n, t0, dur, f"b{i}"))
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass[vb{i}]")
        prev, n = f"[vb{i}]", n + 1
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        render_any(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", prev, "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", B.OUT],
                   check=True)
    print(B.OUT, len(subs), "субтитров,", len(brolls), "кадров")


if __name__ == "__main__":
    main()
