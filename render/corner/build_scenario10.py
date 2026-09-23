"""Сценарий 10 «Когда человек спешит / деликатные темы» — полный ролик.

Стандарт — docs/video-standard.md: аватар уходит только в правый нижний угол.
Отличие от сценариев 5–9 — свои приёмы подачи: пара «Кажется / На деле»,
готовая фраза, разобранная на части с подписями («ради вашей пользы» /
«вопрос»), «поток вопросов» против ритма «вопрос → пауза → ответ → второй»,
ползунки тона для деликатных тем; и свой ритм — шесть сцен со строгим
чередованием, финальный опрос в углу: весь кадр → угол → весь кадр → угол →
весь кадр → угол.

Сцены (границы — середины пауз в scratch/scenario10-full-v2.mp3):
  1  0.00–13.88   весь кадр, Avatar IV — человек спешит; кажется / на деле
  2  13.88–44.34  угол (съезд), Avatar III — смысл вопроса за секунду; по одному
  3  44.34–60.71  весь кадр (возврат), Avatar IV — деликатные темы
  4  60.71–73.86  угол (съезд), Avatar III — ориентир: понять → помочь или к врачу
  5  73.86–S5_END весь кадр (возврат), Avatar IV — услышать проблему; спасибо
  6  S5_END–конец угол (съезд), Avatar III — опрос

Запуск:  python3 -m render.corner.build_scenario10   (ONLY=2,3 — только эти сцены)
Выход:   render/corner/scenario10-full.mp4
"""
import json
import os

from PIL import Image

from . import brand_style as S
from . import cards as K
from . import montage as M
from .montage import item

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = f"{HERE}/_frames"
IMG = f"{ROOT}/scratch/img"
AUDIO = f"{ROOT}/scratch/scenario10-full-v2.mp3"
WHISPER = f"{ROOT}/scratch/scenario10-full-v2-whisper.json"
SCENARIO = f"{ROOT}/docs/scenarios/scenario-10-rush-delicate.md"
OUT = f"{HERE}/scenario10-full.mp4"

# весь кадр — колонки по бокам от аватара
L, R, W = 50, 1330, 540
# угол — контент слева и сверху; правый нижний угол (x>1360, y>730) занят аватаром
PX, PW = 100, 1200
COL2, COL2_W = PX + 580, 620


def f(name):
    return f"{TMP}/s10_{name}.png"


def img(name):
    return f"{IMG}/{name}.png"


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


# ---------------------------------------------------------------- сцены

def scene1(T, dur):
    end = dur - 0.25
    head = K.headline(f("s1_head"), "Человек спешит", "«Дайте что-нибудь, только быстро»", ["быстро"],
                      size=46, w=W)
    myth = K.myth_fact(f("s1_myth"), False, "Вопросы тут лишние", w=W)
    return [
        item(head, L, 80, T("Частая"), end),
        item(K.image_card(f("s1_pic"), img("s10_hurry"), W), L, 80 + h_of(head) + 24, T("Частая"), end),
        item(myth, R, 80, T("Кажется"), end),
        item(K.myth_fact(f("s1_fact"), True, "Спасают его и вас", w=W), R, 80 + h_of(myth) + 24,
             T("На"), end),
    ]


def scene2(T, dur):
    end = dur - 0.25
    t_b = T("Задавайте")                        # второй блок — «по одному»
    a_end = t_b - 0.3
    head_a = K.headline(f("s2_head_a"), "Секрет", "Смысл вопроса — за секунду", ["секунду"], size=56, w=PW,
                        bg=False)
    head_b = K.headline(f("s2_head_b"), "Задавайте вопросы", "Спокойно и по одному", ["одному"], size=56,
                        w=PW, bg=False)
    y2 = 40 + h_of(head_a) + 10
    phrase = K.annotated_phrase(f("s2_phrase"), "Скажите так", [
        ("«Чтобы дать то, что точно подойдёт,", "ради пользы человека", S.BLUE),
        ("уточню одну вещь»", "сам вопрос", S.GREEN)], w=COL2_W)
    flood = K.flood_card(f("s2_flood"), 5, "Пять подряд — допрос", w=COL2_W)
    return [
        item(K.image_card(f("s2_pic"), img("s10_ask"), 520), PX, y2, M.MOVE_D, end),
        # блок A — объяснить смысл вопроса
        item(head_a, PX, 40, T("Секрет"), a_end),
        item(phrase, COL2, y2, T("Чтобы"), a_end),
        item(K.icon_row(f("s2_willing"), img("s10_ic_willing"), "Охотно отвечают, когда видят пользу",
                        w=COL2_W, h=110, text_size=30), COL2, y2 + h_of(phrase) + 24, T("Люди"), a_end),
        # блок B — по одному
        item(head_b, PX, 40, t_b, end),
        item(flood, COL2, y2, T("Поток"), end),
        item(K.beat_line(f("s2_beats"), [("q", "Вопрос"), ("pause", "Пауза"), ("answer", "Ответ"),
                                         ("q2", "Второй")], w=COL2_W),
             COL2, y2 + h_of(flood) + 24, T("Один", t_b), end),
    ]


