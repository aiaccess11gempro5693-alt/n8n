"""
Тайминг появления visual-элементов: переиспользует УЖЕ посчитанные
пословные тайминги из word_layout.json (единый источник правды — тот же,
что рисует караоке-подсветку субтитров), а не отдельную приблизительную
оценку. Задача этого модуля — найти, в какой момент локального времени
сцены начинается заданная триггер-фраза, по первому слову фразы.
"""
import json
import os
import re

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(f"{R}/word_layout.json", encoding="utf-8") as f:
    _MANIFEST = json.load(f)


def _norm(word):
    return re.sub(r"[^\w]+", "", word, flags=re.UNICODE).lower()


def _scene_words(scene):
    """Плоский список слов сцены в порядке речи, с их (start, end) в
    локальном времени сцены — собран из всех чанков word_layout.json."""
    out = []
    for chunk in _MANIFEST["scenes"][str(scene)]["chunks"]:
        out.extend(chunk["words"])
    return out


def trigger_time(scene, phrase, occurrence=1):
    """Возвращает локальное время сцены (сек), на котором начинается
    первое слово `phrase`. Ищет `occurrence`-е совпадение по счёту (на
    случай повторов слова в сцене)."""
    target = _norm(phrase.split(" ")[0])
    if not target:
        raise ValueError(f"empty trigger phrase for scene {scene}")
    words = _scene_words(scene)
    hits = 0
    for w in words:
        if _norm(w["text"]) == target or _norm(w["text"]).startswith(target):
            hits += 1
            if hits == occurrence:
                return w["start"]
    # мягкий фолбэк: ищем частичное совпадение (составное слово/окончание отличается)
    for w in words:
        if target in _norm(w["text"]) or _norm(w["text"]) in target:
            return w["start"]
    raise ValueError(f"trigger phrase {phrase!r} not found in scene {scene} narration words")


def scene_duration(scene):
    return _MANIFEST["scenes"][str(scene)]["duration"]


def enforce_min_gap(times, min_gap=1.2):
    """Гарантирует минимальный интервал между последовательными
    появлениями элементов одной reveal-группы (checklist/grid/sequence/
    two-stage) — сдвигает более поздние триггеры ВПЕРЁД (никогда не
    раньше их реального слова), чтобы два элемента не всплывали
    практически одновременно на короткой сцене. Правило 16 мастер-
    промпта: 'появился -> мелькнул -> исчез' запрещено; для этого
    элементы должны появляться минимум с таким разносом."""
    out = []
    last = None
    for t in times:
        adj = t if last is None else max(t, last + min_gap)
        out.append(adj)
        last = adj
    return out
