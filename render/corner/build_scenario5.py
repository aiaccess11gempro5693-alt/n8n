"""Сценарий 5 «Приветствие и установление контакта» — полный ролик.

Сцены (границы — середины пауз в озвучке scratch/scenario5-full-v2.mp3):
  1  0.00–23.50  полный кадр, Avatar IV — тема ролика → тревога → контакт взглядом
  2 23.50–45.80  угол, Avatar III (съезд) — приветствие как сигнал доверия
  3 45.80–66.46  угол, Avatar III — цепочка доверия → доверие начинается здесь
  4 66.46–84.04  полный кадр, Avatar IV (возврат) — приветствие это работа →
                 вам ничего не стоит / ему очень много значит
  5 84.04–102.43 угол, Avatar III (съезд) — как здороваться → больше чем отпуск
                 препаратов → наша профессия помогать, спасибо
  6 102.43–114.26 полный кадр, Avatar IV (возврат) — опрос в конце

Правило визуального слоя (CLAUDE.md, 23.09.2026 (10)): в кадре одновременно —
элементы одной мысли; блок держится, пока диктор его раскрывает; ничего
короче ~2 с. Все картинки — scratch/img/ (генерация tools/gen_brand_images.py
с брендбуком как референсом, задания docs/scenarios/scenario-5/images-*.json).

Запуск:  python3 -m render.corner.build_scenario5
Выход:   render/corner/scenario5-full.mp4
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
AUDIO = f"{ROOT}/scratch/scenario5-full-v2.mp3"
WHISPER = f"{ROOT}/scratch/scenario5-full-v2-whisper.json"
SCENARIO = f"{ROOT}/docs/scenarios/scenario-5-greeting.md"
OUT = f"{HERE}/scenario5-full.mp4"

# раскладка: полный кадр — колонки по бокам от аватара; угол — заголовок
# сверху, картинка слева, текстовая колонка справа (над углом с аватаром)
L, R, W = 50, 1330, 540
CX, CRX, CRW, CY = 100, 800, 1020, 230


def f(name):
    return f"{TMP}/{name}.png"


def img(name):
    return f"{IMG}/{name}.png"


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


# ---------------------------------------------------------------- сцены

# Правило текста на экране (23.09.2026 (12)): диктор говорит, субтитры
# дублируют речь дословно — поэтому на экране НЕ повторяем реплику, а даём
# короткий тезис (вывод/суть) и визуализацию; внутри кадра тоже без повторов
# (заголовок и карточка под ним не говорят одно и то же). Смен на экране —
# как можно меньше: блок = одна мысль, появляется целиком.

def scene1(T, dur):
    t_worry, t_eyes, end = T("почти"), T("Первое"), dur - 0.25
    worry_end = t_eyes - 0.1
    worry = K.headline(f("s1_worry"), "Важно понимать", "Посетитель часто встревожен", ["встревожен"],
                       size=56, w=W)
    return [
        item(K.topic_card(f("s1_topic"), "Тема ролика", "Приветствие и установление контакта",
                          "Первый шаг к доверию покупателя"), L, 90, 0.4, t_worry - 0.3),
        # блок "тревога": иллюстрация + тезис + кто его беспокоит (одной карточкой)
        item(K.image_card(f("s1_people"), img("s5_people"), W), L, 90, t_worry, worry_end),
        item(worry, R, 90, t_worry, worry_end),
        item(K.icon_trio(f("s1_trio"), [(img("s5_ic_self"), "за себя"), (img("s5_ic_child"), "за детей"),
                                        (img("s5_ic_close"), "за близких")]),
             R, 90 + h_of(worry) + 20, T("за", t_worry), worry_end),
        # блок "контакт": вы — лицо аптеки
        item(K.image_card(f("s1_eyes"), img("s5_eyes"), W), L, 90, t_eyes, end),
        item(K.headline(f("s1_face"), "Главное", "Вы — лицо аптеки", ["лицо"], size=64, w=W), R, 90, t_eyes, end),
        item(K.compare_row(f("s1_c3"), img("s5_ic_specialist"), "Важнее витрины и цены", True), R, 330,
             T("живого"), end),
    ]


def scene2(T, dur):
    t0 = M.MOVE_D
    return [
        item(M.section_header(f("s2_header"), "Не мелочь", "Приветствие — сигнал доверия"), CX, 70, t0),
        item(K.image_card(f("s2_greet"), img("s5_greeting"), 640), CX, CY, t0 + 0.2),
        item(M.quote_card(f("s2_hear"), "Что слышит посетитель", "«Меня видят и готовы помочь»", size=48),
             CRX, CY, t0 + 0.4, T("Одна") - 0.1),
        item(K.headline(f("s2_eff"), "Эффект первых секунд", "Что даёт тёплая фраза", [], size=46, w=CRW),
             CRX, CY, T("Одна")),
        item(K.icon_row(f("s2_r1"), img("s5_ic_relief"), "Меньше напряжения", w=CRW, h=95, num="01",
                        num_color=S.BLUE, text_size=36), CRX, 425, T("напряжение")),
        item(K.icon_row(f("s2_r2"), img("s5_ic_talk"), "Больше деталей от посетителя", w=CRW, h=95, num="02",
                        num_color=S.GREEN, text_size=36), CRX, 532, T("начинает")),
    ]


def scene3(T, dur):
    t_trust = T("Доверие")
    a_end = t_trust - 0.1
    steps = [
        ("01", "s5_ic_talk", "Открытый разговор", S.BLUE, T("спокойнее")),
        ("02", "s5_ic_help", "Точная помощь", S.BLUE, T("точнее")),
        ("03", "s5_ic_leave", "Спокойный уход", S.LIGHT_BLUE, T("уходит")),
        ("04", "s5_ic_return", "Возвращение", S.GREEN, T("возвращается")),
    ]
    sw, gap = 380, 67                         # 4 карточки + 3 стрелки = 1720
    out = [item(M.section_header(f("s3_header"), "Почему это важно", "Цепочка доверия"), CX, 70, 0.3, a_end)]
    x = CX
    for k, (num, ic, text, col, t) in enumerate(steps):
        card = K.step_card(f(f"s3_step{k}"), img(ic), text, w=sw, num=num, num_color=col)
        out.append(item(card, x, CY, t, a_end))
        if k:
            out.append(item(K.arrow(f(f"s3_arrow{k}")), x - gap // 2 - 22, CY + 110, t, a_end))
        x += sw + gap
    out.append(item(M.quote_card(f("s3_goods"), "Итог", "Лояльность — к специалисту, не к товару", w=1300,
                                 h=150, size=44, color=S.GREEN), CX, 585, T("товаром"), a_end))
    out += [
        item(M.section_header(f("s3_header2"), "Первая секунда", "С неё начинается доверие"), CX, 70, t_trust),
        item(K.image_card(f("s3_trust"), img("s5_trust"), 640), CX, CY, t_trust),
        item(M.quote_card(f("s3_formula"), "Формула", "Приветствие = доверие к аптеке", size=48), CRX, CY,
             t_trust + 0.3),
    ]
    return out


def scene4(T, dur):
    t0 = M.MOVE_D
    t_b = T("Оно") - 0.1
    first = K.headline(f("s4_first"), "Этапы диалога", "С чего всё начинается", [], size=46, w=W)
    ry = 90 + h_of(first) + 20
    t_first = T("Самая")
    return [
        item(K.headline(f("s4_work"), "Профессиональный навык", "Не вежливость, а работа", ["работа"],
                        size=58, w=W), R, 90, t0, t_b),
        item(first, L, 90, t_first, t_b),
        item(K.icon_row(f("s4_st1"), img("s5_ic_greet"), "Приветствие", num="01", num_color=S.GREEN,
                        outline=S.GREEN), L, ry, t_first, t_b),
        item(K.icon_row(f("s4_st2"), img("s5_ic_ask"), "Выяснение потребности", num="02", dim=True),
             L, ry + 130, t_first, t_b),
        item(K.icon_row(f("s4_st3"), img("s5_ic_advice"), "Рекомендация", num="03", dim=True),
             L, ry + 260, t_first, t_b),
        # блок "цена / ценность"
        item(K.step_card(f("s4_free"), img("s5_ic_free"), "0 ₽ и пара секунд", w=W, kicker="Цена для вас",
                         text_size=40), L, 90, t_b + 0.1),
        item(K.step_card(f("s4_much"), img("s5_ic_heart"), "Чувство поддержки", w=W,
                         kicker="Ценность для посетителя", text_size=40), R, 90, T("очень")),
        item(K.icon_row(f("s4_pain"), img("s5_ic_pain"), "Вдвойне — при тревоге и боли", text_size=32),
             R, 400, T("Особенно")),
    ]


def scene5(T, dur):
    t0 = M.MOVE_D
    t_b, t_c = T("Мы"), T("Это")
    a_end = t_b - 0.1
    return [
        # блок "правило приветствия" — чек-лист появляется целиком
        item(M.section_header(f("s5_h1"), "Правило", "Здоровайтесь первым"), CX, 70, t0, a_end),
        item(K.image_card(f("s5_hello"), img("s5_first_hello"), 640), CX, CY, t0 + 0.2, a_end),
        item(K.icon_row(f("s5_r1"), img("s5_ic_first"), "Инициатива за вами", w=CRW, h=95, text_size=36), CRX,
             CY, t0 + 0.4, a_end),
        item(K.icon_row(f("s5_r2"), img("s5_ic_warm"), "Тёплый тон и улыбка", w=CRW, h=95, text_size=36), CRX,
             CY + 115, t0 + 0.4, a_end),
        item(K.icon_row(f("s5_r3"), img("s5_ic_eye"), "Зрительный контакт", w=CRW, h=95, text_size=36), CRX,
             CY + 230, t0 + 0.4, a_end),
        # блок "роль фармацевта" — заголовок и картинка держатся до конца сцены
        item(M.section_header(f("s5_h2"), "Наша роль", "Кто мы для посетителя"), CX, 70, t_b),
        item(K.image_card(f("s5_meet"), img("s5_meet"), 640), CX, CY, t_b),
        item(K.compare_row(f("s5_c1"), img("s5_ic_pills"), "Выдача препаратов", False, w=CRW), CRX, CY, t_b + 0.3,
             t_c - 0.1),
        item(K.compare_row(f("s5_c2"), img("s5_ic_heart"), "Поддержка в трудный момент", True, w=CRW), CRX,
             CY + 130, T("первыми"), t_c - 0.1),
        item(M.quote_card(f("s5_mission"), "Миссия", "Помощь — суть профессии", size=52), CRX, CY, t_c),
        item(M.quote_card(f("s5_thanks"), "Спасибо", "за человечность в работе", size=44, color=S.GREEN),
             CRX, CY + 210, T("Спасибо")),
    ]


def scene6(T, dur):
    t_q = T("конце")
    head = K.headline(f("s6_head"), "Далее", "Короткий опрос", ["опрос"], size=60, w=W)
    ry = 90 + h_of(head) + 20
    return [
        item(K.image_card(f("s6_survey"), img("s5_survey"), W), L, 90, t_q),
        item(head, R, 90, t_q),
        item(K.compare_row(f("s6_c1"), img("s5_ic_exam"), "Проверка знаний", False), R, ry, T("проверка")),
        item(K.compare_row(f("s6_c2"), img("s5_ic_opinion"), "Важно ваше мнение", True), R, ry + 130, T("важно")),
        item(K.compare_row(f("s6_c3"), img("s5_ic_next"), "Улучшим следующие ролики", True), R, ry + 260,
             T("обязательно")),
    ]


SCENES = [
    # (номер, начало, конец, mode, enter, контент)
    (1, 0.00, 23.50, "full", "none", scene1),
    (2, 23.50, 45.80, "corner", "shrink", scene2),
    (3, 45.80, 66.46, "corner", "none", scene3),
    (4, 66.46, 84.04, "full", "grow", scene4),
    (5, 84.04, 102.43, "corner", "shrink", scene5),
    (6, 102.43, 114.26, "full", "grow", scene6),
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
        out = f"{TMP}/s5_scene{n}.mp4"
        parts.append(out)
        if only and n not in only:
            continue
        items = content(M.finder(words), dur)
        M.render_scene(f"{ROOT}/scratch/s5-scene{n}.mp4", dur, words, mode, enter, items, out, TMP)
        print(f"scene {n} ok", flush=True)
    if not only:
        M.concat(parts, AUDIO, OUT, TMP)
        print(OUT)


if __name__ == "__main__":
    main()
