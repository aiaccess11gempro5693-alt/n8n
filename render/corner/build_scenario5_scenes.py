"""Сценарий 5, первые 2 сцены — тестовый прогон нового формата
(23.09.2026 (7), CLAUDE.md):

  сцена 1 — аватар на весь кадр (HeyGen Avatar IV), без отвлекающих
            элементов, только статичные субтитры по центру;
  сцена 2 — аватар (HeyGen Avatar III) плавно уезжает в правый нижний угол,
            на освободившемся месте — брендированная плашка (палитра
            брендбука docs/references/oleg-brand-board-*.jpg), её пункты
            появляются в момент, когда диктор их произносит (тайминги слов —
            whisper-1, scratch/scenario5-full-v1-whisper.json); субтитры
            сдвинуты влево от угла с аватаром.

Звук — непрерывная исходная дорожка scratch/scenario5-full-v1.mp3 (а не
склейка звука двух клипов), чтобы на стыке сцен не было щелчка/паузы.

Запуск:  python3 -m render.corner.build_scenario5_scenes
Вход:    scratch/s5-scene1.mp4, scratch/s5-scene2.mp4 (клипы HeyGen)
Выход:   render/corner/s5-scenes-1-2.mp4
"""
import difflib
import json
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFilter

from . import brand_style as S
from . import geometry as G
from . import static_captions as C

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = f"{HERE}/_frames"
AUDIO = f"{ROOT}/scratch/scenario5-full-v1.mp3"
WHISPER = f"{ROOT}/scratch/scenario5-full-v1-whisper.json"
SCENARIO = f"{ROOT}/docs/scenarios/scenario-5-greeting.md"
OUT = f"{HERE}/s5-scenes-1-2.mp4"

# Границы сцен в исходной дорожке — середины пауз после "…и поможет." и
# "…спокойнее и подробнее." (whisper + silencedetect).
SCENES = [
    {"clip": f"{ROOT}/scratch/s5-scene1.mp4", "start": 0.0, "end": 23.5, "paragraphs": (0, 2)},
    {"clip": f"{ROOT}/scratch/s5-scene2.mp4", "start": 23.5, "end": 45.8, "paragraphs": (2, 3)},
]

FPS = 25
MOVE_T0, MOVE_T1 = 0.0, 0.9          # съезд аватара в угол, от начала сцены 2
APPEAR_D = 0.35                      # появление элемента плашки (fade + подъём)
APPEAR_RISE = 24


def hex_(c):
    return f"0x{c[0]:02X}{c[1]:02X}{c[2]:02X}"


# ---------------------------------------------------------------- тайминги

def _norm(w):
    return re.sub(r"[^\w]+", "", w.lower().replace("ё", "е"))


def scenario_paragraphs():
    body = open(SCENARIO, encoding="utf-8").read().split("\n---\n")[1]
    return [C.strip_emotion_tags(p) for p in body.strip().split("\n\n") if p.strip()]


def word_times(clean_text, whisper_words):
    """Каждому слову сценария — время начала из whisper (выравнивание
    difflib; для слов, которые whisper услышал иначе — время соседа)."""
    src = clean_text.split()
    a = [_norm(w) for w in src]
    b = [_norm(w["word"]) for w in whisper_words]
    times = [None] * len(src)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = whisper_words[blk.b + k]["start"]
    last = 0.0
    for i, t in enumerate(times):
        if t is None:
            times[i] = last
        last = times[i]
    return list(zip(src, times))


def caption_timeline(words, t0, t1):
    """Статичные субтитры: чанки ≤2 строк; чанк висит от своего первого
    слова до первого слова следующего (время — относительно сцены)."""
    max_w = G.SUBTITLE_W - C.ACCENT_BAR_W - C.PAD_LEFT - C.PAD_RIGHT
    # чанк не пересекает границу предложения — текст на экране меняется
    # вместе с мыслью, а не посреди фразы
    sentences, cur = [], []
    for w, _ in words:
        cur.append(w)
        if re.search(r"[.!?…»]$", w):
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)
    chunks = [ch for sent in sentences for ch in C.wrap_into_chunks(" ".join(sent), max_w)]
    tl, i = [], 0
    for ch in chunks:
        n = sum(len(line) for line in ch)
        tl.append({"lines": ch, "start": max(0.0, words[i][1] - t0)})
        i += n
    for k, c in enumerate(tl):
        c["end"] = tl[k + 1]["start"] if k + 1 < len(tl) else t1 - t0
        c["start"], c["end"] = round(c["start"], 3), round(c["end"], 3)
    tl[0]["start"] = 0.0
    return tl


def t_of(words, needle, after=0.0):
    n = _norm(needle)
    for w, t in words:
        if _norm(w) == n and t >= after:
            return t
    raise KeyError(needle)


# ---------------------------------------------------------------- графика

