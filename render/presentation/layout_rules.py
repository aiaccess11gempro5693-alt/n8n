"""
CONTENT ANALYSIS -> LAYOUT SELECTION (design-system.md, "2. Адаптивный выбор
layout"). Правила по типу+количеству пунктов, без ML — ровно то, что просили:
"понятная система правил", не имитация понимания текста.

select_layout() возвращает ИМЯ паттерна, а не координаты — geometry считает
compose_scene.py по этому имени. Если сцена сменит тип содержания в будущем
сценарии, этот код сам подберёт другой layout — не нужно вручную прописывать
geo<N> под номер сцены, как было в render/legacy/layout_engine.py.
"""


def select_layout(structure):
    t = structure["type"]
    items = structure.get("items")
    n = len(items) if items else 0

    if t == "highlight":
        return "highlight_center"
    if t == "key_point":
        return "key_point_accent"
    if t == "comparison":
        return "comparison_pair"
    if t == "process":
        return "process_row"
    if t == "checklist":
        return "checklist_block"
    if t == "cards":
        # 1-2 пункта -> компактный акцент, не сетка ради сетки;
        # 3-4 -> сетка 2x2 (независимые варианты, порядок не важен);
        # 5+ -> перечень плотнее читается как структурированный список.
        if n <= 2:
            return "key_point_accent"
        if n <= 4:
            return "cards_grid"
        return "checklist_block"
    raise ValueError(f"unknown content type: {t}")
