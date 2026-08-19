Переоформи лендинг. Тексты не трогай.

СТРОГИЕ ЗАПРЕТЫ
- Не менять ни одной строки текста. Файл src/data/content.json не редактировать вообще: ни значения, ни ключи, ни порядок.
- Не менять структуру страницы, порядок секций и состав компонентов. Ничего не добавлять и не удалять.
- Не переписывать заголовки, подписи и кнопки «по смыслу». Меняются только классы оформления.

ЦЕЛЬ
Сейчас страница выглядит бледной: заголовки тонкие, текст мелкий светло-серый, блоки плоские, крупные числа набраны красным. Нужен вид как в наших отчётных проектах CenterPharma: жирные заголовки фирменного синего, белые карточки с мягкой тенью, крупные синие цифры, красный только как акцент.

1. ШРИФТ (src/index.css)
Заменить импорт на:
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
Сейчас подключены веса 400–600, поэтому всё жирнее 600 браузер рисует искусственным утолщением — это и есть причина «тонкого текста».

2. ТОКЕНЫ (src/index.css, блок :root)
--foreground: 220 35% 12%;
--muted-foreground: 220 14% 38%;
--primary: 215 75% 36%;
--muted: 210 22% 95%;
--border: 214 22% 87%;
--radius: 1rem;
--shadow-card: 0 2px 10px -2px hsl(215 40% 20% / 0.06), 0 12px 32px -12px hsl(215 40% 20% / 0.12);
--shadow-elevated: 0 4px 16px -4px hsl(215 40% 20% / 0.1), 0 24px 56px -16px hsl(215 45% 20% / 0.18);
В блоке h1–h6 добавить letter-spacing: -0.022em.

3. TAILWIND (tailwind.config.ts, внутри theme.extend)
boxShadow: { card: "var(--shadow-card)", elevated: "var(--shadow-elevated)" }
backgroundImage: { brand: "var(--gradient-brand)" }
В borderRadius добавить xl: "calc(var(--radius) + 4px)".

4. ЗАГОЛОВКИ
- H1 на первом экране: text-[2.75rem] leading-[1.02] md:text-7xl font-extrabold tracking-tight text-primary.
- SectionTitle в src/components/Reveal.tsx: text-3xl md:text-5xl font-extrabold leading-[1.08] tracking-tight text-primary.
- Заголовки внутри карточек (h3): text-xl font-bold text-foreground.

5. КАРТОЧКИ
Плоские блоки с тонкими границами заменить на карточки: rounded-2xl bg-card p-6 shadow-card md:p-7. Применить в Reality, Pain, Segments, Cases, Faq, в блоке формы FinalCta и в Trust — к цитате, к диаграмме и к каждой цифре доверия.
Внутри сетки карточек: gap-6, у Reveal и внутренних div добавить h-full, чтобы карточки в ряду были одной высоты.

6. ТЕКСТ
Основной текст поднять с text-sm до text-[15px] (в первом экране и во вводных абзацах — text-base или text-lg), leading-relaxed оставить. Подписи и пометки — text-sm font-medium вместо text-xs.

7. ЦВЕТ ЧИСЕЛ
Все крупные числа — синие: text-primary font-extrabold tracking-tight tabular-nums. Это касается 58% и 29,6% на экране «Провизор — центральный узел влияния» (сейчас они красные) и цифр доверия на экране с данными.
Красный (secondary) оставить только акцентом: иконки на экране «Знакомая картина?», вертикальная черта слева у выводов, бейдж «VS», плашка «Резидент Сколково», столбцы коммерческих факторов на диаграмме.

8. ИКОНКИ
Каждую иконку положить в плашку: h-11 w-11 rounded-xl, фон bg-accent для синих иконок и bg-secondary/10 для красных, сама иконка h-5 w-5 strokeWidth={2}.

9. НАДЗАГОЛОВКИ
Мелкие подписи над блоками — «Как устроен путь влияния», «Факторы переключения препарата провизором», «Нам доверяют», «Наши клиенты», «Что можно сделать уже в ближайшие 90 дней», заголовки колонок в обеих таблицах сравнения — набрать капсом: text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground. Правую колонку в таблицах — тем же стилем, но цветом text-primary.

10. КНОПКИ И ПОЛЯ
Кнопки: rounded-full px-8 py-4 text-base font-semibold shadow-card, при наведении shadow-elevated.
Поля формы: сейчас это подчёркивания снизу — сделать полноценные поля rounded-xl border border-border bg-background px-4 py-3.5 text-base, при фокусе focus:border-primary focus:ring-2 focus:ring-primary/20.
Бейджи на первом экране: rounded-full bg-card px-4 py-2 text-sm font-semibold shadow-card вместо тонкой рамки.

11. ШАПКА И ФУТЕР
Шапка: высота h-16; название «ЦентрФарма» — text-base font-extrabold; пункты навигации вывести в строку на xl и выше (rounded-full px-3.5 py-2 text-sm font-semibold, при наведении bg-primary/5 text-primary), бургер оставить только ниже xl; при скролле фон bg-background/90 backdrop-blur-xl shadow-card вместо тонкой линии снизу.
Футер: добавить логотип с названием над заголовком, заголовок — text-xl md:text-2xl font-extrabold, контакты — text-base font-semibold, ссылки на сайты — пилюли bg-white/15 px-4 py-1.5 text-sm font-semibold.

12. ФОН СЕКЦИЙ
Убрать тонкие линии border-t между секциями. Вместо них чередовать фон: секции «Новая реальность», «Провизор — центральный узел», «Решения под задачи», «Кейсы», FAQ — bg-muted/50; остальные — обычный фон.

13. ПЕРВЫЙ ЭКРАН
Иллюстрация со схемой и растущей кривой сейчас скрыта на мобильном (hidden lg:block) — показывать её всегда. Толщину линий в SVG поднять с 2 до 3, радиус точек с 6 до 7.
