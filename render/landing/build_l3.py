"""Лендинг, ролик 3 «Как не попасться телефонным мошенникам» — вертикаль 9:16.

Стиль «Reels-эксперт», вариант A (render/landing/theme_reels.py, борд
scratch/img/l3_board_a.png), эксперт по кибербезопасности банка
(scratch/img/l3_expert_9x16.png → HeyGen photo avatar, клип webm с прозрачным
фоном), голос Синев (eleven_v3). Сценарий — docs/scenarios/landing-3-scams.md.

Раскладка своя (не как в ролике 1) и меняется каждую сцену:
  1 hook    — эксперт крупно внизу, сверху карточка входящего звонка
              «Служба безопасности банка», на неё падает штамп «ОПАСНО»
  2 type    — без эксперта: огромная жёлтая «3», «признака мошенника»
  3 side    — эксперт сдвинут вправо, слева стопка стикеров-признаков
              (1 торопит, 2 код из СМС → «••••» перечёркнут + «банк не спрашивает»)
  4 finder  — лицо эксперта в жёлтом видоискателе сверху, ниже
              «безопасный счёт» и штамп «НЕ СУЩЕСТВУЕТ»
  5 action  — эксперт слева, справа кнопки «положите трубку» → «перезвоните
              сами» и оборот карты с номером банка
  6 final   — эксперт на весь кадр с наездом, итог «1 минута паузы = деньги целы»

Подача Reels: элементы «выпрыгивают» с перелётом (ease-out-back), штампы
«впечатываются» сверху, эксперт в полнокадровых сценах медленно наезжает,
переход — жёлтый мазок через кадр. Субтитры крупные, текущее слово — на жёлтой
плашке (решение пользователя для примеров сайта, 05.10.2026).

Запуск:  python3 -m render.landing.build_l3
Выход:   render/landing/l3-9x16.mp4
"""
import os
import re
import subprocess

from PIL import Image

from render.landing import build_l1_v3 as V
from render.landing import sfx as SFX
from render.landing import theme_reels as T

ROOT = V.ROOT
HERE = V.HERE
IMG = f"{ROOT}/scratch/img"
TMP = f"{HERE}/_frames_l3"
AUDIO = f"{ROOT}/scratch/l3-v-full-v2.mp3"
CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l3-v-expert.webm")
OUT = f"{HERE}/l3-9x16.mp4"

W, H, FPS = 1080, 1920, 25
# границы сцен — середины пауз между предложениями (silencedetect)
BOUNDS = [0.0, 2.79, 5.61, 12.92, 19.11, 24.90]
CAP_W, CAP_X, CAP_BOTTOM = 980, 50, 1850
POP = 0.32

V.TEXTS = f"{ROOT}/docs/scenarios/landing-3-scams.md"
V.WHISPER = f"{ROOT}/scratch/l3-v-full-v2-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 9:16 (до 30 с)", "## Раскладка 9:16"

# числа на экране и в субтитрах — цифрами
SHOW = {"три": "3"}

# Силуэт эксперта в кадре клипа HeyGen 1080×1920 (голова, плечи; ниже —
# только корпус в чёрной рубашке, там допустимы субтитры). Измерено по альфе.
AVATAR_BOX = (110, 300, 980, 1100)
FACE = (535, 545, 265)
CLIP_BOTTOM = 1769   # ниже — пусто (край исходного фото): всегда за кадром
FACE_Y = FACE[1] / 1920   # доля высоты клипа, где лицо: точка опоры резкого наезда
PUNCH = 0.13              # резкий наезд на ключевом слове: +13% к масштабу   # центр лица и половина стороны кропа для видоискателя


def run(cmd):
    subprocess.run(cmd, check=True)


def p(name):
    return f"{TMP}/{name}.png"


# ---------------------------------------------------------------- субтитры

