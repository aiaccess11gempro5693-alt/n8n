"""Instagram Reels №3 «Лифт и зеркала» — 9:16, серия `iiavatar.video`.

Сценарий — docs/scenarios/insta-3-elevator.md: известная история про небоскрёб,
где жильцы ненавидели медленные лифты → дорогой ремонт против решения «за один день»
→ «как — скажу в конце» → реклама в середине → развязка: зеркала у лифтов →
мораль «не быстрее, а интереснее ждать» → «отправьте тому, кто решает всё деньгами».

Стиль «Табло лифта» (render/landing/theme_led.py, борд scratch/img/ig3_board_led.png),
ведущая с борда (scratch/img/ig3_host.png → HeyGen photo avatar
3241144eb6a1066821b3523d9dbd4ca7, avatar_iv, expressiveness high), голос Ana
(eleven_v3, scratch/ig3-full-b-trim.mp3). Картинки истории — gpt-image-2
(docs/scenarios/insta-3/images.json). Текст и графика — только в безопасной зоне
Instagram 250–1500 px (docs/landing/video-rules.md, раздел 7, п.7).

Движок сцен — общий с build_ig1.py; здесь — только свои данные.

Запуск:  python3 -m render.landing.build_ig3   (CHECK=1 — только проверка раскладки)
Выход:   render/landing/ig3-9x16.mp4
"""
from render.landing import build_ig1 as B
from render.landing import theme_led as T

ROOT = B.ROOT
IMG = f"{ROOT}/scratch/img"
B.T = T
B.AUDIO = f"{ROOT}/scratch/ig3-full-b-trim.mp3"
B.WHISPER = f"{ROOT}/scratch/ig3-full-b-whisper-1.json"
B.CLIP = f"{ROOT}/scratch/ig3-host.mp4"
B.MUSIC = f"{ROOT}/scratch/ig1-music.mp3"
B.TEXTS = f"{ROOT}/docs/scenarios/insta-3-elevator.md"
B.TMP = f"{B.HERE}/_frames_ig3"
B.OUT = f"{B.HERE}/ig3-9x16.mp4"

# Сцены: крючок · толпа · инженеры · «за 1 день» · реклама · решение · зеркала · мораль · финал
B.BOUNDS = [0.0, 2.35, 7.85, 12.95, 19.75, 32.75, 39.35, 48.55, 54.3]
# Голова ведущей в кадре клипа 1080×1920 (волосы, лицо, шея) — по кадру клипа.
B.HEAD = (360, 200, 710, 720)
B.FACE = (540, 500)
B.SHOW = {}
B.LAYOUT = {
    "full": {"kind": "scale", "s": 1.0, "y": 460, "mask": dict(top=200)},
    "panel": {"kind": "scale", "s": 0.7, "y": 740, "mask": dict(top=200, side=160)},
    "circle": {"kind": "circle", "size": 400, "x": 340, "y": 260, "r": 330},
}
P = B.p


def chip_row(items, y_gap=24, size=58):
    """Метки в одну строку по центру кадра: [(png, x, слово-триггер)]."""
    from PIL import Image
    pngs = [(T.tag(P(f"chip_{i}"), t, size), w) for i, (t, w) in enumerate(items)]
    ws = [Image.open(p_).width for p_, _ in pngs]
    x = (B.W - sum(ws) - y_gap * (len(ws) - 1)) / 2
    out = []
    for (p_, w), wd in zip(pngs, ws):
        out.append((p_, int(x), w))
        x += wd + y_gap
    return out


