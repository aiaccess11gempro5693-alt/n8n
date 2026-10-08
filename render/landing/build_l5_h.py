"""Лендинг, ролик 5 «Приветствие директора», горизонталь 16:9, v2 — «Один день директора».

Свой сюжет, не пересказ вертикали (жалоба 08.10.2026: «на минуту, не тем же
сюжетом, а сильно расширеннее и интереснее»): один день Елены Орловой — утром она
говорит с Москвой по-русски, в полдень с новой командой в Лондоне по-английски,
вечером с новой командой в Мадриде по-испански, в конце снова по-русски. Три
языка тем же голосом и лицом. Сценарий — docs/scenarios/landing-5-ceo.md,
«Текст 16:9 (до 60 с), v2». Та же ведущая (photo avatar
53ba82e5b13921585f38cac0f06b8441, клип 9:16 webm с прозрачным фоном в
горизонтальном кадре), голос Ana, стиль «Премиальный корпоративный», тихая музыка
из библиотеки HeyGen. Тайминги — whisper отдельно по каждому языку
(scratch/l5h2-seg0..3 → scratch/l5h2-final-whisper-1.json).

Раскладка меняется каждую сцену, сквозной приём — шкала дня 09:00 → 12:00 → 18:00:
   1 09:00 Москва — Елена справа, слева шкала дня, чип RU, плашка имени
   2 год назад    — фото маленькой переговорной, «вся команда — в одной комнате»
   3 сегодня      — карта: Москва → Лондон, Мадрид
   4 языки        — бордовый экран: «с каждой командой — на её языке», чипы RU · EN · ES
   5 12:00 London — Елена справа, шкала дня, чип EN
   6 UK           — фото лондонского офиса, «A team that speaks their language»
   7 Monday       — Елена слева, справа карточка «Your first project — Monday»
   8 18:00 Madrid — Елена справа, шкала дня, чип ES, фото офиса в Мадриде
   9 energía      — фото Мадрида на полкадра и испанская цитата
  10 итог         — Елена справа, «Три города · три языка · одна команда», языки, кнопка

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
B.AUDIO = f"{ROOT}/scratch/l5h2-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l5h2-ceo.webm")
B.OUT = f"{HERE}/l5-16x9.mp4"
B.CAP_W, B.CAP_X, B.CAP_BOTTOM = 1100, 410, 1010
B.SHOW = {"uk": "UK", "ceo": "CEO"}
V.WHISPER = f"{ROOT}/scratch/l5h2-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 16:9 (до 60 с), v2", "## Раскладка 16:9 v2"
L.ALIAS = {}
# границы сцен — середины пауз (silencedetect)
B.BOUNDS = [0.0, 6.03, 10.64, 14.81, 20.41, 26.99, 32.81, 38.68, 43.23, 48.78]

p = B.p
size = L.size
STOPS = [("09:00", "Москва"), ("12:00", "London"), ("18:00", "Madrid")]


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
    tl = [T.day_timeline(p(f"tl{i}"), STOPS, i, w=1000) for i in range(3)]

    c1_ru = T.lang_chip(p("c1_ru"), "RU")
    c1_name = T.name_plate(p("c1_name"), "Елена Орлова", "генеральный директор", w=640)
    c2_kick = T.kicker(p("c2_kick"), "год назад", size=30)
    c2_head = T.headline(p("c2_head"), [[("Вся команда —", "k")], [("в одной", "b")], [("переговорной", "b")]],
                         640, size=84)
    c2_ph = T.photo_card(p("c2_ph"), ph("small"), 820, 520, ax=0.7)
    c3_kick = T.kicker(p("c3_kick"), "а сегодня — новые офисы", size=30)
    c3_map = P.map_el(p("c3_map"), w=1200)
    c3_msk = T.city_chip(p("c3_msk"), "Москва")
    c3_lon = T.city_chip(p("c3_lon"), "Лондон")
    c3_mad = T.city_chip(p("c3_mad"), "Мадрид")
    c4_head = T.headline(p("c4_head"), [[("с каждой командой —", "w")], [("на её родном языке", "g")]], 1400,
                         size=88, align="center")
    c4_l = [T.lang_chip(p(f"c4_{c}"), c, size=96) for c in ("RU", "EN", "ES")]
    c5_en = T.lang_chip(p("c5_en"), "EN")
    c5_kick = T.kicker(p("c5_kick"), "newest team", color=T.BORDO, size=30)
    c5_head = T.headline(p("c5_head"), [[("and the", "k")], [("fastest-growing", "b")]], 640, size=80)
    c6_ph = T.photo_card(p("c6_ph"), ph("london"), 860, 500, ax=0.6, caption="London")
    c6_head = T.headline(p("c6_head"), [[("A team", "k")], [("that speaks", "k")], [("their language", "b")]],
                         640, size=78)
    c7_note = T.note_card(p("c7_note"), "your first project", ["Starts on Monday"], w=760, size=66)
    c7_kick = T.kicker(p("c7_kick"), "can't wait to see what you build", color=T.BORDO, size=28)
    c8_es = T.lang_chip(p("c8_es"), "ES")
    c8_ph = T.photo_card(p("c8_ph"), ph("madrid"), 560, 330, ax=0.55, caption="Madrid")
    c9_ph = T.photo_card(p("c9_ph"), ph("madrid"), 820, 560, ax=0.5)
    c9_head = T.headline(p("c9_head"), [[("Vuestra energía", "k")], [("y vuestras ideas", "b")]], 640, size=78)
    c9_kick = T.kicker(p("c9_kick"), "lo que necesitamos", color=T.GOLD, size=30)
    c10_head = T.headline(p("c10_head"), [[("Три города,", "k")], [("три языка —", "k")], [("одна команда", "b")]],
                          760, size=84)
    c10_langs = T.lang_row(p("c10_langs"), ("RU", "EN", "ES", "DE", "FR"), active=3, size=40)
    c10_cta = T.cta_button(p("c10_cta"), "Одно видео — на любом языке", w=640, size=40)

    mx, my = cx(c3_map), 160
    city = {"msk": (722, 224), "lon": (522, 236), "mad": (500, 300)}

    def at(key, dx, dy):
        x0, y0 = city[key]
        return mx + x0 + dx, my + y0 + dy

    return [
        # 1 09:00 Москва — Елена справа, слева шкала дня, чип, имя
        {"bg": p("bg_frame"), "av": host(1420, zoom=0.03, punch=[F("Я")]),
         "sfx": [(0.05, "chime", 0.3)], "els": [
            (tl[0], 90, 90, 0.1),
            (c1_ru, 120, 290, F("Москва.")),
            (c1_name, 90, 470, F("Елена")),
        ]},
        # 2 год назад — маленькая переговорная
        {"bg": p("bg_ivory"), "av": None, "els": [
            (c2_ph, 90, 90, b[1] + 0.1),
            (c2_kick, 1060, 160, b[1] + 0.05),
            (c2_head, 1060, 220, F("команда")),
        ]},
        # 3 сегодня — карта: Москва → Лондон, Мадрид
        {"bg": p("bg_ivory"), "av": None,
         "sfx": [(F("Лондоне"), "pop", 0.4), (F("Мадриде."), "pop", 0.4), (F("открываем"), "ding", 0.3)], "els": [
            (c3_map, mx, my, b[2] + 0.1, None, "frame"),
            (c3_kick, cx(c3_kick), 100, F("сегодня")),
            (c3_msk, *at("msk", 30, -100), b[2] + 0.4),
            (c3_lon, *at("lon", -310, -90), F("Лондоне")),
            (c3_mad, *at("mad", -340, 60), F("Мадриде.")),
        ]},
        # 4 языки — бордо, чипы RU · EN · ES
        {"bg": p("bg_bordo"), "av": None,
         "flash": [(F("языке.") + 0.05, "gold")],
         "sfx": [(F("каждой"), "pop", 0.4), (F("новой"), "pop", 0.4), (F("языке."), "chime", 0.5)], "els": [
            (c4_head, cx(c4_head), 170, F("каждой") - 0.3),
            (c4_l[0], 400, 520, F("каждой")),
            (c4_l[1], 800, 520, F("новой")),
            (c4_l[2], 1200, 520, F("языке.")),
        ]},
        # 5 12:00 London — Елена справа, шкала дня, чип EN
        {"bg": p("bg_frame"), "av": host(1420, zoom=0.03, punch=[F("London!")]),
         "sfx": [(b[4] + 0.1, "chime", 0.35)], "els": [
            (tl[1], 90, 90, b[4] + 0.1),
            (c5_en, 120, 300, F("afternoon,")),
            (c5_kick, 120, 520, F("newest")),
            (c5_head, 120, 570, F("already")),
        ]},
        # 6 UK — лондонский офис, «a team that speaks their language»
        {"bg": p("bg_ivory"), "av": None, "els": [
            (c6_ph, 90, 70, b[5] + 0.1),
            (c6_head, 1080, 200, F("people")),
        ]},
        # 7 Monday — Елена слева, справа карточка проекта
        {"bg": p("bg_frame"), "av": host(500, zoom=0.03, punch=[F("Monday")]),
         "sfx": [(F("Monday"), "ding", 0.35)], "els": [
            (c7_note, 960, 160, F("Your")),
            (c7_kick, 980, 560, F("can't")),
        ]},
        # 8 18:00 Madrid — Елена справа, шкала дня, чип ES, фото Мадрида
        {"bg": p("bg_frame"), "av": host(1420, zoom=0.03, punch=[F("Bienvenidos")]),
         "sfx": [(b[7] + 0.1, "chime", 0.35)], "els": [
            (tl[2], 90, 90, b[7] + 0.1),
            (c8_es, 120, 300, F("tardes,")),
            (c8_ph, 370, 300, F("Madrid!")),
        ]},
        # 9 energía — Мадрид и испанская цитата
        {"bg": p("bg_ivory"), "av": None, "els": [
            (c9_ph, 980, 70, b[8] + 0.1),
            (c9_head, 110, 200, F("Vuestra")),
            (c9_kick, 110, 480, F("necesitamos.")),
        ]},
        # 10 итог — Елена справа, формула, языки, кнопка
        {"bg": p("bg_ivory"), "av": host(1420, zoom=0.04, punch=[F("одна")]),
         "sfx": [(F("Три"), "ding", 0.3)], "els": [
            (c10_head, 110, 90, F("Три")),
            (c10_langs, 90, 470, F("языка")),
            (c10_cta, 110, 620, F("Спасибо,")),
        ]},
    ]


L.scenes = scenes

if __name__ == "__main__":
    P.pad_audio()
    L.main()