def caption_chunks(words, total):
    """Предложение → чанки: режем по «—», длинное (>2 строк) — поровну.
    Каждый чанк — список (слово, время); показывается до начала следующего."""
    f = T.font(T.F_BODY, T.CAP_F)
    sents, cur = [], []
    for w, t in words:
        w = w.replace("\u0301", "")   # знак ударения — для озвучки, не для экрана
        letters = re.sub(r"[^\w]", "", w)
        if letters.isupper() and len(letters) > 1 and letters != "СМС":
            w = w.lower()   # КАПС в тексте — подсказка ударения для eleven_v3, не для экрана
        cur.append((SHOW.get(w.lower(), w), t))
        if re.search(r"[.!?]»?$", w):
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)
    parts = []
    for s in sents:
        piece = []
        for w, t in s:
            if w == "—":
                if piece:
                    parts.append(piece)
                piece = []
                continue
            piece.append((w, t))
        if piece:
            parts.append(piece)
    chunks = []
    for part in parts:
        lines = T.caption_layout([w for w, _ in part], CAP_W)
        n = (len(lines) + 1) // 2
        k = len(part)
        for i in range(n):
            chunks.append(part[round(i * k / n):round((i + 1) * k / n)])
    out = []
    for i, ch in enumerate(chunks):
        t1 = chunks[i + 1][0][1] if i + 1 < len(chunks) else total
        out.append({"words": ch, "t0": ch[0][1], "t1": t1})
    out[0]["t0"] = 0.0
    return out


def caption_height(ch):
    lines = T.caption_layout([w for w, _ in ch["words"]], CAP_W)
    return 36 + len(lines) * 80 + 30


# ---------------------------------------------------------------- сцены

