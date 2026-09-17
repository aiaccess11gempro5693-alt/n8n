import json
from fontTools.ttLib import TTFont

import os
R = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = f"{R}/fonts/Inter-Bold.otf"
FONTSIZE = 40
LINE_HEIGHT = 54
os.makedirs(f"{R}/text", exist_ok=True)

# Плашка ФИКСИРОВАННОГО размера/позиции на ВСЕХ сценах (не подгоняется
# по ширине под конкретный текст, как было в v11/v12 — см.
# docs/design-system.md, п.3). В Подходе A ширина была подобрана так,
# чтобы не доходить до PIP-угла аватара — в Подходе B PIP больше нет
# (аватар всегда на весь кадр, иконки по бокам оканчиваются выше плашки
# по Y), поэтому по прямому запросу плашка теперь ПО ЦЕНТРУ экрана
# (15.09.2026), а не прижата влево.
PANEL_W = 1300
PANEL_X = (1920 - PANEL_W) // 2
PANEL_Y = 900
PANEL_H = 150
ACCENT_BAR_W = 5
PAD_LEFT = 30
PAD_RIGHT = 26
PAD_TOP = 24
TX = PANEL_X + ACCENT_BAR_W + PAD_LEFT
TY0 = PANEL_Y + PAD_TOP
MAX_TEXT_W = PANEL_W - ACCENT_BAR_W - PAD_LEFT - PAD_RIGHT

font = TTFont(FONT_PATH)
cmap = font.getBestCmap()
hmtx = font["hmtx"]
upm = font["head"].unitsPerEm

def glyph_width(ch):
    name = cmap.get(ord(ch))
    if name is None:
        return None
    aw, _lsb = hmtx[name]
    return aw * FONTSIZE / upm

def text_width(s):
    total = 0.0
    for ch in s:
        w = glyph_width(ch)
        if w is None:
            print(f"WARNING: glyph missing for {ch!r} (U+{ord(ch):04X})")
            w = FONTSIZE * 0.55
        total += w
    return total

SPACE_W = text_width(" ")

# Полные дословные реплики диктора (источник — docs/scenario-4-test-video.md,
# "Текст диктора" по сценам) — ИСПРАВЛЕНИЕ 14.09.2026: раньше на экране
# показывался только короткий пересказ фразы, а не то, что реально
# произносит аватар целиком. Теперь субтитры — это ВСЯ реплика, разбитая
# на последовательные чанки по ≤2 строки (см. docs/design-system.md, п.3).
NARRATION = {
    1: 'Здравствуйте. "Иммунитет" — пожалуй, одно из самых популярных слов в современной аптеке. Люди слышат его в рекламе, читают в интернете, обсуждают с друзьями. И приходят к вам с ощущением, что знают, чего хотят.',
    2: 'Но за этим уверенным запросом почти всегда стоит что-то конкретное — то, что человек пока не сформулировал. И именно фармацевт помогает добраться до сути.',
    3: 'Итак, покупатель говорит: "Дайте что-нибудь для иммунитета". Что он имеет в виду? Возможно, он болеет каждую осень и хочет это изменить. Возможно, только недавно перенёс ОРВИ и чувствует слабость. Возможно, просто устал и решил, что виноват "плохой иммунитет". А возможно, он уже принимает три разных БАДа и хочет добавить четвёртый.',
    4: 'Каждая из этих ситуаций требует разного ответа. И только уточнив запрос, вы сможете дать рекомендацию, которая реально поможет, а не просто "что-то от иммунитета".',
    5: 'Помогут несколько простых вопросов: что именно вас беспокоит — частые простуды, постоянная усталость, долгое восстановление после болезни? Как давно вы замечаете это состояние? Принимаете ли сейчас какие-то витамины, добавки или препараты? Есть ли хронические заболевания?',
    6: 'Эти вопросы не просто помогают подобрать препарат — они защищают покупателя. Например, если человек уже пьёт поливитаминный комплекс с высокой дозой витамина С, добавлять ещё один иммуномодулятор может быть излишним. А тому, кто только вышел из болезни, нужна восстановительная поддержка, а не стимуляция.',
    7: 'Когда покупатель слышит такие вопросы, он понимает: здесь не просто продают — здесь думают о его здоровье. Это ощущение бесценно.',
    8: 'Иммунитет — это не один препарат. Это системная забота. И вы — часть этой системы. Спасибо, что подходите к этому серьёзно.',
}

# Реальная длительность аватар-клипа каждой сцены (ffprobe на
# /tmp/final-scenes/scene-N.mp4) — субтитры растягиваются на ВСЮ эту
# длительность, а не только на время короткой фразы, как раньше.
DURATIONS = {1: 16.002, 2: 9.408, 3: 25.056, 4: 11.88, 5: 21.96, 6: 20.84, 7: 9.504, 8: 8.663}