def rounded_card(w, h, fill, radius=28, shadow=True):
    pad = 30 if shadow else 0
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 8, pad + w, pad + h + 8], radius, fill=(20, 40, 90, 40))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(img).rounded_rectangle([pad, pad, pad + w, pad + h], radius, fill=fill)
    return img, pad


def wrap(draw, text, font, max_w):
    lines, cur = [], []
    for word in text.split():
        trial = " ".join(cur + [word])
        if cur and draw.textlength(trial, font=font) > max_w:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    return lines + [" ".join(cur)] if cur else lines


def make_background(path):
    """Светлый фон брендбука + мягкие декоративные круги (как в разделе
    "Декоративные элементы" брендборда)."""
    img = Image.new("RGBA", (G.FRAME_W, G.FRAME_H), S.LIGHT_BG)
    deco = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(deco)
    d.ellipse([1500, -260, 2140, 380], fill=(47, 128, 237, 26))
    d.ellipse([-220, 760, 260, 1240], fill=(39, 174, 96, 20))
    img = Image.alpha_composite(img, deco.filter(ImageFilter.GaussianBlur(2)))
    img.save(path)


def make_header(path):
    img = Image.new("RGBA", (1300, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 6, 8, 150], 4, fill=S.GREEN)
    d.text((34, 0), "ПРИВЕТСТВИЕ", font=S.font(S.F_SEMIBOLD, 28), fill=S.LIGHT_BLUE)
    d.text((32, 44), "Первый сигнал доверия", font=S.font(S.F_HEADLINE, 76), fill=(15, 45, 125, 255))
    img.save(path)
    return img.size


def make_quote(path, w=1720, h=170):
    img, pad = rounded_card(w, h, S.BLUE)
    d = ImageDraw.Draw(img)
    x0, y0 = pad + 56, pad
    d.text((x0 - 8, y0 + 8), "“", font=S.font(S.F_HEADLINE, 150), fill=(255, 255, 255, 70))
    d.text((x0 + 80, y0 + 30), "ЧТО СЛЫШИТ ЧЕЛОВЕК", font=S.font(S.F_SEMIBOLD, 24), fill=(190, 212, 255, 255))
    d.text((x0 + 80, y0 + 66), "«Я вас вижу. Я готов помочь»", font=S.font(S.F_HEADLINE, 56), fill=S.WHITE)
    img.save(path)
    return img.size, pad


def make_step(path, num, text, color, w=540, h=230):
    img, pad = rounded_card(w, h, S.WHITE)
    d = ImageDraw.Draw(img)
    x0, y0 = pad + 36, pad + 34
    d.ellipse([x0, y0, x0 + 64, y0 + 64], fill=color)
    f_num = S.font(S.F_SEMIBOLD, 28)
    tw = d.textlength(num, font=f_num)
    d.text((x0 + 32 - tw / 2, y0 + 15), num, font=f_num, fill=S.WHITE)
    f = S.font(S.F_SEMIBOLD, 36)
    for i, line in enumerate(wrap(d, text, f, w - 72)):
        d.text((x0, y0 + 92 + i * 46), line, font=f, fill=S.TEXT_DARK)
    img.save(path)
    return img.size, pad


def make_corner_frame(path, radius=22, border=5):
    """Рамка поверх уехавшего в угол аватара: мягкая тень вокруг, углы
    вне скругления закрашены цветом фона, белая обводка. Внутри —
    прозрачно (клип виден)."""
    m = 40
    w, h = G.CORNER_W + 2 * m, G.CORNER_H + 2 * m
    box = [m, m, m + G.CORNER_W - 1, m + G.CORNER_H - 1]
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([m, m + 10, m + G.CORNER_W, m + G.CORNER_H + 10], radius, fill=(20, 40, 90, 70))
    img = sh.filter(ImageFilter.GaussianBlur(16))
    ImageDraw.Draw(img).rectangle(box, fill=S.LIGHT_BG)        # углы вне скругления — фон
    ImageDraw.Draw(img).rounded_rectangle(box, radius, fill=(0, 0, 0, 0))  # внутри — прозрачно
    ImageDraw.Draw(img).rounded_rectangle(box, radius, outline=S.WHITE, width=border)
    img.save(path)
    return m


# ---------------------------------------------------------------- рендер

def run(cmd):
    subprocess.run(cmd, check=True)


