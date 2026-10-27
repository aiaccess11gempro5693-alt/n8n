"""Лендинг, ролик 4 «Продукт за 60 секунд» — сервис доставки «Быстро», вертикаль 9:16.

Стиль A «Свежий рынок» (render/landing/theme_product.py, борд
scratch/img/l4_board2_a.png), ведущий — сборщик заказов (scratch/img/l4_host_d2.png
→ HeyGen photo avatar 665d8a82a44ecc41db71e40dbf6b9dfc, клип webm с прозрачным
фоном), голос Max (eleven_v3, Uv3rf12Omd9Asyv54Bqw). Сценарий —
docs/scenarios/landing-4-delivery.md. Движок — render/landing/build_l3.py
(render_scene / check_layout / субтитры со словом-подсветкой, наезды, вспышки,
тряска, звук), здесь — свои сцены, свой подклад и свои звуки.

Раскладка меняется каждую сцену (2–4 с):
  1 hook   — продуктовый кадр: пустой холодильник, «Гости через ЧАС», таймер
             60:00, штамп «Пусто!»
  2 intro  — ведущий на весь кадр, над головой выпрыгивает логотип «Быстро»
  3 раз    — зелёный фон, ведущий справа внизу, слева «60 мин до самой двери»
  4 два    — томатный фон без ведущего: ценник «0 ₽ от 1 000 ₽» + штамп «Бесплатно»
  5 три    — лицо ведущего в круге сверху, ниже телефон с картой + чип «курьер»
  6 было/стало — типографика без ведущего: серое «было» → зелёное «3 касания»
  7 кому   — ведущий ниже, над ним по очереди чипы аудиторий
  8 cta    — кадр с пакетом у двери + кнопка «Скачать «Быстро»»
  9 финал  — ведущий на весь кадр, наезд и штамп «Соберу сам!»

Запуск:  python3 -m render.landing.build_l4
Выход:   render/landing/l4-9x16.mp4
"""
import os
import subprocess

from PIL import Image

from render.landing import build_l1_v3 as V
from render.landing import build_l3 as B
from render.landing import sfx as SFX
from render.landing import theme_product as T

ROOT, HERE = B.ROOT, B.HERE
IMG = f"{ROOT}/scratch/img"
W, H = 1080, 1920

B.T = T
B.TMP = f"{HERE}/_frames_l4"
B.AUDIO = f"{ROOT}/scratch/l4-v-full-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l4-v-host.webm")
B.OUT = f"{HERE}/l4-9x16.mp4"
B.CAP_W, B.CAP_X, B.CAP_BOTTOM = 980, 50, 1850
B.SHOW = {"шестьдесят": "60", "тысячи": "1 000", "три": "3"}
# границы сцен — середины пауз между предложениями (silencedetect)
B.BOUNDS = [0.0, 3.25, 6.44, 9.85, 13.18, 16.46, 21.70, 24.66, 26.08]
V.TEXTS = f"{ROOT}/docs/scenarios/landing-4-delivery.md"
V.WHISPER = f"{ROOT}/scratch/l4-v-full-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 9:16 под сборщика, v2", "## Набросок раскладки"

# Силуэт ведущего в кадре клипа HeyGen 1080×1920 (голова и плечи; ниже —
# корпус в фартуке, там допустимы субтитры). Измерено по альфе клипа.
B.AVATAR_BOX = tuple(int(v) for v in os.environ.get("AVATAR_BOX", "140,240,980,1060").split(","))
B.FACE = tuple(int(v) for v in os.environ.get("FACE", "540,590,300").split(","))
B.CLIP_BOTTOM = int(os.environ.get("CLIP_BOTTOM", "1769"))
B.FACE_Y = B.FACE[1] / 1920

p = B.p

# общие настройки main(), ролики-наследники переопределяют: L.BED = SFX.pad
BED, BED_GAIN, STAMP_FLASH = SFX.groove, 0.28, "yellow"

# whisper пишет некоторые слова иначе, чем в тексте: слово сценария → слово whisper
ALIAS = {"БЕСПЛАТНО.": "бесплатная", "Два:": None}


def word_times():
    """Тайминги слов (V.word_times) + сопоставление слов, которые whisper
    записал по-своему; «—» перед таким словом берёт его время."""
    import json
    words = V.word_times()
    ww = json.load(open(V.WHISPER, encoding="utf-8"))["words"]
    out = list(words)
    for i, (w, t) in enumerate(out):
        a = ALIAS.get(w)
        if a:
            hit = [x["start"] for x in ww if V.norm(x["word"]) == a]
            if hit:
                out[i] = (w, hit[0])
                if i and out[i - 1][0] == "—":
                    out[i - 1] = ("—", hit[0])
    return out


def size(path):
    return Image.open(path).size


def cx(path, center=W / 2):
    return int(center - size(path)[0] / 2)


