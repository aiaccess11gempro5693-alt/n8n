"""Сценарий 13 «Тонкости: уместность, отказ, ответственное лечение» — полный ролик.

Стандарт — docs/video-standard.md: аватар уходит только в правый нижний угол.
Отличие от сценариев 5–12 — ритм с двумя сценами на весь кадр подряд в конце
(вывод → опрос, один клип HeyGen, разрезанный по паузе, поэтому стык
бесшовный): весь кадр → угол → угол → весь кадр → угол → весь кадр → весь кадр.
Приёмы подачи — новые: плитки-вердикты «уместно / невпопад», «связь с
запросом» (сплошная или разорванная линия) + стрелки доверия, диалог в стиле
мессенджера, «сегодня → завтра», «не про … — а про …», команда препаратов со
скобкой, янтарное последствие, итог сеткой 2×2.

Сцены (границы — середины пауз в scratch/scenario13-full-v1.mp3):
  1  0.00–13.42    весь кадр, Avatar IV — тонкая грань: уместно / невпопад
  2  13.42–30.14   угол (съезд), Avatar III — правило 1: связь с запросом
  3  30.14–46.13   угол, Avatar III — правило 2: спокойно к отказу
  4  46.13–54.32   весь кадр (возврат), Avatar IV — самое важное: не комфорт, а результат
  5  54.32–83.10   угол (съезд), Avatar III — схема врача: команда препаратов
  6  83.10–105.05  весь кадр (возврат), Avatar IV — итог 2×2 + «доводите до конца»
  7  105.05–117.16 весь кадр (без перехода, тот же клип), Avatar IV — опрос

Запуск:  python3 -m render.corner.build_scenario13   (ONLY=2,3 — только эти сцены)
Выход:   render/corner/scenario13-full.mp4
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
AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/scenario13-full-v1.mp3")
WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/scenario13-full-v1-whisper.json")
SCENARIO = f"{ROOT}/docs/scenarios/scenario-13-fine-points.md"
OUT = f"{HERE}/scenario13-full.mp4"

# весь кадр — колонки по бокам от аватара
L, R, W = 50, 1330, 540
# угол — контент слева и сверху; правый нижний угол (x>1360, y>730) занят аватаром
PX, PW = 100, 1200

# Временные замены из одобренной библиотеки прошлых роликов — только пока
# картинка сценария 13 не прошла QA-гейт (DRAFT=1). В финальном ролике
# используются только свои картинки.
DRAFT_SUBST = {
    "s13_ic_miss": "s5_ic_price", "s13_ic_person": "s9_ic_person", "s13_ic_random": "s7_ic_box",
    "s13_ic_comfort": "s12_ic_soft", "s13_ic_result": "s11_ic_done", "s13_ic_cause": "s11_ic_treat",
    "s13_ic_symptom": "s5_ic_relief", "s13_ic_organ": "s11_ic_stomach", "s13_ic_return": "s5_ic_return",
    "s13_ic_calm": "s5_ic_warm", "s13_ic_convince": "s12_ic_explain", "s13_ic_finish": "s9_ic_habit",
    "s13_refusal": "s12_calm",
}


def f(name):
    return f"{TMP}/s13_{name}.png"


def img(name):
    meta = f"{IMG}/{name}.json"
    ok = not os.path.exists(meta) or json.load(open(meta, encoding="utf-8")).get("status") == "ok"
    if ok and os.path.exists(f"{IMG}/{name}.png"):
        return f"{IMG}/{name}.png"
    if os.environ.get("DRAFT") and name in DRAFT_SUBST:
        return f"{IMG}/{DRAFT_SUBST[name]}.png"
    raise FileNotFoundError(f"{name}: картинка не прошла QA или отсутствует (DRAFT=1 — временная замена)")


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


def w_of(made):
    png, pad = made
    return Image.open(png).width - 2 * pad


# ---------------------------------------------------------------- сцены

def scene1(T, dur):
    end = dur - 0.25
    topic = K.topic_card(f("s1_topic"), "Поговорим о", "Тонкая грань", "Где совет, а где навязывание", w=W)
    good = K.verdict_tile(f("s1_good"), img("s13_ic_fit"), "Уместно", "Допродажа помогает", w=W)
    bad = K.verdict_tile(f("s1_bad"), img("s13_ic_miss"), "Невпопад", "Работает против вас",
                         note="Человек чувствует сразу", good=False, w=W)
    return [
        item(topic, L, 80, T("Поговорим"), end),
        item(good, R, 80, T("помогает") - 0.4, end),
        item(bad, R, 80 + h_of(good) + 24, T("Предложение"), end),
    ]


def scene2(T, dur):
    end = dur - 0.25
    head = K.headline(f("s2_head"), "Правило 1 · уместность", "Дополнение — из ситуации человека", ["ситуации"],
                      size=58, w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    t0 = max(T("Первое"), M.MOVE_D)
    link = K.link_row(f("s2_link"), (img("s13_ic_person"), "Ситуация человека"),
                      (img("s13_ic_fit"), "Дополнение по делу"), linked=True)
    y3 = y2 + h_of(link) + 30
    broken = K.link_row(f("s2_broken"), (img("s13_ic_person"), "Запрос"),
                        (img("s13_ic_random"), "Без связи — промолчать"), linked=False)
    t_tr = T("Уместное")
    up = K.trend_badge(f("s2_up"), "Доверие", up=True)
    down = K.trend_badge(f("s2_down"), "Отдаляет", up=False)
    bx = PX + w_of(link) + 30
    return [
        item(head, PX, 40, t0, end),
        item(link, PX, y2, t0, end),
        item(broken, PX, y3, T("Если"), end),
        item(up, bx, y2 + (h_of(link) - h_of(up)) // 2, t_tr, end),
        item(down, bx, y3 + (h_of(broken) - h_of(down)) // 2, t_tr, end),
    ]


def scene3(T, dur):
    end = dur - 0.25
    head = K.headline(f("s3_head"), "Правило 2", "Спокойно к отказу", ["отказу"], size=60, w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    pic = K.image_card(f("s3_pic"), img("s13_refusal"), 420)
    cx, cw = PX + 460, 740
    b1 = K.chat_bubble(f("s3_b1"), "Посетитель", "«Спасибо, только основное»", w=cw)
    b2 = K.chat_bubble(f("s3_b2"), "Вы", "«Конечно. Если понадобится, вы знаете, где нас найти»", mine=True, w=cw)
    y_b2 = y2 + h_of(b1) + 10
    tt = K.today_tomorrow(f("s3_tt"), (img("s13_ic_palm"), "Сегодня", "Отказ"),
                          (img("s13_ic_trust"), "Завтра", "Доверие"), w=cw, isz=92)
    t0 = max(T("Второе"), 0.3)
    return [
        item(head, PX, 40, t0, end),
        item(pic, PX, y2, t0, end),
        item(b1, cx, y2, T("говорит"), end),
        item(b2, cx, y_b2, T("Принимаете"), end),
        item(tt, cx, y_b2 + h_of(b2) + 24, T("Отказ"), end),
    ]


def scene4(T, dur):
    end = dur - 0.25
    head = K.headline(f("s4_head"), "Самое важное", "Ответственное лечение", ["лечение"], size=60, w=W)
    pivot = K.pivot_card(f("s4_pivot"), (img("s13_ic_comfort"), "комфорт"), (img("s13_ic_result"), "результат"), w=W)
    return [
        item(head, L, 80, max(T("самое"), M.MOVE_D), end),
        item(pivot, R, 80, T("Иногда"), end),
    ]


def scene5(T, dur):
    end = dur - 0.25
    head = K.headline(f("s5_head"), "Назначение врача", "Схема из нескольких препаратов", ["препаратов"],
                      size=58, w=PW, bg=False)
    y2 = 40 + h_of(head) + 10
    team = K.team_card(f("s5_team"), "У каждого своя роль",
                       [(img("s13_ic_cause"), "Лечит причину"), (img("s13_ic_symptom"), "Снимает симптом"),
                        (img("s13_ic_organ"), "Защищает орган")], w=PW, isz=110)
    y3 = y2 + h_of(team) + 28
    say = K.script_card(f("s5_say"), "Объясните спокойно",
                        "«Дополняют друг друга, вместе дают полный эффект»", w=700, size=38)
    risk = K.consequence_card(f("s5_risk"), img("s13_ic_return"), "Легкомыслие", "Недолечили",
                              "Вернётся с осложнением", w=460, isz=90)
    return [
        item(head, PX, 40, max(T("врач"), M.MOVE_D), end),
        item(team, PX, y2, T("Один"), end),
        item(say, PX, y3, T("Стоит"), end),
        item(risk, PX + 740, y3, T("Легкомыслие"), end),
    ]


def scene6(T, dur):
    end = dur - 0.25
    grid = K.recap_grid(f("s6_grid"), "Из чего складывается", "Допродажа, которой доверяют",
                        [(img("s13_ic_fit"), "Уместно"), (img("s13_ic_calm"), "Спокойно"),
                         (img("s12_ic_benefit"), "Через пользу"), (img("s13_ic_result"), "Забота о результате")],
                        w=W)
    conv = K.icon_row(f("s6_conv"), img("s13_ic_convince"), "Сомневаются? Объяснённая польза убеждает",
                      w=W, h=130, text_size=30)
    fin = K.icon_row(f("s6_fin"), img("s13_ic_finish"), "Доводите помощь до конца", w=W, h=120, text_size=32,
                     outline=S.GREEN)
    thx = K.icon_row(f("s6_thx"), img("s12_ic_thanks"), "Спасибо за такой подход к людям", w=W, h=120,
                     text_size=30)
    y_f = 80 + h_of(conv) + 24
    return [
        item(grid, L, 80, max(T("Уместно"), M.MOVE_D), end),
        item(conv, R, 80, T("бойтесь"), end),
        item(fin, R, y_f, T("Доводите"), end),
        item(thx, R, y_f + h_of(fin) + 24, T("Спасибо"), end),
    ]


def scene7(T, dur):
    end = dur - 0.25
    head = K.headline(f("s7_head"), "В конце ролика", "Несколько коротких вопросов", ["вопросов"], size=60, w=W)
    op = K.icon_row(f("s7_op"), img("s12_ic_opinion"), "Не проверка знаний — нам важно ваше мнение", w=W, h=140,
                    text_size=30, outline=S.GREEN)
    return [
        item(head, L, 80, max(T("конце"), 0.3), end),
        item(op, R, 80, T("Это"), end),
    ]


# границы сцен (BOUNDS='[...]' в окружении — переопределить)
BOUNDS = json.loads(os.environ.get("BOUNDS", "null") or "null") or [0, 13.42, 30.14, 46.13, 54.32, 83.10,
                                                                     105.05, 117.16]
KINDS = [("full", "none", scene1), ("corner", "shrink", scene2), ("corner", "none", scene3),
         ("full", "grow", scene4), ("corner", "shrink", scene5), ("full", "grow", scene6),
         ("full", "none", scene7)]
SCENES = [(k + 1, BOUNDS[k], BOUNDS[k + 1], *KINDS[k]) for k in range(7)]


def main():
    os.makedirs(TMP, exist_ok=True)
    paras = M.scenario_paragraphs(SCENARIO)
    all_words = M.word_times(" ".join(paras), json.load(open(WHISPER, encoding="utf-8"))["words"])
    only = {int(x) for x in os.environ.get("ONLY", "").split(",") if x}
    parts = []
    for n, a, b, mode, enter, content in SCENES:
        dur = round(b - a, 3)
        # начало первого слова сцены whisper иногда ставит в паузу перед границей
        words = [(w, round(max(t - a, 0.05), 3)) for w, t in all_words if a <= t + 0.25 < b]
        out = f"{TMP}/s13_scene{n}.mp4"
        parts.append(out)
        if only and n not in only:
            continue
        clip = f"{ROOT}/scratch/s13-scene{n}.mp4"
        if not os.path.exists(clip):          # пока нет клипа HeyGen — черновик на подставном
            clip = os.environ.get("DRAFT_CLIP", f"{ROOT}/scratch/s12-scene1.mp4")
        items = content(M.finder(words), dur)
        M.render_scene(clip, dur, words, mode, enter, items, out, TMP)
        print(f"scene {n} ok", flush=True)
    if not only:
        M.concat(parts, AUDIO, OUT, TMP)
        print(OUT)


if __name__ == "__main__":
    main()
