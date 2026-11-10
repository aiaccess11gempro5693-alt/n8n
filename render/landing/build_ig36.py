"""Reels №36 «100 раз поможешь — забудут» (по референсу instagram.com/reel/Dd6aReNsx8U).

Формат как в референсе: чёрный вертикальный кадр, сверху белый заголовок, посередине горизонтальное видео
ведущего за рулём ночью (HeyGen 16:9), под видео — белые субтитры с жёлтым ключевым словом. Медленный наезд
внутри окна видео и короткие наезды на главных фразах, тихое фортепиано.

python3 render/landing/build_ig36.py  →  render/landing/ig36-9x16.mp4
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import sfx as SFX

ROOT = B.ROOT
W, H = 1080, 1920
YELLOW = (255, 214, 10)
TMP = f"{ROOT}/render/landing/.ig36"
AUDIO = f"{ROOT}/scratch/ig36/trim.mp3"
WHISPER = f"{ROOT}/scratch/ig36-whisper-final.json"
CLIP = f"{ROOT}/scratch/ig36/host.mp4"
OUT = f"{ROOT}/render/landing/ig36-9x16.mp4"
MUSIC = f"{ROOT}/scratch/music/ig36-music.mp3"
GAIN = 0.10

VW, VH = 1080, 608          # окно видео 16:9
VY = 600                    # верх окна видео
SUB_CY = 1360               # центр субтитров под видео
SPOKEN = ("Сто раз поможешь — забудут. Один раз откажешь — запомнят. Знаешь, почему так? Когда ты помогаешь всегда, "
          "помощь перестаёт быть подарком. Она становится нормой. Как свет в квартире: его не замечают, пока не "
          "выключат. И вот один раз ты не смог. Устал, нет денег, нет сил. И вдруг ты — плохой. Будто все прошлые "
          "разы не считались. Это не твоя вина. Это проверка. Отказ показывает, кто рядом ради тебя, а кто — ради "
          "твоей помощи. Поэтому помогай, когда хочешь, а не когда должен. И говори «нет» спокойно, без оправданий. "
          "А тех, кто после одного «нет» забыл всё хорошее, — отпусти. Им был нужен… не ты. Отправь это тому, кто "
          "всем помогает.")
HOT = {"забудут", "запомнят", "подарком", "нормой", "выключат", "плохой", "вина", "проверка", "хочешь", "должен",
       "оправданий", "отпусти", "ты", "помогает", "сил"}
PUNCH = ["проверка.", "Им"]


def norm(w):
    return re.sub(r"[^\wё]", "", w.lower())


def render_title(path):
    f = ImageFont.truetype(B.FONT, 64)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rows = [("100 раз поможешь — ", "забудут", (255, 255, 255)), ("1 раз откажешь — ", "запомнят", YELLOW)]
    y = 400
    for a, b, col in rows:
        wa, wb = d.textlength(a, font=f), d.textlength(b, font=f)
        x = W / 2 - (wa + wb) / 2
        d.text((x, y), a, font=f, fill=(255, 255, 255), anchor="lm")
        d.text((x + wa, y), b, font=f, fill=col, anchor="lm")
        assert x >= 40, a + b
        y += 86
    bb = (0, 400 - 40, W, y - 86 + 40)
    assert bb[1] >= 250 and bb[3] < VY - 20, bb
    im.save(path)


def render_sub(path, text):
    size = 60
    f = ImageFont.truetype(B.FONT, size)
    im = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines, cur = [], []
    for w in text.split():
        c = cur + [w]
        if d.textlength(" ".join(c), font=f) > 940 and cur:
            lines.append(cur)
            cur = [w]
        else:
            cur = c
    lines.append(cur)
    lh = size * 1.15
    y = 130 - lh * len(lines) / 2
    sp = d.textlength(" ", font=f)
    for ln in lines:
        x = W / 2 - d.textlength(" ".join(ln), font=f) / 2
        for w in ln:
            col = YELLOW if norm(w) in HOT else (255, 255, 255)
            d.text((x, y + lh / 2), w, font=f, fill=col, anchor="lm")
            x += d.textlength(w, font=f) + sp
        y += lh
    top, bot = SUB_CY - lh * len(lines) / 2, SUB_CY + lh * len(lines) / 2
    assert top >= VY + VH + 15 and bot <= 1500, (text, top, bot)
    im.save(path)


def main():
    os.makedirs(TMP, exist_ok=True)
    B.WHISPER = WHISPER
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", AUDIO]).decode()) + 0.8
    subs = B.chunks(words, min(total, last + 0.8))
    for s in subs:
        assert s["t1"] - s["t0"] >= 0.5, s
    punch = [(F(PUNCH[0]), F(PUNCH[0]) + 1.8), (F(PUNCH[1], after=38), F(PUNCH[1], after=38) + 2.2)]
    json.dump({"subs": subs, "punch": punch}, open(f"{TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    padded = f"{TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", AUDIO, "-af", "apad=pad_dur=0.8", "-ar", "48000", padded],
                   check=True)
    audio = f"{TMP}/mix.wav"
    SFX.mix(padded, [], audio, f"{TMP}/sfx", bed_gain=GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    title = f"{TMP}/title.png"
    render_title(title)
    pz = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in punch)
    z = f"(1+0.06*t/{total:.2f}+0.12*({pz}))"
    inputs = ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r=30:d={total:.3f}", "-i", CLIP, "-i", audio,
              "-i", title]
    filt = [f"[1:v]scale={VW}:{VH}:force_original_aspect_ratio=increase,crop={VW}:{VH},setsar=1,fps=30,"
            f"tpad=stop_duration=3:stop_mode=clone,"
            f"scale=w='trunc({VW}*{z}/2)*2':h='trunc({VH}*{z}/2)*2':eval=frame,"
            f"crop={VW}:{VH}:'(iw-{VW})*0.35':'(ih-{VH})*0.3',format=yuv420p[v]",
            f"[0:v][v]overlay=0:{VY}[b0]", "[b0][3:v]overlay=0:0[b1]"]
    prev, k = "[b1]", 4
    for i, s in enumerate(subs):
        p = f"{TMP}/sub{i:03d}.png"
        render_sub(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{k}:v]overlay=0:{SUB_CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, k = f"[s{i}]", k + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{TMP}/graph.txt",
                    "-map", "[vout]", "-map", "2:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "8M", "-bufsize", "16M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)
    print(OUT, f"{total:.1f} c,", len(subs), "субтитров")


if __name__ == "__main__":
    main()
