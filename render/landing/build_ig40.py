"""Reels №40 «Не проси денег — проси эти 5 вещей» (по референсу instagram.com/reel/DeLyXuXt8ag).

Как в референсе: ведущий в кресле в тёмной студии, склейки крупный план ↔ средний на каждом предложении,
субтитры — по одному слову заглавными белым посередине кадра; названия пяти пунктов — жёлтым и крупнее.
Тихая вдохновляющая музыка.

python3 render/landing/build_ig40.py  →  render/landing/ig40-9x16.mp4
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import sfx as SFX

ROOT = B.ROOT
W, H = 1080, 1920
TMP = f"{ROOT}/render/landing/.ig40"
AUDIO = f"{ROOT}/scratch/ig40/voice-trim.mp3"
WHISPER = f"{ROOT}/scratch/ig40-whisper-trim.json"
CLIP = f"{ROOT}/scratch/ig40/host.mp4"
MUSIC = f"{ROOT}/scratch/music/ig40-music.mp3"
OUT = f"{ROOT}/render/landing/ig40-9x16.mp4"
SPOKEN = ("Не проси у Бога денег. Проси вот эти пять вещей. Потому что деньги — это результат. А эти пять — то, "
          "что их приносит. Первое — видение. Не сухая цель, а большая картина, ради которой хочется вставать по "
          "утрам. Второе — план. Даже Ною дали не просто идею ковчега, а точные размеры. Тебе нужны не деньги — "
          "тебе нужна дорожная карта. Третье — мудрость. Соломон мог попросить богатства. Он попросил мудрости — и "
          "богатство пришло следом. Четвёртое — ясность. Каша в голове убивает любое движение. Проси ясный ум — "
          "чтобы каждый следующий шаг был понятен. Пятое — правильное окружение. Семя растёт там, где хорошая "
          "почва. Проси, чтобы тебя поставили туда, где ты раскроешься. Деньги — это следствие. Перестань гоняться "
          "за купюрами. Стань человеком, который готов их принять. И да — меня сделала нейросеть. А эти пять вещей "
          "— настоящие. Сохрани, чтобы не забыть.")
KEY = {"видение", "план", "мудрость", "ясность", "окружение", "денег", "пять", "нейросеть", "следствие"}
YELLOW = (255, 214, 10)
FACE_Y = 0.29        # доля высоты кадра, где лицо — центр крупного плана
CLOSE_Z = 1.45
CUT_EVERY = 1       # сколько предложений подряд держится один план
SUB_Y = 1190         # центр слова — на груди, ниже лица


def norm(w):
    return re.sub(r"[^\wё]", "", w.lower())


def render_word(path, word):
    key = any(norm(x) in KEY for x in word.split())
    size = 96 if key else 78
    f = ImageFont.truetype(B.FONT, size)
    txt = re.sub(r"[«»]", "", word).upper()
    im = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    while d.textlength(txt, font=f) > W - 120:
        size -= 4
        f = ImageFont.truetype(B.FONT, size)
    d.text((W / 2, 100), txt, font=f, fill=YELLOW if key else (255, 255, 255), anchor="mm",
           stroke_width=5, stroke_fill=(0, 0, 0, 235))
    im.save(path)


def main():
    os.makedirs(TMP, exist_ok=True)
    B.WHISPER = WHISPER
    words_all = SPOKEN.split()
    B.clean_words = lambda: words_all
    words, last = B.timed_words()
    voice_len = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                               "-of", "csv=p=0", AUDIO]).decode())
    total = voice_len + 0.7
    shown = [(w, t) for w, t in words if w not in ("—", "–")]
    # группы: слово показывается не короче ~0.3 с — слишком быстрые слова объединяются (до 3 в группе)
    groups, i = [], 0
    while i < len(shown):
        g = [shown[i]]
        while (i + len(g) < len(shown) and len(g) < 3 and not re.search(r"[.!?]$", g[-1][0])
               and shown[i + len(g)][1] - g[0][1] < 0.32):
            g.append(shown[i + len(g)])
        groups.append(g)
        i += len(g)
    subs = []
    for j, g in enumerate(groups):
        t = g[0][1]
        nxt = groups[j + 1][0][1] if j + 1 < len(groups) else total - 0.3
        end = min(nxt, t + (1.3 if re.search(r"[.!?]$", g[-1][0]) else 1.0))
        subs.append({"text": " ".join(w for w, _ in g), "t0": t, "t1": end})
    short = [s for s in subs if s["t1"] - s["t0"] < 0.2]
    print("коротких групп:", len(short), short[:5])
    # склейки: каждое предложение — свой план, чередуем средний / крупный
    starts = [shown[0][1]] + [shown[i + 1][1] for i, (w, _) in enumerate(shown[:-1]) if re.search(r"[.!?]$", w)]
    bounds = [0.0] + starts[1:] + [total]
    close = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1) if (i // CUT_EVERY) % 2 == 1]
    json.dump({"subs": subs, "close": close}, open(f"{TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    voice = f"{TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", AUDIO, "-af", "apad=pad_dur=0.7", "-ar", "48000",
                    "-ac", "1", voice], check=True)
    audio = f"{TMP}/mix.wav"
    SFX.mix(voice, [], audio, f"{TMP}/sfx", bed_gain=0.11, total=total, bed_fn=SFX.music_bed(MUSIC))

    cz = "+".join(f"between(t,{a:.3f},{b - 0.001:.3f})" for a, b in close) or "0"
    z = f"(1+0.04*t/{total:.2f}+{CLOSE_Z - 1:.2f}*({cz}))"
    inputs = ["-i", CLIP, "-i", audio]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
            f"tpad=stop_duration=2:stop_mode=clone,"
            f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})*0.5':'(ih-{H})*{FACE_Y}',format=yuv420p[v0]"]
    prev, k = "[v0]", 2
    for i, s in enumerate(subs):
        p = f"{TMP}/w{i:03d}.png"
        render_word(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{k}:v]overlay=0:{SUB_Y - 100}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, k = f"[s{i}]", k + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)
    print(OUT, f"{total:.1f} c,", len(subs), "слов,", len(close), "крупных планов")


if __name__ == "__main__":
    main()
