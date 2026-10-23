"""Instagram Reels №2 «Вы забудете это видео» — 9:16, серия `iiavatar.video`.

Сценарий — docs/scenarios/insta-2-forgetting.md: крючок → история Эббингауза →
интрига «приём в конце» → реклама в середине (такого ведущего сделаем и вам) →
развязка-проверка зрителя («как звали учёного?») → кривая подскакивает на
каждом вспоминании → «отправьте тому, кто учится».

Стиль «Светлый журнальный» (render/landing/theme_light.py, борд
scratch/img/ig2_board_light.png), ведущий-мужчина (scratch/img/ig2_host.png →
HeyGen photo avatar ef27c1f2674f9cc6c3e105356556f378, avatar_iv, expressiveness
high), голос Artem (eleven_v3, scratch/ig2-full-b-trim.mp3).

Движок сцен — общий с build_ig1.py (склейки-наезды, тряска, глитч, полоса
прогресса, проверка «ничего не наезжает»); здесь — только свои данные.

Запуск:  python3 -m render.landing.build_ig2   (CHECK=1 — только проверка раскладки)
Выход:   render/landing/ig2-9x16.mp4
"""
from render.landing import build_ig1 as B
from render.landing import theme_light as T

ROOT = B.ROOT
B.T = T
B.AUDIO = f"{ROOT}/scratch/ig2-full-b-trim.mp3"
B.WHISPER = f"{ROOT}/scratch/ig2-full-b-whisper-1.json"
B.CLIP = f"{ROOT}/scratch/ig2-host.mp4"
B.MUSIC = f"{ROOT}/scratch/ig1-music.mp3"
B.TEXTS = f"{ROOT}/docs/scenarios/insta-2-forgetting.md"
B.TMP = f"{B.HERE}/_frames_ig2"
B.OUT = f"{B.HERE}/ig2-9x16.mp4"

# Сцены: крючок · Эббингауз · интрига · реклама · проверка · развязка
B.BOUNDS = [0.0, 5.95, 13.70, 23.10, 33.55, 45.70]
# Голова ведущего в кадре клипа 1080×1920 (волосы, лицо, шея) — по кадру клипа.
B.HEAD = (330, 70, 750, 640)
B.FACE = (540, 380)
B.SHOW = {"девятнадцатом": "XIX", "19": "XIX"}
B.LAYOUT = {
    "full": {"kind": "scale", "s": 1.0, "y": 370, "mask": dict(top=240)},
    "panel": {"kind": "scale", "s": 0.72, "y": 860, "mask": dict(top=260, side=170)},
    "circle": {"kind": "circle", "size": 480, "x": 300, "y": 120, "r": 330},
}
P = B.p


