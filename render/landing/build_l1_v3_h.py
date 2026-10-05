"""Лендинг, ролик 1 «Возврат товара» — горизонталь 16:9, виток 3.

Тот же стиль «Графит и красный», та же Анна (клип HeyGen 9:16 с прозрачным
фоном ставится в горизонтальный кадр) и голос Victoria, что у одобренной
вертикали (build_l1_v3.py), но СВОЙ расширенный текст и свои картинки
(кинокадры и иконки от gpt-image-2, docs/scenarios/landing-1/images-graphite-h.json).
Движок сцен — общий с вертикалью (render_scene из build_l1_v3).

Раскладка меняется от сцены к сцене (9 сцен, ни одна не повторяет соседнюю):
  1 кадр-фото у кассы без Анны            6 фото телефона + Анна в круге + «чек потерян?»
  2 Анна по центру, «проверка сервиса» / «скандал» зачёркнут
  3 Анна справа + плашка имени, слева оглавление 01–04
  4 Анна слева, справа «01 Разговор» + чек-лист
  5 фото бирки слева, справа «02 Осмотр», плитки-иконки, «14 дней», без Анны
  7 Анна справа, слева бланк заявления заполняется по словам
  8 фон-фото кассы, Анна по центру, по бокам «картой → на карту» / «наличными → из кассы»
  9 Анна по центру, слева цитата «Спасибо…», справа итог

Запуск:  python3 -m render.landing.build_l1_v3_h
Выход:   render/landing/l1-v3-16x9.mp4
"""
import os

from render.landing import build_l1_v3 as V
from render.landing import theme_graphite as T

ROOT, HERE = V.ROOT, V.HERE
IMG = f"{ROOT}/scratch/img"
W, H = 1920, 1080

V.W, V.H = W, H
V.TMP = f"{HERE}/_frames_v3h"
V.AUDIO = f"{ROOT}/scratch/l1-h3-full-v1.mp3"
V.WHISPER = f"{ROOT}/scratch/l1-h3-full-v1-whisper-1.json"
V.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/l1-h3-anna.webm")
V.OUT = f"{HERE}/l1-v3-16x9.mp4"
V.TEXT_HEAD, V.TEXT_END = "## Текст 16:9, виток 3", "## Раскладка 9:16"
V.CAP_W, V.CAP_X, V.CAP_BOTTOM = 1100, 410, 1050
# границы сцен — середины пауз между предложениями (silencedetect)
V.BOUNDS = [0.0, 5.86, 9.97, 13.89, 20.32, 26.99, 30.67, 37.35, 43.57]

p = V.p


def anna(x, s=0.62, y=0):
    return {"kind": "scale", "s": s, "x": x, "y": y}


