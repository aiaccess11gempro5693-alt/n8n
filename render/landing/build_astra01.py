"""Блог @astra_seek, серия «Представь: ты — Скорпион», серия 1.

Ведущего нет: плоская мультанимация «Ночное небо» (кадры gpt-image-2 по борду
scratch/img/astra_board_night.png, движение — монтажом), сверху игровая панель
«♏ СКОРПИОН · ИНТУИЦИЯ / ДОВЕРИЕ», карточки в стиле блога (индиго, золото,
курсив Playfair), штампы, крупные субтитры с золотым ключевым словом, звуки и
тихая игриво-мистическая музыка из библиотеки HeyGen.

Входы: scratch/astra/ep1-trim.mp3, scratch/astra-ep1-whisper.json, scratch/img/astra1_*.png,
scratch/music/astra-music-full.mp3. Выход: render/landing/astra01-9x16.mp4.
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B  # noqa: E402
import sfx as SFX  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIO = f"{ROOT}/scratch/astra/ep1-trim.mp3"
WHISPER = f"{ROOT}/scratch/astra-ep1-whisper.json"
SCEN = f"{ROOT}/docs/scenarios/astra-signs/ep01-scorpio.md"
MUSIC = f"{ROOT}/scratch/music/astra-music-full.mp3"
OUT = f"{ROOT}/render/landing/astra01-9x16.mp4"
TMP = f"{ROOT}/render/landing/.astra01"
IMG = f"{ROOT}/scratch/img"
FONTS = f"{ROOT}/render/fonts"

W, H, FPS = 1080, 1920, 30
INK = (0x16, 0x10, 0x2A)
PANEL = (0x1E, 0x16, 0x38)
GOLD, LAV, CREAM, RED = (0xD9, 0xB2, 0x5F), (0xB9, 0xA6, 0xE0), (0xF3, 0xEB, 0xDD), (0xC8, 0x3E, 0x4D)
SAFE_TOP, SAFE_BOTTOM = 250, 1500


def F(size, kind="bold"):
    name = {"bold": "Montserrat-ExtraBold.ttf", "semi": "Montserrat-SemiBold.ttf",
            "serif": "PlayfairDisplay-BoldItalic.ttf"}[kind]
    return ImageFont.truetype(f"{FONTS}/{name}", size)


SYM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 64)


# ---------- слова и тайминги ----------

def script_words():
    s = open(SCEN, encoding="utf-8").read().split("## Текст для озвучки (eleven_v3)")[1].split("## Кадры")[0]
    return re.sub(r"\[[^\]]*\]", " ", s).split()


def timed():
    ws = json.load(open(WHISPER))["words"]
    text = script_words()
    a = [B.norm(w) for w in text]
    b = [B.norm(x["word"]) for x in ws]
    times = [None] * len(text)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = ws[blk.b + k]["start"]
    for i, t in enumerate(times):
        if t is None:
            prev = next((times[j] for j in range(i - 1, -1, -1) if times[j] is not None), 0.0)
            nxt = next((times[j] for j in range(i + 1, len(times)) if times[j] is not None), prev + 0.4)
            times[i] = prev + (nxt - prev) * 0.5
    return list(zip(text, times))


WORDS = None


def at(phrase, after=0.0):
    p = [B.norm(x) for x in phrase.split()]
    n = [B.norm(w) for w, _ in WORDS]
    for i in range(len(n) - len(p) + 1):
        if n[i:i + len(p)] == p and WORDS[i][1] >= after - 0.01:
            return WORDS[i][1]
    raise KeyError(phrase)


# ---------- графика ----------

def blank():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im, name):
    p = f"{TMP}/{name}.png"
    box = im.getbbox() or (0, 0, 2, 2)
    im.crop(box).save(p)
    return (p, box[0], box[1])


def spaced(d, xy, text, font, fill, gap=6, anchor="mm"):
    """Разреженные капители, как надписи над заголовками в блоге."""
    total = sum(d.textlength(c, font=font) for c in text) + gap * (len(text) - 1)
    x = xy[0] - total / 2 if anchor == "mm" else xy[0]
    for c in text:
        d.text((x, xy[1]), c, font=font, fill=fill, anchor="lm")
        x += d.textlength(c, font=font) + gap
    return total


def wrap(d, text, font, maxw):
    out, cur = [], ""
    for w in text.split():
        c = (cur + " " + w).strip()
        if d.textlength(c, font=font) > maxw and cur:
            out.append(cur)
            cur = w
        else:
            cur = c
    out.append(cur)
    return out


def frame(d, box, r=28):
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0, y0 + 8, x1, y1 + 8), r, fill=(0, 0, 0, 110))
    d.rounded_rectangle(box, r, fill=PANEL + (232,), outline=GOLD + (255,), width=3)
    d.rounded_rectangle((x0 + 9, y0 + 9, x1 - 9, y1 - 9), r - 8, outline=GOLD + (90,), width=1)


def star(d, cx, cy, r, fill):
    d.polygon([(cx, cy - r), (cx + r * .22, cy - r * .22), (cx + r, cy), (cx + r * .22, cy + r * .22),
               (cx, cy + r), (cx - r * .22, cy + r * .22), (cx - r, cy), (cx - r * .22, cy - r * .22)], fill=fill)


def hud(name, trust, trust_col=LAV, label=""):
    """Игровая панель: медальон ♏ + шкалы ИНТУИЦИЯ / ДОВЕРИЕ."""
    im, d = blank()
    x0, y0, x1, y1 = 120, 262, 960, 382
    frame(d, (x0, y0, x1, y1), 26)
    cx, cy = x0 + 66, (y0 + y1) / 2
    d.ellipse((cx - 42, cy - 42, cx + 42, cy + 42), outline=GOLD, width=3)
    d.text((cx, cy + 2), "♏", font=SYM, fill=GOLD, anchor="mm")
    spaced(d, (x0 + 130, y0 + 32), "СКОРПИОН", F(28, "semi"), CREAM, gap=4, anchor="lm")
    if label:
        lw = d.textlength(label, font=F(24, "semi")) + 40
        d.rounded_rectangle((x1 - 30 - lw, y0 + 14, x1 - 30, y0 + 50), 18, fill=GOLD)
        d.text((x1 - 30 - lw / 2, y0 + 32), label, font=F(24, "semi"), fill=INK, anchor="mm")
    bars = [("ИНТУИЦИЯ", 1.0, "100%", GOLD), ("ДОВЕРИЕ", trust / 100, f"{trust}%", trust_col)]
    for k, (lab, v, txt, col) in enumerate(bars):
        bx = x0 + 130 + k * 345
        by = y0 + 72
        d.text((bx, by), lab, font=F(20, "semi"), fill=LAV, anchor="lm")
        d.rounded_rectangle((bx, by + 18, bx + 220, by + 34), 8, outline=GOLD + (160,), width=2)
        if v > 0:
            d.rounded_rectangle((bx + 3, by + 21, bx + 3 + max(10, 214 * v), by + 31), 5, fill=col)
        d.text((bx + 232, by + 26), txt, font=F(26), fill=col, anchor="lm")
    return save(im, name)


def chip(name, text, y=410):
    im, d = blank()
    f = F(30, "semi")
    w = d.textlength(text, font=f) + len(text) * 4 + 70
    d.rounded_rectangle((W / 2 - w / 2, y, W / 2 + w / 2, y + 58), 29, fill=PANEL + (225,), outline=GOLD, width=2)
    spaced(d, (W / 2, y + 30), text, f, GOLD, gap=4)
    return save(im, name)


def title_card(name, kicker, lines, top=470, gold_line=None, size=72):
    """Карточка в стиле постов блога: капители сверху, курсив, золотая черта."""
    im, d = blank()
    fs = F(size, "serif")
    lh = int(size * 1.22)
    rows = []
    for ln in lines:
        rows += wrap(d, ln, fs, 800)
    h = 92 + lh * len(rows) + 70
    frame(d, (90, top, 990, top + h))
    spaced(d, (W / 2, top + 58), kicker, F(26, "semi"), GOLD, gap=5)
    y = top + 92
    for i, ln in enumerate(rows):
        col = GOLD if gold_line is not None and i == gold_line else CREAM
        d.text((W / 2, y + lh / 2), ln, font=fs, fill=col, anchor="mm")
        y += lh
    d.line((W / 2 - 70, y + 26, W / 2 - 16, y + 26), fill=GOLD, width=2)
    d.line((W / 2 + 16, y + 26, W / 2 + 70, y + 26), fill=GOLD, width=2)
    star(d, W / 2, y + 26, 9, GOLD)
    assert top >= 395 and top + h + 8 <= 1150, (name, top, h)
    return save(im, name)


def info_card(name, kicker, title, extra=None, top=405):
    im, d = blank()
    ft, fe = F(54, "serif"), F(38, "serif")
    rows = wrap(d, title, ft, 800)
    erows = wrap(d, extra, fe, 800) if extra else []
    h = 74 + 66 * len(rows) + (12 + 50 * len(erows) if erows else 0) + 30
    frame(d, (100, top, 980, top + h))
    spaced(d, (W / 2, top + 44), kicker, F(22, "semi"), GOLD, gap=5)
    y = top + 72
    for ln in rows:
        d.text((W / 2, y + 33), ln, font=ft, fill=CREAM, anchor="mm")
        y += 66
    if erows:
        y += 12
        for ln in erows:
            d.text((W / 2, y + 25), ln, font=fe, fill=GOLD, anchor="mm")
            y += 50
    assert top >= 395 and top + h + 8 <= 1150, (name, top, h)
    return save(im, name)


def bubble(name, text, top=520):
    """Реплика партнёра — светлое облачко с хвостиком."""
    im, d = blank()
    f = F(58, "serif")
    rows = wrap(d, text, f, 700)
    w = max(d.textlength(r, font=f) for r in rows) + 110
    h = 70 * len(rows) + 70
    x0 = W / 2 - w / 2
    d.rounded_rectangle((x0, top + 8, x0 + w, top + h + 8), 40, fill=(0, 0, 0, 100))
    d.rounded_rectangle((x0, top, x0 + w, top + h), 40, fill=CREAM + (250,))
    d.polygon([(x0 + w - 150, top + h - 2), (x0 + w - 90, top + h - 2), (x0 + w - 60, top + h + 50)], fill=CREAM)
    y = top + 35
    for r in rows:
        d.text((W / 2, y + 35), r, font=f, fill=INK, anchor="mm")
        y += 70
    return save(im, name)


def stamp(name, text, cy=640, rot=-8, col=RED):
    f = F(70)
    tmp = Image.new("RGBA", (900, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    tw = d.textlength(text, font=f)
    x0 = 450 - tw / 2 - 40
    d.rounded_rectangle((x0, 60, 900 - x0, 200), 18, outline=col, width=9)
    d.rounded_rectangle((x0 + 14, 74, 900 - x0 - 14, 186), 12, outline=col + (150,), width=3)
    d.text((450, 130), text, font=f, fill=col, anchor="mm")
    tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=True)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.alpha_composite(tmp, (int(W / 2 - tmp.width / 2), int(cy - tmp.height / 2)))
    return save(im, name)


def subtitle(name, text, key):
    im, d = blank()
    f = F(62)
    words = text.upper().split()
    lines, cur = [], []
    for w in words:
        if cur and d.textlength(" ".join(cur + [w]), font=f) > 900:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    lh = 78
    y = 1330 - lh * (len(lines) - 1) / 2
    for ln in lines:
        total = d.textlength(" ".join(ln), font=f)
        x = W / 2 - total / 2
        for w in ln:
            col = GOLD if B.norm(w) == key else (255, 255, 255)
            d.text((x, y), w, font=f, fill=col, anchor="lm", stroke_width=7, stroke_fill=INK)
            x += d.textlength(w + " ", font=f)
        y += lh
    assert 1330 - lh * len(lines) / 2 - 10 >= 1160 and y - lh / 2 + 40 <= SAFE_BOTTOM, text
    return save(im, name)


KEYS = {"скорпион", "новолуние", "тайно", "соврёт", "сто", "три", "праздникам", "сама", "секретная", "пятницу",
        "кафе", "следишь", "помнишь", "четверг", "навсегда", "переписки", "вычёркиваешь", "сжигаешь",
        "жизнь", "обид", "знак"}


def key_of(text):
    ws = [B.norm(w) for w in text.split()]
    hit = [w for w in ws if w in {B.norm(k) for k in KEYS}]
    return hit[0] if hit else max(ws, key=len)


# ---------- фон ----------

def scene_clip(i, img, dur, zoom=(1.05, 1.12), pan=0.0, focus=0.5):
    """Кадр 2:3 → 9:16, медленный наезд/отъезд и панорама. Зум ≥1.05 прячет тонкую
    рамку, которую gpt-image-2 иногда рисует по краю."""
    src = Image.open(f"{IMG}/{img}.png").convert("RGB")
    w, h = src.size
    cw = int(h * 9 / 16)
    cx = int((w - cw) * focus)
    src.crop((cx, 0, cx + cw, h)).resize((2160, 3840), Image.LANCZOS).save(f"{TMP}/bg{i}.png")
    n = int(round(dur * FPS))
    z0, z1 = zoom
    z = f"{z0}+({z1}-{z0})*on/{n}"
    x = f"(iw-iw/zoom)/2+{pan}*(iw-iw/zoom)/2*(2*on/{n}-1)"
    out = f"{TMP}/sc{i}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", f"{TMP}/bg{i}.png", "-vf",
                    f"zoompan=z='{z}':x='{x}':y='(ih-ih/zoom)*0.2':d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
                    "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out], check=True)
    return out


def main():
    global WORDS
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP)
    WORDS = timed()
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  AUDIO], capture_output=True, text=True).stdout)

    t_watch = at("Досмотри")
    t_seven = at("Семь утра")
    t_intu = at("Интуиция")
    t_nine = at("Девять утра")
    t_conf = at("признаётся")
    t_lunch = at("Обед")
    t_rest = at("Остальное")
    t_eve = at("Вечер Дома")
    t_quote = at("Я в пятницу")
    t_ok = at("Хорошо")
    t_five = at("Через пять минут")
    t_follow = at("Ты что следишь")
    t_all = at("Ты же помнишь")
    t_years = at("четыре года назад")
    t_love = at("Зато если")
    t_betray = at("А если предали")
    t_cross = at("вычёркиваешь")
    t_23 = at("Одиннадцать вечера", after=t_betray)
    t_list = at("берёшь лист")
    t_burn = at("И сжигаешь")
    t_secret = at("Вот она")
    t_grudge = at("Но список обид")
    t_know = at("Узнаёшь себя")
    print({k: round(v, 2) for k, v in locals().items() if k.startswith("t_")})

    plan = [
        ("astra1_moon", 0.0, (1.12, 1.05), 0.0, 0.5),
        ("astra1_bed", t_seven - 0.15, (1.05, 1.13), 0.0, 0.45),
        ("astra1_office", t_nine - 0.15, (1.05, 1.12), 0.5, 0.5),
        ("astra1_lunch", t_lunch - 0.15, (1.13, 1.05), 0.0, 0.5),
        ("astra1_partner", t_eve - 0.15, (1.05, 1.12), -0.5, 0.6),
        ("astra1_board", t_five - 0.15, (1.05, 1.13), 0.0, 0.45),
        ("astra1_archive", t_all - 0.15, (1.06, 1.14), 0.4, 0.45),
        ("astra1_protect", t_love - 0.15, (1.12, 1.05), 0.0, 0.5),
        ("astra1_cross", t_betray - 0.15, (1.05, 1.14), 0.0, 0.5),
        ("astra1_burn", t_23 - 0.15, (1.05, 1.12), 0.4, 0.55),
        ("astra1_drawer", t_secret - 0.15, (1.05, 1.11), 0.0, 0.5),
    ]
    starts = [p[1] for p in plan] + [total]
    clips = [scene_clip(i, p[0], starts[i + 1] - p[1] + 0.3, *p[2:]) for i, p in enumerate(plan)]
    inputs, fc, last = [], [], "[0:v]"
    for c in clips:
        inputs += ["-i", c]
    for i in range(1, len(clips)):
        lab = f"[x{i}]"
        fc.append(f"{last}[{i}:v]xfade=transition=fade:duration=0.3:offset={starts[i] - 0.15:.3f}{lab}")
        last = lab
    bgv = f"{TMP}/bg.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", last,
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", bgv], check=True)

    ov = []   # (png, t0, t1, fade_in, kind) — kind: card/stamp/hud/sub
    ov.append((title_card("hook", "НОВОЛУНИЕ · 9 НОЯБРЯ", ["Представь:", "ты — Скорпион"], top=430, gold_line=1),
               0.25, t_watch - 0.05, 0.3, "card"))
    ov.append((title_card("promise", "ДОСМОТРИ ДО КОНЦА", ["В 23:00 —", "тайный ритуал"], top=430, gold_line=1),
               t_watch, t_seven - 0.1, 0.25, "card"))
    for nm, tr, lab, a, b in [("h07", 3, "07:00 · УТРО", t_seven, t_nine), ("h09", 3, "09:00 · ОФИС", t_nine, t_lunch),
                              ("h13", 3, "13:00 · ОБЕД", t_lunch, t_eve), ("h19", 3, "19:00 · ДОМА", t_eve, t_five),
                              ("h19b", 0, "19:00 · ДОМА", t_five, t_all), ("hx", 0, "", t_all, t_23),
                              ("h23", 0, "23:00 · НОВОЛУНИЕ", t_23, t_secret), ("hy", 0, "", t_secret, total)]:
        ov.append((hud(nm, tr, RED if tr == 0 else LAV, lab), a, b, 0.3 if nm == "h07" else 0.0, "hud"))
    ov.append((info_card("conf", "РЕЗУЛЬТАТ ДОПРОСА", "Признание получено", "без единого вопроса"),
               t_conf, t_lunch - 0.1, 0.2, "card"))
    ov.append((stamp("secret", "СЕКРЕТНО", cy=520), t_rest, t_eve - 0.1, 0.0, "stamp"))
    ov.append((bubble("fri", "«Я в пятницу задержусь»"), t_quote, t_five - 0.05, 0.2, "card"))
    ov.append((info_card("inv", "РАССЛЕДОВАНИЕ", "5 минут", "с кем · где · до скольки кафе"),
               t_five, t_all - 0.1, 0.2, "card"))
    ov.append((info_card("arch", "АРХИВ ПАМЯТИ", "Помнишь всё", "4 года назад · четверг · 21:00"),
               t_years, t_love - 0.1, 0.2, "card"))
    ov.append((info_card("love", "ЕСЛИ ЛЮБИШЬ", "Это навсегда", "в огонь · в воду · в переписки"),
               t_love, t_betray - 0.1, 0.2, "card"))
    ov.append((info_card("cross", "ЕСЛИ ПРЕДАЛИ", "Тихо вычеркнуть", "без крика и сцен"),
               t_cross, t_23 - 0.1, 0.2, "card"))
    ov.append((info_card("ritual", "РИТУАЛ НОВОЛУНИЯ", "Написать и сжечь", "всё, что пора отпустить"),
               t_list, t_secret - 0.1, 0.2, "card"))
    ov.append((title_card("tain", "ТАЙНА СКОРПИОНА", ["Каждый раз —", "новая жизнь"], top=405, gold_line=1, size=58),
               t_secret, t_grudge - 0.05, 0.25, "card"))
    ov.append((stamp("grudge", "ОБИДЫ: СОХРАНЕНЫ", cy=520, rot=6), t_grudge + 0.6, t_know - 0.1, 0.0, "stamp"))
    ov.append((title_card("end", "СЛЕДУЮЩАЯ СЕРИЯ — ТВОЯ", ["Узнаёшь себя?", "Напиши свой знак"], top=405,
                          gold_line=1, size=58), t_know, total, 0.25, "card"))

    subs = B.chunks(WORDS, total)
    for k, s in enumerate(subs):
        ov.append((subtitle(f"s{k}", s["text"], key_of(s["text"])), s["t0"], s["t1"], 0.0, "sub"))

    # карточки и штампы в центре не пересекаются по времени между собой
    mid = sorted((a, b, os.path.basename(p)) for (p, _x, _y), a, b, _f, k in ov if k in ("card", "stamp"))
    for (a0, a1, n0), (b0, b1, n1) in zip(mid, mid[1:]):
        assert b0 >= a1 - 0.05, ("наложились", n0, n1, a0, a1, b0, b1)
    # всё в безопасной зоне 250–1500
    for (p, x, y), *_ in ov:
        hgt = Image.open(p).height
        assert y >= SAFE_TOP - 5 and y + hgt <= SAFE_BOTTOM + 15, (p, y, hgt)

    inputs = ["-i", bgv]
    fc = []
    last = "[0:v]"
    for i, ((p, ox, oy), a, b, fin, _k) in enumerate(ov):
        inputs += ["-loop", "1", "-t", f"{total:.3f}", "-i", p]
        src = f"[{i + 1}:v]format=rgba"
        if fin:
            src += f",fade=in:st={a:.3f}:d={fin}:alpha=1"
        fc.append(src + f"[o{i}]")
        fc.append(f"{last}[o{i}]overlay={ox}:{oy}:enable='between(t,{a:.3f},{b:.3f})'[v{i + 1}]")
        last = f"[v{i + 1}]"

    ev = [(0.25, "chime", 0.45), (t_watch, "riser", 0.3), (t_seven, "whoosh", 0.35), (t_intu, "ding", 0.4),
          (t_nine, "whoosh", 0.3), (t_conf, "pop", 0.5), (t_lunch, "whoosh", 0.3), (t_rest, "stamp", 0.55),
          (t_eve, "whoosh", 0.3), (t_quote, "pop", 0.45), (t_ok, "tick", 0.3), (t_five, "hit", 0.45),
          (t_follow, "click", 0.4), (t_years, "pop", 0.45), (t_love, "chime", 0.35), (t_cross, "glitch", 0.35),
          (t_23 - 0.6, "riser", 0.35), (t_23, "bass", 0.5), (t_burn, "whoosh", 0.35), (t_secret, "chime", 0.4),
          (t_grudge + 0.6, "stamp", 0.55), (t_know, "pop", 0.5)]
    mixed = SFX.mix(AUDIO, ev, f"{TMP}/mix.wav", f"{TMP}/sfx", bed_gain=0.14, total=total,
                    bed_fn=SFX.music_bed(MUSIC))
    inputs += ["-i", mixed]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
                    "-map", last, "-map", f"{len(ov) + 1}:a", "-t", f"{total:.3f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT], check=True)
    print(OUT, round(total, 1), "c,", len(subs), "субтитров")


if __name__ == "__main__":
    main()
