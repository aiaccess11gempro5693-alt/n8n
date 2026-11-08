"""Reels №27 «О чём вы жалеете больше всего?» — вопрос девушки → ответ дедушки в ч/б.

По референсу instagram.com/reel/DfFMyLnIl_4: девушка в машине задаёт вопрос (цвет, крупные белые
заглавные субтитры), склейка на пожилого мужчину (чёрно-белый, медленный наезд, белые субтитры с
засечками), в конце — чёрный экран с главной фразой. Под всем — тихие фортепиано и струнные.
Клипы HeyGen — отдельно на голос девушки и голос дедушки, звук собирается встык.

python3 render/landing/build_ig27.py   →  render/landing/ig27-9x16.mp4
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
W, H = B.W, B.H
TMP = f"{ROOT}/render/landing/.ig27"
OUT = f"{ROOT}/render/landing/ig27-9x16.mp4"
FONTS = f"{ROOT}/render/fonts"
GIRL = ("Спросила у дедушки во дворе: о чём вы больше всего жалеете в жизни? Слушайте.")
OLD = ("Что ждал подходящего момента. Маме хотел сказать, что люблю, — думал, потом. К морю хотел поехать — думал, "
       "на пенсии. А потом… уже некому говорить. И уже не так хочется. Подходящий момент — это сегодня. Завтра его "
       "могут забрать.")
GAP, END = 0.35, 2.6          # пауза между репликами, финальная карточка
FINAL = "Подходящий момент —\nэто сегодня."


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).decode())


def timed(text, audio, whisper, offset):
    B.AUDIO, B.WHISPER = audio, whisper
    B.clean_words = lambda: text.split()
    words, last = B.timed_words()
    subs = B.chunks(words, last + 0.5)
    for s in subs:
        s["t0"] += offset
        s["t1"] += offset
    return subs


def caps_sub(path, text):
    """Девушка: крупные белые заглавные с мягкой тенью (как в референсе)."""
    f = ImageFont.truetype(f"{FONTS}/Montserrat-ExtraBold.ttf", 62)
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines, cur = [], ""
    for w in text.upper().split():
        c = (cur + " " + w).strip()
        if d.textlength(c, font=f) > 900 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = c
    lines.append(cur)
    lh = 72
    y = 150 - lh * len(lines) / 2
    for ln in lines:
        d.text((W / 2, y + lh / 2), ln, font=f, fill="white", anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 200))
        y += lh
    im.save(path)
    assert len(lines) <= 3, text


def serif_sub(path, text):
    """Дедушка: белый текст с засечками, без плашки."""
    f = ImageFont.truetype(f"{FONTS}/PlayfairDisplay-SemiBold.ttf", 54)
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines, cur = [], ""
    for w in text.split():
        c = (cur + " " + w).strip()
        if d.textlength(c, font=f) > 880 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = c
    lines.append(cur)
    lh = 66
    y = 150 - lh * len(lines) / 2
    for ln in lines:
        d.text((W / 2, y + lh / 2), ln, font=f, fill=(245, 245, 240), anchor="mm", stroke_width=3,
               stroke_fill=(0, 0, 0, 170))
        y += lh
    im.save(path)


def final_card(path):
    f = ImageFont.truetype(f"{FONTS}/PlayfairDisplay-SemiBold.ttf", 76)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    d.multiline_text((W / 2, 900), FINAL, font=f, fill=(240, 236, 228), anchor="mm", align="center", spacing=22)
    im.save(path)


def main():
    os.makedirs(TMP, exist_ok=True)
    g_audio, o_audio = f"{ROOT}/scratch/ig27/girl.mp3", f"{ROOT}/scratch/ig27/old.mp3"
    g = dur(g_audio)
    o = dur(o_audio)
    t_old = g + GAP
    total = t_old + o + END
    subs_g = timed(GIRL, g_audio, f"{ROOT}/scratch/ig27-girl-whisper.json", 0.0)
    subs_o = timed(OLD, o_audio, f"{ROOT}/scratch/ig27-old-whisper-final.json", t_old)
    subs_g[0]["t0"] = 0.0
    subs_g[-1]["t1"] = t_old
    subs_o[0]["t0"] = t_old + 0.1
    subs_o[-1]["t1"] = t_old + o
    json.dump({"girl": subs_g, "old": subs_o}, open(f"{TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    voice = f"{TMP}/voice.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", g_audio, "-i", o_audio, "-filter_complex",
                    f"[0:a]aresample=48000,aformat=channel_layouts=mono,apad=pad_dur={GAP}[a];"
                    f"[1:a]aresample=48000,aformat=channel_layouts=mono,apad=pad_dur={END}[b];[a][b]concat=n=2:v=0:a=1",
                    voice], check=True)
    audio = f"{TMP}/mix.wav"
    SFX.mix(voice, [], audio, f"{TMP}/sfx", bed_gain=0.13, total=total,
            bed_fn=SFX.music_bed(f"{ROOT}/scratch/music/ig27-music.mp3"))

    card = f"{TMP}/final.png"
    final_card(card)
    inputs = ["-i", f"{ROOT}/scratch/ig27/girl.mp4", "-i", f"{ROOT}/scratch/ig27/old.mp4", "-i", audio,
              "-loop", "1", "-t", f"{END:.2f}", "-i", card]
    zo = f"(1+0.07*t/{o:.2f})"
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
            f"tpad=stop_duration=1:stop_mode=clone,trim=0:{t_old:.3f},setpts=PTS-STARTPTS[g]",
            f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
            f"tpad=stop_duration=1:stop_mode=clone,trim=0:{o:.3f},setpts=PTS-STARTPTS,"
            f"hue=s=0,eq=contrast=1.12:brightness=-0.03,"
            f"scale=w='trunc({W}*{zo}/2)*2':h='trunc({H}*{zo}/2)*2':eval=frame,crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3',"
            f"fade=in:st=0:d=0.25[o]",
            f"[3:v]format=rgba,fps=30,fade=in:st=0:d=0.6[c]",
            "[g][o]concat=n=2:v=1:a=0,format=yuv420p[gv]",
            f"[gv][c]overlay=0:0:enable='gte(t,{t_old + o:.3f})':eof_action=pass[v0]"]
    # оверлей финальной карточки должен стартовать в нужный момент
    filt[2] = f"[3:v]format=rgba,fps=30,fade=in:st=0:d=0.6,setpts=PTS+{t_old + o:.3f}/TB[c]"
    filt[4] = f"[gv][c]overlay=0:0:eof_action=pass[v0]"
    filt[3] = f"[g][o]concat=n=2:v=1:a=0,tpad=stop_duration={END + 0.5}:stop_mode=clone,format=yuva420p[gv]"
    prev, k = "[v0]", 4
    for i, s in enumerate(subs_g + subs_o):
        p = f"{TMP}/sub{i:03d}.png"
        (caps_sub if i < len(subs_g) else serif_sub)(p, s["text"])
        y = 1150 if i < len(subs_g) else 1230
        inputs += ["-i", p]
        filt.append(f"{prev}[{k}:v]overlay=0:{y}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, k = f"[s{i}]", k + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{TMP}/graph.txt",
                    "-map", "[vout]", "-map", "2:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", OUT], check=True)
    print(OUT, f"{total:.1f} c,", len(subs_g) + len(subs_o), "субтитров")


if __name__ == "__main__":
    main()
