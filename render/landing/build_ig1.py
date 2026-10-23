"""Instagram Reels №1 «Меня не существует» — 9:16, серия продающих Reels
`iiavatar.video` (docs/landing/insta/content-plan.md).

Стиль серии — render/landing/theme_brand.py (борд scratch/img/ig1_board.png),
ведущая B (scratch/img/ig1_host_b.png → HeyGen photo avatar
3f66091c5e29b7a6f7774fb97cb43337, avatar_iv, expressiveness high, клип mp4 с
фоном-лофтом scratch/ig1-host.mp4), голос Victoria (eleven_v3,
scratch/ig1-full-b-trim.mp3). Сценарий — docs/scenarios/insta-1-not-exist.md.

Формула: крючок → польза → раскрытие «я ИИ» (глитч) → призыв.
Раскладка меняется по сценам:
  1 hook   — ведущая на весь кадр, сверху «СТОП. 2 СЕКУНДЫ», наезд на «Стоп»
  2 type   — без ведущей: огромная «3» + «правила видео, которое досматривают»
  3 panel  — ведущая ниже, сверху карточка правил 01→02→03 (одна карточка
             с состояниями, будущие пункты — пустые слоты)
  4 reveal — ведущая на весь кадр, на «существует» — цифровой сбой
  5 circle — лицо в оранжевом круге, «камера» и «студия» зачёркнуты,
             «текст → видео», «за 1 день»
  6 cta    — ведущая ниже, сверху «Хотите такого ведущего?» → «Напишите
             «ВЕДУЩИЙ» в директ»

Запуск:  python3 -m render.landing.build_ig1   (CHECK=1 — только проверка раскладки)
Выход:   render/landing/ig1-9x16.mp4
"""
import difflib
import json
import os
import re
import subprocess

from PIL import Image

from render.landing import sfx as SFX
from render.landing import theme_brand as T

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = f"{HERE}/_frames_ig1"
AUDIO = f"{ROOT}/scratch/ig1-v2-b-trim.mp3"
WHISPER = f"{ROOT}/scratch/ig1-v2-b-whisper-1.json"
CLIP = f"{ROOT}/scratch/ig1-host-v2.mp4"
MUSIC = f"{ROOT}/scratch/ig1-music.mp3"
TEXTS = f"{ROOT}/docs/scenarios/insta-1-not-exist.md"
OUT = f"{HERE}/ig1-9x16.mp4"

W, H, FPS = 1080, 1920, 25
TAIL = 0.8
BOUNDS = [0.0, 7.75, 11.35, 22.85, 26.55, 32.95]
CAP_W, CAP_X, CAP_BOTTOM = 980, 50, 1840
POP = 0.32
TOTAL = 1.0
PROGRESS_H = 12          # оранжевая полоса прогресса сверху (удержание)
# Голова ведущей в кадре клипа (1080×1920): волосы, лицо, шея — измерено по кадру.
HEAD = (350, 240, 730, 760)
FACE = (540, 520)          # центр лица — точка опоры наезда
SHOW = {"три": "3", "один": "1"}

LAYOUT = {
    "full": {"kind": "scale", "s": 1.0, "y": 240, "mask": dict(top=300)},
    "panel": {"kind": "scale", "s": 0.68, "y": 700, "mask": dict(top=320, side=170)},
    "low": {"kind": "scale", "s": 0.66, "y": 800, "mask": dict(top=320, side=170)},
    "circle": {"kind": "circle", "size": 460, "x": 310, "y": 110, "r": 300},
}


def run(cmd):
    subprocess.run(cmd, check=True)


def p(name):
    return f"{TMP}/{name}.png"


# ---------------------------------------------------------------- текст и тайминги

def clean_words():
    md = open(TEXTS, encoding="utf-8").read()
    body = md.split("## Текст", 1)[1].split("##", 1)[0]
    body = body.split("\n", 1)[1]
    out = []
    for w in body.split():
        if w in ("—", "-"):
            if out:
                out[-1] += "|"   # тире — граница чанка субтитров
            continue
        out.append(w)
    return out


def norm(w):
    return re.sub(r"[^\w]", "", w.lower().replace("ё", "е"))


