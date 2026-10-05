"""Лендинг, ролик 1 «Возврат товара за 4 шага» — вертикаль 9:16, виток 3.

Стиль «Графит и красный» (render/landing/theme_graphite.py, борд
scratch/img/l1c_board_graphite.png), новая Анна (scratch/img/l1g_anna_9x16.png),
голос Victoria. В отличие от первых версий раскладка МЕНЯЕТСЯ по ходу ролика
(решение пользователя 05.10.2026): ведущая приходит из HeyGen одним клипом с
прозрачным фоном (webm, VP9 с альфой) и в каждой сцене стоит по-своему:

  1 full    — Анна на весь кадр, крупный заголовок над головой
  2 type    — типографика на весь экран: «4 шага», без Анны
  3 bottom  — Анна в нижней половине, над ней карточка шага (1 → 2) + «нет чека»
  4 split   — Анна справа, слева «ШАГ 3 Заявление» и чек-лист
  5 circle  — лицо Анны в красном круге, «ШАГ 4 Верните деньги» + чек-лист
  6 final   — Анна на весь кадр, итог «сегодня → завтра»

Смена раскладки — жёсткая склейка с красной диагональю, пролетающей через кадр.
Субтитры — чёрная плашка с красной полосой, по предложениям, статичные.

Запуск:  python3 -m render.landing.build_l1_v3
Выход:   render/landing/l1-v3-9x16.mp4
"""
import difflib
import json
import os
import re
import subprocess

from PIL import Image

from render.landing import theme_graphite as T

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = f"{HERE}/_frames_v3"
AUDIO = f"{ROOT}/scratch/l1-v3-full-v1.mp3"
WHISPER = f"{ROOT}/scratch/l1-v3-full-v1-whisper-1.json"
TEXTS = f"{ROOT}/docs/scenarios/landing-1-returns.md"
CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l1-v3-anna.webm")
OUT = f"{HERE}/l1-v3-9x16.mp4"

W, H, FPS = 1080, 1920, 25
# границы сцен — середины пауз между предложениями (silencedetect)
BOUNDS = [0.0, 4.23, 6.05, 13.87, 17.31, 21.27]
CAP_Y, CAP_X, CAP_W = 1610, 60, 960
APPEAR = 0.35


def run(cmd):
    subprocess.run(cmd, check=True)


def p(name):
    return f"{TMP}/{name}.png"


def norm(w):
    return re.sub(r"[^\w]+", "", w.lower().replace("ё", "е"))


TEXT_HEAD, TEXT_END = "## Текст 9:16 (до 30 с)", "## Текст 16:9, виток 3"
CAP_BOTTOM = None   # для 16:9 плашка субтитров прижимается к низу кадра


def clean_text():
    s = open(TEXTS, encoding="utf-8").read()
    body = s.split(TEXT_HEAD)[1].split(TEXT_END)[0]
    line = [l for l in body.splitlines() if l.startswith("[")][0]
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", "", line)).strip()


def word_times():
    """Слово сценария → время начала из whisper; неуслышанное — от соседа справа."""
    src = clean_text().split()
    ww = json.load(open(WHISPER, encoding="utf-8"))["words"]
    a, b = [norm(w) for w in src], [norm(w["word"]) for w in ww]
    times = [None] * len(src)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for j in range(blk.size):
            times[blk.a + j] = ww[blk.b + j]["start"]
    nxt = None
    for i in range(len(times) - 1, -1, -1):
        if times[i] is None:
            times[i] = max(0.0, nxt - 0.4) if nxt is not None else ww[-1]["start"]
        nxt = times[i]
    return list(zip(src, times))


def captions(words, total):
    """Субтитры по предложениям; длинное делится на равные части ≤2 строк."""
    f = T.font(T.F_BODY_B, 46)
    sents, cur = [], []
    for k, (w, t) in enumerate(words):
        cur.append((w, t))
        nxt = words[k + 1][0] if k + 1 < len(words) else "A"
        if re.search(r"[.!?]$", w) or (w.endswith(":") and False):
            sents.append(cur)
            cur = []
        elif w.endswith("—") and nxt[:1].islower():
            pass
    if cur:
        sents.append(cur)
    chunks = []
    for s in sents:
        text = " ".join(w for w, _ in s)
        lines = T.wrap(text, f, CAP_W - 80)
        n = (len(lines) + 1) // 2
        k = len(s)
        for i in range(n):
            part = s[round(i * k / n):round((i + 1) * k / n)]
            chunks.append((T.wrap(" ".join(w for w, _ in part), f, CAP_W - 80), part[0][1]))
    out = []
    for i, (lines, t0) in enumerate(chunks):
        t1 = chunks[i + 1][1] if i + 1 < len(chunks) else total
        out.append({"lines": lines, "t0": t0, "t1": t1})
    out[0]["t0"] = 0.0
    return out


