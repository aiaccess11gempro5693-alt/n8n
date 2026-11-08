"""Мультсериал «Саша: 30 дней без долгов», серия 1 — «День первый: список долгов».

Саша (мультяшный фото-аватар HeyGen) на весь кадр; сверху игровая панель ДЕНЬ / ДОЛГ / СОБЛАЗНЫ;
ниже лица по репликам: список долгов (микрозайм — «гасить первым») → уведомление-соблазн (соблазны 0→1)
→ выбор зрителя на завтра: А — наушники в рассрочку, Б — эти деньги в микрозайм, «пишите А или Б».
Движок ad_engine (затемнение под карточкой, субтитры скрываются под карточкой, наезды, звуки, музыка HeyGen).

python3 render/landing/build_debt01.py   →  render/landing/debt01-9x16.mp4
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ad_engine as E
import build_ig6 as B
import debt_cards as D

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/debt01/trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/debt01-whisper-final.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/debt01/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/debt01-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.debt01"
E.FACE_BOTTOM = 900          # у мультяшного Саши подбородок ниже, чем у ведущих рекламных роликов

SPOKEN = ("Меня зовут Саша, мне тридцать… и я должен триста тысяч рублей. Три кредитки, кредит на телефон и "
          "микрозайм, о котором я стараюсь не думать. Даю себе тридцать дней, чтобы всё это разгрести. И решать "
          "за меня будете вы. День первый. Шаг первый — без паники. Выписываю все долги в один список: сколько "
          "должен, под какой процент и когда платить. Ого… Микрозайм — самый маленький, но самый дорогой. Значит, "
          "гасить его первым. И тут… уведомление! Наушники, минус сорок процентов, рассрочка без переплаты! Ну вы "
          "поняли. Выбирайте, что я сделаю завтра. Вариант А — беру наушники в рассрочку, это же всего две тысячи в "
          "месяц. Вариант Б — откладываю эти деньги и гашу ими микрозайм. Пишите в комментариях: А или Б. Что "
          "выберете — то и будет. Только честно.")
HOOK = "ДЕНЬ 1 ИЗ 30: САША ВЫЛЕЗАЕТ ИЗ_ДОЛГОВ"
TAIL = 2.0                   # выбор держится после последнего слова


def main():
    os.makedirs(B.TMP, exist_ok=True)
    padded = f"{B.TMP}/voice-pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", B.AUDIO, "-af", f"apad=pad_dur={TAIL}", "-ar", "48000",
                    padded], check=True)
    B.AUDIO = padded
    words, total, subs, F = E.prepare(SPOKEN, HOOK)
    T = lambda w, after=0.0: F(w, after) - 0.05
    t_debt = T("триста")
    t_days = T("Даю")
    t_you = T("И", t_days)
    t_day1 = T("День", t_you)
    t_list = T("Выписываю")
    t_ogo = T("Ого…")
    t_hot = T("Микрозайм", t_ogo)
    t_then = T("И", t_hot + 1.0)
    t_note = T("уведомление!")
    t_choose = T("Выбирайте")
    t_a = T("Вариант")
    t_b = T("Вариант", t_a + 0.5)
    t_cta = T("Пишите")
    P = lambda name: f"{B.TMP}/{name}.png"

    cards = []
    for k, (a, b, l1, l2, col, tilt) in enumerate([
            (t_days, t_you, "30 ДНЕЙ", "чтобы всё разгрести", D.MUSTARD, -3),
            (t_you, t_day1, "РЕШАЕТЕ ВЫ", "каждый день — выбор в комментариях", D.BLUE, 2),
            (t_day1, t_list, "ШАГ 1", "без паники", D.GREEN, -2)]):
        path, box = D.sticker(P(f"st{k}"), 1080, l1, l2, col, tilt)
        cards.append((path, a, b, box))
    for k, (a, b) in enumerate([(t_list, t_hot), (t_hot, t_then)]):
        path, box = D.debt_list(P(f"list{k}"), 1010, highlight=bool(k))
        cards.append((path, a, b, box))
    path, box = D.notification(P("note"), 1050)
    cards.append((path, t_note, t_choose, box))
    for k, (a, b) in enumerate([(t_a, t_b), (t_b, t_cta), (t_cta, total)]):
        path, box = D.choice(P(f"choice{k}"), 960, level=k + 1)
        cards.append((path, a, b, box))

    hud = [(D.hud(P("hud0"), temptations=0)[0], 0.25, t_note),
           (D.hud(P("hud1"), temptations=1, flash=True)[0], t_note, t_note + 1.6),
           (D.hud(P("hud2"), temptations=1)[0], t_note + 1.6, total)]
    sfx = [(0.25, "pop", 0.5), (t_debt, "hit", 0.55), (t_days, "pop", 0.5), (t_you, "pop", 0.5), (t_day1, "pop", 0.5), (t_list, "whoosh", 0.4), (t_hot, "stamp", 0.7),
           (t_note, "ding", 0.6), (t_a, "pop", 0.55), (t_b, "pop", 0.55), (t_cta, "hit", 0.6)]
    cfg = {"cards": cards, "hud": hud, "brolls": [], "glitch": [],
           "punch": [(t_debt, t_debt + 1.4), (t_note, t_note + 1.2)], "sfx": sfx,
           "music": f"{ROOT}/scratch/music/debt-music.mp3", "music_gain": 0.10, "dim_alpha": 0.28}
    E.build(cfg, words, total, subs)


if __name__ == "__main__":
    main()