def word_times():
    ws = json.load(open(WHISPER))["words"]
    text = clean_words()
    a, b = [norm(w) for w in text], [norm(x["word"]) for x in ws]
    times = [None] * len(text)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = ws[blk.b + k]["start"]
    for i, t in enumerate(times):   # несовпавшие слова — между соседями
        if t is None:
            prev = next((times[j] for j in range(i - 1, -1, -1) if times[j] is not None), 0.0)
            nxt = next((times[j] for j in range(i + 1, len(times)) if times[j] is not None), prev + 0.4)
            times[i] = prev + (nxt - prev) * 0.5
    return list(zip(text, times))


def finder(words):
    def F(needle, after=0.0):
        for w, t in words:
            if t >= after and norm(w).startswith(norm(needle)):
                return t
        raise KeyError(needle)
    return F


def caption_chunks(words, total):
    sents, cur = [], []
    for w, t in words:
        brk = w.endswith("|")
        w = w.rstrip("|")
        cur.append((SHOW.get(norm(w), w), t))
        if brk or re.search(r"[.!?…]»?$", w) or w.endswith(":"):
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)
    chunks = []
    for part in sents:
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


# ---------------------------------------------------------------- сцены

def scenes(F):
    """«cuts» — монтажные склейки-наезды (jump cut): с момента t ведущая крупнее
    в k раз. Каждая новая фраза — новый план, кадр не стоит на месте."""
    b = BOUNDS
    T.background(p("bg"), W, H, "plain")
    T.background(p("bg_grid"), W, H, "grid")
    rules = ["Лицо в кадре", "1 мысль = 1 сцена", "Субтитры"]
    return [
        {"bg": p("bg"), "av": dict(LAYOUT["full"], cuts=[(0.0, 1.25), (F("Две"), 1.0), (F("Столько"), 1.12),
                                                        (F("Получилось"), 1.25)]),
         "flash": [(0.02, "white")], "shake": [0.02], "sfx": [(0.0, "bass", 0.7)],
         "els": [
             (T.headline(p("s1_stop"), [[("Стоп.", "w")]], 1000, size=210), 40, -110, 0.02),
             (T.headline(p("s1_sec"), [[("2 секунды", "box")]], 1000, size=112), 40, 150, F("Две")),
         ]},
        {"bg": p("bg_grid"), "av": None, "flash": [(b[1] + 0.03, "orange")], "els": [
            (T.big_number(p("s2_three"), "3", [[("правила", "w"), ("видео,", "w")], [("которое", "w")],
                                                [("досматривают", "box")]], 1000), 40, 110, b[1] + 0.05),
        ]},
        {"bg": p("bg"), "av": dict(LAYOUT["panel"], cuts=[(F("Второе"), 1.1), (F("Третье"), 1.0)]), "els": [
            (T.rules_card(p("s3_r0"), rules, 0), 10, 30, b[2] + 0.05, F("Второе"), "pop", True),
            (T.rules_card(p("s3_r1"), rules, 1), 10, 30, F("Второе"), F("Третье"), "state"),
            (T.rules_card(p("s3_r2"), rules, 2), 10, 30, F("Третье"), None, "state"),
        ], "sfx": [(F("Первое"), "click", 0.4), (F("Второе"), "click", 0.4), (F("Третье"), "click", 0.4)]},
        {"bg": p("bg"), "av": dict(LAYOUT["full"], cuts=[(F("меня", b[3]), 1.12), (F("существует"), 1.3)]),
         "glitch": [(F("существует") - 0.05, 0.5), (F("существует") + 0.7, 0.2)],
         "flash": [(F("существует"), "white")], "shake": [F("существует")],
         "sfx": [(b[3] + 0.1, "riser", 0.45), (F("существует") - 0.05, "glitch", 0.7)], "els": [
             (T.headline(p("s4_head"), [[("Меня не", "w")], [("существует", "box")]], 1000, size=100), 40, 0,
              F("существует")),
         ]},
        {"bg": p("bg_grid"), "av": LAYOUT["circle"], "els": [
            (T.ring(p("s5_ring"), 460), 310 - 44, 110 - 44, b[4] + 0.02, None, "frame"),
            (T.cross_chip(p("s5_cam"), "Камера", w=440), 50, 640, F("камеры")),
            (T.cross_chip(p("s5_studio"), "Студия", w=440), 530, 640, F("студии")),
            (T.flow(p("s5_flow"), "ТЕКСТ", "ВИДЕО", 960), 30, 880, F("собран")),
            (T.tag(p("s5_day"), "за 1 день", 64), 320, 1140, F("день")),
        ], "sfx": [(F("нейросеть"), "glitch", 0.35)]},
        {"bg": p("bg"), "av": dict(LAYOUT["low"], cuts=[(F("Напишите"), 1.12)]), "els": [
            (T.headline(p("s6_q"), [[("Хотите", "w"), ("такого", "w")], [("ведущего?", "box")]], 1000, size=110),
             40, 60, b[5] + 0.05, F("Напишите"), "pop", True),
            (T.cta_card(p("s6_cta"), 1000), 40, 40, F("Напишите"), None, "state"),
        ], "sfx": [(F("Напишите"), "ding", 0.5)]},
    ]


