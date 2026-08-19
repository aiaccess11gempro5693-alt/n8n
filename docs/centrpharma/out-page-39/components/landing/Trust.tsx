import { motion } from "framer-motion";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { CountUp, Eyebrow, Reveal, Section, SectionTitle, Statement } from "@/components/Reveal";

const data = content as SiteContent;
const { trust } = data;

const Trust = () => (
  <Section id="trust">
    <SectionTitle>{trust.title}</SectionTitle>

    <Reveal delay={0.1}>
      <figure className="mt-10 max-w-3xl rounded-2xl bg-card p-6 shadow-card md:p-8">
        <blockquote className="text-lg md:text-xl font-medium leading-relaxed text-foreground">
          «{trust.quote}»
        </blockquote>
        <figcaption className="mt-4 text-sm font-semibold text-muted-foreground">
          {trust.quoteSource}
        </figcaption>
      </figure>
    </Reveal>

    {/* Диаграмма */}
    <Reveal delay={0.05}>
      <div className="mt-10 max-w-3xl rounded-2xl bg-card p-6 shadow-card md:p-8">
        <Eyebrow>{trust.chart.title}</Eyebrow>

        <div className="mt-8 flex flex-col gap-6">
          {trust.chart.bars.map((bar, i) => (
            <div key={bar.label} className="flex flex-col gap-2">
              <div className="flex items-baseline justify-between gap-4">
                <span className="text-[15px] font-medium text-foreground">{bar.label}</span>
                <span
                  className={`text-base font-bold tabular-nums ${
                    bar.type === "knowledge" ? "text-primary" : "text-muted-foreground"
                  }`}
                >
                  <CountUp value={bar.value} suffix="%" />
                </span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: `${bar.value}%` }}
                  viewport={{ once: true, amount: 0.6 }}
                  transition={{ duration: 1.1, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
                  className={`h-full rounded-full ${
                    bar.type === "knowledge" ? "bg-primary" : "bg-secondary/50"
                  }`}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-7 flex flex-wrap gap-5">
          {trust.chart.legend.map((l) => (
            <span key={l.type} className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  l.type === "knowledge" ? "bg-primary" : "bg-secondary/50"
                }`}
              />
              {l.label}
            </span>
          ))}
        </div>
      </div>
    </Reveal>

    <Reveal delay={0.1}>
      <Statement className="mt-14">{trust.conclusion}</Statement>
    </Reveal>

    {/* Цифры */}
    <Reveal>
      <Eyebrow className="mt-20">{trust.statsTitle}</Eyebrow>
    </Reveal>
    <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {trust.stats.map((s, i) => (
        <Reveal key={s.label} delay={i * 0.1} className="h-full">
          <div className="flex h-full flex-col gap-2 rounded-2xl bg-card p-6 shadow-card">
            <span className="text-4xl md:text-5xl font-extrabold tracking-tight tabular-nums text-primary">
              <CountUp value={s.value} suffix={s.suffix} />
            </span>
            <span className="text-[15px] font-medium text-muted-foreground">{s.label}</span>
          </div>
        </Reveal>
      ))}
    </div>

    <Reveal delay={0.15}>
      <div className="mt-6 flex flex-wrap items-center gap-4">
        <span className="rounded-full bg-secondary px-4 py-2 text-sm font-bold text-secondary-foreground shadow-card">
          {trust.residency}
        </span>
      </div>
    </Reveal>

    {/* Логотипы клиентов */}
    <Reveal>
      <Eyebrow className="mt-20">{trust.clients.title}</Eyebrow>
    </Reveal>
    <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {Array.from({ length: trust.clients.placeholderCount }).map((_, i) => (
        <Reveal key={i} delay={i * 0.05}>
          <div className="flex h-24 items-center justify-center rounded-2xl border-2 border-dashed border-border bg-card/60">
            <span className="text-sm font-medium text-muted-foreground/70">
              {trust.clients.placeholderLabel}
            </span>
          </div>
        </Reveal>
      ))}
    </div>
    <Reveal delay={0.1}>
      <p className="mt-4 text-sm text-muted-foreground">{trust.clients.note}</p>
    </Reveal>

    <Reveal delay={0.1}>
      <p className="mt-10 max-w-3xl text-base leading-relaxed text-muted-foreground">{trust.note}</p>
    </Reveal>
  </Section>
);

export default Trust;
