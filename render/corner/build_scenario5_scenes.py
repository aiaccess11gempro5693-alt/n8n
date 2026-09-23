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
from . import cards as K
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


def make_quote(path, w=1020, h=170):
    img, pad = rounded_card(w, h, S.BLUE)
    d = ImageDraw.Draw(img)
    x0, y0 = pad + 56, pad
    d.text((x0 - 8, y0 + 8), "“", font=S.font(S.F_HEADLINE, 150), fill=(255, 255, 255, 70))
    d.text((x0 + 80, y0 + 30), "ЧТО СЛЫШИТ ЧЕЛОВЕК", font=S.font(S.F_SEMIBOLD, 24), fill=(190, 212, 255, 255))
    d.text((x0 + 80, y0 + 70), "«Я вас вижу. Я готов помочь»", font=S.font(S.F_HEADLINE, 50), fill=S.WHITE)
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

IMG = f"{ROOT}/scratch/img"
FADE_OUT = 0.3


def run(cmd):
    subprocess.run(cmd, check=True)


def item(made, x, y, t_in, t_out=None):
    """made — (png, pad) из cards.*; x/y — позиция видимой части."""
    png, pad = made
    return {"png": png, "x": x - pad, "y": y - pad, "t_in": t_in, "t_out": t_out}


def overlay_items(fc, inputs, prev, items, dur, first_idx):
    """Появление: fade + подъём снизу; исчезновение (t_out): fade."""
    for k, it in enumerate(items):
        idx = first_idx + k
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i", it["png"]]
        t, t_out = it["t_in"], it["t_out"]
        chain = f"[{idx}:v]format=rgba,fade=t=in:st={t:.2f}:d={APPEAR_D}:alpha=1"
        if t_out:
            chain += f",fade=t=out:st={t_out - FADE_OUT:.2f}:d={FADE_OUT}:alpha=1"
        fc.append(chain + f"[it{idx}]")
        rise = f"{APPEAR_RISE}*(1-clip((t-{t:.2f})/{APPEAR_D}\\,0\\,1))"
        en = f"between(t,{t:.2f},{t_out:.2f})" if t_out else f"gte(t,{t:.2f})"
        fc.append(f"[{prev}][it{idx}]overlay=x={it['x']}:y='{it['y']}+{rise}':enable='{en}'[o{idx}]")
        prev = f"o{idx}"
    return prev


def scene1_items(words):
    """Правило (23.09.2026 (10)): в кадре одновременно — только элементы
    ОДНОЙ мысли (текущее предложение/смысловой блок), и ничего не
    появляется на миг: блок держится, пока диктор его раскрывает.
      0–5.4    тема ролика (приветствие + "десятки людей" — вступление);
      5.8–13.4 тревога: иллюстрация встревоженной очереди + заголовок +
               "за себя / за ребёнка / за близкого";
      13.5–    контакт взглядом: иллюстрация + заголовок, затем
               ✗ витрина ✗ ценник ✓ живой специалист (то, что он ищет глазами).
    """
    T = lambda w, after=0.0: t_of(words, w, after)  # noqa: E731
    L, R, W = 50, 1330, 540
    f = lambda n: f"{TMP}/s1_{n}.png"  # noqa: E731
    t_worry, t_eyes, t_cmp, end = T("почти"), T("Первое"), T("витрину"), 23.25
    worry_end = t_eyes - 0.1
    t_self = T("за", t_worry)
    t_child = T("за", t_self + 0.1)
    t_close = T("за", t_child + 0.1)
    worry = K.headline(f("worry"), "Почти каждый приходит", "с лёгкой тревогой", ["тревогой"], size=58, w=W)
    rows_y = 90 + Image.open(worry[0]).height - 2 * worry[1] + 20  # строки — под фактической высотой заголовка
    return [
        item(K.topic_card(f("topic"), "Тема ролика", "Приветствие и установление контакта",
                          "Первый шаг к доверию покупателя"), L, 90, 0.4, t_worry - 0.3),
        # блок "тревога"
        item(K.image_card(f("people"), f"{IMG}/s5_people.png", W), L, 90, t_worry, worry_end),
        item(worry, R, 90, t_worry, worry_end),
        item(K.icon_row(f("self"), f"{IMG}/s5_ic_self.png", "За себя"), R, rows_y, t_self, worry_end),
        item(K.icon_row(f("child"), f"{IMG}/s5_ic_child.png", "За ребёнка"), R, rows_y + 130, t_child, worry_end),
        item(K.icon_row(f("close"), f"{IMG}/s5_ic_close.png", "За близкого человека"), R, rows_y + 260,
             t_close, worry_end),
        # блок "контакт взглядом"
        item(K.image_card(f("eyes"), f"{IMG}/s5_eyes.png", W, "Контакт начинается со взгляда"),
             L, 90, t_eyes, end),
        item(K.headline(f("you"), "Главное", "Первым он ищет глазами вас", ["вас"], size=62, w=W),
             R, 90, t_eyes, t_cmp - 0.1),
        item(K.compare_row(f("c1"), f"{IMG}/s5_ic_showcase.png", "Витрина", False), R, 90, t_cmp, end),
        item(K.compare_row(f("c2"), f"{IMG}/s5_ic_price.png", "Ценник", False), R, 220, T("ценник"), end),
        item(K.compare_row(f("c3"), f"{IMG}/s5_ic_specialist.png", "Живой специалист", True), R, 350,
             T("живого"), end),
    ]


