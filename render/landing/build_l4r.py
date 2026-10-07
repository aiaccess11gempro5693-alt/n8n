"""Лендинг, ролик 4, виток 2 — «Ужин из видео», сервис «Повтори», вертикаль 9:16.

Нейросеть превращает видео-рецепт из ленты в корзину продуктов, учитывает,
что уже есть дома, курьер — за 15 минут. Стиль A «Свежий рынок»
(render/landing/theme_product.py), ведущая — рыжая фуд-блогерша
(scratch/img/l4r_host_2.png → HeyGen photo avatar 98082e6c9f96dd72faba9a17b491260f,
клип webm с прозрачным фоном), голос Viktoriia (eleven_v3, 8M81RK3MD7u4DOJpu2G5).
Сценарий — docs/scenarios/landing-4-recipe.md. Движок — build_l3 через build_l4.

Раскладка (ведущая — в разумных количествах, как в роликах 1 и 3):
  1 hook   — кадр-фото: лента с видео-рецептом, «Рецепт в ленте — хочу сейчас!»
  2        — ведущая на весь кадр, логотип «Повтори» над головой
  3        — без ведущей: ингредиенты + корзина, галочки по словам
  4        — фото холодильника: «уже дома — не покупаем», зачёркнутые чипы
  5        — ведущая справа, слева специи + штамп «Найдено!», затем «6 порций»
  6        — зелёный фон, лицо в круге, «15 мин — курьер у двери»
  7        — без ведущей: готовое блюдо, штамп «Увидела — повторила!»
  8 финал  — ведущая на весь кадр, кнопка «Скачать «Повтори»»

Запуск:  python3 -m render.landing.build_l4r
Выход:   render/landing/l4r-9x16.mp4
"""
import os

from render.landing import build_l1_v3 as V
from render.landing import build_l3 as B
from render.landing import build_l4 as L
from render.landing import theme_product as T

ROOT, HERE = B.ROOT, B.HERE
IMG = f"{ROOT}/scratch/img"
W, H = 1080, 1920

B.TMP = f"{HERE}/_frames_l4r"
B.AUDIO = f"{ROOT}/scratch/l4r-v2-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l4r-v2-host.webm")
B.OUT = f"{HERE}/l4r-9x16.mp4"
B.SHOW = {"пятнадцать": "15", "тридцать": "30"}
# границы сцен — середины пауз (3→4 режется между словами: пауз там нет)
B.BOUNDS = [0.0, 3.86, 5.50, 8.45, 10.56, 13.60, 17.39, 20.18]
V.TEXTS = f"{ROOT}/docs/scenarios/landing-4-recipe.md"
V.WHISPER = f"{ROOT}/scratch/l4r-v2-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 9:16 (до 30 с), v2", "## Набросок раскладки"
# whisper склеивает «рецепт и» → «рецепты», «курьер у» → «курьеру», пишет числа цифрами
L.ALIAS = {"рецепт": "рецепты", "курьер": "курьеру", "пятна́дцать": "15", "тридцать": "30"}

# Силуэт ведущей в клипе HeyGen 1080×1920 (голова и плечи) — измерен по альфе.
B.AVATAR_BOX = tuple(int(v) for v in os.environ.get("AVATAR_BOX", "180,380,900,1000").split(","))
B.FACE = tuple(int(v) for v in os.environ.get("FACE", "530,560,230").split(","))
B.CLIP_BOTTOM = int(os.environ.get("CLIP_BOTTOM", "1769"))
B.FACE_Y = B.FACE[1] / 1920

p = B.p
size, cx, host = L.size, L.cx, L.host


