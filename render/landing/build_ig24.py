"""Reels №24 «Пока вы это смотрите, настоящая я сплю» — продающий, с параллельной историей.

Кондитер Марина три года не могла вести блог (5 утра, дети, заказы) → отправила одну фотографию и рецепты →
в кадре её цифровая копия, а Марина высыпается → «такую копию можно сделать и вам»: карточка двух вариантов
(делаем за вас от 1 000 ₽/мин / своя система) → «КОПИЯ». Кадры истории — gpt-image-2 с ведущей как референсом.
Движок ad_engine (карточки ниже лица, субтитры скрываются под карточкой, глитч, наезды, звуки, музыка HeyGen).

python3 render/landing/build_ig24.py   →  render/landing/ig24-9x16.mp4
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ad_cards as C
import ad_engine as E
import build_ig6 as B

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig24/trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig24-whisper-final.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig24/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig24-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig24"
IMG = f"{ROOT}/scratch/img"

SPOKEN = ("Пока вы смотрите это видео, настоящая я… сплю. Меня зовут Марина, я пеку торты на заказ. Встаю в пять "
          "утра, потом дети, школа, заказы до ночи. Блог я хотела вести три года. Но когда снимать? Поэтому я "
          "отправила одну фотографию… и тексты своих рецептов. И вот я здесь. Я её цифровая копия. Снимаюсь каждый "
          "день, не устаю и не прошу перерыв. А Марина наконец высыпается. Такую копию можно сделать и вам. Мы пишем "
          "сценарий, подбираем картинки и музыку, монтируем и всё согласуем с вами. От тысячи рублей за минуту. А "
          "если хотите делать ролики сами, настроим всю систему под вас. Напишите «Копия» в директ, подскажем, что "
          "подойдёт вам.")
HOOK = "ПОКА ВЫ ЭТО СМОТРИТЕ, НАСТОЯЩАЯ Я_СПЛЮ"


TAIL = 1.6   # призыв держится после последнего слова


def main():
    os.makedirs(B.TMP, exist_ok=True)
    import subprocess
    padded = f"{B.TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af", f"apad=pad_dur={TAIL}", "-ar", "48000",
                    padded], check=True)
    B.AUDIO = padded
    words, total, subs, F = E.prepare(SPOKEN, HOOK)
    T = lambda w, after=0.0: F(w, after) - 0.05
    t_name, t_up, t_blog = T("Меня"), T("Встаю"), T("Блог")
    t_send = T("Поэтому")
    t_here = T("И", t_send)
    t_copy = T("Я", t_here)
    t_marina = T("А", t_copy)
    t_offer = T("Такую")
    t_self = T("А", t_offer)
    t_cta = T("Напишите")
    gap = lambda a, b, d: min(d, b - a - 0.05)
    brolls = [(f"{IMG}/ig24_b1.png", t_name, gap(t_name, t_up, 3.2)),
              (f"{IMG}/ig24_b2.png", t_up, gap(t_up, t_blog, 3.6)),
              (f"{IMG}/ig24_b3.png", t_blog, gap(t_blog, t_send, 3.8)),
              (f"{IMG}/ig24_b4.png", t_marina, gap(t_marina, t_offer, 3.2))]
    P = lambda name: f"{B.TMP}/{name}.png"
    cards = []
    for k, (a, b) in enumerate([(t_offer, t_self), (t_self, t_cta)]):
        path, box = E.place(*C.options(P(f"opt{k}"), k + 1), 640)
        cards.append((path, a, b, box))
    path, box = E.place(*C.cta(P("cta"), "КОПИЯ"), 900)
    cards.append((path, t_cta, total, box))
    sfx = [(t_name, "whoosh", 0.35), (t_copy, "glitch", 0.6), (t_copy + 0.05, "bass", 0.45),
           (t_offer, "whoosh", 0.5), (t_self, "pop", 0.6), (t_cta, "hit", 0.7)]
    cfg = {"cards": cards, "brolls": brolls, "glitch": [(t_copy - 0.05, t_copy + 0.4)],
           "punch": [(t_copy, t_copy + 1.6)], "sfx": sfx,
           "music": f"{ROOT}/scratch/music/ig24-music.mp3", "music_gain": 0.12}
    for img, a, d in brolls:
        assert d >= 2.0, f"кадр {img} короче 2 с"
        assert not (a < t_copy + 1.6 and a + d > t_copy), "кадр закрывает раскрытие"
    E.build(cfg, words, total, subs)


if __name__ == "__main__":
    main()
