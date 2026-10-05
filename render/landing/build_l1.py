"""Лендинг, ролик 1 «Как принять возврат товара за 4 шага» — 16:9 и 9:16.

Механика — общий монтаж render/corner/montage.py (стандарт
docs/video-standard.md: весь кадр ↔ правый нижний угол, статичные
субтитры, элементы по таймингам whisper). Отличия от фарма-роликов:
  - палитра — дизайн-борд ниши ритейл (scratch/img/l1_board.png):
    тёмно-синий #1F2A44, коралл #F2643D, мятный #2BB59A, фон #FAF7F2;
    подменяется в brand_style ДО импорта cards/montage;
  - второй формат 9:16 (1080×1920): та же механика, своя геометрия
    (угол 360×640, субтитры 600 px), клипы HeyGen приближены по лицу;
  - новый приём — полоса шагов 1-2-3-4 (текущий шаг подсвечен) и под ней
    карточка шага, сменяющаяся на одном месте.

Ритм: весь кадр → угол (одна длинная сцена на все 4 шага) → весь кадр.

Запуск:  python3 -m render.landing.build_l1 h|v
Выход:   render/landing/l1-16x9.mp4 / l1-9x16.mp4
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

from render.corner import brand_style as S
from render.corner import geometry as G

FMT = (sys.argv[1] if len(sys.argv) > 1 else "h")
assert FMT in ("h", "v")

# ---------------------------------------------------------------- палитра ниши
NAVY = (31, 42, 68, 255)        # #1F2A44
CORAL = (242, 100, 61, 255)     # #F2643D
MINT = (43, 181, 154, 255)      # #2BB59A
WARM_BG = (250, 247, 242, 255)  # #FAF7F2
PALE = (243, 238, 230, 255)
S.BLUE, S.LIGHT_BLUE, S.GREEN, S.LIGHT_BG, S.TEXT_DARK = NAVY, CORAL, CORAL, WARM_BG, NAVY
S.ACCENT, S.ACCENT_SECONDARY = NAVY, CORAL

# ---------------------------------------------------------------- геометрия формата
if FMT == "v":
    G.FRAME_W, G.FRAME_H = 1080, 1920
    G.CORNER_W, G.CORNER_H = 360, 640
    G.CORNER_X, G.CORNER_Y = 1080 - 360 - 40, 1920 - 640 - 60
    G.SUBTITLE_W, G.SUBTITLE_Y = 600, 1440
    G.SUBTITLE_X_CENTERED = (1080 - 600) // 2
    G.SUBTITLE_X_CORNER = 40

from render.corner import cards as K      # noqa: E402  (после подмены палитры)
from render.corner import montage as M    # noqa: E402
from render.corner import static_captions as C  # noqa: E402
from render.corner.montage import item    # noqa: E402

K.NAVY, K.PALE_BLUE, K.SHADOW = NAVY, PALE, (31, 42, 68, 46)
M.NAVY = NAVY

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = f"{HERE}/_frames_{FMT}"
IMG = f"{ROOT}/scratch/img"
AUDIO = f"{ROOT}/scratch/l1-{FMT}-full-v2.mp3"
WHISPER = f"{ROOT}/scratch/l1-{FMT}-full-v2-whisper-1.json"
TEXTS = f"{ROOT}/docs/scenarios/landing-1-returns.md"
OUT = f"{HERE}/l1-{'16x9' if FMT == 'h' else '9x16'}.mp4"

# границы сцен — середины пауз (как резались клипы HeyGen)
BOUNDS = {"h": [0.0, 17.40, 51.53], "v": [0.0, 6.90, 25.38]}[FMT]
# v2 — клипы новой Анны (фото с нейтральным лицом, 05.10.2026 (8)): весь кадр —
# avatar_iv + expressiveness high, угол — avatar_iii
CLIPS = {"h": [f"{ROOT}/scratch/l1-h2-scene{k}.mp4" for k in (1, 2, 3)],
         "v": [f"{ROOT}/scratch/l1-v2-scene{k}.mp4" for k in (1, 2, 3)]}[FMT]


def f(name):
    return f"{TMP}/{name}.png"


def img(name):
    meta = json.load(open(f"{IMG}/{name}.json", encoding="utf-8"))
    assert meta["status"] == "ok", f"{name}: картинка не прошла QA"
    return f"{IMG}/{name}.png"


def h_of(made):
    return Image.open(made[0]).height - 2 * made[1]


def w_of(made):
    return Image.open(made[0]).width - 2 * made[1]


# ---------------------------------------------------------------- фон и новые компоненты

def make_background(path):
    """Тёплый фон борда + мягкие круги коралл/мятный."""
    W, H = G.FRAME_W, G.FRAME_H
    bg = Image.new("RGBA", (W, H), WARM_BG)
    deco = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(deco)
    d.ellipse([W - 420, -260, W + 220, 380], fill=(242, 100, 61, 22))
    d.ellipse([-220, H - 320, 260, H + 160], fill=(43, 181, 154, 22))
    Image.alpha_composite(bg, deco.filter(ImageFilter.GaussianBlur(2))).save(path)
    return path


M.make_background = make_background

STEP_LABELS = ["Выслушать", "Проверить", "Оформить", "Вернуть"]


def stepper(path, active, w):
    """Полоса шагов: 4 кружка-номера на линии, подписи; пройденные — мятные
    с галочкой, текущий — коралловый крупнее, следующие — серые."""
    h = 150
    img_ = K._card(w, h, K.WHITE if hasattr(K, "WHITE") else S.WHITE, radius=28)
    d = ImageDraw.Draw(img_)
    P = K.PAD
    n = len(STEP_LABELS)
    colw = (w - 40) / n
    xs = [P + 20 + colw * (k + 0.5) for k in range(n)]
    cy = P + 52
    for k in range(n - 1):
        col = MINT if k < active else (226, 222, 214, 255)
        d.line([(xs[k] + 30, cy), (xs[k + 1] - 30, cy)], fill=col, width=6)
    f_n, f_l = S.font(S.F_HEADLINE, 30), S.font(S.F_SEMIBOLD, 26 if w > 900 else 24)
    for k, (x, lab) in enumerate(zip(xs, STEP_LABELS)):
        r = 30 if k == active else 24
        fill = CORAL if k == active else MINT if k < active else (226, 222, 214, 255)
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=fill)
        if k < active:
            d.line([(x - 10, cy + 1), (x - 2, cy + 9), (x + 12, cy - 8)], fill=S.WHITE, width=5)
        else:
            num = str(k + 1)
            d.text((x - d.textlength(num, font=f_n) / 2, cy - 19), num, font=f_n,
                   fill=S.WHITE if k == active else (140, 136, 128, 255))
        col = NAVY if k == active else (150, 146, 138, 255) if k > active else MINT
        d.text((x - d.textlength(lab, font=f_l) / 2, cy + 44), lab, font=f_l, fill=col)
    img_.save(path)
    return path, P


def step_detail(path, icon_src, num, title, keys, w, isz=150):
    """Карточка текущего шага: крупная иконка, «шаг N», заголовок-глагол,
    ключевые слова реплики чипами."""
    P = K.PAD
    f_k, f_t, f_c = S.font(S.F_SEMIBOLD, 26), S.font(S.F_HEADLINE, 56), S.font(S.F_SEMIBOLD, 30)
    tx = 40 + isz + 36
    t_lines = K.wrap(title, f_t, w - tx - 30)
    # чипы — по строкам
    rows, cur, cw = [], [], 0
    for kword in keys:
        kw = ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(kword, font=f_c) + 44
        if cur and cw + kw > w - tx - 30:
            rows.append(cur)
            cur, cw = [], 0
        cur.append((kword, kw))
        cw += kw + 12
    if cur:
        rows.append(cur)
    h = max(40 + isz + 40, 40 + 36 + len(t_lines) * 64 + 16 + len(rows) * 62 + 30)
    im = K._card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(im)
    im.alpha_composite(K._icon(icon_src, isz), (P + 40, P + (h - isz) // 2))
    x, y = P + tx, P + 36
    d.text((x, y), f"ШАГ {num}", font=f_k, fill=CORAL)
    y += 36
    for line in t_lines:
        d.text((x, y), line, font=f_t, fill=NAVY)
        y += 64
    y += 16
    for row in rows:
        cx = x
        for kword, kw in row:
            d.rounded_rectangle([cx, y, cx + kw, y + 50], 25, fill=PALE)
            d.text((cx + 22, y + 9), kword, font=f_c, fill=NAVY)
            cx += kw + 12
        y += 62
    im.save(path)
    return path, P


def note_card(path, icon_src, kicker, text, w, isz=96):
    """Плашка-подсказка с мятной рамкой: «нет чека → выписка из банка»."""
    P = K.PAD
    f_k, f_t = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 38)
    lines = K.wrap(text, f_t, w - isz - 90)
    h = max(isz + 40, 30 + 34 + len(lines) * 46 + 26)
    im = K._card(w, h, S.WHITE, radius=24)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([P, P, P + w, P + h], 24, outline=MINT, width=4)
    im.alpha_composite(K._icon(icon_src, isz), (P + 22, P + (h - isz) // 2))
    x, y = P + isz + 46, P + 30
    d.text((x, y), kicker.upper(), font=f_k, fill=MINT)
    y += 34
    for line in lines:
        d.text((x, y), line, font=f_t, fill=NAVY)
        y += 46
    im.save(path)
    return path, P


def four_card(path, w):
    """Крупно «4 шага» + подпись «всё решают» (вместо узкого big_metric)."""
    P = K.PAD
    f_num, f_u, f_k = S.font(S.F_HEADLINE, 170), S.font(S.F_HEADLINE, 64), S.font(S.F_SEMIBOLD, 30)
    h = 220
    im = K._card(w, h, NAVY, radius=30)
    d = ImageDraw.Draw(im)
    x = P + 44
    d.text((x, P - 4), "4", font=f_num, fill=S.WHITE)
    x += d.textlength("4", font=f_num) + 22
    d.text((x, P + 46), "шага", font=f_u, fill=S.WHITE)
    d.rounded_rectangle([x, P + 130, x + 60, P + 136], 3, fill=CORAL)
    d.text((x, P + 150), "ВСЁ РЕШАЮТ", font=f_k, fill=CORAL)
    im.save(path)
    return path, P


def verbs_card(path, w, vertical=False):
    """Итог: четыре глагола-шага одной волной (номер + слово, стрелки)."""
    P = K.PAD
    f_k, f_v, f_n = S.font(S.F_SEMIBOLD, 24), S.font(S.F_HEADLINE, 40), S.font(S.F_HEADLINE, 24)
    if vertical:
        h = 30 + 34 + 4 * 66 + 20
    else:
        h = 30 + 34 + 4 * 64 + 24
    im = K._card(w, h, S.WHITE, radius=28)
    d = ImageDraw.Draw(im)
    x, y = P + 36, P + 30
    d.text((x, y), "ЗАПОМНИТЕ ПОРЯДОК", font=f_k, fill=CORAL)
    y += 44
    for k, v in enumerate(STEP_LABELS):
        d.ellipse([x, y, x + 44, y + 44], fill=CORAL if k == 3 else NAVY)
        num = str(k + 1)
        d.text((x + 22 - d.textlength(num, font=f_n) / 2, y + 8), num, font=f_n, fill=S.WHITE)
        d.text((x + 64, y - 2), v, font=f_v, fill=NAVY)
        y += 64
    im.save(path)
    return path, P


def today_tomorrow(path, w):
    """Сегодня спокойный возврат → завтра постоянный покупатель."""
    P = K.PAD
    f_k, f_t = S.font(S.F_SEMIBOLD, 26), S.font(S.F_HEADLINE, 44)
    half = w - 70
    l1 = K.wrap("Спокойный возврат", f_t, half - 60)
    l2 = K.wrap("Постоянный покупатель", f_t, half - 160)
    h = 34 + 34 + len(l1) * 52 + 26 + 44 + 34 + len(l2) * 52 + 34
    im = K._card(w, h, NAVY, radius=28)
    d = ImageDraw.Draw(im)
    x, y = P + 40, P + 34
    d.text((x, y), "СЕГОДНЯ", font=f_k, fill=(200, 206, 220, 255))
    y += 34
    for line in l1:
        d.text((x, y), line, font=f_t, fill=S.WHITE)
        y += 52
    y += 10
    d.polygon([(x + 10, y), (x + 34, y), (x + 22, y + 26)], fill=CORAL)
    y += 44
    d.text((x, y), "ЗАВТРА", font=f_k, fill=CORAL)
    y += 34
    for line in l2:
        d.text((x, y), line, font=f_t, fill=S.WHITE)
        y += 52
    ic = K._icon(img("l1_ic_loyal"), 120)
    im.alpha_composite(ic, (P + w - 150, P + h - 150))
    im.save(path)
    return path, P


# ---------------------------------------------------------------- тайминги

def clean_text():
    s = open(TEXTS, encoding="utf-8").read()
    if FMT == "h":
        body = s.split("## Текст 16:9 (до 60 с)")[1].split("\n---")[0]
    else:
        body = s.split("## Текст 9:16 (до 30 с)")[1].split("## Раскладка 9:16")[0]
        body = "\n".join(l for l in body.splitlines() if l.startswith("["))
    return C.strip_emotion_tags(re.sub(r"\s*\n\s*", " ", body.strip()))


def word_times(text, whisper_words):
    """Как montage.word_times, но слово, которого whisper не услышал
    (напр. «Первый:» — он пишет его цифрой «1.»), получает время СЛЕДУЮЩЕГО
    услышанного слова минус 0.45 с, а не предыдущего — иначе субтитр с ним
    появляется раньше, чем слово звучит (и даже в предыдущей сцене)."""
    import difflib
    src = text.split()
    a = [M.norm(w) for w in src]
    b = [M.norm(w["word"]) for w in whisper_words]
    times = [None] * len(src)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for j in range(blk.size):
            times[blk.a + j] = whisper_words[blk.b + j]["start"]
    nxt = None
    for i in range(len(times) - 1, -1, -1):
        if times[i] is None:
            times[i] = max(0.0, nxt - 0.45) if nxt is not None else whisper_words[-1]["start"]
        nxt = times[i]
    return list(zip(src, times))


def scene_words(k, words):
    """Слова сцены k со временем от начала сцены (запас 0.25 с — whisper
    иногда ставит начало первого слова в паузу перед границей)."""
    t0 = BOUNDS[k]
    t1 = BOUNDS[k + 1] if k + 1 < len(BOUNDS) else 1e9
    return [(w, max(0.0, t - t0)) for w, t in words if t0 - 0.25 <= t < t1 - 0.25]


# ---------------------------------------------------------------- сцены 16:9

L, R, W = 60, 1320, 540     # весь кадр: колонки по бокам от аватара
PX = 100                    # угол: контент от x=100


def h_scene1(T, dur):
    end = dur - 0.25
    topic = K.topic_card(f("h1_topic"), "Обучение персонала", "Возврат товара",
                         "Как принять без конфликта", w=W)
    chance = K.headline(f("h1_chance"), "Покупатель вернулся", "Не конфликт, а шанс", ["шанс"], size=58, w=W)
    four = four_card(f("h1_four"), W)
    t2 = T("конфликт")
    return [
        item(topic, L, 80, T("возврат") - 0.3, t2 - 0.2),
        item(chance, L, 80, t2, end),
        item(four, R, 80, T("четыре"), end),
    ]


STEPS_H = [
    # (номер, иконка, глагол, ключевые слова, слово-триггер)
    (1, "l1_ic_listen", "Улыбнитесь и выслушайте", ["не спорить", "не перебивать", "что случилось?"], "Шаг"),
    (2, "l1_ic_check", "Проверьте товар и покупку", ["ярлыки", "товарный вид", "чек"], "второй"),
    (3, "l1_ic_form", "Оформите заявление", ["паспорт", "причина", "подпись"], "третий"),
    (4, "l1_ic_refund", "Верните деньги", ["тем же способом", "спасибо, что пришли"], "четвертый"),
]


def h_scene2(T, dur):
    end = dur - 0.25
    t_steps = [max(T("Шаг"), M.MOVE_D), T("второй"), T("третий"), T("четвертый")]
    out = []
    sw = 1220
    for k in range(4):
        t_in, t_out = t_steps[k], (t_steps[k + 1] if k < 3 else end)
        out.append(item(stepper(f(f"h2_bar{k}"), k, sw), PX, 50, t_in, t_out if k < 3 else end))
    ill = K.image_card(f("h2_ill"), img("l1_ill_counter"), 560)
    out.append(item(ill, PX, 260, t_steps[0], end))
    dx, dw = PX + 560 + 40, 620
    for k, (num, icon, title, keys, _) in enumerate(STEPS_H):
        t_in, t_out = t_steps[k], (t_steps[k + 1] if k < 3 else end)
        card = step_detail(f(f"h2_step{k}"), img(icon), num, title, keys, dw, isz=120)
        out.append(item(card, dx, 260, t_in, t_out))
        if num == 2:
            note = note_card(f("h2_note"), img("l1_ic_bank"), "Нет чека — не беда", "Подойдёт выписка из банка", dw)
            out.append(item(note, dx, 260 + h_of(card) + 26, T("Нет"), t_out))
    return out


def h_scene3(T, dur):
    end = dur - 0.25
    verbs = verbs_card(f("h3_verbs"), W)
    tt = today_tomorrow(f("h3_tt"), W)
    return [
        item(verbs, L, 90, max(T("Выслушать"), M.MOVE_D), end),
        item(tt, R, 90, T("Спокойный"), end),
    ]


# ---------------------------------------------------------------- сцены 9:16

VX, VW = 60, 960            # контент по ширине кадра


def v_scene1(T, dur):
    end = dur - 0.25
    topic = K.topic_card(f("v1_topic"), "Обучение персонала", "Возврат товара за 4 шага",
                         "Не конфликт, а шанс", w=VW)
    return [item(topic, VX, 1130, 0.4, end)]


def v_scene2(T, dur):
    end = dur - 0.25
    t_steps = [max(T("Выслушайте"), M.MOVE_D), T("Проверьте"), T("Заявление"), T("Четвертый")]
    out = []
    for k in range(4):
        t_in, t_out = t_steps[k], (t_steps[k + 1] if k < 3 else end)
        out.append(item(stepper(f(f"v2_bar{k}"), k, VW), VX, 80, t_in, t_out))
    steps = [
        (1, "l1_ic_listen", "Выслушайте", ["не спорьте"]),
        (2, "l1_ic_check", "Проверьте", ["ярлыки", "вид", "чек"]),
        (3, "l1_ic_form", "Заявление", ["паспорт", "причина", "подпись"]),
        (4, "l1_ic_refund", "Верните деньги", ["тем же способом", "спасибо"]),
    ]
    ill = K.image_card(f("v2_ill"), img("l1_ill_counter"), VW - 120)
    out.append(item(ill, VX + 60, 620, t_steps[0], end))
    for k, (num, icon, title, keys) in enumerate(steps):
        t_in, t_out = t_steps[k], (t_steps[k + 1] if k < 3 else end)
        card = step_detail(f(f"v2_step{k}"), img(icon), num, title, keys, VW, isz=130)
        out.append(item(card, VX, 290, t_in, t_out))
        if num == 2:
            note = note_card(f("v2_note"), img("l1_ic_bank"), "Нет чека", "Выписка из банка", 580, isz=80)
            out.append(item(note, 40, 1236, T("нет"), t_out))
    return out


def v_scene3(T, dur):
    end = dur - 0.25
    tt = today_tomorrow(f("v3_tt"), VW)
    return [item(tt, VX, 1080, max(0.3, M.MOVE_D), end)]


# ---------------------------------------------------------------- сборка

def prep_vertical_clip(src, dst):
    """Клип 9:16 (Анна в полный рост) — приближение ×1.4 к верхней части
    кадра, чтобы лицо было крупнее (указание пользователя 05.10.2026)."""
    if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src):
        return dst
    M.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
           "crop=772:1372:154:40,scale=1080:1920,setsar=1", "-an", "-c:v", "libx264", "-crf", "16",
           "-preset", "fast", dst])
    return dst


def main():
    os.makedirs(TMP, exist_ok=True)
    wh = json.load(open(WHISPER, encoding="utf-8"))
    words = word_times(clean_text(), wh["words"])
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                  "csv=p=0", AUDIO], capture_output=True, text=True).stdout)
    plan = {"h": [("full", "none", h_scene1), ("corner", "shrink", h_scene2), ("full", "grow", h_scene3)],
            "v": [("full", "none", v_scene1), ("corner", "shrink", v_scene2), ("full", "grow", v_scene3)]}[FMT]
    parts = []
    for k, (mode, enter, build) in enumerate(plan):
        t0 = BOUNDS[k]
        t1 = BOUNDS[k + 1] if k + 1 < len(BOUNDS) else total
        dur = round(t1 - t0, 3)
        sw = scene_words(k, words)
        clip = CLIPS[k]
        if FMT == "v":
            clip = prep_vertical_clip(clip, f"{TMP}/clip{k + 1}.mp4")
        items = build(M.finder(sw), dur)
        out = f"{TMP}/scene{k + 1}.mp4"
        M.render_scene(clip, dur, sw, mode, enter, items, out, TMP)
        parts.append(out)
        print("scene", k + 1, mode, enter, dur, flush=True)
    M.concat(parts, AUDIO, OUT, TMP)
    print("done", OUT)


if __name__ == "__main__":
    main()
