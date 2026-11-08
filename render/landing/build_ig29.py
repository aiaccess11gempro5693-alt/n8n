"""Reels №29 «Видео для 40 товаров без единой съёмки» — продающий для продавцов на маркетплейсах.

Ведущий из карточки товара раскрывается сразу: «меня не существует, меня сделала нейросеть для мастера Андрея»
(глитч + штамп) → мастер в мастерской (кадр) → съёмка = фотограф, студия, деньги (карточка) → 40 товаров (кадр)
→ фото + пара строк → ролик (ФОТО → РОЛИК) → покупательница с доской (кадр) → ×40, у каждой доски свой ролик
→ цена → «ТОВАР». Движок ad_engine.

python3 render/landing/build_ig29.py   →  render/landing/ig29-9x16.mp4
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ad_cards as C
import ad_engine as E
import build_ig6 as B

ROOT = B.ROOT
B.AUDIO = f"{ROOT}/scratch/ig29/trim.mp3"
B.WHISPER = f"{ROOT}/scratch/ig29-whisper-final.json"
B.CLIP = f"{ROOT}/scratch/ig29/host.mp4"
B.OUT = f"{ROOT}/render/landing/ig29-9x16.mp4"
B.TMP = f"{ROOT}/render/landing/.ig29"
IMG = f"{ROOT}/scratch/img"

SPOKEN = ("Этот ролик — из карточки товара. И меня не существует. Меня сделала нейросеть для мастера Андрея. Андрей "
          "делает деревянные разделочные доски. С видео покупатель лучше понимает товар… но съёмка каждого ролика — "
          "это фотограф, студия и деньги. А товаров у Андрея — сорок. Он прислал фотографии и пару строк о каждом. "
          "Теперь у каждой доски свой ролик: я рассказываю, из какого дерева, какой размер и как ухаживать. Хотите "
          "так же для своих товаров? " + os.environ.get("PRICE", "Цена — от тысячи рублей за минуту!") +
          " Напишите в директ слово «Товар»!")
HOOK = "ВИДЕО ДЛЯ 40 ТОВАРОВ — БЕЗ_ЕДИНОЙ СЪЁМКИ"
TAIL = 1.6


def main():
    os.makedirs(B.TMP, exist_ok=True)
    padded = f"{B.TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af", f"apad=pad_dur={TAIL}", "-ar", "48000",
                    padded], check=True)
    B.AUDIO = padded
    words, total, subs, F = E.prepare(SPOKEN, HOOK)
    T = lambda w, after=0.0: F(w, after) - 0.05
    t_ai = T("Меня")
    t_andrey = T("Андрей")
    t_with = T("С", t_andrey)
    t_but = T("но", t_with)
    t_forty = T("А", t_but)
    t_sent = T("фотографии")
    t_now = T("Теперь")
    t_tell = T("из", t_now)
    t_want = T("Хотите")
    t_cta = T("Напишите")
    gap = lambda a, b, d: min(d, b - a - 0.05)
    brolls = [(f"{IMG}/ig29_b1.png", t_andrey, gap(t_andrey, t_but, 4.0)),
              (f"{IMG}/ig29_b2.png", t_forty, gap(t_forty, t_sent, 3.6)),
              (f"{IMG}/ig29_b3.png", t_now, gap(t_now, t_tell, 3.0))]
    P = lambda name: f"{B.TMP}/{name}.png"
    cards = []
    path, box = C.ai_stamp(P("stamp"))
    cards.append((path, t_ai, t_ai + 2.4, box))
    path, box = C.big_count(P("shoot"), "СЪЁМКА", "каждого ролика — это", ["фотограф", "студия", "деньги"])
    cards.append((path, t_but, t_forty, box))
    path, box = E.place(*C.doc_to_video(P("doc"), left="ФОТО", right="РОЛИК"), 680)
    cards.append((path, t_sent, t_now, box))
    path, box = C.big_count(P("x40"), "×40", "у каждой доски — свой ролик", ["из какого дерева", "размер", "уход"])
    cards.append((path, t_tell, t_want, box))
    path, box = E.place(*C.price(P("price"), 1), 640)
    cards.append((path, t_want, t_cta, box))
    path, box = E.place(*C.cta(P("cta"), "ТОВАР"), 900)
    cards.append((path, t_cta, total, box))
    sfx = [(t_ai - 0.05, "glitch", 0.6), (t_ai, "stamp", 0.6), (t_andrey, "whoosh", 0.35), (t_but, "hit", 0.5),
           (t_forty, "whoosh", 0.45), (t_sent, "pop", 0.45), (t_now, "chime", 0.5), (t_tell, "pop", 0.5),
           (t_want, "whoosh", 0.5), (t_cta, "hit", 0.7)]
    t_not = T("И")
    cfg = {"cards": cards, "brolls": brolls, "glitch": [(t_not - 0.05, t_not + 0.4), (t_ai - 0.1, t_ai + 0.3)],
           "punch": [(t_not, t_not + 1.4)], "sfx": sfx,
           "music": f"{ROOT}/scratch/music/ig29-music.mp3", "music_gain": 0.11}
    for img, a, d in brolls:
        assert d >= 2.0, f"кадр {img} короче 2 с"
    E.build(cfg, words, total, subs)


if __name__ == "__main__":
    main()
