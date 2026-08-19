import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import logo from "@/assets/logo.png";
import Hero from "@/components/landing/Hero";
import Reality from "@/components/landing/Reality";
import Pain from "@/components/landing/Pain";
import Amplify from "@/components/landing/Amplify";
import Solution from "@/components/landing/Solution";
import Segments from "@/components/landing/Segments";
import Trust from "@/components/landing/Trust";
import Cases from "@/components/landing/Cases";
import Economy from "@/components/landing/Economy";
import Faq from "@/components/landing/Faq";
import FinalCta from "@/components/landing/FinalCta";

const data = content as SiteContent;

const scrollTo = (id: string) => {
  const el = document.getElementById(id);
  if (el) {
    const top = el.getBoundingClientRect().top + window.scrollY - 64;
    window.scrollTo({ top, behavior: "smooth" });
  }
};

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

  const go = (id: string) => {
    scrollTo(id);
    setMobileOpen(false);
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? "bg-background/90 backdrop-blur-xl shadow-card" : "bg-transparent"
      }`}
    >
      <div className="container max-w-6xl flex items-center justify-between h-16 px-4">
        <div className="flex items-center gap-2.5">
          <img src={logo} alt={data.siteName} className="w-10 h-10 rounded-full object-cover" />
          <span className="text-base font-extrabold tracking-tight">
            <span className="text-secondary">Центр</span>
            <span className="text-primary">Фарма</span>
          </span>
        </div>

        {/* Навигация: в строку на широком экране, в меню на узком */}
        <nav className="hidden xl:flex items-center gap-1">
          {data.nav.map((item) => (
            <button
              key={item.id}
              onClick={() => go(item.id)}
              className="rounded-full px-3.5 py-2 text-sm font-semibold text-foreground/70 transition-colors hover:bg-primary/5 hover:text-primary"
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="relative xl:hidden" ref={menuRef}>
          <button
            aria-label="Меню"
            aria-expanded={mobileOpen}
            className="rounded-xl p-2 transition-colors hover:bg-foreground/5"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? (
              <X className="w-6 h-6 text-foreground" />
            ) : (
              <Menu className="w-6 h-6 text-foreground" />
            )}
          </button>

          <AnimatePresence>
            {mobileOpen && (
              <motion.div
                initial={{ opacity: 0, y: -6, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6, scale: 0.97 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-60 origin-top-right rounded-2xl bg-card p-2 shadow-elevated"
              >
                {data.nav.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => go(item.id)}
                    className="w-full rounded-xl px-3.5 py-2.5 text-left text-sm font-semibold text-foreground/80 transition-colors hover:bg-primary/5 hover:text-primary"
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

/* ───── FOOTER ───── */
const FooterSection = () => (
  <footer className="bg-primary px-5 py-12 text-primary-foreground">
    <div className="container max-w-6xl text-center">
      <div className="mb-6 flex items-center justify-center gap-3">
        <img src={logo} alt={data.siteName} className="h-11 w-11 rounded-full bg-white object-cover" />
        <span className="text-lg font-extrabold tracking-tight">{data.siteName}</span>
      </div>

      <h3 className="mb-5 text-xl md:text-2xl font-extrabold tracking-tight">{data.footer.title}</h3>

      <div className="mb-4 flex flex-col flex-wrap justify-center gap-2 text-base font-semibold sm:flex-row sm:gap-6">
        <a href={`mailto:${data.footer.email}`} className="opacity-90 transition-opacity hover:opacity-100 hover:underline">
          {data.footer.email}
        </a>
        <a href={`tel:${data.footer.phone.replace(/\s/g, "")}`} className="opacity-90 transition-opacity hover:opacity-100 hover:underline">
          {data.footer.phone}
        </a>
        <a
          href={`https://t.me/${data.footer.telegram.replace("@", "")}`}
          target="_blank"
          rel="noopener noreferrer"
          className="opacity-90 transition-opacity hover:opacity-100 hover:underline"
        >
          {data.footer.telegram}
        </a>
      </div>

      <div className="mb-6 flex flex-wrap justify-center gap-2">
        {data.footer.sites.map((s: string, i: number) => (
          <a
            key={i}
            href={`https://${s}`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full bg-white/15 px-4 py-1.5 text-sm font-semibold transition-colors hover:bg-white/25"
          >
            {s}
          </a>
        ))}
      </div>

      <div className="flex flex-col items-center justify-center gap-2 text-sm opacity-80 sm:flex-row sm:gap-4">
        <a href={data.footer.privacy.href} className="transition-opacity hover:opacity-100 hover:underline">
          {data.footer.privacy.label}
        </a>
        <span className="hidden opacity-50 sm:inline">·</span>
        <p>{data.footer.copyright}</p>
      </div>
    </div>
  </footer>
);

const Index = () => (
  <div className="min-h-screen flex flex-col">
    <Header />
    <main>
      <Hero />
      <Reality />
      <Pain />
      <Amplify />
      <Solution />
      <Segments />
      <Trust />
      <Cases />
      <Economy />
      <Faq />
      <FinalCta />
    </main>
    <FooterSection />
  </div>
);

export default Index;
