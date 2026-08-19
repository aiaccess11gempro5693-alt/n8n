import { Flame, HelpCircle, TrendingDown, Unlink } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;

const icons: Record<string, typeof Flame> = {
  help: HelpCircle,
  "trending-down": TrendingDown,
  flame: Flame,
  unlink: Unlink,
};

const Pain = () => (
  <Section id="pain" className="border-t border-border bg-muted/40">
    <SectionTitle>{data.pain.title}</SectionTitle>

    <div className="mt-14 grid gap-x-14 gap-y-12 md:grid-cols-2">
      {data.pain.items.map((item, i) => {
        const Icon = icons[item.icon] ?? HelpCircle;
        return (
          <Reveal key={item.title} delay={i * 0.1}>
            <div className="flex gap-5">
              <Icon className="mt-1 h-6 w-6 shrink-0 text-secondary" strokeWidth={1.5} />
              <div className="flex flex-col gap-3">
                <h3 className="text-lg font-medium leading-snug text-foreground">{item.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{item.description}</p>
                {item.note && (
                  <p className="rounded-lg border border-border bg-background px-3.5 py-2.5 text-xs text-muted-foreground">
                    {item.note}
                  </p>
                )}
              </div>
            </div>
          </Reveal>
        );
      })}
    </div>
  </Section>
);

export default Pain;
