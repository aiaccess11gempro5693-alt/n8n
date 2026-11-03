"""Reels №12 «Проверь свою дикцию» — ведущая на подкасте + бегущий текст для чтения вслух.

Как в референсе instagram.com/reel/DcD2bptIv_Z: вступление ведущей → ведущая размывается, на тёмной
полосе медленно ползёт вверх тяжёлый канцелярский текст (зритель читает вслух) → ведущая снова в
кадре: «на каком слове споткнулся?» и поворот «меня сделала нейросеть». Всё в безопасной зоне 250–1500.

Дорожка для HeyGen собрана заранее: вступление (0–INTRO) + тишина SCROLL с + финал —
`scratch/ig12/track.mp3`; тайминги слов — из whisper исходного дубля со сдвигом финала.

python3 render/landing/build_ig12.py   →  render/landing/ig12-9x16.mp4
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import sfx as SFX

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig12/track.mp3")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig12/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig12-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig12"
WHISPER_TAKE = f"{ROOT}/scratch/ig12-whisper-b.json"
MUSIC = f"{ROOT}/scratch/music/ig12-music.mp3"
MUSIC_GAIN = 0.10
W, H = B.W, B.H

INTRO_END, OUTRO_FROM, SCROLL = 9.2, 10.2, 32.0      # как резали дорожку
SHIFT = INTRO_END + SCROLL - OUTRO_FROM
SPOKEN = ("Давай проверим твою дикцию! Прочитай вслух текст, который сейчас появится на экране. И не сбейся! "
          "Ну что, на каком слове споткнулся? Пиши в комментариях. А я бы прочитала без единой запинки… "
          "потому что меня сделала нейросеть.")
READ_TEXT = (
    "Систематизация разнонаправленных коммуникационных процессов предопределяет необходимость "
    "последовательной синхронизации артикуляционных механизмов. При возрастании интенсивности "
    "словоупотребления и непредсказуемости интонационных переходов принципиально важна своевременная "
    "корректировка произносительных навыков, обеспечивающих безукоризненную разборчивость высказывания. "
    "Подобная методология нивелирует фонетические искажения, способствуя кристаллизации "
    "индивидуального речевого стиля. Внедрение многоступенчатых дыхательных упражнений позволяет "
    "трансформировать хаотичные звукосочетания в структурированные интонационные конструкции, "
    "увеличивая выразительность и убедительность выступления перед многочисленной аудиторией "
    "в непредсказуемых обстоятельствах.")

F_READ = f"{ROOT}/render/fonts/PlayfairDisplay-SemiBold.ttf"
F_LABEL = f"{ROOT}/render/fonts/Montserrat-ExtraBold.ttf"
BAND_Y0, BAND_Y1 = 560, 1420             # тёмная полоса (внутри зоны 250–1500)
WIN_Y0, WIN_Y1 = 660, 1400                # окно бегущего текста
MX = 80
READ_SIZE, READ_LH = 48, 1.55
CREAM, RED = (242, 234, 222), (226, 60, 60)


def make_whisper():
    """Слова дубля → тайминги дорожки (финал сдвинут на длину бегущего текста)."""
    ws = json.load(open(WHISPER_TAKE))["words"]
    out = []
    for w in ws:
        if w["start"] < INTRO_END:
            out.append(dict(w))
        elif w["start"] >= OUTRO_FROM and w["word"].lower() != "пока":
            out.append({**w, "start": w["start"] + SHIFT, "end": w["end"] + SHIFT})
    p = f"{B.TMP}/whisper-track.json"
    json.dump({"words": out}, open(p, "w"), ensure_ascii=False)
    return p


def read_png(path):
    f = ImageFont.truetype(F_READ, READ_SIZE)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], ""
    for w in READ_TEXT.upper().split():
        c = (cur + " " + w).strip()
        if d0.textlength(c, font=f) > W - 2 * MX and cur:
            lines.append(cur)
            cur = w
        else:
            cur = c
    lines.append(cur)
    lh = int(READ_SIZE * READ_LH)
    win = WIN_Y1 - WIN_Y0
    hgt = 40 + lh * len(lines) + win            # снизу запас на высоту окна — текст уходит целиком
    im = Image.new("RGBA", (W - 2 * MX, hgt), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text((0, 40 + i * lh), ln, font=f, fill=CREAM)
    im.save(path)
    return hgt, 40 + lh * len(lines), len(lines)


def band_png(path):
    im = Image.new("RGBA", (W, BAND_Y1 - BAND_Y0), (12, 10, 12, 225))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_LABEL, 30)
    d.text((MX, 48), "ЧИТАЙ ВСЛУХ", font=f, fill=RED, anchor="lm")
    d.line([(MX + d.textlength("ЧИТАЙ ВСЛУХ", font=f) + 24, 48), (W - MX, 48)], fill=(90, 84, 84), width=2)
    im.save(path)


def main():
    os.makedirs(B.TMP, exist_ok=True)
    B.WHISPER = make_whisper()
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    k = next(i for i, (w, _) in enumerate(words) if w.endswith(("!", ".", "?"))) + 1
    rest = B.chunks(words[k:], min(total, last + 0.6))
    rest[0]["t0"] = words[k][1]
    subs = [{"text": " ".join(w for w, _ in words[:k]).rstrip("!.").upper(), "t0": 0.0, "t1": rest[0]["t0"]}] + rest
    s0, s1 = INTRO_END - 0.3, INTRO_END + SCROLL - 0.2       # размытие + полоса
    for s in subs:                                            # во время чтения субтитров нет
        if s["t0"] < s0:
            s["t1"] = min(s["t1"], s0)
    subs = [s for s in subs if s["t0"] < s0 or s["t0"] >= s1]
    json.dump({"subs": subs, "scroll": [s0, s1]}, open(f"{B.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    rp, bp = f"{B.TMP}/read.png", f"{B.TMP}/band.png"
    hgt, text_h, nlines = read_png(rp)
    band_png(bp)
    win = WIN_Y1 - WIN_Y0
    m0, m1 = s0 + 1.0, s1 - 0.6                               # текст движется
    dist = text_h - 120                                        # последняя строка доходит до верха окна
    speed = dist / (m1 - m0)
    print(f"{nlines} строк, скорость {speed:.0f} px/с")

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [], audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    dur = s1 - s0
    inputs = ["-i", B.CLIP, "-i", audio, "-loop", "1", "-t", f"{dur:.2f}", "-i", bp,
              "-loop", "1", "-t", f"{dur:.2f}", "-i", rp]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
            f"scale=w='trunc({W}*(1+0.04*t/{total:.2f})/2)*2':h='trunc({H}*(1+0.04*t/{total:.2f})/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3',format=yuv420p,split[v0][vb]",
            f"[vb]gblur=sigma=24,eq=brightness=-0.04:saturation=0.9,format=rgba,"
            f"trim=start={s0:.3f}:end={s1:.3f},setpts=PTS-STARTPTS,"
            f"fade=in:st=0:d=0.5:alpha=1,fade=out:st={dur - 0.5:.2f}:d=0.5:alpha=1,setpts=PTS+{s0:.3f}/TB[blur]",
            f"[v0][blur]overlay=0:0:eof_action=pass[vbl]",
            f"[2:v]format=rgba,fade=in:st=0.3:d=0.4:alpha=1,fade=out:st={dur - 0.6:.2f}:d=0.4:alpha=1,"
            f"setpts=PTS+{s0:.3f}/TB[band]",
            f"[vbl][band]overlay=0:{BAND_Y0}:eof_action=pass[vband]",
            f"[3:v]format=rgba,crop={W - 2 * MX}:{win}:0:'min({hgt - win},max(0,(t-{m0 - s0:.3f})*{speed:.3f}))',"
            f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*min(1,min(Y,H-Y)/60)',"
            f"fade=in:st=0.5:d=0.4:alpha=1,fade=out:st={dur - 0.6:.2f}:d=0.4:alpha=1,"
            f"setpts=PTS+{s0:.3f}/TB[txt]",
            f"[vband][txt]overlay={MX}:{WIN_Y0}:eof_action=pass[vt]"]
    prev, n = "[vt]", 4
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        N.render_any(p, s["text"])
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
