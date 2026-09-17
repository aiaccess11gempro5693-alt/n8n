"""
Слой "заголовок главной мысли" — третий текстовый слой поверх видео,
поверх уже отрендеренных сцен (аватар+субтитры из render_scenes.sh,
или аватар+иконки+субтитры из render_icon_scenes.py).

Правило (закреплено 16-17.09.2026, см. docs/design-system.md):
каждая сцена/смысловой блок (1-3 предложения) должен показывать
короткий (2-4 слова) заголовок главной мысли текущего момента —
в левом верхнем углу, пока угол не занят иконкой-стикером (тогда
заголовок гаснет ПЕРЕД первой иконкой и передаёт эту роль подписям
иконок). Заголовок никогда не должен "мелькать" на 1-2 секунды —
либо появляется рано и держится до конца сцены/блока, либо гаснет
заранее, если место понадобится под иконку.

Стиль — тот же pill-бейдж, что и подписи под иконками (см.
pill_gen_all.py): скруглённый бейдж, тень, тёмная обводка, шрифт
Inter-Bold, слегка выезжает снизу при появлении.

Вход: уже отрендеренные $R/scene-N.mp4 (перезаписываются на месте).
Каждая сцена описывается списком из одного или нескольких сегментов
{text, color, start, end}. `end=None` — держать до конца сцены.
Позиция сейчас всегда top-left (x=60,y=60 корпус бейджа) — единственная
зона, которая по построению не занята субтитрами (низ кадра) и не
занята иконками сцен 2/4/5/7/8 (без иконок в левом верхнем углу).
Для сцен 3/6 (иконка ЕСТЬ в левом верхнем углу) headline получает
`end` = момент триггера первой иконки этой сцены.
"""
import json
import os
import subprocess
import sys

R = os.path.dirname(os.path.abspath(__file__))
SCENES_DIR = R  # сцены рендерятся/перезаписываются прямо здесь ($R/scene-N.mp4)
FONT = f"{R}/fonts/Inter-Bold.otf"

sys.path.insert(0, R)
from pill_gen_all import rounded_pill, TEAL, CORAL  # noqa: E402

SLIDE = 30       # px, анимация выезда снизу при появлении
FADE_IN = 0.3    # с, время фейда текста
POP_EASE = 0.35  # с, время анимации выезда бейджа


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    ).stdout.strip()
    return float(out)


def render_headline(scene_n, segments):
    """segments: список [{text, color, start, end_or_None, fs}, ...] в порядке появления."""
    scene_path = f"{SCENES_DIR}/scene-{scene_n}.mp4"
    tmp_out = f"{SCENES_DIR}/scene-{scene_n}-headline-tmp.mp4"
    D = dur(scene_path)

    pill_paths = []
    for i, seg in enumerate(segments):
        name = f"headline-scene{scene_n}-{i+1}"
        meta = rounded_pill(f"{R}/pills/{name}.png", seg["text"], seg["fs"], seg["color"],
                             pad_x=40, pad_y=22)
        pill_paths.append((f"{R}/pills/{name}.png", meta))

    inputs = ["-i", scene_path]
    for p, _ in pill_paths:
        inputs += ["-i", p]

    fc = []
    prev = "0:v"
    for i, (seg, (_, meta)) in enumerate(zip(segments, pill_paths)):
        idx = i + 1
        start = seg["start"]
        end = seg.get("end")
        cond = f"gte(t,{start})" if end is None else f"between(t,{start},{end})"
        pw, ph = meta["pill_w"], meta["pill_h"]
        bx, by = 60, 60  # top-left, фиксированная позиция бейджа-заголовка
        margin = meta["margin"]
        ox, oy = bx - margin, by - margin
        ease = f"max(0,1-(t-{start})/{POP_EASE})"
        nxt = f"h{idx}a"
        fc.append(f"[{prev}][{idx}:v]overlay=x={ox}:y='{oy}-{SLIDE}*{ease}':enable='{cond}'[{nxt}]")
        prev = nxt
        nxt = f"h{idx}b"
        text_esc = seg["text"].replace("'", r"\'").replace(":", r"\:")
        fc.append(
            f"[{prev}]drawtext=fontfile={FONT}:fontcolor=white:fontsize={seg['fs']}:text='{text_esc}':"
            f"shadowcolor=black@0.35:shadowx=1:shadowy=1:"
            f"x={bx}+({pw}-text_w)/2:y='{by}+({ph}-text_h)/2-{SLIDE}*{ease}':"
            f"enable='{cond}':alpha='min((t-{start})/{FADE_IN}\\,1)'[{nxt}]"
        )
        prev = nxt

    filter_complex = ";\n".join(fc)
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", f"[{prev}]", "-map", "0:a", "-t", str(D),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "aac", "-b:a", "160k",
        tmp_out,
    ]
    print(f"=== headline scene {scene_n} ({len(segments)} segment(s)) ===")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FFMPEG STDERR TAIL:\n", r.stderr[-4000:])
        raise SystemExit(f"headline render failed for scene {scene_n}")
    os.replace(tmp_out, scene_path)
    print(f"scene {scene_n} OK -> {scene_path}")


# Тайминги слов ("start" каждого сегмента) взяты из word_layout.json —
# либо начало сцены (0.3с, стандартный небольшой отступ, чтобы не
# конкурировать с самым первым кадром), либо момент начала новой мысли
# в реплике. Значения ниже — конкретно для "Сценарий 4, иммунитет";
# для нового ролика пересчитываются под его собственный word_layout.json
# по тому же принципу (см. docs/design-system.md, раздел "Заголовки").
PLAN = {
    1: [
        # первая мысль: "Иммунитет" — самое популярное слово; вторая: люди
        # приходят с готовым мнением. Второй сегмент меняет headline, а не
        # добавляется поверх первого.
        {"text": "ИММУНИТЕТ", "color": TEAL, "start": 1.12, "end": 6.82, "fs": 50},
        {"text": "Приходят с готовым мнением", "color": TEAL, "start": 6.82, "end": None, "fs": 32},
    ],
    2: [{"text": "Скрытый запрос", "color": TEAL, "start": 0.3, "end": None, "fs": 50}],
    3: [{"text": "Что он имеет в виду?", "color": TEAL, "start": 0.3, "end": 7.0, "fs": 44}],  # гаснет до 1й иконки (t=7.15)
    4: [{"text": "Точный вопрос — точный ответ", "color": CORAL, "start": 0.3, "end": None, "fs": 30}],
    5: [{"text": "Простые вопросы", "color": TEAL, "start": 0.3, "end": None, "fs": 50}],  # иконки только справа, конфликта нет
    6: [{"text": "Вопросы защищают покупателя", "color": CORAL, "start": 0.3, "end": 13.5, "fs": 40}],  # гаснет до 1й иконки (t=13.79)
    7: [{"text": "Доверие, а не продажа", "color": CORAL, "start": 0.3, "end": None, "fs": 44}],
    8: [{"text": "Системная забота", "color": TEAL, "start": 0.3, "end": None, "fs": 50}],
}

if __name__ == "__main__":
    os.makedirs(f"{R}/pills", exist_ok=True)
    for scene_n, segments in PLAN.items():
        render_headline(scene_n, segments)
    print("ALL HEADLINES DONE")
