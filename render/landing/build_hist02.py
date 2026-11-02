"""История России №2 «Часы, у которых крутился циферблат» — Reels 9:16.

Правила серии — docs/scenarios/history/README.md: рисованный дедушка-летописец (HeyGen),
голос Станислав, только настоящие картинки (Wikimedia Commons), движение — монтажом,
без звука «вжух» на сменах, ≤5–6 картинок, каждая держится ≥4 с.

Главный приём — вращающийся циферблат: кольцо из 17 славянских букв-чисел медленно
крутится под неподвижным золотым лучом поверх размытого фото Спасской башни
(рисуется кодом, это монтажная графика, не генерация).

python3 render/landing/build_hist02.py   →  render/landing/hist02-9x16.mp4
"""
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_hist01 as H   # картинки, плашки, наезды/панорамы (общие для серии)
import build_ig6 as B
import sfx as SFX

ROOT = B.ROOT
B.SCEN = f"{ROOT}/docs/scenarios/history/02-clock.md"
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/hist/02-trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/hist02-whisper-a.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/hist/02-host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/hist02-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.hist02"
WEB = f"{ROOT}/scratch/img/web/hist02"
MUSIC = H.MUSIC
MUSIC_GAIN = 0.11
W, H_ = B.W, B.H
GOLD = (214, 170, 82)
DIAL_D, DIAL_CY = 680, 730
F_DIAL = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
# славянские числа 1–17 (буква + титло рисуется линией над ней)
SLAV = ["а", "в", "г", "д", "є", "ѕ", "з", "и", "ѳ", "і", "аі", "ві", "гі", "ді", "єі", "ѕі", "зі"]

# (имя, файл/dial, режим, слово-начало, после слова, слово-конец, опции)
SHOTS = [
    ("dial1", None, "dial", None, None, "Это", {}),
    ("tower", "tower_1.jpg", "cover", "Такие", None, "В", {"dx": 0}),
    ("kremlin", "kremlin_4.jpg", "cover", "В", "Кремля", "Сверху", {"dx": 1}),
    ("dial2", None, "dial", "Сверху", None, "И", {}),
    ("dial3", None, "dial", "Летом", None, "Иностранцы", {"seventeen": True}),
    ("foreign", "spass2_1.jpg", "cover", "Иностранцы", None, "потом", {"dx": -1}),
    ("peter", "peter_1.jpg", "card", "потом", None, "Скажите", {"zoom": 1.06}),
]
CHIPS = [
    ("Спасская башня, Кремль", "Такие", None, "В", 330),
    ("1625 · мастер Христофор Головей", "В", "Кремля", "Сверху", 330),
    ("Вместо цифр — буквы", "вместо", None, "И", 1115),
    ("17 делений — самый длинный день", "Летом", None, "Иностранцы", 1115),
    ("Гравюра XVIII века", "Иностранцы", None, "потом", 330),
    ("Пётр I — часы на 12 цифр", "потом", None, "Скажите", 330),
]
HOOK = ("СТРЕЛКА СТОИТ,", "А ЦИФЕРБЛАТ", "КРУТИТСЯ")