# ---------------------------------------------------------------- проверка

def _rect(png, x, y):
    im = Image.open(png)
    bb = im.getchannel("A").point(lambda v: 255 if v > 60 else 0).getbbox()
    return (x + bb[0], y + bb[1], x + bb[2], y + bb[3]) if bb else None


def _hit(a, b, pad=10):
    return a and b and a[0] < b[2] + pad and b[0] < a[2] + pad and a[1] < b[3] + pad and b[1] < a[3] + pad


def head_rect(av):
    if not av:
        return None
    if av["kind"] == "circle":
        return (av["x"], av["y"], av["x"] + av["size"], av["y"] + av["size"])
    s = av["s"] * max([1.0] + [k for _, k in av.get("cuts", ())])
    s0 = av["s"]
    cx = 540
    fy = av["y"] + FACE[1] * s0                      # лицо стоит на месте при наезде
    x0, y0, x1, y1 = HEAD
    return (cx + (x0 - 540) * s, fy + (y0 - FACE[1]) * s, cx + (x1 - 540) * s, fy + (y1 - FACE[1]) * s)


def check_layout(k, sc, t0, t1, caps):
    """Правило «ничего не наезжает» (docs/landing/video-rules.md): надписи не
    ложатся на голову ведущей, на субтитры, друг на друга, не выходят за кадр."""
    dur = t1 - t0
    boxes = []
    r = head_rect(sc["av"])
    if r:
        boxes.append(("голова ведущей", r, 0, dur))
    for c in caps:
        a, z = max(0.0, c["t0"] - t0), min(dur, c["t1"] - t0)
        if z > 0 and a < dur:
            hh = T.caption_height([w for w, _ in c["words"]], CAP_W)
            boxes.append((f"субтитр «{c['words'][0][0]}…»", (CAP_X, CAP_BOTTOM - hh, CAP_X + CAP_W, CAP_BOTTOM), a, z))
    els, errs = [], []
    for el in sc["els"]:
        tin = max(0.0, el[3] - t0)
        tout = (el[4] - t0) if len(el) > 4 and el[4] is not None else dur
        mode = el[5] if len(el) > 5 else "pop"
        els.append((os.path.basename(el[0]), _rect(el[0], el[1], el[2]), tin, tout, mode))
    for i, (n, rr, a, z, m) in enumerate(els):
        if m == "frame":
            continue
        for n2, r2, a2, z2, *_ in [(*bx, None) for bx in boxes] + [e for e in els[i + 1:] if e[4] != "frame"]:
            if a < z2 - 0.05 and a2 < z - 0.05 and _hit(rr, r2):
                errs.append(f"сцена {k + 1}: {n} {tuple(map(int, rr))} наезжает на {n2} {tuple(map(int, r2))}")
        if rr and (rr[0] < 0 or rr[1] < 0 or rr[2] > W or rr[3] > H):
            errs.append(f"сцена {k + 1}: {n} выходит за кадр {rr}")
    if errs:
        raise SystemExit("Наложение элементов:\n" + "\n".join(errs))


# ---------------------------------------------------------------- рендер

