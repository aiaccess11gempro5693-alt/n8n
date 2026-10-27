"""Сценарий 8 «Вопрос часто важнее таблетки» — полный ролик.

Стандарт — docs/video-standard.md: аватар уходит только в правый нижний угол.
Отличие от сценариев 5–7 — свои приёмы подачи: размытые запросы в пунктирных
плашках, карточка вопросов «?», граница «фармацевт / диагноз», развилка
«простая ситуация / к врачу», зачёркивание «не задержка, не допрос — забота»,
итог галочками; и свой ритм: весь кадр → три угловые сцены подряд (вся
«механика» вопроса) → возврат на весь кадр для вывода и опроса.

Сцены (границы — середины пауз в scratch/scenario8-full-v1.mp3):
  1  0.00–23.24    весь кадр, Avatar IV — расплывчатые запросы, человек не врач
  2  23.24–45.21   угол (съезд), Avatar III — работа фармацевта: три вопроса
  3  45.21–68.27   угол, Avatar III — границы: диагноз не ставит, развилка к врачу
  4  68.27–85.50   угол, Avatar III — что это даёт посетителю и вам
  5  85.50–113.24  весь кадр (возврат), Avatar IV — не бойтесь спрашивать; опрос

Запуск:  python3 -m render.corner.build_scenario8   (ONLY=2,3 — только эти сцены)
Выход:   render/corner/scenario8-full.mp4
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
AUDIO = f"{ROOT}/scratch/scenario8-full-v1.mp3"
WHISPER = f"{ROOT}/scratch/scenario8-full-v1-whisper.json"
SCENARIO = f"{ROOT}/docs/scenarios/scenario-8-questions.md"
OUT = f"{HERE}/scenario8-full.mp4"

# весь кадр — колонки по бокам от аватара
L, R, W = 50, 1330, 540
# угол — контент слева и сверху; правый нижний угол (x>1360, y>730) занят аватаром
PX, PW = 100, 1200


def f(name):
    return f"{TMP}/s8_{name}.png"


def img(name):
    return f"{IMG}/{name}.png"


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


# ---------------------------------------------------------------- сцены

def scene1(T, dur):
    end = dur - 0.25
    head = K.headline(f("s1_head"), "Люди редко приходят", "С точным запросом", ["точным"], size=56, w=W)
    hidden = K.headline(f("s1_hidden"), "За этими словами", "То, что сложно сформулировать", ["сложно"],
                        size=50, w=W)
    return [
        item(head, L, 90, T("Люди"), end),
        # три расплывчатые реплики подряд — одной волной
        item(K.fuzzy_chips(f("s1_fuzzy"), [(img("s8_ic_throat"), "что-нибудь от горла"),
                                            (img("s8_ic_immunity"), "для иммунитета"),
                                            (img("s8_ic_head"), "от головы")], w=W),
             L, 90 + h_of(head) + 24, T("Чаще"), end),
        item(hidden, R, 90, T("За"), end),
        item(K.icon_row(f("s1_doctor"), img("s8_ic_doctor"), "Не врач — рассчитывает на вас", w=W, h=110,
                        text_size=34), R, 90 + h_of(hidden) + 24, T("Он"), end),
    ]


def scene2(T, dur):
    end = dur - 0.25
    head = K.headline(f("s2_head"), "Здесь начинается", "Настоящая работа фармацевта", ["работа"], size=60,
                      w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    q = K.question_card(f("s2_q"), "Один-два коротких вопроса",
                        [(img("s8_ic_who"), "Для кого?"), (img("s8_ic_what"), "Что беспокоит?"),
                         (img("s8_ic_when"), "Как давно?")], w=640)
    return [
        item(head, PX, 40, T("здесь"), end),
        item(K.image_card(f("s2_asking"), img("s8_asking"), 520, "Картина проясняется"), PX, y2,
             T("Один-два"), end),
        item(q, PX + 560, y2, T("Для"), end),
        item(K.compare_row(f("s2_real"), img("s8_ic_care"), "Понять проблему, отсеять лишнее", True, w=640),
             PX + 560, y2 + h_of(q) + 24, T("Иногда"), end),
    ]


def scene3(T, dur):
    end = dur - 0.25
    head = K.headline(f("s3_head"), "Помните про", "Границы", ["Границы"], size=60, w=620, bg=False)
    care = K.headline(f("s3_care"), "Это тоже часть", "Заботы и профессионализма", ["Заботы"], size=40, w=560)
    y2 = 40 + max(h_of(head), h_of(care)) + 24
    bound = K.boundary_card(f("s3_bound"), img("s8_ic_pharmacist"), "Фармацевт", "Симптомы и назначения врача",
                            img("s8_ic_doctor"), "Не ставит", "Диагноз", w=PW)
    y3 = y2 + h_of(bound) + 30
    return [
        item(head, PX, 40, T("Помните"), end),
        item(bound, PX, y2, T("фармацевт"), end),
        item(K.fork_card(f("s3_fork"), "Точные вопросы",
                         (img("s8_ic_care"), "Простая ситуация", "Поможете в аптеке", S.GREEN),
                         (img("s8_ic_doctor"), "Честнее и правильнее", "Направить к врачу", S.BLUE), w=PW),
             PX, y3, T("Но"), end),
        # итог сцены — рядом с заголовком, на свободном месте сверху
        item(care, PX + 640, 40, T("Это"), end),
    ]


def scene4(T, dur):
    end = dur - 0.25
    ticks = K.ticks_card(f("s4_ticks"), "Что это даёт человеку",
                         ["Берёт то, что помогает", "Чувствует: его услышали", "Уходит с благодарностью"], w=600)
    return [
        item(K.image_card(f("s4_grateful"), img("s8_grateful"), 560), PX, 60, T("Что"), end),
        item(ticks, PX + 600, 60, T("Человек"), end),
        item(K.headline(f("s4_you"), "А у вас остаётся", "Ощущение хорошо сделанной работы", ["хорошо"],
                        size=44, w=600), PX + 600, 60 + h_of(ticks) + 24, T("А"), end),
    ]


def scene5(T, dur):
    t_survey, end = T("конце"), dur - 0.25
    ask_end = t_survey - 0.4
    head = K.headline(f("s5_head"), "Не бойтесь", "Спрашивать", ["Спрашивать"], size=64, w=W)
    main = K.headline(f("s5_main"), "Задавайте смелее", "Вопрос вовремя ценнее любой таблетки", ["ценнее"],
                      size=50, w=W)
    survey = K.headline(f("s5_survey"), "В конце ролика", "Пара коротких вопросов", ["вопросов"], size=56, w=W)
    return [
        # блок «не бойтесь спрашивать»
        item(head, L, 90, T("Не"), ask_end),
        item(K.strike_card(f("s5_strike"), ["Задержка", "Допрос"], "Забота", w=W), L, 90 + h_of(head) + 24,
             T("Хороший"), ask_end),
        item(main, R, 90, T("Задавайте"), ask_end),
        item(K.icon_row(f("s5_thanks"), img("s8_ic_care"), "Спасибо за внимание к людям", w=W, h=110,
                        text_size=34), R, 90 + h_of(main) + 24, T("Спасибо"), ask_end),
        # блок «опрос»
        item(survey, L, 90, t_survey, end),
        item(K.icon_row(f("s5_opinion"), img("s8_ic_survey"), "Ваше мнение учтём в новых материалах", w=W, h=110,
                        text_size=32), L, 90 + h_of(survey) + 24, T("Ваше"), end),
    ]


SCENES = [
    # (номер, начало, конец, mode, enter, контент)
    (1, 0.00, 23.24, "full", "none", scene1),
    (2, 23.24, 45.21, "corner", "shrink", scene2),
    (3, 45.21, 68.27, "corner", "none", scene3),
    (4, 68.27, 85.50, "corner", "none", scene4),
    (5, 85.50, 113.24, "full", "grow", scene5),
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
        out = f"{TMP}/s8_scene{n}.mp4"
        parts.append(out)
        if only and n not in only:
            continue
        clip = f"{ROOT}/scratch/s8-scene{n}.mp4"
        if not os.path.exists(clip):          # пока нет клипа HeyGen — черновик на подставном
            clip = os.environ.get("DRAFT_CLIP", f"{ROOT}/scratch/s7-scene1.mp4")
        items = content(M.finder(words), dur)
        M.render_scene(clip, dur, words, mode, enter, items, out, TMP)
        print(f"scene {n} ok", flush=True)
    if not only:
        M.concat(parts, AUDIO, OUT, TMP)
        print(OUT)


if __name__ == "__main__":
    main()
