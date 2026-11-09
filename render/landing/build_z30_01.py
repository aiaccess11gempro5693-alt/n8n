"""Серия «Представь: у тебя 0 ₽ и 30 дней», серия 1 «День первый: ноль».

Ведущего нет: плоская анимация «Ночной город» (кадры gpt-image-2, движение —
монтажом: медленный наезд/панорама, мягкие склейки), сверху игровая панель
«ДЕНЬ 1/30 · БАЛАНС», карточка правила с состояниями, крупные субтитры с
салатовым ключевым словом, звуки и тревожный подклад.

Входы: scratch/z30/ep1-trim.mp3, scratch/z30-ep1-whisper.json, scratch/img/z30e1_*.png,
scratch/music/z30-music.wav. Выход: render/landing/z30-01-9x16.mp4.
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B  # noqa: E402  (нарезка субтитров по фразам)
import sfx as SFX  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIO = f"{ROOT}/scratch/z30/ep1-trim.mp3"
WHISPER = f"{ROOT}/scratch/z30-ep1-whisper.json"
SCEN = f"{ROOT}/docs/scenarios/zero-30/ep01.md"
MUSIC = f"{ROOT}/scratch/music/z30-music.wav"
OUT = f"{ROOT}/render/landing/z30-01-9x16.mp4"
TMP = f"{ROOT}/render/landing/.z30-01"
IMG = f"{ROOT}/scratch/img"
FB = f"{ROOT}/render/fonts/Montserrat-Bold.ttf"   # в ExtraBold/SemiBold нет знака ₽
FM = FB

W, H, FPS = 1080, 1920, 30
BG1, BG2 = (0x24, 0x21, 0x2F), (0x3A, 0x35, 0x50)
YEL, LIME, RED, WHITE = (0xE8, 0xB0, 0x4B), (0xC6, 0xF4, 0x32), (0xFF, 0x5A, 0x4E), (255, 255, 255)
SAFE_TOP, SAFE_BOTTOM = 250, 1500


def F(size, bold=True):
    return ImageFont.truetype(FB if bold else FM, size)


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
    """Время начала первого вхождения фразы (последовательности слов) после after."""
    p = [B.norm(x) for x in phrase.split()]
    n = [B.norm(w) for w, _ in WORDS]
    for i in range(len(n) - len(p) + 1):
        if n[i:i + len(p)] == p and WORDS[i][1] >= after - 0.01:
            return WORDS[i][1]
    raise KeyError(phrase)


# ---------- графика ----------

def rbox(d, xy, r, fill, outline=None, width=0):
    d.rounded_rectangle(xy, r, fill=fill, outline=outline, width=width)


def save(im, name):
    """Слой обрезается по содержимому — в итоговом графе накладывается со смещением
    (полноэкранные слои с прозрачностью замедляли рендер в разы)."""
    p = f"{TMP}/{name}.png"
    box = im.getbbox() or (0, 0, 2, 2)
    im.crop(box).save(p)
    return (p, box[0], box[1])


def hud(name, balance, red=False):
    """Игровая панель: ДЕНЬ 1/30 · БАЛАНС."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 150, 262, 930, 372
    rbox(d, (x0, y0 + 6, x1, y1 + 6), 26, (0, 0, 0, 110))
    rbox(d, (x0, y0, x1, y1), 26, (0x1B, 0x19, 0x26, 235), outline=(0x55, 0x50, 0x70, 255), width=3)
    # кошелёк
    d.rounded_rectangle((x0 + 30, y0 + 30, x0 + 86, y0 + 80), 10, fill=(0x55, 0x50, 0x70, 255))
    d.rounded_rectangle((x0 + 62, y0 + 44, x0 + 92, y0 + 66), 6, fill=YEL)
    d.text((x0 + 112, (y0 + y1) / 2), "ДЕНЬ 1/30", font=F(44), fill=WHITE, anchor="lm")
    mid = x0 + 450
    d.line((mid, y0 + 22, mid, y1 - 22), fill=(0x55, 0x50, 0x70, 255), width=3)
    d.text((mid + 30, y0 + 30), "БАЛАНС", font=F(24, False), fill=(0xB8, 0xB2, 0xCC), anchor="lm")
    d.text((mid + 30, y0 + 72), balance, font=F(46), fill=RED if red else LIME, anchor="lm")
    return save(im, name)


