"""
STEP: NARRATION / SCENE CONTENT -> SEMANTIC ANALYSIS -> VISUAL INTENT.

Это ручной (не NLP-автоматический) семантический разбор каждой сцены —
сделан человеком-редактором (Claude Code) чтением реального текста
диктора (`render/compute_word_layout.py::NARRATION`), а не вычислен
эвристикой. Так и должно быть: контент-анализ — творческая часть
(см. CLAUDE.md, "Роли"), не механическая. Но представление СТРУКТУРИРОВАНО
(SceneSemantics), и то, что дальше происходит с этой структурой
(composition.py, layout.py), не знает о номерах сцен вообще — только о
полях ниже. Если завтра текст сцены 2 изменится, просто меняется эта
запись; движок ниже по пайплайну не тронут.

`visual_concept` — это КЛАССИФИКАЦИЯ информационной структуры контента
(bullets/checklist/comparison/sequence/single-statement/...), а не имя
шаблона под конкретный номер сцены. Один и тот же concept может
повториться на двух сценах, если у них правда одинаковая структура
информации (см. сцены 1 и 8 — оба "keyword_emphasis", потому что оба
буквально об одном ключевом слове-теме ролика).
"""
from dataclasses import dataclass, field


@dataclass
class VisualElement:
    """Один смысловой блок, который стоит визуализировать (не обязательно
    один на сцену — checklist/grid/sequence дают несколько)."""
    label: str                 # короткий текст на экране (не дословная цитата)
    trigger_phrase: str        # фраза из NARRATION, на которой это должно появиться
    kicker: str = ""           # необязательная надстрочная мини-метка (для keyword/headline)
    sublabel: str = ""         # необязательная вторая строка / уточнение


@dataclass
class SceneSemantics:
    scene: int
    main_message: str
    information_structure: str      # bullets|checklist|comparison|sequence|single_statement|none
    visual_priority: str            # what the visual must communicate, one sentence
    visual_concept: str             # concept key -> dispatched in composition.py
    elements: list = field(default_factory=list)   # list[VisualElement]
    elements_to_omit: list = field(default_factory=list)  # documented, not rendered
    notes: str = ""


