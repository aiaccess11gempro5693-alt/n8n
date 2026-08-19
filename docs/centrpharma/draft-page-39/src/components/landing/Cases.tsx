import { motion } from "framer-motion";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { cases } = data;

const maxValue = Math.max(...cases.items.map((c) => c.after));

const Cases = () => (
  <Section id="cases" className="border-t border-border">
    <SectionTitle>{cases.title}</SectionTitle>

    <Reveal delay={0.1}>
      <p className="mt-8 max-w-3xl text-base leading-relaxed text-muted-foreground">{cases.intro}</p>
    </Reveal>

    <div className="mt-16 grid gap-14 md:grid-cols-3">
      {cases.items.map((item, i) => (
        <Reveal key={item.tag} delay={i * 0.12}>
          <div className="flex flex-col gap-5">
            <div className="flex items-center gap-3">
              <span className="rounded-full border border-border px-2.5 py-1 text-[11px] tracking-wide text-muted-foreground">
                {item.tag}
              </span>
              <span className="text-sm font-medium text-primary">{item.delta}</span>
            </div>
            <h3 className="text-base font-medium leading-snug text-foreground">{item.title}</h3>

            <div className="flex h-40 items-stretch gap-6">
              {[
                { label: "до", value: item.before, accent: false },
                { label: "после", value: item.after, accent: true },
              ].map((bar, bi) => (
                <div key={bar.label} className="flex flex-1 flex-col gap-2">
                  <div className="flex flex-1 flex-col justify-end gap-2">
                    <span className="text-center text-xs tabular-nums text-muted-foreground">
                      {bar.value}
                    </span>
                    <motion.div
                      initial={{ height: 0 }}
                      whileInView={{ height: `${(bar.value / maxValue) * 82}%` }}
                      viewport={{ once: true, amount: 0.5 }}
                      transition={{
                        duration: 1,
                        delay: i * 0.1 + bi * 0.2,
                        ease: [0.22, 1, 0.36, 1],
                      }}
                      className={`w-full rounded-t-md ${bar.accent ? "bg-primary" : "bg-border"}`}
                    />
                  </div>
                  <span className="text-center text-xs text-muted-foreground">{bar.label}</span>
                </div>
              ))}
            </div>


            <p className="text-xs text-muted-foreground">{item.metric}</p>
          </div>
        </Reveal>
      ))}
    </div>

    <Reveal delay={0.1}>
      <p className="mt-12 inline-block rounded-lg border border-border px-3.5 py-2.5 text-xs text-muted-foreground">
        {cases.disclaimer}
      </p>
    </Reveal>
  </Section>
);

export default Cases;
