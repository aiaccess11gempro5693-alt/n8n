"""Reels №16 «Не суди по обёртке» — мужчина на подкасте + белые субтитры + кинокадры.

Как в референсе instagram.com/reel/DdMXaMqMaCn (тот же автор, что у №9): ведущий на диване
с микрофоном, первая фраза — крупный заголовок заглавными, дальше белые субтитры (движок
build_ig6/ig9). Поверх — четыре кинокадра gpt-image-2 на контрасте «обёртка / характер»
(холодный в костюме, татуированный помогает бабушке, тихий поступок ночью, байкер с котёнком),
тихая акустика из библиотеки HeyGen. Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig16.py   →  render/landing/ig16-9x16.mp4
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import sfx as SFX

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig16/trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig16-whisper-final.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig16/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig16-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig16"
IMG = f"{ROOT}/scratch/img"
MUSIC = f"{ROOT}/scratch/music/ig16-music.mp3"
MUSIC_GAIN = 0.10

SPOKEN = ("Порой самые добрые люди, которых ты встретишь, курят, ругаются и выглядят так, что их хочется обойти "
          "стороной. А самые холодные — в идеальном костюме, с безупречной репутацией и правильными словами. "
          "Поэтому я перестал судить людей по обёртке. Настоящий характер виден в том, как человек относится к тебе, "
          "когда ему с этого ничего не будет… и рядом никого нет. В его преданности. В тихих поступках, за которые "
          "никто не аплодирует. Так что прежде чем судить — задай вопросы получше. Как он любит? Как поступает, "
          "когда это ему чего-то стоит? За самым безупречным образом может прятаться самое холодное сердце. А за "
          "грубой внешностью — самое тёплое. Кстати, моё лицо — тоже обёртка… меня сделала нейросеть. А вот слова — "
          "настоящие. Суди людей по характеру. И напиши в комментариях: кто в твоей жизни оказался лучше, чем "
          "казался? Пока!")
HOOK = "САМЫЕ ДОБРЫЕ ЛЮДИ КУРЯТ И РУГАЮТСЯ"
# (картинка, слово-триггер, искать после слова, длительность)
BROLLS = [("ig16_b1", "А", "стороной.", 4.2), ("ig16_b2", "Настоящий", None, 4.2),
          ("ig16_b3", "В", "нет.", 4.2), ("ig16_b4", "А", "сердце.", 3.6)]


def main():
    os.makedirs(B.TMP, exist_ok=True)
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    subs = N.chunks_with_hook(words, min(total, last + 0.6))
    subs[0]["text"] = HOOK       # первая фраза длинная — заголовок её суть, как в референсе
    brolls = []
    for img, w, after, dur in BROLLS:
        a = F(after) if after else 0.0
        brolls.append((img, F(w, a) - 0.1, dur))
    for (a, ta, da), (b, tb, db) in zip(brolls, brolls[1:]):
        assert ta + da <= tb, f"картинки {a}/{b} перекрываются"
    assert brolls[0][1] >= subs[0]["t1"] - 0.15, "кадр не должен закрывать заголовок"
    json.dump({"subs": subs, "brolls": brolls}, open(f"{B.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [], audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={B.W}:{B.H}:force_original_aspect_ratio=increase,crop={B.W}:{B.H},setsar=1,fps=30,"
            f"scale=w='trunc({B.W}*(1+0.05*t/{total:.2f})/2)*2':h='trunc({B.H}*(1+0.05*t/{total:.2f})/2)*2':eval=frame,"
            f"crop={B.W}:{B.H}:'(iw-{B.W})/2':'(ih-{B.H})/3',format=yuv420p[v0]"]
    prev, n = "[v0]", 2
    for i, (img, t0, dur) in enumerate(brolls):
        inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", f"{IMG}/{img}.png"]
        filt.append(N.broll_filter(n, t0, dur, f"b{i}"))
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass[vb{i}]")
        prev, n = f"[vb{i}]", n + 1
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
    print(B.OUT, len(subs), "субтитров, кадры:", [(b, round(t, 1)) for b, t, _ in brolls])


if __name__ == "__main__":
    main()
