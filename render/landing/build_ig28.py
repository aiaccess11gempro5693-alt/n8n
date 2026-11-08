"""Reels №28 «20 уроков — и ни разу не включила камеру» — продающий для преподавателей и онлайн-школ.

Преподаватель английского: раньше урок = свет, штатив, дубли, монтаж (кадр) → курс ждал 2 года (карточка)
→ отправила тексты и одну фотографию (ТЕКСТЫ → УРОКИ) → через неделю курс готов (кадр) → «это видео тоже без
камеры, меня сделала нейросеть» (глитч + штамп) → два варианта (делаем за вас / своя система) → «КУРС».
Движок ad_engine.

python3 render/landing/build_ig28.py   →  render/landing/ig28-9x16.mp4
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ad_cards as C
import ad_engine as E
import build_ig6 as B

ROOT = B.ROOT
B.AUDIO = f"{ROOT}/scratch/ig28/trim.mp3"
B.WHISPER = f"{ROOT}/scratch/ig28-whisper-final.json"
B.CLIP = f"{ROOT}/scratch/ig28/host.mp4"
B.OUT = f"{ROOT}/render/landing/ig28-9x16.mp4"
B.TMP = f"{ROOT}/render/landing/.ig28"
IMG = f"{ROOT}/scratch/img"

SPOKEN = ("Двадцать уроков… и ни разу не включила камеру. Я преподаю английский. Раньше один урок — это свет, "
          "штатив, десять дублей… и вечер монтажа. Свой курс я откладывала два года. А потом просто отправила тексты "
          "уроков… и одну фотографию. Через неделю курс был готов: субтитры, картинки, музыка. И да… это видео тоже "
          "без камеры. Меня сделала нейросеть! Хотите так же? Делаем уроки за вас — от тысячи рублей за минуту. Или "
          "настроим систему, и будете делать сами. Напишите «Курс» в директ.")
HOOK = "20 УРОКОВ — И НИ РАЗУ НЕ_ВКЛЮЧИЛА КАМЕРУ"
TAIL = 1.6


def main():
    os.makedirs(B.TMP, exist_ok=True)
    padded = f"{B.TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af", f"apad=pad_dur={TAIL}", "-ar", "48000",
                    padded], check=True)
    B.AUDIO = padded
    words, total, subs, F = E.prepare(SPOKEN, HOOK)
    T = lambda w, after=0.0: F(w, after) - 0.05
    t_before = T("Раньше")
    t_years = T("Свой")
    t_send = T("А", t_years)
    t_week = T("Через")
    t_yes = T("И", t_week + 1.0)
    t_ai = T("Меня", t_yes)
    t_want = T("Хотите")
    t_or = T("Или", t_want)
    t_cta = T("Напишите")
    gap = lambda a, b, d: min(d, b - a - 0.05)
    brolls = [(f"{IMG}/ig28_b1.png", t_before, gap(t_before, t_years, 4.0)),
              (f"{IMG}/ig28_b2.png", t_week, gap(t_week, t_yes, 4.0))]
    P = lambda name: f"{B.TMP}/{name}.png"
    cards = []
    path, box = C.big_count(P("years"), "2 ГОДА", "курс ждал своего часа", ["свет", "штатив", "10 дублей", "монтаж"])
    cards.append((path, t_years, t_send, box))
    path, box = E.place(*C.doc_to_video(P("doc"), left="ТЕКСТЫ", right="УРОКИ"), 680)
    cards.append((path, t_send, t_week, box))
    path, box = C.ai_stamp(P("stamp"))
    cards.append((path, t_ai, t_ai + 1.8, box))
    for k, (a, b) in enumerate([(t_want, t_or), (t_or, t_cta)]):
        path, box = E.place(*C.options(P(f"opt{k}"), k + 1), 640)
        cards.append((path, a, b, box))
    path, box = E.place(*C.cta(P("cta"), "КУРС"), 900)
    cards.append((path, t_cta, total, box))
    sfx = [(t_before, "whoosh", 0.35), (t_years, "hit", 0.5), (t_send, "whoosh", 0.45), (t_week, "chime", 0.5),
           (t_ai - 0.05, "glitch", 0.6), (t_ai, "stamp", 0.6), (t_want, "whoosh", 0.5), (t_or, "pop", 0.6),
           (t_cta, "hit", 0.7)]
    cfg = {"cards": cards, "brolls": brolls, "glitch": [(t_ai - 0.1, t_ai + 0.35)],
           "punch": [(t_yes, t_yes + 1.4), (t_ai, t_ai + 1.6)], "sfx": sfx,
           "music": f"{ROOT}/scratch/music/ig28-music.mp3", "music_gain": 0.11}
    for img, a, d in brolls:
        assert d >= 2.0, f"кадр {img} короче 2 с"
    E.build(cfg, words, total, subs)


if __name__ == "__main__":
    main()
