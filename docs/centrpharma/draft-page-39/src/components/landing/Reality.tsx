import { Gauge, Network, ShieldCheck } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;

const icons: Record<string, typeof Gauge> = {
  shield: ShieldCheck,
  gauge: Gauge,
  network: Network,
};

const Reality = () => (
  <Section id="reality" className="border-t border-border">
    <SectionTitle>{data.reality.title}</SectionTitle>

    <div className="mt-14 grid gap-12 md:grid-cols-3">
      {data.reality.items.map((item, i) => {
        const Icon = icons[item.icon] ?? Gauge;
        return (
          <Reveal key={item.num} delay={i * 0.12}>
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <Icon className="h-6 w-6 text-primary" strokeWidth={1.5} />
                <span className="text-sm text-muted-foreground">{item.num}</span>
              </div>
              <h3 className="text-lg font-medium leading-snug text-foreground">{item.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{item.description}</p>
              {item.note && (
                <p className="mt-1 rounded-lg border border-border px-3.5 py-2.5 text-xs text-muted-foreground">
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
