"""Reels №15 «Не отвечай на рабочие звонки после семи» — ведущий в частном самолёте, урок отца.

Как в референсе instagram.com/reel/DeOmLCuIYL1: седой мужчина в кресле частного самолёта говорит в
камеру, белые субтитры по центру. У нас поверх: первая фраза — крупный заголовок (движок build_ig9),
наезды на лицо на ключевых фразах (слова отца, «не дисциплина», «кормит ожидание», поворот),
три вечерних кинокадра gpt-image-2 (звонок при отце, телефон на ужине, телефон экраном вниз)
и тихое фортепиано из библиотеки HeyGen. Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig15.py   →  render/landing/ig15-9x16.mp4
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import sfx as SFX

ROOT = B.ROOT
B.AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig15/trim.mp3")
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig15-whisper-final.json")
B.CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig15/host.mp4")
B.OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig15-9x16.mp4")
B.TMP = f"{ROOT}/render/landing/.ig15"
IMG = f"{ROOT}/scratch/img"
MUSIC = f"{ROOT}/scratch/music/ig15-music.mp3"
MUSIC_GAIN = 0.09
W, H = B.W, B.H
FACE, ZOOM = (520, 490), 1.45

SPOKEN = ("Никогда не отвечай на рабочие звонки после семи вечера. Этому меня научил отец. Мне было двадцать "
          "четыре. Клиент позвонил в половине десятого, я ответил. Отец дождался, пока я положу трубку, и сказал: "
          "«Сынок, этот звонок только что сделал тебя дешевле». Теперь клиент знает: ты доступен, когда удобно ему. "
          "А то, что доступно по первому желанию, не ценят. Этим пользуются. Нас приучили гордиться, что мы всегда "
          "на связи. Но это не дисциплина. Это отсутствие границ. Кто отвечает в десять вечера — ответит и в "
          "субботу. И в свой день рождения. И с температурой. Каждый принятый звонок кормит ожидание следующего. "
          "Уважают того, до кого можно дозвониться только в его время. Кстати, мне можно звонить хоть ночью… "
          "меня сделала нейросеть. А вам — нет. Отправь это тому, кто берёт трубку в любое время. А ты — до "
          "какого часа отвечаешь? Напиши в комментариях. Пока!")


def main():
    os.makedirs(B.TMP, exist_ok=True)
    B.clean_words = lambda: SPOKEN.split()
    words, last = B.timed_words()
    F = N.finder(words)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    subs = N.chunks_with_hook(words, min(total, last + 0.6))
    # крупные планы: (начало, конец)
    t_son = F("Сынок,") - 0.1
    t_now = F("Теперь", t_son) - 0.1
    t_but = F("Но", t_now) - 0.1
    t_who = F("Кто", t_but) - 0.1
    t_each = F("Каждый", t_who) - 0.1
    t_resp = F("Уважают", t_each) - 0.1
    t_btw = F("Кстати,", t_resp) - 0.1
    t_send = F("Отправь", t_btw) - 0.1
    close = [(t_son, t_now), (t_but, t_who), (t_each, t_resp), (t_btw, t_send)]
    # кинокадры: (картинка, начало, длительность)
    t_cli = F("Клиент") - 0.1
    brolls = [("ig15_b1", t_cli, min(4.2, t_son - t_cli - 0.05)),
              ("ig15_b2", t_who, min(4.4, t_each - t_who - 0.05)),
              ("ig15_b3", t_resp, min(4.2, t_btw - t_resp - 0.05))]
    for img, t0, d in brolls:
        assert d >= 2.5, f"{img} мелькает: {d:.2f}"
    assert brolls[0][1] >= subs[0]["t1"] - 0.01, "кадр не должен закрывать заголовок"
    json.dump({"subs": subs, "close": close, "brolls": brolls}, open(f"{B.TMP}/plan.json", "w"),
              ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, [], audio, f"{B.TMP}/sfx", bed_gain=MUSIC_GAIN, total=total, bed_fn=SFX.music_bed(MUSIC))

    cw, ch = int(W / ZOOM), int(H / ZOOM)
    cx = min(max(FACE[0] - cw // 2, 0), W - cw)
    cy = min(max(FACE[1] - int(ch * 0.40), 0), H - ch)
    close_on = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in close)
    inputs = ["-i", B.CLIP, "-i", audio]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,split=2[m0][c0]",
            f"[m0]scale=w='trunc({W}*(1+0.04*t/{total:.2f})/2)*2':h='trunc({H}*(1+0.04*t/{total:.2f})/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3'[med]",
            f"[c0]crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}[close]",
            f"[med][close]overlay=0:0:enable='{close_on}'[v0]"]
    prev, n = "[v0]", 2
    for i, (img, t0, dur) in enumerate(brolls):
        inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", f"{IMG}/{img}.png"]
        filt.append(N.broll_filter(n, t0, dur, f"b{i}"))
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass[vb{i}]")
        prev, n = f"[vb{i}]", n + 1
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        N.render_any(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{B.CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, len(subs), "субтитров, крупные:", [(round(a, 1), round(b, 1)) for a, b in close])


if __name__ == "__main__":
    main()
