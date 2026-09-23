"""Статичные субтитры — БЕЗ караоке-подсветки слов (прямое указание
Олега, 23.09.2026: "сделай субтитры статичными, чтобы не подсвечивались,
никакого пословного эффекта"). Белая плашка, чёрный текст, меняется
целиком по чанкам — в отличие от render/compute_word_layout.py +
build_trend_video.py (старая караоке-система, всё ещё канон для видео
без нового corner-формата), здесь нет per-word crop-подсветки вообще.

Тайминги чанков — приближённые (пропорционально числу символов на общую
длительность аудио), т.к. ElevenLabs TTS-эндпоинт в этом мосте не отдаёт
пословные метки времени (нет alignment/timestamps). Достаточно для
статичного текста (в отличие от караоке, здесь не нужна точность до
слова — только чтобы блок текста не отставал от речи заметно на глаз).
Если позже подключим ElevenLabs `/with-timestamps` или whisper-alignment
— эту функцию можно заменить на точную, остальной pipeline не изменится.
"""
import os
import re
from fontTools.ttLib import TTFont

from . import brand_style as S
from . import geometry as G

FONT_PATH = S.F_CAPTION
FONTSIZE = S.SIZE_CAPTION
LINE_HEIGHT = 54
PAD_LEFT = 30
PAD_RIGHT = 26
PAD_TOP = 24
ACCENT_BAR_W = 5

_font = TTFont(FONT_PATH)
_cmap = _font.getBestCmap()
_hmtx = _font["hmtx"]
_upm = _font["head"].unitsPerEm


def _glyph_width(ch):
    name = _cmap.get(ord(ch))
    if name is None:
        return FONTSIZE * 0.55
    aw, _ = _hmtx[name]
    return aw * FONTSIZE / _upm


def _text_width(s):
    return sum(_glyph_width(ch) for ch in s)


_SPACE_W = _text_width(" ")
_EMOTION_TAG_RE = re.compile(r"\[[^\]]*\]")


def strip_emotion_tags(text):
    """Убирает [warmly]-теги — они инструкция для TTS, не текст для экрана."""
    cleaned = _EMOTION_TAG_RE.sub("", text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    return cleaned.strip()


def wrap_into_chunks(text, max_width):
    words = text.split()
    chunks = []
    cur_lines = [[]]
    cur_w = 0.0
    for word in words:
        w_w = _text_width(word)
        extra = (_SPACE_W if cur_lines[-1] else 0.0) + w_w
        if cur_w + extra <= max_width:
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


def build_chunk_timeline(text, total_duration, panel_w=G.SUBTITLE_W):
    """Возвращает список {lines, start, end} — тайминг пропорционален
    числу символов в чанке (see module docstring)."""
    max_text_w = panel_w - ACCENT_BAR_W - PAD_LEFT - PAD_RIGHT
    clean = strip_emotion_tags(text)
    chunks = wrap_into_chunks(clean, max_text_w)

    weights = [sum(len(w) for line in chunk for w in line) + len(chunk) for chunk in chunks]
    total_weight = sum(weights) or 1
    t = 0.0
    timeline = []
    for chunk, weight in zip(chunks, weights):
        dur = total_duration * weight / total_weight
        timeline.append({"lines": chunk, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur
    if timeline:
        timeline[-1]["end"] = round(total_duration, 3)
    return timeline


def panel_x_for_time(t, corner_start):
    """Панель субтитров смещается влево, когда аватар уже (или ещё)
    в угловой фазе — прямое указание Олега (см. geometry.py)."""
    return G.SUBTITLE_X_CORNER if t >= corner_start else G.SUBTITLE_X_CENTERED


def build_filter(prev_label, timeline, corner_start, panel_color="0xF7F9FBEE",
                  text_color="0x1E2228", accent_color=None, panel=None):
    """Возвращает (filter_complex-строки, финальный label). Рисует
    плашку + текст поверх prev_label. Панель может быть по центру или
    сдвинута (см. panel_x_for_time) — оба варианта прорисовываются с
    enable=between(...), как и раньше в старой системе, просто без
    per-word подсветки."""
    accent_color = accent_color or f"0x{S.BLUE[0]:02X}{S.BLUE[1]:02X}{S.BLUE[2]:02X}"
    fc = []
    prev = prev_label
    # panel=(x, w) — одна фиксированная позиция плашки (сплит-экран)
    phases = ([("fixed", panel[0], panel[1])] if panel else
              [("centered", G.SUBTITLE_X_CENTERED, G.SUBTITLE_W), ("corner", G.SUBTITLE_X_CORNER, G.SUBTITLE_W)])
    for ci, chunk in enumerate(timeline):
        # конец не включительно: на кадре-стыке иначе видны обе фразы —
        # полупрозрачная плашка новой ложится поверх текста старой ("тень")
        cond = f"gte(t,{chunk['start']})*lt(t,{chunk['end']})"
        for phase, x, pw in phases:
            time_cond = {"fixed": "1", "centered": f"lt(t,{corner_start})"}.get(phase, f"gte(t,{corner_start})")
            full_cond = f"({cond})*({time_cond})"
            pn = f"scap_panel_{ci}_{phase}"
            fc.append(
                f"[{prev}]drawbox=x={x}:y={G.SUBTITLE_Y}:w={pw}:h={G.SUBTITLE_H}:"
                f"color={panel_color}:t=fill:enable='{full_cond}'[{pn}]"
            )
            prev = pn
            an = f"scap_accent_{ci}_{phase}"
            fc.append(
                f"[{prev}]drawbox=x={x}:y={G.SUBTITLE_Y}:w={ACCENT_BAR_W}:h={G.SUBTITLE_H}:"
                f"color={accent_color}@1.0:t=fill:enable='{full_cond}'[{an}]"
            )
            prev = an
            for li, line in enumerate(chunk["lines"]):
                line_text = " ".join(line)
                text_w = _text_width(line_text)
                lx = x + ACCENT_BAR_W + (pw - ACCENT_BAR_W - text_w) / 2
                # однострочный чанк — по вертикальному центру плашки
                ly = G.SUBTITLE_Y + PAD_TOP + (2 - len(chunk["lines"])) * LINE_HEIGHT // 2 + li * LINE_HEIGHT
                txt_file = f"{os.path.dirname(os.path.abspath(__file__))}/_tmp_line_{ci}_{li}.txt"
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(line_text)
                tn = f"scap_text_{ci}_{li}_{phase}"
                fc.append(
                    f"[{prev}]drawtext=fontfile={FONT_PATH}:fontcolor={text_color}:"
                    f"fontsize={FONTSIZE}:textfile={txt_file}:x={lx:.1f}:y={ly}:"
                    f"enable='{full_cond}'[{tn}]"
                )
                prev = tn
    return fc, prev
