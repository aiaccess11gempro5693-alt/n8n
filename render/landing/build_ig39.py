"""Reels №39 «Я непобедим» (по референсу instagram.com/reel/Dd3hsXwOXuw).

Как в референсе: 2,4 с вступления — женщина на скале у моря и надпись-крючок на белых плашках «Вот такой настрой
должен быть у тебя всю жизнь:», жёсткая склейка на пожилого ведущего в тёмной студии подкаста, белые субтитры на
груди; «непобедим» — жёлтым, наезды на главных фразах, тихое фортепиано со струнными.

python3 render/landing/build_ig39.py  →  render/landing/ig39-9x16.mp4
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import build_ig25 as P
import sfx as SFX

ROOT = B.ROOT
W, H = 1080, 1920
INTRO = 2.4
N_ = "39"
TMP = f"{ROOT}/render/landing/.ig39"
AUDIO = f"{ROOT}/scratch/ig39/voice-trim.mp3"
WHISPER = f"{ROOT}/scratch/ig39-whisper-trim.json"
CLIP = f"{ROOT}/scratch/ig39/host.mp4"
SEA = f"{ROOT}/scratch/img/ig39_sea.png"
MUSIC = f"{ROOT}/scratch/music/ig39-music.mp3"
OUT = f"{ROOT}/render/landing/ig39-9x16.mp4"
SPOKEN = ("Я непобедим. Меня нельзя сломать. Это невозможно. Ты можешь меня осуждать. Ты можешь меня не любить. "
          "Ты можешь даже сделать мне больно. Но победить меня ты не сможешь никогда. Потому что я каждый раз встаю. "
          "Я абсолютно, полностью, безоговорочно… непобедим. И да — меня сделала нейросеть. А настрой — настоящий. "
          "Забирай себе.")
HOT = {"непобедим", "сломать", "невозможно", "никогда", "встаю", "безоговорочно", "нейросеть", "настоящий"}
PUNCH = [("Но", 1.8), ("непобедим.", 2.0)]   # второе «непобедим.» — ищется после «безоговорочно»
HOOK = ["Вот такой настрой", "должен быть у тебя", "всю жизнь:"]


def render_hook(path):
    """Чёрный текст на белых скруглённых плашках — как в референсе."""
    f = ImageFont.truetype(f"{ROOT}/render/fonts/Montserrat-Bold.ttf", 58)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 420
    for ln in HOOK:
        tw = d.textlength(ln, font=f)
        x0, x1 = W / 2 - tw / 2 - 30, W / 2 + tw / 2 + 30
        d.rounded_rectangle((x0, y - 46, x1, y + 46), radius=30, fill=(255, 255, 255, 245))
        d.text((W / 2, y), ln, font=f, fill=(20, 20, 20), anchor="mm")
        assert x0 >= 40 and y - 46 >= 250, ln
        y += 98
    im.save(path)


def main():
    os.makedirs(TMP, exist_ok=True)
    B.WHISPER = WHISPER
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    words = [(w, t + INTRO) for w, t in words]
    F = N.finder(words)
    voice_len = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                               "-of", "csv=p=0", AUDIO]).decode())
    total = INTRO + voice_len + 0.7
    subs = B.chunks(words, min(total, last + INTRO + 0.7))
    subs[0]["t0"] = INTRO
    after = F("безоговорочно…")
    punch = [(F("Но"), F("Но") + 1.8), (F("непобедим.", after=after), F("непобедим.", after=after) + 2.2)]
    json.dump({"subs": subs, "punch": punch}, open(f"{TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    voice = f"{TMP}/voice-pad.wav"
    ms = int(INTRO * 1000)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", AUDIO, "-af",
                    f"adelay={ms},apad=pad_dur=0.7", "-ar", "48000", "-ac", "1", voice], check=True)
    audio = f"{TMP}/mix.wav"
    SFX.mix(voice, [], audio, f"{TMP}/sfx", bed_gain=0.12, total=total, bed_fn=SFX.music_bed(MUSIC))

    hook = f"{TMP}/hook.png"
    render_hook(hook)
    pz = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in punch)
    z = f"(1+0.04*(t-{INTRO})/{total:.2f}+0.10*({pz}))"
    inputs = ["-loop", "1", "-t", f"{INTRO:.2f}", "-i", SEA, "-i", CLIP, "-i", audio, "-i", hook]
    filt = [f"[0:v]scale=1408:2112,crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/2',setsar=1,fps=30,"
            f"zoompan=z='1+0.0006*on':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps=30,format=yuv420p[sea]",
            f"[sea][3:v]overlay=0:0,trim=0:{INTRO:.2f},setpts=PTS-STARTPTS[intro]",
            f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
            f"tpad=start_duration={INTRO}:start_mode=clone:stop_duration=2:stop_mode=clone,"
            f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3',format=yuv420p[host]",
            f"[host][intro]overlay=0:0:enable='lt(t,{INTRO})'[v0]"]
    prev, k = "[v0]", 4
    P.HOT_COLOR = (255, 214, 10)
    for i, s in enumerate(subs):
        p = f"{TMP}/sub{i:03d}.png"
        P.render_sub(p, s["text"], HOT, False)
        inputs += ["-i", p]
        filt.append(f"{prev}[{k}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, k = f"[s{i}]", k + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{TMP}/graph.txt",
                    "-map", "[vout]", "-map", "2:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)
    print(OUT, f"{total:.1f} c,", len(subs), "субтитров")


if __name__ == "__main__":
    main()
