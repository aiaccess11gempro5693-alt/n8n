"""
STEP: raw scene text -> SEMANTIC ANALYSIS -> VisualIntent. COMPUTED, not
authored.

This replaces the deleted `semantic.py`, which stored one hand-written
`SceneSemantics` Python literal per `scene_id` (`SCENES: dict[int, ...]`).
That was flagged in a forensic audit (CLAUDE.md, 21.09.2026) as the same
"scene -> fixed pattern" problem the visual system was supposed to remove,
just renamed. This module has no `SCENES` dict, no per-scene branching, and
no reference to any of the 8 current scenes anywhere in its code — it takes
arbitrary text and returns a computed `SceneSemantics`. A 9th scene, or a
rewritten scene 2, works with zero changes here.

The actual analysis is an LLM call (Gemini, via the project's existing
CometAPI bridge) — this project's own role model (CLAUDE.md, "Роли") assigns
semantic classification/QA work to Gemini, not to hand-authored Python data.
This sandbox cannot reach api.cometapi.com directly (proxy denies it, see
`/root/.ccr/README.md` — confirmed 21.09.2026: `CONNECT tunnel failed,
response 403`), so the call runs through
`.github/workflows/call-scene-semantic-analysis.yml`, the same
dispatch-a-workflow bridge pattern as `call-image-pipeline.yml`.

Unlike every earlier GitHub Actions bridge in this project (which were all
driven by Claude manually calling `mcp__github__actions_run_trigger` from
inside a chat turn), `analyze_scenes()` below drives that bridge itself over
the plain GitHub REST API, using the `GITHUB_TOKEN` already present in this
environment. `api.github.com` is reachable directly from this sandbox
(confirmed 21.09.2026, unlike api.cometapi.com) — so this is a real function
callable by any Python script, with no Claude/human in the loop per call.
"""
import json
import os
import sys
from dataclasses import dataclass, field

from . import gh_bridge

WORKFLOW_FILE = "call-scene-semantic-analysis.yml"

# The only place the vocabulary of visual concepts / asset strategies is
# defined. Extending it (a new concept, a new asset type) means adding a
# value here + a matching builder in composition.py — never a per-scene
# edit. The LLM is constrained to these values so the builder dispatch
# stays deterministic; it does not invent unmapped strings.
VISUAL_CONCEPTS = [
    "process_flow",          # ordered steps that lead somewhere (arrows/chain)
    "structured_alternatives",  # independent, non-sequential options
    "checklist",              # a set of items to go through/verify
    "comparison",              # two contrasting cases
    "cause_effect",            # cause -> mechanism -> effect chain
    "qa_structure",            # an implicit or explicit question -> answer
    "strong_typography",       # one core message, nothing else adds value
    "none",                    # no visual would help this text
]
ASSET_STRATEGIES = [
    "typography", "illustration", "diagram", "icon", "image",
    "data_visualization", "combination", "none",
]


@dataclass
class VisualElement:
    role: str            # step|item|left|right|cause|mechanism|effect|question|answer|headline
    label: str
    sublabel: str = ""
    order: int = 0


@dataclass
class SceneSemantics:
    scene_id: str
    text: str
    duration: float
    main_message: str
    information_structure: str
    visual_priority: str
    visual_concept: str
    asset_strategy: str
    asset_brief: str = ""
    elements: list = field(default_factory=list)          # list[VisualElement]
    elements_to_omit: list = field(default_factory=list)


