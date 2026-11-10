"""Серия «Представь: у тебя 0 ₽ и 30 дней», серия 2 «День второй: лёгкие деньги».

Тот же стиль и движок, что у серии 1 (`build_z30_01.py`): кадры gpt-image-2 «Ночной город» с медленными
наездами, игровая панель «ДЕНЬ 2/30 · БАЛАНС», карточки правил с состояниями, сообщения-«пузыри» от
покупателя, красная вспышка и тряска на ловушке, крупные субтитры с салатовым словом.

Входы: scratch/z30/ep2-trim.mp3, scratch/z30-ep2-whisper.json, scratch/img/z30e2_*.png,
scratch/music/z30-music.wav. Выход: render/landing/z30-02-9x16.mp4.
"""
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_z30_01 as Z  # noqa: E402
import sfx as SFX  # noqa: E402

ROOT = Z.ROOT
Z.AUDIO = f"{ROOT}/scratch/z30/ep2-trim.mp3"
Z.WHISPER = f"{ROOT}/scratch/z30-ep2-whisper.json"
Z.SCEN = f"{ROOT}/docs/scenarios/zero-30/ep02.md"
Z.OUT = f"{ROOT}/render/landing/z30-02-9x16.mp4"
Z.TMP = f"{ROOT}/render/landing/.z30-02"
W, H, F, rbox, save = Z.W, Z.H, Z.F, Z.rbox, Z.save
LIME, RED, YEL, WHITE, BG1 = Z.LIME, Z.RED, Z.YEL, Z.WHITE, Z.BG1


def hud(name, balance, red=False):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 150, 262, 930, 372
    rbox(d, (x0, y0 + 6, x1, y1 + 6), 26, (0, 0, 0, 110))
    rbox(d, (x0, y0, x1, y1), 26, (0x1B, 0x19, 0x26, 235), outline=(0x55, 0x50, 0x70, 255), width=3)
    d.rounded_rectangle((x0 + 30, y0 + 30, x0 + 86, y0 + 80), 10, fill=(0x55, 0x50, 0x70, 255))
    d.rounded_rectangle((x0 + 62, y0 + 44, x0 + 92, y0 + 66), 6, fill=YEL)
    d.text((x0 + 112, (y0 + y1) / 2), "ДЕНЬ 2/30", font=F(44), fill=WHITE, anchor="lm")
    mid = x0 + 450
    d.line((mid, y0 + 22, mid, y1 - 22), fill=(0x55, 0x50, 0x70, 255), width=3)
    d.text((mid + 30, y0 + 30), "БАЛАНС", font=F(24, False), fill=(0xB8, 0xB2, 0xCC), anchor="lm")
    d.text((mid + 30, y0 + 72), balance, font=F(46), fill=RED if red else LIME, anchor="lm")
    return save(im, name)


