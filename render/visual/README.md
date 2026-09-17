# `render/visual/` — новая визуальная система (17.09.2026, с нуля)

Presentation-слой поверх канона (Ken Burns / переходы / субтитры,
`render/build_trend_video.py`), спроектированный заново после RESET
17.09.2026 (6) по прямому ТЗ пользователя ("новая visual system с нуля",
"CONTENT FIRST, DESIGN SECOND"). Ни один файл из удалённых
`render/presentation/` / `render/legacy/` не переиспользован.

## Пайплайн

```
NARRATION (compute_word_layout.py)
        │
        ▼
semantic.py        — SceneSemantics: main_message, information_structure,
                      visual_priority, visual_concept, elements (ручной
                      контент-анализ реального текста диктора, не NLP)
        │
        ▼
composition.py      — CONTENT + CONCEPT -> ColumnGroup[] (какая колонка,
                      accumulate/replace, триггеры слов через timing.py)
        │
        ▼
layout.py            — ColumnGroup -> PlacedItem[] (пиксели x/y, safe
                      zones, вертикальное центрирование, collision-safe
                      стекинг)
        │
        ▼
validate.py          — жёсткая проверка (safe zones, min visible time);
                      падает с ошибкой, НЕ откатывается на старый layout
        │
        ▼
render_visual_layer.py — рендерит PNG (components.py, PIL) + manifest.json
        │
        ▼
build_trend_video.py — overlay+fade каждого PNG в общий filter_complex
```

Диспетчинг везде идёт по `visual_concept` (строка = классификация
информационной структуры контента), **никогда** по номеру сцены.
`composition.py::BUILDERS` — единственное место, где имя concept'а
превращается в код; добавление новой сцены с уже существующей структурой
(bullets/checklist/comparison/...) не требует нового кода вообще.

## Design language (единый для всех концептов, `style.py`)

- Шрифты: Inter Display Black (заголовки/keyword), Inter SemiBold
  (киккеры/маркеры/номера), Inter Display Medium (подписи/sublabel).
- Единственный акцент — `#FF6B4A` (тонкие линии/номера/маркеры, никогда
  большая заливка).
- Никаких карточек/pill/фоновых заливок — легибность на живом видео даёт
  текстовая тень (`_draw_text_shadow`), не подложка.
- Единственный неоново-декоративный элемент — тонкая акцентная
  blockquote-линия слева/справа от заголовка (не рамка, не карточка).

## Компоненты (`components.py`)

- `render_kicker_word` — KEYWORD_EMPHASIS стадия 1 (киккер + огромное
  слово, автоуменьшение шрифта, если слово не переносится и не влезает).
- `render_headline` — TYPOGRAPHY_ONLY / KEYWORD_EMPHASIS стадия 2 /
  половина COMPARISON_PAIR (заголовок + опциональный sublabel,
  поддерживает зеркальное right-align).
- `render_list_item` — один пункт вертикального списка, 3 стиля маркера:
  `number` (независимые альтернативы), `node` (шаги процесса, кружок),
  `check` (чек-лист, квадрат).

## Visual concepts (`composition.py::BUILDERS`)

| concept | когда используется | компонент | колонка |
|---|---|---|---|
| `keyword_emphasis` | сцена буквально о одном слове/теме, с сюжетным сдвигом | kicker_word → headline (replace) | left |
| `typography_only` | одна мысль, диаграмма не добавляет пользы | headline | left |
| `process_sequence` | идея раскрывается как процесс/шаги | list_item(node) | right |
| `options_grid` | несколько независимых равнозначных альтернатив | list_item(number) | right |
| `checklist_vertical` | последовательность вопросов/пунктов одного разговора | list_item(check) | right |
| `comparison_pair` | два противоположных случая | headline×2, зеркально | left+right |

## Safe zones (`safe_zones.py`)

Измерены по реальным кадрам всех 8 канонических клипов аватара (не
подобраны на глаз): аватар — статичный поясной план по центру кадра на
всех сценах. `LEFT_COLUMN`/`RIGHT_COLUMN` — единственные зоны, куда может
попасть visual-слой; `validate.py` проверяет это программно на каждый
рендер, а не только "по договорённости".

## Тайминг (`timing.py`)

Триггер появления каждого элемента — это реальный момент начала
соответствующей фразы в `word_layout.json` (тот же источник, что красит
караоке-подсветку субтитров), не отдельная оценка. `enforce_min_gap`
гарантирует, что на коротких сценах элементы одной группы не всплывают
практически одновременно (правило «не мелькать <1с»).

## Как перегенерировать

```bash
cd render/
python3 compute_word_layout.py        # тайминги слов (если текст менялся)
python3 -m visual.render_visual_layer  # только PNG-ассеты + manifest.json (для отладки)
python3 build_trend_video.py           # полная сборка (сам вызывает visual-слой)
```

`render/visual_assets/` — регенерируемые артефакты, в git не хранятся
(см. `.gitignore`).
