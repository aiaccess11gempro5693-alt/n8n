"""Reels №19 «Самая важная часть стула» — ведущий на подкасте + белые субтитры + кинокадры.

По референсу instagram.com/reel/Db_Ec50w0Ip (притча про стул и болты). Движок build_ig16
(build_ig6/ig9): крючок-заголовок, белые субтитры, четыре кинокадра gpt-image-2 (меловой стул на доске,
болт крупно, стул разваливается, близкие за столом), тихое фортепиано из библиотеки HeyGen.
Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig19.py   →  render/landing/ig19-9x16.mp4
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
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig19/trim2.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig19-whisper-final2.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig19/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig19-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig19"
IMG = f"{ROOT}/scratch/img"
MUSIC = f"{ROOT}/scratch/music/ig19-music.mp3"
MUSIC_GAIN = 0.10

SPOKEN = ("Однажды учительница спросила детей одну простую вещь — и никто не ответил правильно. На доске был нарисован стул. "
          "«Назовите самую важную часть этого стула». Дети писали: ножки, сиденье, спинка. Учительница покачала головой. "
          "«Самая важная часть — та, которую вы не видите. Маленькие винтики, которые держат всю конструкцию. "
          "Выкрути их — и стул развалится». Жизнь устроена так же. Мы смотрим на то, что видно: работа, дом, доход, "
          "достижения. А держат всё это винтики, которых никто не замечает. Здоровье. Сон. Привычки. Близкие, которые "
          "рядом, когда никто не смотрит. Маленькие решения, которые ты принимаешь каждый день. Не жди… пока твой стул "
          "начнёт разваливаться. Кстати, меня тоже не видно по-настоящему… меня сделала нейросеть. А вот винтики — "
          "настоящие. Напиши в комментариях: какой твой главный винтик?")
HOOK = "ГДЕ САМАЯ ВАЖНАЯ ЧАСТЬ_СТУЛА?"
# (картинка, слово-триггер, искать после слова, длительность)
BROLLS = [("ig19_b1", "На", None, 3.6), ("ig19_b2", "видите.", None, 3.4),
          ("ig19_b3", "Выкрути", None, 3.2), ("ig19_b4", "Близкие,", None, 3.6)]


# «Болты» Gemini слышит как «бОлты» (норма — болтЫ): слово вырезано из звука и клипа одной склейкой
# от середины паузы до середины паузы; склейку закрывает кадр с болтом (ig19_b2).
CUT = (19.87, 20.87)


def cut_sources():
    a0, a1 = CUT
    d = a1 - a0
    audio, clip, wh = f"{B.TMP}/voice-cut.wav", f"{B.TMP}/host-cut.mp4", f"{B.TMP}/whisper-cut.json"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af",
                    f"aselect='not(between(t,{a0},{a1}))',asetpts=N/SR/TB", "-ar", "48000", audio], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.CLIP, "-vf",
                    f"select='not(between(t,{a0},{a1}))',setpts=N/FRAME_RATE/TB", "-af",
                    f"aselect='not(between(t,{a0},{a1}))',asetpts=N/SR/TB", "-c:v", "libx264", "-crf", "16",
                    "-preset", "fast", clip], check=True)
    w = json.load(open(B.WHISPER))
    words = []
    for x in w["words"]:
        if a0 <= x["start"] < a1:
            continue
        if x["start"] >= a1:
            x = dict(x, start=x["start"] - d, end=x["end"] - d)
        words.append(x)
    w["words"] = words
    json.dump(w, open(wh, "w"), ensure_ascii=False)
    B.AUDIO, B.CLIP, B.WHISPER = audio, clip, wh


def main():
    os.makedirs(B.TMP, exist_ok=True)
    cut_sources()
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    subs = N.chunks_with_hook(words, min(total, last + 0.6))
    subs[0]["text"] = HOOK       # первая фраза длинная — заголовок её суть
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
