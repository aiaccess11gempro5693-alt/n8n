import { Package, Pill, Stethoscope } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;

const icons: Record<string, typeof Pill> = {
  pill: Pill,
  package: Package,
  stethoscope: Stethoscope,
};

const Segments = () => (
  <Section id="segments" className="border-t border-border">
    <SectionTitle>{data.segments.title}</SectionTitle>

    <div className="mt-14 grid gap-12 md:grid-cols-3">
      {data.segments.items.map((item, i) => {
        const Icon = icons[item.icon] ?? Pill;
        return (
          <Reveal key={item.tag} delay={i * 0.12}>
            <div className="flex flex-col gap-5">
              <div className="flex items-center gap-3">
                <Icon className="h-6 w-6 text-primary" strokeWidth={1.5} />
                <span className="rounded-full border border-border px-2.5 py-1 text-[11px] tracking-wide text-muted-foreground">
                  {item.tag}
                </span>
              </div>
              <h3 className="text-lg font-medium leading-snug text-foreground">{item.title}</h3>

              <div className="flex flex-col gap-3 text-sm leading-relaxed">
                <p className="text-muted-foreground">
                  <span className="text-foreground">Задача. </span>
                  {item.task}
                </p>
                <p className="text-muted-foreground">
                  <span className="text-foreground">Решение. </span>
                  {item.solution}
                </p>
              </div>

              <p className="rounded-lg border border-border px-3.5 py-2.5 text-xs text-muted-foreground">
                {item.offer}
              </p>
            </div>
          </Reveal>
        );
      })}
    </div>
  </Section>
);

export default Segments;
