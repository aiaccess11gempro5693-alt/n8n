"""Лендинг, ролик 5 «Приветствие директора: русский и английский», вертикаль 9:16.

Локализация через живой сюжет (сценарий v2): директор вымышленной компании
«Меридиан» Елена Орлова обращается к команде, к которой в этом году
присоединились коллеги из Лондона и Дубая, и, чтобы каждый услышал её на своём
языке, продолжает по-английски — тем же голосом и лицом. Стиль A «Премиальный
корпоративный» (render/landing/theme_premium.py, борд scratch/img/l5_board_a.png),
фото scratch/img/l5_ceo_9x16.png → HeyGen photo avatar
53ba82e5b13921585f38cac0f06b8441, клип webm с прозрачным фоном; голос Ana
(eleven_v3, jCQ8uWWBzw3HoBe23v4N). Сценарий — docs/scenarios/landing-5-ceo.md.
Подклад — готовый трек из библиотеки HeyGen (scratch/music/l5-music-2-full.mp3),
тихо (синтезированные pad/piano/corporate отклонены: «жутко», «для сна», «не то»).
Движок — build_l3 через build_l4.

Раскладка меняется каждую сцену:
  1 RU    — директор в кадре с полями, чип RU, плашка «имя — должность», логотип
  2 карта — без директора: «Новые команды», карта мира, по словам загораются
            Москва → Лондон → Дубай
  3 смена — бордовый экран: «каждый — на своём языке», переключатель RU → EN
            щёлкает на слове «языке»
  4 EN    — директор, чип EN, плашка «Elena Orlova — CEO», логотип латиницей
  5 города — без директора: фото офисов London / Dubai / Moscow по словам,
            «one goal: our clients' lives easier»
  6 итог  — директор ниже, «Одно видео — на любом языке», ряд языков, кнопка
(v3: английская часть расширена на ≈10 с по просьбе пользователя)

Запуск:  python3 -m render.landing.build_l5
Выход:   render/landing/l5-9x16.mp4
"""
import os

from PIL import Image

from render.landing import build_l1_v3 as V
from render.landing import build_l3 as B
from render.landing import build_l4 as L
from render.landing import sfx as SFX
from render.landing import theme_premium as T

ROOT, HERE = B.ROOT, B.HERE
IMG = f"{ROOT}/scratch/img"
W, H = 1080, 1920

B.T = T
L.T = T
B.TMP = f"{HERE}/_frames_l5"
B.AUDIO = f"{ROOT}/scratch/l5v3-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l5v3-ceo.webm")
B.OUT = f"{HERE}/l5-9x16.mp4"
B.CAP_W, B.CAP_X, B.CAP_BOTTOM = 920, 80, 1820
B.SHOW = {"ceo": "CEO"}
# границы сцен — середины пауз (silencedetect)
B.BOUNDS = [0.0, 4.37, 8.78, 12.70, 15.66, 23.22]
V.TEXTS = f"{ROOT}/docs/scenarios/landing-5-ceo.md"
V.WHISPER = f"{ROOT}/scratch/l5v3-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 9:16 (до 30 с), v3", "## Текст 16:9 (до 60 с), v1"
L.ALIAS = {}
# готовый трек, тише прежнего подклада (жалоба «не так громко»)
L.BED, L.BED_GAIN, L.STAMP_FLASH = SFX.music_bed(f"{ROOT}/scratch/music/l5-music-2-full.mp3"), 0.13, "gold"

# Силуэт директора в клипе HeyGen 1080×1920 (голова и плечи) — измерен по альфе.
B.AVATAR_BOX = (140, 279, 990, 960)
B.FACE = (545, 540, 240)
B.CLIP_BOTTOM = 1769
B.FACE_Y = B.FACE[1] / 1920

p = B.p
size = L.size
TAIL = 0.8


def cx(path, center=W / 2):
    return int(center - size(path)[0] / 2)


def host(s=1.0, cxx=540, y=0, zoom=0.0, punch=()):
    return {"kind": "scale", "s": s, "x": cxx - 540 * s, "y": y, "zoom": zoom, "punch": list(punch)}


def map_el(path, w=860):
    im = Image.open(f"{IMG}/l5_map.png").convert("RGBA")
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    px = im.load()   # светлый фон картинки → прозрачный, остаются точки и дуги
    for y in range(im.height):
        for x in range(im.width):
            r, g, b_, _ = px[x, y]
            light = min(r, g, b_)
            if light > 225:
                px[x, y] = (r, g, b_, 0)
            elif light > 200:
                px[x, y] = (r, g, b_, int(255 * (225 - light) / 25))
    im.save(path)
    return path


