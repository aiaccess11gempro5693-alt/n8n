"""Сценарий 9 «Воронка из трёх вопросов» — полный ролик.

Стандарт — docs/video-standard.md: аватар уходит только в правый нижний угол.
Отличие от сценариев 5–8 — свои приёмы подачи: воронка из трёх уровней, к
которым потом пристраиваются пояснения «зачем» (одна композиция на всю
сцену), пара «вопрос о человеке / вопрос о товаре» по бокам от аватара,
карточка тревожных признаков, формула «3 вопроса + полминуты = точная
помощь»; и свой ритм — строгое чередование: весь кадр → угол → весь кадр →
угол → весь кадр.

Сцены (границы — середины пауз в scratch/scenario9-full-v1.mp3):
  1  0.00–11.43    весь кадр, Avatar IV — приветствие, инструмент «воронка», полминуты
  2  11.43–46.38  угол (съезд), Avatar III — три вопроса и зачем каждый
  3  46.38–67.76  весь кадр (возврат), Avatar IV — вопрос о человеке vs о товаре
  4  67.76–83.51  угол (съезд), Avatar III — тревожные признаки → к врачу
  5  83.51–111.15 весь кадр (возврат), Avatar IV — итог-формула, привычка; опрос

Запуск:  python3 -m render.corner.build_scenario9   (ONLY=2,3 — только эти сцены)
Выход:   render/corner/scenario9-full.mp4
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
AUDIO = f"{ROOT}/scratch/scenario9-full-v1.mp3"
WHISPER = f"{ROOT}/scratch/scenario9-full-v1-whisper.json"
SCENARIO = f"{ROOT}/docs/scenarios/scenario-9-funnel.md"
OUT = f"{HERE}/scenario9-full.mp4"

# весь кадр — колонки по бокам от аватара
L, R, W = 50, 1330, 540
# угол — контент слева и сверху; правый нижний угол (x>1360, y>730) занят аватаром
PX, PW = 100, 1200


def f(name):
    return f"{TMP}/s9_{name}.png"


def img(name):
    return f"{IMG}/{name}.png"


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


# ---------------------------------------------------------------- сцены

def scene1(T, dur):
    end = dur - 0.25
    head = K.headline(f("s1_head"), "Конкретный инструмент", "Воронка из трёх вопросов", ["Воронка"], size=58, w=W)
    pic = K.image_card(f("s1_pic"), img("s9_funnel"), W)
    return [
        item(head, L, 90, T("Разберём"), end),
        item(pic, R, 90, T("воронку"), end),
        item(K.icon_row(f("s1_time"), img("s9_ic_stopwatch"), "Полминуты — почти в любой ситуации", w=W, h=110,
                        text_size=32), R, 90 + h_of(pic) + 24, T("Она"), end),
    ]


# воронка сцены 2: три уровня друг под другом, сужаются книзу
FUNNEL_TOP, FUNNEL_H, FUNNEL_GAP, FUNNEL_STEP = 840, 170, 20, 90
FUNNEL_Y0 = 200


def funnel_geom(i):
    top = FUNNEL_TOP - i * FUNNEL_STEP
    x = PX + (FUNNEL_TOP - top) // 2
    y = FUNNEL_Y0 + i * (FUNNEL_H + FUNNEL_GAP)
    return x, y, top, top - FUNNEL_STEP


def scene2(T, dur):
    end = dur - 0.25
    t_why = T("Смотрите")
    levels = [
        ("s9_ic_q_what", "Для кого и что беспокоит", "«Что именно беспокоит?»", S.BLUE, T("Первый")),
        ("s9_ic_q_when", "Как давно и как часто", "«Когда это началось?»", S.LIGHT_BLUE, T("Второй")),
        ("s9_ic_q_took", "Что уже предпринято", "«Уже что-то принимали?»", S.GREEN, T("Третий")),
    ]
    whys = [("Суть проблемы", T("Первый", t_why)),
            ("Острая или затянувшаяся", T("Второй", t_why)),
            ("Не повторить то, что не подошло", T("Третий", t_why))]
    out = [item(K.headline(f("s2_head"), "Воронка", "Три вопроса по порядку", ["Три"], size=60, w=PW, bg=False),
                PX, 40, T("Первый") - 0.4, end)]
    note_x = PX + FUNNEL_TOP + 40
    out.append(item(K.headline(f("s2_whyhead"), "Смотрите", "Зачем каждый", ["Зачем"], size=40, w=400,
                               bg=False), note_x, FUNNEL_Y0 - 150, t_why, end))
    for i, ((icon, kick, q, col, t), (why, tw)) in enumerate(zip(levels, whys)):
        x, y, top, bot = funnel_geom(i)
        out.append(item(K.funnel_level(f(f"s2_lvl{i}"), str(i + 1), top, bot, FUNNEL_H, img(icon), kick, q, col),
                        x, y, t, end))
        note = K.why_note(f(f"s2_why{i}"), why, w=PX + PW - note_x + 40 - i * 0, h=120, color=col)
        out.append(item(note, note_x - i * FUNNEL_STEP // 2, y + (FUNNEL_H - 120) // 2, tw, end))
    return out


def scene3(T, dur):
    end = dur - 0.25
    t_help = T("Помогает")
    head = K.headline(f("s3_head"), "Замечает и система", "Одно важное различие", ["различие"], size=50, w=W)
    human = K.ask_type_card(f("s3_human"), img("s9_ic_person"), "Вопрос о человеке", "«Что беспокоит?»",
                            "Выявление потребности", True, w=W)
    goods = K.ask_type_card(f("s3_goods"), img("s9_ic_package"), "Вопрос о товаре", "«Какой объём брать?»",
                            "Оформление покупки", False, w=W)
    return [
        item(head, L, 70, max(T("Одно"), M.MOVE_D), end),  # после возврата аватара
        item(human, L, 70 + h_of(head) + 24, T("человеке"), end),
        item(goods, R, 70, T("товаре"), end),
        item(K.headline(f("s3_help"), "Помогает первый", "Про человека, а не про упаковку", ["человека"],
                        size=40, w=W), R, 70 + h_of(goods) + 24, t_help, end),
    ]


def scene4(T, dur):
    end = dur - 0.25
    head = K.headline(f("s4_head"), "Если в ответах", "Тревожные признаки", ["Тревожные"], size=60, w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    alert = K.alert_card(f("s4_alert"), ["Резкая боль", "Высокая температура", "Затянулось надолго"], w=620)
    return [
        item(head, PX, 40, T("И"), end),
        item(K.image_card(f("s4_pic"), img("s9_doctor"), 520), PX, y2, T("И"), end),
        item(alert, PX + 580, y2, T("резкая"), end),
        item(K.icon_row(f("s4_doctor"), img("s9_ic_doctor"), "Честный ход — к врачу", w=620, h=110,
                        text_size=32, outline=S.GREEN), PX + 580, y2 + h_of(alert) + 24, T("здесь"), end),
    ]


def scene5(T, dur):
    t_survey, end = T("ещё"), dur - 0.25
    ask_end = t_survey - 0.4
    head = K.headline(f("s5_head"), "Не затянет разговор", "Наоборот, упростит", ["упростит"], size=48, w=W)
    formula = K.formula_card(f("s5_formula"), [("3", "вопроса"), ("½", "минуты")], "Точная помощь", w=W)
    survey = K.headline(f("s5_survey"), "И ещё одно", "В конце — несколько вопросов", ["вопросов"], size=52, w=W)
    return [
        # блок «итог»
        item(formula, L, 90, max(T("Три"), M.MOVE_D), ask_end),  # после возврата аватара
        item(K.icon_row(f("s5_thanks"), img("s9_ic_person"), "Спасибо, что берёте приём в работу", w=W, h=110,
                        text_size=30), L, 90 + h_of(formula) + 24, T("Спасибо"), ask_end),
        item(head, R, 90, T("Не"), ask_end),
        item(K.icon_row(f("s5_habit"), img("s9_ic_habit"), "Задавайте как привычку", w=W, h=110, text_size=34),
             R, 90 + h_of(head) + 24, T("Задавайте"), ask_end),
        # блок «опрос»
        item(survey, L, 90, t_survey, end),
        item(K.icon_row(f("s5_opinion"), img("s9_ic_survey"), "Не проверка знаний — важно ваше мнение", w=W,
                        h=110, text_size=30), L, 90 + h_of(survey) + 24, T("Это", t_survey), end),
    ]


# (номер, начало, конец, mode, enter, контент)
SCENES = [
    (1, 0.00, 11.43, "full", "none", scene1),
    (2, 11.43, 46.38, "corner", "shrink", scene2),
    (3, 46.38, 67.76, "full", "grow", scene3),
    (4, 67.76, 83.51, "corner", "shrink", scene4),
    (5, 83.51, 111.15, "full", "grow", scene5),
]


def main():
    os.makedirs(TMP, exist_ok=True)
    paras = M.scenario_paragraphs(SCENARIO)
    all_words = M.word_times(" ".join(paras), json.load(open(WHISPER, encoding="utf-8"))["words"])
    only = {int(x) for x in os.environ.get("ONLY", "").split(",") if x}
    parts = []
    for n, a, b, mode, enter, content in SCENES:
        dur = round(b - a, 3)
        words = [(w, round(t - a, 3)) for w, t in all_words if a <= t < b]
        out = f"{TMP}/s9_scene{n}.mp4"
        parts.append(out)
        if only and n not in only:
            continue
        clip = f"{ROOT}/scratch/s9-scene{n}.mp4"
        if not os.path.exists(clip):          # пока нет клипа HeyGen — черновик на подставном
            clip = os.environ.get("DRAFT_CLIP", f"{ROOT}/scratch/s8-scene1.mp4")
        items = content(M.finder(words), dur)
        M.render_scene(clip, dur, words, mode, enter, items, out, TMP)
        print(f"scene {n} ok", flush=True)
    if not only:
        M.concat(parts, AUDIO, OUT, TMP)
        print(OUT)


if __name__ == "__main__":
    main()
