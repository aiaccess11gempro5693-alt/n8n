"""
Visual brief для каждой сцены (design-system.md, "8. Semantic -> Visual
layer"): main_message / supporting_points / visual_goal / information_structure
/ visual_components / asset_requirements — описание СМЫСЛА и творческого
решения, не координаты. Layout и geometry считает layout_rules.py +
compose_scene.py по `information_structure`, а не по номеру сцены.

Тексты остаются теми, что уже были утверждены в narration/render_headlines
PLAN — но КОМПОЗИЦИОННОЕ РЕШЕНИЕ для сцен 2 и 6 пересмотрено заново (не
скопировано из старой системы), см. visual_goal каждой сцены и отчёт в чате
от 17.09.2026 (5).
"""
from . import grid as G

SCENES = {
    1: {
        "information_structure": "sequence_statement",
        "main_message": "«Иммунитет» — самое частое слово, с которым приходят в аптеку",
        "supporting_points": ["Люди приходят с уже готовым мнением"],
        "visual_goal": "Тема + сдвиг мысли, без визуального шума — тезис сменяется тезисом, иконка не нужна.",
        "visual_components": ["statement"],
        "asset_requirements": [],
        "segments": [
            {"title": "ИММУНИТЕТ", "accent": "teal", "start": 1.12, "end": 6.82},
            {"title": "Приходят с готовым мнением", "accent": "teal", "start": 6.82, "end": None},
        ],
    },
    2: {
        "information_structure": "single_thesis",
        "main_message": "За уверенным запросом почти всегда стоит несформулированная потребность",
        "supporting_points": [],
        "visual_goal": (
            "17.09.2026 (5): редизайн по прямой жалобе — раньше 'Добраться до сути' было "
            "карточкой с иконкой лупы, триггерящейся на t=8.3 из 9.4с сцены (видна ~1с, "
            "мелькала). Убрали иконку (абстрактная мысль, иконка не проясняет её), тезис "
            "показывается РАНЬШЕ реального слова в речи и держится большую часть сцены — "
            "устойчивая композиция, а не всплывающая подпись."
        ),
        "visual_components": ["statement"],
        "asset_requirements": [],
        "eyebrow": "Скрытый запрос",
        "title": "Добраться до сути",
        "accent": "coral",
        "start": 1.6,   # раньше словесного триггера (8.3) — намеренно, см. visual_goal
    },
    3: {
        "information_structure": "independent_causes",
        "main_message": "Что покупатель имеет в виду под «что-нибудь для иммунитета»?",
        "supporting_points": [
            "Болеет каждую осень", "Слабость после ОРВИ", "Просто устал", "Уже принимает БАДы",
        ],
        "visual_goal": (
            "4 КОНКРЕТНЫХ разных сценария — иконка реально помогает быстро отличить один от "
            "другого (в отличие от сцены 2, здесь не абстракция, а предметные ситуации). "
            "Убрана карточка-рамка вокруг каждой пары — иконка-стикер + подпись с тенью "
            "текста достаточно контрастны сами по себе."
        ),
        "visual_components": ["headline", "icon_annotation x4"],
        "asset_requirements": ["переиспользованы scene3-icon1..4-norm.png — стиль/смысл подходят новой лёгкой подаче"],
        "eyebrow": "Что он имеет в виду?",
        "eyebrow_start": 0.3,
        "eyebrow_end": 7.0,
        "accent": "teal",
        "items": [
            {"icon": "scene3-icon1-norm.png", "label": "Болеет каждую осень", "start": 7.15, "accent": "teal"},
            {"icon": "scene3-icon2-norm.png", "label": "Слабость после ОРВИ", "start": 12.13, "accent": "coral"},
            {"icon": "scene3-icon3-norm.png", "label": "Просто устал", "start": 15.56, "accent": "teal"},
            {"icon": "scene3-icon4-norm.png", "label": "Уже принимает БАДы", "start": 20.81, "accent": "coral"},
        ],
    },
    4: {
        "information_structure": "single_thesis",
        "main_message": "Точный вопрос — точный ответ",
        "supporting_points": [],
        "visual_goal": "Единственный вывод сцены — крупный тезис, без карточки/иконки.",
        "visual_components": ["statement"],
        "asset_requirements": [],
        "eyebrow": None,
        "title": "Точный вопрос — точный ответ",
        "accent": "coral",
        "start": 0.3,
    },
    5: {
        "information_structure": "sequential_checklist",
        "main_message": "Несколько простых вопросов, которые нужно уточнить у покупателя",
        "supporting_points": [
            "Что именно беспокоит?", "Длительность симптомов",
            "Приём других препаратов", "Хронические заболевания",
        ],
        "visual_goal": (
            "17.09.2026 (5): убраны иконки у каждого пункта (не добавляли ясности — все 4 "
            "пункта абстрактные категории вопроса, не предметы) в пользу нумерованных строк "
            "на одном общем scrim — единая композиция чек-листа, не 4 отдельные плашки. "
            "Показывается ОДНИМ разом (не по одному пункту вслед за словом) с момента первого "
            "вопроса и держится до конца сцены — иначе прогрессивное появление читается как "
            "мелькающие стикеры, а не список."
        ),
        "visual_components": ["slim_checklist"],
        "asset_requirements": [],
        "title": "Простые вопросы",
        "accent": "teal",
        "items": [
            "Что именно беспокоит?", "Длительность симптомов",
            "Приём других препаратов", "Хронические заболевания",
        ],
        "start": 2.92,
    },
    6: {
        "information_structure": "comparison",
        "main_message": "Вопросы защищают покупателя от лишнего или неподходящего препарата",
        "supporting_points": ["Излишняя стимуляция", "Восстановительная поддержка"],
        "visual_goal": (
            "17.09.2026 (5): редизайн по прямой жалобе — раньше это были две одинаковые "
            "тёмные карточки ('выглядит как UI dashboard'). Убраны карточки-рамки и иконки "
            "(баночка/щит не добавляли смысла сильнее самого текста); физический разделитель "
            "по центру невозможен — аватар занимает всю высоту центра кадра и закрыл бы лицо "
            "— поэтому единство композиции даёт зеркальная симметрия (одинаковая высота, общий "
            "верхний штрих-акцент, текст развёрнут к центру/аватару с обеих сторон) вместо "
            "физического соединения. Появляются ВМЕСТЕ (не одна раньше другой) в момент, "
            "когда речь заходит о противопоставлении — это и есть 'единая композиция', не "
            "последовательность независимых карточек."
        ),
        "visual_components": ["headline", "split_comparison_side x2"],
        "asset_requirements": [],
        "eyebrow": "Вопросы защищают покупателя",
        "eyebrow_start": 0.3,
        "eyebrow_end": 13.5,
        "left": {"label": "Излишняя стимуляция", "accent": "coral"},
        "right": {"label": "Восстановительная поддержка", "accent": "teal"},
        "start": 13.79,
    },
    7: {
        "information_structure": "single_thesis",
        "main_message": "Доверие, а не продажа",
        "supporting_points": [],
        "visual_goal": "Финальный вывод блока — крупный тезис.",
        "visual_components": ["statement"],
        "asset_requirements": [],
        "eyebrow": None,
        "title": "Доверие, а не продажа",
        "accent": "coral",
        "start": 0.3,
    },
    8: {
        "information_structure": "single_thesis",
        "main_message": "Системная забота",
        "supporting_points": [],
        "visual_goal": "Закрывающий тезис ролика.",
        "visual_components": ["statement"],
        "asset_requirements": [],
        "eyebrow": None,
        "title": "Системная забота",
        "accent": "teal",
        "start": 0.3,
    },
}

ACCENT = {"teal": G.TEAL, "coral": G.CORAL}


def get_structure(scene_n):
    return SCENES[scene_n]