def scenes(F):
    b = BOUNDS
    T.background(p("bg_plain"), W, H, "plain")
    T.background(p("bg_dots"), W, H, "dots")
    T.background(p("bg_type"), W, H, "type")
    ic = lambda n: f"{IMG}/l3_ic_{n}.png"
    full = {"kind": "scale", "s": 1.0, "x": 0, "y": 340, "zoom": 0.03, "punch": [F("банка»?")]}
    return [
        {"bg": p("bg_dots"), "av": full, "sfx": [(0.1, "ring", 0.4)], "els": [
            (T.call_card(p("s1_call"), 940), 40, 40, 0.15),
            (T.stamp(p("s1_stamp"), "ОПАСНО", size=120, angle=-9), 470, 270, F("банка»?") + 0.05, None, "stamp"),
        ]},
        {"bg": p("bg_type"), "av": None, "flash": [(b[1] + 0.05, "yellow")], "els": [
            (T.big_three(p("s2_three"), 1000), 10, 170, b[1] + 0.05),
        ]},
        {"bg": p("bg_plain"), "av": {"kind": "scale", "s": 0.9, "x": 820 - 486, "y": 619},
         "sfx": [(F("Первый:"), "tick", 0.35), (F("Второй:"), "glitch", 0.3)], "els": [
            (T.sticker(p("s3_st1"), 1, ["Торопит и пугает"], ic("bolt"), 1000), 10, 30, F("Первый:")),
            (T.sticker(p("s3_st2"), 2, ["Просит код из СМС"], ic("sms"), 1000), 10, 310, F("Второй:")),
            (T.code_card(p("s3_code"), 360, ("БАНК НЕ", "СПРАШИВАЕТ")), 0, 610, F("банк")),
        ]},
        {"bg": p("bg_dots"), "av": {"kind": "finder", "size": 560, "x": (W - 560) // 2, "y": 110},
         "sfx": [(b[3] + 0.05, "glitch", 0.35), (F("Такого") - 1.15, "riser", 0.45)], "els": [
            (T.viewfinder(p("s4_vf"), 560), (W - 560) // 2 - 20, 90, b[3] + 0.05, None, "frame"),
            (T.headline(p("s4_head"), [[("«Безопасный", "w")], [("счёт»", "b")]], 1000, size=92,
                        align="center"), 40, 740, F("Предлагает")),
            (T.stamp(p("s4_stamp"), "НЕ СУЩЕСТВУЕТ", size=104, angle=-6, seed=9), 90, 1110,
             F("Такого") + 0.05, None, "stamp"),
        ]},
        {"bg": p("bg_plain"), "av": {"kind": "scale", "s": 0.85, "x": 180 - 459, "y": 635, "punch": [F("Положите")]},
         "els": [
            (T.headline(p("s5_head"), [[("Что", "w"), ("делать?", "b")]], 1000, size=84), 40, 40, b[4] + 0.05),
            (T.action_button(p("s5_hang"), ["Положите", "трубку"], T.RED, True), 40, 250, F("Положите")),
            (T.action_button(p("s5_call"), ["Перезвоните", "сами"], T.YELLOW, False), 40, 480, F("перезвоните")),
            (T.card_back(p("s5_card"), 420), 540, 900, F("банк", 21.5) - 0.1),
        ]},
        {"bg": p("bg_dots"), "av": {"kind": "scale", "s": 1.0, "x": 0, "y": 340, "zoom": 0.04, "punch": [F("сбережёт")]},
         "flash": [(b[5] + 0.05, "yellow")], "els": [
            (T.headline(p("s6_head"), [[("1 минута", "w")], [("паузы", "b")], [("= деньги целы", "y")]], 1000,
                        size=88, align="center"), 40, 40, b[5] + 0.05),
        ]},
    ]


# ---------------------------------------------------------------- проверка

def _avatar_rect(av):
    if not av:
        return None
    if av["kind"] == "finder":
        return (av["x"], av["y"], av["x"] + av["size"], av["y"] + av["size"])
    s0 = av["s"]
    s = s0 * (1 + av.get("zoom", 0)) * (1 + PUNCH * len(av.get("punch", ())))
    ax0, ay0, ax1, ay1 = AVATAR_BOX
    cx = av["x"] + 540 * s0
    top = av["y"] - (s - s0) * 1920 * FACE_Y   # наезд — к лицу (точка лица стоит на месте)
    return (cx + (ax0 - 540) * s, top + ay0 * s, cx + (ax1 - 540) * s, top + ay1 * s)


def check_layout(k, sc, t0, t1, caps):
    """Правило «ничего не наезжает» (docs/landing/video-rules.md, п.7): элементы
    не ложатся на силуэт эксперта, на субтитры, друг на друга и не выходят за
    кадр. Нарушение — ошибка сборки."""
    dur = t1 - t0
    boxes = []
    r = _avatar_rect(sc["av"])
    if r:
        boxes.append(("эксперт", r, 0, dur))
    for c in caps:
        a, z = max(0.0, c["t0"] - t0), min(dur, c["t1"] - t0)
        if z > 0 and a < dur:
            hh = caption_height(c)
            boxes.append((f"субтитр «{c['words'][0][0]}…»", (CAP_X, CAP_BOTTOM - hh, CAP_X + CAP_W, CAP_BOTTOM), a, z))
    errs = []
    els = []
    for el in sc["els"]:
        tin = max(0.0, el[3] - t0)
        tout = (el[4] - t0) if len(el) > 4 and el[4] is not None else dur
        mode = el[5] if len(el) > 5 else "pop"
        els.append((os.path.basename(el[0]), V._rect(el[0], el[1], el[2]), tin, tout, mode))
    av = sc["av"]
    if av and av["kind"] == "scale" and av["y"] + CLIP_BOTTOM * av["s"] < H:
        errs.append(f"сцена {k + 1}: нижний край клипа эксперта виден в кадре")
    for i, (n, rr, a, z, m) in enumerate(els):
        if m == "frame":
            continue       # рамка видоискателя намеренно обрамляет лицо эксперта
        for n2, r2, a2, z2, *m2 in [(*bx, None) for bx in boxes] + els[i + 1:]:
            if "stamp" in (m, *m2) and m2 and m2[0] is not None:
                continue   # штамп намеренно ложится на карточку, которую «штампует»
            if a < z2 - 0.05 and a2 < z - 0.05 and V._hit(rr, r2, pad=8):
                errs.append(f"сцена {k + 1}: {n} {tuple(map(int, rr))} наезжает на {n2} {tuple(map(int, r2))}")
        if rr and (rr[0] < 0 or rr[1] < 0 or rr[2] > W or rr[3] > H):
            errs.append(f"сцена {k + 1}: {n} выходит за кадр {rr}")
    if errs:
        raise SystemExit("Наложение элементов:\n" + "\n".join(errs))


# ---------------------------------------------------------------- рендер

def render_scene(k, sc, t0, t1, caps):
    check_layout(k, sc, t0, t1, caps)
    dur = round(t1 - t0, 3)
    loop = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i"]
    inputs = [*loop, sc["bg"]]
    fc = [f"[0:v]format=rgba,fps={FPS}[bg]"]
    last, idx = "bg", 1
    av = sc["av"]
    if av:
        inputs += ["-c:v", "libvpx-vp9", "-ss", f"{t0}", "-t", f"{dur}", "-i", CLIP]
        if av["kind"] == "scale":
            z = av.get("zoom", 0)
            pn = "".join(f"+{PUNCH}*clip((t-{tp - t0:.2f})/0.09\\,0\\,1)" for tp in av.get("punch", ()))
            k_ = f"({av['s']}*(1+{z}*t/{dur})*(1{pn}))"
            fc.append(f"[{idx}:v]format=rgba,fps={FPS},scale=w='trunc(1080*{k_}/2)*2':h='trunc(1920*{k_}/2)*2'"
                      f":eval=frame[av]")
            cx = av["x"] + 540 * av["s"]
            h0 = 1920 * av["s"]
            fc.append(f"[{last}][av]overlay=x='{cx}-w/2':y='{av['y']}-(h-{h0})*{FACE_Y:.4f}':shortest=0[a0]")
        else:   # видоискатель: квадратный кроп лица
            cx, cy, r = FACE
            fc.append(f"[{idx}:v]format=rgba,fps={FPS},crop={2 * r}:{2 * r}:{cx - r}:{cy - r},"
                      f"scale={av['size']}:{av['size']}[av]")
            fc.append(f"[{last}][av]overlay={av['x']}:{av['y']}[a0]")
        last, idx = "a0", idx + 1
    for j, el in enumerate(sc["els"]):
        png, x, y = el[0], el[1], el[2]
        tin = max(0.0, el[3] - t0)
        tout = (el[4] - t0) if len(el) > 4 and el[4] is not None else dur
        mode = el[5] if len(el) > 5 else "pop"
        iw, ih = Image.open(png).size
        inputs += [*loop, png]
        q = f"clip((t-{tin:.2f})/{POP}\\,0\\,1)"
        if mode == "stamp":   # впечатывается: крупнее и быстро садится
            q = f"clip((t-{tin:.2f})/0.18\\,0\\,1)"
            kk = f"(1+0.7*pow(1-{q}\\,2))"
        else:                 # выпрыгивает с перелётом (ease-out-back)
            kk = f"(0.55+0.45*(1+2.70158*pow({q}-1\\,3)+1.70158*pow({q}-1\\,2)))"
        fout = f"fade=t=out:st={max(tin, tout - 0.2):.2f}:d=0.2:alpha=1," if tout < dur - 0.01 else ""
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={tin:.2f}:d=0.12:alpha=1,{fout}"
                  f"scale=w='max(2\\,trunc({iw}*{kk}/2)*2)':h='max(2\\,trunc({ih}*{kk}/2)*2)':eval=frame[e{j}]")
        fc.append(f"[{last}][e{j}]overlay=x='{x + iw / 2}-w/2':y='{y + ih / 2}-h/2'"
                  f":enable='between(t,{tin:.2f},{tout:.2f})'[o{j}]")
        last, idx = f"o{j}", idx + 1
    n = 0
    for ci, c in enumerate(caps):
        a, z = max(0.0, c["t0"] - t0), min(dur, c["t1"] - t0)
        if z <= 0 or a >= dur:
            continue
        ws = [w for w, _ in c["words"]]
        for wi, (_, wt) in enumerate(c["words"]):
            s0 = a if wi == 0 else max(a, wt - t0)
            s1 = (c["words"][wi + 1][1] - t0) if wi + 1 < len(ws) else z
            s1 = min(s1, z)
            if s1 <= s0:
                continue
            path = p(f"cap_{ci}_{wi}")
            T.caption(path, ws, wi, CAP_W)
            cy = CAP_BOTTOM - Image.open(path).height
            inputs += [*loop, path]
            fc.append(f"[{last}][{idx}:v]overlay={CAP_X}:{cy}:enable='gte(t,{s0:.3f})*lt(t,{s1:.3f})'[c{n}]")
            last, idx, n = f"c{n}", idx + 1, n + 1
    for j, (tf, col) in enumerate(sc.get("flash", [])):   # вспышка цвета на акценте
        a = max(0.0, tf - t0)
        T.flash(p(f"flash_{col}"), W, H, col)
        inputs += [*loop, p(f"flash_{col}")]
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={a:.2f}:d=0.04:alpha=1,"
                  f"fade=t=out:st={a + 0.06:.2f}:d=0.32:alpha=1[fl{j}]")
        fc.append(f"[{last}][fl{j}]overlay=0:0:enable='between(t,{a:.2f},{a + 0.4:.2f})'[f{j}]")
        last, idx = f"f{j}", idx + 1
    shakes = [max(0.0, ts - t0) for ts in sc.get("shake", [])]
    if shakes:   # тряска кадра на ударе штампа
        amp = "+".join(f"between(t\\,{a:.2f}\\,{a + 0.32:.2f})*(1-(t-{a:.2f})/0.32)" for a in shakes)
        fc.append(f"[{last}]pad={W + 48}:{H + 48}:24:24:color=0x0E0E10,"
                  f"crop={W}:{H}:x='24+16*sin(t*97)*({amp})':y='24+12*cos(t*83)*({amp})'[shk]")
        last = "shk"
    if k > 0:   # смена раскладки: жёлтый мазок пролетает через кадр
        T.swipe(p("swipe"), W, H)
        inputs += [*loop, p("swipe")]
        fc.append(f"[{last}][{idx}:v]overlay=x='-{W}+{2 * W}*t/0.3':y=0:enable='lt(t,0.3)'[sw]")
        last, idx = "sw", idx + 1
    fc.append(f"[{last}]format=yuv420p[vout]")
    out = f"{TMP}/scene{k + 1}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]",
         "-an", "-t", f"{dur}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", out])
    return out


