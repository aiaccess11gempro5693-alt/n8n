"""Лендинг, ролик 4 «Быстро» — горизонталь 16:9.

Тот же стиль «Свежий рынок», тот же сборщик (photo avatar
665d8a82a44ecc41db71e40dbf6b9dfc, клип HeyGen 9:16 webm с прозрачным фоном ставится
в горизонтальный кадр) и голос Max, что у вертикали (build_l4.py), но СВОЙ
расширенный текст и свои картинки gpt-image-2 (docs/scenarios/landing-4/images-h.json).
Движок — общий (render/landing/build_l3.py через build_l4.py).

Раскладка меняется каждую сцену:
   1 фото вечерней кухни (холодильник с лимоном), справа «20:00» и «Знакомо?»
   2 сборщик справа, слева логотип «Быстро» и «сборщик заказов»
   3 фото склада справа, слева пуш «Новый заказ» и «бегу по складу»
   4 без ведущего: три фото продуктов в ряд, под каждым бирка с галочкой
   5 сборщик по центру, по бокам «КАЖДЫЙ продукт» / «как для себя»
   6 сборщик слева, справа «60 мин» и ценник «0 ₽»
   7 фото телефона с картой слева, справа «курьер уже у дома»
   8 «было»: серое фото очереди, справа зачёркнутые неудобства
   9 «стало»: типографика — 3 шага «выбрали → оплатили → получили»
  10 фото семьи за ужином справа, слева чипы аудиторий и «для вас»
  11 сборщик по центру, кнопка «Скачать» и штамп «Соберу сам!»

Запуск:  python3 -m render.landing.build_l4_h
Выход:   render/landing/l4-16x9.mp4
"""
import os

from render.landing import build_l1_v3 as V
from render.landing import build_l3 as B
from render.landing import build_l4 as L
from render.landing import theme_product as T

ROOT, HERE = B.ROOT, B.HERE
IMG = f"{ROOT}/scratch/img"
W, H = 1920, 1080

B.W, B.H = W, H
L.W, L.H = W, H
B.TMP = f"{HERE}/_frames_l4h"
B.AUDIO = f"{ROOT}/scratch/l4-h-full-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l4-h-host.webm")
B.OUT = f"{HERE}/l4-16x9.mp4"
B.CAP_W, B.CAP_X, B.CAP_BOTTOM = 1100, 410, 1050
B.SHOW = {**B.SHOW, "восемь": "8"}
V.WHISPER = f"{ROOT}/scratch/l4-h-full-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 16:9 (до 60 с), v1", "## Раскладка 16:9"
L.ALIAS = {"Знакомо?": "знакома"}
# границы сцен — середины пауз между предложениями (silencedetect)
B.BOUNDS = [0.0, 4.87, 7.88, 10.63, 15.40, 18.18, 23.27, 26.90, 31.17, 34.96, 40.92]

p = B.p
size, cx = L.size, L.cx


def host(cxx, s=0.6, y=0, zoom=0.0, punch=()):
    """Сборщик с центром силуэта в cxx; срез клипа (1769 px) всегда ниже кадра."""
    return {"kind": "scale", "s": s, "x": cxx - 540 * s, "y": y, "zoom": zoom, "punch": list(punch)}


