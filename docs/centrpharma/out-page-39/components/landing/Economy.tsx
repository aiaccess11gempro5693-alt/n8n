import { Check, Minus } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Eyebrow, Reveal, Section, SectionTitle, Statement } from "@/components/Reveal";

const data = content as SiteContent;
const { economy } = data;

const Economy = () => (
  <Section id="economy">
    <SectionTitle>{economy.title}</SectionTitle>

    {/* Одна сетка на заголовки и строки — так колонки гарантированно совпадают.
        На мобильном сетка выключена: заголовки идут строкой с «VS»,
        а каждая строка сравнения остаётся парой «минус / плюс». */}
    <Reveal className="mt-14 max-w-4xl rounded-2xl bg-card p-6 shadow-card md:grid md:grid-cols-[1fr_auto_1fr] md:gap-x-8 md:p-8">
      <div className="flex flex-wrap items-center gap-3 md:contents">
        <Eyebrow className="md:pb-4">{economy.leftTitle}</Eyebrow>
        <span className="rounded-full bg-secondary px-4 py-1.5 text-sm font-extrabold tracking-wide text-secondary-foreground md:justify-self-center md:self-start">
          VS
        </span>
        <Eyebrow className="!text-primary md:pb-4">{economy.rightTitle}</Eyebrow>
      </div>

      {economy.rows.map((row, i) => (
        <div key={i} className="mt-4 border-t border-border pt-4 md:mt-0 md:contents">
          <div className="flex items-start gap-3 md:border-t md:border-border md:py-4">
            <Minus className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
            <p className="text-[15px] text-muted-foreground">{row[0]}</p>
          </div>
          <div className="hidden md:block md:border-t md:border-border" />
          <div className="mt-3 flex items-start gap-3 md:mt-0 md:border-t md:border-border md:py-4">
            <Check className="mt-0.5 h-5 w-5 shrink-0 text-primary" strokeWidth={2.5} />
            <p className="text-[15px] font-semibold text-foreground">{row[1]}</p>
          </div>
        </div>
      ))}
    </Reveal>

    <Reveal delay={0.1}>
      <Statement className="mt-14">{economy.conclusion}</Statement>
    </Reveal>
  </Section>
);

export default Economy;