def enrich(sc_list):
    """Акценты по умолчанию: штамп — тряска кадра + красная вспышка."""
    for sc in sc_list:
        for el in sc["els"]:
            if len(el) > 5 and el[5] == "stamp":
                sc.setdefault("shake", []).append(el[3])
                sc.setdefault("flash", []).append((el[3], "red"))
    return sc_list


def sound_events(sc_list, bounds):
    """Звук из событий кадра: смена сцены — вжух, появление — поп, штамп —
    удар, вспышка/наезд — «бум»; плюс свои звуки сцены (sc["sfx"])."""
    ev = []
    for k, sc in enumerate(sc_list):
        if k > 0:
            ev.append((bounds[k] - 0.12, "whoosh", 0.55))
        for el in sc["els"]:
            mode = el[5] if len(el) > 5 else "pop"
            if mode == "stamp":
                ev += [(el[3], "stamp", 0.9), (el[3], "hit", 0.45)]
            elif mode != "frame":
                ev.append((el[3], "pop", 0.3))
        for tf, col in sc.get("flash", []):
            if col != "red":
                ev.append((tf, "hit", 0.5))
        av = sc.get("av") or {}
        for tp in av.get("punch", ()):
            ev.append((tp, "hit", 0.35))
        ev += sc.get("sfx", [])
    return ev


def main():
    os.makedirs(TMP, exist_ok=True)
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                  "csv=p=0", AUDIO], capture_output=True, text=True).stdout)
    words = V.word_times()
    caps = caption_chunks(words, total)
    sc = enrich(scenes(V.finder(words)))
    bounds = BOUNDS + [total]
    only = os.environ.get("ONLY")
    for k, s in enumerate(sc):
        check_layout(k, s, bounds[k], bounds[k + 1], caps)
    if os.environ.get("CHECK"):
        print("layout ok")
        return
    parts = []
    for k, s in enumerate(sc):
        if only and str(k + 1) not in only.split(","):
            continue
        parts.append(render_scene(k, s, bounds[k], bounds[k + 1], caps))
        print("scene", k + 1, flush=True)
    if only:
        return
    lst = f"{TMP}/concat.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{x}'\n" for x in parts)
    mixed = SFX.mix(AUDIO, sound_events(sc, bounds), f"{TMP}/mix.wav", f"{TMP}/sfx", total=total)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", mixed, "-map", "0:v",
         "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT])
    print("done", OUT)


if __name__ == "__main__":
    main()
