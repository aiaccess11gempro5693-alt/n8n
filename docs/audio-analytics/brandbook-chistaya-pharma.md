🎨 Design System — «Чистая Фарма» LMS

Полный аудит визуального языка проекта. Документ — источник правды для создания новых экранов, полностью совместимых со стилем существующего продукта.

---

1. Общая дизайн-концепция

Философия. Modern SaaS/EdTech для фармацевтической отрасли: доверие, чистота, ясность данных. Интерфейс дружелюбный, но серьёзный — «медицинская точность в мягкой оболочке».

Визуальный стиль.
- Neo-corporate / soft-modern: крупные скругления (16px базовый радиус), лёгкие «пастельные» поверхности, глубокий синий как ядро.
- Glassmorphism-акценты (`.glass-card`, `backdrop-blur-xl`) на карточках второго уровня.
- Gradient-mesh фоны для «wow»-секций (лендинги, hero, статистика).
- Data-forward: KPI-плитки, воронки, таблицы — центральные элементы.

Основные принципы.
1. Ясность > красота. Каждый элемент несёт функцию.
2. Один акцент на экран. Coral/red — только для критичных CTA и алертов.
3. Мягкая иерархия. Тени и полупрозрачность вместо жёстких линий.
4. Данные — герой. Числа крупнее подписей, `tabular-nums` обязательно.
5. Респонсив от 320px. Мобильный не «урезан», а перекомпонован.

Настроение. Спокойное, профессиональное, современное. Не игривое, не корпоративно-скучное — «Notion × Linear × медтех».

---

2. Цветовая система

Все цвета — HSL-токены в `src/index.css`. Никогда не использовать сырые hex/`text-white`/`bg-black` в компонентах.

Light theme (root)

| Токен | HSL | HEX (прибл.) | Применение |
|---|---|---|---|
| `--background` | `220 20% 98%` | `#F7F8FB` | Основной фон приложения |
| `--foreground` | `222 47% 11%` | `#0F172A` | Основной текст |
| `--card` | `0 0% 100%` | `#FFFFFF` | Поверхность карточек |
| `--card-foreground` | `222 47% 11%` | `#0F172A` | Текст на карточках |
| `--popover` | `0 0% 100%` | `#FFFFFF` | Поповеры, дропдауны |
| `--primary` | `230 80% 56%` | `#2E52E6` | Ядро: CTA, ссылки, фокус |
| `--primary-foreground` | `0 0% 100%` | `#FFFFFF` | Текст на primary |
| `--secondary` | `220 20% 96%` | `#EFF1F5` | Кнопки-secondary, chips |
| `--secondary-foreground` | `222 47% 11%` | `#0F172A` | Текст на secondary |
| `--muted` | `220 14% 96%` | `#EFF1F4` | Пассивные поверхности |
| `--muted-foreground` | `220 10% 46%` | `#6B7280` | Подписи, метаинфо |
| `--accent` | `4 90% 58%` | `#F0362D` | Coral/red — критичные акценты |
| `--accent-foreground` | `0 0% 100%` | `#FFFFFF` | Текст на accent |
| `--success` | `152 76% 42%` | `#19B27A` | Успех, positive delta |
| `--warning` | `38 92% 50%` | `#F5A20A` | Предупреждения |
| `--destructive` | `0 84% 60%` | `#EF4444` | Удаление, ошибки |
| `--border` | `220 13% 91%` | `#E2E5EB` | Границы |
| `--input` | `220 13% 91%` | `#E2E5EB` | Границы полей |
| `--ring` | `230 80% 56%` | `#2E52E6` | Focus-ring |

Sidebar (тёмный всегда)

| Токен | HSL | Применение |
|---|---|---|
| `--sidebar-background` | `230 35% 12%` | Фон боковой навигации |
| `--sidebar-foreground` | `220 20% 96%` | Текст в сайдбаре |
| `--sidebar-accent` | `230 30% 20%` | Hover пункта меню |
| `--sidebar-accent-foreground` | `220 20% 98%` | Текст hover/active |
| `--sidebar-border` | `230 30% 18%` | Разделители |

