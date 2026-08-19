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
    <Section id="faq" className="border-t border-border">
      <SectionTitle>{data.faq.title}</SectionTitle>

      <div className="mt-12 max-w-3xl">
        {data.faq.items.map((item, i) => (
          <Reveal key={item.q} delay={i * 0.08}>
            <div className="border-t border-border last:border-b">
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="flex w-full items-start justify-between gap-6 py-5 text-left"
              >
                <span className="text-base font-medium leading-snug text-foreground">{item.q}</span>
                <Plus
                  className={`mt-1 h-4 w-4 shrink-0 text-primary transition-transform duration-300 ${
                    open === i ? "rotate-45" : ""
                  }`}
                />
              </button>
              <AnimatePresence initial={false}>
                {open === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                    className="overflow-hidden"
                  >
                    <p className="pb-6 pr-10 text-sm leading-relaxed text-muted-foreground">
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