def scenes(F):
    b = B.BOUNDS
    ph = lambda n: f"{IMG}/l4r_p_{n}.png"
    T.background(p("bg_doodle"), W, H, "doodle", seed=7)
    T.background(p("bg_plain"), W, H, "plain")
    T.background(p("bg_green"), W, H, "green", seed=8)
    T.background(p("bg_tomato"), W, H, "tomato", seed=9)
    T.photo_bg(p("bg_feed"), ph("feed"), W, H, ay=0.25)
    T.photo_bg(p("bg_fridge"), ph("fridge"), W, H, ay=0.6)

    s1_stop = T.sticker_text(p("s1_stop"), "СТОП!", fill=T.TOMATO, size=110, angle=-6)
    s1_head = T.headline(p("s1_head"), [[("Слюнки", "k"), ("потекли?", "T")]], 1000, size=80)
    s2_logo = T.logo(p("s2_logo"), size=112, text="Повтори")
    s3_chip = T.sticker_text(p("s3_chip"), "нейросеть · 1 сек", fill=T.MUSTARD, ink=T.INK, size=60, angle=-4)
    s3_ingr = T.photo_card(p("s3_ingr"), ph("ingredients"), 600, 400, angle=3)
    items = ["паста", "томаты черри", "базилик", "пармезан", "сливки"]
    s3_list = [T.list_card(p(f"s3_list{k}"), "Корзина", items, k, w=860, size=48) for k in (0, 2, 5)]
    s4_head = T.headline(p("s4_head"), [[("Что есть дома —", "k")], [("не покупаю", "G")]], 1000, size=84)
    s4_c = [T.strike_chip(p(f"s4_c{i}"), t, size=72, angle=a) for i, (t, a) in
            enumerate([("яйца", -3), ("масло", 2), ("сыр", -2)])]
    s5_sp = T.photo_card(p("s5_sp"), ph("spices"), 560, 560, angle=-3)
    s5_found = T.sticker_text(p("s5_found"), "Нашла!", fill=T.GREEN, size=96, angle=-8)
    s6_ring = T.ring(p("s6_ring"), 560)
    s6_num = T.big_number(p("s6_num"), "15", "мин", "курьер у двери", w=760)
    s6_tap = T.sticker_text(p("s6_tap"), "1 касание", fill=T.MUSTARD, ink=T.INK, size=72, angle=-5)
    s7_dish = T.photo_card(p("s7_dish"), ph("dish"), 760, 640, angle=-2)
    s7_head = T.headline(p("s7_head"), [[("Первая корзина", "w")]], 1000, size=84)
    s7_off = T.sticker_text(p("s7_off"), "−30%", fill=T.MUSTARD, ink=T.INK, size=200, angle=-7)
    s8_cta = T.cta_button(p("s8_cta"), "Скачать «Повтори»", w=760, size=70)
    s8_sl = T.sticker_text(p("s8_sl"), "Увидели? Повторили!", fill=T.TOMATO, size=64, angle=-4)

    return [
        # 1 hook — лента с видео-рецептом, «СТОП!»
        {"bg": p("bg_feed"), "av": None, "keep": [(300, 368, 860, 1650)],
         "sfx": [(0.0, "bass", 0.6), (F("слюнки"), "ding", 0.35)], "els": [
            (s1_stop, 40, 20, 0.0, None, "stamp"),
            (s1_head, 30, 185, F("слюнки")),
        ]},
        # 2 ведущая на весь кадр, логотип над головой
        {"bg": p("bg_doodle"), "av": host(1.0, 540, 200, zoom=0.03, punch=[F("«Повтори»")]),
         "flash": [(F("«Повтори»") + 0.05, "yellow")], "sfx": [(F("Кидаю"), "whoosh", 0.4)], "els": [
            (s2_logo, cx(s2_logo), 10, F("«Повтори»")),
        ]},
        # 3 нейросеть за секунду собирает корзину
        {"bg": p("bg_plain"), "av": None, "sfx": [(F("нейросеть"), "beep", 0.4), (F("корзину!"), "ding", 0.4)],
         "els": [
            (s3_chip, 40, 40, F("нейросеть")),
            (s3_ingr, cx(s3_ingr), 270, F("нейросеть") + 0.2),
            (s3_list[0], cx(s3_list[0]), 820, F("СЕКУНДУ"), F("собирает"), "cut"),
            (s3_list[1], cx(s3_list[1]), 820, F("собирает"), F("корзину!"), "cut"),
            (s3_list[2], cx(s3_list[2]), 820, F("корзину!"), None, "cut"),
        ]},
        # 4 холодильник: что есть дома — не покупаю
        {"bg": p("bg_fridge"), "av": None, "sfx": [(F("уже"), "click", 0.45), (F("есть"), "click", 0.45),
                                                    (F("дома,"), "click", 0.45)], "els": [
            (s4_head, 40, 40, F("Всё,")),
            (s4_c[0], 40, 430, F("уже")),
            (s4_c[1], 440, 430, F("есть")),
            (s4_c[2], 250, 660, F("дома,")),
        ]},
        # 5 ведущая справа, специи + «Нашла!»
        {"bg": p("bg_doodle"), "av": host(0.72, 880, 700, punch=[F("нашла!")]), "els": [
            (s5_sp, 20, 60, F("специи")),
            (s5_found, 120, 560, F("нашла!"), None, "stamp"),
        ]},
        # 6 зелёный фон: лицо в круге, 1 касание, 15 мин
        {"bg": p("bg_green"), "av": {"kind": "circle", "size": 500, "x": (W - 500) // 2, "y": 70},
         "flash": [(F("пятна́дцать") + 0.05, "yellow")],
         "sfx": [(F("касание"), "click", 0.6), (F("пятна́дцать"), "bass", 0.5), (F("курьер"), "beep", 0.35)], "els": [
            (s6_ring, (W - size(s6_ring)[0]) // 2, 40, b[5] + 0.05, None, "frame"),
            (s6_tap, 40, 560, F("касание")),
            (s6_num, cx(s6_num), 810, F("пятна́дцать")),
        ]},
        # 7 оффер: первая корзина −30%
        {"bg": p("bg_tomato"), "av": None, "sfx": [(F("минус"), "ding", 0.5)], "els": [
            (s7_head, 40, 40, F("Первая")),
            (s7_dish, cx(s7_dish), 260, F("Первая") + 0.1),
            (s7_off, cx(s7_off), 900, F("минус"), None, "stamp"),
        ]},
        # 8 финал: ведущая, кнопка, слоган
        {"bg": p("bg_doodle"), "av": host(1.0, 540, 280, zoom=0.04, punch=[F("увидели,")]),
         "sfx": [(F("Скачивайте") + 0.1, "click", 0.55)], "els": [
            (s8_cta, cx(s8_cta), 20, F("Скачивайте")),
            (s8_sl, cx(s8_sl), 300, F("увидели,"), None, "stamp"),
        ]},
    ]


L.scenes = scenes

if __name__ == "__main__":
    L.main()
