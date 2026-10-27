"""Сценарий 11 «Допродажа — это полнота помощи» — полный ролик.

Стандарт — docs/video-standard.md: аватар уходит только в правый нижний угол.
Отличие от сценариев 5–10 — свои приёмы подачи: две роли «Продавец /
Фармацевт» по бокам от аватара, пары «средство + дополнение» с зелёным «+»,
шкала полноты «половина решения / полное решение», правило-таймлайн
«потребность → предложение → польза», карточка «человек слышит как…»,
«Молчание ≠ деликатность»; и свой ритм — три угловые сцены подряд с разной
раскладкой, возврат на весь кадр и опрос снова в углу:
весь кадр → угол → угол → угол → весь кадр → угол.

Сцены (границы — середины пауз в scratch/scenario11-full-v1.mp3):
  1  0.00–19.64    весь кадр, Avatar IV — продавец и фармацевт
  2  19.64–42.97   угол (съезд), Avatar III — суть допродажи: средство + дополнение
  3  42.97–62.30   угол, Avatar III — половина решения / полное решение
  4  62.30–82.82   угол, Avatar III — главное правило; «слышит как совет»
  5  82.82–100.38  весь кадр (возврат), Avatar IV — не бойтесь предлагать; спасибо
  6  100.38–108.93 угол (съезд), Avatar III — опрос

Запуск:  python3 -m render.corner.build_scenario11   (ONLY=2,3 — только эти сцены)
Выход:   render/corner/scenario11-full.mp4
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
AUDIO = f"{ROOT}/scratch/scenario11-full-v1.mp3"
WHISPER = f"{ROOT}/scratch/scenario11-full-v1-whisper.json"
SCENARIO = f"{ROOT}/docs/scenarios/scenario-11-upsell.md"
OUT = f"{HERE}/scenario11-full.mp4"

# весь кадр — колонки по бокам от аватара
L, R, W = 50, 1330, 540
# угол — контент слева и сверху; правый нижний угол (x>1360, y>730) занят аватаром
PX, PW = 100, 1200
COL2, COL2_W = PX + 580, 620


def f(name):
    return f"{TMP}/s11_{name}.png"


def img(name):
    return f"{IMG}/{name}.png"


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


def w_of(made):
    png, pad = made
    return Image.open(png).width - 2 * pad


# ---------------------------------------------------------------- сцены

def scene1(T, dur):
    end = dur - 0.25
    head = K.headline(f("s1_head"), "Есть разница", "Продавец и фармацевт", ["фармацевт"], size=48, w=W)
    seller = K.role_card(f("s1_seller"), img("s11_ic_seller"), "Продавец", "Отпускает то, что попросили", w=W)
    pharm = K.role_card(f("s1_pharm"), img("s11_ic_pharm"), "Фармацевт", "Думает на шаг вперёд",
                        chips=["Быстрее", "Мягче", "Без осложнений"], accent=True, w=W)
    return [
        item(head, L, 80, T("Есть"), end),
        item(seller, L, 80 + h_of(head) + 24, T("Продавец"), end),
        item(pharm, R, 80, T("Фармацевт", T("Продавец")), end),
        item(K.stamp(f("s1_stamp"), "Отличает специалиста", size=32), R, 80 + h_of(pharm) + 24, T("Именно"), end),
    ]


def scene2(T, dur):
    end = dur - 0.25
    head = K.headline(f("s2_head"), "Суть допродажи", "Не «продать больше», а полнота помощи", ["полнота"],
                      size=56, w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    pic = K.image_card(f("s2_pic"), img("s11_combo"), 520)
    c1 = K.plus_combo(f("s2_c1"), (img("s11_ic_stomach"), "Раздражает желудок"),
                      (img("s11_ic_shield"), "Защита"), w=COL2_W)
    c2 = K.plus_combo(f("s2_c2"), (img("s11_ic_treat"), "Лечение"),
                      (img("s11_ic_recover"), "Быстрее восстановиться"), w=COL2_W)
    return [
        item(head, PX, 40, max(T("суть"), M.MOVE_D), end),
        item(pic, PX, y2, max(T("суть"), M.MOVE_D), end),
        item(c1, COL2, y2, T("средству"), end),
        item(c2, COL2, y2 + h_of(c1) + 24, T("лечению"), end),
        item(K.icon_row(f("s2_care"), img("s11_ic_care"), "Забота в виде рекомендации", w=520, h=110,
                        text_size=30, outline=S.GREEN), PX, y2 + h_of(pic) + 24, T("Такое"), end),
    ]


def scene3(T, dur):
    end = dur - 0.25
    head = K.headline(f("s3_head"), "Нужное дополнение", "Доводите помощь до конца", ["конца"], size=56,
                      w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    bars = K.completeness_bars(f("s3_bars"), [("Половина решения", 0.5, False, ""),
                                              ("Полное решение", 1.0, True, "выздоровеет быстрее")], w=700)
    return [
        item(head, PX, 40, 0.3, end),
        item(K.image_card(f("s3_pic"), img("s11_full"), 470), PX, y2, 0.3, end),
        item(bars, PX + 500, y2, T("половиной"), end),
        item(K.icon_row(f("s3_done"), img("s11_ic_done"), "Вы сделали всё, что могли, а не промолчали", w=700,
                        h=120, text_size=32, outline=S.GREEN), PX + 500, y2 + h_of(bars) + 24, T("чувствуете"), end),
    ]


def scene4(T, dur):
    end = dur - 0.25
    head = K.headline(f("s4_head"), "Допродажа без неловкости", "Главное правило", ["правило"], size=60,
                      w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    line = K.rule_timeline(f("s4_line"), "Порядок", [(img("s11_ic_need"), "Потребность понятна"),
                                                    (img("s11_ic_offer"), "Предложение"),
                                                    (img("s11_ic_benefit"), "Объясните пользой")], w=PW)
    y3 = y2 + h_of(line) + 24
    heard = K.heard_as(f("s4_heard"), img("s11_ic_listen"), "Человек слышит", "Совет специалиста",
                       "«Купите ещё»", w=640)
    return [
        item(head, PX, 40, 0.3, end),
        item(line, PX, y2, T("предложение"), end),
        item(heard, PX, y3, T("Уместное"), end),
        item(K.stamp(f("s4_stamp"), "Нормальная часть заботы"), PX + 680, y3 + 40, T("Тогда"), end),
    ]


def scene5(T, dur):
    end = dur - 0.25
    t0 = max(T("бойтесь"), M.MOVE_D)            # после возврата аватара
    head = K.headline(f("s5_head"), "Не бойтесь", "Предлагать", ["Предлагать"], size=60, w=W)
    chips = K.word_chips(f("s5_chips"), "Как", ["Смело", "По-доброму", "Через пользу"], w=W)
    neq = K.not_equal(f("s5_neq"), img("s11_ic_silence"), "Молчание", "деликатность", "недоданная помощь", w=W)
    return [
        item(head, L, 80, t0, end),
        item(chips, L, 80 + h_of(head) + 24, T("Предлагайте"), end),
        item(neq, R, 80, T("Молчание"), end),
        item(K.icon_row(f("s5_thanks"), img("s11_ic_thanks"), "Спасибо: лечим полно, а не наполовину", w=W,
                        h=120, text_size=30), R, 80 + h_of(neq) + 24, T("Спасибо"), end),
    ]


def scene6(T, dur):
    end = dur - 0.25
    head = K.headline(f("s6_head"), "И напоследок", "Несколько вопросов", ["вопросов"], size=60, w=PW,
                      bg=False)
    y2 = 40 + h_of(head) + 20
    return [
        item(head, PX, 40, max(T("напоследок"), M.MOVE_D), end),
        item(K.icon_row(f("s6_listen"), img("s11_ic_survey"), "Важно услышать именно вас", w=580, h=130,
                        text_size=34), PX, y2, T("Нам"), end),
        item(K.icon_row(f("s6_use"), img("s11_ic_care"), "Ответы учтём в работе", w=580, h=130,
                        text_size=34, outline=S.GREEN), PX + 620, y2, T("ответы"), end),
    ]


# (номер, начало, конец, mode, enter, контент)
SCENES = [
    (1, 0.00, 19.64, "full", "none", scene1),
    (2, 19.64, 42.97, "corner", "shrink", scene2),
    (3, 42.97, 62.30, "corner", "none", scene3),
    (4, 62.30, 82.82, "corner", "none", scene4),
    (5, 82.82, 100.38, "full", "grow", scene5),
    (6, 100.38, 108.93, "corner", "shrink", scene6),
]


def main():
    os.makedirs(TMP, exist_ok=True)
    paras = M.scenario_paragraphs(SCENARIO)
    all_words = M.word_times(" ".join(paras), json.load(open(WHISPER, encoding="utf-8"))["words"])
    only = {int(x) for x in os.environ.get("ONLY", "").split(",") if x}
    parts = []
    for n, a, b, mode, enter, content in SCENES:
        dur = round(b - a, 3)
        # whisper иногда ставит начало первого слова сцены в паузу перед границей
        # («Не» в 82.60 при границе 82.82) — такое слово относится к следующей сцене
        words = [(w, round(max(t - a, 0.05), 3)) for w, t in all_words if a <= t + 0.25 < b]
        out = f"{TMP}/s11_scene{n}.mp4"
        parts.append(out)
        if only and n not in only:
            continue
        clip = f"{ROOT}/scratch/s11-scene{n}.mp4"
        if not os.path.exists(clip):          # пока нет клипа HeyGen — черновик на подставном
            clip = os.environ.get("DRAFT_CLIP", f"{ROOT}/scratch/s10-scene1.mp4")
        items = content(M.finder(words), dur)
        M.render_scene(clip, dur, words, mode, enter, items, out, TMP)
        print(f"scene {n} ok", flush=True)
    if not only:
        M.concat(parts, AUDIO, OUT, TMP)
        print(OUT)


if __name__ == "__main__":
    main()