def scenes(F):
    b = B.BOUNDS
    T.background(p("bg_ivory"), W, H, "ivory")
    T.background(p("bg_frame"), W, H, "frame")
    T.background(p("bg_bordo"), W, H, "bordo")

    s1_ru = T.lang_chip(p("s1_ru"), "RU")
    s1_logo = T.word_logo(p("s1_logo"), "Меридиан", size=78)
    s1_name = T.name_plate(p("s1_name"), "Елена Орлова", "генеральный директор", w=640)
    s2_kick = T.kicker(p("s2_kick"), "в этом году", size=32)
    s2_head = T.headline(p("s2_head"), [[("Новые", "k")], [("команды", "b")]], 900, size=120)
    s2_map = map_el(p("s2_map"), w=1000)
    s2_msk = T.city_chip(p("s2_msk"), "Москва")
    s2_lon = T.city_chip(p("s2_lon"), "Лондон")
    s2_dxb = T.city_chip(p("s2_dxb"), "Дубай")
    s3_head = T.headline(p("s3_head"), [[("каждый —", "w")], [("на своём языке", "g")]], 940, size=96,
                         align="center")
    s3_ru = T.lang_switch(p("s3_ru"), "RU", w=860)
    s3_en = T.lang_switch(p("s3_en"), "EN", w=860)
    s4_en = T.lang_chip(p("s4_en"), "EN")
    s4_logo = T.word_logo(p("s4_logo"), "Meridian", size=78)
    s4_name = T.name_plate(p("s4_name"), "Elena Orlova", "CEO, Meridian", w=640)
    s5_c = [T.photo_card(p(f"s5_{n}"), f"{IMG}/l5h_ph_{n}.png", 760, 210, ax=a, caption=c) for n, a, c in
            (("london", 0.6, "London"), ("dubai", 0.45, "Dubai"), ("moscow", 0.85, "Moscow"))]
    s5_goal = T.kicker(p("s5_goal"), "one goal", color=T.BORDO, size=34)
    s6_head = T.headline(p("s6_head"), [[("Одно видео —", "k")], [("на любом языке", "b")]], 940,
                         size=96, align="center")
    s6_langs = T.lang_row(p("s6_langs"), ("RU", "EN", "DE", "ES", "FR"), active=2, size=42)
    s6_cta = T.cta_button(p("s6_cta"), "Заказать ролик", w=560, size=46)

    # карта (1000 px): точки офисов в координатах элемента — Москва, Лондон, Дубай
    mx, my = cx(s2_map), 660
    city = {"msk": (601, 186), "lon": (435, 196), "dxb": (619, 290)}

    def at(chip, key, dx, dy):
        x0, y0 = city[key]
        return mx + x0 + dx, my + y0 + dy

    return [
        # 1 RU — директор в кадре с полями, чип, имя, логотип
        {"bg": p("bg_frame"), "av": host(1.0, 540, 230, zoom=0.03, punch=[F("«Меридиана».")]),
         "sfx": [(0.05, "chime", 0.3)], "els": [
            (s1_ru, 90, 90, 0.1),
            (s1_name, 50, 1300, F("Елена")),
            (s1_logo, W - 90 - size(s1_logo)[0], 110, F("«Меридиана».")),
        ]},
        # 2 карта — новые команды: Москва → Лондон → Дубай
        {"bg": p("bg_ivory"), "av": None,
         "sfx": [(F("Лондона"), "pop", 0.4), (F("Дубая."), "pop", 0.4), (F("Дубая."), "ding", 0.3)], "els": [
            (s2_map, mx, my, b[1] + 0.25, None, "frame"),
            (s2_kick, 100, 150, b[1] + 0.05),
            (s2_head, 100, 220, F("команды")),
            (s2_msk, *at(s2_msk, "msk", 30, -110), b[1] + 0.5),
            (s2_lon, *at(s2_lon, "lon", -330, 20), F("Лондона")),
            (s2_dxb, *at(s2_dxb, "dxb", -20, 50), F("Дубая.")),
        ]},
        # 3 смена языка — бордовый экран, переключатель щёлкает на «языке»
        {"bg": p("bg_bordo"), "av": None,
         "flash": [(F("языке.") + 0.05, "gold")],
         "sfx": [(F("языке."), "click", 0.7), (F("языке.") + 0.05, "chime", 0.5)], "els": [
            (s3_head, cx(s3_head), 380, F("каждый")),
            (s3_ru, cx(s3_ru), 760, b[2] + 0.1, F("языке."), "cut"),
            (s3_en, cx(s3_en), 760, F("языке."), None, "cut"),
        ]},
        # 4 EN — директор, чип EN, имя латиницей, логотип
        {"bg": p("bg_frame"), "av": host(1.0, 540, 230, zoom=0.03, punch=[F("Welcome")]),
         "sfx": [(F("Welcome"), "chime", 0.3)], "els": [
            (s4_en, 90, 90, b[3] + 0.1),
            (s4_name, 50, 1300, F("Dear") + 0.3),
            (s4_logo, W - 90 - size(s4_logo)[0], 110, F("Meridian.")),
        ]},
        # 5 города — три офиса стопкой по словам, «one goal»
        {"bg": p("bg_ivory"), "av": None,
         "sfx": [(F("London,"), "pop", 0.35), (F("Dubai,"), "pop", 0.35), (F("Moscow"), "pop", 0.35),
                 (F("goal:"), "ding", 0.3)], "els": [
            (s5_c[0], cx(s5_c[0]), 70, F("London,")),
            (s5_c[1], cx(s5_c[1]), 470, F("Dubai,")),
            (s5_c[2], cx(s5_c[2]), 870, F("Moscow")),
            (s5_goal, cx(s5_goal), 1300, F("goal:")),
        ]},
        # 6 итог — формула, ряд языков, кнопка
        {"bg": p("bg_ivory"), "av": host(0.86, 540, 700, zoom=0.04, punch=[F("wherever")]),
         "sfx": [(F("Thank"), "ding", 0.3)], "els": [
            (s6_head, cx(s6_head), 110, b[5] + 0.05),
            (s6_langs, cx(s6_langs), 400, F("team")),
            (s6_cta, cx(s6_cta), 560, F("wherever")),
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
