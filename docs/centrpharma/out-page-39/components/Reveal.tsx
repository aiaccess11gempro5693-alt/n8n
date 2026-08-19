import { motion } from "framer-motion";
import { useEffect, useRef, useState, type ReactNode } from "react";

export const Reveal = ({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) => (
  <motion.div
    className={className}
    initial={{ opacity: 0, y: 28 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, amount: 0.25 }}
    transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
  >
    {children}
  </motion.div>
);

export const SectionTitle = ({ children }: { children: ReactNode }) => (
  <Reveal>
    <h2 className="max-w-4xl text-3xl md:text-5xl font-extrabold leading-[1.08] tracking-tight text-primary">
      {children}
    </h2>
  </Reveal>
);

/* Надзаголовок: капсом, с разрядкой — как в отчётных проектах */
export const Eyebrow = ({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) => (
  <p className={`text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground ${className}`}>
    {children}
  </p>
);

/* Вывод под блоком: жирная строка с красной чертой слева */
export const Statement = ({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) => (
  <p
    className={`max-w-3xl border-l-4 border-secondary pl-5 text-lg md:text-xl font-semibold leading-snug text-foreground ${className}`}
  >
    {children}
  </p>
);

export const Section = ({
  id,
  children,
  className = "",
}: {
  id?: string;
  children: ReactNode;
  className?: string;
}) => (
  <section id={id} className={`py-20 md:py-28 px-5 ${className}`}>
    <div className="container max-w-6xl">{children}</div>
  </section>
);

const format = (n: number) =>
  Number.isInteger(n) ? n.toLocaleString("ru-RU") : n.toFixed(1).replace(".", ",");

export const CountUp = ({
  value,
  suffix = "",
  duration = 1400,
}: {
  value: number;
  suffix?: string;
  duration?: number;
}) => {
  const ref = useRef<HTMLSpanElement>(null);
  const [display, setDisplay] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting || started.current) return;
        started.current = true;
        const start = performance.now();
        const tick = (now: number) => {
          const p = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          setDisplay(value * eased);
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      },
      { threshold: 0.4 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [value, duration]);

  return (
    <span ref={ref}>
      {format(Number.isInteger(value) ? Math.round(display) : display)}
      {suffix}
    </span>
  );
};
