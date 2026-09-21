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
    information_structure: str      # Gemini's OWN WORDS, free text — not constrained to an enum
    visual_goal: str                 # what the viewer should come away understanding
    asset_required: bool
    asset_type_raw: str              # Gemini's OWN WORD for the asset type, unnormalized
    asset_brief: str
    asset_caption: str                # short (2-4 word) Russian on-screen label for the image card, "" if no asset
    composition_intent: str          # free text: how it should sit relative to avatar/subtitles
    motion_intent: str               # free text: how it should reveal/animate
    avoid: list                      # things deliberately not shown, and why
    no_asset_reason: str             # required reasoning when asset_required is False
    visual_concept: str              # TECHNICAL dispatch key (controlled vocabulary, see below)
    asset_strategy: str              # TECHNICAL dispatch key (controlled vocabulary, see below)
    elements: list = field(default_factory=list)          # list[VisualElement]


PROJECT_VISUAL_CONTEXT = """\
Проект: обучающие видео для сотрудников аптеки, фармацевт-аватар говорит
на камеру, статичный поясной план по центру кадра (1920x1080), лицо и
плечи занимают центральную полосу x≈600-1340 на всю высоту кадра — это
AVATAR ZONE, в неё нельзя помещать никакую графику. Внизу кадра —
субтитровая плашка (SUBTITLE ZONE), тоже запрещена для графики. Всё, что
можно разместить, идёт в одну из двух боковых колонок слева/справа от
аватара, каждая примерно 470-490px шириной и ~765px высотой. Стиль —
premium editorial: единственный акцентный цвет #FF6B4A. И текст
(заголовки, списки, чек-листы), и картинка — ВСЕГДА на собственной
залитой скруглённой карточке (непрозрачный фон, акцентная обводка,
мягкая тень) — никогда не бывает "голого" текста или картинки без
заполненного фона поверх видео.

ВАЖНО про стиль картинки: аватар в кадре — это РЕАЛЬНОЕ живое видео
человека в аптеке, не иллюстрация. Сгенерированная картинка должна
визуально принадлежать тому же миру — фотореалистичная, документальная/
редакционная фотография (реальные люди, реальный интерьер аптеки,
естественный свет), а НЕ 3D-мультфильм, НЕ иллюстрация, НЕ мультяшный/
глянцевый рендер, НЕ клипарт. asset_brief должен явно требовать этого от
модели генерации (photorealistic photography, real people, documentary/
editorial style, NOT illustration, NOT 3D render, NOT cartoon)."""