def host(s=1.0, cxx=540, y=0, zoom=0.0, punch=()):
    """Ведущий с центром силуэта в cxx; срез клипа всегда ниже кадра."""
    return {"kind": "scale", "s": s, "x": cxx - 540 * s, "y": y, "zoom": zoom, "punch": list(punch)}


def scenes(F):
    b = B.BOUNDS
    ph = lambda n: f"{IMG}/l4a_p_{n}.png"
    T.background(p("bg_doodle"), W, H, "doodle", seed=1)
    T.background(p("bg_plain"), W, H, "plain")
    T.background(p("bg_green"), W, H, "green", seed=2)
    T.background(p("bg_tomato"), W, H, "tomato", seed=3)
    T.photo_bg(p("bg_fridge"), ph("fridge"), W, H, ax=0.3, ay=0.5)
    T.photo_bg(p("bg_bag"), ph("bag"), W, H, ax=0.7, ay=0.5)

    s1_head = T.headline(p("s1_head"), [[("Гости через", "k")], [("ЧАС!", "T")]], 1000, size=118)
    s1_timer = T.timer(p("s1_timer"), "60:00", size=150)
    s1_empty = T.sticker_text(p("s1_empty"), "Пусто!", fill=T.INK, size=96, angle=8)
    s2_logo = T.logo(p("s2_logo"), size=112)
    s2_sp = T.sparkles(p("s2_sp"), 170)
    s3_num = T.big_number(p("s3_num"), "60", "мин", "до самой двери", w=700)
    s3_head = T.headline(p("s3_head"), [[("Раз:", "w")]], 500, size=110)
    s4_tag = T.price_tag(p("s4_tag"), w=760, angle=5)
    s4_free = T.sticker_text(p("s4_free"), "Бесплатно!", fill=T.GREEN, size=104, angle=-7)
    s4_head = T.headline(p("s4_head"), [[("Два:", "w")]], 500, size=110)
    s5_ring = T.ring(p("s5_ring"), 600)
    s5_phone = T.photo_card(p("s5_phone"), ph("phone"), 560, 640, ay=0.38, angle=-3)
    s5_chip = T.map_chip(p("s5_chip"), "Курьер на карте")
    s6_was = T.was_card(p("s6_was"), ["очереди", "пакеты", "пробки"], w=900)
    s6_arrow = T.down_arrow(p("s6_arrow"), 160, T.GREEN)
    s6_now = T.now_card(p("s6_now"), w=900)
    s7_c1 = T.chip(p("s7_c1"), "занятым", fill=T.GREEN, ink=T.WHITE, size=74, angle=-4, dot=T.MUSTARD)
    s7_c2 = T.chip(p("s7_c2"), "мамам", fill=T.TOMATO, ink=T.WHITE, size=74, angle=4, dot=T.MUSTARD)
    s7_c3 = T.chip(p("s7_c3"), "всем, кому дорог вечер", fill=T.MUSTARD, ink=T.INK, size=66, angle=-2,
                   dot=T.GREEN)
    s8_cta = T.cta_button(p("s8_cta"), "Скачать «Быстро»", w=900)
    s8_logo = T.logo(p("s8_logo"), size=110, angle=4)
    s9_sam = T.sticker_text(p("s9_sam"), "Соберу сам!", fill=T.TOMATO, size=110, angle=-6)

    return [
        # 1 hook — продукт: пустой холодильник
        {"bg": p("bg_fridge"), "av": None, "sfx": [(0.05, "tick", 0.35)], "els": [
            (s1_head, 40, 40, 0.05),
            (s1_timer, W - size(s1_timer)[0] - 20, 430, F("холодильник")),
            (s1_empty, 470, 900, F("ПУСТОЙ?") + 0.05, None, "stamp"),
        ]},
        # 2 intro — ведущий на весь кадр, логотип над головой
        {"bg": p("bg_doodle"), "av": host(1.0, 540, 200, zoom=0.03, punch=[F("«Быстро».")]),
         "flash": [(F("«Быстро».") + 0.05, "yellow")], "sfx": [(F("«Быстро»."), "ding", 0.4)], "els": [
            (s2_logo, cx(s2_logo), 10, F("заказы") + 0.1),
            (s2_sp, W - 190, 20, F("«Быстро»."), None, "frame"),
        ]},
        # 3 раз — зелёный фон, ведущий справа внизу, слева 60 мин
        {"bg": p("bg_green"), "av": host(0.72, 800, 700), "sfx": [(b[2] + 0.4, "beep", 0.4)], "els": [
            (s3_head, 40, 40, b[2] + 0.1),
            (s3_num, 20, 290, F("шестьдесят")),
        ]},
        # 4 два — томатный фон, ценник
        {"bg": p("bg_tomato"), "av": None, "sfx": [(F("тысячи") , "ding", 0.45)], "els": [
            (s4_head, 40, 40, b[3] + 0.1),
            (s4_tag, cx(s4_tag), 290, F("тысячи") - 0.15),
            (s4_free, cx(s4_free), 1170, F("БЕСПЛАТНО.") + 0.05, None, "stamp"),
        ]},
        # 5 три — лицо в круге, телефон с картой
        {"bg": p("bg_doodle"), "av": {"kind": "circle", "size": 520, "x": (W - 520) // 2, "y": 60},
         "sfx": [(F("карте"), "click", 0.5), (F("карте") + 0.15, "beep", 0.35)], "els": [
            (s5_ring, (W - size(s5_ring)[0]) // 2, 20, b[4] + 0.05, None, "frame"),
            (s5_phone, cx(s5_phone), 640, F("Три:") + 0.1),
            (s5_chip, cx(s5_chip), 1440, F("карте")),
        ]},
        # 6 было → стало — типографика
        {"bg": p("bg_plain"), "av": None,
         "flash": [(F("ТРИ") + 0.05, "green")],
         "sfx": [(F("ТРИ"), "bass", 0.55), (F("касания"), "click", 0.45),
                 (F("касания") + 0.18, "click", 0.45), (F("касания") + 0.36, "click", 0.45)], "els": [
            (s6_was, cx(s6_was), 40, F("Было:")),
            (s6_arrow, cx(s6_arrow), 640, F("Стало:") - 0.1),
            (s6_now, cx(s6_now), 840, F("Стало:")),
        ]},
        # 7 кому — ведущий ниже, над ним чипы аудиторий
        {"bg": p("bg_doodle"), "av": host(0.86, 540, 580, zoom=0.03, punch=[F("вечер.")]), "els": [
            (s7_c1, 40, 40, F("занятых,")),
            (s7_c2, W - size(s7_c2)[0] - 40, 262, F("мам,")),
            (s7_c3, cx(s7_c3), 490, F("всех,")),
        ]},
        # 8 cta — пакет у двери, кнопка
        {"bg": p("bg_bag"), "av": None, "sfx": [(F("Скачайте") + 0.1, "click", 0.55)], "els": [
            (s8_logo, cx(s8_logo), 60, b[7] + 0.05),
            (s8_cta, cx(s8_cta), 400, F("Скачайте")),
        ]},
        # 9 финал — ведущий, штамп «Соберу сам!»
        {"bg": p("bg_doodle"), "av": host(1.0, 540, 260, zoom=0.04, punch=[F("соберу")]), "els": [
            (s9_sam, cx(s9_sam), 40, F("соберу"), None, "stamp"),
        ]},
    ]


def sound_events(sc_list, bounds):
    """Звук из событий кадра под тему: смена сцены — свуш, появление — поп,
    штамп — бас-удар + шлепок, вспышка/наезд — бас; плюс свои звуки сцены."""
    ev = []
    for k, sc in enumerate(sc_list):
        if k > 0:
            ev.append((bounds[k] - 0.12, "whoosh", 0.5))
        for el in sc["els"]:
            mode = el[5] if len(el) > 5 else "pop"
            if mode == "stamp":
                ev += [(el[3], "stamp", 0.7), (el[3], "bass", 0.55)]
            elif mode != "frame":
                ev.append((el[3], "pop", 0.3))
        av = sc.get("av") or {}
        for tp in av.get("punch", ()):
            ev.append((tp, "bass", 0.4))
        ev += sc.get("sfx", [])
    return ev


def main():
    os.makedirs(B.TMP, exist_ok=True)
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                  "csv=p=0", B.AUDIO], capture_output=True, text=True).stdout)
    words = word_times()
    caps = B.caption_chunks(words, total)
    sc = B.enrich(scenes(V.finder(words)))
    for s in sc:   # у штампа вспышка — тёплая (STAMP_FLASH), не тревожная красная
        s["flash"] = [(t, STAMP_FLASH if c == "red" else c) for t, c in s.get("flash", [])]
    sc[-1]["flash"] = []   # финал не заливаем вспышкой — последний кадр должен читаться
    bounds = B.BOUNDS + [total]
    for k, s in enumerate(sc):
        B.check_layout(k, s, bounds[k], bounds[k + 1], caps)
    if os.environ.get("CHECK"):
        print("layout ok")
        return
    only = os.environ.get("ONLY")
    parts = []
    for k, s in enumerate(sc):
        if only and str(k + 1) not in only.split(","):
            continue
        parts.append(B.render_scene(k, s, bounds[k], bounds[k + 1], caps))
        print("scene", k + 1, flush=True)
    if only:
        return
    lst = f"{B.TMP}/concat.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{x}'\n" for x in parts)
    mixed = SFX.mix(B.AUDIO, sound_events(sc, bounds), f"{B.TMP}/mix.wav", f"{B.TMP}/sfx", total=total,
                    bed_fn=BED, bed_gain=BED_GAIN)
    B.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", mixed, "-map", "0:v",
           "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
           B.OUT])
    print("done", B.OUT)


if __name__ == "__main__":
    main()