def finder(words):
    def T_(needle, after=0.0):
        n = norm(needle)
        for w, t in words:
            if norm(w) == n and t >= after:
                return t
        raise KeyError(needle)
    return T_


# ---------------------------------------------------------------- сцены

def scenes(F):
    """Возвращает список сцен: bg, avatar (размещение) и элементы.
    Время элементов — абсолютное, потом переводится в локальное."""
    b = BOUNDS
    T.background(p("bg_diag"), W, H, "diag")
    T.background(p("bg_type"), W, H, "type")
    T.background(p("bg_split"), W, H, "split")
    T.background(p("bg_plain"), W, H, "plain")
    full = {"kind": "scale", "s": 0.86, "x": 75, "y": H - int(1920 * 0.86)}
    final = {"kind": "scale", "s": 0.80, "x": 108, "y": H - int(1920 * 0.80)}
    return [
        {"bg": p("bg_diag"), "av": full, "els": [
            (T.headline(p("s1_head"), ["Возврат — не", "конфликт, а шанс"], 980, size=96,
                        red_words=["шанс"], kicker="Обучение персонала"), 60, 90, 0.3)]},
        {"bg": p("bg_type"), "av": None, "els": [
            (T.big_number(p("s2_num"), "4", ["ШАГА"], "решают всё", W), 0, 260, b[1] + 0.05)]},
        {"bg": p("bg_diag"), "av": {"kind": "scale", "s": 0.70, "x": 162, "y": H - int(1920 * 0.70) + 120}, "els": [
            (T.step_card(p("s3_step1"), 1, "Выслушайте", "Не спорьте и не перебивайте", 960), 60, 120,
             b[2] + 0.1, F("Второй") - 0.05),
            (T.step_card(p("s3_step2"), 2, "Проверьте", "Ярлыки, товарный вид, чек", 960), 60, 120,
             F("Второй")),
            (T.note(p("s3_note"), "Нет чека — не беда", "Подойдёт выписка из банка", 960), 60, 480,
             F("нет")),
        ]},
        {"bg": p("bg_split"), "av": {"kind": "scale", "s": 0.95, "x": 380, "y": 96}, "els": [
            (T.panel_title(p("s4_title"), 3, "Заявление", 460), 50, 200, b[3] + 0.1),
            (T.check_row(p("s4_c1"), "Паспорт", 420), 50, 560, F("паспорт")),
            (T.check_row(p("s4_c2"), "Причина", 420), 50, 690, F("причина")),
            (T.check_row(p("s4_c3"), "Подпись", 420), 50, 820, F("подпись")),
        ]},
        {"bg": p("bg_plain"), "av": {"kind": "circle", "cx": 540, "cy": 520, "r": 290, "size": 440,
                                      "x": (W - 440) // 2, "y": 130}, "els": [
            (T.headline(p("s5_head"), ["Верните", "деньги"], 960, size=130, red_words=["деньги"],
                        kicker="Шаг 4"), 60, 660, b[4] + 0.1),
            (T.check_row(p("s5_c1"), "Тем же способом", 960), 60, 1120, F("способом") - 0.3),
            (T.check_row(p("s5_c2"), "Скажите спасибо", 960), 60, 1250, F("спасибо") - 0.3),
        ]},
        {"bg": p("bg_diag"), "av": final, "els": [
            (T.statement(p("s6_stmt"), "Спокойный возврат", "Постоянный покупатель", 960), 60, 90,
             b[5] + 0.1)]},
    ]


