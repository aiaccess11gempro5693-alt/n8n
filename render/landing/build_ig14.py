"""Reels №14 «5 самых известных законов в мире» — спикер в кресле на сцене, красный занавес.

Как в референсе instagram.com/reel/DdwxyIkxdhh: заголовок-крючок на общем плане → на каждом законе
склейка на крупный план и плашка «ЗАКОН …» с номером, внутри закона — обратно на общий план; субтитры —
белые плашки с чёрным текстом, одно ключевое слово фиолетовым. Бонус «шестой закон» — поворот
«меня сделала нейросеть». Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig14.py   →  render/landing/ig14-9x16.mp4
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import sfx as SFX

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig14/trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig14-whisper.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig14/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig14-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig14"
MUSIC = f"{ROOT}/scratch/music/ig14-music.mp3"
MUSIC_GAIN = 0.09
W, H = B.W, B.H
FACE = (500, 470)            # центр лица в кадре 1080×1920 (по фото ведущей)
ZOOM = 1.55
F_TXT = f"{ROOT}/render/fonts/Montserrat-ExtraBold.ttf"
F_SUB = f"{ROOT}/render/fonts/Montserrat-Bold.ttf"
VIOLET, WHITE, INK, RED = (124, 70, 230), (255, 255, 255), (20, 20, 24), (196, 26, 46)
SUB_Y = 1290                 # центр плашки субтитра
CHIP_Y = 1110                # центр плашки закона

SPOKEN = ("Пять самых известных законов в мире. Слушай и запоминай. Закон Мёрфи. Если что-то может пойти "
          "не так — оно пойдёт не так. И чем сильнее ты этого боишься, тем вероятнее. Закон Кидлина. Если ты "
          "чётко записал задачу на бумаге — ты уже решил её наполовину. Закон Гилберта. Найти лучший способ "
          "сделать работу — твоя ответственность. Не начальника, не коллег — твоя. Закон Уилсона. Ставь знания "
          "и развитие на первое место — и деньги начнут приходить легче. Закон Фолкленда. Если решение можно "
          "не принимать прямо сейчас — не принимай его. И бонус, шестой закон… этого спикера не существует. "
          "Меня сделала нейросеть. Какой закон работает в твоей жизни? Пиши в комментариях.")
LAWS = [("Мёрфи", "1"), ("Кидлина", "2"), ("Гилберта", "3"), ("Уилсона", "4"), ("Фолкленда", "5")]
STOP = {"если", "что", "это", "этого", "твоя", "ты", "тем", "чем", "можно", "прямо", "его", "меня", "какой",
        "пиши", "закон", "уже", "сейчас", "начнут"}


def sub_png(path, text):
    """Белая плашка, чёрный текст, самое длинное содержательное слово — фиолетовым."""
    f = ImageFont.truetype(F_SUB, 50)
    words = text.split()
    key = max((w for w in words if B.norm(w) not in STOP), key=lambda w: len(B.norm(w)), default=None)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], []
    for w in words:
        if cur and d0.textlength(" ".join(cur + [w]), font=f) > 860:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    assert len(lines) <= 2, text
    lh, padx, pady = 66, 34, 18
    tw = max(d0.textlength(" ".join(l), font=f) for l in lines)
    bw, bh = tw + 2 * padx, lh * len(lines) + 2 * pady
    im = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
    x0, y0 = (W - bw) / 2, 120 - bh / 2
    ImageDraw.Draw(sh).rounded_rectangle([x0, y0 + 6, x0 + bw, y0 + bh + 6], 22, fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 22, fill=WHITE)
    for i, ln in enumerate(lines):
        x = (W - d0.textlength(" ".join(ln), font=f)) / 2
        y = y0 + pady + lh * i + lh / 2
        for w in ln:
            d.text((x, y), w, font=f, fill=VIOLET if w == key else INK, anchor="lm")
            x += d0.textlength(w + " ", font=f)
        key = None if key in ln else key
    im.save(path)
    assert 250 <= SUB_Y - 120 + y0 and SUB_Y - 120 + y0 + bh <= 1500


def chip_png(path, num, name):
    """Плашка закона: красный кружок с номером + «ЗАКОН ИМЯ» белым на тёмной подложке."""
    fn, ft = ImageFont.truetype(F_TXT, 46), ImageFont.truetype(F_TXT, 54)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    txt = name.upper()
    tw = d0.textlength(txt, font=ft)
    bw, bh = tw + 150, 104
    im = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
    x0, y0 = (W - bw) / 2, 28
    sh = Image.new("RGBA", (W, 160), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, y0 + 6, x0 + bw, y0 + bh + 6], 52, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 52, fill=(18, 16, 20, 235))
    cx, cy = x0 + 52, y0 + bh / 2
    d.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=RED)
    d.text((cx, cy - 2), num, font=fn, fill=WHITE, anchor="mm")
    d.text((x0 + 108, cy), txt, font=ft, fill=WHITE, anchor="lm")
    im.save(path)


def hook_png(path):
    f1, f2 = ImageFont.truetype(F_TXT, 150), ImageFont.truetype(F_TXT, 66)
    im = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    for d_, fill in ((ds, (0, 0, 0, 220)),):
        d_.text((W / 2, 110 + 6), "5", font=f1, fill=fill, anchor="mm")
        for i, t in enumerate(("САМЫХ ИЗВЕСТНЫХ", "ЗАКОНОВ В МИРЕ")):
            d_.text((W / 2, 245 + i * 80 + 6), t, font=f2, fill=fill, anchor="mm")
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 110), "5", font=f1, fill=RED, anchor="mm", stroke_width=4, stroke_fill=WHITE)
    for i, t in enumerate(("САМЫХ ИЗВЕСТНЫХ", "ЗАКОНОВ В МИРЕ")):
        assert d.textlength(t, font=f2) <= 1000
        d.text((W / 2, 245 + i * 80), t, font=f2, fill=WHITE, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 230))
    im.save(path)


def main():
    os.makedirs(B.TMP, exist_ok=True)
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    t_first = F("Закон") - 0.1
    laws, after = [], t_first
    for name, num in LAWS:
        t = F(name, after) - 0.55          # «Закон» звучит на ~0.5 с раньше имени
        laws.append((t, name, num))
        after = t + 1
    t_bonus = F("бонус", after) - 0.3
    t_cta = F("Какой", t_bonus) - 0.1
    bounds = [t for t, _, _ in laws] + [t_bonus, t_cta, total]
    # кадр: общий план — крючок; на каждом законе — крупный 0..~2.5 с, затем общий; бонус — крупный; призыв — общий
    close = [(t, min(t + 3.0, bounds[i + 1] - 0.05)) for i, t in enumerate(bounds[:5])]
    close.append((t_bonus, t_cta))
    subs = [s for s in B.chunks(words, min(total, last + 0.6)) if s["t1"] > t_first + 0.05]
    subs[0]["t0"] = max(subs[0]["t0"], t_first)
    # «Закон Мёрфи.» уже написано на плашке закона — субтитр не дублирует
    subs = [s for s in subs if not re.fullmatch(r"Закон \S+\.?", s["text"])]
    json.dump({"laws": laws, "bonus": t_bonus, "cta": t_cta, "close": close, "subs": subs},
              open(f"{B.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [(t + 0.05, "pop", 0.3) for t, _, _ in laws] + [(t_bonus + 0.05, "pop", 0.3)], audio,
            f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    cw, ch = int(W / ZOOM), int(H / ZOOM)
    cx = min(max(FACE[0] - cw // 2, 0), W - cw)
    cy = min(max(FACE[1] - int(ch * 0.40), 0), H - ch)
    close_on = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in close)
    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,split=2[med][c0]",
            f"[c0]crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}[close]",
            f"[med][close]overlay=0:0:enable='{close_on}'[v0]"]
    prev, n = "[v0]", 2
    hp = f"{B.TMP}/hook.png"
    hook_png(hp)
    inputs += ["-i", hp]
    filt.append(f"{prev}[{n}:v]overlay=0:{1100 - 210}:enable='lt(t,{t_first:.3f})'[vh]")
    prev, n = "[vh]", n + 1
    chips = [(t, num, f"Закон {name}", bounds[i + 1]) for i, (t, name, num) in enumerate(laws)]
    chips.append((t_bonus, "6", "Бонус-закон", t_cta))
    for i, (t0, num, name, t1) in enumerate(chips):
        p = f"{B.TMP}/chip{i}.png"
        chip_png(p, num, name)
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{CHIP_Y - 80}:enable='between(t,{t0:.3f},{t1 - 0.05:.3f})'[c{i}]")
        prev, n = f"[c{i}]", n + 1
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        sub_png(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{SUB_Y - 120}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, "законы:", [round(t, 2) for t, _, _ in laws], "субтитров:", len(subs))


if __name__ == "__main__":
    main()