def dial_png(path, seventeen=False):
    d0 = DIAL_D
    im = Image.new("RGBA", (d0, d0), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = d0 / 2
    d.ellipse([6, 6, d0 - 6, d0 - 6], fill=(28, 44, 92, 245), outline=GOLD + (255,), width=10)
    d.ellipse([60, 60, d0 - 60, d0 - 60], outline=GOLD + (200,), width=3)
    d.ellipse([c - 150, c - 150, c + 150, c + 150], fill=(22, 34, 72, 255), outline=GOLD + (220,), width=4)
    f = ImageFont.truetype(F_DIAL, 58)
    r = c - 104
    for i, s in enumerate(SLAV):
        a = -math.pi / 2 + 2 * math.pi * i / 17
        x, y = c + r * math.cos(a), c + r * math.sin(a)
        glyph = Image.new("RGBA", (200, 140), (0, 0, 0, 0))
        g = ImageDraw.Draw(glyph)
        g.text((100, 80), s, font=f, fill=(244, 230, 196), anchor="mm")
        w = g.textlength(s, font=f)
        g.line([(100 - w / 2, 30), (100 - w / 4, 22), (100 + w / 4, 34), (100 + w / 2, 26)], fill=GOLD, width=4)
        glyph = glyph.rotate(-math.degrees(a + math.pi / 2), resample=Image.BICUBIC)
        im.alpha_composite(glyph, (int(x - 100), int(y - 70)))
        # засечки делений
        a2 = a + math.pi / 17
        d.line([(c + (c - 14) * math.cos(a2), c + (c - 14) * math.sin(a2)),
                (c + (c - 52) * math.cos(a2), c + (c - 52) * math.sin(a2))], fill=GOLD, width=4)
    # солнце в центре
    for k in range(16):
        a = 2 * math.pi * k / 16
        d.line([(c + 60 * math.cos(a), c + 60 * math.sin(a)), (c + 120 * math.cos(a), c + 120 * math.sin(a))],
               fill=GOLD, width=6)
    d.ellipse([c - 56, c - 56, c + 56, c + 56], fill=GOLD)
    im.save(path)


def ray_png(path):
    """Неподвижная стрелка — луч солнца сверху, указывает вниз на кольцо."""
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = W / 2
    d.polygon([(cx - 44, 30), (cx + 44, 30), (cx, 270)], fill=(0, 0, 0, 120))
    d.polygon([(cx - 40, 20), (cx + 40, 20), (cx, 258)], fill=GOLD + (255,), outline=(120, 86, 30, 255))
    d.ellipse([cx - 34, 0, cx + 34, 68], fill=GOLD + (255,), outline=(120, 86, 30, 255), width=3)
    im.save(path)


def dial_bg(path):
    im = Image.open(f"{WEB}/tower_1.jpg").convert("RGB")
    k = max(W / im.width, H_ / im.height)
    bg = im.resize((round(im.width * k), round(im.height * k)))
    bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H_))
    bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(26)), Image.new("RGB", (W, H_), (18, 12, 8)), 0.55)
    bg.save(path, quality=94)


def dial_shot(n, t0, dur, label, inputs, filt, bgp, dialp, rayp):
    """Фон + кольцо, вращающееся по часовой (≈ 40° за 6 с), + неподвижный луч."""
    inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", bgp, "-loop", "1", "-t", f"{dur:.2f}", "-i", dialp,
               "-loop", "1", "-t", f"{dur:.2f}", "-i", rayp]
    filt.append(f"[{n}:v]scale={W}:{H_},setsar=1,fps=30,format=rgba[db{label}]")
    filt.append(f"[{n + 1}:v]fps=30,format=rgba,rotate=a='0.12*t':c=none:ow={DIAL_D}:oh={DIAL_D}[dr{label}]")
    filt.append(f"[db{label}][dr{label}]overlay={(W - DIAL_D) // 2}:{DIAL_CY - DIAL_D // 2}[dd{label}]")
    filt.append(f"[dd{label}][{n + 2}:v]overlay=0:{DIAL_CY - DIAL_D // 2 - 210},"
                f"fade=in:st=0:d=0.3:alpha=1,fade=out:st={dur - 0.3:.2f}:d=0.3:alpha=1,"
                f"setpts=PTS+{t0:.3f}/TB[{label}]")
    return n + 3


