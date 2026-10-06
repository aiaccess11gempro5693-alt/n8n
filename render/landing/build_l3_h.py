"""Лендинг, ролик 3 «Как не попасться телефонным мошенникам» — горизонталь 16:9.

Тот же стиль «Reels-эксперт» A, тот же эксперт (photo avatar
d4f9cb52180178230ff161a87e04482c, клип HeyGen 9:16 с прозрачным фоном
ставится в горизонтальный кадр) и голос Синев, что у вертикали (build_l3.py),
но СВОЙ расширенный текст (4 признака) и свои картинки — кинокадры и иконки
от gpt-image-2 (docs/scenarios/landing-3/images-h.json). Движок — общий
(render_scene / check_layout из build_l3).

Раскладка меняется каждую сцену:
  1 кадр-фото звонящего телефона, справа карточка звонка → реплика «по имени»
  2 эксперт справа, слева «4 признака мошенника»
  3 фото человека в панике (справа), слева «01 давление» + реплика + таймер
  4 эксперт слева, справа «02 код из СМС» и перечёркнутый код
  5 эксперт по центру между двумя колонками: «резервный счёт» / деньги ворам
  6 типографика без эксперта: «04» приложение «для защиты» + штамп
  7 фото руки с картой (слева), справа «что делать» — 3 шага
  8 фото семьи, справа «расскажите родителям»
  9 эксперт по центру, по бокам итог «не грубость» / «ваша защита»

Запуск:  python3 -m render.landing.build_l3_h
Выход:   render/landing/l3-16x9.mp4
"""
import os

from render.landing import build_l1_v3 as V
from render.landing import build_l3 as B
from render.landing import theme_reels as T

ROOT, HERE = B.ROOT, B.HERE
IMG = f"{ROOT}/scratch/img"
W, H = 1920, 1080

B.W, B.H = W, H
B.TMP = f"{HERE}/_frames_l3h"
B.AUDIO = f"{ROOT}/scratch/l3-h-full-v2.mp3"
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l3-h-expert.webm")
B.OUT = f"{HERE}/l3-16x9.mp4"
B.CAP_W, B.CAP_X, B.CAP_BOTTOM = 1100, 410, 1050
B.SHOW = {**B.SHOW, "четыре": "4"}
V.WHISPER = f"{ROOT}/scratch/l3-h-full-v2-whisper-1.json"
V.TEXT_HEAD, V.TEXT_END = "## Текст 16:9 (до 60 с)", "## Раскладка 16:9"
# границы сцен — середины пауз между предложениями (silencedetect)
B.BOUNDS = [0.0, 6.75, 12.83, 19.11, 25.99, 34.91, 40.01, 47.88, 49.95]

p = B.p


def expert(cx, s=0.66, y=0, zoom=0.0, punch=()):
    """Эксперт с центром силуэта в cx; срез клипа (1769 px) всегда ниже кадра.
    punch — моменты резкого наезда к лицу на ключевых словах."""
    return {"kind": "scale", "s": s, "x": cx - 540 * s, "y": y, "zoom": zoom, "punch": list(punch)}


