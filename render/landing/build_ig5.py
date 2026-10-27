"""Instagram Reels №5 «Почему вы не можете бросить сериал» (эффект Зейгарник) — 9:16,
серия `iiavatar.video`.

Сценарий — docs/scenarios/insta-5-zeigarnik.md: бытовой крючок → кафе и официант,
который забывает оплаченные заказы → лаборатория «незаконченное помнят почти ×2» →
открытая петля → «поэтому вы досмотрели до этого места» → совет «первые 5 минут» →
раскрытие «меня не существует» и реклама только в конце (слово «ПЕТЛЯ»).

Стиль «Блокнот» (render/landing/theme_notepad.py, борд scratch/img/ig5_board_notepad.png):
бумага в клетку, графит, красный карандаш, жёлтый маркер, скетчи gpt-image-2.
Ведущая — gpt-image-2 по борду (scratch/img/ig5_host.png → HeyGen photo avatar
1e59fc3686da963d355f0d768f66406a, avatar_iv, expressiveness high). Голос Olga Narrator
`IfP8A5cbeh6QoSUPogHR` (eleven_v3). Текст и графика — в безопасной зоне 250–1500 px.

Запуск:  python3 -m render.landing.build_ig5   (CHECK=1 — только проверка раскладки)
Выход:   render/landing/ig5-9x16.mp4
"""
from PIL import Image

from render.landing import build_ig1 as B
from render.landing import theme_notepad as T

ROOT = B.ROOT
IMG = f"{ROOT}/scratch/img"
B.T = T
B.AUDIO = f"{ROOT}/scratch/ig5-full-trim.mp3"
B.WHISPER = f"{ROOT}/scratch/ig5-vc-olga.json"
B.CLIP = f"{ROOT}/scratch/ig5-host.mp4"
B.MUSIC = f"{ROOT}/scratch/ig1-music.mp3"
B.TEXTS = f"{ROOT}/docs/scenarios/insta-5-zeigarnik.md"
B.TMP = f"{B.HERE}/_frames_ig5"
B.OUT = f"{B.HERE}/ig5-9x16.mp4"

# Сцены: крючок · кафе-интрига · Зейгарник · официант · лаборатория · петля · попались ·
# совет · раскрытие · реклама
B.BOUNDS = [0.0, 3.70, 8.90, 12.90, 19.95, 26.45, 34.15, 38.65, 46.05, 50.95]
# Голова ведущей в кадре клипа 1080×1920 (волосы с хвостом, лицо, шея) — по фото.
B.HEAD = (350, 190, 860, 750)
B.FACE = (524, 510)
B.SHOW = {"пять": "5"}
B.LAYOUT = {
    "full": {"kind": "scale", "s": 1.0, "y": 300, "mask": dict(top=200)},
    "panel": {"kind": "scale", "s": 0.7, "y": 760, "mask": dict(top=320, side=340)},
    "circle": {"kind": "circle", "size": 400, "x": 340, "y": 270, "r": 330},
}
P = B.p


def chip_row(items, y, gap=24, size=50):
    """Метки на маркере в одну строку по центру: [(текст, слово-триггер)]."""
    pngs = [(T.tag(P(f"chip_{t}"), t, size), w) for t, w in items]
    ws = [Image.open(p_).width for p_, _ in pngs]
    x = (B.W - sum(ws) - gap * (len(ws) - 1)) / 2
    out = []
    for (p_, w), wd in zip(pngs, ws):
        out.append((p_, int(x), y, w))
        x += wd + gap
    return out


