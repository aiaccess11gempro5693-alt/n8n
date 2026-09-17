"""
VisualStructure для каждой сцены — ОПИСАНИЕ СМЫСЛА (design-system.md, "1.
СОЗДАЙ ПОНЯТИЕ VISUAL STRUCTURE"), не координаты. Тексты/тайминги те же,
что были утверждены раньше (render_headlines.py::PLAN, content2..content6
из build_trend_video.py) — здесь они просто переструктурированы по типу
содержания, а не придуманы заново.

`start`/`end` — секунды от начала СЦЕНЫ (локальное время), берутся из уже
посчитанного word_layout.json / прежних ручных таймингов, привязанных к
конкретному слову диктора — механизм синхронизации с речью не меняется,
меняется только то, во что эти тайминги укладываются на экране.
"""
from . import grid as G

SCENES = {
    1: {
        "type": "highlight",
        "segments": [
            {"title": "ИММУНИТЕТ", "accent": "teal", "start": 1.12, "end": 6.82},
            {"title": "Приходят с готовым мнением", "accent": "teal", "start": 6.82, "end": None},
        ],
    },
    2: {
        "type": "key_point",
        "eyebrow": "Скрытый запрос",
        "eyebrow_start": 0.3,
        "accent": "coral",
        "items": [
            {"icon": "scene2-icon1-norm.png", "label": "Добраться до сути", "start": 8.3},
        ],
    },
    3: {
        "type": "cards",
        "eyebrow": "Что он имеет в виду?",
        "eyebrow_start": 0.3,
        "eyebrow_end": 7.0,   # гаснет до первой карточки — эстафету принимают подписи карточек
        "items": [
            {"icon": "scene3-icon1-norm.png", "label": "Болеет каждую осень", "start": 7.15, "accent": "teal"},
            {"icon": "scene3-icon2-norm.png", "label": "Слабость после ОРВИ", "start": 12.13, "accent": "coral"},
            {"icon": "scene3-icon3-norm.png", "label": "Просто устал", "start": 15.56, "accent": "teal"},
            {"icon": "scene3-icon4-norm.png", "label": "Уже принимает БАДы", "start": 20.81, "accent": "coral"},
        ],
    },
    4: {
        "type": "highlight",
        "segments": [
            {"title": "Точный вопрос — точный ответ", "accent": "coral", "start": 0.3, "end": None},
        ],
    },
    5: {
        "type": "checklist",
        "eyebrow": "Простые вопросы",
        "eyebrow_start": 0.3,
        "accent": "teal",
        "items": [
            {"icon": "scene5-icon1-norm.png", "label": "Что именно беспокоит?", "start": 2.92},
            {"icon": "scene5-icon2-norm.png", "label": "Длительность симптомов", "start": 11.28},
            {"icon": "scene5-icon3-norm.png", "label": "Приём других препаратов", "start": 14.26},
            {"icon": "scene5-icon4-norm.png", "label": "Хронические заболевания", "start": 19.86},
        ],
    },
    6: {
        "type": "comparison",
        "eyebrow": "Вопросы защищают покупателя",
        "eyebrow_start": 0.3,
        "eyebrow_end": 13.5,
        "left": {"icon": "scene6-icon1-norm.png", "label": "Излишняя стимуляция", "start": 13.79, "accent": "coral"},
        "right": {"icon": "scene6-icon2-norm.png", "label": "Восстановительная поддержка", "start": 17.2, "accent": "teal"},
    },
    7: {
        "type": "highlight",
        "segments": [
            {"title": "Доверие, а не продажа", "accent": "coral", "start": 0.3, "end": None},
        ],
    },
    8: {
        "type": "highlight",
        "segments": [
            {"title": "Системная забота", "accent": "teal", "start": 0.3, "end": None},
        ],
    },
}

ACCENT = {"teal": G.TEAL, "coral": G.CORAL}


def get_structure(scene_n):
    return SCENES[scene_n]
