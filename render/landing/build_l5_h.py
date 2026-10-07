"""Лендинг, ролик 5 «Приветствие директора: русский и английский», горизонталь 16:9.

Тот же сюжет, что у вертикали (build_l5.py), расширенный и своими словами
(docs/scenarios/landing-5-ceo.md, «Текст 16:9 (до 60 с), v1»): Елена Орлова
представляется, рассказывает о новых командах в Лондоне и Дубае и обращается к
каждому на его языке — дальше по-английски. Та же ведущая (photo avatar
53ba82e5b13921585f38cac0f06b8441, клип 9:16 webm с прозрачным фоном ставится в
горизонтальный кадр), голос Ana, стиль «Премиальный корпоративный», тихая
музыка из библиотеки HeyGen. Свои картинки — офисы в Лондоне, Дубае и Москве
(docs/scenarios/landing-5/images-h.json). Тайминги слов — whisper по-русски
до смены языка и по-английски после (scratch/l5h-final-whisper-1.json).

Раскладка меняется каждую сцену:
  1 RU     — Елена справа, слева чип RU, логотип, плашка «имя — должность»
  2 команды — без Елены: «Сильные команды», фото офисов Лондона и Дубая по словам
  3 страны  — карта мира, по словам загораются Москва, Лондон, Дубай
  4 смена   — бордовый экран: «каждому — на родном языке», переключатель RU → EN
  5 EN     — Елена по центру, чип EN, плашка по-английски, логотип латиницей
  6 города  — три фото офисов в ряд по словам London / Dubai / Moscow
  7 двери   — Елена слева, справа «Our doors are always open» и три пункта
  8 итог   — Елена справа, слева «Одно видео — на любом языке», языки и кнопка

Запуск:  python3 -m render.landing.build_l5_h
Выход:   render/landing/l5-16x9.mp4
"""
import os

from render.landing import build_l1_v3 as V
from render.landing import build_l3 as B
from render.landing import build_l4 as L
from render.landing import build_l5 as P   # общие настройки ролика 5 (стиль, музыка, силуэт)
from render.landing import theme_premium as T

ROOT, HERE = B.ROOT, B.HERE
IMG = f"{ROOT}/scratch/img"
W, H = 1920, 1080

B.W, B.H = W, H
L.W, L.H = W, H
B.TMP = f"{HERE}/_frames_l5h"
B.AUDIO = f"{ROOT}/scratch/l5h-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l5h-ceo.webm")
B.OUT = f"{HERE}/l5-16x9.mp4"
B.CAP_W, B.CAP_X, B.CAP_BOTTOM = 1100, 410, 1010
V.WHISPER = f"{ROOT}/scratch/l5h-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 16:9 (до 60 с), v1", "## Раскладка 16:9"
L.ALIAS = {}
# границы сцен — середины пауз (silencedetect); 2→3 — между словами «Дубая» и «Теперь»
B.BOUNDS = [0.0, 5.83, 12.40, 18.19, 22.34, 26.12, 31.54, 37.78]

p = B.p
size = L.size
TAIL = P.TAIL


def cx(path, center=W / 2):
    return int(center - size(path)[0] / 2)


def host(cxx, s=0.62, y=0, zoom=0.0, punch=()):
    """Елена с центром силуэта в cxx; срез клипа (1769 px) всегда ниже кадра."""
    return {"kind": "scale", "s": s, "x": cxx - 540 * s, "y": y, "zoom": zoom, "punch": list(punch)}


