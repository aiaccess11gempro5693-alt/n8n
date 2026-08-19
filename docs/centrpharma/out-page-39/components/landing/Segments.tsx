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
  <Section id="segments" className="bg-muted/50">
    <SectionTitle>{data.segments.title}</SectionTitle>

    <div className="mt-14 grid gap-6 md:grid-cols-3">
      {data.segments.items.map((item, i) => {
        const Icon = icons[item.icon] ?? Pill;
        return (
          <Reveal key={item.tag} delay={i * 0.12} className="h-full">
            <div className="flex h-full flex-col gap-5 rounded-2xl bg-card p-6 shadow-card md:p-7">
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent">
                  <Icon className="h-5 w-5 text-primary" strokeWidth={2} />
                </span>
                <span className="rounded-full bg-primary px-3 py-1 text-xs font-bold tracking-wide text-primary-foreground">
                  {item.tag}
                </span>
              </div>
              <h3 className="text-xl font-bold leading-snug text-foreground">{item.title}</h3>

              <div className="flex flex-col gap-3 text-[15px] leading-relaxed">
                <p className="text-muted-foreground">
                  <span className="font-bold text-foreground">Задача. </span>
                  {item.task}
                </p>
                <p className="text-muted-foreground">
                  <span className="font-bold text-foreground">Решение. </span>
                  {item.solution}
                </p>
              </div>

              <p className="mt-auto rounded-xl bg-muted px-4 py-3 text-sm font-semibold text-foreground/80">
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
