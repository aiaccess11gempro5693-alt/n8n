"""Reels №11 «Назови трёх людей» — ведущий за столом с микрофоном, голос Гончаров.

Как в референсе instagram.com/reel/DeuNBKCIh7O: интерактив «назови за 3 секунды», счёт
киноплёнкой (ракорд: круг, крест, бегущий сектор, цифра — рисуется кодом покадрово, цифры
идут вверх вместе с голосом «раз, два, три»), «дай угадаю», вставки-кинокадры, крупные слова
поверх кадра, белые субтитры (движок build_ig6), тихая музыка. Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig11.py   →  render/landing/ig11-9x16.mp4
"""
import json
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N     # broll_filter, finder
import sfx as SFX

ROOT = B.ROOT
B.SCEN = f"{ROOT}/docs/scenarios/insta-11-three-people.md"
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig11/trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig11-whisper-a.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig11/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig11-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig11"
IMG = f"{ROOT}/scratch/img"
MUSIC = os.environ.get("MUSIC", f"{ROOT}/scratch/music/ig11-music.mp3")
MUSIC_GAIN = 0.09
W, H = B.W, B.H
F_SERIF = f"{ROOT}/render/fonts/PlayfairDisplay-Bold.ttf"
F_HEAD = f"{ROOT}/render/fonts/Oswald-Bold.ttf"
CREAM, GOLD = (250, 240, 222), (232, 196, 120)

# крупный заголовок до отсчёта: (строка, цвет)
HOOK = [("3 СЕКУНДЫ:", "gold"), ("ТРИ САМЫХ ЛЮБИМЫХ?", "cream")]
# крупные слова поверх ведущего: (текст, слово-начало, слово-конец)
POPS = [("СЕБЯ — НЕ НАЗВАЛ?", "Себя", "А")]
# кинокадры: (картинка, слово-начало, слово-конец, крупная надпись)
BROLLS = [("ig11_b0", "А", "Подумай", "КАЖДУЮ МИНУТУ — С СОБОЙ"),
          ("ig11_b1", "Цени", "Отправь", "ЛЮБИ СЕБЯ")]
CTA = ("КОГО НАЗВАЛ ТЫ?", "комментариях")      # текст, слово-начало


def serif_png(path, text, size=104, color=CREAM, maxw=980):
    f = ImageFont.truetype(F_SERIF, size)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while d0.textlength(text, font=f) > maxw and size > 60:
        size -= 4
        f = ImageFont.truetype(F_SERIF, size)
    im = Image.new("RGBA", (W, 220), (0, 0, 0, 0))
    tw = d0.textlength(text, font=f)
    band = Image.new("RGBA", (W, 220), (0, 0, 0, 0))
    ImageDraw.Draw(band).rounded_rectangle([W / 2 - tw / 2 - 50, 40, W / 2 + tw / 2 + 50, 180], 60,
                                           fill=(20, 12, 6, 120))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(22)))
    sh = Image.new("RGBA", (W, 220), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((W / 2, 112), text, font=f, fill=(0, 0, 0, 230), anchor="mm")
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((W / 2, 106), text, font=f, fill=color, anchor="mm",
                            stroke_width=2, stroke_fill=(40, 26, 14, 200))
    im.save(path)


def hook_png(path, lines, size=92):
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    f = ImageFont.truetype(F_SERIF, size)
    while max(d0.textlength(t, font=f) for t, _ in lines) > 980:
        size -= 4
        f = ImageFont.truetype(F_SERIF, size)
    lh = size * 1.18
    im = Image.new("RGBA", (W, int(lh * len(lines) + 60)), (0, 0, 0, 0))
    tw = max(d0.textlength(t, font=f) for t, _ in lines)
    band = im.copy()
    ImageDraw.Draw(band).rounded_rectangle([W / 2 - tw / 2 - 50, 20, W / 2 + tw / 2 + 50, im.height - 20], 60,
                                           fill=(20, 12, 6, 120))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(22)))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for i, (txt, c) in enumerate(lines):
        y = 30 + lh * (i + 0.5)
        ImageDraw.Draw(sh).text((W / 2, y + 6), txt, font=f, fill=(0, 0, 0, 200), anchor="mm")
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    for i, (txt, c) in enumerate(lines):
        assert d.textlength(txt, font=f) <= 1000, txt
        d.text((W / 2, 30 + lh * (i + 0.5)), txt, font=f, fill=GOLD if c == "gold" else CREAM, anchor="mm",
               stroke_width=2, stroke_fill=(40, 26, 14, 200))
    im.save(path)
    return im.height


