import { motion } from "framer-motion";
import { ArrowRight, Check, Minus } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { CountUp, Eyebrow, Reveal, Section, SectionTitle, Statement } from "@/components/Reveal";

const data = content as SiteContent;
const { amplify } = data;

/* Стрелка: вниз на мобильном, вправо на широком экране */
const FlowArrow = () => (
  <ArrowRight className="h-5 w-5 shrink-0 rotate-90 text-muted-foreground lg:rotate-0" />
);

const Amplify = () => (
  <Section id="amplify" className="bg-muted/50">
    <SectionTitle>{amplify.title}</SectionTitle>

    <div className="mt-14 grid gap-6 md:grid-cols-2">
      {amplify.figures.map((f, i) => (
        <Reveal key={f.label} delay={i * 0.12} className="h-full">
          <div className="flex h-full flex-col gap-3 rounded-2xl bg-card p-7 shadow-card md:p-8">
            <span className="text-6xl md:text-7xl font-extrabold tracking-tight tabular-nums text-primary">
              <CountUp value={f.value} suffix={f.suffix} />
            </span>
            <p className="max-w-md text-[15px] leading-relaxed text-muted-foreground">{f.label}</p>
          </div>
        </Reveal>
      ))}
    </div>

    {/* Путь влияния: производитель → каналы → провизор → продажи */}
    <Reveal delay={0.1}>
      <div className="mt-16 rounded-2xl bg-card p-6 shadow-card md:p-8">
        <Eyebrow>{amplify.flow.title}</Eyebrow>

        <div className="mt-6 flex flex-col items-start gap-4 lg:flex-row lg:items-center lg:gap-5">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45 }}
            className="rounded-full bg-muted px-5 py-2.5 text-sm font-bold text-foreground"
          >
            {amplify.flow.source}
          </motion.span>

          <FlowArrow />

          <div className="flex flex-wrap gap-2">
            {amplify.flow.steps.map((step, i) => (
              <motion.span
                key={step}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 + i * 0.08, duration: 0.45 }}
                className="rounded-full border border-border px-4 py-2 text-sm font-medium text-muted-foreground"
              >
                {step}
              </motion.span>
            ))}
          </div>

          <FlowArrow />

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="rounded-full bg-primary px-6 py-2.5 text-sm font-bold text-primary-foreground shadow-card"
          >
            {amplify.flow.hub}
          </motion.div>

          <FlowArrow />

          <span className="text-sm font-semibold text-foreground">{amplify.flow.result}</span>
        </div>
      </div>
    </Reveal>

    {/* Контраст: цена ошибки против системной работы.
        Одна сетка на заголовки и строки — колонки совпадают по вертикали.
        На мобильном каждая строка остаётся парой «минус / плюс». */}
    <Reveal className="mt-16 max-w-4xl md:grid md:grid-cols-2 md:gap-x-14">
      <div className="flex flex-col gap-1 md:contents">
        <Eyebrow className="md:pb-4">{amplify.comparison.leftTitle}</Eyebrow>
        <Eyebrow className="!text-primary md:pb-4">{amplify.comparison.rightTitle}</Eyebrow>
      </div>

      {amplify.comparison.rows.map((row, i) => (
        <div key={i} className="mt-4 border-t border-border pt-4 md:mt-0 md:contents">
          <div className="flex items-start gap-3 md:border-t md:border-border md:py-4">
            <Minus className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
            <p className="text-[15px] leading-relaxed text-muted-foreground">{row[0]}</p>
          </div>
          <div className="mt-3 flex items-start gap-3 md:mt-0 md:border-t md:border-border md:py-4">
            <Check className="mt-0.5 h-5 w-5 shrink-0 text-primary" strokeWidth={2.5} />
            <p className="text-[15px] font-medium leading-relaxed text-foreground">{row[1]}</p>
          </div>
        </div>
      ))}
    </Reveal>

    <Reveal delay={0.1}>
      <Statement className="mt-14">{amplify.conclusion}</Statement>
    </Reveal>
  </Section>
);

export default Amplify;
