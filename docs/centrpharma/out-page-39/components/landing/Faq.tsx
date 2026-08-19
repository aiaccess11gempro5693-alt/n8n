import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Plus } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;

const Faq = () => {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <Section id="faq" className="bg-muted/50">
      <SectionTitle>{data.faq.title}</SectionTitle>

      <div className="mt-12 flex max-w-3xl flex-col gap-3">
        {data.faq.items.map((item, i) => (
          <Reveal key={item.q} delay={i * 0.08}>
            <div className="overflow-hidden rounded-2xl bg-card shadow-card">
              <button
                onClick={() => setOpen(open === i ? null : i)}
                aria-expanded={open === i}
                aria-controls={`faq-answer-${i}`}
                className="flex w-full items-start justify-between gap-6 p-6 text-left md:p-7"
              >
                <span className="text-lg font-bold leading-snug text-foreground">{item.q}</span>
                <Plus
                  className={`mt-0.5 h-5 w-5 shrink-0 text-primary transition-transform duration-300 ${
                    open === i ? "rotate-45" : ""
                  }`}
                  strokeWidth={2.5}
                />
              </button>
              <AnimatePresence initial={false}>
                {open === i && (
                  <motion.div
                    id={`faq-answer-${i}`}
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                    className="overflow-hidden"
                  >
                    <p className="px-6 pb-6 text-[15px] leading-relaxed text-muted-foreground md:px-7 md:pb-7">
                      {item.a}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </Reveal>
        ))}
      </div>
    </Section>
  );
};

export default Faq;