def scenes(F):
    b = B.BOUNDS
    T.background(P("bg"), B.W, B.H, "plain")
    T.background(P("bg_grid"), B.W, B.H, "grid")
    L = B.LAYOUT
    tv = T.photo_card(P("tv"), f"{IMG}/ig5_tv.png", w=860, h=560, caption="серия оборвалась")
    cafe = T.photo_card(P("cafe"), f"{IMG}/ig5_cafe.png", w=860, h=620, angle=-1.5)
    lab = T.photo_card(P("lab"), f"{IMG}/ig5_lab.png", w=860, h=620)
    pads = [T.order_pad(P(f"pad{i}"), i) for i in range(3)]
    bars = [T.bars_card(P(f"bars{i}"), i) for i in range(2)]
    loop_open = T.loop_icon(P("loop_open"), False, size=360, label="открытая петля")
    loop_small = T.loop_icon(P("loop_small"), False, size=220)
    loop_done = T.loop_icon(P("loop_done"), True, size=220)
    return [
        # 1. Крючок: ведущая ниже, сверху «ПОЧЕМУ ВЫ НЕ МОЖЕТЕ БРОСИТЬ СЕРИАЛ?»
        {"bg": P("bg"), "av": dict(L["panel"], cuts=[(F("сериал"), 1.08)]),
         "flash": [(0.02, "white")], "shake": [0.02],
         "sfx": [(0.0, "bass", 0.5), (F("сериал"), "pop", 0.35)],
         "els": [
             (T.headline(P("s1_h"), [[("Почему вы не", "w")], [("можете бросить", "w")],
                                     [("сериал?", "box")]], 1000, size=80), 40, 270, 0.02),
         ]},
        # 2. «Это не слабая воля» → «открыли… в кафе» (без ведущей)
        {"bg": P("bg_grid"), "av": None, "els": [
            (tv, 60, 260, b[1] + 0.02),
            (T.headline(P("s2_h1"), [[("Не", "w"), ("слабая воля", "s")]], 1000, size=72), 40, 960,
             F("слабая"), F("эффект"), "pop"),
            (T.headline(P("s2_h2"), [[("Открыли… в", "w"), ("кафе", "c")]], 1000, size=72), 40, 960,
             F("кафе")),
        ], "sfx": [(F("слабая"), "pop", 0.3), (F("кафе"), "ding", 0.4)]},
        # 3. Блюма Зейгарник: ведущая в круге, имя и «почти 100 лет назад»
        {"bg": P("bg_grid"), "av": L["circle"], "els": [
            (T.ring(P("s3_ring"), 400), 340 - 18, 270 - 18, b[2] + 0.02, None, "frame"),
            (T.headline(P("s3_h"), [[("Блюма", "w")], [("Зейгарник", "box")]], 1000, size=88), 40, 720,
             F("психолог")),
            (T.note(P("s3_n"), "почти 100 лет назад", size=76, angle=-3), 230, 1020, F("Почти")),
        ], "sfx": [(F("Зейгарник"), "click", 0.4)]},
        # 4. Официант: скетч кафе → блокнот заказов (оплаченные зачёркнуты → исчезли)
        {"bg": P("bg_grid"), "av": None, "els": [
            (cafe, 60, 260, b[3] + 0.02, F("пока"), "pop"),
            (pads[0], 120, 280, F("пока"), F("оплатили"), "pop", True),
            (pads[1], 120, 280, F("оплатили"), F("забывает"), "state", True),
            (pads[2], 120, 280, F("забывает"), None, "state"),
            (T.note(P("s4_n"), "оплачено = забыто", size=80, angle=-3), 250, 1060, F("забывает")),
        ], "sfx": [(F("оплатили"), "click", 0.4), (F("забывает"), "pop", 0.35)]},
        # 5. Лаборатория → «что помнят»: законченные vs незаконченные ×2
        {"bg": P("bg_grid"), "av": None, "els": [
            (lab, 60, 260, b[4] + 0.02, F("Незаконченные"), "pop"),
            (bars[0], 20, 300, F("Незаконченные"), F("два"), "pop", True),
            (bars[1], 20, 300, F("два"), None, "state"),
        ], "flash": [(F("два"), "orange")], "shake": [F("два")],
            "sfx": [(F("Незаконченные"), "pop", 0.3), (F("два"), "stamp", 0.5)]},
        # 6. Открытая петля → серия обрывается на самом интересном
        {"bg": P("bg"), "av": dict(L["panel"], cuts=[(F("Поэтому"), 1.06)]), "els": [
            (loop_open, 270, 260, b[5] + 0.05, F("Поэтому"), "pop"),
            (T.player(P("s6_pl"), 1, w=880, h=420), 70, 260, F("Поэтому")),
        ], "sfx": [(F("петлю"), "riser", 0.3), (F("Поэтому"), "hit", 0.4)]},
        # 7. «Вы досмотрели до этого места» — ведущая на весь кадр
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(F("досмотрели"), 1.12)]), "els": [
            (T.headline(P("s7_h"), [[("Вы", "w"), ("досмотрели", "box")]], 1000, size=76), 40, 260,
             F("досмотрели")),
        ], "flash": [(F("досмотрели"), "orange")], "shake": [F("досмотрели")],
            "sfx": [(F("досмотрели"), "stamp", 0.5)]},
        # 8. Совет: первые 5 минут
        {"bg": P("bg_grid"), "av": dict(L["panel"], y=820), "els": [
            (T.headline(P("s8_h"), [[("Сложное", "w"), ("дело?", "c")]], 1000, size=80), 40, 300,
             b[7] + 0.05, F("Сделайте")),
            (T.timer_card(P("s8_t"), w=760), 140, 260, F("Сделайте")),
        ], "sfx": [(F("Сделайте"), "tick", 0.4)]},
        # 9. Раскрытие: «ещё одна открытая петля: меня не существует» — глитч
        {"bg": P("bg"), "av": dict(L["full"], y=380, cuts=[(F("существует"), 1.05)]),
         "glitch": [(F("существует"), 0.5)], "els": [
             (T.headline(P("s9_h1"), [[("Ещё одна", "w")], [("открытая петля", "o")]], 1000, size=68), 40, 260,
              b[8] + 0.05, F("Меня"), "pop"),
             (T.headline(P("s9_h2"), [[("Меня не", "w")], [("существует", "box")]], 1000, size=76), 40, 260,
              F("Меня")),
         ], "sfx": [(F("существует"), "glitch", 0.4)]},
        # 10. Реклама: круг, «я нейросеть · из текста · за 1 день» → «ПЕТЛЯ» в директ, петля замыкается
        {"bg": P("bg_grid"), "av": L["circle"], "els": [
            (T.ring(P("s10_ring"), 400), 340 - 18, 270 - 18, b[9] + 0.02, None, "frame"),
            (loop_small, 30, 300, b[9] + 0.02, F("петля", F("Напишите")), "pop", True),
            (loop_done, 30, 300, F("петля", F("Напишите")), None, "state"),
            (T.headline(P("s10_h0"), [[("Я", "w"), ("нейросеть", "box")]], 1000, size=80), 40, 720,
             b[9] + 0.05, F("Хотите", b[9])),
            *[(png, x, y, F(w, b[9]), F("Хотите", b[9])) for png, x, y, w in chip_row(
                [("Из текста", "текста"), ("За 1 день", "день")], 900)],
            (T.headline(P("s10_h1"), [[("Такого ведущего —", "w")], [("вашему", "w"), ("бизнесу", "box")]], 1000,
                        size=64), 40, 720, F("Хотите", b[9]), F("Напишите")),
            (T.cta_card(P("s10_cta"), 860, "ПЕТЛЯ", k=0.8), 90, 690, F("Напишите")),
        ], "sfx": [(F("нейросеть"), "glitch", 0.3), (F("петля", F("Напишите")), "ding", 0.45)]},
    ]


B.scenes = scenes

if __name__ == "__main__":
    B.main()
