"""Лендинг, ролик 4 «Повтори» — горизонталь 16:9 (до 60 с).

Тот же стиль «Свежий рынок», та же ведущая (photo avatar
98082e6c9f96dd72faba9a17b491260f, клип HeyGen 9:16 webm с прозрачным фоном ставится
в горизонтальный кадр) и голос Viktoriia, что у вертикали (build_l4r.py), но СВОЙ
расширенный текст и свои картинки (docs/scenarios/landing-4/images-recipe-h.json).
Движок — общий (build_l3 через build_l4). Уроки вертикали: элементы держатся,
пока их можно прочитать (корзина — одна карточка с состояниями «на месте»),
хвост 0.8 с в конце (звук не обрывается).

Раскладка меняется каждую сцену:
  1 фото телефона с сохранёнными рецептами слева, справа «Сохранили — и не приготовили?»
  2 ведущая справа, слева «Вот и я!»
  3 фото пустой кухни слева, справа зачёркнутые «нет сливок / специй / сил»
  4 ведущая по центру, логотип «Повтори» над головой
  5 без ведущей: продукты слева, корзина справа (заполняется → порции → «есть дома»)
  6 фото курьера у двери справа, слева «1 касание» и «15 мин»
  7 фото стола с пастой, пловом, тирамису справа, слева бирки по словам
  8 томатный фон, ведущая слева, справа «Первая корзина −30%»
  9 ведущая по центру, кнопка «Скачать» и штамп

Запуск:  python3 -m render.landing.build_l4r_h
Выход:   render/landing/l4r-16x9.mp4
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
B.TMP = f"{HERE}/_frames_l4rh"
B.AUDIO = f"{ROOT}/scratch/l4rh-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l4rh-host.webm")
B.OUT = f"{HERE}/l4r-16x9.mp4"
B.CAP_W, B.CAP_X, B.CAP_BOTTOM = 1100, 410, 1050
B.SHOW = {"тридцать": "30"}
V.TEXTS = f"{ROOT}/docs/scenarios/landing-4-recipe.md"
V.WHISPER = f"{ROOT}/scratch/l4rh-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 16:9 (до 60 с), v1", "## Раскладка 16:9"
L.ALIAS = {"тридцать": "30"}
B.BOUNDS = [float(v) for v in os.environ.get("BOUNDS", "0").split(",")]

# Силуэт ведущей в клипе HeyGen 1080×1920 (голова и плечи) — измерен по альфе.
B.AVATAR_BOX = (180, 380, 900, 1000)
B.FACE = (530, 560, 230)
B.CLIP_BOTTOM = 1769
B.FACE_Y = B.FACE[1] / 1920

p = B.p
size, cx = L.size, L.cx
TAIL = 0.8


def host(cxx, s=0.66, y=0, zoom=0.0, punch=()):
    """Ведущая с центром силуэта в cxx; срез клипа (1769 px) всегда ниже кадра."""
    return {"kind": "scale", "s": s, "x": cxx - 540 * s, "y": y, "zoom": zoom, "punch": list(punch)}


def scenes(F):
    b = B.BOUNDS
    ph = lambda n: f"{IMG}/l4rh_ph_{n}.png"
    pv = lambda n: f"{IMG}/l4r_p_{n}.png"
    T.background(p("bg_doodle"), W, H, "doodle", seed=11)
    T.background(p("bg_plain"), W, H, "plain")
    T.background(p("bg_green"), W, H, "green_flat", seed=12)
    T.background(p("bg_tomato"), W, H, "tomato_flat", seed=13)
    T.photo_half(p("bg_saved"), ph("saved"), W, H, (0, 0, 1150, H), "right", ax=0.1)
    T.photo_half(p("bg_empty"), ph("empty"), W, H, (0, 0, 1150, H), "right", ax=0.0)
    T.photo_half(p("bg_door"), ph("door"), W, H, (760, 0, 1160, H), "left", ax=0.9)
    T.photo_half(p("bg_feast"), ph("feast"), W, H, (700, 0, 1220, H), "left", ax=0.9)

    h1_head = T.headline(p("h1_head"), [[("Сохранили —", "k")], [("и не приготовили?", "T")]], 760, size=78)
    h1_cnt = T.sticker_text(p("h1_cnt"), "сохранено: 127", fill=T.MUSTARD, ink=T.INK, size=60, angle=-4)
    h2_me = T.sticker_text(p("h2_me"), "Вот и я так жила!", fill=T.TOMATO, size=72, angle=-5)
    h3_c = [T.strike_chip(p(f"h3_c{i}"), t, size=70, angle=a) for i, (t, a) in
            enumerate([("сливки", -3), ("специи", 2), ("силы", -2)])]
    h3_head = T.headline(p("h3_head"), [[("Вечно чего-то", "k")], [("не хватает", "T")]], 700, size=76)
    h4_logo = T.logo(p("h4_logo"), size=96, text="Повтори")
    h4_found = T.sticker_text(p("h4_found"), "нашла!", fill=T.GREEN, size=72, angle=6)
    h5_chip = T.sticker_text(p("h5_chip"), "ссылка на видео → нейросеть", fill=T.MUSTARD, ink=T.INK, size=52,
                             angle=-3)
    h5_ingr = T.photo_card(p("h5_ingr"), pv("ingredients"), 640, 420, angle=-3)
    items = ["паста", "томаты черри", "базилик", "сливки", "яйца", "сыр"]
    h5_full = T.list_card(p("h5_full"), "Корзина", items, 6, w=760, size=44)
    h5_home = T.list_card(p("h5_home"), "Корзина", items, 6, w=760, size=44, struck=("яйца", "сыр"))
    h5_por = T.sticker_text(p("h5_por"), "на всех гостей", fill=T.TOMATO, size=56, angle=4)
    h5_none = T.sticker_text(p("h5_none"), "Ничего лишнего!", fill=T.GREEN, size=66, angle=-5)
    h6_tap = T.sticker_text(p("h6_tap"), "1 касание", fill=T.MUSTARD, ink=T.INK, size=64, angle=-5)
    h6_num = T.big_number(p("h6_num"), "15", "мин", "курьер у двери", w=600, k=0.8)
    h7_head = T.headline(p("h7_head"), [[("Любое видео —", "k")], [("в ужин", "G")]], 640, size=84)
    h7_t = [T.tick_tag(p(f"h7_t{i}"), t, fill=c, size=56) for i, (t, c) in
            enumerate([("паста", T.TOMATO), ("плов", T.GREEN), ("тирамису", T.MUSTARD)])]
    h8_head = T.headline(p("h8_head"), [[("Первая корзина", "w")]], 900, size=84)
    h8_off = T.sticker_text(p("h8_off"), "−30%", fill=T.MUSTARD, ink=T.INK, size=210, angle=-7)
    h9_cta = T.cta_button(p("h9_cta"), "Скачать «Повтори»", w=400, size=46)
    h9_sl = T.sticker_text(p("h9_sl"), "Готовьте то, что вдохновляет!", fill=T.TOMATO, size=44, angle=5)

    return [
        # 1 сохранённые рецепты
        {"bg": p("bg_saved"), "av": None, "keep": [(120, 60, 760, H)],
         "sfx": [(0.05, "bass", 0.5), (F("сохранили"), "click", 0.4)], "els": [
            (h1_head, 1120, 120, 0.1),
            (h1_cnt, 1180, 470, F("сохранили")),
        ]},
        # 2 ведущая справа: «вот и я»
        {"bg": p("bg_doodle"), "av": host(1380, punch=[F("жила!")]), "els": [
            (h2_me, 80, 300, F("жила!") - 0.3, None, "stamp"),
        ]},
        # 3 пустая кухня: чего не хватает
        {"bg": p("bg_empty"), "av": None, "keep": [(60, 200, 800, 900)],
         "sfx": [(F("сливок,"), "click", 0.45), (F("специй,"), "click", 0.45), (F("сил"), "click", 0.45)], "els": [
            (h3_head, 1140, 90, b[2] + 0.1),
            (h3_c[0], 1160, 420, F("сливок,")),
            (h3_c[1], 1500, 420, F("специй,")),
            (h3_c[2], 1300, 600, F("сил")),
        ]},
        # 4 ведущая по центру, логотип
        {"bg": p("bg_doodle"), "av": host(960, zoom=0.03, punch=[F("«Повтори».")]),
         "flash": [(F("«Повтори».") + 0.05, "yellow")], "sfx": [(F("«Повтори»."), "ding", 0.45)], "els": [
            (h4_logo, 80, 300, F("нашла")),
            (h4_found, 1400, 330, F("«Повтори»."), None, "stamp"),
        ]},
        # 5 нейросеть собирает корзину (одна карточка, состояния на месте)
        {"bg": p("bg_plain"), "av": None,
         "sfx": [(F("нейросеть"), "beep", 0.4), (F("разбирает"), "ding", 0.35), (F("порции"), "click", 0.45),
                 (F("дома."), "click", 0.5), (F("Ничего"), "bass", 0.45)], "els": [
            (h5_chip, 40, 40, F("ссылку")),
            (h5_ingr, 60, 250, F("нейросеть")),
            (h5_full, 1040, 60, F("разбирает"), F("дома."), "cut"),
            (h5_home, 1040, 60, F("дома."), None, "cut"),
            (h5_por, 140, 800, F("порции")),
            (h5_none, 560, 790, F("Ничего"), None, "stamp"),
        ]},
        # 6 курьер у двери: 1 касание, 15 мин
        {"bg": p("bg_door"), "av": None, "keep": [(1100, 150, W, H)],
         "sfx": [(F("касание"), "click", 0.6), (F("четверть"), "bass", 0.5), (F("курьер"), "beep", 0.35)], "els": [
            (h6_tap, 80, 70, F("касание")),
            (h6_num, 60, 290, F("четверть")),
        ]},
        # 7 любое видео — в ужин
        {"bg": p("bg_feast"), "av": None, "keep": [(880, 60, W, H)], "els": [
            (h7_head, 40, 80, F("Паста,")),
            (h7_t[0], 60, 420, F("Паста,")),
            (h7_t[1], 360, 420, F("плов,")),
            (h7_t[2], 140, 580, F("тирамису")),
        ], "sfx": [(F("плов,"), "click", 0.4), (F("тирамису"), "click", 0.4), (F("ужин!"), "ding", 0.4)]},
        # 8 оффер: ведущая слева, −30% справа
        {"bg": p("bg_tomato"), "av": host(440, punch=[F("минус")]), "sfx": [(F("минус"), "ding", 0.5)], "els": [
            (h8_head, 900, 120, F("первая")),
            (h8_off, 1000, 360, F("минус"), None, "stamp"),
        ]},
        # 9 финал: ведущая по центру, кнопка, штамп
        {"bg": p("bg_doodle"), "av": host(1010, zoom=0.04, punch=[F("вдохновляет!")]),
         "sfx": [(F("Скачивайте") + 0.1, "click", 0.55)], "els": [
            (h9_cta, 8, 330, F("Скачивайте")),
            (h9_sl, W - 10 - size(h9_sl)[0], 300, F("готовьте"), None, "stamp"),
        ]},
    ]


L.scenes = scenes


def pad_audio():
    """Озвучка + TAIL секунд тишины — финал не обрывается на последнем звуке."""
    out = f"{B.TMP}/voice_tail.wav"
    os.makedirs(B.TMP, exist_ok=True)
    B.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af", f"apad=pad_dur={TAIL}", "-ar", "48000", out])
    B.AUDIO = out


if __name__ == "__main__":
    pad_audio()
    L.main()