def scene3(T, dur):
    end = dur - 0.25
    t0 = max(T("Отдельно"), M.MOVE_D)           # после возврата аватара
    head = K.headline(f("s3_head"), "Отдельно про", "Деликатные темы", ["Деликатные"], size=56, w=W)
    trio = K.icon_trio(f("s3_trio"), [(img("s10_ic_private"), "Интимные"), (img("s10_ic_child"), "Детские"),
                                      (img("s10_ic_chronic"), "Хронические")], w=W)
    sliders = K.tone_sliders(f("s3_tone"), "Как говорить", [("Формулировка", "мягкая", 0.22),
                                                            ("Тон", "ровный", 0.5),
                                                            ("Любопытство", "без лишнего", 0.08)], w=W)
    return [
        item(head, L, 80, t0, end),
        item(trio, L, 80 + h_of(head) + 24, T("Интимные"), end),
        item(sliders, R, 80, T("Здесь"), end),
        item(K.icon_row(f("s3_care"), img("s10_ic_care"), "Забота, а не разбор жизни", w=W, h=110,
                        text_size=32, outline=S.GREEN), R, 80 + h_of(sliders) + 24, T("Человек"), end),
    ]


def scene4(T, dur):
    end = dur - 0.25
    head = K.headline(f("s4_head"), "Ваша цель", "Держите ориентир", ["ориентир"], size=60, w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    order = K.order_card(f("s4_order"), "Понять человека", "Помочь или направить к врачу", w=COL2_W)
    return [
        item(head, PX, 40, T("держите"), end),
        item(K.image_card(f("s4_pic"), img("s10_goal"), 520), PX, y2, T("держите"), end),
        item(order, COL2, y2, T("понять"), end),
        item(K.icon_row(f("s4_honest"), img("s10_ic_honest"), "Оба варианта — честная работа", w=COL2_W, h=110,
                        text_size=32, outline=S.GREEN), COL2, y2 + h_of(order) + 24, T("Оба"), end),
    ]


def scene5(T, dur):
    end = dur - 0.25
    t0 = max(T("Умение"), M.MOVE_D)
    head = K.headline(f("s5_head"), "Редкое и ценное качество", "Услышать за короткой фразой проблему",
                      ["проблему"], size=46, w=W)
    pic = K.image_card(f("s5_pic"), img("s10_grateful"), W, label="Спрашивайте — уходят благодарными")
    return [
        item(head, L, 80, t0, end),
        item(K.icon_row(f("s5_thanks"), img("s10_ic_thanks"), "Спасибо, что относитесь к делу так", w=W, h=110,
                        text_size=30), L, 80 + h_of(head) + 24, T("Спасибо"), end),
        item(pic, R, 60, T("бойтесь"), end),
        item(K.icon_row(f("s5_talk"), img("s10_ic_talk"), "С людьми, а не только с товаром", w=W, h=110,
                        text_size=30, outline=S.GREEN), R, 60 + h_of(pic) + 24, T("Разговаривайте"), end),
    ]


def scene6(T, dur):
    end = dur - 0.25
    head = K.headline(f("s6_head"), "В самом конце", "Ответьте на пару вопросов", ["пару"], size=60, w=PW,
                      bg=False)
    y2 = 40 + h_of(head) + 20
    return [
        item(head, PX, 40, T("А"), end),
        item(K.icon_row(f("s6_read"), img("s10_ic_read"), "Читаем каждый ответ", w=720, h=130, text_size=40),
             PX, y2, T("Мы"), end),
        item(K.icon_row(f("s6_survey"), img("s10_ic_survey"), "Обучение — таким, каким нужно вам", w=720, h=130,
                        text_size=36, outline=S.GREEN), PX, y2 + 130 + 24, T("помогает"), end),
    ]


# (номер, начало, конец, mode, enter, контент); S5_END/END — после вклейки фразы
SCENES = [
    (1, 0.00, 13.88, "full", "none", scene1),
    (2, 13.88, 44.34, "corner", "shrink", scene2),
    (3, 44.34, 60.71, "full", "grow", scene3),
    (4, 60.71, 73.86, "corner", "shrink", scene4),
    (5, 73.86, None, "full", "grow", scene5),
    (6, None, None, "corner", "shrink", scene6),
]