def message(name, who, text, warn=False, top=430):
    """Сообщение в мессенджере: аватар-кружок, имя, текст; warn — красная рамка-предупреждение."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tf = F(46)
    lines = Z.wrap(d, text, tf, 700)
    h = 110 + 58 * len(lines) + 30
    x0, x1 = 100, 980
    rbox(d, (x0, top + 8, x1, top + h + 8), 34, (0, 0, 0, 140))
    rbox(d, (x0, top, x1, top + h), 34, (0xF4, 0xF2, 0xF8, 250), outline=RED if warn else None, width=8 if warn else 0)
    d.ellipse((x0 + 30, top + 30, x0 + 100, top + 100), fill=(0x55, 0x50, 0x70))
    d.text((x0 + 65, top + 65), who[:1], font=F(40), fill=WHITE, anchor="mm")
    d.text((x0 + 124, top + 65), who, font=F(36), fill=(0x6B, 0x67, 0x80), anchor="lm")
    y = top + 120
    for ln in lines:
        d.text((x0 + 124, y + 26), ln, font=tf, fill=BG1, anchor="lm")
        y += 58
    assert top >= 400 and top + h + 8 <= 1150, (name, top, h)
    return save(im, name)


def main():
    shutil.rmtree(Z.TMP, ignore_errors=True)
    os.makedirs(Z.TMP)
    Z.WORDS = Z.timed()
    at = Z.at
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  Z.AUDIO], capture_output=True, text=True).stdout)
    t_minus = at("Минус триста")
    t_offer = at("А сегодня")
    t_q1 = at("Вопрос только")
    t_watch = at("Досмотри")
    t_day = at("День второй")
    t_r4 = at("Правило номер четыре")
    t_bank = at("Открываешь банк")
    t_three = at("Ещё три подписки")
    t_cancel = at("Отменяешь все")
    t_r5 = at("Правило номер пять")
    t_hours = at("Четыре часа")
    t_cash = at("И вот")
    t_plus = at("Баланс снова")
    t_eve = at("Шесть вечера")
    t_msg = at("Беру вашу")
    t_luck = at("Удача правда")
    t_link = at("Оплачу через")
    t_stop = at("Стоп")
    t_fake = at("За этой ссылкой")
    t_trap = at("Вот она")
    t_rule = at("Продаёшь")
    t_block = at("Ты блокируешь")
    t_real = at("Велосипед ещё")
    t_closed = at("День второй закрыт")
    t_tom = at("Но завтра")
    t_q = at("Возьмёшь трубку")
    t_soon = at("День третий")
    print({k: round(v, 2) for k, v in locals().items() if k.startswith("t_")})

    plan = [
        ("z30e2_morning", 0.0, (1.0, 1.08), 0.0, 0.5),
        ("z30e2_hook", t_offer - 0.1, (1.0, 1.10), 0.0, 0.5),
        ("z30e2_morning", t_day - 0.1, (1.08, 1.0), 0.5, 0.55),
        ("z30e2_subs", t_bank - 0.1, (1.0, 1.10), 0.0, 0.5),
        ("z30e2_boxes", t_r5 - 0.1, (1.0, 1.08), -0.6, 0.5),
        ("z30e2_cash", t_cash - 0.1, (1.08, 1.0), 0.0, 0.5),
        ("z30e2_message", t_eve - 0.1, (1.0, 1.08), 0.0, 0.5),
        ("z30e2_hook", t_fake - 0.1, (1.0, 1.12), 0.0, 0.5, True),
        ("z30e2_bike", t_block - 0.1, (1.0, 1.08), 0.6, 0.5),
        ("z30e2_call", t_tom - 0.15, (1.0, 1.12), 0.0, 0.5),
    ]
    starts = [p[1] for p in plan] + [total]
    clips = [Z.scene_clip(i, p[0], starts[i + 1] - p[1] + 0.3, *p[2:]) for i, p in enumerate(plan)]
    inputs, fc, last = [], [], "[0:v]"
    for c in clips:
        inputs += ["-i", c]
    for i in range(1, len(clips)):
        off = starts[i] - 0.15
        fc.append(f"{last}[{i}:v]xfade=transition=fade:duration=0.3:offset={off:.3f}[x{i}]")
        last = f"[x{i}]"
    bgv = f"{Z.TMP}/bg.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", last,
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", bgv], check=True)

    card, end_card, flash = Z.card, Z.end_card, Z.flash
    ov = []
    ov.append((hud("hud0", "−399 ₽", red=True), 0.3, t_plus + 0.2, 0.3))
    ov.append((hud("hud1", "1 101 ₽"), t_plus + 0.2, total, 0.0))
    ov.append((card("offer", "СЕГОДНЯ", "Тебе предложат деньги", "3 000 ₽", YEL, kcol=YEL), t_offer + 0.4, t_watch - 0.05, 0.2))
    ov.append((card("trap0", "!", "Эта ошибка стоит всех денег на карте", kcol=RED), t_watch, t_day - 0.1, 0.2))
    ov.append((card("day", "08:00", "День второй"), t_day, t_r4 - 0.05, 0.2))
    ov.append((card("r4a", "ПРАВИЛО 4", "Найди, кто тянет деньги"), t_r4, t_three, 0.2))
    ov.append((card("r4b", "ПРАВИЛО 4", "Найди, кто тянет деньги", "Ещё 3 подписки", RED), t_three, t_cancel, 0.0))
    ov.append((card("r4c", "ПРАВИЛО 4", "Найди, кто тянет деньги", "+1 200 ₽ в месяц сохранено"), t_cancel, t_r5 - 0.1, 0.0))
    ov.append((card("r5a", "ПРАВИЛО 5", "Первые деньги ближе, чем кажется"), t_r5, t_cash, 0.2))
    ov.append((card("r5b", "ПРАВИЛО 5", "Первые деньги ближе, чем кажется", "+1 500 ₽ наличными"), t_cash, t_eve - 0.1, 0.0))
    ov.append((message("msg1", "Покупатель", "Беру вашу куртку за 3 000 ₽. Без торга!"), t_msg, t_link - 0.05, 0.15))
    ov.append((message("msg2", "Покупатель", "Оплачу через доставку. Перейдите по ссылке и введите данные карты",
                       warn=True), t_link, t_fake - 0.1, 0.0))
    ov.append((card("trap2", "ЛОВУШКА №2", "Фальшивый покупатель", kcol=RED), t_fake, t_rule - 0.05, 0.0))
    ov.append((card("rule", "ПРАВИЛО 6", "Лично и наличными. Никаких ссылок"), t_rule, t_block - 0.1, 0.2))
    ov.append((message("msg3", "Сосед по району", "Велосипед ещё продаёте? Приду завтра, с наличными"), t_real,
               t_closed - 0.1, 0.15))
    ov.append((card("closed", "ДЕНЬ 2", "Закрыт", "1 101 ₽"), t_closed, t_tom - 0.05, 0.2))
    ov.append((card("call", "09:00", "Звонит «служба безопасности банка»", kcol=RED), t_tom + 0.6, t_q - 0.05, 0.2))
    ov.append((end_card("end1", "Возьмёшь трубку?", "Пиши в комментариях"), t_q, t_soon - 0.05, 0.2))
    ov.append((end_card("end2", "День третий —", "уже скоро", YEL), t_soon, total, 0.2))
    ov.append((flash("red", RED, 110), t_stop, t_stop + 0.35, 0.0))

    subs = Z.B.chunks(Z.WORDS, total)
    subs = [s for s in subs if s["t0"] < t_q - 0.05]
    for k, s in enumerate(subs):
        ov.append((Z.subtitle(f"s{k}", s["text"], Z.key_of(s["text"])), s["t0"], s["t1"], 0.0))

    cards_t = sorted((a, b) for (p, _x, _y), a, b, _ in ov
                     if os.path.basename(p)[:1] not in "sh" and "red" not in p)
    for (a0, a1), (b0, b1) in zip(cards_t, cards_t[1:]):
        assert b0 >= a1 - 0.05, ("карточки наложились", a0, a1, b0, b1)
    for (p, _x, _y), a, b, _ in ov:
        if os.path.basename(p)[:1] not in "sh":
            assert b - a >= 1.5 or "red" in p, ("элемент мелькает", p, a, b)

    inputs = ["-i", bgv]
    fc = []
    sh0, sh1 = t_stop, t_stop + 0.7
    fc.append(f"[0:v]scale=1120:1992,crop={W}:{H}:x='20+if(between(t,{sh0},{sh1}),14*sin(t*70),0)':"
              f"y='36+if(between(t,{sh0},{sh1}),10*cos(t*55),0)'[v0]")
    last = "[v0]"
    for i, ((p, ox, oy), a, b, fin) in enumerate(ov):
        inputs += ["-loop", "1", "-t", f"{total:.3f}", "-i", p]
        src = f"[{i + 1}:v]format=rgba"
        if fin:
            src += f",fade=in:st={a:.3f}:d={fin}:alpha=1"
        fc.append(src + f"[o{i}]")
        fc.append(f"{last}[o{i}]overlay={ox}:{oy}:enable='gte(t,{a:.3f})*lt(t,{b:.3f})'[v{i + 1}]")
        last = f"[v{i + 1}]"

    ev = [(t_minus, "hit", 0.5), (t_offer + 0.4, "ding", 0.45), (t_watch, "riser", 0.35), (t_day, "whoosh", 0.4),
          (t_r4, "pop", 0.5), (t_three, "stamp", 0.45), (t_cancel, "ding", 0.4), (t_r5, "pop", 0.5),
          (t_cash, "chime", 0.45), (t_eve, "whoosh", 0.3), (t_msg, "beep", 0.5), (t_link, "beep", 0.45),
          (t_stop - 0.5, "riser", 0.4), (t_stop, "glitch", 0.55), (t_stop, "hit", 0.6), (t_trap, "stamp", 0.55),
          (t_rule, "pop", 0.5), (t_real, "beep", 0.45), (t_closed, "ding", 0.45), (t_tom, "bass", 0.6),
          (t_tom + 0.6, "ring", 0.4), (t_q, "pop", 0.5), (t_soon, "chime", 0.4)]
    mixed = SFX.mix(Z.AUDIO, ev, f"{Z.TMP}/mix.wav", f"{Z.TMP}/sfx", bed_gain=0.16, total=total,
                    bed_fn=SFX.music_bed(Z.MUSIC))
    inputs += ["-i", mixed]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
                    "-map", last, "-map", f"{len(ov) + 1}:a", "-t", f"{total:.3f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", Z.OUT],
                   check=True)
    print(Z.OUT, round(total, 1), "c,", len(subs), "субтитров")


if __name__ == "__main__":
    main()