ANALYSIS_INSTRUCTIONS = f"""\
Ты семантический аналитик для монтажного pipeline обучающих видео.
{PROJECT_VISUAL_CONTEXT}

Тебе даётся текст одной сцены (реплика диктора), её длительность. Твоя
задача — понять СОДЕРЖАНИЕ именно этого текста (не тему ролика в целом) и
решить, как это должно быть представлено на экране поверх видео с
говорящим человеком: главная мысль, второстепенные элементы, нужен ли
вообще дополнительный визуал, и если да — какой именно.

Думай и объясняй СВОИМИ СЛОВАМИ там, где это указано как "free text" —
не подгоняй описание под заранее придуманный список. Примеры того, каким
может быть решение (это ПРИМЕРЫ, не исчерпывающий список): process flow;
comparison; cause/effect; checklist; explanatory illustration;
pharmacy-counter scene; layered diagram; annotated object; sequence;
visual metaphor; typography-only; combination of diagram and text. Если
ни один пример не подходит — опиши своё решение как есть.

ВАЖНОЕ ПРАВИЛО про asset_required: новый творческий курс проекта — видео
должно выглядеть ярче, живее и понятнее за счёт настоящих картинок, не
только текста. Если в тексте сцены есть что-то конкретное и предметное —
физический объект (упаковка, баночка, термометр...), конкретная сцена
(разговор на кассе, полка в аптеке), человек/персонаж, процесс с видимыми
шагами — это почти всегда стоит показать картинкой, а не только словами:
в таких случаях смело выбирай asset_required=true. Оставляй
asset_required=false только для текста, где мысль ДЕЙСТВИТЕЛЬНО абстрактна
и её нечем изобразить конкретно (например, чистое рассуждение или
эмоциональная оценка без предметного образа) — в этом случае
no_asset_reason ОБЯЗАТЕЛЕН и должен быть содержательным (не "не нужно").
Это по-прежнему решение для КАЖДОЙ сцены по её реальному содержанию, не
галочка "true всегда" — но при сомнении сейчас предпочитай true.
Никогда не выбирай буквальную/клишированную иконку одного слова из текста
(например «лупа» для идеи «разобраться в сути») — картинка должна
визуально объяснять МЕХАНИЗМ или РЕЗУЛЬТАТ мысли, а не быть значком-ребусом.

Технические поля (visual_concept, asset_strategy) — контролируемый
словарь, потому что рендер-код сейчас умеет строить только конечный набор
компонентов. Заполняй их как ближайшее технически возможное исполнение
твоего решения; сама смысловая интерпретация (information_structure,
visual_goal, composition_intent, motion_intent) — твоими словами, без
ограничений.
  visual_concept (для форматирования типографики/структуры) — один из:
    {", ".join(VISUAL_CONCEPTS)}.
  asset_strategy (техническая категория итогового изображения, если
    asset_required=true) — ближе всего к одному из:
    {", ".join(v for v in ASSET_STRATEGIES if v not in ("typography", "none"))}.
    Если asset_required=false, поставь "none".

Ответь СТРОГО в формате JSON без пояснений, без markdown-обёртки:
{{
  "main_message": "одна фраза — о чём этот текст",
  "information_structure": "free text — своими словами, что это за тип информации",
  "visual_goal": "free text — что именно зритель должен понять из визуала",
  "asset_required": true/false,
  "asset_type": "free text — твоё слово для типа ассета (illustration/diagram/pharmacy-counter scene/annotated object/...), или 'typography' или 'none'",
  "asset_brief": "если asset_required=true: детальный промпт НА АНГЛИЙСКОМ для модели генерации изображений (что нарисовать, стиль, композиция, что НЕ включать); иначе null",
  "asset_caption": "если asset_required=true: короткая подпись на русском, 2-4 слова, под картинку (не дублирует дословно label из elements, а называет ЧТО на картинке); иначе null",
  "no_asset_reason": "если asset_required=false: почему графика не добавляет пользы; иначе null",
  "composition_intent": "free text — как это должно располагаться относительно аватара/субтитров",
  "motion_intent": "free text — как это должно появляться/анимироваться, или 'static' если не важно",
  "visual_concept": "один из технического списка выше",
  "asset_strategy": "один из технического списка выше, или 'none'",
  "elements": [{{"role": "...", "label": "краткая подпись на экран, 2-6 слов, русский", "sublabel": "... или null", "order": 1}}],
  "avoid": ["что сознательно НЕ визуализируем и почему, коротко"]
}}

Поле "role" в elements зависит от visual_concept:
  process_flow / cause_effect -> "step" (process) или "cause"/"mechanism"/
    "effect" (cause_effect), с "order" по порядку.
  structured_alternatives / checklist -> "item", "order" по порядку.
  comparison -> ровно 2 элемента, role "left" и "right".
  qa_structure -> ровно 2 элемента, role "question" и "answer".
  strong_typography -> ровно 1 элемент, role "headline", можно "sublabel".
  none -> elements: [] (это нормально, если asset_required=true и весь
    смысл несёт картинка, а не текстовые подписи).
"""


