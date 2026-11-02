"""История России №1 «Каракули Онфима» — Reels 9:16.

Серия «История России»: рисованный дедушка-летописец (HeyGen, голос Станислав) + только
настоящие картинки с Wikimedia Commons (общественное достояние / CC). Движение — монтажом:
наезды и панорамы по картинам, вырезанный всадник «скачет» по кадру, быстрые склейки
музейных снимков. Тёплая винтажная обработка (виньетка, зерно), пергаментные плашки,
белые субтитры (движок build_ig6), тихая фолк-музыка из библиотеки HeyGen.
Весь текст — в безопасной зоне 250–1500.

python3 render/landing/build_hist01.py   →  render/landing/hist01-9x16.mp4
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import sfx as SFX

ROOT = B.ROOT
B.SCEN = f"{ROOT}/docs/scenarios/history/01-onfim.md"
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/hist/01-trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/hist01-whisper-a.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/hist/01-host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/hist01-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.hist01"
WEB = f"{ROOT}/scratch/img/web/hist01"
MUSIC = f"{ROOT}/scratch/music/hist-folk.wav"
MUSIC_GAIN = 0.11
W, H = B.W, B.H
FONTS = f"{ROOT}/render/fonts"
F_SERIF = f"{FONTS}/PlayfairDisplay-Bold.ttf"
F_HAND = f"{FONTS}/Caveat-Bold.ttf"
F_SANS = f"{FONTS}/Montserrat-ExtraBold.ttf"
PARCH, INK, RED = (241, 228, 200), (52, 36, 22), (176, 42, 30)
SUB_TOP = B.CY - 130          # верх полосы субтитров: картинки и плашки — выше

# Кадры поверх ведущего: (имя, файл, режим, слово-начало, после слова, слово-конец/секунды)
#   cover  — картина на весь кадр, панорама по горизонтали (dx: -1 влево, 1 вправо) + наезд
#   card   — снимок на размытой подложке в рамке (музейные фото и грамоты), наезд
#   ride   — вырезанный всадник скачет по размытой иконе
SHOTS = [
    ("novgorod", "vasnetsov_4.jpg", "cover", "Новгороде", None, "Звали", {"dx": 1}),
    ("birch", "nerev_1.jpg", "cover", "Бумаги", None, "острым", {"dx": 0}),
    ("stylus", "stylusn_2.jpg", "card", "острым", None, "И", {}),
    ("lesson", "onfimx_6.jpg", "card", "И", "коре", "всадником", {"zoom": 1.12}),
    ("ride", "rider_3.jpg", "ride", "всадником", None, "а", {"cut": "rider3_cut.png"}),
    ("beast", "onfim_6.jpg", "card", "а", "копьем", "Береста", {"zoom": 1.10}),
    ("found1", "onfim_2.jpg", "card", "В", "уцелела", "стопку", {}),
    ("found2", "onfim_4.jpg", "card", "стопку", None, "рисунков", {}),
    ("found3", "onfimx_8.jpg", "card", "рисунков", "уроков", "Это", {}),
    ("famous", "onfimx_6.jpg", "card", "Это", None, "Выходит", {"zoom": 1.06}),
]
# Плашки: (текст, слово-начало, после слова, слово-конец, y центра)
CHIPS = [
    ("Новгород · XIII век", "Новгороде", None, "Звали", 330),
    ("Онфим, 6–7 лет", "Онфим", None, "Бумаги", 330),
    ("Писала, XIII век", "острым", None, "И", 330),
    ("Береста № 210 · рисунок Онфима", "И", "коре", "всадником", 330),
    ("Нашли в 1956 году", "В", "уцелела", "Это", 330),
    ("Автор известен по имени", "автор", None, "Выходит", 330),
]
HOOK = ("ЕГО КАРАКУЛИ", "ПЕРЕЖИЛИ 700 ЛЕТ")


def finder(words):
    def F(needle, after=None):
        t0 = 0.0 if after is None else F(after)
        for w, t in words:
            if t >= t0 - 0.01 and B.norm(w) == B.norm(needle):
                return t
        raise KeyError(needle)
    return F


# ---------- картинки ----------

def cover_src(path, out):
    """Картина под панораму: высота 2000, ширина ≥ 1180 (запас на движение)."""
    im = Image.open(path).convert("RGB")
    k = max(2000 / im.height, 1180 / im.width)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    im.save(out, quality=94)
    return im.size


def card_src(path, out, fg=None):
    """Снимок в пергаментной рамке на размытой затемнённой подложке, 1080×1920."""
    im = Image.open(path).convert("RGB")
    k = max(W / im.width, H / im.height)
    bg = im.resize((round(im.width * k), round(im.height * k)))
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(30))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (20, 14, 8)), 0.55)
    box_w, box_h = 940, SUB_TOP - 60 - 420
    k = min(box_w / im.width, box_h / im.height)
    fgi = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (W - fgi.width) // 2, 420 + (box_h - fgi.height) // 2
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rectangle([x - 14, y - 4, x + fgi.width + 22, y + fgi.height + 30], fill=170)
    bg.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(22)))
    ImageDraw.Draw(bg).rectangle([x - 12, y - 12, x + fgi.width + 12, y + fgi.height + 12], fill=PARCH)
    bg.paste(fgi, (x, y))
    bg.save(out, quality=94)
    assert y + fgi.height + 12 <= SUB_TOP - 20


def ride_src(icon, cut, out_bg, out_rider):
    im = Image.open(icon).convert("RGB")
    k = max(W / im.width, H / im.height)
    bg = im.resize((round(im.width * k), round(im.height * k)))
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(24)), Image.new("RGB", (W, H), (25, 12, 6)), 0.5)
    bg.save(out_bg, quality=94)
    r = Image.open(cut).convert("RGBA")
    r = r.crop(r.getbbox())
    k = 860 / r.width
    r = r.resize((round(r.width * k), round(r.height * k)), Image.LANCZOS)
    if r.height > 760:
        k = 760 / r.height
        r = r.resize((round(r.width * k), round(r.height * k)), Image.LANCZOS)
    r.save(out_rider)
    return r.size


# ---------- плашки ----------

def chip_png(path, text):
    f = ImageFont.truetype(F_SERIF, 46)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tw = d0.textlength(text, font=f)
    w, h = int(tw + 72), 92
    assert w <= W - 80, text
    im = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = (W - w) // 2, 24
    d.rounded_rectangle([x0 + 4, y0 + 8, x0 + w + 4, y0 + h + 8], 8, fill=(0, 0, 0, 110))
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 8, fill=PARCH + (250,), outline=INK + (255,), width=2)
    d.line([(x0 + 18, y0 + h - 16), (x0 + w - 18, y0 + h - 16)], fill=RED + (200,), width=2)
    d.text((W / 2, y0 + h / 2 - 4), text, font=f, fill=INK, anchor="mm")
    im.save(path)


def hook_png(path):
    im = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_SERIF, 92)
    for i, ln in enumerate(HOOK):
        d.text((W / 2, 90 + i * 112), ln, font=f, fill=PARCH, anchor="mm", stroke_width=5, stroke_fill=(30, 18, 8, 240))
    d.line([(260, 286), (W - 260, 286)], fill=RED + (230,), width=6)
    im.save(path)


def zver_png(path):
    im = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_HAND, 150)
    d.text((W / 2 + 4, 136), "«Я зверь»", font=f, fill=(0, 0, 0, 150), anchor="mm")
    d.text((W / 2, 130), "«Я зверь»", font=f, fill=RED, anchor="mm", stroke_width=3, stroke_fill=PARCH + (255,))
    im.save(path)


def cta_png(path):
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_SERIF, 64)
    lines = ["А что рисовали", "на полях вы? ✍"]
    for i, ln in enumerate(lines):
        d.text((W / 2, 80 + i * 86), ln, font=f, fill=PARCH, anchor="mm", stroke_width=5, stroke_fill=(30, 18, 8, 240))
    im.save(path)


# ---------- сборка ----------

def kb(idx, start, dur, label, zoom=1.06, w=W):
    """Неподвижный кадр 1080×1920 → медленный наезд к центру."""
    return (f"[{idx}:v]scale={W}:{H},setsar=1,fps=30,format=rgba,"
            f"scale=w='trunc({W}*(1+{zoom - 1:.3f}*t/{dur:.2f})/2)*2':h='trunc({H}*(1+{zoom - 1:.3f}*t/{dur:.2f})/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/2',"
            f"fade=in:st=0:d=0.25:alpha=1,fade=out:st={dur - 0.25:.2f}:d=0.25:alpha=1,"
            f"setpts=PTS+{start:.3f}/TB[{label}]")


def pan(idx, start, dur, label, size, dx):
    iw, ih = size
    x0, x1 = (0, iw - W) if dx >= 0 else (iw - W, 0)
    if dx == 0:
        x0 = x1 = (iw - W) // 2
    return (f"[{idx}:v]setsar=1,fps=30,format=rgba,"
            f"crop={W}:{H}:'{x0}+({x1}-{x0})*t/{dur:.2f}':'(ih-{H})/2+40-40*t/{dur:.2f}',"
            f"fade=in:st=0:d=0.25:alpha=1,fade=out:st={dur - 0.25:.2f}:d=0.25:alpha=1,"
            f"setpts=PTS+{start:.3f}/TB[{label}]")


def main():
    os.makedirs(B.TMP, exist_ok=True)
    words, last = B.timed_words()
    F = finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    subs = B.chunks(words, min(total, last + 0.6))
    hook_end = F("Новгороде") - 0.05
    subs = [s for s in subs if s["t1"] > hook_end + 0.05]
    subs[0]["t0"] = max(subs[0]["t0"], hook_end)

    shots = []
    for name, file, mode, w0, after, w1, opt in SHOTS:
        t0 = F(w0, after) - 0.15
        t1 = F(w1, w0 if after is None else after) - 0.15 if isinstance(w1, str) else t0 + w1
        shots.append((name, file, mode, t0, t1, opt))
    for a, b in zip(shots, shots[1:]):
        assert a[4] <= b[3] + 0.01, f"кадры {a[0]}/{b[0]} перекрываются"
        assert a[4] - a[3] >= 1.4, f"кадр {a[0]} мелькает ({a[4] - a[3]:.1f} с)"
    chips = []
    for text, w0, after, w1, y in CHIPS:
        t0 = F(w0, after) + 0.1
        t1 = F(w1, w0 if after is None else after) - 0.2
        assert t1 - t0 >= 2.0, f"плашка «{text}» мелькает"
        chips.append((text, t0, t1, y))
    zt = F("подписывает")
    cta_t = F("Напишите")
    json.dump({"subs": subs, "shots": shots, "chips": chips}, open(f"{B.TMP}/plan.json", "w"),
              ensure_ascii=False, indent=1)

    events = [(s[3], "whoosh", 0.25) for s in shots] + [(zt + 1.0, "pop", 0.5), (cta_t, "pop", 0.4)]
    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, events, audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total,
            bed_fn=SFX.music_bed(MUSIC))

    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
            f"scale=w='trunc({W}*(1+0.04*t/{total:.2f})/2)*2':h='trunc({H}*(1+0.04*t/{total:.2f})/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3',format=yuv420p[v0]"]
    prev, n = "[v0]", 2
    for i, (name, file, mode, t0, t1, opt) in enumerate(shots):
        dur = t1 - t0
        src = f"{WEB}/{file}"
        if mode == "cover":
            p = f"{B.TMP}/{name}.jpg"
            size = cover_src(src, p)
            inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", p]
            filt.append(pan(n, t0, dur, f"b{i}", size, opt.get("dx", 1)))
            n += 1
        elif mode == "card":
            p = f"{B.TMP}/{name}.jpg"
            card_src(src, p)
            inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", p]
            filt.append(kb(n, t0, dur, f"b{i}", opt.get("zoom", 1.06)))
            n += 1
        else:
            pb, pr = f"{B.TMP}/{name}_bg.jpg", f"{B.TMP}/{name}_rider.png"
            rw, rh = ride_src(src, f"{WEB}/{opt['cut']}", pb, pr)
            inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", pb, "-loop", "1", "-t", f"{dur:.2f}", "-i", pr]
            filt.append(kb(n, 0, dur, f"rb{i}", 1.05).replace(f"setpts=PTS+0.000/TB", "setpts=PTS-STARTPTS"))
            xe = (W - rw) // 2
            # въезд слева с замедлением и «галоп» — покачивание по вертикали
            filt.append(f"[{n + 1}:v]format=rgba,setpts=PTS-STARTPTS[rr{i}]")
            filt.append(f"[rb{i}][rr{i}]overlay=x='-{rw}+({xe}+{rw})*(1-pow(1-min(t/{dur * 0.7:.2f}\\,1)\\,3))':"
                        f"y='{(SUB_TOP - rh) // 2 + 120}+14*sin(2*PI*t*2.6)':eval=frame,"
                        f"fade=in:st=0:d=0.25:alpha=1,fade=out:st={dur - 0.25:.2f}:d=0.25:alpha=1,"
                        f"setpts=PTS+{t0:.3f}/TB[b{i}]")
            n += 2
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass[vb{i}]")
        prev = f"[vb{i}]"
    # крючок
    hp = f"{B.TMP}/hook.png"
    hook_png(hp)
    inputs += ["-i", hp]
    filt.append(f"{prev}[{n}:v]overlay=0:300:enable='lt(t,{hook_end:.3f})'[vh]")
    prev, n = "[vh]", n + 1
    for i, (text, t0, t1, y) in enumerate(chips):
        p = f"{B.TMP}/chip{i}.png"
        chip_png(p, text)
        inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", p]
        filt.append(f"[{n}:v]format=rgba,fade=in:st={t0:.3f}:d=0.25:alpha=1,fade=out:st={t1 - 0.25:.3f}:d=0.25:alpha=1[c{i}]")
        filt.append(f"{prev}[c{i}]overlay=0:{y - 70}:enable='between(t,{t0:.3f},{t1:.3f})'[vc{i}]")
        prev, n = f"[vc{i}]", n + 1
    zp, cp = f"{B.TMP}/zver.png", f"{B.TMP}/cta.png"
    zver_png(zp)
    cta_png(cp)
    zs = zt + 0.9
    ze = F("Береста") - 0.3
    inputs += ["-i", zp, "-i", cp]
    filt.append(f"{prev}[{n}:v]overlay=0:820:enable='between(t,{zs:.3f},{ze:.3f})'[vz]")
    filt.append(f"[vz][{n + 1}:v]overlay=0:330:enable='gte(t,{cta_t:.3f})'[vcta]")
    prev, n = "[vcta]", n + 2
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        B.render_sub(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    # винтаж: тёплый тон, виньетка, зерно
    filt.append(f"{prev}colorbalance=rs=0.04:bs=-0.05:rm=0.03:bm=-0.03,vignette=PI/5,"
                f"noise=alls=7:allf=t,format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", B.OUT],
                   check=True)
    print(B.OUT, len(subs), "субтитров,", len(shots), "кадров")


if __name__ == "__main__":
    main()