def render_scene(k, sc, t0, t1, caps):
    dur = round(t1 - t0, 3)
    loop = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i"]
    inputs = [*loop, sc["bg"]]
    fc = [f"[0:v]format=rgba,fps={FPS}[bg]"]
    last, idx = "bg", 1
    av = sc["av"]
    if av:
        inputs += ["-ss", f"{t0}", "-t", f"{dur}", "-i", CLIP]
        src = f"[{idx}:v]fps={FPS},tpad=stop_mode=clone:stop_duration=2,trim=duration={dur},format=rgba"
        if av["kind"] == "scale":
            m = T.edge_mask(p(f"mask_{k}"), 1080, 1920, **av["mask"])
            inputs += [*loop, m]
            fc.append(f"{src}[cl]")
            fc.append(f"[{idx + 1}:v]format=gray,fps={FPS}[mk]")
            fc.append("[cl][mk]alphamerge[clm]")
            kk, prev = "1", 1.0
            for tc, kc in sorted(av.get("cuts", ())):
                kk += f"+{kc - prev:.3f}*gte(t\\,{max(0.0, tc - t0):.2f})"
                prev = kc
            ks = f"({av['s']}*(1+0.03*t/{dur})*({kk}))"
            fc.append(f"[clm]scale=w='trunc(1080*{ks}/2)*2':h='trunc(1920*{ks}/2)*2':eval=frame[av]")
            fy = av["y"] + FACE[1] * av["s"]
            fc.append(f"[{last}][av]overlay=x='540-w/2':y='{fy}-h*{FACE[1] / 1920:.4f}':shortest=0[a0]")
            idx += 2
        else:
            cx, cy = FACE
            r = av["r"]
            m = T.circle_mask(p(f"cmask_{k}"), av["size"])
            inputs += [*loop, m]
            fc.append(f"{src},crop={2 * r}:{2 * r}:{cx - r}:{cy - r},scale={av['size']}:{av['size']}[cl]")
            fc.append(f"[{idx + 1}:v]format=gray,fps={FPS}[mk]")
            fc.append("[cl][mk]alphamerge[av]")
            fc.append(f"[{last}][av]overlay={av['x']}:{av['y']}[a0]")
            idx += 2
        last = "a0"
    for j, el in enumerate(sc["els"]):
        png, x, y = el[0], el[1], el[2]
        tin = max(0.0, el[3] - t0)
        tout = (el[4] - t0) if len(el) > 4 and el[4] is not None else dur
        mode = el[5] if len(el) > 5 else "pop"
        keep = len(el) > 6 and el[6]      # следующее состояние встаёт на это место — без угасания
        iw, ih = Image.open(png).size
        inputs += [*loop, png]
        if mode == "state":
            fc.append(f"[{idx}:v]format=rgba[e{j}]")
            fc.append(f"[{last}][e{j}]overlay={x}:{y}:enable='between(t,{tin:.3f},{tout:.3f})'[o{j}]")
        else:
            q = f"clip((t-{tin:.2f})/{POP}\\,0\\,1)"
            kk = "1" if mode == "frame" else f"(0.55+0.45*(1+2.70158*pow({q}-1\\,3)+1.70158*pow({q}-1\\,2)))"
            fout = f"fade=t=out:st={max(tin, tout - 0.2):.2f}:d=0.2:alpha=1," if tout < dur - 0.01 and not keep else ""
            fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={tin:.2f}:d=0.12:alpha=1,{fout}"
                      f"scale=w='max(2\\,trunc({iw}*{kk}/2)*2)':h='max(2\\,trunc({ih}*{kk}/2)*2)':eval=frame[e{j}]")
            end = f"{tout:.3f}" if keep else f"{tout:.2f}"
            fc.append(f"[{last}][e{j}]overlay=x='{x + iw / 2}-w/2':y='{y + ih / 2}-h/2'"
                      f":enable='between(t,{tin:.2f},{end})'[o{j}]")
        last, idx = f"o{j}", idx + 1
    gl = sc.get("glitch", [])
    if gl:   # цифровой сбой: сдвиг каналов, шум, скан-линии
        en = "+".join(f"between(t\\,{a - t0:.2f}\\,{a - t0 + d:.2f})" for a, d in gl)
        T.scanlines(p("scan"), W, H)
        inputs += [*loop, p("scan")]
        fc.append(f"[{last}]rgbashift=rh=-26:bh=26:rv=8:enable='{en}',noise=alls=38:allf=t:enable='{en}'[gl0]")
        fc.append(f"[gl0][{idx}:v]overlay=0:0:enable='{en}'[gl]")
        last, idx = "gl", idx + 1
    n = 0
    for ci, c in enumerate(caps):
        a, z = max(0.0, c["t0"] - t0), min(dur, c["t1"] - t0)
        if z <= 0 or a >= dur:
            continue
        ws = [w for w, _ in c["words"]]
        for wi, (_, wt) in enumerate(c["words"]):
            s0 = a if wi == 0 else max(a, wt - t0)
            s1 = min((c["words"][wi + 1][1] - t0) if wi + 1 < len(ws) else z, z)
            if s1 <= s0:
                continue
            path = p(f"cap_{ci}_{wi}")
            T.caption(path, ws, wi, CAP_W)
            cy = CAP_BOTTOM - Image.open(path).height
            inputs += [*loop, path]
            fc.append(f"[{last}][{idx}:v]overlay={CAP_X}:{cy}:enable='gte(t,{s0:.3f})*lt(t,{s1:.3f})'[c{n}]")
            last, idx, n = f"c{n}", idx + 1, n + 1
    for j, (tf, col) in enumerate(sc.get("flash", [])):
        a = max(0.0, tf - t0)
        T.flash(p(f"flash_{col}"), W, H, col)
        inputs += [*loop, p(f"flash_{col}")]
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={a:.2f}:d=0.04:alpha=1,"
                  f"fade=t=out:st={a + 0.06:.2f}:d=0.3:alpha=1[fl{j}]")
        fc.append(f"[{last}][fl{j}]overlay=0:0:enable='between(t,{a:.2f},{a + 0.4:.2f})'[f{j}]")
        last, idx = f"f{j}", idx + 1
    shakes = [max(0.0, ts - t0) for ts in sc.get("shake", [])]
    if shakes:   # тряска кадра на ударном слове
        amp = "+".join(f"between(t\\,{a:.2f}\\,{a + 0.35:.2f})*(1-(t-{a:.2f})/0.35)" for a in shakes)
        fc.append(f"[{last}]pad={W + 48}:{H + 48}:24:24:color={T.PAD_COLOR},"
                  f"crop={W}:{H}:x='24+18*sin(t*97)*({amp})':y='24+14*cos(t*83)*({amp})'[shk]")
        last = "shk"
    # полоса прогресса сверху — растёт на всю длину ролика
    fc.append(f"[{last}]drawbox=x=0:y=0:w='{W}*(t+{t0:.3f})/{TOTAL:.3f}':h={PROGRESS_H}:color=0xF3531B:t=fill[pg]")
    last = "pg"
    if k > 0:
        T.swipe(p("swipe"), W, H)
        inputs += [*loop, p("swipe")]
        fc.append(f"[{last}][{idx}:v]overlay=x='-{W}+{2 * W}*t/0.3':y=0:enable='lt(t,0.3)'[sw]")
        last, idx = "sw", idx + 1
    fc.append(f"[{last}]format=yuv420p[vout]")
    out = f"{TMP}/scene{k + 1}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]",
         "-an", "-t", f"{dur}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", out])
    return out


