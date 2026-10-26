"""Instagram Reels №4 «Что в паре электронки» — 9:16, серия `iiavatar.video`.

Сценарий — docs/scenarios/insta-4-vape.md: механика чужого залетевшего ролика (эксперт
по здоровью, спорный факт, призыв в комментарии), текст свой и проверенный:
крючок «вещество для бальзамирования — в электронке» → глицерин и пропиленгликоль →
при перегреве — формальдегид → «на высокой мощности больше, чем в сигарете» →
металлы Ni/Cr/Pb → признак — вкус гари → «знал / не знал» в комментарии →
реклама ИИАВАТАР только в конце (слово «КЛИНИКА»).

Стиль «Клиника» (render/landing/theme_clinic.py, борд scratch/img/ig4_board.png):
тёмно-синий, коньячный, коралловый для опасности. Ведущая — фото реального человека
с её согласия, бейдж и логотип убраны (scratch/img/ig4_host.jpg → HeyGen photo avatar
af4891d0bd863afeba4ddc6cf565ec4b, avatar_iv, expressiveness high). Голос «Главный голос
(эталон) — Фарма» `OKAjhIhKwJ4TWXDzbaXU` (eleven_v3). Текст и графика — в безопасной
зоне Instagram 250–1500 px.

Запуск:  python3 -m render.landing.build_ig4   (CHECK=1 — только проверка раскладки)
Выход:   render/landing/ig4-9x16.mp4
"""
from PIL import Image

from render.landing import build_ig1 as B
from render.landing import theme_clinic as T

ROOT = B.ROOT
IMG = f"{ROOT}/scratch/img"
B.T = T
B.AUDIO = f"{ROOT}/scratch/ig4-full-trim.mp3"
B.WHISPER = f"{ROOT}/scratch/ig4-full-etalon-whisper-1.json"
B.CLIP = f"{ROOT}/scratch/ig4-host.mp4"
B.MUSIC = f"{ROOT}/scratch/ig1-music.mp3"
B.TEXTS = f"{ROOT}/docs/scenarios/insta-4-vape.md"
B.TMP = f"{B.HERE}/_frames_ig4"
B.OUT = f"{B.HERE}/ig4-9x16.mp4"

# Сцены: крючок · состав · перегрев · сравнение · металлы · признак · комментарии · реклама
B.BOUNDS = [0.0, 6.45, 12.0, 18.85, 27.75, 35.0, 41.3, 47.15]
# Голова ведущей в кадре клипа 1080×1920 (волосы, лицо, шея) — по фото.
B.HEAD = (230, 230, 830, 700)
B.FACE = (503, 430)
B.SHOW = {}
B.LAYOUT = {
    "full": {"kind": "scale", "s": 1.0, "y": 390, "mask": dict(top=200)},
    "panel": {"kind": "scale", "s": 0.7, "y": 755, "mask": dict(top=200, side=160)},
    "circle": {"kind": "circle", "size": 400, "x": 340, "y": 260, "r": 330},
}
P = B.p


def chip_row(items, gap=24, size=58):
    """Метки в одну строку по центру кадра: [(png, x, слово-триггер)]."""
    pngs = [(T.tag(P(f"chip_{t}"), t, size), w) for t, w in items]
    ws = [Image.open(p_).width for p_, _ in pngs]
    x = (B.W - sum(ws) - gap * (len(ws) - 1)) / 2
    out = []
    for (p_, w), wd in zip(pngs, ws):
        out.append((p_, int(x), w))
        x += wd + gap
    return out


