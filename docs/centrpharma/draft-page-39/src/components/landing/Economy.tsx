import { Check, Minus } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { economy } = data;

const Economy = () => (
  <Section id="economy" className="border-t border-border bg-muted/40">
    <SectionTitle>{economy.title}</SectionTitle>

    <div className="mt-14 grid max-w-4xl gap-x-14 gap-y-0 md:grid-cols-2">
      <Reveal>
        <p className="pb-4 text-sm text-muted-foreground">{economy.leftTitle}</p>
      </Reveal>
      <Reveal delay={0.1}>
        <p className="pb-4 text-sm font-medium text-primary">{economy.rightTitle}</p>
      </Reveal>

      {economy.rows.map((row, i) => (
        <div key={i} className="contents">
          <Reveal delay={i * 0.07}>
            <div className="flex items-start gap-3 border-t border-border py-4">
              <Minus className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">{row[0]}</p>
            </div>
          </Reveal>
          <Reveal delay={i * 0.07 + 0.06}>
            <div className="flex items-start gap-3 border-t border-border py-4">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <p className="text-sm text-foreground">{row[1]}</p>
            </div>
          </Reveal>
        </div>
      ))}
    </div>

    <Reveal delay={0.1}>
      <p className="mt-14 max-w-3xl border-l-2 border-secondary pl-5 text-base md:text-lg font-medium leading-relaxed text-foreground">
        {economy.conclusion}
      </p>
    </Reveal>
  </Section>
);

export default Economy;
