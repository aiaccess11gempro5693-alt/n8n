"""Reels №6 «Прайм-эра женщины» — формат «подкаст»: только ведущая и белые субтитры.

Без графики, картинок и звуков (по просьбе пользователя, как в референсе
instagram.com/reel/De1gftquORP). Субтитры — короткие фразы по 2–4 слова, белый
Montserrat ExtraBold с чёрной обводкой, в безопасной зоне 250–1500 px.

python3 render/landing/build_ig6.py   →  render/landing/ig6-9x16.mp4
"""
import difflib
import json
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCEN = f"{ROOT}/docs/scenarios/insta-6-prime.md"
AUDIO = os.environ.get("AUDIO", f"{ROOT}/scratch/ig6-full-trim.mp3")
WHISPER = os.environ.get("WHISPER", f"{ROOT}/scratch/ig6-ana-whisper.json")
CLIP = os.environ.get("CLIP", f"{ROOT}/scratch/ig6-host.mp4")
OUT = os.environ.get("OUT", f"{ROOT}/render/landing/ig6-9x16.mp4")
TMP = f"{ROOT}/render/landing/.ig6"
FONT = f"{ROOT}/render/fonts/Montserrat-ExtraBold.ttf"
W, H = 1080, 1920
SIZE, STROKE, MAXW = 66, 6, 900
CY = 1270            # центр субтитра; низ строки не ниже 1500 (безопасная зона)
MAXC = 22            # символов в чанке


def clean_words():
    s = open(SCEN, encoding="utf-8").read().split("## Разметка для eleven_v3")[1]
    s = re.sub(r"\[[^\]]*\]", " ", s).replace("Пока-пока!", "")
    return s.split()


def norm(w):
    return re.sub(r"[^\wё]", "", w.lower().replace("ё", "е"))


def timed_words():
    ws = json.load(open(WHISPER))["words"]
    text = clean_words()
    nums = {"двадцать": "25", "сорока": "40", "пятидесяти": "55"}
    a = [nums.get(norm(w), norm(w)) for w in text]
    b = [norm(x["word"]) for x in ws]
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


# после этих слов строку не рвём (предлоги, союзы, первая часть числительного)
NOBREAK = {"в", "во", "к", "ко", "с", "со", "и", "а", "но", "за", "на", "до", "не", "по", "из", "от", "у", "о",
           "об", "для", "что", "как", "друг", "сорок", "тридцать", "двадцать", "пятьдесят", "это", "эти", "все"}


def split_even(ph, n):
    """Разбить фразу на n кусков с минимальной длиной самого длинного куска
    (разрыв после предлога/союза/начала числительного — штраф)."""
    best = None

    def rec(i, k, acc):
        nonlocal best
        if k == 1:
            parts = acc + [ph[i:]]
            m = max(len(" ".join(w for w, _ in g)) for g in parts)
            m += sum(100 for g in parts[:-1] if norm(g[-1][0]) in NOBREAK)
            if best is None or m < best[0]:
                best = (m, parts)
            return
        for j in range(i + 1, len(ph) - k + 2):
            rec(j, k - 1, acc + [ph[i:j]])
    rec(0, n, [])
    return best[1]


def chunks(words, total):
    # фраза — до знака препинания или тире; длинная фраза делится на равные по длине
    # куски; чанк не переходит через конец предложения и не оставляет одинокое слово
    phrases, cur, dashed = [], [], set()
    for w, t in words:
        if w in ("—", "–"):
            if cur:
                phrases.append(cur)
                dashed.add(id(cur))   # фраза закончилась тире — к ней не приклеиваем следующую
            cur = []
            continue
        cur.append((w, t))
        if re.search(r"[.!?…:,»]$", w):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    merged = []
    for ph in phrases:   # короткая фраза присоединяется к предыдущей, если влезает
        ln = lambda g: len(" ".join(w for w, _ in g))
        if merged and ln(ph) < 10 and id(merged[-1]) not in dashed and not re.search(r"[.!?…]»?$", merged[-1][-1][0]) and ln(merged[-1] + ph) <= MAXC:
            merged[-1] += ph
        else:
            merged.append(ph)
    out = []
    for ph in merged:
        n = min(-(-len(" ".join(w for w, _ in ph)) // MAXC), len(ph))
        out += split_even(ph, n)
    # чанк короче ~0.65 с внутри предложения склеиваем со следующим (≤ 28 символов)
    i = 0
    while i < len(out) - 1:
        dur = out[i + 1][0][1] - out[i][0][1]
        txt = " ".join(w for w, _ in out[i] + out[i + 1])
        if dur < 0.65 and not re.search(r"[.!?…]»?$", out[i][-1][0]) and len(txt) <= MAXC + 6:
            out[i] += out.pop(i + 1)
        else:
            i += 1
    # хвост предложения короче 0.5 с — к предыдущему куску того же предложения
    i = 1
    while i < len(out):
        end = out[i + 1][0][1] if i + 1 < len(out) else total
        txt = " ".join(w for w, _ in out[i - 1] + out[i])
        if end - out[i][0][1] < 0.5 and not re.search(r"[.!?…]»?$", out[i - 1][-1][0]) and len(txt) <= MAXC + 6:
            out[i - 1] += out.pop(i)
        else:
            i += 1
    res = []
    for i, ch in enumerate(out):
        t1 = out[i + 1][0][1] if i + 1 < len(out) else total
        res.append({"text": " ".join(w for w, _ in ch).rstrip(",:"), "t0": ch[0][1], "t1": t1})
    res[0]["t0"] = 0.0
    return res


def render_sub(path, text):
    f = ImageFont.truetype(FONT, SIZE)
    im = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    words, lines, cur = text.split(), [], ""
    for w in words:
        c = (cur + " " + w).strip()
        if d.textlength(c, font=f) > MAXW and cur:
            lines.append(cur)
            cur = w
        else:
            cur = c
    lines.append(cur)
    lh = SIZE * 1.12
    y = 130 - lh * len(lines) / 2
    for ln in lines:
        d.text((W / 2, y + lh / 2), ln, font=f, fill="white", anchor="mm",
               stroke_width=STROKE, stroke_fill=(0, 0, 0, 235))
        y += lh
    im.save(path)
    assert 250 <= CY - 130 + (130 - lh * len(lines) / 2) and CY + lh * len(lines) / 2 <= 1500


def main():
    os.makedirs(TMP, exist_ok=True)
    words, last = timed_words()
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", AUDIO]).decode())
    subs = chunks(words, min(total, last + 0.6))
    json.dump(subs, open(f"{TMP}/subs.json", "w"), ensure_ascii=False, indent=1)
    inputs, filt, prev = ["-i", CLIP, "-i", AUDIO], [], "[0:v]"
    filt.append(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,format=yuv420p[v0]")
    prev = "[v0]"
    for i, s in enumerate(subs):
        p = f"{TMP}/sub{i:03d}.png"
        render_sub(p, s["text"])
        inputs += ["-i", p]
        filt.append(f"{prev}[{i + 2}:v]overlay=0:{CY - 130}:enable='gte(t,{s['t0']:.3f})*lt(t,{s['t1']:.3f})'[v{i + 1}]")
        prev = f"[v{i + 1}]"
    filt.append("[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    open(f"{TMP}/graph.txt", "w").write(";\n".join(filt))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", f"{TMP}/graph.txt",
                    "-map", prev, "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT],
                   check=True)
    print(OUT, len(subs), "субтитров")


if __name__ == "__main__":
    main()