def main():
    os.makedirs(B.TMP, exist_ok=True)
    words, last = B.timed_words()
    F = H.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    hook_end = F("Это") - 0.1
    subs = B.chunks(words, min(total, last + 0.6))
    cta_t = F("Скажите")
    subs = [s for s in subs if s["t0"] < cta_t - 0.05]
    subs[-1]["t1"] = min(subs[-1]["t1"], cta_t)

    shots = []
    for name, file, mode, w0, after, w1, opt in SHOTS:
        t0 = 0.0 if w0 is None else F(w0, after) - 0.15
        t1 = F(w1, w0 if after is None else after) - 0.15
        shots.append((name, file, mode, t0, t1, opt))
    for a, b in zip(shots, shots[1:]):
        assert a[4] <= b[3] + 0.01, f"кадры {a[0]}/{b[0]} перекрываются"
    for s in shots:
        assert s[4] - s[3] >= 4.0, f"кадр {s[0]} мелькает ({s[4] - s[3]:.1f} с)"
    chips = []
    for text, w0, after, w1, y in CHIPS:
        t0 = F(w0, after) + 0.1
        t1 = F(w1, w0 if after is None else after) - 0.2
        assert t1 - t0 >= 2.0, f"плашка «{text}» мелькает"
        chips.append((text, t0, t1, y))
    json.dump({"subs": subs, "shots": shots, "chips": chips}, open(f"{B.TMP}/plan.json", "w"),
              ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"   # без «вжуха» на сменах — только музыка под голос
    SFX.mix(B.AUDIO, [], audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    bgp, dialp, dial17, rayp = (f"{B.TMP}/dial_bg.jpg", f"{B.TMP}/dial.png", f"{B.TMP}/dial17.png",
                                f"{B.TMP}/ray.png")
    dial_bg(bgp)
    dial_png(dialp)
    dial_png(dial17, True)
    ray_png(rayp)

    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={W}:{H_}:force_original_aspect_ratio=increase,crop={W}:{H_},setsar=1,fps=30,"
            f"scale=w='trunc({W}*(1+0.04*t/{total:.2f})/2)*2':h='trunc({H_}*(1+0.04*t/{total:.2f})/2)*2':eval=frame,"
            f"crop={W}:{H_}:'(iw-{W})/2':'(ih-{H_})/3',format=yuv420p[v0]"]
    prev, n = "[v0]", 2
    for i, (name, file, mode, t0, t1, opt) in enumerate(shots):
        dur = t1 - t0
        if mode == "dial":
            n = dial_shot(n, t0, dur, f"b{i}", inputs, filt, bgp, dial17 if opt.get("seventeen") else dialp, rayp)
        elif mode == "cover":
            p = f"{B.TMP}/{name}.jpg"
            size = H.cover_src(f"{WEB}/{file}", p)
            inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", p]
            filt.append(H.pan(n, t0, dur, f"b{i}", size, opt.get("dx", 1)))
            n += 1
        else:
            p = f"{B.TMP}/{name}.jpg"
            H.card_src(f"{WEB}/{file}", p)
            inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", p]
            filt.append(H.kb(n, t0, dur, f"b{i}", opt.get("zoom", 1.06)))
            n += 1
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass[vb{i}]")
        prev = f"[vb{i}]"
    # крючок — внизу, под циферблатом
    hp = f"{B.TMP}/hook.png"
    him = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    hd = ImageDraw.Draw(him)
    hf = ImageFont.truetype(H.F_SERIF, 80)
    for i, ln in enumerate(HOOK):
        assert hd.textlength(ln, font=hf) < W - 80, ln
        hd.text((W / 2, 60 + i * 98), ln, font=hf, fill=H.PARCH, anchor="mm", stroke_width=5,
                stroke_fill=(30, 18, 8, 240))
    hd.line([(260, 60 + len(HOOK) * 98 - 30), (W - 260, 60 + len(HOOK) * 98 - 30)], fill=H.RED + (230,), width=6)
    him.save(hp)
    inputs += ["-i", hp]
    filt.append(f"{prev}[{n}:v]overlay=0:1110:enable='lt(t,{hook_end:.3f})'[vh]")
    prev, n = "[vh]", n + 1
    for i, (text, t0, t1, y) in enumerate(chips):
        p = f"{B.TMP}/chip{i}.png"
        H.chip_png(p, text)
        inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", p]
        filt.append(f"[{n}:v]format=rgba,fade=in:st={t0:.3f}:d=0.25:alpha=1,fade=out:st={t1 - 0.25:.3f}:d=0.25:alpha=1[c{i}]")
        filt.append(f"{prev}[c{i}]overlay=0:{y - 70}:enable='between(t,{t0:.3f},{t1:.3f})'[vc{i}]")
        prev, n = f"[vc{i}]", n + 1
    cp = f"{B.TMP}/cta.png"
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(H.F_SERIF, 82)
    for i, ln in enumerate(["А вы бы поняли,", "который час?"]):
        d.text((W / 2, 80 + i * 104), ln, font=f, fill=H.PARCH, anchor="mm", stroke_width=5,
               stroke_fill=(30, 18, 8, 240))
    im.save(cp)
    inputs += ["-i", cp]
    filt.append(f"{prev}[{n}:v]overlay=0:980:enable='gte(t,{cta_t:.3f})'[vcta]")
    prev, n = "[vcta]", n + 1
    for i, s in enumerate(subs):
        if s["t1"] <= hook_end:
            continue
        p = f"{B.TMP}/sub{i:03d}.png"
        B.render_sub(p, s["text"])
        inputs += ["-i", p]
        t0 = max(s["t0"], hook_end)
        filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 130}:enable='gte(t,{t0:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    filt.append(f"{prev}colorbalance=rs=0.04:bs=-0.05:rm=0.03:bm=-0.03,vignette=PI/5,format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "21", "-maxrate", "9M", "-bufsize", "18M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, len(subs), "субтитров,", len(shots), "кадров")


if __name__ == "__main__":
    main()
