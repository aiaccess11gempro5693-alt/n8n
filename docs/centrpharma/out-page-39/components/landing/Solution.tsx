import { motion } from "framer-motion";
import { ArrowRight, RotateCw } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { solution } = data;

const entrySteps = solution.steps.slice(0, solution.loopStartIndex);
const loopSteps = solution.steps.slice(solution.loopStartIndex);

const Chip = ({ step, index, delay }: { step: string; index: number; delay: number }) => (
  <motion.span
    initial={{ opacity: 0, y: 14 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ delay, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
    className="rounded-full bg-card px-5 py-2.5 text-sm font-semibold text-foreground shadow-card"
  >
    <span className="mr-2 text-xs font-bold text-primary">{String(index + 1).padStart(2, "0")}</span>
    {step}
  </motion.span>
);

const Solution = () => (
  <Section id="solution">
    <SectionTitle>{solution.title}</SectionTitle>

    {/* Вход в процесс */}
    <div className="mt-14 flex flex-wrap items-center gap-x-3 gap-y-4">
      {entrySteps.map((step, i) => (
        <div key={step} className="flex items-center gap-3">
          <Chip step={step} index={i} delay={i * 0.12} />
          <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        </div>
      ))}
    </div>

    {/* Замкнутый цикл: по ТЗ возврат идёт к «Измерению лояльности» */}
    <div className="mt-5 rounded-2xl border-2 border-dashed border-primary/30 bg-muted/50 p-5 md:p-7">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-4">
        {loopSteps.map((step, i) => (
          <div key={step} className="flex items-center gap-3">
            <Chip
              step={step}
              index={solution.loopStartIndex + i}
              delay={(solution.loopStartIndex + i) * 0.12}
            />
            {i < loopSteps.length - 1 && (
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-start gap-2.5 border-t-2 border-dashed border-primary/20 pt-5 text-sm font-semibold text-foreground/80">
        <RotateCw className="mt-0.5 h-4 w-4 shrink-0 text-primary" strokeWidth={2.5} />
        <span>{solution.loopNote}</span>
      </div>
    </div>

    <Reveal delay={0.15}>
      <p className="mt-12 max-w-3xl text-base leading-relaxed text-muted-foreground">
        {solution.description}
      </p>
    </Reveal>
  </Section>
);

export default Solution;
