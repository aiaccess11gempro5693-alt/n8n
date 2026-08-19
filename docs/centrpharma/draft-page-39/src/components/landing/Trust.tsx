import { motion } from "framer-motion";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { CountUp, Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { trust } = data;

const Trust = () => (
  <Section id="trust" className="border-t border-border bg-muted/40">
    <SectionTitle>{trust.title}</SectionTitle>

    <Reveal delay={0.1}>
      <figure className="mt-10 max-w-3xl border-l-2 border-primary pl-5">
        <blockquote className="text-base md:text-lg leading-relaxed text-foreground">
          «{trust.quote}»
        </blockquote>
        <figcaption className="mt-3 text-xs text-muted-foreground">{trust.quoteSource}</figcaption>
      </figure>
    </Reveal>

    {/* Диаграмма */}
    <div className="mt-16 max-w-3xl">
      <Reveal>
        <p className="text-sm text-muted-foreground">{trust.chart.title}</p>
      </Reveal>

      <div className="mt-8 flex flex-col gap-6">
        {trust.chart.bars.map((bar, i) => (
          <Reveal key={bar.label} delay={i * 0.08}>
            <div className="flex flex-col gap-2">
              <div className="flex items-baseline justify-between gap-4">
                <span className="text-sm text-foreground">{bar.label}</span>
                <span
                  className={`text-sm tabular-nums ${
                    bar.type === "knowledge" ? "text-primary" : "text-muted-foreground"
                  }`}
                >
                  <CountUp value={bar.value} suffix="%" />
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-border/60">
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: `${bar.value}%` }}
                  viewport={{ once: true, amount: 0.6 }}
                  transition={{ duration: 1.1, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
                  className={`h-full rounded-full ${
                    bar.type === "knowledge" ? "bg-primary" : "bg-muted-foreground/40"
                  }`}
                />
              </div>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.2}>
        <div className="mt-6 flex flex-wrap gap-5">
          {trust.chart.legend.map((l) => (
            <span key={l.type} className="flex items-center gap-2 text-xs text-muted-foreground">
              <span
                className={`h-2 w-2 rounded-full ${
                  l.type === "knowledge" ? "bg-primary" : "bg-muted-foreground/40"
                }`}
              />
              {l.label}
            </span>
          ))}
        </div>
      </Reveal>
    </div>

    <Reveal delay={0.1}>
      <p className="mt-14 max-w-3xl border-l-2 border-secondary pl-5 text-base md:text-lg font-medium leading-relaxed text-foreground">
        {trust.conclusion}
      </p>
    </Reveal>

    {/* Цифры */}
    <Reveal>
      <p className="mt-20 text-sm text-muted-foreground">{trust.statsTitle}</p>
    </Reveal>
    <div className="mt-8 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
      {trust.stats.map((s, i) => (
        <Reveal key={s.label} delay={i * 0.1}>
          <div className="flex flex-col gap-2">
            <span className="text-3xl md:text-4xl font-medium tracking-tight text-primary">
              <CountUp value={s.value} suffix={s.suffix} />
            </span>
            <span className="text-sm text-muted-foreground">{s.label}</span>
          </div>
        </Reveal>
      ))}
    </div>

    <Reveal delay={0.15}>
      <div className="mt-10 flex flex-wrap items-center gap-4">
        <span className="rounded-full border border-border px-3.5 py-1.5 text-xs text-muted-foreground">
          {trust.residency}
        </span>
      </div>
    </Reveal>

    <Reveal delay={0.1}>
      <p className="mt-8 max-w-3xl text-sm leading-relaxed text-muted-foreground">{trust.note}</p>
    </Reveal>
  </Section>
);

export default Trust;
