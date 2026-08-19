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
  <Section id="pain">
    <SectionTitle>{data.pain.title}</SectionTitle>

    <div className="mt-14 grid gap-6 md:grid-cols-2">
      {data.pain.items.map((item, i) => {
        const Icon = icons[item.icon] ?? HelpCircle;
        return (
          <Reveal key={item.title} delay={i * 0.1} className="h-full">
            <div className="flex h-full gap-5 rounded-2xl bg-card p-6 shadow-card md:p-7">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-secondary/10">
                <Icon className="h-5 w-5 text-secondary" strokeWidth={2} />
              </span>
              <div className="flex flex-col gap-3">
                <h3 className="text-xl font-bold leading-snug text-foreground">{item.title}</h3>
                <p className="text-[15px] leading-relaxed text-muted-foreground">
                  {item.description}
                </p>
                {item.note && (
                  <p className="mt-auto rounded-xl bg-muted px-4 py-3 text-sm font-semibold text-foreground/80">
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
