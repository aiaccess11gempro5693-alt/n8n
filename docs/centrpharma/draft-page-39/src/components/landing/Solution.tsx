import { motion } from "framer-motion";
import { RotateCw } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { solution } = data;

const Solution = () => (
  <Section id="solution" className="border-t border-border bg-muted/40">
    <SectionTitle>{solution.title}</SectionTitle>

    <div className="mt-14 flex flex-wrap items-center gap-x-3 gap-y-4">
      {solution.steps.map((step, i) => (
        <div key={step} className="flex items-center gap-3">
          <motion.span
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.12, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="rounded-full bg-background px-4 py-2 text-sm text-foreground ring-1 ring-border"
          >
            <span className="mr-2 text-xs text-primary">{String(i + 1).padStart(2, "0")}</span>
            {step}
          </motion.span>
          {i < solution.steps.length - 1 && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              whileInView={{ opacity: 1, width: 24 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12 + 0.1, duration: 0.4 }}
              className="hidden h-px bg-border sm:block"
            />
          )}
        </div>
      ))}
    </div>

    <Reveal delay={0.3}>
      <p className="mt-6 inline-flex items-center gap-2 rounded-lg border border-border px-3.5 py-2.5 text-xs text-muted-foreground">
        <RotateCw className="h-3.5 w-3.5 text-primary" />
        {solution.loopNote}
      </p>
    </Reveal>

    <Reveal delay={0.15}>
      <p className="mt-12 max-w-3xl text-base leading-relaxed text-muted-foreground">
        {solution.description}
      </p>
    </Reveal>
  </Section>
);

export default Solution;