def leader_frames(folder, t0, marks, dur, fps=30):
    """Ракорд киноплёнки: цифра 1/2/3 по таймингам голоса, сектор обегает круг за отрезок."""
    os.makedirs(folder, exist_ok=True)
    rnd = random.Random(7)
    f = ImageFont.truetype(F_HEAD, 560)
    cx, cy, r = W / 2, 820, 420
    n = int(dur * fps)
    for i in range(n):
        t = t0 + i / fps
        k = max(j for j, m in enumerate(marks) if t >= m - 1e-6) if t >= marks[0] else 0
        seg_end = marks[k + 1] if k + 1 < len(marks) else t0 + dur
        p = (t - marks[k]) / max(0.1, seg_end - marks[k])
        im = Image.new("RGB", (W, H), (34, 33, 31))
        d = ImageDraw.Draw(im)
        d.pieslice([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * max(0.0, min(1, p)), fill=(78, 75, 70))
        for rr, wdt in ((r, 10), (r - 70, 5)):
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(225, 220, 210), width=wdt)
        d.line([(cx, cy - r - 120), (cx, cy + r + 120)], fill=(225, 220, 210), width=4)
        d.line([(60, cy), (W - 60, cy)], fill=(225, 220, 210), width=4)
        d.text((cx, cy + 10), str(k + 1), font=f, fill=(245, 242, 235), anchor="mm",
               stroke_width=8, stroke_fill=(20, 20, 20))
        # пыль и царапины старой плёнки
        for _ in range(14):
            x, y = rnd.randrange(W), rnd.randrange(H)
            d.ellipse([x, y, x + rnd.randint(2, 6), y + rnd.randint(2, 6)], fill=(200, 196, 188))
        if rnd.random() < 0.35:
            x = rnd.randrange(80, W - 80)
            d.line([(x, 0), (x + rnd.randint(-20, 20), H)], fill=(150, 146, 140), width=2)
        im = Image.blend(im, Image.new("RGB", (W, H), (20, 18, 15)), rnd.uniform(0, 0.08))
        im.save(f"{folder}/f{i:04d}.jpg", quality=88)
    return n


def main():
    os.makedirs(B.TMP, exist_ok=True)
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    subs = B.chunks(words, min(total, last + 0.6))
    marks = [F("Раз") - 0.1, F("два") - 0.1, F("три", F("два")) - 0.1]
    lead_t0, lead_t1 = marks[0] - 0.2, F("Дай") - 0.15
    pops = [(txt, F(w0) - 0.05, F(w1, F(w0)) - 0.15) for txt, w0, w1 in POPS]
    brolls = [(img, F(w0, F("Себя")) - 0.1 if w0 == "А" else F(w0) - 0.1, F(w1) - 0.15, txt)
              for img, w0, w1, txt in BROLLS]
    cta_t = F(CTA[1]) - 0.1
    for (_, a0, a1) in pops:
        assert a1 - a0 >= 1.4, "крупное слово мелькает"
    for img, t0, t1, _ in brolls:
        assert t1 - t0 >= 2.5, f"кадр {img} мелькает"
    json.dump({"subs": subs, "pops": pops, "brolls": brolls, "marks": marks}, open(f"{B.TMP}/plan.json", "w"),
              ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    bed = SFX.music_bed(MUSIC) if os.path.exists(MUSIC) else None
    SFX.mix(B.AUDIO, [(m, "beep", 0.22) for m in marks], audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN,
            total=total, bed_fn=bed)

    lead_dir = f"{B.TMP}/leader"
    leader_frames(lead_dir, lead_t0, marks, lead_t1 - lead_t0)
    inputs = ["-i", B.CLIP, "-i", audio, "-framerate", "30", "-i", f"{lead_dir}/f%04d.jpg"]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
            f"scale=w='trunc({W}*(1+0.05*t/{total:.2f})/2)*2':h='trunc({H}*(1+0.05*t/{total:.2f})/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3',format=yuv420p[v0]",
            f"[2:v]format=yuv420p,setpts=PTS-STARTPTS+{lead_t0:.3f}/TB[lead]",
            f"[v0][lead]overlay=0:0:eof_action=pass[vl]"]
    hp = f"{B.TMP}/hook.png"
    hh = hook_png(hp, HOOK)
    inputs += ["-i", hp]
    filt.append(f"[vl][3:v]overlay=0:{1190 - hh}:enable='lt(t,{lead_t0:.3f})'[vh]")
    assert 1190 - hh >= 860, hh
    prev, n = "[vh]", 4
    for i, (img, t0, t1, txt) in enumerate(brolls):
        dur = t1 - t0
        inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", f"{IMG}/{img}.png"]
        filt.append(N.broll_filter(n, t0, dur, f"b{i}"))
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass[vb{i}]")
        prev, n = f"[vb{i}]", n + 1
        p = f"{B.TMP}/bt{i}.png"
        serif_png(p, txt, 96, CREAM if i else GOLD)
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:880:enable='between(t,{t0 + 0.4:.3f},{t1 - 0.2:.3f})'[vbt{i}]")
        prev, n = f"[vbt{i}]", n + 1
    for i, (txt, t0, t1) in enumerate(pops):
        p = f"{B.TMP}/pop{i}.png"
        serif_png(p, txt, 100)
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:930:enable='between(t,{t0:.3f},{t1:.3f})'[vp{i}]")
        prev, n = f"[vp{i}]", n + 1
    cp = f"{B.TMP}/cta.png"
    serif_png(cp, CTA[0], 104, GOLD)
    inputs += ["-i", cp]
    filt.append(f"{prev}[{n}:v]overlay=0:930:enable='gte(t,{cta_t:.3f})'[vc]")
    prev, n = "[vc]", n + 1
    for i, s in enumerate(subs):
        if s["t0"] >= lead_t0 - 0.05 and s["t1"] <= lead_t1 + 0.3:   # во время отсчёта — только плёнка
            continue
        p = f"{B.TMP}/sub{i:03d}.png"
        B.render_sub(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, len(subs), "субтитров")


if __name__ == "__main__":
    main()