def card(name, kicker, title, extra=None, extra_col=LIME, top=420, kcol=LIME):
    """Карточка правила/квеста. kicker — маленький ярлык, title — главная строка,
    extra — нижняя плашка-результат (состояние той же карточки)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tf = F(58)
    lines = wrap(d, title, tf, 820)
    h = 70 + 70 * len(lines) + (96 if extra else 0) + 30
    x0, x1 = 110, 970
    rbox(d, (x0, top + 8, x1, top + h + 8), 30, (0, 0, 0, 120))
    rbox(d, (x0, top, x1, top + h), 30, (0x1B, 0x19, 0x26, 240), outline=(0x55, 0x50, 0x70, 255), width=3)
    kw = d.textlength(kicker, font=F(30)) + 44
    rbox(d, (W / 2 - kw / 2, top - 26, W / 2 + kw / 2, top + 26), 22, kcol)
    d.text((W / 2, top), kicker, font=F(30), fill=BG1, anchor="mm")
    y = top + 60
    for ln in lines:
        d.text((W / 2, y + 35), ln, font=tf, fill=WHITE, anchor="mm")
        y += 70
    if extra:
        y += 14
        ew = d.textlength(extra, font=F(44)) + 60
        rbox(d, (W / 2 - ew / 2, y, W / 2 + ew / 2, y + 72), 20, extra_col)
        d.text((W / 2, y + 36), extra, font=F(44), fill=BG1, anchor="mm")
    assert top - 26 >= 390 and top + h + 8 <= 1150, (name, top, h)
    return save(im, name)


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


def big_zero(name):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = F(104)
    a, b = "0 ₽ ", "НА КАРТЕ"
    x = W / 2 - d.textlength(a + b, font=f) / 2
    d.text((x, 470), a, font=f, fill=LIME, anchor="lm", stroke_width=8, stroke_fill=BG1)
    d.text((x + d.textlength(a, font=f), 470), b, font=f, fill=WHITE, anchor="lm", stroke_width=8, stroke_fill=BG1)
    return save(im, name)


def notif(name):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 110, 430, 970, 640
    rbox(d, (x0, y0 + 8, x1, y1 + 8), 34, (0, 0, 0, 140))
    rbox(d, (x0, y0, x1, y1), 34, (0xF4, 0xF2, 0xF8, 250))
    d.ellipse((x0 + 34, y0 + 52, x0 + 134, y0 + 152), fill=RED)
    d.rectangle((x0 + 60, y0 + 96, x0 + 108, y0 + 108), fill=WHITE)
    d.text((x0 + 164, y0 + 70), "Списание по подписке", font=F(42), fill=BG1, anchor="lm")
    d.text((x0 + 164, y0 + 140), "Баланс:", font=F(34), fill=(0x6B, 0x67, 0x80), anchor="lm")
    d.text((x1 - 40, y0 + 140), "−399 ₽", font=F(58), fill=RED, anchor="rm")
    return save(im, name)


def flash(name, col, a):
    im = Image.new("RGBA", (W, H), col + (a,))
    return save(im, name)


def end_card(name, line1, line2, col=LIME):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rbox(d, (90, 470, 990, 900), 40, (0x1B, 0x19, 0x26, 235), outline=(0x55, 0x50, 0x70, 255), width=3)
    y = 560
    for ln in wrap(d, line1, F(70), 800):
        d.text((W / 2, y), ln, font=F(70), fill=WHITE, anchor="mm")
        y += 84
    d.text((W / 2, y + 40), line2, font=F(76), fill=col, anchor="mm")
    return save(im, name)


def subtitle(name, text, key):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = F(66)
    words = text.upper().split()
    lines, cur = [], []
    for w in words:
        if cur and d.textlength(" ".join(cur + [w]), font=f) > 900:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    lh = 80
    y = 1330 - lh * (len(lines) - 1) / 2
    for ln in lines:
        total = d.textlength(" ".join(ln), font=f)
        x = W / 2 - total / 2
        for w in ln:
            col = LIME if B.norm(w) == key else WHITE
            d.text((x, y), w, font=f, fill=col, anchor="lm", stroke_width=7, stroke_fill=(0x14, 0x12, 0x1C))
            x += d.textlength(w + " ", font=f)
        y += lh
    assert 1330 - lh * len(lines) / 2 - 10 >= 1160 and y - lh / 2 + 40 <= SAFE_BOTTOM, text
    return save(im, name)


def key_of(text):
    ws = [w for w in text.split()]
    num = [w for w in ws if re.search(r"\d|ноль|тысяч|рубл|минус", w.lower())]
    pool = num or ws
    return B.norm(max(pool, key=lambda w: len(B.norm(w))))


# ---------- фон: кадры с движением ----------

def scene_clip(i, img, dur, zoom=(1.0, 1.09), pan=0.0, focus=0.5):
    """Кадр 2:3 → обрезка 9:16 → медленный наезд/отъезд и лёгкая панорама."""
    src = Image.open(f"{IMG}/{img}.png").convert("RGB")
    w, h = src.size
    cw = int(h * 9 / 16)
    cx = int((w - cw) * focus)
    src.crop((cx, 0, cx + cw, h)).resize((2160, 3840), Image.LANCZOS).save(f"{TMP}/bg{i}.png")
    n = int(round(dur * FPS))
    z0, z1 = zoom
    z = f"{z0}+({z1}-{z0})*on/{n}"
    x = f"(iw-iw/zoom)/2+{pan}*(iw-iw/zoom)/2*(2*on/{n}-1)"
    y = "(ih-ih/zoom)/2"
    out = f"{TMP}/sc{i}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", f"{TMP}/bg{i}.png", "-vf",
                    f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
                    "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out], check=True)
    return out


def main():
    global WORDS
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP)
    WORDS = timed()
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  AUDIO], capture_output=True, text=True).stdout)

    t_card0 = at("на карте")
    t_zarp = at("До зарплаты")
    t_task = at("одна задача")
    t_watch = at("Досмотри")
    t_day = at("День первый")
    t_r1 = at("Правило номер один")
    t_week = at("Это неделя еды")
    t_r2 = at("Правило номер два")
    t_month = at("За месяц")
    t_r3 = at("Правило номер три")
    t_old = at("Старый телефон")
    t_photo = at("Фото объявление")
    t_buyer = at("Покупатель")
    t_eve = at("Вечер")
    t_vib = at("И тут")
    t_spis = at("Списание по подписке")
    t_forgot = at("Подписка про которую")
    t_trap = at("Вот она")
    t_q = at("Что ты сделаешь")
    t_tom = at("А завтра")
    print({k: round(v, 2) for k, v in locals().items() if k.startswith("t_")})

    # сцены фона: (кадр, начало, наезд, панорама, фокус)
    plan = [
        ("z30e1_wake", 0.0, (1.0, 1.10), 0.0, 0.45),
        ("z30e1_phone", t_card0 - 0.2, (1.06, 1.0), 0.0, 0.5),
        ("z30e1_wake", t_zarp - 0.1, (1.12, 1.0), 0.6, 0.65),
        ("z30e1_kitchen", t_day - 0.1, (1.0, 1.08), 0.0, 0.55),
        ("z30e1_walk", t_r2 - 0.1, (1.04, 1.04), 0.9, 0.5),
        ("z30e1_stuff", t_r3 - 0.1, (1.0, 1.08), -0.5, 0.5),
        ("z30e1_photo", t_photo - 0.1, (1.0, 1.10), 0.0, 0.45),
        ("z30e1_evening", t_eve - 0.2, (1.08, 1.0), 0.0, 0.5),
        ("z30e1_shock", t_vib - 0.1, (1.0, 1.12), 0.0, 0.5),
        ("z30e1_evening", t_q - 0.2, (1.0, 1.06), 0.0, 0.5),
    ]
    starts = [p[1] for p in plan] + [total]
    clips = [scene_clip(i, p[0], starts[i + 1] - p[1] + 0.3, p[2], p[3], p[4]) for i, p in enumerate(plan)]
    # склейка с короткой растворкой 0.3 с
    inputs, fc, last, off = [], [], "[0:v]", 0.0
    for c in clips:
        inputs += ["-i", c]
    for i in range(1, len(clips)):
        off = starts[i] - 0.15
        lab = f"[x{i}]"
        fc.append(f"{last}[{i}:v]xfade=transition=fade:duration=0.3:offset={off:.3f}{lab}")
        last = lab
    bgv = f"{TMP}/bg.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", last,
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", bgv], check=True)

    # оверлеи: (png, t0, t1, fade_in)
    ov = []
    ov.append((hud("hud0", "0 ₽"), 0.3, t_spis + 0.4, 0.3))
    ov.append((hud("hud1", "−399 ₽", red=True), t_spis + 0.4, total, 0.0))
    ov.append((big_zero("zero"), t_card0 + 0.3, t_zarp - 0.1, 0.15))
    ov.append((card("quest", "КВЕСТ", "Продержаться 30 дней без денег", kcol=YEL), t_task, t_watch, 0.2))
    ov.append((card("trap0", "!", "Вечером — ловушка", kcol=RED), t_watch, t_day - 0.1, 0.2))
    ov.append((card("day", "07:00", "День первый"), t_day, t_r1 - 0.05, 0.2))
    ov.append((card("r1a", "ПРАВИЛО 1", "Не паникуй — посчитай"), t_r1, t_week, 0.2))
    ov.append((card("r1b", "ПРАВИЛО 1", "Не паникуй — посчитай", "≈ 7 дней еды"), t_week, t_r2 - 0.1, 0.0))
    ov.append((card("r2a", "ПРАВИЛО 2", "Никакого транспорта", "−150 ₽ в день", RED), t_r2, t_month, 0.2))
    ov.append((card("r2b", "ПРАВИЛО 2", "Никакого транспорта", "−4 500 ₽ за месяц", RED), t_month, t_r3 - 0.1, 0.0))
    ov.append((card("r3a", "ПРАВИЛО 3", "Деньги уже лежат дома"), t_r3, t_photo, 0.2))
    ov.append((card("r3b", "ПРАВИЛО 3", "Деньги уже лежат дома", "Объявление: 3 000 ₽"), t_photo, t_buyer, 0.0))
    ov.append((card("r3c", "ПРАВИЛО 3", "Деньги уже лежат дома", "Ждём покупателя…", YEL), t_buyer, t_eve - 0.1, 0.0))
    ov.append((notif("notif"), t_spis, t_trap - 0.1, 0.0))
    ov.append((card("trap1", "ЛОВУШКА №1", "Автоплатежи", kcol=RED), t_trap, t_q - 0.1, 0.0))
    ov.append((end_card("end1", "Что ты сделаешь первым?", "Пиши в комментариях"), t_q, t_tom - 0.05, 0.2))
    ov.append((end_card("end2", "День второй —", "уже завтра", YEL), t_tom, total, 0.2))
    ov.append((flash("red", RED, 110), t_spis, t_spis + 0.35, 0.0))

    # субтитры (на время больших карточек в центре — те же, они ниже)
    subs = B.chunks(WORDS, total)
    subs = [s for s in subs if s["t0"] < t_q - 0.05]   # в финале говорят карточки — без дубля
    for k, s in enumerate(subs):
        ov.append((subtitle(f"s{k}", s["text"], key_of(s["text"])), s["t0"], s["t1"], 0.0))

    # проверка: карточки не пересекаются по времени между собой
    cards_t = sorted((a, b) for (p, _x, _y), a, b, _ in ov if os.path.basename(p)[:1] not in "sh" and "red" not in p)
    for (a0, a1), (b0, b1) in zip(cards_t, cards_t[1:]):
        assert b0 >= a1 - 0.05, ("карточки наложились", a0, a1, b0, b1)

    inputs = ["-i", bgv]
    fc = []
    # тряска кадра на уведомлении
    sh0, sh1 = t_spis, t_spis + 0.7
    fc.append(f"[0:v]scale=1120:1992,crop={W}:{H}:x='20+if(between(t,{sh0},{sh1}),14*sin(t*70),0)':"
              f"y='36+if(between(t,{sh0},{sh1}),10*cos(t*55),0)'[v0]")
    last = "[v0]"
    for i, ((p, ox, oy), a, b, fin) in enumerate(ov):
        inputs += ["-loop", "1", "-t", f"{total:.3f}", "-i", p]
        src = f"[{i + 1}:v]format=rgba"
        if fin:
            src += f",fade=in:st={a:.3f}:d={fin}:alpha=1"
        fc.append(src + f"[o{i}]")
        fc.append(f"{last}[o{i}]overlay={ox}:{oy}:enable='between(t,{a:.3f},{b:.3f})'[v{i + 1}]")
        last = f"[v{i + 1}]"

    # звук
    ev = [(t_card0 + 0.3, "hit", 0.5), (t_task, "pop", 0.5), (t_watch, "riser", 0.35), (t_day, "whoosh", 0.4),
          (t_r1, "pop", 0.5), (t_week, "ding", 0.45), (t_r2, "pop", 0.5), (t_month, "stamp", 0.45),
          (t_r3, "pop", 0.5), (t_photo, "click", 0.6), (t_buyer, "tick", 0.25), (t_eve, "whoosh", 0.3),
          (t_vib - 0.6, "riser", 0.4), (t_vib, "bass", 0.6), (t_spis, "glitch", 0.55), (t_spis, "hit", 0.6),
          (t_trap, "stamp", 0.55), (t_q, "pop", 0.5), (t_tom, "chime", 0.4)]
    mixed = SFX.mix(AUDIO, ev, f"{TMP}/mix.wav", f"{TMP}/sfx", bed_gain=0.16, total=total,
                    bed_fn=SFX.music_bed(MUSIC))
    inputs += ["-i", mixed]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
                    "-map", last, "-map", f"{len(ov) + 1}:a", "-t", f"{total:.3f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT], check=True)
    print(OUT, round(total, 1), "c,", len(subs), "субтитров")


if __name__ == "__main__":
    main()
