import { motion } from "framer-motion";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { cases } = data;

/* Масштаб столбцов считается только по кейсам, где есть данные. */
const measured = cases.items.filter((c) => !c.pending && typeof c.after === "number");
const maxValue = measured.length ? Math.max(...measured.map((c) => c.after as number)) : 100;

const Cases = () => (
  <Section id="cases" className="bg-muted/50">
    <SectionTitle>{cases.title}</SectionTitle>

    <Reveal delay={0.1}>
      <p className="mt-8 max-w-3xl text-base leading-relaxed text-muted-foreground">{cases.intro}</p>
    </Reveal>

    <div className="mt-14 grid gap-6 md:grid-cols-3">
      {cases.items.map((item, i) => (
        <Reveal key={item.tag} delay={i * 0.12} className="h-full">
          <div className="flex h-full flex-col gap-5 rounded-2xl bg-card p-6 shadow-card md:p-7">
            <div className="flex items-center gap-3">
              <span className="rounded-full bg-primary px-3 py-1 text-xs font-bold tracking-wide text-primary-foreground">
                {item.tag}
              </span>
              <span
                className={`text-2xl font-extrabold tracking-tight ${
                  item.pending ? "text-muted-foreground/60" : "text-primary"
                }`}
              >
                {item.delta}
              </span>
            </div>
            <h3 className="text-lg font-bold leading-snug text-foreground">{item.title}</h3>

            {item.pending ? (
              <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border bg-muted/60">
                <span className="text-4xl font-extrabold tracking-tight text-muted-foreground/60">
                  {item.delta}
                </span>
                <span className="text-sm font-medium text-muted-foreground">
                  {cases.pendingLabel}
                </span>
              </div>
            ) : (
              <div className="flex h-40 items-stretch gap-6">
                {[
                  { label: "до", value: item.before as number, accent: false },
                  { label: "после", value: item.after as number, accent: true },
                ].map((bar, bi) => (
                  <div key={bar.label} className="flex flex-1 flex-col gap-2">
                    <div className="flex flex-1 flex-col justify-end gap-2">
                      <span className="text-center text-sm font-bold tabular-nums text-foreground">
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
                        className={`w-full rounded-t-lg ${bar.accent ? "bg-primary" : "bg-muted"}`}
                      />
                    </div>
                    <span className="text-center text-sm font-medium text-muted-foreground">
                      {bar.label}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <p className="mt-auto text-sm font-medium text-muted-foreground">{item.metric}</p>
          </div>
        </Reveal>
      ))}
    </div>

    <Reveal delay={0.1}>
      <p className="mt-10 inline-block rounded-xl bg-card px-4 py-3 text-sm text-muted-foreground shadow-card">
        {cases.disclaimer}
      </p>
    </Reveal>
  </Section>
);

export default Cases;