def scenes(F):
    b = B.BOUNDS
    ph = lambda n: f"{IMG}/l5h_ph_{n}.png"
    T.background(p("bg_ivory"), W, H, "ivory")
    T.background(p("bg_frame"), W, H, "frame")
    T.background(p("bg_bordo"), W, H, "bordo")

    h1_ru = T.lang_chip(p("h1_ru"), "RU")
    h1_logo = T.word_logo(p("h1_logo"), "Меридиан", size=84)
    h1_name = T.name_plate(p("h1_name"), "Елена Орлова", "генеральный директор", w=640)
    h2_kick = T.kicker(p("h2_kick"), "этот год", size=30)
    h2_head = T.headline(p("h2_head"), [[("Сильные", "k")], [("команды", "b")]], 480, size=100)
    h2_lon = T.photo_card(p("h2_lon"), ph("london"), 500, 310, ax=0.6, caption="Лондон")
    h2_dxb = T.photo_card(p("h2_dxb"), ph("dubai"), 500, 310, ax=0.45, caption="Дубай")
    h3_kick = T.kicker(p("h3_kick"), "три страны · одна команда", size=30)
    h3_map = P.map_el(p("h3_map"), w=1200)
    h3_msk = T.city_chip(p("h3_msk"), "Москва")
    h3_lon = T.city_chip(p("h3_lon"), "Лондон")
    h3_dxb = T.city_chip(p("h3_dxb"), "Дубай")
    h4_head = T.headline(p("h4_head"), [[("каждому —", "w"), ("на родном языке", "g")]], 1500, size=84,
                         align="center")
    h4_ru = T.lang_switch(p("h4_ru"), "RU", w=820)
    h4_en = T.lang_switch(p("h4_en"), "EN", w=820)
    h5_en = T.lang_chip(p("h5_en"), "EN")
    h5_logo = T.word_logo(p("h5_logo"), "Meridian", size=84)
    h5_name = T.name_plate(p("h5_name"), "Elena Orlova", "CEO, Meridian", w=480)
    h6_c = [T.photo_card(p(f"h6_{n}"), ph(n), 460, 280, ax=a, caption=c) for n, a, c in
            (("london", 0.6, "London"), ("dubai", 0.45, "Dubai"), ("moscow", 0.85, "Moscow"))]
    h6_kick = T.kicker(p("h6_kick"), "your ideas shape our future", color=T.BORDO, size=32)
    h7_head = T.headline(p("h7_head"), [[("Our doors are", "k")], [("always open", "b")]], 760, size=84)
    h7_b = [T.bullet(p(f"h7_b{i}"), n, t, w=760, size=48) for i, (n, t) in
            enumerate((("01", "Share your thoughts"), ("02", "Ask questions"), ("03", "Let's grow together")))]
    h8_head = T.headline(p("h8_head"), [[("Одно видео —", "k")], [("на любом языке", "b")]], 760,
                         size=84)
    h8_langs = T.lang_row(p("h8_langs"), ("RU", "EN", "DE", "ES", "FR"), active=2, size=40)
    h8_cta = T.cta_button(p("h8_cta"), "Заказать ролик", w=520, size=44)

    # карта (1200 px): точки офисов в координатах элемента
    mx, my = cx(h3_map), 140
    city = {"msk": (722, 224), "lon": (522, 236), "dxb": (743, 348)}

    def at(key, dx, dy):
        x0, y0 = city[key]
        return mx + x0 + dx, my + y0 + dy

    return [
        # 1 RU — Елена справа, слева чип, логотип, имя
        {"bg": p("bg_frame"), "av": host(1400, zoom=0.03, punch=[F("«Меридиан».")]),
         "sfx": [(0.05, "chime", 0.3)], "els": [
            (h1_ru, 120, 110, 0.1),
            (h1_logo, 120, 250, F("«Меридиан».")),
            (h1_name, 90, 450, F("Елена")),
        ]},
        # 2 команды — фото офисов Лондона и Дубая
        {"bg": p("bg_ivory"), "av": None,
         "sfx": [(F("Лондона"), "pop", 0.4), (F("Дубая."), "pop", 0.4)], "els": [
            (h2_kick, 120, 140, b[1] + 0.05),
            (h2_head, 120, 200, F("особенным:") - 0.3),
            (h2_lon, 600, 90, F("Лондона")),
            (h2_dxb, 1240, 260, F("Дубая.")),
        ]},
        # 3 страны — карта, по словам загораются города
        {"bg": p("bg_ivory"), "av": None,
         "sfx": [(F("трёх"), "ding", 0.3)], "els": [
            (h3_map, mx, my, b[2] + 0.1, None, "frame"),
            (h3_kick, cx(h3_kick), 95, b[2] + 0.05),
            (h3_msk, *at("msk", 30, -100), F("трёх")),
            (h3_lon, *at("lon", -300, 10), F("трёх") + 0.25),
            (h3_dxb, *at("dxb", -10, 45), F("трёх") + 0.5),
        ]},
        # 4 смена языка — бордовый экран, переключатель
        {"bg": p("bg_bordo"), "av": None,
         "flash": [(F("языке.") + 0.05, "gold")],
         "sfx": [(F("языке."), "click", 0.7), (F("языке.") + 0.05, "chime", 0.5)], "els": [
            (h4_head, cx(h4_head), 150, F("Поэтому")),
            (h4_ru, cx(h4_ru), 330, b[3] + 0.1, F("языке."), "cut"),
            (h4_en, cx(h4_en), 330, F("языке."), None, "cut"),
        ]},
        # 5 EN — Елена по центру, чип, имя латиницей, логотип
        {"bg": p("bg_frame"), "av": host(960, zoom=0.03, punch=[F("Welcome")]),
         "sfx": [(F("Welcome"), "chime", 0.3)], "els": [
            (h5_en, 120, 110, b[4] + 0.1),
            (h5_name, 80, 450, F("afternoon,")),
            (h5_logo, W - 120 - size(h5_logo)[0], 110, F("Meridian.")),
        ]},
        # 6 города — три офиса в ряд
        {"bg": p("bg_ivory"), "av": None,
         "sfx": [(F("London,"), "pop", 0.35), (F("Dubai"), "pop", 0.35), (F("Moscow,"), "pop", 0.35)], "els": [
            (h6_c[0], 70, 130, F("London,")),
            (h6_c[1], 672, 130, F("Dubai")),
            (h6_c[2], 1274, 130, F("Moscow,")),
            (h6_kick, cx(h6_kick), 680, F("ideas")),
        ]},
        # 7 двери открыты — Елена слева, справа три пункта
        {"bg": p("bg_frame"), "av": host(480, zoom=0.03, punch=[F("open")]),
         "els": [
            (h7_head, 980, 110, F("Our")),
            (h7_b[0], 980, 380, F("Share")),
            (h7_b[1], 980, 500, F("ask")),
            (h7_b[2], 980, 620, F("let's")),
        ], "sfx": [(F("Share"), "pop", 0.35), (F("ask"), "pop", 0.35), (F("let's"), "pop", 0.35)]},
        # 8 итог — формула, языки, кнопка
        {"bg": p("bg_ivory"), "av": host(1380, zoom=0.04, punch=[F("wherever")]),
         "sfx": [(F("We"), "ding", 0.3)], "els": [
            (h8_head, 120, 110, F("We")),
            (h8_langs, 100, 470, F("team")),
            (h8_cta, 130, 620, F("wherever")),
        ]},
    ]


L.scenes = scenes

if __name__ == "__main__":
    P.pad_audio()
    L.main()
