"""Reels №21 «Ваш директор этого не говорил» — рекламный, B2B (обучение персонала).

Директор в стеклянном офисе объявляет «новые правила»: карточка «Регламент», пункты отмечаются
галочками по словам → «Вопросы есть?» (наезд) → «я этого не говорил» (глитч) и штамп «СДЕЛАНО
НЕЙРОСЕТЬЮ» → кадр: тот же директор спокойно пьёт кофе в кафе → «инструкция → видео» с чипами
«расскажу / проверю / повторю ×100» → «Напишите «РЕГЛАМЕНТ» в директ». Движок ad_engine.

python3 render/landing/build_ig21.py   →  render/landing/ig21-9x16.mp4
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ad_cards as C
import ad_engine as E
import build_ig6 as B

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig21/trim2.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig21-whisper-final2.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig21/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig21-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig21"

SPOKEN = ("Коллеги, с понедельника у нас новые правила. Три пункта. Первое: каждого покупателя встречаем "
          "за десять секунд. Второе: на вопрос «а есть подешевле?» — всегда предлагаем два варианта. "
          "Третье: улыбаемся, даже если день тяжёлый. Вопросы есть? Тогда признаюсь… я этого не говорил. "
          "Меня сделали из одной фотографии и текста регламента. А настоящий директор в это время спокойно "
          "пил кофе. Если ваши сотрудники не читают инструкции — превратите их в видео. Я расскажу, проверю "
          "и повторю хоть сто раз. Напишите «Регламент» в директ.")
HOOK = "ВАШ ДИРЕКТОР ЭТОГО НЕ_ГОВОРИЛ"


def main():
    os.makedirs(B.TMP, exist_ok=True)
    words, total, subs, F = E.prepare(SPOKEN, HOOK)
    T = lambda w, after=0.0: F(w, after) - 0.05
    t_memo = T("Три")
    t1, t2, t3 = T("Первое:"), T("Второе:"), T("Третье:")
    t_q, t_then = T("Вопросы"), T("Тогда")
    t_lie = T("я", t_then)
    t_made = T("Меня", t_lie)
    t_real = T("А", t_made)
    t_if = T("Если", t_real)
    t_tell = T("Я", t_if)
    t_cta = T("Напишите")
    P = lambda name: f"{B.TMP}/{name}.png"
    cards = []
    for k, (a, b) in enumerate([(t_memo, t1), (t1, t2), (t2, t3), (t3, t_then)]):
        cards.append((*E.place(*C.memo(P(f"memo{k}"), k), 640), ))
        cards[-1] = (cards[-1][0], a, b, cards[-1][1])
    path, box = E.place(*C.ai_stamp(P("stamp")), 700)
    cards.append((path, t_made, t_real, box))
    for k, (a, b) in enumerate([(t_if, t_tell), (t_tell, t_cta)]):
        path, box = E.place(*C.doc_to_video(P(f"doc{k}"), chips=k == 1), 660)
        cards.append((path, a, b, box))
    path, box = E.place(*C.cta(P("cta"), "РЕГЛАМЕНТ"), 900)
    cards.append((path, t_cta, total, box))
    brolls = [(f"{ROOT}/scratch/img/ig21_coffee.png", t_real, t_if - t_real)]
    sfx = [(t_memo, "whoosh", 0.5), (t1, "pop", 0.6), (t2, "pop", 0.6), (t3, "pop", 0.6),
           (t_q, "tick", 0.4), (t_lie, "glitch", 0.6), (t_made, "stamp", 0.9), (t_real, "whoosh", 0.4),
           (t_if, "whoosh", 0.5), (t_tell, "pop", 0.6), (t_cta, "hit", 0.7)]
    cfg = {"cards": cards, "brolls": brolls, "glitch": [(t_lie - 0.05, t_lie + 0.4)],
           "punch": [(t_q, t_then), (t_lie, t_made)], "sfx": sfx,
           "music": f"{ROOT}/scratch/music/ig21-music.mp3", "music_gain": 0.12}
    E.build(cfg, words, total, subs)


if __name__ == "__main__":
    main()
