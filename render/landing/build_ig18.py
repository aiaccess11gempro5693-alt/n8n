"""Reels №18 «Это видео записала моя бабушка» — тёплый продающий ролик.

Вступление 2.6 с: старое ч/б фото бабушки в рамке на столе (gpt-image-2), наезд в фото и
крючок «ЭТО ВИДЕО ЗАПИСАЛА МОЯ БАБУШКА» → фото «оживает»: клип HeyGen проявляется из
чёрно-белого в цвет → бабушка говорит внуку (кадры: пироги, телефон) → на «А теперь секрет…
меня не существует» картинка снова уходит в ч/б, на «Если хочешь…» возвращается цвет → на
«Но сначала… позвони своей» кадр темнеет и крупно: «Позвони своей. Пока можешь.»
Белые субтитры движка build_ig6, тихое фортепиано из библиотеки HeyGen. Зона 250–1500.

python3 render/landing/build_ig18.py   →  render/landing/ig18-9x16.mp4
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
VOICE = f"{ROOT}/scratch/ig18/trim.mp3"
WHISPER_SRC = f"{ROOT}/scratch/ig18-whisper-final.json"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig18/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig18-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig18"
IMG = f"{ROOT}/scratch/img"
MUSIC = f"{ROOT}/scratch/music/ig18-music.mp3"
MUSIC_GAIN = 0.12
SERIF = f"{ROOT}/render/fonts/PlayfairDisplay-Bold.ttf"

INTRO = 2.6          # вступление: фото в рамке, голоса ещё нет
TAIL = 1.6           # финальная карточка держится после последнего слова
SPOKEN = ("Внучек, здравствуй. Опять сидишь в телефоне до ночи? Поешь нормально, не перекусывай на бегу. "
          "Маме позвони — она скучает, хоть и не скажет. И не бойся ничего. У тебя всё получится. "
          "Я тобой горжусь. А теперь секрет… Меня не существует. Меня сделала нейросеть — из одной фотографии. "
          "Если хочешь, чтобы твоя бабушка вот так сказала тебе пару слов — на юбилей, на память, просто так — "
          "напиши «Память». Но сначала… позвони своей. Пока можешь.")
HOOK = "ЭТО ВИДЕО ЗАПИСАЛА МОЯ БАБУШКА"
BROLLS = [("ig18_pies", "Поешь", 3.4), ("ig18_phone", "Маме", 3.4)]
# центр фото в рамке на кадре ig18_frame (доли ширины/высоты исходника 1024×1536)
FRAME_CX, FRAME_CY, ZOOM = 0.50, 0.45, 1.9


def prepare():
    """Голос со сдвигом на INTRO и whisper-тайминги с тем же сдвигом."""
    os.makedirs(B.TMP, exist_ok=True)
    voice = f"{B.TMP}/voice.wav"
    ms = int(INTRO * 1000)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VOICE, "-af", f"adelay={ms}:all=1,apad=pad_dur={TAIL}",
                    "-ar", "48000", voice], check=True)
    w = json.load(open(WHISPER_SRC))
    for x in w["words"]:
        x["start"] += INTRO
        x["end"] += INTRO
    path = f"{B.TMP}/whisper.json"
    json.dump(w, open(path, "w"), ensure_ascii=False)
    B.AUDIO, B.WHISPER = voice, path
    B.clean_words = lambda: SPOKEN.split()


def render_final(path):
    """«Позвони своей. / Пока можешь.» — крупный белый Playfair по центру."""
    im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f1, f2 = ImageFont.truetype(SERIF, 104), ImageFont.truetype(SERIF, 76)
    d.text((B.W / 2, 820), "Позвони своей.", font=f1, fill="white", anchor="mm",
           stroke_width=3, stroke_fill=(0, 0, 0, 160))
    d.text((B.W / 2, 960), "Пока можешь.", font=f2, fill=(240, 220, 190), anchor="mm",
           stroke_width=3, stroke_fill=(0, 0, 0, 160))
    im.save(path)
    return 820 - 70, 960 + 55     # верх/низ текста — для проверки зоны


def sat_expr(t_bw0, t_bw1):
    """Насыщенность клипа: из ч/б в цвет после вступления, снова ч/б на «секрете»."""
    up = f"min(1,max(0,(t-{INTRO:.2f})/1.8))"
    bw = (f"min(1,max(0,(t-{t_bw0:.2f})/0.6))*(1-min(1,max(0,(t-{t_bw1:.2f})/0.8)))")
    return f"{up}*(1-{bw})"


def main():
    prepare()
    words, last = B.timed_words()
    F = N.finder(words)
    total = INTRO + float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                                   "-of", "csv=p=0", VOICE]).decode()) + TAIL
    t_secret, t_back, t_final = F("А", F("горжусь.")), F("Если"), F("Но", F("«Память».") - 0.3)
    subs = [s for s in N.chunks(words, last + 0.6) if s["t0"] < t_final - 0.05]
    subs[-1]["t1"] = min(subs[-1]["t1"], t_final)
    brolls = [(img, F(w) - 0.1, dur) for img, w, dur in BROLLS]
    for (a, ta, da), (b, tb, db) in zip(brolls, brolls[1:]):
        assert ta + da <= tb, f"кадры {a}/{b} перекрываются"
    assert brolls[-1][1] + brolls[-1][2] < t_secret, "кадр не должен закрывать «секрет»"
    top, bottom = render_final(f"{B.TMP}/final.png")
    assert 250 <= top and bottom <= 1500
    json.dump({"subs": subs, "brolls": brolls, "secret": t_secret, "back": t_back, "final": t_final},
              open(f"{B.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [], audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    W, H = B.W, B.H
    fin = total - t_final
    inputs = ["-i", B.CLIP, "-i", audio,
              "-loop", "1", "-t", f"{INTRO + 0.6:.2f}", "-i", f"{IMG}/ig18_frame.png",
              "-f", "lavfi", "-t", f"{fin:.2f}", "-i", f"color=black:s={W}x{H}:r=30",
              "-loop", "1", "-t", f"{fin:.2f}", "-i", f"{B.TMP}/final.png"]
    sx, sy = FRAME_CX * 1280, FRAME_CY * 1920
    z = f"(1+{ZOOM - 1:.2f}*pow(min(t/{INTRO + 0.6:.2f},1),2))"
    filt = [
        # бабушка: задержка на вступление, цвет по выражению, лёгкий наезд на весь ролик
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
        f"tpad=start_duration={INTRO:.2f}:start_mode=clone:stop_duration={TAIL + 1:.2f}:stop_mode=clone,"
        f"hue=s='{sat_expr(t_secret, t_back)}',"
        f"scale=w='trunc({W}*(1+0.05*t/{total:.2f})/2)*2':h='trunc({H}*(1+0.05*t/{total:.2f})/2)*2':eval=frame,"
        f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3',format=yuv420p[v0]",
        # вступление: фото в рамке, наезд в портрет, растворение в живую бабушку
        f"[2:v]scale=1280:1920,setsar=1,fps=30,format=rgba,"
        f"scale=w='trunc(1280*{z}/2)*2':h='trunc(1920*{z}/2)*2':eval=frame,"
        f"crop={W}:{H}:'min(max({sx:.0f}*{z}-{W / 2:.0f},0),iw-{W})':'min(max({sy:.0f}*{z}-{H / 2:.0f},0),ih-{H})',"
        f"fade=out:st={INTRO:.2f}:d=0.6:alpha=1[intro]",
        "[v0][intro]overlay=0:0:eof_action=pass[vi]",
    ]
    prev, n = "[vi]", 5
    for i, (img, t0, dur) in enumerate(brolls):
        inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", f"{IMG}/{img}.png"]
        filt.append(N.broll_filter(n, t0, dur, f"b{i}"))
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass[vb{i}]")
        prev, n = f"[vb{i}]", n + 1
    hook = f"{B.TMP}/hook.png"
    N.render_any(hook, HOOK)
    inputs += ["-i", hook]
    filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 130}:enable='lt(t,{INTRO:.2f})'[vh]")
    prev, n = "[vh]", n + 1
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        N.render_any(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    # финал: затемнение и крупная надпись
    filt.append(f"[3:v]format=rgba,colorchannelmixer=aa=0.62,fade=in:st=0:d=0.8:alpha=1,"
                f"setpts=PTS+{t_final:.3f}/TB[dk]")
    filt.append(f"[4:v]format=rgba,fade=in:st=0.3:d=0.8:alpha=1,setpts=PTS+{t_final:.3f}/TB[fn]")
    filt.append(f"{prev}[dk]overlay=0:0:eof_action=pass[vd]")
    filt.append("[vd][fn]overlay=0:0:eof_action=pass,format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, f"{total:.1f} c,", len(subs), "субтитров; секрет", round(t_secret, 1), "финал", round(t_final, 1))


if __name__ == "__main__":
    main()
