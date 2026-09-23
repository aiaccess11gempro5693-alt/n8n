"""Сценарий 6 «Как здороваться: приём на две секунды» — полный ролик.

Стандарт — docs/video-standard.md. По прямому указанию пользователя ролик
НЕ повторяет сценарий 5: вместо ухода аватара в угол — сплит-экран
(фармацевт в полный рост уезжает влево, справа выезжает панель брендбука);
другой набор приёмов подачи — реплики-пузыри, опоры-колонны, крупная
цифра, порядок «01 → 02», картинка с отметкой ✓.

Сцены (границы — середины пауз в scratch/scenario6-full-v1.mp3):
  1  0.00–8.84    полный кадр, Avatar IV — тема: приём на пару секунд
  2  8.84–27.37   сплит (выезд), Avatar III — правило: первым, до запроса; фразы
  3  27.37–44.03  полный кадр (возврат), Avatar IV — тон задаёте вы: контакт → препараты;
                  к специалисту, а не к окошку
  4  44.03–59.22  сплит (выезд), Avatar III — три опоры + «2 секунды»
  5  59.22–77.02  сплит, Avatar III — заняты: взгляд и кивок
  6  77.02–104.36 полный кадр (возврат), Avatar IV — всю смену → привычка; опрос

Запуск:  python3 -m render.corner.build_scenario6   (ONLY=2,4 — только эти сцены)
Выход:   render/corner/scenario6-full.mp4
"""
import json
import os

from PIL import Image

from . import cards as K
from . import montage as M
from .montage import item

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = f"{HERE}/_frames"
IMG = f"{ROOT}/scratch/img"
AUDIO = f"{ROOT}/scratch/scenario6-full-v1.mp3"
WHISPER = f"{ROOT}/scratch/scenario6-full-v1-whisper.json"
SCENARIO = f"{ROOT}/docs/scenarios/scenario-6-greeting-technique.md"
OUT = f"{HERE}/scenario6-full.mp4"

# полный кадр — колонки по бокам от аватара
L, R, W = 50, 1330, 540
# сплит — панель справа (x 820..1920), контент в её пределах
PX, PW = 890, 980


def f(name):
    return f"{TMP}/s6_{name}.png"


def img(name):
    return f"{IMG}/{name}.png"


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


# ---------------------------------------------------------------- сцены

def scene1(T, dur):
    return [
        # тема + «пара секунд» одной волной (иначе иконка жила бы ~1 с)
        item(K.topic_card(f("s1_topic"), "Конкретный приём", "Как здороваться",
                          "Чтобы это работало"), L, 110, T("Расскажу"), dur - 0.25),
        item(K.icon_row(f("s1_timer"), img("s6_ic_timer"), "Буквально пару секунд", w=W, text_size=38), L, 430,
             T("Расскажу"), dur - 0.25),
    ]


def scene2(T, dur):
    end = dur - 0.25
    head = K.headline(f("s2_head"), "Правило простое", "Первым — ещё до запроса",
                      ["Первым"], size=64, w=PW, bg=False)
    hy = 50
    y2 = hy + h_of(head) + 10
    return [
        item(head, PX, hy, T("Правило"), end),
        # как именно: картинка «подняла взгляд, встретились глазами»
        item(K.image_card(f("s2_first"), img("s6_first"), 470), PX, y2, T("Поднимаете"), end),
        # сами фразы — одной волной, на первой из них
        item(K.speech_bubble(f("s2_b1"), "«Здравствуйте, слушаю вас»", w=470, size=42), PX + 510, y2,
             T("Здравствуйте", T("фразу")), end),
        item(K.speech_bubble(f("s2_b2"), "«Добрый день, чем помочь?»", w=470, size=42, color=K.S.GREEN,
                             tail="right"), PX + 510, y2 + 230, T("Здравствуйте", T("фразу")), end),
    ]


def scene3(T, dur):
    end = dur - 0.25
    tone = K.headline(f("s3_tone"), "С первых секунд", "Тон разговору задаёте вы", ["вы"], size=54, w=W)
    return [
        item(tone, L, 90, T("задаёте"), end),
        item(K.order_card(f("s3_order"), "Контакт между людьми", "Препараты"), L, 90 + h_of(tone) + 20,
             T("контакта"), end),
        item(K.marked_image(f("s3_spec"), img("s6_specialist"), 470, "К специалисту, а не к окошку выдачи",
                            True), R + 35, 90, T("Человек", T("препаратам")), end),
    ]


