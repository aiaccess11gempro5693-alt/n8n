"""
CONTENT ANALYSIS -> LAYOUT SELECTION по `information_structure` (design-
system.md, "2. Адаптивный выбор layout") — не по номеру сцены. Каждый
паттерн ниже реализован в compose_scene.py как отдельная функция.
"""


def select_layout(structure):
    s = structure["information_structure"]
    mapping = {
        "sequence_statement": "full_bleed_statement",
        "single_thesis": "single_statement",
        "independent_causes": "annotated_grid",
        "sequential_checklist": "slim_checklist_block",
        "comparison": "split_comparison_layout",
    }
    if s not in mapping:
        raise ValueError(f"unknown information_structure: {s}")
    return mapping[s]
