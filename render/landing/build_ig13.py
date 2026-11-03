"""Reels №13 «10 причин, почему тебя не уважают» — ведущий сверху, кинокадр снизу.

Как в референсе instagram.com/reel/DeCRxwUodMj: крючок на весь кадр («10 причин…») → кадр делится
пополам: сверху ведущий, снизу на каждую причину свой кинокадр gpt-image-2, на стыке — золотой номер
в кружке и фраза причины (≈3 с на пункт) → десятая причина-поворот и призыв — снова на весь кадр.
Отдельных субтитров нет: фраза на стыке и есть субтитр. Текст — только в зоне 250–1500.

python3 render/landing/build_ig13.py   →  render/landing/ig13-9x16.mp4
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import sfx as SFX

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig13/trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig13-whisper-final.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig13/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig13-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig13"
IMG = f"{ROOT}/scratch/img"
MUSIC = f"{ROOT}/scratch/music/ig13-music.mp3"
MUSIC_GAIN = 0.10
W, H = B.W, B.H
SPLIT = 900                       # верх — ведущий (0..SPLIT), низ — кинокадр (SPLIT..H)
SEAM = SPLIT - 20                 # центр плашки на стыке
HOST_Y = 130                      # откуда вырезать верхнюю половину из полного кадра ведущего
F_NUM = f"{ROOT}/render/fonts/PlayfairDisplay-Bold.ttf"
F_TXT = f"{ROOT}/render/fonts/Montserrat-ExtraBold.ttf"
GOLD, WHITE = (232, 196, 120), (250, 248, 242)

SPOKEN = ("Десять причин, почему тебя не уважают. Ты смеёшься там, где не смешно. Ты слишком много "
          "рассказываешь о себе. Ты молча терпишь неуважение. Ты постоянно ждёшь чужого одобрения. Ты "
          "стараешься быть хорошим для всех. Ты всё время оправдываешься. Ты не умеешь отстаивать свои границы. "
          "Ты говоришь «да», когда хочешь сказать «нет». Ты боишься остаться один. И ты до сих пор не заметил… "
          "что меня сделала нейросеть. Какая причина про тебя? Пиши номер в комментариях.")
ITEMS = ["смеёшься там, где не смешно", "слишком много рассказываешь о себе", "молча терпишь неуважение",
         "ждёшь чужого одобрения", "хочешь быть хорошим для всех", "всё время оправдываешься",
         "не отстаиваешь свои границы", "говоришь «да», когда хочешь «нет»", "боишься остаться один"]
TENTH = "до сих пор не заметил, что меня сделала нейросеть"


def label_png(path, num, text, maxw=880):
    """Золотой номер в кружке + фраза (1–2 строки), с мягкой тенью — читается на любом фоне."""
    fn, ft = ImageFont.truetype(F_NUM, 64), ImageFont.truetype(F_TXT, 46)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], ""
    for w in ("ты " + text).split():
        c = (cur + " " + w).strip()
        if d0.textlength(c, font=ft) > maxw - 120 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = c
    lines.append(cur)
    assert len(lines) <= 2, text
    hgt = 200
    im = Image.new("RGBA", (W, hgt), (0, 0, 0, 0))
    tw = max(d0.textlength(l, font=ft) for l in lines)
    x0 = (W - (tw + 120)) / 2
    sh = Image.new("RGBA", (W, hgt), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.rounded_rectangle([x0 - 30, 30, x0 + tw + 150, hgt - 30], 40, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(im)
    cx, cy = x0 + 44, hgt / 2
    d.ellipse([cx - 44, cy - 44, cx + 44, cy + 44], outline=GOLD, width=4)
    d.text((cx, cy - 4), str(num), font=fn, fill=GOLD, anchor="mm")
    lh = 54
    y = hgt / 2 - lh * len(lines) / 2 + lh / 2
    for ln in lines:
        d.text((x0 + 120, y), ln, font=ft, fill=WHITE, anchor="lm", stroke_width=2, stroke_fill=(0, 0, 0, 200))
        y += lh
    im.save(path)
    return hgt


def title_png(path, lines, size=96):
    f = ImageFont.truetype(F_TXT, size)
    lh = int(size * 1.08)
    im = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0))
    sh = im.copy()
    for i, (t, c) in enumerate(lines):
        ImageDraw.Draw(sh).text((W / 2, 30 + lh * (i + 0.5) + 6), t, font=f, fill=(0, 0, 0, 220), anchor="mm")
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    for i, (t, c) in enumerate(lines):
        assert d.textlength(t, font=f) <= 1000, t
        d.text((W / 2, 30 + lh * (i + 0.5)), t, font=f, fill=GOLD if c == "gold" else WHITE, anchor="mm",
               stroke_width=3, stroke_fill=(0, 0, 0, 230))
    im.save(path)
    return im.height


def main():
    os.makedirs(B.TMP, exist_ok=True)
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    starts, after = [], 0.0
    for _ in range(9):
        t = F("Ты", after)
        starts.append(t - 0.08)
        after = t + 0.3
    t10 = F("И", after) - 0.08
    t_cta = F("Какая", t10) - 0.08
    bounds = starts + [t10]
    for a, b in zip(bounds, bounds[1:]):
        assert b - a >= 1.6, f"пункт мелькает: {a:.2f}–{b:.2f}"
    json.dump({"items": starts, "t10": t10, "cta": t_cta}, open(f"{B.TMP}/plan.json", "w"), indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [(t + 0.05, "pop", 0.35) for t in starts + [t10]], audio, f"{B.TMP}/sfx",
            bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    split_on = f"between(t,{starts[0]:.3f},{t10:.3f})"
    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,format=yuv420p,"
            f"split[full][top0]",
            f"[full]scale=w='trunc({W}*(1+0.05*t/{total:.2f})/2)*2':h='trunc({H}*(1+0.05*t/{total:.2f})/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3'[vfull]",
            f"[top0]crop={W}:{SPLIT}:0:{HOST_Y}[top]",
            f"[vfull][top]overlay=0:0:enable='{split_on}'[v1]"]
    prev, n = "[v1]", 2
    for i, t0 in enumerate(starts):
        t1 = bounds[i + 1]
        dur = t1 - t0
        inputs += ["-loop", "1", "-t", f"{dur + 0.1:.2f}", "-i", f"{IMG}/ig13_b{i + 1}.png"]
        bh = H - SPLIT
        filt.append(f"[{n}:v]scale=-2:{bh + 40},setsar=1,fps=30,"
                    f"scale=w='trunc(iw*(1+0.06*t/{dur:.2f})/2)*2':h='trunc(ih*(1+0.06*t/{dur:.2f})/2)*2':eval=frame,"
                    f"crop={W}:{bh}:'(iw-{W})/2':'(ih-{bh})/2',setpts=PTS+{t0:.3f}/TB[b{i}]")
        filt.append(f"{prev}[b{i}]overlay=0:{SPLIT}:eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[vb{i}]")
        prev, n = f"[vb{i}]", n + 1
    # тонкая золотая линия на стыке
    inputs += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", f"color=c=0xE8C478:s={W}x4:r=30"]
    filt.append(f"{prev}[{n}:v]overlay=0:{SPLIT - 2}:enable='{split_on}'[vline]")
    prev, n = "[vline]", n + 1
    # крючок
    hp = f"{B.TMP}/hook.png"
    hh = title_png(hp, [("10 ПРИЧИН,", "gold"), ("ПОЧЕМУ ТЕБЯ", "white"), ("НЕ УВАЖАЮТ", "white")])
    inputs += ["-i", hp]
    filt.append(f"{prev}[{n}:v]overlay=0:{1180 - hh // 2}:enable='lt(t,{starts[0]:.3f})'[vh]")
    prev, n = "[vh]", n + 1
    # плашки пунктов
    for i, t0 in enumerate(starts):
        p = f"{B.TMP}/lab{i + 1}.png"
        lh = label_png(p, i + 1, ITEMS[i])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{SEAM - lh // 2}:enable='between(t,{t0:.3f},{bounds[i + 1]:.3f})'[l{i}]")
        prev, n = f"[l{i}]", n + 1
    # десятая причина и призыв — на весь кадр, плашка на груди
    p10 = f"{B.TMP}/lab10.png"
    lh = label_png(p10, 10, TENTH)
    inputs += ["-i", p10]
    filt.append(f"{prev}[{n}:v]overlay=0:{1180 - lh // 2}:enable='between(t,{t10:.3f},{t_cta:.3f})'[l10]")
    prev, n = "[l10]", n + 1
    cp = f"{B.TMP}/cta.png"
    ch = title_png(cp, [("КАКАЯ ПРО ТЕБЯ?", "gold"), ("ПИШИ НОМЕР", "white"), ("В КОММЕНТАРИЯХ", "white")], 84)
    inputs += ["-i", cp]
    filt.append(f"{prev}[{n}:v]overlay=0:{1180 - ch // 2}:enable='gte(t,{t_cta:.3f})'[vc]")
    prev, n = "[vc]", n + 1
    assert 1180 - max(hh, ch, lh) // 2 >= 250 and 1180 + max(hh, ch, lh) // 2 <= 1500
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, "пункты:", [round(t, 2) for t in bounds])


if __name__ == "__main__":
    main()
