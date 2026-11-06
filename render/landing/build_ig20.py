"""Reels №20 «Это видео стоило мне 0 ₽» — рекламный: ведущая + чек, который печатается по словам.

Крючок «ЭТО ВИДЕО СТОИЛО МНЕ 0 РУБЛЕЙ» → кассовый чек (студия, оператор, свет, гримёр, попытки — 0 ₽),
итог «0 ₽» → глитч и штамп «ВЕДУЩЕЙ НЕ СУЩЕСТВУЕТ» → наезд на «нейросеть» → карточка цены
«от 1 000 ₽ / мин» с чипами → «Напишите «ЧЕК» в директ». Стиль сайта ИИАВАТАР (ad_cards), движок ad_engine.

python3 render/landing/build_ig20.py   →  render/landing/ig20-9x16.mp4
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ad_cards as C
import ad_engine as E
import build_ig6 as B

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig20/trim2.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig20-whisper-final2.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig20/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig20-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig20"

SPOKEN = ("Это видео стоило мне ноль рублей. Сейчас покажу чек. Студия ноль. Оператор ноль. Свет ноль. "
          "Гримёр ноль. Двадцать попыток, потому что я запнулась, — тоже ноль. Знаете, почему? "
          "Меня не существует. Я — ведущая, которую создала нейросеть. Из одной фотографии и текста. "
          "А теперь честно: для вас такое видео стоит от тысячи рублей за минуту. Без съёмок, без студии, "
          "без актёров. Реклама, обучение, блог — за пару дней. Напишите «Чек» в директ — посчитаем ваш ролик.")
HOOK = "ЭТО ВИДЕО СТОИЛО МНЕ 0_РУБЛЕЙ"


def main():
    os.makedirs(B.TMP, exist_ok=True)
    words, total, subs, F = E.prepare(SPOKEN, HOOK)
    T = lambda w, after=0.0: F(w, after) - 0.05
    t_check = T("Сейчас")
    rows = [T("Студия"), T("Оператор"), T("Свет"), T("Гримёр"), T("Двадцать")]
    t_total = T("тоже")
    t_know = T("Знаете,")
    t_stamp = T("существует.")
    t_me = T("Я", t_stamp)
    t_price = T("А", t_me)
    t_chips1, t_chips2 = T("Без"), T("Реклама,")
    t_cta = T("Напишите")
    end = total
    P = lambda name: f"{B.TMP}/{name}.png"
    cards = []
    marks = [t_check] + rows + [t_total]
    for k, (a, b) in enumerate(zip(marks, marks[1:] + [t_stamp])):
        n_rows = min(k, 5)
        path, box = E.place(*C.receipt(P(f"rc{k}"), n_rows, total=k == 6), 640, 0.85)
        cards.append((path, a, b, box))
    path, box = E.place(*C.receipt(P("rc_stamp"), 5, total=True, stamp=True), 640, 0.85)
    cards.append((path, t_stamp, t_me, box))
    for lvl, (a, b) in enumerate([(t_price, t_chips1), (t_chips1, t_chips2), (t_chips2, t_cta)]):
        path, box = E.place(*C.price(P(f"pr{lvl}"), lvl), 700)
        cards.append((path, a, b, box))
    path, box = E.place(*C.cta(P("cta"), "ЧЕК"), 900)
    cards.append((path, t_cta, end, box))
    merged = cards
    sfx = [(t_check, "whoosh", 0.5)] + [(t, "click", 0.7) for t in rows] + [(t_total, "ding", 0.6),
           (t_stamp, "stamp", 0.9), (t_stamp - 0.05, "glitch", 0.5), (t_me + 0.6, "bass", 0.5),
           (t_price, "whoosh", 0.5), (t_chips1, "pop", 0.6), (t_chips2, "pop", 0.6), (t_cta, "hit", 0.7)]
    cfg = {"cards": merged, "glitch": [(t_stamp - 0.1, t_stamp + 0.35), (t_me + 0.9, t_me + 1.15)],
           "punch": [(t_stamp, t_stamp + 1.0), (t_me + 0.9, t_price - 0.2)], "sfx": sfx,
           "music": f"{ROOT}/scratch/music/ig20-music.mp3", "music_gain": 0.14}
    # наезд на «нейросеть» только когда нет карточек
    for _, a, b, _ in merged:
        for pa, pb in cfg["punch"][1:]:
            assert b <= pa or a >= pb, "наезд под карточкой"
    E.build(cfg, words, total, subs)


if __name__ == "__main__":
    main()