def scene4(T, dur):
    end = dur - 0.25
    head = K.headline(f("s4_head"), "Хорошее приветствие", "Три опоры", ["Три"], size=64, w=PW, bg=False)
    hy = 50
    py = hy + h_of(head) + 10
    pill = K.pillars(f("s4_pillars"), [(img("s6_ic_eyes"), "Взгляд в глаза"),
                                        (img("s6_ic_phrase"), "Короткая фраза"),
                                        (img("s6_ic_tone"), "Доброжелательная интонация")],
                     w=PW, h=300, isz=110)
    return [
        item(head, PX, hy, T("Три"), end),
        item(pill, PX, py, T("Взгляд"), end),
        item(K.big_metric(f("s4_metric"), "2", "сек", "а впечатление меняется полностью", w=PW),
             PX, py + h_of(pill) + 30, T("Всё"), end),
    ]


def scene5(T, dur):
    end = dur - 0.25
    head = K.headline(f("s5_head"), "Даже когда вы заняты", "Взгляд и лёгкий кивок", ["кивок"],
                      size=60, w=PW, bg=False)
    hy = 50
    y2 = hy + h_of(head) + 10
    seen = K.speech_bubble(f("s5_seen"), "Его заметили — очередь придёт", w=440, size=40, tail="left")
    return [
        item(head, PX, hy, T("Даже"), end),
        item(K.image_card(f("s5_nod"), img("s6_nod"), 500), PX, y2, T("взгляда"), end),
        item(seen, PX + 540, y2, T("заметили"), end),
        item(K.icon_row(f("s5_calm"), img("s6_ic_tone"), "Напряжение уходит ещё до разговора", w=440, h=130,
                        text_size=32), PX + 540, y2 + h_of(seen) + 60, T("Это", T("придёт")), end),
    ]


def scene6(T, dur):
    t_survey, end = T("самом"), dur - 0.25
    habit_end = t_survey - 0.4
    rule = K.headline(f("s6_rule"), "Всю смену", "Первым — с каждым", ["каждым"], size=60, w=W)
    habit = K.icon_row(f("s6_habit"), img("s6_ic_habit"), "Через пару дней — привычка", w=W, h=120,
                       text_size=34)
    return [
        # блок «привычка»
        item(rule, L, 90, T("Попробуйте"), habit_end),
        item(habit, L, 90 + h_of(rule) + 20, T("Через"), habit_end),
        item(K.speech_bubble(f("s6_back"), "Люди отвечают тем же", w=W, size=36, color=K.S.GREEN, tail="right"),
             R, 90, T("Люди"), habit_end),
        # блок «опрос»
        item(K.headline(f("s6_survey"), "В самом конце", "Пара вопросов", ["вопросов"], size=64, w=W),
             L, 90, t_survey, end),
        item(K.icon_row(f("s6_read"), img("s6_ic_survey"), "Мы читаем каждый ответ", w=W, h=120, text_size=36),
             R, 90, T("читаем"), end),
    ]


SCENES = [
    # (номер, начало, конец, mode, enter, контент)
    (1, 0.00, 8.84, "full", "none", scene1),
    (2, 8.84, 27.37, "split", "slide", scene2),
    (3, 27.37, 44.03, "full", "unslide", scene3),
    (4, 44.03, 59.22, "split", "slide", scene4),
    (5, 59.22, 77.02, "split", "none", scene5),
    (6, 77.02, 104.36, "full", "unslide", scene6),
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
        out = f"{TMP}/s6_scene{n}.mp4"
        parts.append(out)
        if only and n not in only:
            continue
        clip = f"{ROOT}/scratch/s6-scene{n}.mp4"
        if not os.path.exists(clip):          # пока нет клипа HeyGen — черновик на подставном
            clip = os.environ.get("DRAFT_CLIP", f"{ROOT}/scratch/s5-scene1.mp4")
        items = content(M.finder(words), dur)
        M.render_scene(clip, dur, words, mode, enter, items, out, TMP)
        print(f"scene {n} ok", flush=True)
    if not only:
        M.concat(parts, AUDIO, OUT, TMP)
        print(OUT)


if __name__ == "__main__":
    main()
