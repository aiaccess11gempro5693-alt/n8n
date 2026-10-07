"""Лендинг, ролик 5 «Приветствие директора: русский и английский», вертикаль 9:16.

Локализация: директор вымышленной компании «Меридиан» Елена Орлова говорит
сначала по-русски, потом по-английски — тем же голосом и лицом. Стиль A
«Премиальный корпоративный» (render/landing/theme_premium.py, борд
scratch/img/l5_board_a.png), фото scratch/img/l5_ceo_9x16.png → HeyGen photo
avatar 53ba82e5b13921585f38cac0f06b8441, клип webm с прозрачным фоном; голос
Ana (eleven_v3, jCQ8uWWBzw3HoBe23v4N). Сценарий — docs/scenarios/landing-5-ceo.md.
Движок — build_l3 через build_l4 (подклад — спокойный SFX.pad).

Раскладка меняется каждую сцену:
  1 hook  — типографика без директора: «Этот ролик никто не снимал», по словам
            зачёркиваются «камера», «студия», «переводчик»
  2 RU    — директор в кадре с полями, чип RU, плашка «имя — должность», логотип
  3 смена — бордовый экран, большой переключатель RU → EN щёлкает на слове
  4 EN    — директор ниже, чип EN, сверху «Hello!» → карта офисов, «wherever you are»
  5 итог  — «Одно обращение — на любом языке», ряд языков, кнопка

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
B.AUDIO = f"{ROOT}/scratch/l5v-final.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l5v-ceo.webm")
B.OUT = f"{HERE}/l5-9x16.mp4"
B.CAP_W, B.CAP_X, B.CAP_BOTTOM = 920, 80, 1820
B.SHOW = {"ceo": "CEO"}
# границы сцен — середины пауз (silencedetect)
B.BOUNDS = [0.0, 5.80, 13.90, 16.26, 23.59]
V.TEXTS = f"{ROOT}/docs/scenarios/landing-5-ceo.md"
V.WHISPER = f"{ROOT}/scratch/l5v-final-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 9:16 (до 30 с), v1", "## Набросок раскладки"
# whisper делит «по-английски» на два слова; «CEO» не превращать в строчные (КАПС-правило субтитров)
L.ALIAS = {"по-английски.": "английски"}
L.BED, L.BED_GAIN, L.STAMP_FLASH = SFX.pad, 0.26, "gold"

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

    s1_kick = T.kicker(p("s1_kick"), "Меридиан · обращение", size=30)
    s1_head = T.headline(p("s1_head"), [[("Этот ролик", "k")], [("никто", "b")], [("не снимал", "k")]], 900,
                         size=130)
    s1_w = [T.strike_word(p(f"s1_w{i}"), t, size=110, angle=a) for i, (t, a) in
            enumerate([("камера", 2), ("студия", -2), ("переводчик", 1)])]
    s2_ru = T.lang_chip(p("s2_ru"), "RU")
    s2_logo = T.word_logo(p("s2_logo"), "Меридиан", size=78)
    s2_name = T.name_plate(p("s2_name"), "Елена Орлова", "генеральный директор", w=640)
    s3_kick = T.kicker(p("s3_kick"), "тот же голос", color=T.GOLD, size=34)
    s3_ru = T.lang_switch(p("s3_ru"), "RU", w=860)
    s3_en = T.lang_switch(p("s3_en"), "EN", w=860)
    s3_sub = T.headline(p("s3_sub"), [[("другой язык", "w")]], 700, size=88, align="center")
    s4_en = T.lang_chip(p("s4_en"), "EN")
    s4_hello = T.headline(p("s4_hello"), [[("Hello!", "b")]], 600, size=150, align="center")
    s4_map = map_el(p("s4_map"))
    s4_where = T.kicker(p("s4_where"), "wherever you are", color=T.BORDO, size=32)
    s5_head = T.headline(p("s5_head"), [[("Одно обращение —", "k")], [("на любом языке", "b")]], 940,
                         size=92, align="center")
    s5_langs = T.lang_row(p("s5_langs"), ("RU", "EN", "DE", "ES", "FR"), active=2, size=42)
    s5_cta = T.cta_button(p("s5_cta"), "Заказать ролик", w=560, size=46)

    return [
        # 1 hook — типографика, зачёркиваются камера / студия / переводчик
        {"bg": p("bg_ivory"), "av": None,
         "sfx": [(0.05, "bass", 0.45), (F("снимал."), "click", 0.5), (F("студии,"), "click", 0.5),
                 (F("переводчика."), "click", 0.5)], "els": [
            (s1_kick, 100, 150, 0.05),
            (s1_head, 100, 240, 0.1),
            (s1_w[0], 100, 860, F("снимал.")),
            (s1_w[1], 400, 1080, F("студии,")),
            (s1_w[2], 140, 1300, F("переводчика.")),
        ]},
        # 2 RU — директор в кадре с полями, чип, имя, логотип
        {"bg": p("bg_frame"), "av": host(1.0, 540, 230, zoom=0.03, punch=[F("Рада")]),
         "flash": [(F("Рада") + 0.05, "gold")], "sfx": [(F("Здравствуйте!"), "chime", 0.35)], "els": [
            (s2_ru, 90, 90, b[1] + 0.1),
            (s2_logo, W - 90 - size(s2_logo)[0], 110, F("«Меридиана».")),
            (s2_name, 50, 1300, F("Елена")),
        ]},
        # 3 смена языка — бордовый экран, переключатель щёлкает RU → EN
        {"bg": p("bg_bordo"), "av": None,
         "flash": [(F("по-английски.") + 0.05, "gold")],
         "sfx": [(F("по-английски."), "click", 0.7), (F("по-английски.") + 0.05, "chime", 0.5)], "els": [
            (s3_kick, cx(s3_kick), 520, b[2] + 0.05),
            (s3_ru, cx(s3_ru), 660, b[2] + 0.1, F("по-английски."), "cut"),
            (s3_en, cx(s3_en), 660, F("по-английски."), None, "cut"),
            (s3_sub, cx(s3_sub), 1060, F("по-английски.") + 0.1),
        ]},
        # 4 EN — директор ниже, сверху «Hello!» → карта офисов
        {"bg": p("bg_frame"), "av": host(0.8, 540, 740, zoom=0.03, punch=[F("Welcome")]),
         "sfx": [(F("Welcome"), "ding", 0.35)], "els": [
            (s4_en, 90, 90, b[3] + 0.1, F("Welcome")),
            (s4_hello, cx(s4_hello), 330, F("Hello!"), F("Welcome")),
            (s4_map, cx(s4_map), 110, F("Welcome")),
            (s4_where, cx(s4_where), 700, F("wherever")),
        ]},
        # 5 итог — формула, ряд языков, кнопка
        {"bg": p("bg_ivory"), "av": host(0.86, 540, 700, zoom=0.04, punch=[F("любом")]),
         "sfx": [(F("Одно"), "bass", 0.4), (F("любом"), "chime", 0.4)], "els": [
            (s5_head, cx(s5_head), 110, b[4] + 0.05),
            (s5_langs, cx(s5_langs), 400, F("любом")),
            (s5_cta, cx(s5_cta), 560, F("языке.")),
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