def render_scene1(words, dur, out):
    tl = caption_timeline(words, 0.0, dur)
    fc = [f"[0:v]tpad=stop_mode=clone:stop_duration=1,trim=0:{dur},setpts=PTS-STARTPTS,scale={G.FRAME_W}:{G.FRAME_H},fps={FPS},format=yuv420p[v0]"]
    cap, last = C.build_filter("v0", tl, corner_start=10 ** 6)
    fc += cap
    run(["ffmpeg", "-v", "error", "-y", "-i", SCENES[0]["clip"], "-filter_complex", ";".join(fc),
         "-map", f"[{last}]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS), out])


def render_scene2(words, t0, dur, out):
    os.makedirs(TMP, exist_ok=True)
    bg = f"{TMP}/s2_bg.png"
    make_background(bg)
    make_header(f"{TMP}/s2_header.png")
    (qw, qh), qpad = make_quote(f"{TMP}/s2_quote.png")
    steps = [
        ("01", "Тёплая фраза в первые секунды", S.BLUE, "Одна"),
        ("02", "Напряжение спадает", S.LIGHT_BLUE, "напряжение"),
        ("03", "Человек рассказывает спокойнее и подробнее", S.GREEN, "начинает"),
    ]
    step_meta = []
    for i, (num, text, color, trig) in enumerate(steps):
        size, pad = make_step(f"{TMP}/s2_step{i}.png", num, text, color)
        step_meta.append((f"{TMP}/s2_step{i}.png", size, pad, t_of(words, trig, t0) - t0))
    fm = make_corner_frame(f"{TMP}/s2_frame.png")

    # раскладка: контент — левее колонки аватара/выше угла (см. geometry.py)
    X0 = 100
    items = [  # (png, x, y, t_appear)
        (f"{TMP}/s2_header.png", X0, 90, MOVE_T1),
        (f"{TMP}/s2_quote.png", X0 - qpad, 290 - qpad, t_of(words, "Я", t0) - t0),
    ]
    sx = X0
    for png, (w, h), pad, t in step_meta:
        items.append((png, sx - pad, 500 - pad, t))
        sx += (w - 2 * pad) + 50

    inputs = ["-i", SCENES[1]["clip"], "-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i", bg]
    for png, *_ in items:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i", png]
    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i", f"{TMP}/s2_frame.png"]

    a, b = MOVE_T0, MOVE_T1
    p = f"clip((t-{a})/({b}-{a})\\,0\\,1)"
    e = f"({p})*({p})*(3-2*({p}))"  # smoothstep
    w_expr = f"{G.FRAME_W}+({G.CORNER_W}-{G.FRAME_W})*{e}"
    h_expr = f"{G.FRAME_H}+({G.CORNER_H}-{G.FRAME_H})*{e}"
    fc = [
        f"[1:v]format=rgba,fps={FPS}[bg]",
        f"[0:v]tpad=stop_mode=clone:stop_duration=1,trim=0:{dur},setpts=PTS-STARTPTS,scale={G.FRAME_W}:{G.FRAME_H},fps={FPS},"
        f"scale=w='{w_expr}':h='{h_expr}':eval=frame[av]",
    ]
    prev = "bg"
    for k, (png, x, y, t) in enumerate(items):
        idx = k + 2
        t = max(t, MOVE_T1)
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={t:.2f}:d={APPEAR_D}:alpha=1[it{k}]")
        rise = f"{APPEAR_RISE}*(1-clip((t-{t:.2f})/{APPEAR_D}\\,0\\,1))"
        fc.append(f"[{prev}][it{k}]overlay=x={x}:y='{y}+{rise}':enable='gte(t,{t:.2f})'[o{k}]")
        prev = f"o{k}"
    fc.append(f"[{prev}][av]overlay=x='{G.CORNER_X}*{e}':y='{G.CORNER_Y}*{e}':eval=frame[wa]")
    fidx = len(items) + 2
    fc.append(f"[{fidx}:v]format=rgba,fade=t=in:st={MOVE_T1 - 0.1:.2f}:d=0.2:alpha=1[fr]")
    fc.append(f"[wa][fr]overlay=x={G.CORNER_X - fm}:y={G.CORNER_Y - fm}:enable='gte(t,{MOVE_T1 - 0.1:.2f})',format=yuv420p[vb]")
    tl = caption_timeline(words, t0, t0 + dur)
    cap, last = C.build_filter("vb", tl, corner_start=0.0)
    fc += cap
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", f"[{last}]", "-an", "-t", f"{dur}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-r", str(FPS), out])


def main():
    os.makedirs(TMP, exist_ok=True)
    paras = scenario_paragraphs()
    whisper_words = json.load(open(WHISPER, encoding="utf-8"))["words"]
    all_words = word_times(" ".join(paras), whisper_words)

    parts = []
    for i, sc in enumerate(SCENES):
        dur = round(sc["end"] - sc["start"], 3)
        words = [(w, t) for w, t in all_words if sc["start"] <= t < sc["end"]]
        out = f"{TMP}/scene{i + 1}.mp4"
        if i == 0:
            render_scene1(words, dur, out)
        else:
            render_scene2(words, sc["start"], dur, out)
        parts.append(out)

    lst = f"{TMP}/concat.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    total = SCENES[-1]["end"] - SCENES[0]["start"]
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-ss", f"{SCENES[0]['start']}", "-t", f"{total}", "-i", AUDIO,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-shortest", OUT])
    print(OUT)


if __name__ == "__main__":
    main()