MIN_CHAR_WEIGHT = 2  # пол не даёт пустым/однобуквенным словам почти нулевую длительность

def wrap_into_chunks(words):
    """Жадный перенос слов на строки (<=2 строки на чанк), новый чанк —
    когда третья строка не помещается. Возвращает список чанков, чанк =
    список строк, строка = список слов."""
    chunks = []
    cur_lines = [[]]
    cur_w = 0.0
    for word in words:
        w_w = text_width(word)
        extra = (SPACE_W if cur_lines[-1] else 0.0) + w_w
        if cur_w + extra <= MAX_TEXT_W:
            cur_lines[-1].append(word)
            cur_w += extra
        else:
            if len(cur_lines) < 2:
                cur_lines.append([word])
                cur_w = w_w
            else:
                chunks.append(cur_lines)
                cur_lines = [[word]]
                cur_w = w_w
    if any(cur_lines):
        chunks.append(cur_lines)
    return chunks

manifest = {
    "panel": {
        "x": PANEL_X, "y": PANEL_Y, "w": PANEL_W, "h": PANEL_H,
        "accent_bar_w": ACCENT_BAR_W, "tx": TX, "ty0": TY0, "line_height": LINE_HEIGHT,
    },
    "scenes": {},
}

for n, text in NARRATION.items():
    words = text.split(" ")
    chunks = wrap_into_chunks(words)
    chunk_lens = []
    for lines in chunks:
        flat = [w for line in lines for w in line]
        chunk_lens.append(len(" ".join(flat)))
    total_len = sum(chunk_lens) or 1
    duration = DURATIONS[n]

    scene_chunks = []
    t_cursor = 0.0
    for ci, lines in enumerate(chunks):
        chunk_dur = duration * chunk_lens[ci] / total_len
        chunk_start = t_cursor
        chunk_end = chunk_start + chunk_dur
        t_cursor = chunk_end

        # 15.09.2026: текст внутри плашки теперь по-настоящему ЦЕНТРИРОВАН
        # построчно (раньше плашка была центрирована на экране, а текст
        # внутри неё всё равно был прижат к левому краю — по прямой
        # жалобе "плашка по центру, но текст внутри тоже должен быть по
        # центру"). Раньше серый слой рисовался ОДНИМ multiline-вызовом
        # drawtext с фиксированным x — у ffmpeg drawtext нет built-in
        # центрирования для multiline-блока с разной длиной строк, поэтому
        # теперь каждая строка чанка — ОТДЕЛЬНЫЙ файл + свой x, вычисленный
        # так, чтобы центрировать именно эту строку в MAX_TEXT_W. Слова
        # (для коралловой crop-подсветки) используют ТЕ ЖЕ центрированные
        # x — иначе подсветка разъедется с центрированным серым текстом.
        line_files = []
        for li, line in enumerate(lines):
            line_text = " ".join(line)
            line_w = text_width(line_text)
            center_offset = max(0.0, (MAX_TEXT_W - line_w) / 2)
            line_path = f"{R}/text/{n}-c{ci+1}-line{li+1}.txt"
            with open(line_path, "w", encoding="utf-8") as f:
                f.write(line_text)
            line_files.append({"file": line_path, "x_offset": round(center_offset, 1)})

        # слова чанка с их (line_idx, x_offset ОТ НАЧАЛА СТРОКИ ПОСЛЕ
        # ЦЕНТРИРОВАНИЯ) и пропорциональным таймингом внутри чанка (по
        # длине слова символами, с полом MIN_CHAR_WEIGHT).
        flat_words = []
        for li, line in enumerate(lines):
            x = line_files[li]["x_offset"]
            for wi, w in enumerate(line):
                if wi > 0:
                    x += SPACE_W
                flat_words.append({"text": w, "line": li, "x": round(x, 1), "width": round(text_width(w), 1)})
                x += text_width(w)

        weights = [max(MIN_CHAR_WEIGHT, len(w["text"])) for w in flat_words]
        total_w = sum(weights) or 1
        w_cursor = chunk_start
        for wi, (w, weight) in enumerate(zip(flat_words, weights)):
            w_dur = chunk_dur * weight / total_w
            w["start"] = round(w_cursor, 3)
            w["end"] = round(w_cursor + w_dur, 3)
            w_cursor += w_dur

        scene_chunks.append({
            "start": round(chunk_start, 3),
            "end": round(chunk_end, 3),
            "line_files": line_files,
            "n_lines": len(lines),
            "words": flat_words,
        })

    manifest["scenes"][n] = {"duration": duration, "chunks": scene_chunks}
    print(f"scene {n}: {len(chunks)} chunk(s), {len(words)} words, {duration}s")

with open(f"{R}/word_layout.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print("written word_layout.json")
