"""МЕХАНИЗМ-ДЕМО нового формата "аватар в угол + плашка" (render/corner/)
на сценарии 5. НЕ финальное видео — реальный HeyGen-клип с новым
голосом/сценарием ещё не сгенерирован (mcp__Heygen_MCP__* заблокированы
в этой сессии, см. CLAUDE.md 23.09.2026 (4)). Пока используем:

  - РЕАЛЬНОЕ аудио — scratch/scenario5-full-v1.mp3 (ElevenLabs v3, голос
    "ТЁПЛЫЙ НАСТАВНИК - фарма", реально сгенерировано в этой сессии).
  - ПОДСТАВНОЕ видео — уже закоммиченный scratch/scene1-status-v2.mp4
    (старый Avatar III клип из прошлого сценария, зациклен под длину
    нового аудио) — только чтобы показать механику перехода в угол,
    липсинк заведомо не совпадает с новой репликой.

Цель прогона — проверить сам движок (переход в угол, сдвиг субтитров,
плашка с буллитами, статичные субтитры без караоке), не оценивать
аватара/голос по этому файлу.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from corner import brand_style as S
from corner import geometry as G
from corner import static_captions as CAP
from corner import plashka as P

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(R)
AUDIO = f"{REPO}/scratch/scenario5-full-v1.mp3"
PLACEHOLDER_VIDEO = f"{REPO}/scratch/scene1-status-v2.mp4"
OUT = f"{os.path.dirname(os.path.abspath(__file__))}/scenario5-corner-demo.mp4"

FULL_TEXT = open(f"{REPO}/docs/scenarios/scenario-5-greeting.md", encoding="utf-8").read()
FULL_TEXT = FULL_TEXT.split("[warmly] Здравствуйте.", 1)[1]
FULL_TEXT = "[warmly] Здравствуйте." + FULL_TEXT.split("\n\n---", 1)[0]


def ffprobe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    for line in r.stdout.splitlines():
        if line.startswith("duration="):
            return float(line.split("=", 1)[1])
    raise RuntimeError(f"could not find duration in ffprobe output for {path}")


def main():
    duration = ffprobe_duration(AUDIO)
    print(f"audio duration: {duration:.3f}s")

    # угловая фаза — последние ~13с, где текст говорит про вопросы в
    # конце ролика (смысловой повод показать плашку с буллитами).
    corner_start = round(duration - 13.0, 3)
    corner_t1 = round(corner_start + 0.6, 3)

    timeline = CAP.build_chunk_timeline(FULL_TEXT, duration)

    assets_dir = os.path.dirname(os.path.abspath(__file__))
    card_img, card_w, card_h = P.render_bullet_card(
        "Ваше мнение",
        ["Несколько коротких вопросов", "Это не проверка знаний", "Учтём в следующих роликах"],
    )
    card_path = f"{assets_dir}/_demo_bullet_card.png"
    card_img.save(card_path)
    card_x = G.PLASHKA_ZONE["x0"]
    card_y = G.PLASHKA_ZONE["y0"]

    w_expr, h_expr, x_expr, y_expr = G.transition_exprs(corner_start, corner_t1)

    inputs = [
        "-stream_loop", "-1", "-t", f"{duration:.3f}", "-i", PLACEHOLDER_VIDEO,
        "-i", AUDIO,
        "-f", "lavfi", "-i", f"color=c=0x14141c:s=1920x1080:d={duration:.3f}",
        "-loop", "1", "-t", f"{duration:.3f}", "-i", card_path,
    ]
    fc = []
    fc.append(f"[2:v]format=rgba[bg]")
    fc.append(f"[0:v]scale=w='{w_expr}':h='{h_expr}':eval=frame[av]")
    fc.append(f"[bg][av]overlay=x='{x_expr}':y='{y_expr}':eval=frame[with_av]")

    card_cond = f"between(t,{corner_t1},{duration:.3f})"
    fc.append(f"[with_av][3:v]overlay=x={card_x}:y={card_y}:enable='{card_cond}'[with_card]")

    cap_fc, cap_final = CAP.build_filter("with_card", timeline, corner_start)
    fc += cap_fc

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(fc),
        "-map", f"[{cap_final}]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        OUT,
    ]
    print("running ffmpeg...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDERR TAIL:\n", r.stderr[-4000:])
        raise SystemExit("ffmpeg failed")
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