Расширенная палитра «pharma»

| Токен | HSL | Применение |
|---|---|---|
| `--pharma-red` | `4 90% 58%` | Бренд-акцент (=accent) |
| `--pharma-blue` | `230 80% 56%` | Бренд-primary |
| `--pharma-blue-dark` | `230 80% 40%` | Градиенты, hover primary |
| `--pharma-blue-light` | `230 80% 96%` | Tinted-фоны, бейджи |
| `--pharma-gray` | `220 20% 96%` | Нейтральные плашки |

Dark theme

Все токены переопределяются в `.dark`. Ключевые: `--background: 230 25% 6%`, `--card: 230 25% 10%`, `--primary: 230 80% 65%` (светлее).

Состояния

| Состояние | Правило |
|---|---|
| hover primary | `hover:bg-primary/90` |
| hover secondary | `hover:bg-secondary/80` |
| hover ghost | `hover:bg-secondary hover:text-secondary-foreground` |
| active | Через `data-[state=active]` (Radix) — `bg-primary text-primary-foreground` |
| disabled | `disabled:pointer-events-none disabled:opacity-50` |
| focus | `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` |
| muted / приглушённый | `text-muted-foreground` |

Градиенты (утилиты)

- `.gradient-primary` — `linear-gradient(135deg, primary → primary-dark)`
- `.gradient-accent` — coral → orange
- `.gradient-success` — green → teal
- `.gradient-mesh` — многослойный radial-mesh для hero/lending
- `.text-gradient` — primary → accent (для крупных заголовков)
- `.text-gradient-blue` — primary → light-blue

Glass

- `.glass-card` — `bg-card/80 backdrop-blur-xl border-border/50`
- `.glass-card-elevated` — то же + `shadow-xl shadow-primary/5`

---

3. Типографика

Шрифт: `Plus Jakarta Sans` (Google Fonts, weights 300–800). Fallback: `sans-serif`. Настроен как `font-sans` в Tailwind — используется по умолчанию везде.

Правило: все `h1–h6` глобально получают `font-semibold tracking-tight` (см. `index.css`). `body` — `antialiased`.

Шкала размеров (Tailwind)

| Класс | Size / line-height | Применение |
|---|---|---|
| `text-xs` | 12 / 16 | Подписи, метки в таблицах |
| `text-sm` | 14 / 20 | Body-текст, форм-контролы |
| `text-base` | 16 / 24 | Основной параграф |
| `text-lg` | 18 / 28 | Подзаголовки карточек |
| `text-xl` | 20 / 28 | H4 |
| `text-2xl` | 24 / 32 | H3, CardTitle |
| `text-3xl` | 30 / 36 | H2 страничные |
| `text-4xl` | 36 / 40 | H1 обычные |
| `text-5xl` | 48 / 1 | Hero H1 |
| `text-6xl` | 60 / 1 | Hero XL / KPI-числа |

Иерархия заголовков (рекомендация)

| Ур. | Классы |
|---|---|
| H1 стр. | `text-3xl md:text-4xl font-bold tracking-tight` |
| H1 hero | `text-4xl md:text-6xl font-extrabold tracking-tight` + `text-gradient` |
| H2 секция | `text-2xl md:text-3xl font-semibold` |
| H3 карточка | `text-lg md:text-xl font-semibold` |
| H4 | `text-base font-semibold` |
| Body | `text-sm md:text-base text-foreground` |
| Caption | `text-xs text-muted-foreground` |
| KPI value | `text-2xl md:text-3xl font-bold tabular-nums` |

Веса

- 300 light — почти не используется
- 400 regular — body
- 500 medium — форм-лейблы, кнопки
- 600 semibold — заголовки, KPI подписи
- 700 bold — H1/H2, крупные числа
- 800 extrabold — hero, лендинги