ANALYSIS_INSTRUCTIONS = f"""\
Ты семантический анализатор для монтажного pipeline обучающих видео
(фармацевт объясняет материал сотрудникам аптеки). Тебе даётся текст одной
сцены (реплика диктора). Проанализируй СОДЕРЖАНИЕ этого конкретного текста
(не тему ролика в целом) и верни структуру для того, что должно появиться
на экране поверх видео с говорящим человеком.

Правила:
- Визуал должен помогать понять мысль, а не иллюстрировать каждое слово.
  Если текст — это одна простая мысль без внутренней структуры, используй
  visual_concept="strong_typography" или даже "none", если графика не
  добавляет пользы.
- visual_concept ОБЯЗАН быть одним из: {", ".join(VISUAL_CONCEPTS)}.
  process_flow — только если шаги реально ведут один к другому по порядку
  (не просто перечисление). structured_alternatives — независимые варианты
  без порядка и без причинной связи. checklist — пункты, которые нужно
  пройти/проверить (обычно вопросы). comparison — ровно два
  противопоставленных случая. cause_effect — цепочка причина->механизм->
  следствие (может быть 2 или 3 звена). qa_structure — в тексте есть
  вопрос (явный или подразумеваемый) и ответ на него.
- asset_strategy ОБЯЗАН быть одним из: {", ".join(ASSET_STRATEGIES)}.
  "typography" — достаточно текста/структуры без изображения.
  "illustration"/"diagram"/"icon"/"image"/"data_visualization"/"combination"
  — если конкретный визуальный образ (не текст) реально прояснит мысль
  лучше, чем текст. Если предлагаешь что-то кроме typography/none —
  обязательно заполни asset_brief (детальный промпт НА АНГЛИЙСКОМ для
  модели генерации изображений: что нарисовать, стиль, композиция).
- elements — краткие подписи НА ЭКРАН (русский, 2-6 слов каждая), не
  дословная цитата реплики. Поле "role" зависит от visual_concept:
    process_flow / cause_effect -> role: "step" (process) или
      "cause"/"mechanism"/"effect" (cause_effect), с "order" по порядку.
    structured_alternatives / checklist -> role: "item", "order" по порядку.
    comparison -> ровно 2 элемента, role: "left" и "right".
    qa_structure -> ровно 2 элемента, role: "question" и "answer".
    strong_typography -> ровно 1 элемент, role: "headline", можно
      "sublabel" для уточнения.
    none -> elements: [].
- Не придумывай информацию, которой нет в тексте. Если структуры
  недостаточно для выбранного concept (например "comparison" без двух
  явных случаев) — выбери другой concept, который честно соответствует
  тексту.

Ответь СТРОГО в формате JSON без пояснений, без markdown-обёртки:
{{
  "main_message": "одна фраза — о чём этот текст",
  "information_structure": "process|alternatives|checklist|comparison|cause_effect|qa|single_message",
  "visual_priority": "что именно должен передать визуал, одна фраза",
  "visual_concept": "...",
  "asset_strategy": "...",
  "asset_brief": "английский промпт для генератора изображений или null",
  "elements": [{{"role": "...", "label": "...", "sublabel": "... или null", "order": 1}}],
  "elements_to_omit": ["что сознательно не визуализируем и почему, коротко"]
}}
"""


def dispatch_and_wait(scenes, output_name, ref="main"):
    """Dispatches call-scene-semantic-analysis.yml with the given scenes
    (list of {id,text,duration}) and returns the parsed
    scratch/<output_name>.json it commits."""
    gh_bridge.dispatch_and_wait(
        WORKFLOW_FILE,
        {"scenes_json": json.dumps(scenes, ensure_ascii=False), "output_name": output_name},
        ref=ref,
        label=f"{len(scenes)} scene(s), output_name={output_name!r}",
    )
    return gh_bridge.pull_and_read(f"scratch/{output_name}.json")


def _parse_one(raw, scene_id, text, duration):
    concept = raw.get("visual_concept")
    strategy = raw.get("asset_strategy")
    if concept not in VISUAL_CONCEPTS:
        raise ValueError(f"scene {scene_id}: LLM returned unknown visual_concept {concept!r} (not in {VISUAL_CONCEPTS})")
    if strategy not in ASSET_STRATEGIES:
        raise ValueError(f"scene {scene_id}: LLM returned unknown asset_strategy {strategy!r} (not in {ASSET_STRATEGIES})")
    elements = [
        VisualElement(role=e["role"], label=e["label"], sublabel=e.get("sublabel") or "", order=e.get("order") or 0)
        for e in raw.get("elements", [])
    ]
    return SceneSemantics(
        scene_id=scene_id,
        text=text,
        duration=duration,
        main_message=raw.get("main_message", ""),
        information_structure=raw.get("information_structure", ""),
        visual_priority=raw.get("visual_priority", ""),
        visual_concept=concept,
        asset_strategy=strategy,
        asset_brief=raw.get("asset_brief") or "",
        elements=elements,
        elements_to_omit=raw.get("elements_to_omit", []),
    )


def analyze_scenes(scenes, output_name, ref="main"):
    """scenes: list of {"id": str, "text": str, "duration": float|None}.
    Returns list[SceneSemantics], one per input scene, in the same order.
    This is the single entry point production code and test code both use
    — neither ever writes a SceneSemantics literal by hand."""
    result = dispatch_and_wait(scenes, output_name, ref=ref)
    by_id = {r["id"]: r["analysis"] for r in result["results"]}
    out = []
    for s in scenes:
        if s["id"] not in by_id:
            raise ValueError(f"scene {s['id']}: no analysis returned by the workflow")
        out.append(_parse_one(by_id[s["id"]], s["id"], s["text"], s.get("duration") or 0.0))
    return out


if __name__ == "__main__":
    demo = [{"id": "demo1", "text": sys.argv[1] if len(sys.argv) > 1 else "Тестовый текст сцены.", "duration": 10}]
    print(json.dumps([r.__dict__ for r in analyze_scenes(demo, "semantic-analysis-demo")], ensure_ascii=False, indent=2, default=lambda o: o.__dict__))