def dispatch_and_wait(scenes, output_name, ref="main"):
    """Dispatches call-scene-semantic-analysis.yml with the given scenes
    (list of {id,text,duration}) and returns the parsed
    scratch/<output_name>.json it commits. On failure, still tries to pull
    and surface whatever error detail the workflow committed (it always
    writes scratch/<output_name>.json, success or failure — see the
    workflow's try/except) before re-raising, since this sandbox can't
    fetch raw job logs directly."""
    try:
        gh_bridge.dispatch_and_wait(
            WORKFLOW_FILE,
            {"scenes_json": json.dumps(scenes, ensure_ascii=False), "output_name": output_name},
            ref=ref,
            label=f"{len(scenes)} scene(s), output_name={output_name!r}",
        )
    except Exception as e:
        try:
            detail = gh_bridge.pull_and_read(f"scratch/{output_name}.json")
            print("[semantic_analysis] committed error detail:\n" + detail.get("error", str(detail)))
        except Exception:
            pass
        raise
    return gh_bridge.pull_and_read(f"scratch/{output_name}.json")


_ASSET_TYPE_KEYWORDS = {
    "illustration": "illustration", "иллюстрац": "illustration", "scene": "illustration",
    "сцен": "illustration", "metaphor": "illustration", "метафор": "illustration",
    "object": "illustration", "annotated": "illustration",
    "diagram": "diagram", "схем": "diagram", "scheme": "diagram", "layered": "diagram",
    "icon": "icon", "иконк": "icon",
    "image": "image", "photo": "image", "фото": "image", "изображен": "image",
    "infograph": "illustration", "инфограф": "illustration",
    "data": "data_visualization", "chart": "data_visualization", "график": "data_visualization",
    "combin": "combination", "комбинац": "combination",
}


def _normalize_asset_strategy(asset_required, asset_type_raw):
    """`asset_strategy` (technical dispatch key) is DERIVED from Gemini's
    own free-text `asset_type`, not required to equal it exactly — the
    controlled vocabulary is scoped to what the renderer can build, the
    free text is Gemini's real, unconstrained answer (kept verbatim in
    `asset_type_raw` and shown in reports/logs)."""
    if not asset_required:
        return "none"
    low = (asset_type_raw or "").lower()
    for kw, mapped in _ASSET_TYPE_KEYWORDS.items():
        if kw in low:
            return mapped
    # asset_required=true but the free-text word didn't match any known
    # technical bucket — asset_required is the authoritative signal, so
    # fall back to the most general "something needs generating" bucket
    # rather than silently downgrading to typography.
    return "illustration"


def _parse_one(raw, scene_id, text, duration):
    concept = raw.get("visual_concept")
    if concept not in VISUAL_CONCEPTS:
        raise ValueError(f"scene {scene_id}: LLM returned unknown visual_concept {concept!r} (not in {VISUAL_CONCEPTS})")
    asset_required = bool(raw.get("asset_required"))
    asset_type_raw = raw.get("asset_type") or ""
    strategy = _normalize_asset_strategy(asset_required, asset_type_raw)
    if asset_required and not raw.get("asset_brief"):
        raise ValueError(f"scene {scene_id}: asset_required=true but no asset_brief was provided")
    if asset_required and not raw.get("asset_caption"):
        raise ValueError(f"scene {scene_id}: asset_required=true but no asset_caption was provided")
    if not asset_required and not raw.get("no_asset_reason"):
        raise ValueError(f"scene {scene_id}: asset_required=false but no no_asset_reason was provided")
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
        visual_goal=raw.get("visual_goal", ""),
        asset_required=asset_required,
        asset_type_raw=asset_type_raw,
        asset_brief=raw.get("asset_brief") or "",
        asset_caption=raw.get("asset_caption") or "",
        composition_intent=raw.get("composition_intent", ""),
        motion_intent=raw.get("motion_intent", ""),
        avoid=raw.get("avoid", []),
        no_asset_reason=raw.get("no_asset_reason") or "",
        visual_concept=concept,
        asset_strategy=strategy,
        elements=elements,
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
