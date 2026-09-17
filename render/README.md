# Монтажный конвейер (ffmpeg-рендер)

**17.09.2026 — RESET.** Весь presentation-слой (заголовки/иконки/карточки/
чек-листы/сравнения и любой layout engine) удалён из активного pipeline по
прямому запросу пользователя — старые design/layout-правила продолжали
навязывать старую композицию, поэтому сначала нужна чистая точка старта.
Новая визуальная система будет спроектирована отдельным этапом. См.
`../CLAUDE.md`, запись "RESET COMPLETE".

## Что осталось (канон, не design/layout rules)

`build_trend_video.py` сейчас делает только три вещи:

1. **Ken Burns (+punch-in)** на каждом сыром клипе аватара.
2. **Переходы (crossfade)** между 8 сценами.
3. **Субтитры** (crop-маска караоке, синхронизация по словам) — из
   `compute_word_layout.py` / `caption_filter.py`.

Никакого дополнительного визуального слоя (текст на экране, иконки,
инфографика) поверх этого сейчас нет.

## Точка входа

```bash
cd render/
python3 compute_word_layout.py   # тайминги слов/субтитров -> word_layout.json
python3 build_trend_video.py     # Ken Burns + переходы + субтитры -> full-trend-video.mp4
```

## Требуемые входные данные

- `/tmp/final-scenes/scene-N.mp4` (N=1..8) — сырые клипы аватара от HeyGen
  (канон, см. `../docs/design-system.md`, раздел 8 — этот раздел про
  аватар/озвучку не затронут reset'ом, там нет design/layout правил).

## Файлы

- `compute_word_layout.py` — считает тайминги слов диктора, пишет `word_layout.json`.
- `caption_filter.py` — исторический генератор субтитровой плашки (техника
  встроена прямо в `build_trend_video.py`); справочный.
- `build_trend_video.py` — единственная точка сборки: Ken Burns + переходы + субтитры.
- `fonts/Inter-Bold.otf` — шрифт субтитров.
- `ambient_bed.m4a` — фоновая музыка.

## Удалено этим reset'ом (сохранено в git-истории, коммит перед reset)

`render/presentation/` (весь editorial-редизайн 17.09.2026 (5): content_model,
layout_rules, components, compose_scene, grid, preview), `render/legacy/`
(layout_engine.py, render_headlines.py, pill_gen_all.py, render_icon_scenes.py,
render_scenes.sh, build_concat_cmd.py). Восстановить можно из истории git
(коммит "Checkpoint: editorial-редизайн presentation-слоя (пред-reset)").