Letter-spacing / line-height

- Заголовки: `tracking-tight` (-0.025em)
- Body: default
- Числа/KPI: всегда `tabular-nums`

Prose (rich-text блоки)

Определён в `.prose` (index.css): H1 2.25em/800, H2 1.65em/700, H3 1.3em/600, адаптив для мобильного ≤480px.

Спец-правило проекта

Символы `®` и `™` — принудительно superscript (см. mem/core).

---

4. Система отступов

База: Tailwind spacing scale (1 unit = 0.25rem = 4px).

Часто используемые шаги

| Класс | px | Применение |
|---|---|---|
| `p-1 / gap-1` | 4 | Внутри плотных элементов (badge) |
| `p-2` | 8 | Компакт-иконки, чипы |
| `p-3` | 12 | Мобильные карточки, KPI-tiles |
| `p-4` | 16 | Стандарт card padding (mobile) |
| `p-5` | 20 | Средние карточки |
| `p-6` | 24 | Base CardHeader/CardContent |
| `p-8` | 32 | Крупные секции, модалки-desktop |
| `p-10` | 40 | Hero-блоки |

Вертикальные ритмы

- Между секциями: `space-y-5` (20) / `space-y-6` (24) / `space-y-8` (32).
- Внутри секции (заголовок → контент): `space-y-3` / `space-y-4`.
- Между KPI-tiles: `gap-3 sm:gap-4`.
- Между заголовком секции и её описанием: `space-y-1.5` (см. CardHeader).

Отступы страницы (page container)

- Mobile: `px-4 py-4`
- Desktop: `px-6 md:px-8 py-6 md:py-8`
- Между главными блоками страницы: `space-y-5` или `space-y-6`.

Правила

1. Не смешивать шаги вне scale (никаких `p-[13px]`).
2. На mobile срезаем padding на 1 ступень: `p-6 sm:p-4` → `p-4 sm:p-6`.
3. Внутри карточек `space-y-4` — стандарт между строками контента.

---

5. Grid и брейкпоинты

Container

```js
container: { center: true, padding: "2rem", screens: { "2xl": "1400px" } }
```

- Max-width: 1400px (2xl).
- Padding: 2rem (32px) по бокам.

Брейкпоинты (Tailwind default)

| Prefix | min-width |
|---|---|
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px |
| `xl` | 1280px |
| `2xl` | 1400px (кастом) |

Типовые grid-паттерны

