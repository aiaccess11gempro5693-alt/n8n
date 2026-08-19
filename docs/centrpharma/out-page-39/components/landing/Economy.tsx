import { Check, Minus } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { economy } = data;

const Economy = () => (
  <Section id="economy" className="border-t border-border bg-muted/40">
    <SectionTitle>{economy.title}</SectionTitle>

    <div className="mt-14 max-w-4xl">
      {/* Шапка сравнения: на мобильном — одной строкой, на десктопе — над колонками */}
      <Reveal>
        <div className="flex flex-wrap items-center gap-3 md:grid md:grid-cols-[1fr_auto_1fr] md:gap-x-8">
          <p className="text-sm text-muted-foreground">{economy.leftTitle}</p>
          <span className="rounded-full bg-secondary px-3 py-1 text-xs font-medium tracking-wide text-secondary-foreground">
            VS
          </span>
          <p className="text-sm font-medium text-primary">{economy.rightTitle}</p>
        </div>
      </Reveal>

      <Reveal delay={0.1}>
        <div className="mt-6 md:grid md:grid-cols-[1fr_auto_1fr] md:gap-x-8">
          {economy.rows.map((row, i) => (
            <div key={i} className="border-t border-border py-4 md:contents">
              <div className="flex items-start gap-3 md:border-t md:border-border md:py-4">
                <Minus className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">{row[0]}</p>
              </div>
              <div className="hidden md:block md:border-t md:border-border" />
              <div className="mt-3 flex items-start gap-3 md:mt-0 md:border-t md:border-border md:py-4">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <p className="text-sm text-foreground">{row[1]}</p>
              </div>
            </div>
          ))}
        </div>
      </Reveal>
    </div>

    <Reveal delay={0.1}>
      <p className="mt-14 max-w-3xl border-l-2 border-secondary pl-5 text-base md:text-lg font-medium leading-relaxed text-foreground">
        {economy.conclusion}
      </p>
    </Reveal>
  </Section>
);

export default Economy;