SCENES = {

    1: SceneSemantics(
        scene=1,
        main_message='"Иммунитет" — самое популярное слово в аптеке; люди приходят, думая, что уже знают, чего хотят.',
        information_structure="single_statement_two_stage",
        visual_priority="Назвать тему ролика одним словом, затем сместить фокус на реальную проблему (шаблонный запрос).",
        visual_concept="keyword_emphasis",
        elements=[
            VisualElement(label="ИММУНИТЕТ", trigger_phrase='"Иммунитет"', kicker="ТЕМА"),
            VisualElement(label="Приходят с готовым мнением", trigger_phrase="приходят к вам с ощущением",
                          sublabel="а не с точным запросом"),
        ],
        elements_to_omit=["реклама/интернет/друзья — три канала, перечисление ради перечисления, не несёт решения"],
        notes="Двухфазный headline: слово -> смещение к реальной теме сцены 2. Обе фазы — один и тот же "
              "компонент (typography), не карточка.",
    ),

    2: SceneSemantics(
        scene=2,
        main_message="За уверенным запросом стоит несформулированная потребность; фармацевт помогает до неё добраться.",
        information_structure="sequence",
        visual_priority="Раскрыть идею «добраться до сути» как процесс из шагов, а не проиллюстрировать её лупой.",
        visual_concept="process_sequence",
        elements=[
            VisualElement(label="Запрос", trigger_phrase="уверенным запросом"),
            VisualElement(label="Настоящая потребность", trigger_phrase="добраться до сути"),
        ],
        elements_to_omit=["лупа / любая буквальная иконка «поиска» — не объясняет идею, просто иллюстрирует слово"],
        notes="Тест-кейс п.17 мастер-промпта: идея раскрывается как 3-шаговый процесс, а не метафора-предмет.",
    ),

    3: SceneSemantics(
        scene=3,
        main_message='За одной фразой "что-нибудь для иммунитета" может стоять одна из нескольких разных ситуаций.',
        information_structure="alternatives",
        visual_priority="Показать, что варианты независимы и равнозначны (не последовательность, не сравнение).",
        visual_concept="options_grid",
        elements=[
            VisualElement(label="Болеет каждую осень", trigger_phrase="болеет каждую осень"),
            VisualElement(label="После ОРВИ — слабость", trigger_phrase="перенёс ОРВИ"),
            VisualElement(label="Просто устал", trigger_phrase="просто устал"),
            VisualElement(label="Уже принимает 3 БАДа", trigger_phrase="три разных БАДа"),
        ],
        notes="4 независимые альтернативы -> сетка 2x2 (частный случай общего принципа, не захардкоженный шаблон "
              "по номеру сцены — выбран, потому что information_structure=alternatives).",
    ),

    4: SceneSemantics(
        scene=4,
        main_message="Каждая ситуация требует своего ответа — универсального совета не бывает.",
        information_structure="single_statement",
        visual_priority="Закрепить контраст: точный ответ vs общий совет «что-то от иммунитета».",
        visual_concept="typography_only",
        elements=[
            VisualElement(label="Точный ответ вместо общего совета", trigger_phrase="реально поможет"),
        ],
        notes="Короткая сцена с одной мыслью — carousel/список не нужен, по правилу «нет пользы -> нет визуала» "
              "используется только типографика, без диаграммы.",
    ),

    5: SceneSemantics(
        scene=5,
        main_message="Есть 4 простых уточняющих вопроса, которые нужно задать по порядку.",
        information_structure="checklist",
        visual_priority="Показать реальный чек-лист вопросов, а не 4 отдельные картинки.",
        visual_concept="checklist_vertical",
        elements=[
            VisualElement(label="Что именно беспокоит?", trigger_phrase="что именно вас беспокоит"),
            VisualElement(label="Как давно это длится?", trigger_phrase="как давно вы замечаете"),
            VisualElement(label="Что уже принимает?", trigger_phrase="принимаете ли сейчас"),
            VisualElement(label="Есть хронические болезни?", trigger_phrase="хронические заболевания"),
        ],
        notes="Последовательность вопросов одного разговора -> вертикальный чек-лист (не 2x2 сетка, в отличие от "
              "сцены 3 — там независимые альтернативы, здесь последовательный опрос).",
    ),

    6: SceneSemantics(
        scene=6,
        main_message="Вопросы защищают покупателя: одному лишняя стимуляция не нужна, другому нужна не стимуляция, а поддержка.",
        information_structure="contrast",
        visual_priority="Показать два противоположных случая рядом, чтобы разница была видна мгновенно.",
        visual_concept="comparison_pair",
        elements=[
            VisualElement(label="Уже принимает высокие дозы", sublabel="Лишняя стимуляция",
                          trigger_phrase="может быть излишним"),
            VisualElement(label="Только после болезни", sublabel="Нужна поддержка, не стимуляция",
                          trigger_phrase="восстановительная поддержка"),
        ],
        notes="Единственная сцена с истинным контрастом двух ситуаций -> comparison, а не две одинаковые карточки.",
    ),

    7: SceneSemantics(
        scene=7,
        main_message="Покупатель чувствует: здесь не продают, а думают о его здоровье — это ощущение ценно.",
        information_structure="single_statement",
        visual_priority="Дать эмоциональному выводу короткую типографическую опору, не перегружая кадр.",
        visual_concept="typography_only",
        elements=[
            VisualElement(label="Думают о здоровье, а не о продаже", trigger_phrase="думают о его здоровье"),
        ],
        notes="Короткая (9.5с), эмоциональная реплика — минимум графики, пуант почти полностью несут субтитры.",
    ),

    8: SceneSemantics(
        scene=8,
        main_message="Иммунитет — это не один препарат, а системная забота, и фармацевт — часть этой системы.",
        information_structure="single_statement_two_stage",
        visual_priority="Закольцевать тему: слово из сцены 1 сменяется итоговой мыслью ролика.",
        visual_concept="keyword_emphasis",
        elements=[
            VisualElement(label="ИММУНИТЕТ", trigger_phrase="Иммунитет", kicker="БЫЛО"),
            VisualElement(label="Системная забота", trigger_phrase="это системная забота",
                          sublabel="и вы — часть этой системы"),
        ],
        notes="Смысловая рифма со сценой 1 (тот же visual_concept, потому что та же информационная структура — "
              "не потому что 'так короче сделать').",
    ),
}
