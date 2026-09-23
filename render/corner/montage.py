"""Общая механика монтажа формата "аватар на весь кадр ↔ аватар в углу +
плашка" (CLAUDE.md, 23.09.2026 (7)-(10)). Содержание конкретного ролика
(какие блоки, картинки, заголовки, на каких словах) — в отдельном
скрипте ролика (например build_scenario5.py), здесь только механика:

  - тайминги слов: сценарий ↔ whisper (word_times), статичные субтитры
    по предложениям (caption_timeline);
  - наложение элементов визуального слоя: fade + подъём при появлении,
    fade при исчезновении (item / overlay_items);
  - типы сцен: mode="full" (аватар на весь кадр, элементы поверх по бокам)
    и mode="corner" (светлый фон брендбука, аватар в правом нижнем углу);
    enter="shrink" — аватар уезжает с полного кадра в угол, enter="grow" —
    возвращается из угла на весь кадр, enter="none" — без перехода.

Правило визуального слоя (23.09.2026 (10)): в кадре одновременно — только
элементы одной мысли; блок держится, пока диктор его раскрывает; ничего
короче ~2 с. Элемент без явного t_out сам гаснет в конце сцены.
"""
import difflib
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFilter

from . import brand_style as S
from . import geometry as G
from . import static_captions as C

FPS = 25
MOVE_D = 0.9          # длительность съезда/возврата аватара
APPEAR_D = 0.35       # появление элемента (fade + подъём)
APPEAR_RISE = 24
FADE_OUT = 0.3
NAVY = (15, 45, 125, 255)


def run(cmd):
    subprocess.run(cmd, check=True)


# ---------------------------------------------------------------- тайминги

def norm(w):
    return re.sub(r"[^\w]+", "", w.lower().replace("ё", "е"))


def scenario_paragraphs(path):
    body = open(path, encoding="utf-8").read().split("\n---\n")[1]
    return [C.strip_emotion_tags(p) for p in body.strip().split("\n\n") if p.strip()]


def word_times(clean_text, whisper_words):
    """Каждому слову сценария — время начала из whisper (выравнивание
    difflib; для слов, которые whisper услышал иначе — время соседа)."""
    src = clean_text.split()
    a = [norm(w) for w in src]
    b = [norm(w["word"]) for w in whisper_words]
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


def caption_timeline(words, dur):
    """Статичные субтитры: чанки ≤2 строк, чанк не пересекает границу
    предложения; висит от своего первого слова до первого слова
    следующего. words — [(слово, время от начала сцены)]."""
    max_w = G.SUBTITLE_W - C.ACCENT_BAR_W - C.PAD_LEFT - C.PAD_RIGHT
    sentences, cur = [], []
    for w, _ in words:
        cur.append(w)
        if re.search(r"[.!?…»]$", w):
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)
    chunks = []
    for sent in sentences:
        sch = C.wrap_into_chunks(" ".join(sent), max_w)
        if len(sch) > 1:
            # делим предложение на части поровну, чтобы не оставался "хвост"
            # из одного слова (напр. "минуту.") отдельной фразой на экране
            n, k = len(sch), len(sent)
            groups = [sent[round(i * k / n):round((i + 1) * k / n)] for i in range(n)]
            even = [C.wrap_into_chunks(" ".join(g), max_w) for g in groups]
            if all(len(e) == 1 for e in even):
                sch = [e[0] for e in even]
        chunks += sch
    tl, i = [], 0
    for ch in chunks:
        tl.append({"lines": ch, "start": max(0.0, words[i][1])})
        i += sum(len(line) for line in ch)
    for k, c in enumerate(tl):
        c["end"] = tl[k + 1]["start"] if k + 1 < len(tl) else dur
        c["start"], c["end"] = round(c["start"], 3), round(c["end"], 3)
    tl[0]["start"] = 0.0
    return tl


def finder(words):
    """T(слово, after=0) — время первого вхождения слова не раньше after."""
    def T(needle, after=0.0):
        n = norm(needle)
        for w, t in words:
            if norm(w) == n and t >= after:
                return t
        raise KeyError(needle)
    return T


# ---------------------------------------------------------------- графика сцены

def make_background(path):
    """Светлый фон брендбука + мягкие декоративные круги."""
    img = Image.new("RGBA", (G.FRAME_W, G.FRAME_H), S.LIGHT_BG)
    deco = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(deco)
    d.ellipse([1500, -260, 2140, 380], fill=(47, 128, 237, 26))
    d.ellipse([-220, 760, 260, 1240], fill=(39, 174, 96, 20))
    img = Image.alpha_composite(img, deco.filter(ImageFilter.GaussianBlur(2)))
    img.save(path)
    return path


def section_header(path, kicker, title):
    """Заголовок раздела на плашке: зелёная полоса + киккер + крупный текст."""
    img = Image.new("RGBA", (1700, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 6, 8, 150], 4, fill=S.GREEN)
    d.text((34, 0), kicker.upper(), font=S.font(S.F_SEMIBOLD, 28), fill=S.LIGHT_BLUE)
    d.text((32, 44), title, font=S.font(S.F_HEADLINE, 76), fill=NAVY)
    img.save(path)
    return path, 0


def quote_card(path, kicker, text, w=1020, h=170, size=50, color=S.BLUE):
    pad = 30
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 8, pad + w, pad + h + 8], 28, fill=(20, 40, 90, 40))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], 28, fill=color)
    x0 = pad + 56
    d.text((x0 - 8, pad + 8), "“", font=S.font(S.F_HEADLINE, 150), fill=(255, 255, 255, 70))
    d.text((x0 + 80, pad + 30), kicker.upper(), font=S.font(S.F_SEMIBOLD, 24), fill=(214, 230, 255, 255))
    d.text((x0 + 80, pad + 70), text, font=S.font(S.F_HEADLINE, size), fill=S.WHITE)
    img.save(path)
    return path, pad


