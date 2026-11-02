"""Reels №10 «5 фраз, которые выдают неуверенного человека» — состоятельный добрый наставник на яхте.

Как в референсе instagram.com/reel/Dc7Q-S2In2D: мужчина «снимает себя сам» на палубе яхты,
ключевая фраза каждого пункта — тёмно-синяя плашка с золотым текстом и номером. Плюс белые
субтитры (движок build_ig6), первая фраза — крупный заголовок заглавными (как в build_ig9), и
тихая лаунж-музыка из библиотеки HeyGen. Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig10.py   →  render/landing/ig10-9x16.mp4
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N   # заголовок-крючок, поиск слова по таймингу
import sfx as SFX

ROOT = B.ROOT
B.SCEN = f"{ROOT}/docs/scenarios/insta-10-five-phrases.md"
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig10-full-trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig10-goncharov-whisper.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig10-host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig10-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig10"
N.HOOK_SIZE = 62               # крючок длиннее, чем в №9: три строки
MUSIC = f"{ROOT}/scratch/music/ig10-music-full.mp3"
MUSIC_GAIN = 0.09
NAVY, GOLD = (16, 30, 58, 238), (226, 190, 112)
PLATE_CY = B.CY - 250          # плашка — над субтитрами, на груди, не на лице
PLATE_SIZE, PLATE_MAXW = 50, 880
# (номер, текст плашки, слово-начало, маркер «после этого слова»)
PLATES = [("01", "«Мне было приятно помочь»", "Мне", "Первое."),
          ("02", "«Спасибо, что подождали»", "спасибо", "Второе."),
          ("03", "«Я этим займусь»", "этим", "Третье."),
          ("04", "«Я узнаю»", "узнаю", "Четвёртое."),
          ("05", "«Я много для этого сделал»", "много", "Пятое."),
          ("", "Уверенность — в деталях", "Настоящая", "двадцать")]


def render_plate(path, num, text):
    f = ImageFont.truetype(B.FONT, PLATE_SIZE)
    fn = ImageFont.truetype(B.FONT, PLATE_SIZE - 8)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tw = d0.textlength(text, font=f)
    nw = d0.textlength(num, font=fn) + 44 if num else 0
    w, h = int(tw + nw + 64), 104
    assert w <= PLATE_MAXW + 120, text
    im = Image.new("RGBA", (B.W, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = (B.W - w) // 2, (160 - h) // 2
    d.rounded_rectangle([x0 + 4, y0 + 6, x0 + w + 4, y0 + h + 6], 10, fill=(0, 0, 0, 90))
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 10, fill=NAVY, outline=GOLD + (255,), width=3)
    x = x0 + 32
    if num:
        d.text((x, y0 + h / 2), num, font=fn, fill=GOLD, anchor="lm")
        x += nw - 22
        d.line([(x - 12, y0 + 24), (x - 12, y0 + h - 24)], fill=GOLD, width=2)
        x += 10
    d.text((x, y0 + h / 2), text, font=f, fill=GOLD, anchor="lm")
    im.save(path)
    assert 250 <= PLATE_CY - h / 2 and PLATE_CY + h / 2 <= 1500


def main():
    os.makedirs(B.TMP, exist_ok=True)
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    subs = N.chunks_with_hook(words, min(total, last + 0.6))
    starts = [F(w, F(after)) for _, _, w, after in PLATES]
    plates = [(num, text, t0, (starts[i + 1] - 0.4) if i + 1 < len(starts) else total)
              for i, ((num, text, _, _), t0) in enumerate(zip(PLATES, starts))]
    for (_, a, t0, t1) in plates:
        assert t1 - t0 >= 2.0, f"плашка «{a}» мелькает ({t1 - t0:.1f} с)"
    assert plates[0][2] >= subs[0]["t1"], "плашка не должна идти под заголовком-крючком"
    json.dump({"subs": subs, "plates": plates}, open(f"{B.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [], audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={B.W}:{B.H}:force_original_aspect_ratio=increase,crop={B.W}:{B.H},setsar=1,fps=30,format=yuv420p[v0]"]
    prev, n = "[v0]", 2
    for i, (num, text, t0, t1) in enumerate(plates):
        p = f"{B.TMP}/plate{i}.png"
        render_plate(p, num, text)
        inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", p]
        filt.append(f"[{n}:v]format=rgba,fade=in:st={t0:.3f}:d=0.25:alpha=1,"
                    f"fade=out:st={t1 - 0.25:.3f}:d=0.25:alpha=1[p{i}]")
        filt.append(f"{prev}[p{i}]overlay=0:{PLATE_CY - 80}:enable='between(t,{t0:.3f},{t1:.3f})'[vp{i}]")
        prev, n = f"[vp{i}]", n + 1
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        N.render_any(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", prev, "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", B.OUT],
                   check=True)
    print(B.OUT, len(subs), "субтитров,", len(plates), "плашек")


if __name__ == "__main__":
    main()
