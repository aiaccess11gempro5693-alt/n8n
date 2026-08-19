import { motion } from "framer-motion";
import { ArrowRight, Check, Minus } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { CountUp, Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { amplify } = data;

const Amplify = () => (
  <Section id="amplify" className="border-t border-border">
    <SectionTitle>{amplify.title}</SectionTitle>

    <div className="mt-14 grid gap-12 md:grid-cols-2">
      {amplify.figures.map((f, i) => (
        <Reveal key={f.label} delay={i * 0.12}>
          <div className="flex flex-col gap-3">
            <span className="text-5xl md:text-6xl font-medium tracking-tight text-secondary">
              <CountUp value={f.value} suffix={f.suffix} />
            </span>
            <p className="max-w-md text-sm leading-relaxed text-muted-foreground">{f.label}</p>
          </div>
        </Reveal>
      ))}
    </div>

    {/* Путь влияния */}
    <Reveal delay={0.1}>
      <div className="mt-20">
        <p className="text-sm text-muted-foreground">{amplify.flow.title}</p>
        <div className="mt-6 flex flex-col gap-6 lg:flex-row lg:items-center">
          <div className="flex flex-wrap gap-2">
            {amplify.flow.steps.map((step, i) => (
              <motion.span
                key={step}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.45 }}
                className="rounded-full border border-border px-3.5 py-1.5 text-xs text-muted-foreground"
              >
                {step}
              </motion.span>
            ))}
          </div>
          <ArrowRight className="hidden h-5 w-5 shrink-0 text-muted-foreground lg:block" />
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="self-start rounded-full bg-primary px-5 py-2 text-sm font-medium text-primary-foreground lg:self-auto"
          >
            {amplify.flow.hub}
          </motion.div>
          <ArrowRight className="hidden h-5 w-5 shrink-0 text-muted-foreground lg:block" />
          <span className="text-sm text-muted-foreground">{amplify.flow.result}</span>
        </div>
      </div>
    </Reveal>

    {/* Контраст */}
    <div className="mt-20 grid gap-x-14 gap-y-4 md:grid-cols-2">
      <Reveal>
        <p className="pb-4 text-sm font-medium text-muted-foreground">{amplify.comparison.leftTitle}</p>
      </Reveal>
      <Reveal delay={0.1}>
        <p className="pb-4 text-sm font-medium text-primary">{amplify.comparison.rightTitle}</p>
      </Reveal>

      {amplify.comparison.rows.map((row, i) => (
        <div key={i} className="contents">
          <Reveal delay={i * 0.07}>
            <div className="flex items-start gap-3 border-t border-border py-4">
              <Minus className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <p className="text-sm leading-relaxed text-muted-foreground">{row[0]}</p>
            </div>
          </Reveal>
          <Reveal delay={i * 0.07 + 0.06}>
            <div className="flex items-start gap-3 border-t border-border py-4">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <p className="text-sm leading-relaxed text-foreground">{row[1]}</p>
            </div>
          </Reveal>
        </div>
      ))}
    </div>

    <Reveal delay={0.1}>
      <p className="mt-14 max-w-3xl border-l-2 border-secondary pl-5 text-base md:text-lg font-medium leading-relaxed text-foreground">
        {amplify.conclusion}
      </p>
    </Reveal>
  </Section>
);

export default Amplify;