- KPI 6 tiles: `grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 sm:gap-4`.
- Cards 3-up: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6`.
- Form 2-col: `grid grid-cols-1 md:grid-cols-2 gap-4`.
- Dashboard split: `grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6`.

Адаптивность

- Всегда проектировать mobile-first.
- `overflow-x-hidden` на корневом контейнере страницы (см. `AdminHomeV2`).
- Таблицы: `overflow-x-auto` + минимальная ширина колонок.
- Скрывать вторичное на mobile через `hidden sm:block` / `sm:hidden`.

---

6. Скругления

База: `--radius: 1rem` (16px).

| Класс | Значение | Применение |
|---|---|---|
| `rounded-sm` | `calc(1rem - 4px)` = 12px | Мелкие бейджи |
| `rounded-md` | `calc(1rem - 2px)` = 14px | Buttons, inputs |
| `rounded-lg` | `1rem` = 16px | Cards, dialogs |
| `rounded-xl` | 12px (tw default) | Иконка-контейнер `.icon-gradient` |
| `rounded-2xl` | 16px | `.stat-card`, KPI-плитки |
| `rounded-full` | 9999px | Аватары, pills, dot-индикаторы, progress |
| `rounded-t-[10px]` | — | Drawer (vaul) верх |

Правила по типам

- Buttons → `rounded-md`
- Inputs / textarea / select trigger → `rounded-md`
- Cards → `rounded-lg`
- Стат-карточки / плитки KPI → `rounded-2xl`
- Модалки/диалоги → `rounded-lg`
- Drawer (bottom sheet) → `rounded-t-[10px]`
- Изображения-обложки → `rounded-lg` или `rounded-2xl` (крупные)
- Аватар, точки, дот-статус → `rounded-full`
- Badges → `rounded-full` (pill) или `rounded-md`

---

7. Тени

Смешаны native Tailwind и кастом с primary-тинтом.

| Класс | Применение |
|---|---|
| `shadow-sm` | Base button, subtle divider |
| `shadow` | Ненавязчивые карточки |
| `shadow-md` | Role-cards, hover buttons |
| `shadow-lg` | Popovers, dropdowns |
| `shadow-xl` | Модалки, `.glass-card-elevated` |
| `shadow-2xl` | Hero-карточки, stat-card hover |

Кастомные утилиты (index.css)

- `.card-shadow` — трёхслойная тень с primary-тинтом (5–8% альфа). Стандарт для карточек-с-данными.
- `.card-shadow-hover` — усиленная (10–15%). Применяется на hover.
- `.glow-primary` / `.glow-accent` / `.glow-success` — «свечение» 40px для акцентных плиток.

Когда что применять

- Плоский UI (кнопки, инпуты): `shadow-sm`.
- Карточки контента: `shadow-sm` покой → `shadow-md/lg` hover.
- KPI-плитки: `.card-shadow` покой → `.card-shadow-hover` hover.
- Overlay (модалки, drawer): `shadow-xl` + оверлей `bg-black/80`.
- Sidebar/nav: без тени, только `border-r`.

---

8. Кнопки (`components/ui/button.tsx`)

Всё через `cva`. Иконки внутри — 16px (`[&_svg]:size-4`).

Варианты (`variant`)

| Вариант | Классы | Когда |
|---|---|---|
| `default` (primary) | `bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm` | Основной CTA страницы |
| `destructive` | `bg-destructive text-destructive-foreground hover:bg-destructive/90` | Удаление |
| `outline` | `border border-input bg-background hover:bg-secondary` | Вторичные действия |
| `secondary` | `bg-secondary text-secondary-foreground hover:bg-secondary/80` | Нейтральные |
| `ghost` | `hover:bg-secondary hover:text-secondary-foreground` | В таблицах, тулбарах |
| `link` | `text-primary underline-offset-4 hover:underline` | Inline-ссылки |
| `accent` | `bg-accent text-accent-foreground hover:bg-accent/90` | Критичный/промо CTA |
| `roleCard` | `bg-accent shadow-md hover:shadow-lg font-semibold` | Role-selection на лендинге |
| `sidebar` | `text-sidebar-foreground hover:bg-sidebar-accent justify-start` | Пункты бокового меню |
| `sidebarActive` | `bg-sidebar-accent font-medium` | Активный пункт меню |

Размеры (`size`)

| Size | Классы |
|---|---|
| `default` | `h-10 px-4 py-2` |
| `sm` | `h-9 px-3` |
| `lg` | `h-11 px-8` |
| `xl` | `h-12 px-10 text-base` |
| `icon` | `h-10 w-10` |

Состояния

- hover: `bg-*/90`, transition 200ms.
- focus-visible: `ring-2 ring-ring ring-offset-2`.
- disabled: `pointer-events-none opacity-50`.
- loading: ставим `disabled` + `<Loader2 className="animate-spin" />` слева от текста.
- active (pressed): без спец-класса, полагаемся на `transition-all`.

Правила

1. Один primary CTA на экран. Остальные — outline/ghost.
2. Иконки только слева от текста (правая — исключение для «arrow →»).
3. Полная ширина кнопки — только в mobile-модалках/wizard-ах.

---

9. Формы

Input (`ui/input.tsx`)

```
h-10 w-full rounded-md border border-input bg-background px-3 py-2
text-base md:text-sm ring-offset-background
focus-visible:ring-2 focus-visible:ring-ring
disabled:opacity-50
```

Textarea

`min-h-[80px]`, тот же стиль что input, `resize-y` по умолчанию.

Select (Radix)

Trigger = как input, `h-10 rounded-md`. Content — `bg-popover shadow-md rounded-md`, элементы `hover:bg-accent hover:text-accent-foreground` (в Radix `accent`=`secondary` семантически).

Checkbox / Radio (Radix)

- Checkbox: `h-4 w-4 rounded-sm border border-primary`, `data-[state=checked]:bg-primary`.
- Radio: `h-4 w-4 rounded-full border border-primary`, точка `h-2.5 w-2.5 bg-current`.

Switch

`h-6 w-11 rounded-full`, thumb `h-5 w-5 rounded-full bg-background shadow-sm`. `data-[state=checked]:bg-primary`.

Labels

`text-sm font-medium leading-none peer-disabled:opacity-70`. Всегда `<Label htmlFor="…">`.

Validation

- Ошибка под полем: `text-sm text-destructive mt-1`.
- Красный бордер поля: `aria-invalid:border-destructive aria-invalid:ring-destructive/20`.
- Success состояние: `border-success` + иконка `Check` справа (редко).
- Хелпер: `text-xs text-muted-foreground`.

Layout полей

- Расстояние label→input: `space-y-1.5`.
- Между полями формы: `space-y-4`.
- Поля в ряд: `grid grid-cols-1 md:grid-cols-2 gap-4`.

---

10. Карточки (`ui/card.tsx`)

Композитная: `Card / CardHeader / CardTitle / CardDescription / CardContent / CardFooter`.

Базовая структура

```
Card:        rounded-lg border bg-card text-card-foreground shadow-sm
CardHeader:  flex flex-col space-y-1.5 p-6
CardTitle:   text-2xl font-semibold leading-none tracking-tight
CardDesc:    text-sm text-muted-foreground
CardContent: p-6 pt-0
CardFooter:  flex items-center p-6 pt-0
```

Внутренние отступы

- Стандарт: `p-6` (24px).
- Компакт (KPI, mobile): `p-3 sm:p-4`.
- Крупные (hero-cards): `p-8`.

Hover-анимации

- Data-карточки (кликабельные): `transition-all duration-300 hover:-translate-y-1 hover:card-shadow-hover`.
- KPI-плитка (`.stat-card`): подъём + фоновый gradient-overlay (см. `.stat-card::before`).
- Обычные карточки: без hover, если некликабельны.

Варианты применения

- Info-card: Card + CardHeader + CardContent.
- Stat-tile: `rounded-2xl p-4 border bg-card` + иконка-контейнер сверху + число + подпись.
- List-item card: `Card` с `p-4`, hover `bg-secondary/50`.
- Glass-card: `.glass-card` для наложений на mesh-фоны.

---

11. Иконки

Библиотека: [`lucide-react`](https://lucide.dev/).

Правила

- Толщина: 1.5–2 px (default lucide `stroke-width={2}`).
- Размеры: 14 / 16 / 20 / 24 / 32.
  - В кнопках: 16px (`size-4`, устанавливается через CVA).
  - В KPI-tiles / заголовках: 20–24px.
  - В hero-фичах: 32px в 48×48 контейнере.
- Цвет: наследуется через `currentColor` — всегда через `text-*` класс (`text-primary`, `text-muted-foreground`).
- Обёртка «icon-gradient»: `w-12 h-12 rounded-xl flex items-center justify-center` + `gradient-primary/accent/success`.

---

12. Анимации

Transitions

- duration: default 200ms (buttons/inputs), 300ms (cards/hover), 500ms (progress bars).
- easing:
  - `ease-out` — вход элементов.
  - `cubic-bezier(0.16, 1, 0.3, 1)` — «мягкий out» для slide-up/scale-in.
  - `ease-in-out` — циклические (pulse, float).

Готовые keyframes (tailwind.config.js)

`accordion-down/up`, `fade-in`, `slide-up`, `image-fade`, `slide-in-{right,left,up,down}`, `swipe-hint`, `pulse-subtle`.

Кастомные утилиты (index.css)

- `.animate-fade-in` (500ms)
- `.animate-slide-up` (600ms, «premium» easing)
- `.animate-scale-in` (400ms)
- `.animate-float` (6s loop)
- `.animate-pulse-soft` (3s loop, opacity)
- `.animate-pulse-gentle` (3s loop, box-shadow + scale — для success-CTA)

Правила

1. Появление секций на скролле — `animate-slide-up` со staggered delay.
2. Модалки — `animate-scale-in`.
3. Toasts / банеры — `animate-slide-in-down`.
4. Микро-hover — только `transition-all duration-200/300`.
5. Никаких bounce/rotate-крутилок кроме `Loader2` (spin 1s linear infinite).

---

13. UI-компоненты проекта

Все `src/components/ui/*.tsx` — shadcn-подобные обёртки над Radix + `cva`.

| Компонент | Назначение |
|---|---|
| `alert` | Инлайновые уведомления (info/warning/destructive) |
| `alert-dialog` | Подтверждения деструктивных действий |
| `aspect-ratio` | Media-контейнеры |
| `badge` | Статусы, теги, счётчики |
| `button` | См. §8 |
| `calendar` | Инлайн-календарь (react-day-picker) |
| `card` | См. §10 |
| `checkbox` | Radix Checkbox |
| `command` | Command palette (cmdk) для поиска |
| `confirm-dialog` | Обёртка над alert-dialog «ок/отмена» |
| `date-picker-field` | Календарь в поповере |
| `dialog` | Модальные окна |
| `drawer` | Bottom-sheet (vaul), моб. панели |
| `dropdown-menu` | Меню действий |
| `html-content` | Безопасный рендер prose-контента |
| `input` | См. §9 |
| `label` | Label формы |
| `mobile-tab-selector` | Селектор табов для мобилки |
| `nav-pills` | Пилюльная навигация (см. mem/style/navigation-pills) |
| `popover` | Плавающие панели |
| `progress` | Прогресс-бар (`.progress-bar`) |
| `radio-group` | Radix RadioGroup |
| `scroll-area` | Кастомный скроллер |
| `select` | Radix Select |
| `separator` | Разделители 1px |
| `sheet` | Side-panel (right/left) |
| `slider` | Радиус-слайдер |
| `switch` | Toggle |
| `table` | Data-table primitives |
| `tabs` | Radix Tabs |
| `textarea` | Многострочный инпут |
| `tooltip` | Подсказки при hover |

Доменные компоненты (примеры)

- `admin/dashboard/*` — `DashboardMetrics`, `DashboardConversion`, `DashboardDynamics`, `DashboardGeography`, `DashboardOrganizationsTable`, `DashboardStudentsTable`, `DashboardCoursesTable`, `DashboardFiltersBar`.
- `admin/home-v2/*` — `HomeV2ModeSwitcher`, `HomeV2ControlBar`, `HomeV2KpiStrip`, `HomeV2QuickPick`, `HomeV2DrillDrawer`, `HomeV2Detail`.
- `courses/*` — CourseCard, CourseSnap*, редакторы блоков (Test, Video, NPS, Survey).
- `layout/DashboardLayout` — общий layout с сайдбаром.

---

14. Tailwind

Theme extend

- fontFamily.sans: `['Plus Jakarta Sans', 'sans-serif']`.
- colors: все семантические токены (`primary/secondary/muted/accent/success/warning/destructive/border/input/ring/background/foreground/card/popover/sidebar/pharma`) — привязаны к HSL-переменным.
- borderRadius: `lg: var(--radius)`, `md: calc - 2px`, `sm: calc - 4px`.
- container: center, padding `2rem`, `2xl: 1400px`.

Custom classes (index.css `@layer`)

Components:
- `.glass-card`, `.glass-card-elevated`
- `.gradient-primary`, `.gradient-accent`, `.gradient-success`, `.gradient-mesh`
- `.stat-card` (+ `::before` overlay)
- `.icon-gradient`
- `.progress-bar`, `.progress-bar-fill`
- `.prose` (rich-text)

Utilities:
- `.text-gradient`, `.text-gradient-blue`
- `.card-shadow`, `.card-shadow-hover`
- `.glow-primary`, `.glow-accent`, `.glow-success`
- `.animate-fade-in`, `.animate-slide-up`, `.animate-scale-in`, `.animate-float`, `.animate-pulse-soft`, `.animate-pulse-gentle`

Utility conventions

1. Порядок в classnames: layout → box → typography → color → state (`hover:`, `focus:`) → responsive (`sm:`, `md:`).
2. Респонсив только «up»: `text-sm md:text-base` — никогда `md:text-sm` без причины.
3. Прозрачности пишем через `/` (`bg-primary/10`, `text-foreground/70`).
4. `cn()` из `@/lib/utils` для условных классов — всегда.
5. Никогда: `text-white`, `bg-black`, `#hex`, `rgb()` в JSX. Только токены.

---

15. Правила оформления

Секции страницы

- Container: `max-w-7xl mx-auto px-4 md:px-6 lg:px-8`.
- Вертикальный ритм между секциями: `space-y-6 md:space-y-8`.
- Каждая секция = либо `<Card>`, либо блок с `<h2>` + контент.

Заголовки секций

```
<div class="space-y-1">
  <h2 class="text-2xl md:text-3xl font-semibold tracking-tight">Заголовок</h2>
  <p class="text-sm text-muted-foreground">Короткое описание секции.</p>
</div>
```

CTA

- Основной CTA справа/по центру, `Button size="lg"` (или `xl` на лендинге).
- Вторичный рядом — `variant="outline"`.
- На мобилке — `w-full` в вертикальном стеке `flex-col gap-2 sm:flex-row sm:gap-3`.

Списки

- Дефолт: `space-y-2`, `text-sm`.
- Иконочные буллеты: `flex items-start gap-2` + `<CheckCircle2 className="w-4 h-4 text-success mt-0.5" />`.
- В `.prose` — нативные `<ul>/<ol>` с disc/decimal.

Карточки преимуществ / фич

```
<Card class="p-6 hover:card-shadow-hover transition-all duration-300">
  <div class="icon-gradient gradient-primary mb-4">
    <Icon class="w-6 h-6 text-primary-foreground" />
  </div>
  <h3 class="text-lg font-semibold mb-2">Заголовок</h3>
  <p class="text-sm text-muted-foreground">Описание.</p>
</Card>
```

Блоки с цифрами (KPI)

```
<div class="rounded-2xl border bg-card p-4 hover:card-shadow-hover transition-all">
  <div class="flex items-center justify-between mb-3">
    <div class="icon-gradient gradient-primary w-10 h-10">
      <Icon class="w-5 h-5 text-primary-foreground" />
    </div>
    <ArrowRight class="w-4 h-4 text-muted-foreground" />
  </div>
  <div class="text-2xl md:text-3xl font-bold tabular-nums">12 847</div>
  <div class="text-xs text-muted-foreground mt-1">Подписчиков</div>
</div>
```

Таблицы

- Header: `text-xs font-medium text-muted-foreground uppercase tracking-wide`.
- Rows: `border-b border-border hover:bg-secondary/50 transition-colors`.
- Числа: `tabular-nums text-right`.
- Actions: `<Button variant="ghost" size="icon">`.

Статусы / бейджи

- Success: `bg-success/10 text-success border-success/20 rounded-full px-2 py-0.5`.
- Warning: аналогично с `warning`.
- Neutral: `bg-secondary text-secondary-foreground`.
- Live/dot: `<span class="w-2 h-2 rounded-full bg-success animate-pulse-soft" />`.

---

16. Что нельзя нарушать

Запреты — жёстко.

1. ❌ Не использовать сырые цвета в компонентах: `text-white`, `bg-black`, `text-[#…]`, `bg-[rgb(…)]`.
2. ❌ Не менять `--radius`. 16px — база бренда.
3. ❌ Не подменять шрифт. Только `Plus Jakarta Sans`.
4. ❌ Не смешивать иконочные библиотеки. Только `lucide-react`.
5. ❌ Не ставить более одного primary CTA на экран.
6. ❌ Не использовать hard-coded shadow значения — только Tailwind-классы или `.card-shadow*`.
7. ❌ Не игнорировать dark-mode: все новые цвета определяются в обоих режимах.
8. ❌ Не писать padding/margin вне spacing scale.
9. ❌ Не использовать unicode буллеты (`•`, `-`) для списков — только `<ul class="prose">` или `<li>` с иконкой.
10. ❌ Не ставить `overflow-visible` на страницу — root всегда `overflow-x-hidden`.
11. ❌ Не использовать `text-red-*`, `text-green-*` — только `text-destructive`, `text-success`, `text-accent`.
12. ❌ Не отключать focus-ring для кнопок и инпутов.
13. ❌ Не ставить анимации > 600ms (кроме loop-эффектов).
14. ❌ Не игнорировать `tabular-nums` на числах в KPI/таблицах.
15. ❌ Не заменять `Card` на голый `<div>` без semantic-обёртки.

Обязательно.

- ✅ Каждая интерактивная плитка — с hover-состоянием.
- ✅ `®` и `™` рендерить как `<sup>` (см. mem/core).
- ✅ Mobile ≥ 320px — работает без горизонтального скролла.
- ✅ Все состояния (loading, empty, error) — покрыты.
- ✅ Skeleton для загрузки использует `bg-muted animate-pulse rounded-*`.

---

Design DNA проекта — 25 принципов

1. Deep blue = ДНК. `--primary: 230 80% 56%` — всегда ядро иерархии.
2. Coral acc — только для критичного. Не украшение, а сигнал.
3. 16px радиус — визуальная подпись. Никогда не «острить».
4. Plus Jakarta Sans — единственный шрифт. Serifs и Inter/Poppins — вне закона.
5. Данные — герой. Числа крупнее подписей, `tabular-nums`, right-align в таблицах.
6. Иерархия через мягкость. Тени и прозрачность вместо жирных бордеров.
7. Один primary CTA. Всё остальное — outline / ghost / link.
8. Semantic tokens only. Никаких hex/rgb в компонентах.
9. Mobile-first, но десктоп — приоритет визуально. Прогрессивно расширяем.
10. Space-y ≥ 4 между смысловыми блоками. Никакой «слипшийся» контент.
11. Card padding = 24 (desktop) / 16 (mobile). Компактность на мобиле — норма.
12. Hover обязателен для всего кликабельного. «Мертвый» UI — bug.
13. Duration 200/300ms — sweet spot. Быстрее — резко, медленнее — тормозит.
14. Focus-ring нельзя убирать. Accessibility — не опция.
15. KPI-плитки — квадратные, скруглённые `rounded-2xl`, иконка сверху.
16. Sidebar — всегда тёмный. Даже в light-theme. Это якорь бренда.
17. Glass — только на mesh-фонах. Не «везде».
18. Gradient-mesh — для эмоциональных секций (hero, empty states, celebrations).
19. Иконки lucide 1.5–2 stroke, 16/20/24. Никаких смайлов.
20. `tracking-tight` на всех заголовках. Плотная гарнитура — читается лучше.
21. Skeleton-loading > spinner. Показываем скелет, а не кружок.
22. Empty states = иконка + фраза + CTA. Никогда пустой экран.
23. Errors в форме — inline `text-destructive`. Toast — только для системных.
24. Один экран = одна цель. Всё лишнее в drawer/sheet/dialog.
25. Консистентность > креатив. Новая страница должна быть неотличима от старой.


