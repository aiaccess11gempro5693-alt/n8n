# Монтажный конвейер (ffmpeg + PIL рендер)

Рабочий код финальной сборки видео — субтитры, presentation-слой
(заголовки/тезисы/чек-листы/сравнения/аннотированные сетки), Ken Burns,
переходы, склейка.

Правила/стиль, которые этот код реализует, зафиксированы в
`../docs/design-system.md` — этот README про то, **как запускать**,
design-system про то, **что должно получиться**.

## Архитектура (с 17.09.2026 (5) — editorial-редизайн)

```
render/presentation/
  content_model.py   — visual brief на каждую сцену: main_message,
                        supporting_points, visual_goal, information_structure
                        (не координаты — описание СМЫСЛА)
  layout_rules.py     — information_structure -> layout (по правилам, не по
                        номеру сцены)
  components.py       — переиспользуемые компоненты (editorial_headline,
                        statement, icon_annotation, slim_checklist,
                        split_comparison_side) — текст ложится прямо на
                        видео со scrim-подложкой, БЕЗ тёмных карточек-рамок
  compose_scene.py    — content -> layout -> components -> geometry, с
                        валидацией (safe zone аватара И субтитровой плашки)
  preview.py          — статичное превью presentation-слоя БЕЗ полного
                        рендера видео (geometry-проверка)

render/build_trend_video.py — единственный скрипт финальной сборки:
  1. Ken Burns (+punch-in) на каждом сыром клипе аватара (канон, не менять).
  2. Crossfade всех 8 клипов (без текста).
  3. "Тихая зона" текста вокруг каждого перехода.
  4. Субтитры (crop-маска караоке) — канон, не менять.
  5. Presentation-слой: для каждой сцены compose_scene() отдаёт готовые PNG
     (текст+иконка+scrim уже запечены), этот шаг только накладывает их по
     глобальному времени с fade+лёгким подъездом снизу.
```

## Требуемые входные данные (готовятся заранее, не этим кодом)

- `/tmp/final-scenes/scene-N.mp4` (N=1..8) — сырые клипы аватара от HeyGen
  (`avatar_iii`, лип-синк по `audio_asset_id`, см. `../CLAUDE.md`).
- `../scratch/sceneN-iconM-norm.png` — изолированные иконки на пурпурном
  фоне `0xE91E8F`, нужны только для сцен, где `content_model.py` реально
  просит иконку (сейчас — только сцена 3; см. `visual_goal` каждой сцены).

## Порядок запуска (по одному сценарию)

```bash
cd render/

# 1. Посчитать тайминги слов и разбивку субтитров на чанки.
python3 compute_word_layout.py

# 2. (опционально, перед полным рендером) — превью presentation-слоя без
#    видео, чтобы проверить geometry/стиль на нескольких сценах:
python3 presentation/preview.py   # -> /tmp/presentation-preview/sceneN-preview.png

# 3. Собрать весь ролик целиком.
python3 build_trend_video.py
# результат: full-trend-video.mp4 — скопировать в ../scratch/ с версией
```

## Правка под новый сценарий — что где менять

| Что нужно поменять | Файл |
|---|---|
| Текст реплик по сценам, длительности клипов | `compute_word_layout.py` (`NARRATION`, `DURATIONS`) |
| Смысл/контент каждой сцены (main_message, тезисы, чек-лист, сравнение) | `presentation/content_model.py` (`SCENES`) |
| Какой layout выбирается для какого типа контента | `presentation/layout_rules.py` |
| Как выглядит конкретный компонент (типографика/scrim/отступы) | `presentation/components.py` |
| Единая сетка/safe zones/палитра/шрифт | `presentation/grid.py` |
| Какие 1-2 реплики получают punch-in зум | `build_trend_video.py` (`PUNCH{}`) |
| Порядок сцен, тип перехода между ними | `build_trend_video.py` (`scenes`, `SCENE_KIND`) |

## Файлы

- `compute_word_layout.py` — считает тайминги слов диктора (для караоке-подсветки
  и для синхронизации появления presentation-слоя с речью), пишет `word_layout.json`.
- `caption_filter.py` — исторический генератор filter_complex для субтитровой
  плашки одной сцены; сама техника (crop-маска караоке) встроена прямо в
  `build_trend_video.py`, этот файл — справочный.
- `presentation/` — весь presentation-слой (см. архитектуру выше).
- `build_trend_video.py` — единственная точка сборки финального видео.
- `fonts/Inter-Bold.otf` — единственный шрифт во всём ролике.
- `ambient_bed.m4a` — фоновая музыка (микшируется тихо под озвучку).

## `legacy/` — не используется в реальной сборке

`layout_engine.py` (движок координат до editorial-редизайна),
`render_headlines.py`+`pill_gen_all.py` (pill-бейдж заголовков — заменён
`presentation/components.py`), `render_icon_scenes.py`, `render_scenes.sh`,
`build_concat_cmd.py` — более ранние версии сборки. Оставлены для истории и
возможного отката, **не импортируются** из `build_trend_video.py`.