def scenes(F):
    b = B.BOUNDS
    ph = lambda n: f"{IMG}/l3h_ph_{n}.png"
    ic = lambda n: f"{IMG}/l3h_ic_{n}.png"
    T.background(p("bg_plain"), W, H, "plain")
    T.background(p("bg_dots"), W, H, "dots")
    T.background(p("bg_type"), W, H, "type")
    T.photo_bg(p("bg_ring"), ph("ring"), W, H, rect=(0, 0, 1250, H), dark=0.15, fade_side="right", ax=0.0)
    T.photo_bg(p("bg_rush"), ph("rush"), W, H, rect=(700, 0, 1220, H), dark=0.2, fade_side="left", ax=0.0)
    T.photo_bg(p("bg_card"), ph("card"), W, H, rect=(0, 0, 1150, H), dark=0.15, fade_side="right", ax=0.25)
    T.photo_bg(p("bg_parents"), ph("parents"), W, H, rect=(0, 0, 1300, H), dark=0.1, fade_side="right", ax=0.2)
    return [
        {"bg": p("bg_ring"), "av": None, "sfx": [(0.15, "ring", 0.45), (F("Вежливый"), "glitch", 0.25)], "els": [
            (T.call_card(p("h1_call"), 800), 1040, 140, 0.2, F("Вежливый") - 0.1),
            (T.quote_card(p("h1_quote"), ["Иван Сергеевич,", "добрый день!"], 700, 56), 1140, 130,
             F("Вежливый")),
        ]},
        {"bg": p("bg_dots"), "av": expert(1440, punch=[F("четыре")]), "els": [
            (T.tag(p("h2_tag"), "Эксперт по безопасности"), 70, 120, F("специалист")),
            (T.headline(p("h2_head"), [[("4", "y"), ("признака", "w")], [("мошенника", "b")]], 900, size=96),
             70, 330, F("четыре")),
        ]},
        {"bg": p("bg_rush"), "av": None, "keep": [(830, 60, 1600, H)], "sfx": [(F("давление."), "tick", 0.4)],
         "els": [
            (T.tag(p("h3_tag"), "01 · Давление"), 70, 50, F("Первый:")),
            (T.icon_text(p("h3_fear"), ic("timer"), ["Спешка", "и страх"], 700, 210, 66), 60, 200, F("давление.")),
            (T.stamp(p("h3_stamp"), "СРОЧНО!", size=110, angle=-8, seed=23), 90, 470, F("«Срочно!") + 0.05,
             None, "stamp"),
        ]},
        {"bg": p("bg_plain"), "av": expert(430, punch=[F("НИКОГДА")]), "els": [
            (T.tag(p("h4_tag"), "02 · Код из СМС"), 900, 50, F("Второй:")),
            (T.icon_text(p("h4_ask"), ic("chat"), ["Просят", "продиктовать код"], 920, 190, 56), 900, 175,
             F("просят")),
            (T.code_card(p("h4_code"), 700, ("БАНК НЕ СПРАШИВАЕТ",)), 900, 430, F("Банк")),
        ]},
        {"bg": p("bg_dots"), "av": expert(960, punch=[F("Деньги", b[4])]), "sfx": [(F("Таких") - 1.15, "riser", 0.45)],
         "els": [
            (T.tag(p("h5_tag"), "03 · Перевод"), 40, 80, F("Третий:")),
            (T.headline(p("h5_head"), [[("«Резервный", "w")], [("счёт»", "b")]], 620, size=56), 30, 210,
             F("резервный")),
            (T.stamp(p("h5_stamp"), "НЕ СУЩЕСТВУЕТ", size=72, angle=-7, seed=13), 40, 440, F("Таких") + 0.05,
             None, "stamp"),
            (T.icon_text(p("h5_money"), ic("transfer"), ["Деньги —", "к ворам"], 600, 200, 58), 1290, 220,
             F("сбережения")),
        ]},
        {"bg": p("bg_type"), "av": None, "sfx": [(b[5] + 0.05, "glitch", 0.35)], "els": [
            (T.tag(p("h6_tag"), "04 · Приложение"), 760, 90, b[5] + 0.05),
            (T.icon_tile(p("h6_icon"), ic("app"), 380), 170, 250, b[5] + 0.3),
            (T.headline(p("h6_head"), [[("«Для", "w")], [("защиты»", "b")], [("телефона", "w")]], 1000, size=90),
             720, 230, F("приложение")),
            (T.stamp(p("h6_stamp"), "ЛОВУШКА", size=90, angle=-8, seed=17), 1300, 600, F("защиты»") + 0.05,
             None, "stamp"),
        ]},
        {"bg": p("bg_card"), "av": None, "keep": [(120, 300, 1080, H)], "els": [
            (T.headline(p("h7_head"), [[("Что", "w"), ("делать?", "b")]], 800, size=76), 1100, 40, F("Что")),
            (T.step_row(p("h7_s1"), 1, "Ничего не диктуйте", 780), 1100, 260, F("Ничего")),
            (T.step_row(p("h7_s2"), 2, "Положите трубку", 780), 1100, 420, F("положить")),
            (T.step_row(p("h7_s3"), 3, "Перезвоните сами", 780), 1100, 580, F("Позвоните")),
        ]},
        {"bg": p("bg_parents"), "av": None, "keep": [(420, 350, 1240, H)], "els": [
            (T.icon_text(p("h8_fam"), ic("family"), ["Расскажите", "родителям"], 620, 200, 54), 1258, 240,
             b[7] + 0.05),
        ]},
        {"bg": p("bg_dots"), "av": expert(960, zoom=0.03, punch=[F("защита.")]), "flash": [(F("защита.") , "yellow")],
         "els": [
            (T.headline(p("h9_l"), [[("Положить", "w")], [("трубку —", "w")], [("не грубость", "r")]], 640,
                        size=58), 20, 200, b[8] + 0.05),
            (T.headline(p("h9_r"), [[("Это ваша", "w")], [("защита", "b")]], 600, size=64), 1290, 260,
             F("грубость")),
        ]},
    ]


B.scenes = scenes

if __name__ == "__main__":
    B.main()