def scenes(F):
    b = B.BOUNDS
    T.background(P("bg"), B.W, B.H, "plain")
    T.background(P("bg_grid"), B.W, B.H, "grid")
    L = B.LAYOUT
    return [
        # 1. Крючок: ведущий на весь кадр, «ВЫ ЗАБУДЕТЕ ЭТО ВИДЕО» + «через час»
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(0.0, 1.2), (F("И"), 1.0), (F("мозг"), 1.12)]),
         "flash": [(0.02, "white")], "shake": [0.02], "sfx": [(0.0, "bass", 0.6)],
         "els": [
             (T.headline(P("s1_h"), [[("Вы забудете", "w")], [("это видео", "box")]], 1000, size=104), 40, -20, 0.02),
         ]},
        # 2. Эббингауз: кривая падает, «−50 % за сутки»
        {"bg": P("bg_grid"), "av": dict(L["panel"], cuts=[(F("Уже"), 1.08)]), "els": [
            (T.tag(P("s2_tag"), "Герман Эббингауз · XIX век", 44), 40, 20, b[1] + 0.05),
            (T.chart(P("s2_c0"), "forget", 0, h=650), 20, 150, b[1] + 0.2, F("сутки"), "pop", True),
            (T.chart(P("s2_c1"), "forget", 1, h=650), 20, 150, F("сутки"), None, "state"),
        ], "sfx": [(F("сутки"), "ding", 0.4)]},
        # 3. Почему не работает + интрига «приём — в конце»
        {"bg": P("bg"), "av": dict(L["full"], cuts=[(F("Поэтому"), 1.0), (F("Но", b[2] + 2), 1.15)]), "els": [
            (T.headline(P("s3_h1"), [[("1 лекция", "w")], [("≠ знание", "box")]], 1000, size=104), 40, -20,
             b[2] + 0.05, F("Но", b[2] + 2), "pop", True),
            (T.headline(P("s3_h2"), [[("Приём —", "w")], [("в конце", "box")]], 1000, size=104), 40, -20,
             F("Но", b[2] + 2), None, "state"),
        ], "sfx": [(F("конце"), "riser", 0.35)]},
        # 4. Реклама в середине: такого ведущего — вам
        {"bg": P("bg_grid"), "av": L["circle"], "els": [
            (T.ring(P("s4_ring"), 480), 300 - 44, 120 - 44, b[3] + 0.02, None, "frame"),
            (T.headline(P("s4_h"), [[("Такого ведущего", "w")], [("сделаем вам", "box")]], 1000, size=92), 40, 640,
             F("Такого")),
            (T.cross_chip(P("s4_c1"), "Обучение", crossed=False, w=460), 50, 990, F("обучения")),
            (T.cross_chip(P("s4_c2"), "Блог", crossed=False, w=460), 570, 990, F("блога")),
            (T.cross_chip(P("s4_c3"), "Любые задачи", crossed=False, w=980), 50, 1190, F("любой")),
        ], "sfx": [(F("нейросети"), "glitch", 0.35)]},
        # 5. Проверка зрителя: вопрос → 3·2·1 → «ЭББИНГАУЗ ✓»
        {"bg": P("bg"), "av": dict(L["panel"], cuts=[(F("Как"), 1.08), (F("Эббингауз", 35), 1.0)]), "els": [
            (T.tag(P("s5_tag"), "Проверка", 56), 380, 40, b[4] + 0.05, F("Как"), "pop", True),
            (T.question_card(P("s5_q"), "Проверка", ["Как звали учёного", "из начала видео?"]), 20, 30, F("Как"),
             F("Эббингауз", 35), "pop", True),
            (T.countdown(P("s5_n3"), 3, 260), 410, 470, F("видео", F("Как")) + 0.35, F("видео", F("Как")) + 0.75,
             "state"),
            (T.countdown(P("s5_n2"), 2, 260), 410, 470, F("видео", F("Как")) + 0.75, F("видео", F("Как")) + 1.15,
             "state"),
            (T.countdown(P("s5_n1"), 1, 260), 410, 470, F("видео", F("Как")) + 1.15, F("Эббингауз", 35), "state"),
            (T.answer_card(P("s5_a"), "Эббингауз"), 20, 60, F("Эббингауз", 35)),
            (T.tag(P("s5_ok"), "вы только что применили приём", 44), 150, 300, F("Значит")),
        ], "flash": [(F("Эббингауз", 35), "white")], "sfx": [(F("Эббингауз", 35), "ding", 0.6)]},
        # 6. Развязка: кривая подскакивает на каждом вспоминании → «отправьте»
        {"bg": P("bg_grid"), "av": dict(L["panel"], cuts=[(F("Вспомните"), 1.08), (F("Отправьте"), 1.0)]),
         "els": [
             (T.chart(P("s6_c0"), "repeat", 0), 20, 40, b[5] + 0.05, F("Вспомните"), "pop", True),
             (T.chart(P("s6_c1"), "repeat", 1), 20, 40, F("Вспомните"), F("завтра"), "state"),
             (T.chart(P("s6_c2"), "repeat", 2), 20, 40, F("завтра"), F("неделю"), "state"),
             (T.chart(P("s6_c3"), "repeat", 3), 20, 40, F("неделю"), F("Отправьте"), "state"),
             (T.headline(P("s6_h"), [[("Отправьте тому,", "w")], [("кто учится", "box")]], 1000, size=96), 40, 120,
              F("Отправьте")),
         ], "sfx": [(F("Вспомните"), "click", 0.4), (F("завтра"), "click", 0.4), (F("неделю"), "click", 0.4)]},
    ]


B.scenes = scenes

if __name__ == "__main__":
    B.main()
