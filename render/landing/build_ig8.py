"""Reels №8 «7 правил» — ведущая-коуч + картинки, визуализирующие каждое правило.

Как в референсе instagram.com/reel/DdRdmF6Ov0b: ведущая в кадре со склейками-наездами,
на каждом правиле — плашка «ПРАВИЛО N · …», затем полноэкранная картинка (gpt-image-2)
с медленным наездом; субтитры заглавными, ключевое слово выделено цветом.
Весь текст и графика — в безопасной зоне 250–1500 px.

python3 render/landing/build_ig8.py   →  render/landing/ig8-9x16.mp4
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig7 as S   # numfix / chunk_words — общие

ROOT = B.ROOT
B.SCEN = f"{ROOT}/docs/scenarios/insta-8-7-rules.md"
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig8-victoria-whisper.json")
B.NUMS = {}
B.MAXC = 28
B.SCEN_SPLIT = "## Наш текст (разметка для eleven_v3)"
AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig8-full-trim.mp3")
CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig8-host.mp4")
OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig8-9x16.mp4")
TMP = f"{ROOT}/render/landing/.ig8"
IMG = f"{ROOT}/scratch/img"
FONT = f"{ROOT}/render/fonts/Montserrat-ExtraBold.ttf"
W, H = 1080, 1920
SAFE_TOP, SAFE_BOTTOM = 250, 1500
CAP_CY, CAP_SIZE = 1270, 64
ACCENT = (110, 205, 255)
FACE = (540, 560)
PUNCH = 1.18
RULE_Y = CAP_CY - 235   # плашка правила — над субтитрами, на груди, не на лице

# правило: (номер, плашка, слово начала правила, картинка, слово начала картинки, длительность картинки)
RULES = [
    (1, "ОТМЕНЯЮ", "Первое", "ig8_b1", "Поймала", 4.6),
    (2, "Я ВЫБИРАЮ", "Второе", "ig8_b2", "сразу", 4.6),
    (3, "МИР ПОЗАБОТИТСЯ", "Третье", "ig8_b3", "Сделай", 4.6),
    (4, "ПРОСТИ И ПРОЩАЙ", "Четвёртое", "ig8_b4", "Не", 4.6),
    (5, "МНЕ ВЕЗЁТ", "Пятое", "ig8_b5", "Нужный", 4.6),
    (6, "ВОЗВРАЩАЮ ЭНЕРГИЮ", "Шестое", "ig8_b6", "Закрой", 4.6),
    (7, "ПОПРОСИ ПОДСКАЗКУ", "седьмое", "ig8_b7", "Не", 4.6),
]
FINAL = ("ig8_b8", "Действуй", 4.6)


def scen_words():
    s = open(B.SCEN, encoding="utf-8").read().split(B.SCEN_SPLIT)[1]
    s = re.sub(r"\[[^\]]*\]", " ", s).replace("Пока-пока!", "")
    return s.split()


B.clean_words = lambda: scen_words()


def finder(words):
    def F(needle, after=0.0):
        for w, t in words:
            if t >= after - 0.01 and B.norm(w) == B.norm(needle):
                return t
        raise KeyError(needle)
    return F


def font(size):
    return ImageFont.truetype(FONT, size)


def render_caption(path, words):
    """Заглавные, белые с обводкой; самое длинное слово фразы — цветом."""
    f = font(CAP_SIZE)
    up = [re.sub(r"[«»]", "", w.upper()) for w in words]
    clean = [re.sub(r"[^\wЁё-]", "", w) for w in up]
    key = max(range(len(clean)), key=lambda i: len(clean[i])) if max(len(c) for c in clean) >= 5 else -1
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], []
    for i, w in enumerate(up):
        if cur and d0.textlength(" ".join(up[j] for j in cur + [i]), font=f) > 940:
            lines.append(cur)
            cur = []
        cur.append(i)
    lines.append(cur)
    lh = int(CAP_SIZE * 1.15)
    hh = lh * len(lines) + 20
    im = Image.new("RGBA", (W, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, ln in enumerate(lines):
        tw = d.textlength(" ".join(up[j] for j in ln), font=f)
        x, y = (W - tw) / 2, 10 + li * lh
        for j in ln:
            d.text((x, y), up[j], font=f, fill=ACCENT if j == key else "white",
                   stroke_width=6, stroke_fill=(0, 0, 0, 230))
            x += d.textlength(up[j] + " ", font=f)
    im.save(path)
    top = CAP_CY - hh // 2
    assert top >= RULE_Y + 130, f"субтитр наезжает на плашку правила: {path}"
    assert SAFE_TOP <= top and top + hh <= SAFE_BOTTOM, path
    return top


def render_rule(path, num, title):
    f, fn = font(54), font(58)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tw = d0.textlength(title, font=f)
    h, r = 110, 42
    w = int(tw + 2 * r + 60 + 40)
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + w, 10 + h], radius=h // 2, fill=(17, 17, 20, 225))
    cx, cy = 10 + 20 + r, 10 + h // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    d.text((cx, cy + 2), str(num), font=fn, fill=(17, 17, 20), anchor="mm")
    d.text((cx + r + 30, cy + 2), title, font=f, fill="white", anchor="lm")
    im.save(path)
    assert w + 20 <= W - 40
    return (W - im.width) // 2


def render_hook(path):
    f = font(70)
    lines = [("7 ПРАВИЛ,", "white"), ("ЧТОБЫ ВСЕЛЕННАЯ", ACCENT), ("ПОМОГАЛА", "white")]
    lh = 84
    im = Image.new("RGBA", (W, lh * 3 + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (t, c) in enumerate(lines):
        d.text((W / 2, 15 + i * lh + lh / 2), t, font=f, fill=c, anchor="mm", stroke_width=7,
               stroke_fill=(0, 0, 0, 235))
    im.save(path)
    return im.height


def broll_filter(idx, start, dur, label):
    """Картинка 1024×1536 → cover 1080×1920 с наездом 1.0→1.08 и мягким появлением."""
    return (f"[{idx}:v]scale=1280:1920,setsar=1,fps=30,format=rgba,"
            f"scale=w='trunc(1280*(1+0.08*t/{dur:.2f})/2)*2':h='trunc(1920*(1+0.08*t/{dur:.2f})/2)*2':eval=frame,"
            f"crop=1080:1920:'(iw-1080)/2':'(ih-1920)/2',"
            f"fade=in:st=0:d=0.25:alpha=1,fade=out:st={dur - 0.25:.2f}:d=0.25:alpha=1,"
            f"setpts=PTS+{start:.3f}/TB[{label}]")


def main():
    os.makedirs(TMP, exist_ok=True)
    S.numfix()
    words, last = B.timed_words()
    F = finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", AUDIO]).decode())
    subs = S.chunk_words(words, min(total, last + 0.6))

    brolls, rules = [], []
    for num, title, w0, img, w1, dur in RULES:
        t0 = F(w0)
        tb = F(w1, t0 + 0.5)
        rules.append((num, title, t0, tb))
        brolls.append((img, tb, dur))
    img, w1, dur = FINAL
    brolls.append((img, F(w1), min(dur, total - F(w1))))
    for (a, ta, da), (b, tb, db) in zip(brolls, brolls[1:]):
        assert ta + da <= tb, f"картинки {a}/{b} перекрываются"

    # планы ведущей: смена крупности на каждом предложении
    starts, new = [0.0], False
    for w, t in words:
        if new and t - starts[-1] > 2.0:
            starts.append(t)
        new = bool(re.search(r"[.!?…]»?$", w))
    plan = [(s, starts[i + 1] if i + 1 < len(starts) else total, i % 2 == 1) for i, s in enumerate(starts)]

    cw, ch = int(W / PUNCH), int(H / PUNCH)
    cx = min(max(FACE[0] - cw // 2, 0), W - cw)
    cy = min(max(FACE[1] - int(ch * 0.40), 0), H - ch)
    inputs = ["-i", CLIP, "-i", AUDIO]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,split=2[med][c0]",
            f"[c0]crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}[close]"]
    close_on = "+".join(f"between(t,{s:.3f},{e - 0.001:.3f})" for s, e, z in plan if z) or "0"
    # пока висит плашка правила на ведущей — только средний план, чтобы плашка не легла на лицо
    calm = "*".join(f"not(between(t,{t0:.3f},{tb:.3f}))" for _, _, t0, tb in rules)
    close_on = f"({close_on})*{calm}"
    filt.append(f"[med][close]overlay=0:0:enable='{close_on}'[v0]")
    prev, n = "[v0]", 2

    for i, (img, t0, dur) in enumerate(brolls):
        inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", f"{IMG}/{img}.png"]
        filt.append(broll_filter(n, t0, dur, f"b{i}"))
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.3f},{t0 + dur:.3f})'[vb{i}]")
        prev, n = f"[vb{i}]", n + 1

    hook = f"{TMP}/hook.png"
    hh = render_hook(hook)
    inputs += ["-i", hook]
    t_hook_end = F("Сохрани")      # крючок стоит вместо субтитров первой фразы
    hy = CAP_CY - hh // 2
    filt.append(f"{prev}[{n}:v]overlay=0:{hy}:enable='between(t,0.1,{t_hook_end:.3f})'[vh]")
    assert SAFE_TOP <= hy and hy + hh <= SAFE_BOTTOM
    prev, n = "[vh]", n + 1

    for num, title, t0, tb in rules:
        p = f"{TMP}/rule{num}.png"
        x = render_rule(p, num, title)
        inputs += ["-i", p]
        end = tb + 4.6 if num != 7 else tb + 4.6
        filt.append(f"{prev}[{n}:v]overlay={x}:{RULE_Y}:enable='between(t,{t0:.3f},{end:.3f})'[vr{num}]")
        prev, n = f"[vr{num}]", n + 1

    for si, s in enumerate(subs):
        if s["t1"] <= t_hook_end + 0.01:
            continue
        p = f"{TMP}/s{si:03d}.png"
        top = render_caption(p, [w for w, _ in s["words"]])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{top}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[vs{si}]")
        prev, n = f"[vs{si}]", n + 1

    filt.append("[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    open(f"{TMP}/graph.txt", "w").write(";\n".join(filt))
    json.dump({"rules": rules, "brolls": brolls, "subs": [(" ".join(w for w, _ in s["words"]), s["t0"], s["t1"]) for s in subs]},
              open(f"{TMP}/plan.json", "w"), ensure_ascii=False, indent=1)
    if os.environ.get("CHECK"):
        print("check ok", len(subs), "фраз,", len(brolls), "картинок")
        return
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{TMP}/graph.txt",
                    "-map", prev, "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT],
                   check=True)
    print(OUT, len(subs), "фраз,", len(brolls), "картинок")


if __name__ == "__main__":
    main()
