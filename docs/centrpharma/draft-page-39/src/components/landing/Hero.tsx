import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";

const data = content as SiteContent;

const scrollToCta = () => {
  const el = document.getElementById("cta");
  if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 60, behavior: "smooth" });
};

const Hero = () => (
  <section className="relative flex min-h-[92vh] items-center overflow-hidden px-5 pt-24 pb-16">
    <div
      className="absolute inset-0 -z-10 opacity-[0.06]"
      style={{
        backgroundImage:
          "radial-gradient(circle at 1px 1px, hsl(var(--foreground)) 1px, transparent 0)",
        backgroundSize: "34px 34px",
      }}
    />
    <div className="absolute -top-40 -right-32 -z-10 h-[38rem] w-[38rem] rounded-full bg-primary/10 blur-3xl" />
    <div className="absolute bottom-0 -left-40 -z-10 h-[26rem] w-[26rem] rounded-full bg-secondary/10 blur-3xl" />

    <div className="container max-w-6xl grid gap-14 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
      <div>
        <motion.h1
          initial={{ opacity: 0, y: 26 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-3xl text-4xl md:text-6xl font-medium leading-[1.05] tracking-tight text-foreground"
        >
          {data.hero.title}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
          className="mt-7 max-w-xl text-base md:text-lg leading-relaxed text-muted-foreground"
        >
          {data.hero.subtitle}
        </motion.p>

        <motion.p
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.24, ease: [0.22, 1, 0.36, 1] }}
          className="mt-7 max-w-xl border-l-2 border-secondary pl-5 text-lg md:text-xl font-medium leading-snug text-foreground"
        >
          {data.hero.statement}
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.36, ease: [0.22, 1, 0.36, 1] }}
          className="mt-10"
        >
          <button
            onClick={scrollToCta}
            className="group inline-flex items-center gap-3 rounded-full bg-primary px-7 py-3.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
          >
            {data.hero.cta}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </button>
        </motion.div>

        <motion.ul
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="mt-10 flex flex-wrap gap-2"
        >
          {data.hero.badges.map((badge) => (
            <li
              key={badge}
              className="rounded-full border border-border px-3.5 py-1.5 text-xs text-muted-foreground"
            >
              {badge}
            </li>
          ))}
        </motion.ul>
      </div>

      {/* Схематичная «система»: узлы и растущая динамика */}
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.9, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="relative hidden lg:block"
      >
        <svg viewBox="0 0 420 340" className="w-full">
          <defs>
            <linearGradient id="heroLine" x1="0" y1="1" x2="1" y2="0">
              <stop offset="0%" stopColor="hsl(var(--primary))" />
              <stop offset="100%" stopColor="hsl(var(--secondary))" />
            </linearGradient>
          </defs>
          {[0, 1, 2, 3].map((i) => (
            <line
              key={i}
              x1="30"
              y1={70 + i * 60}
              x2="400"
              y2={70 + i * 60}
              stroke="hsl(var(--border))"
              strokeWidth="1"
            />
          ))}
          {[
            [60, 250],
            [140, 215],
            [220, 165],
            [300, 110],
            [380, 55],
          ].map(([x, y], i) => (
            <g key={i}>
              <motion.circle
                cx={x}
                cy={y}
                r="6"
                fill="hsl(var(--primary))"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.7 + i * 0.13, duration: 0.4 }}
              />
              {i < 4 && (
                <motion.line
                  x1={x}
                  y1={y}
                  x2={[140, 220, 300, 380][i]}
                  y2={[215, 165, 110, 55][i]}
                  stroke="url(#heroLine)"
                  strokeWidth="2"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ delay: 0.8 + i * 0.13, duration: 0.5 }}
                />
              )}
            </g>
          ))}
          <motion.path
            d="M60 250 C 150 250, 250 140, 390 45"
            fill="none"
            stroke="hsl(var(--secondary))"
            strokeWidth="2.5"
            strokeDasharray="6 6"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: 1.1, duration: 1.2 }}
          />
          <motion.path
            d="M372 38 L392 44 L378 58"
            fill="none"
            stroke="hsl(var(--secondary))"
            strokeWidth="2.5"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.2, duration: 0.4 }}
          />
        </svg>
      </motion.div>
    </div>
  </section>
);

export default Hero;
