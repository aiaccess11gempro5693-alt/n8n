import { Gauge, Network, ShieldCheck, Sprout } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;

const icons: Record<string, typeof Gauge> = {
  shield: ShieldCheck,
  gauge: Gauge,
  sprout: Sprout,
  network: Network,
};

const Reality = () => (
  <Section id="reality" className="bg-muted/50">
    <SectionTitle>{data.reality.title}</SectionTitle>

    <div className="mt-14 grid gap-6 md:grid-cols-3">
      {data.reality.items.map((item, i) => {
        const Icon = icons[item.icon] ?? Gauge;
        return (
          <Reveal key={item.num} delay={i * 0.12} className="h-full">
            <div className="flex h-full flex-col gap-4 rounded-2xl bg-card p-6 shadow-card md:p-7">
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent">
                  <Icon className="h-5 w-5 text-primary" strokeWidth={2} />
                </span>
                <span className="text-sm font-bold tracking-[0.1em] text-muted-foreground">
                  {item.num}
                </span>
              </div>
              <h3 className="text-xl font-bold leading-snug text-foreground">{item.title}</h3>
              <p className="text-[15px] leading-relaxed text-muted-foreground">{item.description}</p>
              {item.note && (
                <p className="mt-auto rounded-xl bg-muted px-4 py-3 text-sm font-semibold text-foreground/80">
                  {item.note}
                </p>
              )}
            </div>
          </Reveal>
        );
      })}
    </div>
  </Section>
);

export default Reality;
