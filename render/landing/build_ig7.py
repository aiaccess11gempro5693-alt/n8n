"""Reels №7 «36 вопросов» — формат «документальное интервью»: только ведущая и субтитры.

Как в референсе instagram.com/reel/DewxUO9q7FU: склейки крупный ↔ средний план на каждой
фразе, субтитры курсивом с засечками (PT Serif Italic) на белой плашке — произнесённые
слова чёрные, ещё не сказанные — серые. Без графики и звуков. Всё в безопасной зоне 250–1500.

python3 render/landing/build_ig7.py   →  render/landing/ig7-9x16.mp4
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ig6 as B   # выравнивание слов по whisper и нарезка фраз — общие

ROOT = B.ROOT
B.SCEN = f"{ROOT}/docs/scenarios/insta-7-36-questions.md"
B.WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig7-victoria-whisper.json")
AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig7-full-trim.mp3")
CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig7-host.mp4")
OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig7-9x16.mp4")
TMP = f"{ROOT}/render/landing/.ig7"
FONT = f"{ROOT}/render/fonts/PTSerif-Italic.ttf"
W, H = 1080, 1920
SIZE, PADX, PADY = 54, 22, 12
CY = 1180                   # центр плашки субтитра
INK, GREY = (20, 20, 20), (165, 165, 165)
FACE = (540, 560)           # центр лица в кадре 1080×1920 (для крупного плана)
ZOOM = 1.45
B.MAXC = 26
B.NUMS = {"сорок": "45", "тридцать": "36"}


def numfix():
    """whisper пишет числа цифрами — сопоставляем первое слово числительного с цифрой."""
    orig = B.timed_words

    def tw():
        import difflib
        ws = json.load(open(B.WHISPER))["words"]
        text = B.clean_words()
        a = [B.NUMS.get(B.norm(w), B.norm(w)) for w in text]
        b = [B.norm(x["word"]) for x in ws]
        times = [None] * len(text)
        for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = ws[blk.b + k]["start"]
        for i, t in enumerate(times):
            if t is None:
                prev = next((times[j] for j in range(i - 1, -1, -1) if times[j] is not None), 0.0)
                nxt = next((times[j] for j in range(i + 1, len(times)) if times[j] is not None), prev + 0.4)
                times[i] = prev + (nxt - prev) * 0.5
        return list(zip(text, times)), ws[-1]["end"]
    B.timed_words = tw
    return orig


def chunk_words(words, total):
    """Чанки как в build_ig6, но со словами и их таймингами (для пословного проявления)."""
    subs = B.chunks(words, total)
    out, i = [], 0
    flat = [(w, t) for w, t in words if w not in ("—", "–")]
    for s in subs:
        n = len(s["text"].split())
        out.append({"words": flat[i:i + n], "t0": s["t0"], "t1": s["t1"]})
        i += n
    return out


def render_state(path, words, k):
    """Плашка с фразой: первые k слов чёрные, остальные серые."""
    f = ImageFont.truetype(FONT, SIZE)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    text = " ".join(words).rstrip(",:")
    tw = d0.textlength(text, font=f)
    asc, desc = f.getmetrics()
    bw, bh = int(tw + PADX * 2), asc + desc + PADY * 2
    im = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = (W - bw) // 2, (200 - bh) // 2
    d.rectangle([x0, y0, x0 + bw, y0 + bh], fill=(255, 255, 255, 245))
    x = x0 + PADX
    shown = text.split()
    for i, w in enumerate(shown):
        d.text((x, y0 + PADY), w, font=f, fill=INK if i < k else GREY)
        x += d.textlength(w + " ", font=f)
    im.save(path)
    assert bw <= W - 60, f"плашка шире кадра: {text}"
    assert 250 <= CY - bh / 2 and CY + bh / 2 <= 1500


def shots(words, total):
    """Смена плана на начале каждого предложения: крупный / средний по очереди (начинаем с крупного)."""
    starts, new = [0.0], False
    for w, t in words:
        if new and t - starts[-1] > 2.5:
            starts.append(t)
        new = bool(re.search(r"[.!?…]»?$", w))
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else total
        out.append((s, e, "close" if i % 2 == 0 else "medium"))
    out[-1] = (out[-1][0], out[-1][1], "medium")   # призыв — средним планом
    return out


def main():
    os.makedirs(TMP, exist_ok=True)
    numfix()
    words, last = B.timed_words()
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", AUDIO]).decode())
    subs = chunk_words(words, min(total, last + 0.6))
    plan = shots(words, total)
    json.dump({"subs": [{"text": " ".join(w for w, _ in s["words"]), "t0": s["t0"], "t1": s["t1"]} for s in subs],
               "shots": plan}, open(f"{TMP}/plan.json", "w"), ensure_ascii=False, indent=1)

    cw, ch = int(W / ZOOM), int(H / ZOOM)
    cx = min(max(FACE[0] - cw // 2, 0), W - cw)
    cy = min(max(FACE[1] - int(ch * 0.42), 0), H - ch)
    filt = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,split=2[med][c0]",
            f"[c0]crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}[close]"]
    close_on = "+".join(f"between(t,{s:.3f},{e - 0.001:.3f})" for s, e, k in plan if k == "close")
    filt.append(f"[med][close]overlay=0:0:enable='{close_on or 0}'[v0]")
    inputs, prev, n = ["-i", CLIP, "-i", AUDIO], "[v0]", 0
    for si, s in enumerate(subs):
        ws = s["words"]
        for k in range(1, len(ws) + 1):
            t0 = s["t0"] if k == 1 else ws[k - 1][1]
            t1 = ws[k][1] if k < len(ws) else s["t1"]
            if t1 - t0 < 0.02:
                continue
            p = f"{TMP}/s{si:03d}_{k:02d}.png"
            render_state(p, [w for w, _ in ws], k)
            inputs += ["-i", p]
            n += 1
            filt.append(f"{prev}[{n + 1}:v]overlay=0:{CY - 100}:enable='gte(t,{t0:.3f})*lt(t,{t1:.3f})'[v{n}]")
            prev = f"[v{n}]"
    filt.append("[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    open(f"{TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{TMP}/graph.txt",
                    "-map", prev, "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT],
                   check=True)
    print(OUT, len(subs), "фраз,", n, "состояний,", len(plan), "планов")


if __name__ == "__main__":
    main()
