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
B.AUDIO = f"{ROOT}/scratch/l4r-v-full-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l4r-v-host.webm")
B.OUT = f"{HERE}/l4r-9x16.mp4"
B.SHOW = {"пятнадцать": "15"}
B.BOUNDS = [0.0, 3.52, 7.03, 10.45, 13.77, 18.48, 22.45, 25.06]
V.TEXTS = f"{ROOT}/docs/scenarios/landing-4-recipe.md"
V.WHISPER = f"{ROOT}/scratch/l4r-v-full-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 9:16 (до 30 с), v1", "## Набросок раскладки"
L.ALIAS = {}

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
    T.photo_bg(p("bg_feed"), ph("feed"), W, H, ay=0.25)
    T.photo_bg(p("bg_fridge"), ph("fridge"), W, H, ay=0.6)

    s1_head = T.headline(p("s1_head"), [[("Рецепт в ленте —", "k")], [("хочу СЕЙЧАС!", "T")]], 1000, size=80)
    s2_logo = T.logo(p("s2_logo"), size=112, text="Повтори")
    s3_chip = T.sticker_text(p("s3_chip"), "нейросеть", fill=T.MUSTARD, ink=T.INK, size=64, angle=-4)
    s3_ingr = T.photo_card(p("s3_ingr"), ph("ingredients"), 600, 400, angle=3)
    items = ["паста", "томаты черри", "базилик", "пармезан", "сливки"]
    s3_list = [T.list_card(p(f"s3_list{k}"), "Корзина", items, k, w=860, size=48) for k in (0, 2, 5)]
    s4_head = T.headline(p("s4_head"), [[("Уже дома —", "k")], [("не покупаем", "G")]], 1000, size=92)
    s4_c = [T.strike_chip(p(f"s4_c{i}"), t, size=72, angle=a) for i, (t, a) in
            enumerate([("яйца", -3), ("масло", 2), ("сыр", -2)])]
    s5_sp = T.photo_card(p("s5_sp"), ph("spices"), 480, 480, angle=-3)
    s5_found = T.sticker_text(p("s5_found"), "Найдено!", fill=T.GREEN, size=80, angle=-8)
    s5_por = T.big_number(p("s5_por"), "6", "порций", "на всех гостей", color=T.TOMATO, w=300, k=0.55)
    s6_ring = T.ring(p("s6_ring"), 560)
    s6_num = T.big_number(p("s6_num"), "15", "мин", "курьер у двери", w=760)
    s6_tap = T.sticker_text(p("s6_tap"), "1 касание", fill=T.MUSTARD, ink=T.INK, size=72, angle=-5)
    s7_dish = T.photo_card(p("s7_dish"), ph("dish"), 860, 860, angle=-2)
    s7_stamp = T.sticker_text(p("s7_stamp"), "Увидела — повторила!", fill=T.TOMATO, size=72, angle=-5)
    s8_cta = T.cta_button(p("s8_cta"), "Скачать «Повтори»", w=760, size=70)

    return [
        # 1 hook — лента с видео-рецептом
        {"bg": p("bg_feed"), "av": None, "keep": [(300, 368, 860, 1650)], "sfx": [(0.1, "click", 0.4), (F("захотелось"), "ding", 0.35)], "els": [
            (s1_head, 40, 0, F("захотелось") - 0.2),
        ]},
        # 2 ведущая на весь кадр, логотип над головой
        {"bg": p("bg_doodle"), "av": host(1.0, 540, 200, zoom=0.03, punch=[F("«Повтори»…")]),
         "flash": [(F("«Повтори»…") + 0.05, "yellow")], "sfx": [(F("Скидываю"), "whoosh", 0.4)], "els": [
            (s2_logo, cx(s2_logo), 10, F("«Повтори»…")),
        ]},
        # 3 нейросеть собирает корзину
        {"bg": p("bg_plain"), "av": None, "sfx": [(F("разбирает"), "beep", 0.4), (F("корзину."), "ding", 0.4)],
         "els": [
            (s3_chip, 40, 40, b[2] + 0.1),
            (s3_ingr, cx(s3_ingr), 270, F("разбирает")),
            (s3_list[0], cx(s3_list[0]), 820, F("собирает"), F("собирает") + 0.35, "cut"),
            (s3_list[1], cx(s3_list[1]), 820, F("собирает") + 0.35, F("корзину."), "cut"),
            (s3_list[2], cx(s3_list[2]), 820, F("корзину."), None, "cut"),
        ]},
        # 4 холодильник: что уже есть дома
        {"bg": p("bg_fridge"), "av": None, "sfx": [(F("УЖЕ"), "click", 0.45), (F("есть"), "click", 0.45),
                                                    (F("холодильнике."), "click", 0.45)], "els": [
            (s4_head, 40, 40, F("Учитывает,")),
            (s4_c[0], 40, 430, F("УЖЕ")),
            (s4_c[1], 440, 430, F("есть")),
            (s4_c[2], 250, 660, F("холодильнике.")),
        ]},
        # 5 ведущая справа, специи и порции
        {"bg": p("bg_doodle"), "av": host(0.72, 880, 700), "els": [
            (s5_sp, 20, 40, F("специи")),
            (s5_found, 80, 400, F("найдёт.") + 0.05, None, "stamp"),
            (s5_por, 10, 690, F("Порции")),
        ]},
        # 6 зелёный фон: лицо в круге, 15 мин
        {"bg": p("bg_green"), "av": {"kind": "circle", "size": 500, "x": (W - 500) // 2, "y": 70},
         "flash": [(F("ПЯТНАДЦАТЬ") + 0.05, "yellow")],
         "sfx": [(F("касание"), "click", 0.6), (F("ПЯТНАДЦАТЬ"), "bass", 0.5), (F("курьер"), "beep", 0.35)], "els": [
            (s6_ring, (W - size(s6_ring)[0]) // 2, 40, b[5] + 0.05, None, "frame"),
            (s6_tap, 40, 560, F("касание")),
            (s6_num, cx(s6_num), 810, F("ПЯТНАДЦАТЬ")),
        ]},
        # 7 готовое блюдо
        {"bg": p("bg_plain"), "av": None, "els": [
            (s7_dish, cx(s7_dish), 90, b[6] + 0.05),
            (s7_stamp, cx(s7_stamp), 1060, F("повторила.") - 0.1, None, "stamp"),
        ]},
        # 8 финал: ведущая, кнопка
        {"bg": p("bg_doodle"), "av": host(1.0, 540, 260, zoom=0.04, punch=[F("вдохновляет!")]),
         "sfx": [(F("Скачайте") + 0.1, "click", 0.55)], "els": [
            (s8_cta, cx(s8_cta), 40, F("Скачайте")),
        ]},
    ]


L.scenes = scenes

if __name__ == "__main__":
    L.main()
