"""Сценарий 7 «Приветствие в сложные моменты» — полный ролик.

Стандарт — docs/video-standard.md: аватар уходит только в правый нижний угол.
Отличие от сценариев 5 и 6 — свои приёмы подачи: метки-ситуации,
карточка «ситуация → что делать» (сквозной приём ролика: сцены 2 и 3 —
две ситуации одним языком), готовая фраза-скрипт, счётчик «×100»; и свой
ритм: две угловые сцены подряд в середине, длинная сцена на весь кадр
перед финалом, опрос — в углу.

Сцены (границы — середины пауз в scratch/scenario7-full-v1.mp3):
  1  0.00–18.04   весь кадр, Avatar IV — сложные моменты: очередь/телефон/товар/запрос с порога
  2  18.04–36.62  угол (съезд), Avatar III — начал с запроса → поздороваться в ответ + фраза
  3  36.62–50.08  угол, Avatar III — большая очередь → контакт глазами
  4  50.08–92.69  весь кадр (возврат), Avatar IV — интонация ×100; тёплое начало, спасибо
  5  92.69–102.03 угол (съезд), Avatar III — несколько вопросов

Запуск:  python3 -m render.corner.build_scenario7   (ONLY=2,3 — только эти сцены)
Выход:   render/corner/scenario7-full.mp4
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
AUDIO = f"{ROOT}/scratch/scenario7-full-v1.mp3"
WHISPER = f"{ROOT}/scratch/scenario7-full-v1-whisper.json"
SCENARIO = f"{ROOT}/docs/scenarios/scenario-7-hard-moments.md"
OUT = f"{HERE}/scenario7-full.mp4"

# весь кадр — колонки по бокам от аватара
L, R, W = 50, 1330, 540
# угол — контент слева и сверху; правый нижний угол (x>1360, y>730) занят аватаром
PX, PW = 100, 1200


def f(name):
    return f"{TMP}/s7_{name}.png"


def img(name):
    return f"{IMG}/{name}.png"


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


# ---------------------------------------------------------------- сцены

def scene1(T, dur):
    end = dur - 0.25
    head = K.headline(f("s1_head"), "Поговорим о", "Сложных моментах", ["Сложных"], size=60, w=W)
    return [
        item(head, L, 90, T("Поговорим"), end),
        # перечисление подряд — одной волной
        item(K.tag_chips(f("s1_chips"), [(img("s7_ic_queue"), "Очередь"), (img("s7_ic_phone"), "Звонит телефон"),
                                         (img("s7_ic_box"), "Приехал товар"), (img("s7_ic_door"), "Запрос с порога")],
                         w=W), L, 90 + h_of(head) + 24, T("Бывает"), end),
        item(K.headline(f("s1_help"), "Нет секунды на приветствие?", "Именно здесь оно выручает", ["выручает"],
                        size=52, w=W), R, 90, T("Кажется"), end),
    ]


def scene2(T, dur):
    end = dur - 0.25
    case = K.case_card(f("s2_case"), img("s7_ic_door"), "Начал сразу с запроса",
                       "Поздоровайтесь в ответ и перехватите инициативу", w=PW)
    y2 = 60 + h_of(case) + 30
    script = K.script_card(f("s2_script"), "Скажите", "«Здравствуйте, сейчас помогу. Давайте уточню пару деталей»",
                           w=640, size=40)
    return [
        item(case, PX, 60, T("Если"), end),
        item(K.image_card(f("s2_reply"), img("s7_reply"), 520), PX, y2, T("Поздоровайтесь"), end),
        item(script, PX + 560, y2, T("Здравствуйте", T("инициативу")), end),
        item(K.compare_row(f("s2_done"), img("s7_ic_warm"), "И поприветствовали, и к делу", True, w=640),
             PX + 560, y2 + h_of(script) + 24, T("Так"), end),
    ]


def scene3(T, dur):
    end = dur - 0.25
    case = K.case_card(f("s3_case"), img("s7_ic_queue"), "Большая очередь",
                       "Контакт глазами — с каждым, кто ждёт", w=PW)
    y2 = 60 + h_of(case) + 30
    return [
        item(case, PX, 60, T("Если"), end),
        item(K.image_card(f("s3_queue"), img("s7_queue"), 520), PX, y2, T("Если"), end),
        # одна фраза диктора — одной волной
        item(K.icon_row(f("s3_nod"), img("s7_ic_eye"), "Взгляд и кивок — секунда", w=640, h=110, text_size=36),
             PX + 560, y2, T("Короткий"), end),
        item(K.icon_row(f("s3_calm"), img("s7_ic_queue"), "Человек замечен и ждёт спокойнее", w=640, h=110,
                        text_size=34), PX + 560, y2 + 140, T("Короткий"), end),
    ]


def scene4(T, dur):
    t_warm, end = T("Тёплое"), dur - 0.25
    tone_end = t_warm - 0.4
    live = K.headline(f("s4_live"), "Секрет живого приветствия", "Смотреть на человека", ["человека"], size=50, w=W)
    warm = K.headline(f("s4_warm"), "Тёплое начало", "Задаёт весь диалог", ["весь"], size=56, w=W)
    return [
        # блок «интонация»
        item(K.counter(f("s4_count"), "×100", "«Здравствуйте» за смену — и каждое звучит по-разному"),
             L, 90, T("Одна"), tone_end),
        item(live, R, 90, T("Секрет"), tone_end),
        item(K.compare_row(f("s4_through"), img("s7_ic_blank"), "Сквозь него", False), R,
             90 + h_of(live) + 20, T("Секрет"), tone_end),
        # блок «спасибо»: тезис слева держится, ниже на одном месте сменяются мысли
        item(warm, L, 90, t_warm, end),
        item(K.icon_row(f("s4_even"), img("s7_ic_eye"), "Ровно — даже в спешке", w=W, h=110, text_size=36),
             L, 90 + h_of(warm) + 20, T("Держите"), T("Не", T("мимо")) - 0.2),
        item(K.icon_row(f("s4_back"), img("s7_ic_warm"), "Секунда возвращается теплом", w=W, h=110, text_size=34),
             L, 90 + h_of(warm) + 20, T("Не", T("мимо")), end),
        item(K.headline(f("s4_thanks"), "Спасибо", "Каждого — как человека, а не запрос", ["человека"],
                        size=46, w=W), R, 90, T("Спасибо"), end),
    ]


def scene5(T, dur):
    end = dur - 0.25
    head = K.headline(f("s5_head"), "И напоследок", "Несколько вопросов", ["вопросов"], size=64, w=PW, bg=False)
    return [
        item(head, PX, 80, T("напоследок"), end),
        item(K.icon_row(f("s5_hear"), img("s7_ic_survey"), "Важно услышать именно вас — ответы учтём в работе",
                        w=900, h=120, text_size=36), PX, 80 + h_of(head) + 30, T("Нам"), end),
    ]


SCENES = [
    # (номер, начало, конец, mode, enter, контент)
    (1, 0.00, 18.04, "full", "none", scene1),
    (2, 18.04, 36.62, "corner", "shrink", scene2),
    (3, 36.62, 50.08, "corner", "none", scene3),
    (4, 50.08, 92.69, "full", "grow", scene4),
    (5, 92.69, 102.03, "corner", "shrink", scene5),
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
        out = f"{TMP}/s7_scene{n}.mp4"
        parts.append(out)
        if only and n not in only:
            continue
        clip = f"{ROOT}/scratch/s7-scene{n}.mp4"
        if not os.path.exists(clip):          # пока нет клипа HeyGen — черновик на подставном
            clip = os.environ.get("DRAFT_CLIP", f"{ROOT}/scratch/s6-scene1.mp4")
        items = content(M.finder(words), dur)
        M.render_scene(clip, dur, words, mode, enter, items, out, TMP)
        print(f"scene {n} ok", flush=True)
    if not only:
        M.concat(parts, AUDIO, OUT, TMP)
        print(OUT)


if __name__ == "__main__":
    main()