def scenes(F):
    b = B.BOUNDS
    ph = lambda n: f"{IMG}/l4h_ph_{n}.png"
    st = lambda n: f"{IMG}/l4h_st_{n}.png"
    T.background(p("bg_doodle"), W, H, "doodle", seed=4)
    T.background(p("bg_plain"), W, H, "plain")
    T.background(p("bg_green"), W, H, "green", seed=5)
    T.photo_half(p("bg_kitchen"), ph("kitchen"), W, H, (0, 0, 1180, H), "right", ax=0.0)
    T.photo_half(p("bg_store"), ph("store"), W, H, (780, 0, 1140, H), "left", ax=0.7)
    T.photo_half(p("bg_phone"), ph("phone"), W, H, (0, 0, 1150, H), "right", ax=0.1)
    T.photo_half(p("bg_queue"), ph("queue"), W, H, (0, 0, 1150, H), "right", ax=0.3, grey=0.65)
    T.photo_half(p("bg_dinner"), ph("dinner"), W, H, (760, 0, 1160, H), "left", ax=0.85)

    h1_time = T.timer(p("h1_time"), "20:00", size=120, fill=T.INK)
    h1_q = T.headline(p("h1_q"), [[("Знакомо?", "T")]], 640, size=96)
    h2_logo = T.logo(p("h2_logo"), size=120)
    h2_role = T.sticker_text(p("h2_role"), "сборщик заказов", fill=T.MUSTARD, ink=T.INK, size=64, angle=3)
    h3_notif = T.notif_card(p("h3_notif"), "Новый заказ!", "собираю прямо сейчас", w=700)
    h3_run = T.headline(p("h3_run"), [[("Бегу", "k")], [("по складу", "G")]], 700, size=88)
    h4_t = T.photo_card(p("h4_t"), st("tomato"), 470, 470, radius=48, angle=-3)
    h4_g = T.photo_card(p("h4_g"), st("greens"), 470, 470, radius=48, angle=2)
    h4_b = T.photo_card(p("h4_b"), st("bread"), 470, 470, radius=48, angle=-2)
    h4_tt = T.tick_tag(p("h4_tt"), "плотные", fill=T.TOMATO, size=54)
    h4_tg = T.tick_tag(p("h4_tg"), "хрустящая", fill=T.GREEN, size=54)
    h4_tb = T.tick_tag(p("h4_tb"), "сегодняшний", fill=T.MUSTARD, size=54)
    h5_l = T.headline(p("h5_l"), [[("Каждый", "G")], [("продукт", "k")]], 560, size=86)
    h5_r = T.headline(p("h5_r"), [[("как", "k")], [("для себя", "T")]], 520, size=86, align="right")
    h6_num = T.big_number(p("h6_num"), "60", "мин", "до вашей двери", w=620)
    h6_tag = T.price_tag(p("h6_tag"), w=560, angle=6)
    h7_chip = T.map_chip(p("h7_chip"), "Курьер уже у дома")
    h7_head = T.headline(p("h7_head"), [[("Видно", "k")], [("на карте", "G")]], 700, size=96)
    h8_was = T.was_card(p("h8_was"), ["очередь на кассе", "тяжёлые пакеты", "пробки"], w=700)
    h9_steps = T.steps_card(p("h9_steps"), ["выбрали", "оплатили", "получили"], w=1300)
    h10_c1 = T.chip(p("h10_c1"), "работаете допоздна", fill=T.GREEN, ink=T.WHITE, size=60, angle=-3, dot=T.MUSTARD)
    h10_c2 = T.chip(p("h10_c2"), "растите детей", fill=T.TOMATO, ink=T.WHITE, size=60, angle=3, dot=T.MUSTARD)
    h10_c3 = T.chip(p("h10_c3"), "бережёте вечер", fill=T.MUSTARD, ink=T.INK, size=60, angle=-2, dot=T.GREEN)
    h10_head = T.headline(p("h10_head"), [[("«Быстро» —", "k")], [("для вас", "G")]], 700, size=90)
    h11_cta = T.cta_button(p("h11_cta"), "Скачать «Быстро»", w=700)
    h11_sam = T.sticker_text(p("h11_sam"), "Соберу сам!", fill=T.TOMATO, size=90, angle=6)

    return [
        # 1 кухня вечером
        {"bg": p("bg_kitchen"), "av": None, "keep": [(0, 300, 560, H)], "sfx": [(0.05, "tick", 0.3)], "els": [
            (h1_time, 1220, 140, 0.1),
            (h1_q, 1240, 430, F("Знакомо?")),
        ]},
        # 2 сборщик справа, слева логотип и роль
        {"bg": p("bg_doodle"), "av": host(1400, punch=[F("«Быстро»")]), "sfx": [(F("«Быстро»"), "ding", 0.4)], "els": [
            (h2_logo, 110, 180, F("«Быстро»")),
            (h2_role, 160, 480, F("сборщик")),
        ]},
        # 3 склад справа, слева пуш и «бегу»
        {"bg": p("bg_store"), "av": None, "sfx": [(F("нажимаете"), "beep", 0.45)], "els": [
            (h3_notif, 60, 130, F("нажимаете")),
            (h3_run, 60, 420, F("бегу")),
        ]},
        # 4 три продукта в ряд
        {"bg": p("bg_plain"), "av": None, "els": [
            (h4_t, 120, 70, F("Помидоры")),
            (h4_g, 720, 70, F("зелень")),
            (h4_b, 1320, 70, F("хлеб")),
            (h4_tt, cx(h4_tt, 380), 600, F("плотные,")),
            (h4_tg, cx(h4_tg, 975), 600, F("хрустящая,")),
            (h4_tb, cx(h4_tb, 1570), 600, F("сегодняшний.")),
        ], "sfx": [(F("плотные,"), "click", 0.4), (F("хрустящая,"), "click", 0.4),
                   (F("сегодняшний."), "click", 0.4)]},
        # 5 сборщик по центру, по бокам «каждый продукт / как для себя»
        {"bg": p("bg_doodle"), "av": host(960, zoom=0.03, punch=[F("КАЖДЫЙ")]),
         "flash": [(F("КАЖДЫЙ") + 0.05, "yellow")], "els": [
            (h5_l, 40, 230, F("КАЖДЫЙ")),
            (h5_r, W - 40 - size(h5_r)[0], 230, F("как")),
        ]},
        # 6 сборщик слева, справа 60 мин и ценник
        {"bg": p("bg_green"), "av": host(420), "sfx": [(F("шестьдесят"), "beep", 0.4),
                                                        (F("тысячи"), "ding", 0.45)], "els": [
            (h6_num, 770, 120, F("шестьдесят")),
            (h6_tag, 1340, 120, F("Доставка")),
        ]},
        # 7 телефон с картой
        {"bg": p("bg_phone"), "av": None, "keep": [(120, 120, 760, H)], "sfx": [(F("свернул"), "click", 0.5)],
         "els": [
            (h7_head, 1180, 150, F("курьера")),
            (h7_chip, 1180, 520, F("свернул")),
        ]},
        # 8 было: серое фото очереди
        {"bg": p("bg_queue"), "av": None, "sfx": [(F("Раньше") + 0.3, "tick", 0.3)], "els": [
            (h8_was, 1170, 120, F("очередь")),
        ]},
        # 9 стало: 3 шага
        {"bg": p("bg_doodle"), "av": None, "flash": [(F("ТРИ") + 0.05, "green")],
         "sfx": [(F("ТРИ"), "bass", 0.55), (F("выбрали,"), "click", 0.45), (F("оплатили,"), "click", 0.45),
                 (F("получили."), "ding", 0.4)], "els": [
            (h9_steps, cx(h9_steps), 150, F("Теперь")),
        ]},
        # 10 семья за ужином справа, слева аудитории
        {"bg": p("bg_dinner"), "av": None, "keep": [(1100, 120, W, H)], "els": [
            (h10_c1, 60, 90, F("Работаете")),
            (h10_c2, 120, 250, F("растите")),
            (h10_c3, 60, 410, F("бережёте")),
            (h10_head, 60, 580, F("«Быстро»", 39.0)),
        ]},
        # 11 финал: сборщик, кнопка, штамп
        {"bg": p("bg_doodle"), "av": host(960, zoom=0.04, punch=[F("соберу")]),
         "sfx": [(F("Скачайте") + 0.1, "click", 0.55)], "els": [
            (h11_cta, 40, 300, F("Скачайте")),
            (h11_sam, W - 40 - size(h11_sam)[0], 280, F("соберу"), None, "stamp"),
        ]},
    ]


L.scenes = scenes

if __name__ == "__main__":
    L.main()