def sound_events(sc_list, bounds):
    ev = []
    for k, sc in enumerate(sc_list):
        if k > 0:
            ev.append((bounds[k] - 0.12, "whoosh", 0.5))
        for el in sc["els"]:
            mode = el[5] if len(el) > 5 else "pop"
            if mode == "pop":
                ev.append((el[3], "pop", 0.3))
        for tf, col in sc.get("flash", []):
            ev.append((tf, "hit", 0.45))
        for tc, _ in (sc.get("av") or {}).get("cuts", ()):
            if tc > bounds[k] + 0.05:
                ev.append((tc, "whoosh", 0.18))   # склейка-наезд — лёгкий вжух
        ev += sc.get("sfx", [])
    return ev


def main():
    os.makedirs(TMP, exist_ok=True)
    voice = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  AUDIO], capture_output=True, text=True).stdout)
    total = round(voice + TAIL, 2)
    global TOTAL
    TOTAL = total
    words = word_times()
    caps = caption_chunks(words, voice)
    sc = scenes(finder(words))
    bounds = BOUNDS + [total]
    for k, s in enumerate(sc):
        check_layout(k, s, bounds[k], bounds[k + 1], caps)
    if os.environ.get("CHECK"):
        print("layout ok")
        return
    only = os.environ.get("ONLY")
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
    padded = f"{TMP}/voice.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", AUDIO, "-af", f"apad=pad_dur={TAIL}", "-t", f"{total}", padded])
    mixed = SFX.mix(padded, sound_events(sc, bounds), f"{TMP}/mix.wav", f"{TMP}/sfx", bed_gain=0.12, total=total,
                    bed_fn=SFX.music_bed(MUSIC))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", mixed, "-map", "0:v",
         "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT])
    print("done", OUT)


if __name__ == "__main__":
    main()