def scene2_items(words, t0):
    T = lambda w: t_of(words, w, t0) - t0  # noqa: E731
    f = lambda n: f"{TMP}/s2_{n}.png"  # noqa: E731
    (qw, qh), qpad = make_quote(f("quote"))
    make_header(f("header"))
    RX, RW = 800, 1020
    return [
        {"png": f("header"), "x": 100, "y": 70, "t_in": MOVE_T1, "t_out": None},
        item(K.image_card(f("greet"), f"{IMG}/s5_greeting.png", 640), 100, 230, MOVE_T1 + 0.2),
        item(K.headline(f("trifle"), "Кажется мелочью?", "На самом деле — сильный сигнал", ["сильный"],
                        size=54, w=RW), RX, 230, MOVE_T1 + 0.4, T("Я") - 0.05),
        {"png": f("quote"), "x": RX - qpad, "y": 230 - qpad, "t_in": T("Я"), "t_out": None},
        item(K.icon_row(f("r1"), f"{IMG}/s5_ic_phrase.png", "Одна тёплая фраза в первые секунды", w=RW, h=95,
                        num="01", num_color=S.BLUE, text_size=34), RX, 425, T("Одна")),
        item(K.icon_row(f("r2"), f"{IMG}/s5_ic_relief.png", "Напряжение спадает, человек выдыхает", w=RW, h=95,
                        num="02", num_color=S.LIGHT_BLUE, text_size=34), RX, 532, T("напряжение")),
        item(K.icon_row(f("r3"), f"{IMG}/s5_ic_talk.png", "Рассказывает спокойнее и подробнее", w=RW, h=95,
                        num="03", num_color=S.GREEN, text_size=34), RX, 639, T("начинает")),
    ]


def render_scene1(words, dur, out):
    items = scene1_items(words)
    inputs = ["-i", SCENES[0]["clip"]]
    fc = [f"[0:v]tpad=stop_mode=clone:stop_duration=1,trim=0:{dur},setpts=PTS-STARTPTS,"
          f"scale={G.FRAME_W}:{G.FRAME_H},fps={FPS},format=rgba[v0]"]
    last = overlay_items(fc, inputs, "v0", items, dur, 1)
    fc.append(f"[{last}]format=yuv420p[vo]")
    cap, last = C.build_filter("vo", caption_timeline(words, 0.0, dur), corner_start=10 ** 6)
    fc += cap
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", f"[{last}]", "-an", "-t", f"{dur}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-r", str(FPS), out])


def render_scene2(words, t0, dur, out):
    bg = f"{TMP}/s2_bg.png"
    make_background(bg)
    items = scene2_items(words, t0)
    fm = make_corner_frame(f"{TMP}/s2_frame.png")
    inputs = ["-i", SCENES[1]["clip"], "-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i", bg,
              "-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i", f"{TMP}/s2_frame.png"]
    a, b = MOVE_T0, MOVE_T1
    p = f"clip((t-{a})/({b}-{a})\\,0\\,1)"
    e = f"({p})*({p})*(3-2*({p}))"  # smoothstep
    fc = [
        f"[1:v]format=rgba,fps={FPS}[bg]",
        f"[0:v]tpad=stop_mode=clone:stop_duration=1,trim=0:{dur},setpts=PTS-STARTPTS,"
        f"scale={G.FRAME_W}:{G.FRAME_H},fps={FPS},"
        f"scale=w='{G.FRAME_W}+({G.CORNER_W}-{G.FRAME_W})*{e}':h='{G.FRAME_H}+({G.CORNER_H}-{G.FRAME_H})*{e}':eval=frame[av]",
        f"[2:v]format=rgba,fade=t=in:st={b - 0.1:.2f}:d=0.2:alpha=1[fr]",
    ]
    last = overlay_items(fc, inputs, "bg", items, dur, 3)
    fc.append(f"[{last}][av]overlay=x='{G.CORNER_X}*{e}':y='{G.CORNER_Y}*{e}':eval=frame[wa]")
    fc.append(f"[wa][fr]overlay=x={G.CORNER_X - fm}:y={G.CORNER_Y - fm}:enable='gte(t,{b - 0.1:.2f})',format=yuv420p[vb]")
    cap, last = C.build_filter("vb", caption_timeline(words, t0, t0 + dur), corner_start=0.0)
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
