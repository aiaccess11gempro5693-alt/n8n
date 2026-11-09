"""Мультсериал «Саша: 30 дней без долгов», серия 2 — «Верняк».

Зрители выбрали «Б» (настоящий комментарий в кадре) → 2 000 ₽ ушли в микрозайм, долг 298 000 → подработка дня:
промоутер у метро (4 часа, +1 500 ₽; Саша сам говорит у метро) → в автобусе сообщение Лёхи «ставь на матч, кэф 5,
верняк» → ставит всё → проигрыш, кошелёк 0 → выбор: А — отыграться / Б1 — грузчик ночью 4 ч · 3 000 ₽ /
Б2 — мойщик посуды 6 ч · 2 500 ₽. Четыре клипа HeyGen (стол → метро → автобус → стол) склеены встык под одну дорожку.

python3 render/landing/build_debt02.py   →  render/landing/debt02-9x16.mp4
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ad_engine as E
import build_ig6 as B
import debt_cards as D

ROOT = B.ROOT
DIR = f"{ROOT}/scratch/debt02"
B.AUDIO = f"{DIR}/trim.mp3"
B.WHISPER = f"{ROOT}/scratch/debt02-whisper-final.json"
B.CLIP = f"{DIR}/host.mp4"
B.OUT = f"{ROOT}/render/landing/debt02-9x16.mp4"
B.TMP = f"{ROOT}/render/landing/.debt02"
E.FACE_BOTTOM = 900
SEGS = [("clip1.mp4", 9.1), ("clip2.mp4", 18.09 - 9.1), ("clip3.mp4", 36.27 - 18.09), ("clip4.mp4", None)]

SPOKEN = ("День второй. Вы выбрали Б — и я отнёс две тысячи в микрозайм. И долг стал меньше! Мелочь… а приятно! "
          "Подработка дня — промоутер у метро. Четыре часа раздаю листовки. Руки замёрзли… но полторы тысячи мои. "
          "Еду домой в автобусе, и тут пишет Лёха: «Ставь на матч, коэффициент пять, это верняк». Пять… это же семь "
          "с половиной тысяч! Я поставил. Все полторы тысячи. Матч закончился… Ноль. Верняков не бывает. Теперь два "
          "пути. Вариант А — отыграться: поставлю ещё, и всё вернётся. Вариант Б — остановиться и срочно идти на "
          "вторую подработку. Б1 — грузчик ночью: четыре часа, три тысячи. Б2 — мойщик посуды в кафе: шесть часов, "
          "две с половиной тысячи. Пишите в комментариях: А, Б1 или Б2. Только честно.")
HOOK = "ДЕНЬ 2 ИЗ 30: ВЕРНЯК"
TAIL = 2.0


def join_clips():
    """Четыре клипа HeyGen встык, каждый ровно по длине своего куска озвучки."""
    inputs, filt = [], []
    for i, (name, dur) in enumerate(SEGS):
        inputs += ["-i", f"{DIR}/{name}"]
        tr = f"trim=0:{dur:.3f}," if dur else ""
        filt.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,"
                    f"tpad=stop_duration=1:stop_mode=clone,{tr}setpts=PTS-STARTPTS[v{i}]")
    filt.append("".join(f"[v{i}]" for i in range(len(SEGS))) + f"concat=n={len(SEGS)}:v=1:a=0[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[v]",
                    "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-an", B.CLIP], check=True)


def main():
    os.makedirs(B.TMP, exist_ok=True)
    if not os.path.exists(B.CLIP):
        join_clips()
    padded = f"{B.TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af", f"apad=pad_dur={TAIL}", "-ar", "48000",
                    padded], check=True)
    B.AUDIO = padded
    words, total, subs, F = E.prepare(SPOKEN, HOOK)
    T = lambda w, after=0.0: F(w, after) - 0.05
    t_b = T("Б")
    subs[0]["t1"] = t_b
    subs[1]["t0"] = t_b
    t_less = T("И", t_b + 1.0)
    t_job = T("Подработка")
    t_cold = T("Руки")
    t_paid = T("но", t_cold)
    t_bus = T("Еду")
    t_msg = T("пишет")
    t_five = T("Пять…")
    t_bet = T("Я", t_five)
    t_end = T("Матч", t_bet)
    t_zero = T("Ноль.")
    t_two = T("Теперь")
    t_a = T("Вариант")
    t_bb = T("Вариант", t_a + 0.5)
    t_b1 = T("Б1")
    t_b2 = T("Б2")
    t_cta = T("Пишите")
    P = lambda name: f"{B.TMP}/{name}.png"

    cards = []
    path, box = D.comment_card(P("comment"), 980, f"{ROOT}/scratch/img/debt02_comment_src.png")
    cards.append((path, t_b, t_less, box))
    path, box = D.sticker(P("st_less"), 1060, "ДОЛГ −2 000 ₽", "микрозайм стал меньше", D.GREEN, -3)
    cards.append((path, t_less, t_job - 0.05, box))
    jk = dict(title="Промоутер у метро", sub="раздать листовки · 4 часа")
    path, box = D.job_card(P("job0"), 1080, False, **jk)
    cards.append((path, t_job, t_paid, box))
    path, box = D.job_card(P("job1"), 1080, True, pay="+1 500 ₽", note="4 часа на холоде", **jk)
    cards.append((path, t_paid, t_bus - 0.05, box))
    path, box = D.bet_card(P("bet0"), 1000)
    cards.append((path, t_msg, t_five, box))
    path, box = D.sticker(P("st_five"), 1070, "×5 = 7 500 ₽?", "«это верняк»", D.MUSTARD, 3)
    cards.append((path, t_five, t_bet, box))
    path, box = D.sticker(P("st_bet"), 1070, "СТАВКА: ВСЕ 1 500 ₽", "весь заработок дня", D.RED, -3)
    cards.append((path, t_bet, t_end, box))
    path, box = D.bet_card(P("bet1"), 900, lost=True)
    cards.append((path, t_end, t_two - 0.05, box))
    for k, (lvl, a, b) in enumerate([(1, t_a, t_b1), (2, t_b1, t_b2), (3, t_b2, t_cta), (4, t_cta, total)]):
        path, box = D.choice2(P(f"choice{k}"), 900, level=lvl)
        cards.append((path, a, b, box))
    H = lambda n, **kw: D.hud(P(f"hud{n}"), day=2, **kw)[0]
    hud = [(H(0, debt="300 000 ₽", wallet="0 ₽"), 0.25, t_less),
           (H(1, debt="298 000 ₽", wallet="0 ₽"), t_less, t_paid),
           (H(2, debt="298 000 ₽", wallet="1 500 ₽", wallet_flash=True), t_paid, t_bet),
           (H(3, debt="298 000 ₽", wallet="0 ₽", temptations=1, flash=True), t_bet, t_bet + 1.6),
           (H(4, debt="298 000 ₽", wallet="0 ₽", temptations=1), t_bet + 1.6, total)]
    sfx = [(0.25, "pop", 0.5), (t_b, "pop", 0.55), (t_less, "chime", 0.5), (t_job - 0.15, "whoosh", 0.45),
           (t_paid, "chime", 0.6), (t_bus - 0.15, "whoosh", 0.45), (t_msg, "ding", 0.6), (t_five, "riser", 0.4),
           (t_bet, "hit", 0.55), (t_end, "tick", 0.4), (t_zero, "stamp", 0.75), (t_a, "pop", 0.55),
           (t_bb, "pop", 0.55), (t_b1, "pop", 0.5), (t_b2, "pop", 0.5), (t_cta, "hit", 0.6)]
    cfg = {"cards": cards, "hud": hud, "brolls": [], "glitch": [(t_zero - 0.05, t_zero + 0.45)],
           "punch": [(t_five, t_five + 1.2), (t_zero, t_zero + 1.4)], "sfx": sfx,
           "music": f"{ROOT}/scratch/music/debt-music.mp3", "music_gain": 0.10, "dim_alpha": 0.28}
    E.build(cfg, words, total, subs)


if __name__ == "__main__":
    main()