def scenes(F):
    b = B.BOUNDS
    T.background(P("bg"), B.W, B.H, "plain")
    T.background(P("bg_grid"), B.W, B.H, "grid")
    L = B.LAYOUT
    crowd = T.photo_card(P("crowd"), f"{IMG}/ig3_crowd.png", w=980, h=500)
    crowd_cap = T.photo_card(P("crowd_cap"), f"{IMG}/ig3_crowd.png", w=980, h=500, caption="грозились съехать")
    eng = T.photo_card(P("eng"), f"{IMG}/ig3_engineers.png", w=980, h=620)
    mir_big = T.photo_card(P("mir_big"), f"{IMG}/ig3_mirrors.png", w=980, h=980, caption="Зеркала")
    mir = T.photo_card(P("mir"), f"{IMG}/ig3_mirrors.png", w=980, h=500)
    return [
        # 1. Крючок: ведущая на весь кадр, «ЛИФТ, КОТОРЫЙ ВСЕ НЕНАВИДЕЛИ»
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(0.0, 1.15)]),
         "flash": [(0.02, "white")], "shake": [0.02], "sfx": [(0.0, "bass", 0.6), (0.05, "ding", 0.35)],
         "els": [
             (T.headline(P("s1_h"), [[("Лифт, который", "w")], [("все", "w"), ("ненавидели", "o")]], 1000,
                         size=104), 40, 250, 0.02),
         ]},
        # 2. Толпа у лифтов: «грозились съехать»
        {"bg": P("bg_grid"), "av": dict(L["panel"], cuts=[(F("грозились"), 1.08)]), "els": [
            (crowd, 20, 230, b[1] + 0.05, F("грозились"), "pop", True),
            (crowd_cap, 20, 230, F("грозились"), None, "state"),
        ], "sfx": [(F("грозились"), "hit", 0.3)]},
        # 3. Инженеры: «Ускорить лифты: МИЛЛИОНЫ · 1 ГОД» — без ведущей
        {"bg": P("bg_grid"), "av": None, "els": [
            (eng, 20, 250, b[2] + 0.05),
            (T.led_panel(P("s3_led"), "Ускорить лифты:", "Миллионы · 1 год"), 20, 930, F("миллионы")),
        ], "sfx": [(F("миллионы"), "tick", 0.35)]},
        # 4. «Решили за 1 день» → «Как? — в конце»
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(F("решили"), 1.1), (F("Как"), 1.0)]), "els": [
            (T.stamp(P("s4_st"), ["Решили", "за 1 день"]), 230, 250, F("решили"), F("Как"), "pop"),
            (T.headline(P("s4_h"), [[("Как?", "o"), ("— в конце", "w")]], 1000, size=110), 40, 270, F("Как")),
        ], "flash": [(F("решили"), "orange")], "shake": [F("решили")],
            "sfx": [(F("решили"), "stamp", 0.6), (F("конце"), "riser", 0.35)]},
        # 5. Реклама: ведущая в круге, «такого ведущего сделаем вам» → «ЛИФТ» в директ
        {"bg": P("bg_grid"), "av": L["circle"], "glitch": [(F("нейросети"), 0.5)], "els": [
            (T.ring(P("s5_ring"), 400), 340 - 44, 260 - 44, b[4] + 0.02, None, "frame"),
            (T.headline(P("s5_h"), [[("Такого ведущего", "w")], [("сделаем", "w"), ("вам", "box")]], 1000,
                        size=84), 40, 700, F("Такого"), F("Пишите")),
            *[(png, x, 980, F(w), F("Пишите")) for png, x, w in chip_row(
                [("Обучение", "обучения"), ("Реклама", "рекламы"), ("Блог", "блога")])],
            (T.cta_card(P("s5_cta"), 1000, "ЛИФТ"), 40, 720, F("Пишите")),
        ], "sfx": [(F("нейросети"), "glitch", 0.35)]},
        # 6. Развязка: «Итак… решение» → ЗЕРКАЛА (без ведущей)
        {"bg": P("bg_grid"), "av": None, "els": [
            (T.floor_display(P("s6_fl"), "РЕШЕНИЕ", arrow="down", size=18, pitch=9), 45, 620, b[5] + 0.05,
             F("зеркала"), "pop"),
            (mir_big, 20, 280, F("зеркала")),
        ], "flash": [(F("зеркала"), "white")], "shake": [F("зеркала")],
            "sfx": [(F("Итак"), "tick", 0.3), (F("зеркала"), "ding", 0.6)]},
        # 7. Люди смотрят в зеркала → «жалобы: почти нет»
        {"bg": P("bg_grid"), "av": dict(L["panel"], cuts=[(F("Жалобы"), 1.08)]), "els": [
            (mir, 20, 250, b[6] + 0.05, F("Жалобы"), "pop"),
            (T.led_panel(P("s7_led"), "Жалобы:", "почти нет"), 20, 330, F("Жалобы")),
        ], "sfx": [(F("Жалобы"), "pop", 0.35)]},
        # 8. Мораль
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(F("Изменилось"), 1.12)]), "els": [
            (T.headline(P("s8_h"), [[("Не быстрее —", "w")], [("интереснее", "o"), ("ждать", "w")]], 1000,
                        size=104), 40, 250, b[7] + 0.05),
        ]},
        # 9. Финал: «отправьте тому, кто решает всё деньгами»
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(b[8], 1.15)]), "els": [
            (T.headline(P("s9_h"), [[("Отправьте тому,", "w")], [("кто решает", "w"), ("деньгами", "box")]],
                        1000, size=92), 40, 250, b[8] + 0.05),
        ]},
    ]


B.scenes = scenes

if __name__ == "__main__":
    B.main()