def scenes(F):
    b = V.BOUNDS
    T.background(p("bg_plain"), W, H, "plain")
    T.background(p("bg_diag"), W, H, "diag")
    T.background(p("bg_split"), W, H, "split")
    T.photo_bg(p("bg_counter"), f"{IMG}/l1h_ph_counter.png", W, H, dark=0.35)
    T.photo_bg(p("bg_tag"), f"{IMG}/l1h_ph_tag.png", W, H, rect=(0, 0, 1100, H), dark=0.2, fade_side="right", ax=0.85)
    T.photo_bg(p("bg_phone"), f"{IMG}/l1h_ph_phone.png", W, H, rect=(0, 0, 1100, H), dark=0.2, fade_side="right")
    T.photo_bg(p("bg_refund"), f"{IMG}/l1h_ph_refund.png", W, H, dark=0.6)
    form = [("Паспорт", "4510 ••• 218"), ("Причина", "не подошёл размер"), ("Подпись", "А. Смирнова")]
    fts = [F("паспорта"), F("причина"), F("подпись")]
    return [
        {"bg": p("bg_counter"), "av": None, "els": [
            (T.headline(p("h1"), ["У кассы —", "возврат"], 900, size=130, red_words=["возврат"],
                        kicker="Ситуация"), 1020, 120, 0.3),
            (T.note(p("h1n"), "Что происходит", "Продавец напрягается", 780), 1020, 560, F("Многие")),
        ]},
        {"bg": p("bg_diag"), "av": anna(625), "els": [
            (T.headline(p("h2"), ["Возврат —", "проверка", "сервиса"], 560, size=110, red_words=["сервиса"],
                        kicker="Зря"), 80, 150, b[1] + 0.2),
            (T.strike_word(p("h2s"), "скандал"), 1330, 250, F("скандал") - 0.2),
        ]},
        {"bg": p("bg_split"), "av": anna(1180), "els": [
            (T.nameplate(p("h3n"), "Анна", "администратор"), 1150, 720, b[2] + 0.2),
            (T.roadmap(p("h3r"), ["Разговор", "Осмотр", "Документы", "Расчёт"], 620,
                       title="Порядок для любого магазина"), 100, 200, F("порядок")),
        ]},
        {"bg": p("bg_plain"), "av": anna(60), "els": [
            (T.step_label(p("h4l"), 1, "Разговор"), 860, 120, b[3] + 0.15),
            (T.check_row(p("h4a"), "Дать договорить", 960), 880, 380, F("Дайте")),
            (T.check_row(p("h4b"), "Один уточняющий вопрос", 960), 880, 510, F("Задайте")),
            (T.check_row(p("h4c"), "Без оправданий", 960), 880, 640, F("оправдывайтесь") - 0.3),
        ]},
        {"bg": p("bg_tag"), "av": None, "els": [
            (T.step_label(p("h5l"), 2, "Осмотр"), 1000, 80, b[4] + 0.15),
            (T.icon_tile(p("h5a"), f"{IMG}/l1h_ic_shirt.png", "Не носили"), 990, 300, F("Вещь")),
            (T.icon_tile(p("h5b"), f"{IMG}/l1h_ic_tag.png", "Бирки"), 1290, 300, F("бирки")),
            (T.icon_tile(p("h5c"), f"{IMG}/l1h_ic_box.png", "Упаковка"), 1590, 300, F("упаковка")),
            (T.big_days(p("h5d"), "14", "дней", "с покупки"), 1010, 620, F("срок")),
        ]},
        {"bg": p("bg_phone"), "av": {"kind": "circle", "cx": 540, "cy": 500, "r": 300, "size": 420,
                                      "x": 1330, "y": 80}, "els": [
            (T.note(p("h6"), "Чек потерян?", "Оплата в банковском приложении", 700), 1140, 560, F("Чек")),
        ]},
        {"bg": p("bg_diag"), "av": anna(1200), "els": [
            (T.step_label(p("h7l"), 3, "Документы"), 100, 50, b[6] + 0.15),
            (T.form_card(p("h7f0"), "Заявление на возврат", form, 1000, 0), 100, 270, F("Бланк"), fts[0]),
            (T.form_card(p("h7f1"), "Заявление на возврат", form, 1000, 1), 100, 270, fts[0], fts[1], "cut"),
            (T.form_card(p("h7f2"), "Заявление на возврат", form, 1000, 2), 100, 270, fts[1], fts[2], "cut"),
            (T.form_card(p("h7f3"), "Заявление на возврат", form, 1000, 3), 100, 270, fts[2], b[7], "cut"),
        ]},
        {"bg": p("bg_refund"), "av": anna(647, s=0.58), "els": [
            (T.step_label(p("h8l"), 4, "Расчёт"), 90, 50, b[7] + 0.15),
            (T.pay_card(p("h8a"), f"{IMG}/l1h_ic_card.png", "Картой", "на карту"), 110, 300, F("Платили")),
            (T.pay_card(p("h8b"), f"{IMG}/l1h_ic_cash.png", "Наличными", "из кассы"), 1370, 300, F("Наличными")),
        ]},
        {"bg": p("bg_diag"), "av": anna(625), "els": [
            (T.quote(p("h9q"), "Спасибо, что пришли к нам", 560, kicker="Скажите напоследок"), 60, 140,
             F("Напоследок")),
            (T.statement(p("h9s"), "Спокойный возврат", "Придёт снова — с друзьями", 600), 1260, 140,
             F("Человек")),
        ]},
    ]


def captions(words, total):
    caps = V.captions(words, total)
    for c in caps:   # в субтитрах — цифрами, как на экране
        c["lines"] = [ln.replace("четырнадцать", "14") for ln in c["lines"]]
    return caps


V.scenes = scenes


def main():
    os.makedirs(V.TMP, exist_ok=True)
    total = float(V.subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                    "csv=p=0", V.AUDIO], capture_output=True, text=True).stdout)
    words = V.word_times()
    caps = captions(words, total)
    sc = scenes(V.finder(words))
    bounds = V.BOUNDS + [total]
    parts = []
    for k, s in enumerate(sc):
        parts.append(V.render_scene(k, s, bounds[k], bounds[k + 1], caps))
        print("scene", k + 1, flush=True)
    lst = f"{V.TMP}/concat.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{x}'\n" for x in parts)
    V.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", V.AUDIO, "-map", "0:v",
           "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
           V.OUT])
    print("done", V.OUT)


if __name__ == "__main__":
    main()
