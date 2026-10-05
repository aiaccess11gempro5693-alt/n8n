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
AVATAR_BOX = (150, 330, 930, 1150)
FACE = (540, 600, 250)   # центр лица и половина стороны кропа для видоискателя


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
            if w == "—" and piece:
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
    full = {"kind": "scale", "s": 1.0, "x": 0, "y": 420, "zoom": 0.03}
    return [
        {"bg": p("bg_dots"), "av": full, "els": [
            (T.call_card(p("s1_call"), 940), 40, 60, 0.15),
            (T.stamp(p("s1_stamp"), "ОПАСНО", size=120, angle=-9), 470, 300, F("банка") + 0.05, None, "stamp"),
        ]},
        {"bg": p("bg_type"), "av": None, "els": [
            (T.big_three(p("s2_three"), 1000), 40, 170, b[1] + 0.05),
        ]},
        {"bg": p("bg_plain"), "av": {"kind": "scale", "s": 0.92, "x": 330, "y": 520}, "els": [
            (T.sticker(p("s3_st1"), 1, ["Торопит", "и пугает"], ic("bolt"), 640), 30, 90, F("Первый:")),
            (T.sticker(p("s3_st2"), 2, ["Просит код", "из СМС"], ic("sms"), 640), 30, 400, F("Второй:")),
            (T.code_card(p("s3_code"), 620), 40, 720, F("Банк")),
        ]},
        {"bg": p("bg_dots"), "av": {"kind": "finder", "size": 560, "x": (W - 560) // 2, "y": 110}, "els": [
            (T.viewfinder(p("s4_vf"), 560), (W - 560) // 2 - 20, 90, b[3] + 0.05),
            (T.headline(p("s4_head"), [[("«Безопасный", "w")], [("счёт»", "b")]], 1000, size=96,
                        align="center"), 40, 760, F("Предлагает")),
            (T.stamp(p("s4_stamp"), "НЕ СУЩЕСТВУЕТ", size=104, angle=-6, seed=9), 90, 1130,
             F("Такого") + 0.05, None, "stamp"),
        ]},
        {"bg": p("bg_plain"), "av": {"kind": "scale", "s": 0.95, "x": -330, "y": 480}, "els": [
            (T.headline(p("s5_head"), [[("Что", "w")], [("делать?", "b")]], 640, size=92), 420, 70, b[4] + 0.05),
            (T.action_button(p("s5_hang"), ["Положите", "трубку"], T.RED, True), 470, 450, F("Положите")),
            (T.action_button(p("s5_call"), ["Перезвоните", "сами"], T.YELLOW, False), 470, 700, F("перезвоните")),
            (T.card_back(p("s5_card"), 540), 440, 960, F("номеру") - 0.2),
        ]},
        {"bg": p("bg_dots"), "av": {"kind": "scale", "s": 1.0, "x": 0, "y": 480, "zoom": 0.06}, "els": [
            (T.headline(p("s6_head"), [[("1 минута", "w")], [("паузы", "b")], [("= деньги целы", "y")]], 1000,
                        size=92, align="center"), 40, 70, b[5] + 0.05),
        ]},
    ]


# ---------------------------------------------------------------- проверка

def _avatar_rect(av):
    if not av:
        return None
    if av["kind"] == "finder":
        return (av["x"], av["y"], av["x"] + av["size"], av["y"] + av["size"])
    s = av["s"] * (1 + av.get("zoom", 0))
    ax0, ay0, ax1, ay1 = AVATAR_BOX
    cx = av["x"] + 540 * av["s"]   # наезд — от центра верхней части силуэта
    return (cx + (ax0 - 540) * s, av["y"] + ay0 * s, cx + (ax1 - 540) * s, av["y"] + ay1 * s)


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
    els = []
    for el in sc["els"]:
        tin = max(0.0, el[3] - t0)
        tout = (el[4] - t0) if len(el) > 4 and el[4] is not None else dur
        els.append((os.path.basename(el[0]), V._rect(el[0], el[1], el[2]), tin, tout))
    errs = []
    for i, (n, rr, a, z) in enumerate(els):
        for n2, r2, a2, z2 in boxes + els[i + 1:]:
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
            k_ = f"({av['s']}*(1+{z}*t/{dur}))"
            fc.append(f"[{idx}:v]format=rgba,fps={FPS},scale=w='trunc(1080*{k_}/2)*2':h='trunc(1920*{k_}/2)*2'"
                      f":eval=frame[av]")
            cx = av["x"] + 540 * av["s"]
            fc.append(f"[{last}][av]overlay=x='{cx}-w/2':y={av['y']}:shortest=0[a0]")
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


def main():
    os.makedirs(TMP, exist_ok=True)
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                  "csv=p=0", AUDIO], capture_output=True, text=True).stdout)
    words = V.word_times()
    caps = caption_chunks(words, total)
    sc = scenes(V.finder(words))
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
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", AUDIO, "-map", "0:v",
         "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT])
    print("done", OUT)


if __name__ == "__main__":
    main()
