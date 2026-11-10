"""Reels №25 «Кому ты позвонишь в три ночи?» и №26 «Ж . . . Ь» — ведущая на весь кадр + субтитры.

№25 (по референсу instagram.com/reel/Ddg6_QBQ5cU): ведущая на подкасте, белые субтитры Montserrat
с обводкой, одно ключевое слово в чанке — жёлтое; первая фраза — крупный заголовок; медленный
наезд, тихое фортепиано.
№26 (по референсу instagram.com/reel/DYhXGOYKrWi): психолог в кресле, над головой всё время
крупно «Ж . . . Ь» жёлтым, субтитры заглавными с жёлтыми словами «жизнь / ждать / жесть»,
лёгкая игривая музыка, наезд на шутке.

python3 render/landing/build_ig25.py 25|26   →  render/landing/ig25-9x16.mp4 / ig26-9x16.mp4
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import sfx as SFX

ROOT = B.ROOT
YELLOW = (255, 214, 10)
FONTS = f"{ROOT}/render/fonts"

CFG = {
    "25": dict(
        spoken=("Мне однажды сказали фразу, которую я не могу забыть. Настоящий друг — это тот, кому можно позвонить в "
                "три часа ночи… и ничего не объяснять. Подумай. В твоём телефоне сотни контактов. А кому ты позвонишь, "
                "если ночью станет по-настоящему плохо? Не тому, с кем весело на праздниках. И не тому, кто ставит "
                "лайки. А тому, кто молча возьмёт трубку и скажет: «Еду». Дружба — не про то, как часто вы видитесь. "
                "Она про то, кто приходит, когда плохо. И если у тебя есть хотя бы один такой человек — ты богаче, чем "
                "думаешь. Отправь ему это видео. Пусть знает."),
        hook="КОМУ ТЫ ПОЗВОНИШЬ В_3_НОЧИ?",
        hot={"друг", "ночи", "объяснять", "плохо", "праздниках", "лайки", "еду", "дружба", "приходит", "богаче",
             "отправь", "сотни", "контактов", "знает"},
        punch=[("Еду»."), ("богаче,")], music="ig25-music.mp3", gain=0.10, caps=False, title=None),
    "26": dict(
        spoken=("Посмотри, как ты прочитаешь это слово. Если ты читаешь «жизнь» — у тебя сейчас хороший период, и ты "
                "это чувствуешь. Если «ждать» — ты давно чего-то ждёшь… и очень устал. А если «жесть»… значит, "
                "неделька была та ещё. Но с тобой всё нормально. Напиши в комментариях, какое слово у тебя!"),
        hook="КАК ТЫ ПРОЧИТАЕШЬ ЭТО СЛОВО?",
        hot={"жизнь", "ждать", "жесть", "хороший", "устал", "нормально", "комментариях"},
        punch=["«жесть»…"], music="ig26-music.mp3", gain=0.12, caps=True, title="Ж . . . Ь"),
    "33": dict(
        spoken=("Не трогайте искренних. Слышите? Искренних — не трогайте. Если у вас нет серьёзных намерений — не "
                "пишите им «доброе утро». Не обещайте того, чего не собираетесь делать. Они верят словам. Они ждут. "
                "И им потом больнее всех. Хотите играть — идите к тем, кто играет так же, как вы. А искренних "
                "людей… оставьте в покое. Отправь это тому, кто искренний. Пусть знает, что он не один."),
        hook="НЕ ТРОГАЙТЕ ИСКРЕННИХ",
        hot={"искренних", "намерений", "утро»", "обещайте", "верят", "ждут", "больнее", "играть", "покое", "искренний",
             "один"},
        punch=["Слышите?", "больнее", "покое."], music="ig33-music.mp3", gain=0.12, caps=False, title=None),
    "34": dict(
        spoken=("Вам станет гораздо легче жить, когда вы запомните одну простую вещь. Красивые люди — делают "
                "комплименты. Счастливые — подбадривают. Успешные — поддерживают. Уверенные в себе — вдохновляют… "
                "и искренне радуются за других. А те, кто пуст внутри… только и пытаются вас опустить. Поэтому не "
                "тратьте свою жизнь на мнение пустых людей. Сохрани, чтобы не забыть."),
        hook="ВАМ СТАНЕТ ЛЕГЧЕ ЖИТЬ",
        hot={"красивые", "комплименты", "счастливые", "подбадривают", "успешные", "поддерживают", "уверенные",
             "вдохновляют", "радуются", "пуст", "опустить", "пустых", "сохрани"},
        punch=["пуст", "Поэтому"], music="ig34-music.mp3", gain=0.11, caps=False, title=None,
        # врезки собеседницы (слушает): (слово начала, длительность)
        guest=("scratch/ig34/guest.mp4", [("Счастливые", 2.0), ("Уверенные", 2.6), ("Сохрани,", 1.6)])),
}


def norm(w):
    return re.sub(r"[^\wё]", "", w.lower())


def render_sub(path, text, hot, caps):
    """Белые слова с чёрной обводкой; слово из hot — жёлтое."""
    size = 64 if caps else 66
    f = ImageFont.truetype(B.FONT, size)
    im = Image.new("RGBA", (B.W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    words = (text.upper() if caps else text).split()
    lines, cur = [], []
    for w in words:
        c = cur + [w]
        if d.textlength(" ".join(c), font=f) > B.MAXW and cur:
            lines.append(cur)
            cur = [w]
        else:
            cur = c
    lines.append(cur)
    lh = size * 1.12
    y = 130 - lh * len(lines) / 2
    space = d.textlength(" ", font=f)
    for ln in lines:
        x = B.W / 2 - d.textlength(" ".join(ln), font=f) / 2
        for w in ln:
            col = YELLOW if norm(w) in hot else (255, 255, 255)
            d.text((x, y + lh / 2), w, font=f, fill=col, anchor="lm", stroke_width=B.STROKE, stroke_fill=(0, 0, 0, 235))
            x += d.textlength(w, font=f) + space
        y += lh
    im.save(path)
    assert B.CY - lh * len(lines) / 2 >= 250 and B.CY + lh * len(lines) / 2 <= 1500, text


def render_title(path, text):
    f = ImageFont.truetype(f"{FONTS}/Oswald-Bold.ttf", 150)
    im = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((B.W / 2, 345), text, font=f, fill=YELLOW, anchor="mm", stroke_width=5, stroke_fill=(60, 40, 0, 200))
    bb = d.textbbox((B.W / 2, 345), text, font=f, anchor="mm", stroke_width=5)
    assert bb[1] >= 250, bb
    im.save(path)


def main(n):
    c = CFG[n]
    B.AUDIO = f"{ROOT}/scratch/ig{n}/trim.mp3"
    B.WHISPER = f"{ROOT}/scratch/ig{n}-whisper-final.json"
    B.CLIP = f"{ROOT}/scratch/ig{n}/host.mp4"
    B.OUT = f"{ROOT}/render/landing/ig{n}-9x16.mp4"
    B.TMP = f"{ROOT}/render/landing/.ig{n}"
    os.makedirs(B.TMP, exist_ok=True)
    B.clean_words = lambda: c["spoken"].split()
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode()) + 0.6
    subs = N.chunks_with_hook(words, min(total, last + 0.6))
    subs[0]["text"] = c["hook"]
    punch = [(F(w), F(w) + 1.6) for w in c["punch"]]
    json.dump({"subs": subs, "punch": punch}, open(f"{B.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    padded = f"{B.TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af", "apad=pad_dur=0.6", "-ar", "48000", padded],
                   check=True)
    audio = f"{B.TMP}/mix.wav"
    SFX.mix(padded, [], audio, f"{B.TMP}/sfx", bed_gain=c["gain"], total=total,
            bed_fn=SFX.music_bed(f"{ROOT}/scratch/music/{c['music']}"))

    pz = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in punch) or "0"
    z = f"(1+0.05*t/{total:.2f}+0.10*({pz}))"
    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={B.W}:{B.H}:force_original_aspect_ratio=increase,crop={B.W}:{B.H},setsar=1,fps=30,"
            f"tpad=stop_duration=2:stop_mode=clone,"
            f"scale=w='trunc({B.W}*{z}/2)*2':h='trunc({B.H}*{z}/2)*2':eval=frame,"
            f"crop={B.W}:{B.H}:'(iw-{B.W})/2':'(ih-{B.H})/3',format=yuv420p[v0]"]
    prev, k = "[v0]", 2
    if c.get("guest"):
        gpath, wins = c["guest"]
        inputs += ["-i", f"{ROOT}/{gpath}"]
        en = "+".join(f"between(t,{F(w) - 0.15:.2f},{F(w) - 0.15 + d:.2f})" for w, d in wins)
        filt.append(f"[{k}:v]scale={B.W}:{B.H}:force_original_aspect_ratio=increase,crop={B.W}:{B.H},setsar=1,"
                    f"fps=30,tpad=stop_duration=5:stop_mode=clone,format=yuv420p[g]")
        filt.append(f"{prev}[g]overlay=0:0:enable='{en}'[vg]")
        prev, k = "[vg]", k + 1
    if c["title"]:
        p = f"{B.TMP}/title.png"
        render_title(p, c["title"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{k}:v]overlay=0:0[vt]")
        prev, k = "[vt]", k + 1
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        if i == 0:
            N.render_any(p, s["text"])
        else:
            render_sub(p, s["text"], c["hot"], c["caps"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{k}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, k = f"[s{i}]", k + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, f"{total:.1f} c,", len(subs), "субтитров")


if __name__ == "__main__":
    main(sys.argv[1])
