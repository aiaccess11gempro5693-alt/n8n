"""Общий монтаж рекламных Reels №20–21: ведущий на весь кадр + карточки ad_cards поверх
затемнения + белые субтитры (build_ig6) + крючок (build_ig9) + глитч/наезды + звуки (sfx).

build(cfg):
  cfg["hook"]     — текст крючка (заглавными, «_» — неразрывный пробел), держится первое предложение;
  cfg["cards"]    — [(png, t0, t1, (верх, низ))] — состояния карточек; одно место — смена без угасания;
  cfg["brolls"]   — [(png, t0, dur)] — кинокадры на весь экран (картинка 2:3, наезд);
  cfg["glitch"]   — [(t0, t1)] — RGB-сдвиг и шум;
  cfg["punch"]    — [(t0, t1)] — резкий наезд на лицо ×1.12;
  cfg["sfx"]      — [(t, имя, громкость)];
  cfg["music"], cfg["music_gain"];
  cfg["dim_alpha"] — сила затемнения под карточкой (по умолчанию 0.55);
  cfg["hud"]      — [(png, t0, t1)] — постоянный слой поверх всего (игровая панель), не затемняется.
Проверки: карточки внутри зоны 250–1500 и выше субтитров (низ ≤ 1130), кадры не перекрываются.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B
import build_ig9 as N
import sfx as SFX

SUB_TOP = B.CY - 130          # верх полосы субтитров (1140)
CARD_MAX_BOTTOM = 1500        # на время карточки субтитры скрыты — карточка может уходить ниже
FACE_BOTTOM = 600             # подбородок ведущего: карточки начинаются ниже, лицо всегда видно


def place(png, box, top, scale=1.0, out=None):
    """Перенести нарисованную карточку (полный кадр RGBA) на высоту top с масштабом scale."""
    from PIL import Image
    im = Image.open(png)
    bb = im.getbbox()
    card = im.crop((bb[0], box[0], bb[2], min(im.height, box[1] + 50)))
    if scale != 1.0:
        card = card.resize((round(card.width * scale), round(card.height * scale)), Image.LANCZOS)
    res = Image.new("RGBA", im.size, (0, 0, 0, 0))
    res.alpha_composite(card, ((im.width - card.width) // 2, top))
    res.save(out or png)
    return out or png, (top, top + card.height)


def windows_expr(wins):
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in wins) or "0"


def merge(wins):
    out = []
    for a, b in sorted(wins):
        if out and a <= out[-1][1] + 0.05:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def build(cfg, words, total, subs):
    os.makedirs(B.TMP, exist_ok=True)
    for png, t0, t1, (top, bot) in cfg["cards"]:
        assert FACE_BOTTOM <= top and bot <= CARD_MAX_BOTTOM, f"{png}: карточка {top}–{bot} на лице/вне зоны"
        assert t1 - t0 >= 0.6, f"{png}: держится {t1 - t0:.2f} с — мелькание"
    br = sorted(cfg.get("brolls", []), key=lambda x: x[1])
    for (a, ta, da), (b, tb, _) in zip(br, br[1:]):
        assert ta + da <= tb, f"кадры {a}/{b} перекрываются"
    for png, t0, t1, _ in cfg["cards"]:
        for img, ta, da in br:
            assert t1 <= ta + 0.01 or t0 >= ta + da - 0.01, f"карточка {png} попадает на кадр {img}"
    json.dump({"subs": subs, "cards": [c[:3] for c in cfg["cards"]], "brolls": br},
              open(f"{B.TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    audio = f"{B.TMP}/mix.wav"
    SFX.mix(B.AUDIO, cfg.get("sfx", []), audio, f"{B.TMP}/sfx", bed_gain=cfg.get("music_gain", 0.12),
            total=total, bed_fn=SFX.music_bed(cfg["music"]))

    W, H = B.W, B.H
    punch = windows_expr(cfg.get("punch", []))
    z = f"(1+0.05*t/{total:.2f}+0.12*({punch}))"
    gl = windows_expr(cfg.get("glitch", []))
    dim = windows_expr(merge([(c[1], c[2]) for c in cfg["cards"]]))
    inputs = ["-i", B.CLIP, "-i", audio, "-f", "lavfi", "-t", f"{total:.2f}", "-i", f"color=black:s={W}x{H}:r=30"]
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
            f"tpad=stop_duration=3:stop_mode=clone,"
            f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,"
            f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/3',"
            f"rgbashift=rh=-14:bh=14:gv=6:enable='{gl}',noise=alls=28:allf=t:enable='{gl}',format=yuv420p[v0]",
            f"[2:v]format=rgba,colorchannelmixer=aa={cfg.get('dim_alpha', 0.55)}[dk]",
            f"[v0][dk]overlay=0:0:enable='{dim}'[vd]"]
    prev, n = "[vd]", 3
    for i, (img, t0, dur) in enumerate(br):
        inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", img]
        filt.append(N.broll_filter(n, t0, dur, f"b{i}"))
        filt.append(f"{prev}[b{i}]overlay=0:0:eof_action=pass[vb{i}]")
        prev, n = f"[vb{i}]", n + 1
    for i, (png, t0, t1, _) in enumerate(cfg["cards"]):
        inputs += ["-i", png]
        filt.append(f"{prev}[{n}:v]overlay=0:0:enable='gte(t,{t0:.3f})*lt(t,{t1:.3f})'[c{i}]")
        prev, n = f"[c{i}]", n + 1
    for i, s in enumerate(subs):
        p = f"{B.TMP}/sub{i:03d}.png"
        N.render_any(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{n}:v]overlay=0:{SUB_TOP}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})*not({dim})'[s{i}]")
        prev, n = f"[s{i}]", n + 1
    for i, (png, t0, t1) in enumerate(cfg.get("hud", [])):
        inputs += ["-i", png]
        filt.append(f"{prev}[{n}:v]overlay=0:0:enable='gte(t,{t0:.3f})*lt(t,{t1:.3f})'[h{i}]")
        prev, n = f"[h{i}]", n + 1
    filt.append(f"{prev}format=yuv420p[vout]")
    open(f"{B.TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{B.TMP}/graph.txt",
                    "-map", "[vout]", "-map", "1:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", B.OUT], check=True)
    print(B.OUT, f"{total:.1f} c,", len(subs), "субтитров,", len(cfg["cards"]), "карточек")


def prepare(spoken, hook):
    """Слова с таймингами, длина дорожки и субтитры с крючком вместо первой фразы."""
    B.clean_words = lambda: spoken.split()
    words, last = B.timed_words()
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", B.AUDIO]).decode())
    subs = N.chunks_with_hook(words, min(total, last + 0.6))
    subs[0]["text"] = hook
    return words, total, subs, N.finder(words)
