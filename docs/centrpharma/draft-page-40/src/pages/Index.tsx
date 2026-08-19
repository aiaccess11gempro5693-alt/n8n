import { useState, useEffect, useRef, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, MessageSquare, ArrowDown } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent, Section } from "@/types/content";
import logo from "@/assets/logo.png";

const data = content as SiteContent;

/* ───── RICH TEXT: ==жёлтая заливка==, [[прокомментированный текст]] ───── */
const RichText = ({ text }: { text: string }) => {
  const parts = text.split(/(==[^=]+==|\[\[[^\]]+\]\])/g).filter(Boolean);
  return (
    <>
      {parts.map((p, i) => {
        if (p.startsWith("==") && p.endsWith("==")) {
          return (
            <mark key={i} className="bg-highlight text-highlight-foreground px-0.5 rounded-sm">
              <RichText text={p.slice(2, -2)} />
            </mark>
          );
        }
        if (p.startsWith("[[") && p.endsWith("]]")) {
          return (
            <span
              key={i}
              className="text-comment bg-comment/10 border-b-2 border-comment/50 px-0.5 rounded-sm"
            >
              <RichText text={p.slice(2, -2)} />
            </span>
          );
        }
        return <span key={i}>{p}</span>;
      })}
    </>
  );
};

/* ───── REVEAL ───── */
const Reveal = ({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 24 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-60px" }}
    transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    className={className}
  >
    {children}
  </motion.div>
);

/* ───── HEADER ───── */
const Header = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMobileOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      const top = el.getBoundingClientRect().top + window.scrollY - 60;
      window.scrollTo({ top, behavior: "smooth" });
    }
    setMobileOpen(false);
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-background/80 backdrop-blur-xl border-b border-border/50 shadow-sm"
          : "bg-transparent"
      }`}
    >
      <div className="container max-w-6xl flex items-center justify-between h-14 px-4">
        <div className="flex items-center gap-2.5">
          <img src={logo} alt={data.siteName} className="w-9 h-9 rounded-full object-cover" />
          <span className="font-semibold text-sm tracking-tight">
            <span className="text-secondary">{data.brand.first}</span>
            <span className="text-primary">{data.brand.second}</span>
          </span>
        </div>

        <div className="relative" ref={menuRef}>
          <button
            aria-label={data.ui.menuLabel}
            aria-expanded={mobileOpen}
            className="p-2 rounded-lg hover:bg-foreground/5 transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? (
              <X className="w-5 h-5 text-foreground" />
            ) : (
              <Menu className={`w-5 h-5 ${scrolled ? "text-foreground" : "text-foreground/70"}`} />
            )}
          </button>

          <AnimatePresence>
            {mobileOpen && (
              <motion.div
                initial={{ opacity: 0, y: -6, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6, scale: 0.97 }}
                transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
                className="absolute right-0 top-full mt-2 w-60 max-h-[70vh] overflow-y-auto rounded-xl border border-border bg-background/95 backdrop-blur-xl shadow-lg p-1.5"
              >
                {data.nav.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => scrollTo(item.id)}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-foreground/75 hover:text-primary hover:bg-primary/5 transition-colors"
                  >
                    {item.label}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
};

/* ───── HERO ───── */
const Hero = () => (
  <section className="relative min-h-[88vh] flex items-center overflow-hidden bg-gradient-to-br from-primary/5 via-background to-secondary/5">
    <div
      className="absolute inset-0 opacity-[0.04]"
      style={{
        backgroundImage: "radial-gradient(circle at 1px 1px, hsl(var(--foreground)) 1px, transparent 0)",
        backgroundSize: "40px 40px",
      }}
    />
    <div className="container relative z-10 max-w-5xl px-4 py-28">
      <Reveal>
        <p className="text-primary tracking-[0.35em] text-xs md:text-sm mb-6">{data.hero.brand}</p>
      </Reveal>
      <Reveal delay={0.1}>
        <h1 className="text-4xl md:text-6xl font-semibold tracking-tight text-foreground max-w-3xl leading-[1.1]">
          {data.hero.title}
        </h1>
      </Reveal>
      <Reveal delay={0.2}>
        <p className="mt-6 text-base md:text-lg text-muted-foreground max-w-2xl leading-relaxed">
          {data.hero.subtitle}
        </p>
      </Reveal>
      <Reveal delay={0.3}>
        <div className="mt-8 inline-flex items-center rounded-lg border border-border px-4 py-2 text-xs md:text-sm text-muted-foreground">
          {data.hero.note}
        </div>
      </Reveal>
      <Reveal delay={0.4}>
        <div className="mt-10">
          <a
            href="#contacts"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-7 py-3 text-primary-foreground text-sm shadow-lg hover:opacity-90 transition-opacity"
          >
            {data.hero.cta}
          </a>
        </div>
      </Reveal>
    </div>
  </section>
);

/* ───── COMMENTS ───── */
const Comments = ({ section }: { section: Section }) => {
  if (!section.comments?.length) return null;
  return (
    <div className="mt-8 space-y-3">
      {section.comments.map((c, i) => (
        <Reveal key={i} delay={i * 0.08}>
          <div className="rounded-lg border border-comment/40 bg-comment/5 px-4 py-3 text-sm">
            <div className="flex items-center gap-2 text-comment mb-1.5">
              <MessageSquare className="w-3.5 h-3.5" />
              <span className="text-xs font-medium">{data.ui.commentLabel} · {c.author}</span>
            </div>
            <p className="text-comment/80 text-xs italic mb-1.5">«{c.target}»</p>
            <p className="text-comment font-medium">{c.text}</p>
          </div>
        </Reveal>
      ))}
    </div>
  );
};

/* ───── BLOCK ───── */
const Block = ({ section, index }: { section: Section; index: number }) => (
  <section
    id={section.id}
    className={`py-20 md:py-24 px-4 ${index % 2 === 1 ? "bg-muted/40" : "bg-background"}`}
  >
    <div className="container max-w-5xl">
      <Reveal>
        <div className="flex items-baseline gap-4 mb-3">
          <span className="text-xs text-primary/60 tabular-nums">{section.num}</span>
          {section.kicker && (
            <span className="text-xs text-secondary tracking-wide">{section.kicker}</span>
          )}
        </div>
        <h2 className="text-2xl md:text-4xl font-semibold tracking-tight text-foreground max-w-3xl leading-tight">
          {section.title}
        </h2>
      </Reveal>

      {section.lead && (
        <div className="mt-6 space-y-2 max-w-3xl">
          {section.lead.map((l, i) => (
            <Reveal key={i} delay={0.05 + i * 0.06}>
              <p className="text-base md:text-lg text-muted-foreground leading-relaxed">
                <RichText text={l} />
              </p>
            </Reveal>
          ))}
        </div>
      )}

      {section.list && (
        <div className="mt-8 max-w-3xl">
          {section.listTitle && (
            <Reveal>
              <p className="text-xs tracking-[0.2em] uppercase text-primary/70 mb-4">
                {section.listTitle}
              </p>
            </Reveal>
          )}
          <ul className="space-y-3">
            {section.list.map((item, i) => (
              <Reveal key={i} delay={i * 0.07}>
                <li className="flex items-start gap-3 text-base md:text-lg text-foreground/85">
                  <span className="mt-2.5 w-1.5 h-1.5 rounded-full bg-secondary shrink-0" />
                  <span>
                    <RichText text={item} />
                  </span>
                </li>
              </Reveal>
            ))}
          </ul>
        </div>
      )}

      {section.flow && (
        <div className="mt-10 max-w-xl">
          {section.flow.map((step, i) => (
            <Reveal key={i} delay={i * 0.12}>
              <div>
                <div className="flex items-center gap-4">
                  <span className="w-8 h-8 shrink-0 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center tabular-nums">
                    {i + 1}
                  </span>
                  <span className="text-base md:text-lg text-foreground/90">
                    <RichText text={step} />
                  </span>
                </div>
                {i < section.flow!.length - 1 && (
                  <div className="ml-4 my-1 flex items-center text-primary/40">
                    <ArrowDown className="w-4 h-4" />
                  </div>
                )}
              </div>
            </Reveal>
          ))}
        </div>
      )}

      {section.stats && (
        <div className="mt-10 grid sm:grid-cols-3 gap-8">
          {section.stats.map((s, i) => (
            <Reveal key={i} delay={i * 0.12}>
              <div>
                <p className="text-3xl md:text-5xl font-semibold text-primary tracking-tight">
                  {s.value}
                </p>
                <p className="mt-2 text-sm md:text-base text-muted-foreground">
                  <RichText text={s.label} />
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      )}

      {section.cards && (
        <div className="mt-10 grid md:grid-cols-3 gap-8">
          {section.cards.map((c, i) => (
            <Reveal key={i} delay={i * 0.12}>
              <div className="border-t-2 border-secondary/60 pt-4">
                <h3 className="text-lg md:text-xl text-foreground mb-2">
                  <RichText text={c.title} />
                </h3>
                <p className="text-sm md:text-base text-muted-foreground">{c.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      )}

      {section.segments && (
        <div className="mt-10 space-y-6">
          {section.segments.map((s, i) => (
            <Reveal key={i} delay={i * 0.12}>
              <div>
                <div className="flex items-center gap-4 mb-2">
                  <span className="text-sm tracking-[0.2em] text-primary w-20">{s.level}</span>
                  <span className="text-base md:text-lg text-foreground/85">{s.text}</span>
                </div>
                <div className="h-1 rounded-full bg-muted overflow-hidden max-w-xl">
                  <motion.div
                    className="h-full bg-primary"
                    initial={{ width: 0 }}
                    whileInView={{ width: `${100 - i * 33}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.9, delay: 0.15 + i * 0.12, ease: [0.22, 1, 0.36, 1] }}
                  />
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      )}

      {section.compare && (
        <div className="mt-10">
          <div className="grid sm:grid-cols-[1fr_auto_1fr] items-center gap-4 max-w-3xl">
            <Reveal>
              <p className="text-base md:text-lg text-muted-foreground">{section.compare.left}</p>
            </Reveal>
            <Reveal delay={0.1}>
              <span className="text-xs tracking-[0.2em] text-secondary">VS</span>
            </Reveal>
            <Reveal delay={0.2}>
              <p className="text-base md:text-lg text-foreground">{section.compare.right}</p>
            </Reveal>
          </div>
          <div className="mt-8 max-w-3xl divide-y divide-border">
            {section.compare.params.map((p, i) => (
              <Reveal key={i} delay={i * 0.08}>
                <p className="py-3 text-base text-foreground/80">{p}</p>
              </Reveal>
            ))}
          </div>
        </div>
      )}

      {section.caseBlocks && (
        <div className="mt-10 space-y-8 max-w-3xl">
          {section.caseBlocks.map((b, i) => (
            <Reveal key={i} delay={i * 0.12}>
              <div>
                <p className="text-xs tracking-[0.2em] uppercase text-primary/70 mb-2">{b.label}</p>
                <p className="text-base md:text-lg text-foreground/85">
                  <RichText text={b.text} />
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      )}

      {section.logos && (
        <div className="mt-10 grid grid-cols-2 md:grid-cols-3 gap-6">
          {section.logos.map((_, i) => (
            <Reveal key={i} delay={i * 0.08}>
              <div className="h-20 rounded-lg border border-dashed border-border flex items-center justify-center text-xs text-muted-foreground">
                {data.ui.logoPlaceholder}
              </div>
            </Reveal>
          ))}
        </div>
      )}

      {section.contacts && (
        <div className="mt-10 grid sm:grid-cols-2 gap-6 max-w-3xl">
          {section.contacts.map((c, i) => (
            <Reveal key={i} delay={i * 0.1}>
              <div>
                <p className="text-xs tracking-[0.2em] uppercase text-primary/70 mb-1">{c.label}</p>
                <a
                  href={c.href}
                  className="text-base md:text-lg text-foreground hover:text-primary transition-colors"
                >
                  {c.value}
                </a>
              </div>
            </Reveal>
          ))}
        </div>
      )}

      {section.note && (
        <Reveal delay={0.1}>
          <div className="mt-8 inline-block rounded-lg border border-border bg-card px-4 py-3 text-xs md:text-sm text-muted-foreground max-w-md">
            {section.note}
          </div>
        </Reveal>
      )}

      {section.offer && (
        <Reveal delay={0.1}>
          <p className="mt-8 text-lg md:text-2xl text-primary max-w-3xl leading-snug">
            {section.offer}
          </p>
        </Reveal>
      )}

      {section.conclusion && (
        <Reveal delay={0.1}>
          <p className="mt-8 border-l-2 border-secondary pl-5 text-lg md:text-2xl text-foreground max-w-3xl leading-snug">
            {section.conclusion}
          </p>
        </Reveal>
      )}

      <Comments section={section} />
    </div>
  </section>
);

/* ───── FOOTER ───── */
const FooterSection = () => (
  <footer className="py-6 bg-primary text-primary-foreground px-4">
    <div className="container max-w-5xl text-center">
      <h3 className="text-base sm:text-lg font-semibold mb-3">{data.footer.title}</h3>
      <div className="flex flex-col sm:flex-row flex-wrap justify-center gap-2 sm:gap-4 mb-3 text-xs sm:text-sm">
        <a href={`mailto:${data.footer.email}`} className="hover:underline opacity-90">
          {data.footer.email}
        </a>
        <a href={`tel:${data.footer.phone.replace(/\s/g, "")}`} className="hover:underline opacity-90">
          {data.footer.phone}
        </a>
      </div>
      <div className="flex flex-wrap justify-center gap-2 mb-3">
        {data.footer.sites.map((s, i) => (
          <a
            key={i}
            href={`https://${s}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1 rounded-full bg-primary-foreground/10 hover:bg-primary-foreground/20 transition-colors text-xs"
          >
            {s}
          </a>
        ))}
      </div>
      <p className="text-xs opacity-80">{data.footer.copyright}</p>
    </div>
  </footer>
);

const Index = () => (
  <div className="min-h-screen flex flex-col">
    <Header />
    <main>
      <Hero />
      {data.sections.map((s, i) => (
        <Block key={s.id} section={s} index={i} />
      ))}
    </main>
    <FooterSection />
  </div>
);

export default Index;
