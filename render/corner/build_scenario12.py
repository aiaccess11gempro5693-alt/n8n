"""Сценарий 12 «Схема: основное → дополнение → польза» — полный ролик.

Стандарт — docs/video-standard.md: аватар уходит только в правый нижний угол.
Отличие от сценариев 5–11 — сквозная цветная схема: в сцене 2 появляются три
ячейки «основное → дополнение → польза» (голубая / синяя / зелёная), в обоих
примерах (сцены 3 и 5) те же ячейки тех же цветов заполняются конкретными
средствами через «+» и «=», в итоге (сцена 6) схема собирается вертикальной
лесенкой. Плюс карточка приёма с цитатой и замена слова «взять» →
«показать / взглянуть». Ритм — 7 сцен, пары угловых сцен-примеров
разделены возвратом на весь кадр:
весь кадр → угол → угол → весь кадр → угол → весь кадр → угол.

Сцены (границы — середины пауз в scratch/scenario12-full-v2.mp3):
  1  0.00–7.88     весь кадр, Avatar IV — тема: естественная допродажа
  2  7.88–22.83    угол (съезд), Avatar III — два шага: три ячейки схемы
  3  22.83–41.13   угол, Avatar III — пример 1: спрей + пастилки = между применениями
  4  41.13–60.69   весь кадр (возврат), Avatar IV — два приёма
  5  60.69–74.58   угол (съезд), Avatar III — пример 2: капли + раствор
  6  74.58–96.35   весь кадр (возврат), Avatar IV — схема простая, не бойтесь
  7  96.35–106.34  угол (съезд), Avatar III — опрос
Дорожка v2 = v1 с переозвученной фразой «К каплям…» (в v1 «К» проглочено).

Запуск:  python3 -m render.corner.build_scenario12   (ONLY=2,3 — только эти сцены)
Выход:   render/corner/scenario12-full.mp4
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
AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/scenario12-full-v2.mp3")
WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/scenario12-full-v2-whisper.json")
SCENARIO = f"{ROOT}/docs/scenarios/scenario-12-upsell-scheme.md"
OUT = f"{HERE}/scenario12-full.mp4"

# весь кадр — колонки по бокам от аватара
L, R, W = 50, 1330, 540
# угол — контент слева и сверху; правый нижний угол (x>1360, y>730) занят аватаром
PX, PW = 100, 1200
# ряд схемы: три ячейки и два оператора между ними на ширину PW
CELL_W, CELL_H, OP = 340, 320, 64
GAP = (PW - 3 * CELL_W - 2 * OP) // 4          # зазор ячейка–оператор


def f(name):
    return f"{TMP}/s12_{name}.png"


def img(name):
    return f"{IMG}/{name}.png"


def h_of(made):
    png, pad = made
    return Image.open(png).height - 2 * pad


def cell_x(k):
    return PX + k * (CELL_W + 2 * GAP + OP)


def op_x(k):
    return cell_x(k) + CELL_W + GAP


def scheme_row(tag, cells, ops, y, t1, t23, end):
    """Ряд схемы: ячейка 1 — по своему предложению, ячейки 2–3 с операторами —
    одной волной (одно предложение)."""
    out = []
    for k, (kind, label, icon, text) in enumerate(cells):
        made = K.scheme_cell(f(f"{tag}_c{k}"), kind, label, img(icon), text, w=CELL_W, h=CELL_H, isz=104)
        out.append(item(made, cell_x(k), y, t1 if k == 0 else t23, end))
    for k, sym in enumerate(ops):
        col = K.SCHEME_COLORS[cells[k + 1][0]]
        made = K.op_badge(f(f"{tag}_op{k}"), sym, col, OP)
        out.append(item(made, op_x(k), y + (CELL_H - OP) // 2, t23, end))
    return out


# ---------------------------------------------------------------- сцены

def scene1(T, dur):
    end = dur - 0.25
    topic = K.topic_card(f("s1_topic"), "Разберём схему", "Естественная допродажа", "Из двух простых шагов", w=W)
    return [item(topic, L, 80, T("Разберём"), end)]


def scene2(T, dur):
    end = dur - 0.25
    head = K.headline(f("s2_head"), "Схема допродажи", "Два шага", ["шага"], size=60, w=PW, bg=False)
    y2 = 40 + h_of(head) + 6
    t0 = max(T("первый"), M.MOVE_D)
    row = scheme_row("s2", [("main", "Шаг 1", "s12_ic_main", "Отпустите основной товар"),
                            ("add", "Шаг 2", "s12_ic_addon", "Предложите дополнение"),
                            ("benefit", "Коротко", "s12_ic_benefit", "Объясните, зачем оно")],
                     ["→", "+"], y2, t0, T("второй"), end)
    # «человек спокоен и открыт» — картинка под шагом 1 и зелёная плашка рядом, одной волной
    y3 = y2 + CELL_H + 30
    calm = K.image_card(f("s2_calm"), img("s12_calm"), CELL_W)
    ok = K.stamp(f("s2_ok"), "Спокоен и открыт", size=34)
    t_calm = T("Человек")
    return [item(head, PX, 40, M.MOVE_D, end)] + row + [
        item(calm, PX, y3, t_calm, end),
        item(ok, PX + CELL_W + 30, y3 + (h_of(calm) - h_of(ok)) // 2, t_calm, end),
    ]


def example(tag, T, dur, kicker, title, accent, pic, cells, t1, t23, extra):
    end = dur - 0.25
    head = K.headline(f(f"{tag}_head"), kicker, title, accent, size=60, w=PW, bg=False)
    y2 = 40 + h_of(head) + 6
    t0 = max(T(kicker.split()[0]), M.MOVE_D)
    row = scheme_row(tag, cells, ["+", "="], y2, t1, t23, end)
    y3 = y2 + CELL_H + 30
    picm = K.image_card(f(f"{tag}_pic"), img(pic), 380)
    made, t_extra = extra
    return [item(head, PX, 40, t0, end), item(picm, PX, y3, t0, end)] + row + [
        item(made, PX + 420, y3 + 40, t_extra, end),
    ]


def scene3(T, dur):
    bubble = K.speech_bubble(f("s3_bubble"), "«Ваш спрей. … Показать?»", w=560, size=44)
    return example("s3", T, dur, "Пример", "Спрей от боли в горле", ["Спрей"], "s12_spray",
                   [("main", "Основное", "s12_ic_spray", "Спрей для горла"),
                    ("add", "Дополнение", "s12_ic_lozenge", "Пастилки с антисептиком"),
                    ("benefit", "Польза", "s12_ic_between", "Действуют между применениями")],
                   T("берёт"), T("Многие"), (bubble, T("говорите")))


def scene4(T, dur):
    end = dur - 0.25
    head = K.headline(f("s4_head"), "Обратите внимание", "Два приёма", ["приёма"], size=60, w=W)
    tech = K.technique_card(f("s4_tech"), 1, img("s12_ic_explain"), "Приём 1", "Объясните пользу",
                            "действуют между применениями", w=W)
    swap = K.word_swap(f("s4_swap"), "Приём 2 · мягкое слово", "взять", ["показать", "взглянуть"], w=W)
    swap_h = h_of(swap)
    return [
        item(head, L, 80, max(T("Обратите"), M.MOVE_D), end),
        item(tech, L, 80 + h_of(head) + 24, T("Первый"), end),
        item(swap, R, 80, T("Второй"), end),
        item(K.stamp(f("s4_stamp"), "Совет, а не продажа", size=34), R, 80 + swap_h + 24, T("Мягкая"), end),
    ]


def scene5(T, dur):
    stamp = K.stamp(f("s5_stamp"), "Коротко, по делу, через пользу", size=32)
    return example("s5", T, dur, "Ещё пример", "Капли от насморка", ["Капли"], "s12_drops",
                   [("main", "Основное", "s12_ic_drops", "Капли от насморка"),
                    ("add", "Дополнение", "s12_ic_rinse", "Промывающий раствор"),
                    ("benefit", "Польза", "s12_ic_clean", "Очищает и продлевает эффект")],
                   T("покупает"), T("каплям"), (stamp, T("Коротко")))


def scene6(T, dur):
    end = dur - 0.25
    t0 = max(T("Схема"), M.MOVE_D)
    stack = K.scheme_stack(f("s6_stack"), "Схема простая",
                           [("main", img("s12_ic_main"), "Основное"),
                            ("add", img("s12_ic_addon"), "Дополнение"),
                            ("benefit", img("s12_ic_benefit"), "Польза")], w=W)
    y_l = 80 + h_of(stack) + 24
    three = K.stamp(f("s6_three"), "Три шага, одна фраза", size=32)
    bubble = K.speech_bubble(f("s6_bubble"), "«Спасибо, не надо»", w=W, size=44, color=S.GRAY)
    y_r = 80 + h_of(bubble) + 14
    ok = K.stamp(f("s6_ok"), "И это нормально", size=34)
    return [
        item(stack, L, 80, t0, end),
        item(three, L, y_l, T("Три"), end),
        item(K.icon_row(f("s6_help"), img("s12_ic_help"), "Помогайте полно в каждом уместном диалоге", w=W,
                        h=130, text_size=30, outline=S.GREEN), L, y_l + h_of(three) + 24, T("Помогайте"), end),
        item(bubble, R, 80, T("бойтесь"), end),
        item(ok, R, y_r, T("бойтесь"), end),
        item(K.icon_row(f("s6_thanks"), img("s12_ic_thanks"), "Спасибо, что берёте приём в работу", w=W,
                        h=120, text_size=30), R, y_r + h_of(ok) + 24, T("Спасибо", T("Помогайте")), end),
    ]


def scene7(T, dur):
    end = dur - 0.25
    head = K.headline(f("s7_head"), "В конце ролика", "Пара коротких вопросов", ["вопросов"], size=60, w=PW,
                      bg=False)
    y2 = 40 + h_of(head) + 20
    return [
        item(head, PX, 40, max(T("конце"), M.MOVE_D), end),
        item(K.icon_row(f("s7_opinion"), img("s12_ic_opinion"), "Ваше мнение ценно: учтём его в следующих материалах",
                        w=880, h=130, text_size=34, outline=S.GREEN), PX, y2, T("Ваше"), end),
    ]


# границы сцен в дорожке v2 (BOUNDS='[...]' в окружении — переопределить)
BOUNDS = json.loads(os.environ.get("BOUNDS", "null") or "null") or [0, 7.88, 22.83, 41.13, 60.69, 74.58, 96.35, 106.34]
KINDS = [("full", "none", scene1), ("corner", "shrink", scene2), ("corner", "none", scene3),
         ("full", "grow", scene4), ("corner", "shrink", scene5), ("full", "grow", scene6),
         ("corner", "shrink", scene7)]
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
        out = f"{TMP}/s12_scene{n}.mp4"
        parts.append(out)
        if only and n not in only:
            continue
        clip = f"{ROOT}/scratch/s12-scene{n}.mp4"
        if not os.path.exists(clip):          # пока нет клипа HeyGen — черновик на подставном
            clip = os.environ.get("DRAFT_CLIP", f"{ROOT}/scratch/s11-scene1.mp4")
        items = content(M.finder(words), dur)
        M.render_scene(clip, dur, words, mode, enter, items, out, TMP)
        print(f"scene {n} ok", flush=True)
    if not only:
        M.concat(parts, AUDIO, OUT, TMP)
        print(OUT)


if __name__ == "__main__":
    main()