def make_corner_frame(path, radius=22, border=5):
    """Рамка поверх аватара в углу: тень, углы вне скругления — цвет фона,
    белая обводка; внутри прозрачно."""
    m = 40
    w, h = G.CORNER_W + 2 * m, G.CORNER_H + 2 * m
    box = [m, m, m + G.CORNER_W - 1, m + G.CORNER_H - 1]
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([m, m + 10, m + G.CORNER_W, m + G.CORNER_H + 10], radius,
                                         fill=(20, 40, 90, 70))
    img = sh.filter(ImageFilter.GaussianBlur(16))
    ImageDraw.Draw(img).rectangle(box, fill=S.LIGHT_BG)
    ImageDraw.Draw(img).rounded_rectangle(box, radius, fill=(0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle(box, radius, outline=S.WHITE, width=border)
    img.save(path)
    return m


# ---------------------------------------------------------------- рендер сцены

def item(made, x, y, t_in, t_out=None):
    """made — (png, pad) из cards.* / section_header / quote_card; x/y —
    позиция видимой части; t_out=None — гаснет в конце сцены."""
    png, pad = made
    return {"png": png, "x": x - pad, "y": y - pad, "t_in": t_in, "t_out": t_out}


def _overlay_items(fc, inputs, prev, items, dur, first_idx):
    for k, it in enumerate(items):
        idx = first_idx + k
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i", it["png"]]
        t = it["t_in"]
        t_out = it["t_out"] if it["t_out"] is not None else dur - 0.02
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={t:.2f}:d={APPEAR_D}:alpha=1,"
                  f"fade=t=out:st={t_out - FADE_OUT:.2f}:d={FADE_OUT}:alpha=1[it{idx}]")
        rise = f"{APPEAR_RISE}*(1-clip((t-{t:.2f})/{APPEAR_D}\\,0\\,1))"
        fc.append(f"[{prev}][it{idx}]overlay=x={it['x']}:y='{it['y']}+{rise}':"
                  f"enable='between(t,{t:.2f},{t_out:.2f})'[o{idx}]")
        prev = f"o{idx}"
    return prev


def render_scene(clip, dur, words, mode, enter, items, out, tmp):
    """mode: "full" | "corner"; enter: "none" | "shrink" | "grow"."""
    bg = make_background(f"{tmp}/_bg.png")
    fm = make_corner_frame(f"{tmp}/_frame.png")
    loop = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i"]
    inputs = ["-i", clip, *loop, bg, *loop, f"{tmp}/_frame.png"]
    base = (f"[0:v]tpad=stop_mode=clone:stop_duration=1,trim=0:{dur},setpts=PTS-STARTPTS,"
            f"scale={G.FRAME_W}:{G.FRAME_H},fps={FPS}")
    p = f"clip(t/{MOVE_D}\\,0\\,1)"
    e = f"({p})*({p})*(3-2*({p}))"                      # smoothstep 0→1 за MOVE_D
    fc = []
    if not (mode == "full" and enter == "none"):
        fc.append(f"[1:v]format=rgba,fps={FPS}[bg]")
    cw, ch, cx, cy = G.CORNER_W, G.CORNER_H, G.CORNER_X, G.CORNER_Y
    fw, fh = G.FRAME_W, G.FRAME_H

    if mode == "corner":
        if enter == "shrink":
            fc.append(f"{base},scale=w='{fw}+({cw}-{fw})*{e}':h='{fh}+({ch}-{fh})*{e}':eval=frame[av]")
            pos = f"x='{cx}*{e}':y='{cy}*{e}':eval=frame"
            fr_in = MOVE_D - 0.1
        else:
            fc.append(f"{base},scale={cw}:{ch}[av]")
            pos, fr_in = f"x={cx}:y={cy}", 0.0
        fc.append(f"[2:v]format=rgba,fade=t=in:st={fr_in:.2f}:d=0.2:alpha=1[fr]")
        last = _overlay_items(fc, inputs, "bg", items, dur, 3)
        fc.append(f"[{last}][av]overlay={pos}[wa]")
        fc.append(f"[wa][fr]overlay=x={cx - fm}:y={cy - fm}:enable='gte(t,{fr_in:.2f})',format=yuv420p[vb]")
        corner_start = 0.0
    else:
        if enter == "grow":
            fc.append(f"{base},scale=w='{cw}+({fw}-{cw})*{e}':h='{ch}+({fh}-{ch})*{e}':eval=frame[av]")
            fc.append(f"[2:v]format=rgba,fade=t=out:st=0:d=0.2:alpha=1[fr]")
            fc.append(f"[bg][av]overlay=x='{cx}*(1-{e})':y='{cy}*(1-{e})':eval=frame[g0]")
            fc.append(f"[g0][fr]overlay=x={cx - fm}:y={cy - fm}:enable='lt(t,0.2)'[va]")
        else:
            fc.append(f"{base},format=rgba[va]")
        last = _overlay_items(fc, inputs, "va", items, dur, 3)
        fc.append(f"[{last}]format=yuv420p[vb]")
        corner_start = 10 ** 6
    cap, last = C.build_filter("vb", caption_timeline(words, dur), corner_start=corner_start)
    fc += cap
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", f"[{last}]", "-an", "-t", f"{dur}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-r", str(FPS), out])


def concat(parts, audio, out, tmp):
    lst = f"{tmp}/concat.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-shortest", out])
