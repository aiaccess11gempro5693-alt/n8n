"""Reels №22 «Вы правы» — сценка из вечернего ток-шоу (ведущий + гость), без графики.

Монтаж как у живого ток-шоу: общий план студии → ведущий спрашивает → гость отвечает → ведущий возражает →
пауза → гость «Вы правы.» (наезд) → ведущий хохочет. Два клипа HeyGen (каждый со своей дорожкой, в которой
реплики собеседника — тишина), склейки по репликам. Субтитры — крупные заглавные Montserrat с голубыми
ключевыми словами, в безопасной зоне 250–1500. Тихий джаз из библиотеки HeyGen.

python3 render/landing/build_ig22.py   →  render/landing/ig22-9x16.mp4
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import sfx as SFX

ROOT = B.ROOT
B.AUDIO = f"{ROOT}/scratch/ig22/dialog.mp3"
B.WHISPER = f"{ROOT}/scratch/ig22-whisper.json"
B.TMP = f"{ROOT}/render/landing/.ig22"
OUT = f"{ROOT}/render/landing/ig22-9x16.mp4"
HOST, GUEST = f"{ROOT}/scratch/ig22/host.mp4", f"{ROOT}/scratch/ig22/guest.mp4"
WIDE = f"{ROOT}/scratch/img/ig22_wide.png"
MUSIC = f"{ROOT}/scratch/music/ig22-music.mp3"
W, H = B.W, B.H
SPOKEN = ("Слушай, а в чём вообще твой главный секрет успеха? Я никогда не спорю с людьми, которые не хотят "
          "меня слушать. Просто говорю: «Вы правы». Но это же никак не связано с успехом! Вы правы. Ха-ха! Ну ты даёшь!")
ACCENT = {"секрет", "успеха", "не", "спорю", "вы", "правы", "связано", "успехом", "даёшь"}
BLUE = (79, 195, 247)
FONT = f"{ROOT}/render/fonts/Montserrat-ExtraBold.ttf"


def render_caps(path, text, size=78, maxw=940):
    f = ImageFont.truetype(FONT, size)
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    words, lines, cur = text.upper().split(), [], []
    for w in words:
        if cur and d.textlength(" ".join(cur + [w]), font=f) > maxw:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    lh = size * 1.14
    y = 150 - lh * len(lines) / 2
    sp = d.textlength(" ", font=f)
    for ln in lines:
        x = (W - d.textlength(" ".join(ln), font=f)) / 2
        for w in ln:
            col = BLUE if B.norm(w) in ACCENT else (255, 255, 255)
            d.text((x, y + lh / 2), w, font=f, fill=col, anchor="lm", stroke_width=6, stroke_fill=(0, 0, 0, 240))
            x += d.textlength(w, font=f) + sp
        y += lh
    im.save(path)
    top = B.CY - 150 + 150 - lh * len(lines) / 2
    assert 250 <= top and top + lh * len(lines) <= 1500, text


def main():
    os.makedirs(B.TMP, exist_ok=True)
    plan = json.load(open(f"{ROOT}/scratch/ig22/plan.json"))
    t = {k: (a, b) for _, k, a, b in plan}
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    subs = B.chunks(words, min(total, last + 0.5))
    # смех whisper не распознаёт — финальная реплика ведущего встаёт ровно на начало его дорожки
    k = next(i for i, s in enumerate(subs) if s["text"].startswith("Ха-ха"))
    subs = subs[:k] + [{"text": "Ха-ха! Ну ты даёшь!", "t0": t["h3"][0], "t1": t["h3"][1] + 0.3}]
    subs[k - 1]["t1"] = t["h3"][0]
    # склейки: кто в кадре (переход чуть раньше начала реплики)
    cut_g1, cut_h2, cut_g2, cut_h3 = t["g1"][0] - 0.12, t["h2"][0] - 0.12, t["g2"][0] - 0.55, t["h3"][0] - 0.1
    wide_end = 1.5
    guest_win = [(cut_g1, cut_h2), (cut_g2, cut_h3)]
    punch = (cut_g2, cut_h3)
    gexpr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in guest_win)
    json.dump({"subs": subs, "guest": guest_win, "wide_end": wide_end}, open(f"{B.TMP}/plan.json", "w"),
              ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [], audio, f"{B.TMP}/sfx", bed_gain=0.10, total=total, bed_fn=SFX.music_bed(MUSIC))

    def cam(idx, label, z):
        return (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
                f"tpad=stop_duration=2:stop_mode=clone,"
                f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,"
                f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3',format=yuv420p[{label}]")
    zh = f"(1+0.04*t/{total:.2f})"
    zg = f"(1+0.04*t/{total:.2f}+0.14*between(t,{punch[0]:.3f},{punch[1]:.3f})*min(1,(t-{punch[0]:.3f})/0.25))"
    inputs = ["-i", HOST, "-i", GUEST, "-i", audio, "-loop", "1", "-t", f"{wide_end + 0.5:.2f}", "-i", WIDE]
    filt = [cam(0, "h", zh), cam(1, "g", zg),
            "[h][g]overlay=0:0:enable='" + gexpr + "'[v1]",
            f"[3:v]scale=1280:1920,setsar=1,fps=30,format=rgba,"
            f"scale=w='trunc(1280*(1+0.06*t/{wide_end:.2f})/2)*2':h='trunc(1920*(1+0.06*t/{wide_end:.2f})/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/2'[wd]",
            f"[v1][wd]overlay=0:0:enable='lt(t,{wide_end:.3f})'[v2]"]
    prev, n = "[v2]", 4
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        render_caps(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 150}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "2:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)
    print(OUT, f"{total:.1f} c,", len(subs), "субтитров; гость:", [(round(a, 2), round(b, 2)) for a, b in guest_win])


if __name__ == "__main__":
    main()