def scenes(F):
    b = B.BOUNDS
    T.background(P("bg"), B.W, B.H, "plain")
    T.background(P("bg_grid"), B.W, B.H, "grid")
    L = B.LAYOUT
    r1, r2, r3 = (T.reaction_card(P(f"react{i}"), i) for i in (1, 2, 3))
    coil = T.photo_card(P("coil"), f"{IMG}/ig4_coil.png", w=980, h=330)
    coil_cap = T.photo_card(P("coil_cap"), f"{IMG}/ig4_coil.png", w=980, h=330, caption="как в формалине")
    lab = T.photo_card(P("lab"), f"{IMG}/ig4_lab.png", w=980, h=500)
    lab_cap = T.photo_card(P("lab_cap"), f"{IMG}/ig4_lab.png", w=980, h=500, caption="нашли в исследованиях")
    return [
        # 1. Крючок: «ЧТО В ПАРЕ ЭЛЕКТРОНКИ»
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(0.0, 1.12), (F("Не"), 1.0), (F("Смотрите"), 1.15)]),
         "flash": [(0.02, "white")], "shake": [0.02, F("Смотрите")],
         "sfx": [(0.0, "bass", 0.6), (F("Смотрите"), "hit", 0.4)],
         "els": [
             (T.headline(P("s1_h"), [[("Что в паре", "w")], [("электронки", "o")]], 1000, size=118), 40, 170, 0.02),
         ]},
        # 2. Состав: глицерин + пропиленгликоль — «сами по себе не страшные»
        {"bg": P("bg_grid"), "av": dict(L["panel"], cuts=[(F("Сами"), 1.08)]), "els": [
            (r1, 20, 222, F("глицерин"), b[2], "pop", True),
        ], "sfx": [(F("глицерин"), "pop", 0.3)]},
        # 3. Перегрев → формальдегид (без ведущей), спираль крупно
        {"bg": P("bg_grid"), "av": None, "els": [
            (r1, 20, 222, b[2], F("перегревается"), "state", True),
            (r2, 20, 222, F("перегревается"), F("формальдегид"), "state", True),
            (r3, 20, 222, F("формальдегид"), None, "state"),
            (coil, 20, 840, F("спираль"), F("формалина"), "pop", True),
            (coil_cap, 20, 840, F("формалина"), None, "state"),
        ], "flash": [(F("формальдегид"), "orange")], "shake": [F("формальдегид")],
            "sfx": [(F("перегревается"), "riser", 0.3), (F("формальдегид"), "hit", 0.5)]},
        # 4. Сравнение с сигаретой → «как понять? — в конце»
        {"bg": P("bg_grid"), "av": dict(L["panel"], cuts=[(F("больше"), 1.08), (F("Как"), 1.0)]), "els": [
            (T.compare_card(P("cmp1"), 1), 20, 240, F("Учёные"), F("больше"), "pop", True),
            (T.compare_card(P("cmp2"), 2), 20, 240, F("больше"), F("Как"), "state"),
            (T.headline(P("s4_h"), [[("Как понять?", "o")], [("— в конце", "w")]], 1000, size=104), 40, 280,
             F("Как")),
        ], "sfx": [(F("больше"), "ding", 0.4), (F("конце"), "riser", 0.35)]},
        # 5. Металлы: лаборатория + плитки Ni / Cr / Pb (без ведущей)
        {"bg": P("bg_grid"), "av": None, "els": [
            (lab, 20, 230, b[4] + 0.05, F("находили"), "pop", True),
            (lab_cap, 20, 230, F("находили"), None, "state"),
            (T.element_tiles(P("tile1"), 1), 50, 830, F("Никель"), F("хром"), "pop", True),
            (T.element_tiles(P("tile2"), 2), 50, 830, F("хром"), F("свинец"), "state", True),
            (T.element_tiles(P("tile3"), 3), 50, 830, F("свинец"), None, "state"),
        ], "sfx": [(F("Никель"), "click", 0.4), (F("хром"), "click", 0.4), (F("свинец"), "click", 0.4)]},
        # 6. Признак перегрева — вкус гари
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(F("гари"), 1.15), (F("Значит"), 1.05)]), "els": [
            (T.headline(P("s6_h1"), [[("Как понять,", "w")], [("что перегрелась?", "w")]], 1000, size=96), 40, 260,
             b[5] + 0.05, F("гари"), "pop", True),
            (T.headline(P("s6_h2"), [[("Вкус гари", "o")], [("= перегрев", "w")]], 1000, size=110), 40, 250,
             F("гари"), None, "state"),
        ], "flash": [(F("гари"), "orange")], "shake": [F("гари")], "sfx": [(F("гари"), "stamp", 0.5)]},
        # 7. Комментарии: «ЗНАЛИ? знал / не знал» → «отправьте тому, кто парит»
        {"bg": P("bg_grid"), "av": dict(L["panel"], cuts=[(F("отправьте"), 1.08)]), "els": [
            (T.comment_card(P("cmt")), 20, 240, b[6] + 0.05, F("отправьте"), "pop", True),
            (T.headline(P("s7_h"), [[("Отправьте тому,", "w")], [("кто", "w"), ("парит", "o")]], 1000, size=104),
             40, 300, F("отправьте")),
        ], "sfx": [(F("знал"), "pop", 0.3)]},
        # 8. Реклама в конце: ведущая в круге, «лицо · голос · монтаж» → «КЛИНИКА» в директ
        {"bg": P("bg_grid"), "av": L["circle"], "glitch": [(F("нейросети"), 0.5)], "els": [
            (T.ring(P("s8_ring"), 400), 340 - 44, 260 - 44, b[7] + 0.02, None, "frame"),
            (T.headline(P("s8_h0"), [[("Меня собрали", "w")], [("нейросети", "o")]], 1000, size=96), 40, 730,
             F("нейросети"), F("Сделаем")),
            *[(png, x, 1010, F(w), F("Сделаем")) for png, x, w in chip_row(
                [("Лицо", "Лицо"), ("Голос", "голос"), ("Монтаж", "монтаж")])],
            (T.headline(P("s8_h"), [[("Такого ведущего", "w")], [("сделаем", "w"), ("вам", "box")]], 1000,
                        size=84), 40, 730, F("Сделаем"), F("Пишите")),
            *[(png, x, 1010, F(w), F("Пишите")) for png, x, w in chip_row(
                [("Клиника", "клиники"), ("Блог", "блога"), ("Обучение", "обучения")])],
            (T.cta_card(P("s8_cta"), 1000, "КЛИНИКА"), 40, 700, F("Пишите")),
        ], "sfx": [(F("нейросети"), "glitch", 0.35)]},
    ]


B.scenes = scenes

if __name__ == "__main__":
    B.main()