def render_scene(k, sc, t0, t1, caps):
    dur = round(t1 - t0, 3)
    loop = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur}", "-i"]
    inputs = [*loop, sc["bg"]]
    fc = [f"[0:v]format=rgba,fps={FPS}[bg]"]
    last, idx = "bg", 1
    av = sc["av"]
    if av:
        inputs += ["-c:v", "libvpx-vp9", "-ss", f"{t0}", "-t", f"{dur}", "-i", CLIP]
        if av["kind"] == "scale":
            fc.append(f"[{idx}:v]format=rgba,fps={FPS},scale={int(1080 * av['s'])}:-1[av]")
            fc.append(f"[{last}][av]overlay={av['x']}:{av['y']}:shortest=0[a0]")
        else:   # лицо в круге: вырез → графитовая подложка → круглая маска + кольцо
            r, size = av["r"], av["size"]
            T.circle_mask(p("mask"), size)
            T.circle_ring(p("ring"), size)
            inputs += [*loop, p("mask"), *loop, p("ring")]
            fc.append(f"color=c=0x22252B:s={size}x{size}:r={FPS}:d={dur}[sq]")
            fc.append(f"[{idx}:v]format=rgba,fps={FPS},crop={2 * r}:{2 * r}:{av['cx'] - r}:{av['cy'] - r},"
                      f"scale={size}:{size}[face]")
            fc.append(f"[sq][face]overlay=0:0[fsq]")
            fc.append(f"[{idx + 1}:v]format=gray,fps={FPS}[m]")
            fc.append(f"[fsq][m]alphamerge[circ]")
            fc.append(f"[{last}][circ]overlay={av['x']}:{av['y']}[a1]")
            fc.append(f"[{idx + 2}:v]format=rgba,fps={FPS}[rg]")
            fc.append(f"[a1][rg]overlay={av['x'] - 12}:{av['y'] - 12}[a0]")
            idx += 2
        last, idx = "a0", idx + 1
    for j, el in enumerate(sc["els"]):
        png, x, y, tin = el[0], el[1], el[2], el[3] - t0
        tout = (el[4] - t0) if len(el) > 4 else dur
        tin = max(0.0, tin)
        cut = len(el) > 5 and el[5] == "cut"   # смена состояния на месте — без въезда
        inputs += [*loop, png]
        if cut:
            fc.append(f"[{idx}:v]format=rgba[e{j}]")
        else:
            fc.append(f"[{idx}:v]format=rgba,fade=t=in:st={tin:.2f}:d={APPEAR}:alpha=1,"
                      f"fade=t=out:st={max(tin, tout - 0.2):.2f}:d=0.2:alpha=1[e{j}]")
        slide = "0" if cut else f"90*pow(1-clip((t-{tin:.2f})/{APPEAR}\\,0\\,1)\\,2)"
        fc.append(f"[{last}][e{j}]overlay=x='{x}-{slide}':y={y}:enable='between(t,{tin:.2f},{tout:.2f})'[o{j}]")
        last, idx = f"o{j}", idx + 1
    for j, c in enumerate(caps):
        a, z = max(0.0, c["t0"] - t0), min(dur, c["t1"] - t0)
        if z <= 0 or a >= dur:
            continue
        T.caption(p(f"cap_{k}_{j}"), c["lines"], CAP_W)
        cy = CAP_Y if CAP_BOTTOM is None else CAP_BOTTOM - Image.open(p(f"cap_{k}_{j}")).height
        inputs += [*loop, p(f"cap_{k}_{j}")]
        fc.append(f"[{last}][{idx}:v]overlay={CAP_X}:{cy}:enable='gte(t,{a:.2f})*lt(t,{z:.2f})'[c{j}]")
        last, idx = f"c{j}", idx + 1
    if k > 0:   # смена раскладки: красная диагональ пролетает через кадр
        T.slash(p("slash"), W, H)
        inputs += [*loop, p("slash")]
        fc.append(f"[{last}][{idx}:v]overlay=x='-{W}+{2 * W}*t/0.35':y=0:enable='lt(t,0.35)'[sl]")
        last, idx = "sl", idx + 1
    fc.append(f"[{last}]format=yuv420p[vout]")
    out = f"{TMP}/scene{k + 1}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]",
         "-an", "-t", f"{dur}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", out])
    return out


def main():
    os.makedirs(TMP, exist_ok=True)
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                  "csv=p=0", AUDIO], capture_output=True, text=True).stdout)
    words = word_times()
    caps = captions(words, total)
    sc = scenes(finder(words))
    bounds = BOUNDS + [total]
    parts = []
    for k, s in enumerate(sc):
        parts.append(render_scene(k, s, bounds[k], bounds[k + 1], caps))
        print("scene", k + 1, flush=True)
    lst = f"{TMP}/concat.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{x}'\n" for x in parts)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", AUDIO, "-map", "0:v",
         "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT])
    print("done", OUT)


if __name__ == "__main__":
    main()
