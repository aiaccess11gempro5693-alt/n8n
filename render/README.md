# Монтажный конвейер (ffmpeg-рендер)

**17.09.2026 (7) — новая визуальная система.** После RESET (17.09.2026
(6), см. `../CLAUDE.md`) визуальный слой спроектирован и реализован
заново с нуля — CONTENT FIRST, DESIGN SECOND, без единого элемента из
старой icon+pill/card системы. Код — `render/visual/`, подробности и
таблица visual concepts — `render/visual/README.md`.

## Что делает `build_trend_video.py`

1. **Ken Burns (+punch-in)** на каждом сыром клипе аватара (канон).
2. **Переходы (crossfade)** между 8 сценами (канон).
3. **Субтитры** (crop-маска караоке, синхронизация по словам) — из
   `compute_word_layout.py` / `caption_filter.py` (канон).
4. **Visual layer** (`render/visual/`) — typography-driven editorial-
   графика (заголовки/списки/чек-листы/сравнения), сгенерированная по
   реальному содержанию сцены, а не по номеру сцены. Каждый элемент
   появляется в реальный момент произнесения своей фразы (переиспользует
   тайминги субтитров) и гаснет либо когда его сменяет вторая стадия
   (keyword_emphasis), либо на границе "тихой зоны" перехода.

## Точка входа

```bash
cd render/
python3 compute_word_layout.py   # тайминги слов/субтитров -> word_layout.json
python3 build_trend_video.py     # canon + visual layer -> full-trend-video.mp4
```

(`build_trend_video.py` сам вызывает `visual.render_visual_layer.build_all()`
в начале — отдельно генерировать `visual_assets/` не нужно, но можно для
отладки: `python3 -m visual.render_visual_layer`.)

## Требуемые входные данные

- `/tmp/final-scenes/scene-N.mp4` (N=1..8) — сырые клипы аватара от HeyGen
  (канон, см. `../docs/design-system.md`, раздел 8). **Это сессионный
  временный путь, он НЕ переживает конец сессии** — при старте новой
  сессии его нужно каждый раз заново скопировать из закоммиченных
  канонических клипов:

  ```bash
  mkdir -p /tmp/final-scenes
  for n in 1 2 3 4 5 8; do cp ../scratch/scene${n}-status-v2.mp4 /tmp/final-scenes/scene-$n.mp4; done
  cp ../scratch/scene6-status-v6-tse-b.mp4 /tmp/final-scenes/scene-6.mp4   # "витамина С" написано, "цэ" в озвучке
  cp ../scratch/scene7-status-v3.mp4 /tmp/final-scenes/scene-7.mp4
  ```

  ⚠️ **Не путать с `scratch/final-scene-N-status*.mp4`** (без цифры перед
  `-status`) — это более ранние черновики от 11.08.2026, их длительности
  НЕ совпадают с `DURATIONS` в `compute_word_layout.py`. Канонический
  набор — `scratch/sceneN-status-v2.mp4` (N=1..6,8) и
  `scratch/scene7-status-v3.mp4`, закоммичены 14.09.2026 13:30-13:32
  (сцена 6 отдельно заменена на `scene6-status-v6-tse-b.mp4`,
  15.09.2026 — та же картинка, но озвучка "витамина Цэ", см. `CLAUDE.md`
  15.09.2026 (10)/(11)). Сверяйте по `DURATIONS` в `compute_word_layout.py`
  (`{1: 16.002, 2: 9.408, 3: 25.056, 4: 11.88, 5: 21.96, 6: 20.84, 7: 9.504, 8: 8.663}`)
  через `ffprobe -show_entries format=duration`, если сомневаетесь.

## Файлы

- `compute_word_layout.py` — считает тайминги слов диктора, пишет `word_layout.json`.
- `caption_filter.py` — исторический генератор субтитровой плашки (техника
  встроена прямо в `build_trend_video.py`); справочный.
- `build_trend_video.py` — точка сборки: Ken Burns + переходы + субтитры + visual layer.
- `visual/` — новая визуальная система (semantic -> composition -> layout -> render). См. `visual/README.md`.
- `fonts/` — Inter-Bold (субтитры), Inter Display Black/Medium + Inter SemiBold (visual layer), Montserrat-Bold (историческое).
- `ambient_bed.m4a` — фоновая музыка.

## История

17.09.2026 (6) reset удалил `render/presentation/` и `render/legacy/`
(старая icon+pill/card система) — сохранены в git-истории, коммит
"Checkpoint: editorial-редизайн presentation-слоя (пред-reset)". Новый
`render/visual/` — независимая реализация с нуля, ничего оттуда не
переиспользует.
