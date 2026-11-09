"""Reels №30 «Сильного сотрудника теряют раньше» — по референсу instagram.com/reel/DcTIMH_t6WU.

Как в референсе: бизнес-наставница за столиком в ресторане на весь кадр, на ключевых мыслях —
крупные заглавные надписи (Oswald) сверху над лицом, под некоторыми — красная плашка с
уточнением («бесконечный кредит доверия»), внизу обычные белые субтитры (движок build_ig25),
медленный наезд и резкие наезды на главных фразах, тихая музыка из библиотеки HeyGen.

python3 render/landing/build_ig30.py  →  render/landing/ig30-9x16.mp4
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B  # noqa: E402
import build_ig9 as N  # noqa: E402
import build_ig25 as G  # noqa: E402
import sfx as SFX  # noqa: E402

ROOT = B.ROOT
FONTS = f"{ROOT}/render/fonts"
RED = (226, 38, 44)
SPOKEN = ("Сильного сотрудника теряют не в тот день, когда он кладёт заявление на стол. Его теряют раньше. В тот "
          "момент, когда он понимает: хорошо работать здесь… невыгодно. Он закрывает чужие задачи. Исправляет "
          "чужие ошибки. Берёт ответственность. А в награду получает… ещё больше работы. А тот, кто полгода не "
          "даёт результата, получает ещё один шанс. И ещё один. У слабого — бесконечный кредит доверия. А у "
          "сильного… бесконечный список обязанностей. Сильный выдержит аврал, тяжёлый период и даже ошибку "
          "руководителя. Но он не станет работать там, где правила — не для всех. И самый тревожный знак — не "
          "когда он спорит. А когда перестаёт спорить. И спокойно отвечает: «Хорошо. Сделаем, как скажете». "
          "Скорее всего, он уже ищет новое место. Кстати… меня не существует. Меня сделала нейросеть. А вот "
          "ваши сильные сотрудники — настоящие. Берегите их. Напишите в комментариях: вы когда-нибудь уходили "
          "молча?")
HOT = {"сильного", "раньше", "невыгодно", "больше", "шанс", "слабого", "доверия", "обязанностей", "всех",
       "спорить", "место", "нейросеть", "настоящие", "молча", "аврал"}
# (слово-триггер, искать после, заголовок, красная плашка или None)
HEADS = [
    ("Сильного", None, "СИЛЬНОГО СОТРУДНИКА", "теряют раньше, чем кажется"),
    ("невыгодно.", None, "РАБОТАТЬ ХОРОШО", "невыгодно"),
    ("больше", "награду", "НАГРАДА", "ещё больше работы"),
    ("слабого", None, "СЛАБОГО СОТРУДНИКА", "бесконечный кредит доверия"),
    ("сильного", "доверия.", "СИЛЬНОГО СОТРУДНИКА", "бесконечный список обязанностей"),
    ("правила", None, "ПРАВИЛА НЕ ДЛЯ ВСЕХ", None),
    ("перестаёт", None, "ПЕРЕСТАЁТ СПОРИТЬ", "тревожный знак"),
    ("ищет", None, "ОН ИЩЕТ НОВОЕ МЕСТО", None),
    ("существует.", None, "МЕНЯ НЕ СУЩЕСТВУЕТ", "сделано нейросетью"),
    ("Напишите", None, "ВЫ УХОДИЛИ МОЛЧА?", "напишите в комментариях"),
]
MAXDUR = 3.4
PUNCH = ["слабого", "ищет", "существует."]
TOP_LIMIT = 500          # ниже начинается лицо ведущей — заголовки и плашки не ниже


def render_head(path, text, pill):
    im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(f"{FONTS}/Oswald-Bold.ttf", 104)
    while d.textlength(text, font=f) > 980:
        f = ImageFont.truetype(f"{FONTS}/Oswald-Bold.ttf", f.size - 4)
    y = 330
    sh = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((B.W / 2 + 4, y + 6), text, font=f, fill=(0, 0, 0, 150), anchor="mm")
    from PIL import ImageFilter
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d.text((B.W / 2, y), text, font=f, fill="white", anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 120))
    bottom = d.textbbox((B.W / 2, y), text, font=f, anchor="mm")[3]
    if pill:
        fp = ImageFont.truetype(f"{FONTS}/Montserrat-Bold.ttf", 40)
        w = d.textlength(pill, font=fp) + 56
        y0 = bottom + 18
        d.rounded_rectangle((B.W / 2 - w / 2, y0, B.W / 2 + w / 2, y0 + 64), 32, fill=RED)
        d.text((B.W / 2, y0 + 33), pill, font=fp, fill="white", anchor="mm")
        bottom = y0 + 64
    top = d.textbbox((B.W / 2, y), text, font=f, anchor="mm")[1]
    assert top >= 255 and bottom <= TOP_LIMIT, (text, top, bottom)
    im.save(path)


def main():
    B.AUDIO = f"{ROOT}/scratch/ig30/trim.mp3"
    B.WHISPER = f"{ROOT}/scratch/ig30-whisper-final.json"
    B.CLIP = f"{ROOT}/scratch/ig30/host.mp4"
    B.OUT = f"{ROOT}/render/landing/ig30-9x16.mp4"
    B.TMP = f"{ROOT}/render/landing/.ig30"
    os.makedirs(B.TMP, exist_ok=True)
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode()) + 0.6
    subs = B.chunks(words, min(total, last + 0.6))

    heads = []
    for trig, after, text, pill in HEADS:
        t = 0.15 if not heads else F(trig, F(after) if after else heads[-1][0])
        heads.append([t, text, pill])
    for i, h in enumerate(heads):
        nxt = heads[i + 1][0] - 0.05 if i + 1 < len(heads) else total
        end = nxt if i + 1 == len(heads) else min(nxt, h[0] + MAXDUR)
        h.append(end)
        assert end - h[0] >= 1.6, ("заголовок мелькает", h)
    punch = [(F(w), F(w) + 1.5) for w in PUNCH]
    json.dump({"subs": subs, "heads": heads, "punch": punch}, open(f"{B.TMP}/plan.json", "w"),
              ensure_ascii=False, indent=1)

    padded = f"{B.TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af", "apad=pad_dur=0.6", "-ar", "48000", padded],
                   check=True)
    audio = f"{B.TMP}/mix.wav"
    ev = [(h[0], "pop", 0.35) for h in heads[1:]] + [(F("существует."), "glitch", 0.3)]
    SFX.mix(padded, ev, audio, f"{B.TMP}/sfx", bed_gain=0.10, total=total,
            bed_fn=SFX.music_bed(f"{ROOT}/scratch/music/ig30-music.mp3"))

    pz = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in punch)
    z = f"(1+0.05*t/{total:.2f}+0.10*({pz}))"
    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={B.W}:{B.H}:force_original_aspect_ratio=increase,crop={B.W}:{B.H},setsar=1,fps=30,"
            f"tpad=stop_duration=2:stop_mode=clone,"
            f"scale=w='trunc({B.W}*{z}/2)*2':h='trunc({B.H}*{z}/2)*2':eval=frame,"
            f"crop={B.W}:{B.H}:'(iw-{B.W})/2':'(ih-{B.H})/3',format=yuv420p[v0]"]
    prev, k = "[v0]", 2
    for i, (t0, text, pill, t1) in enumerate(heads):
        p = f"{B.TMP}/head{i:02d}.png"
        render_head(p, text, pill)
        inputs += ["-loop", "1", "-t", f"{total:.3f}", "-i", p]
        filt.append(f"[{k}:v]format=rgba,fade=in:st={t0:.3f}:d=0.18:alpha=1[h{i}]")
        filt.append(f"{prev}[h{i}]overlay=0:0:enable='gte(t,{t0:.3f})*lt(t,{t1:.3f})'[vh{i}]")
        prev, k = f"[vh{i}]", k + 1
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        G.render_sub(p, s["text"], HOT, False)
        inputs += ["-i", p]
        filt.append(f"{prev}[{k}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, k = f"[s{i}]", k + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, f"{total:.1f} c,", len(subs), "субтитров,", len(heads), "заголовков")


if __name__ == "__main__":
    main()
