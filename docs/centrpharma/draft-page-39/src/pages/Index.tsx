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
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? "bg-background/80 backdrop-blur-xl border-b border-border/50 shadow-sm" : "bg-transparent"}`}>
      <div className="container max-w-6xl flex items-center justify-between h-14 px-4">
        <div className="flex items-center gap-2.5">
          <img src={logo} alt={data.siteName} className="w-9 h-9 rounded-full object-cover" />
          <span className="font-medium text-sm tracking-tight">
            <span className="text-secondary">Центр</span>
            <span className="text-primary">Фарма</span>
          </span>
        </div>

        <div className="relative" ref={menuRef}>
          <button
            aria-label="Меню"
            aria-expanded={mobileOpen}
            className="p-2 rounded-lg hover:bg-foreground/5 transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen
              ? <X className={`w-5 h-5 ${scrolled ? "text-foreground" : "text-foreground/70"}`} />
              : <Menu className={`w-5 h-5 ${scrolled ? "text-foreground" : "text-foreground/70"}`} />
            }
          </button>

          <AnimatePresence>
            {mobileOpen && (
              <motion.div
                initial={{ opacity: 0, y: -6, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6, scale: 0.97 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-56 origin-top-right rounded-xl border border-border/60 bg-background/95 backdrop-blur-xl shadow-lg p-1.5"
              >
                {data.nav.map(item => (
                  <button
                    key={item.id}
                    onClick={() => scrollTo(item.id)}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-foreground/70 hover:text-primary hover:bg-primary/5 transition-colors"
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
  <footer className="py-8 bg-primary text-primary-foreground px-5">
    <div className="container max-w-6xl text-center">
      <h3 className="text-base sm:text-lg font-medium mb-3">{data.footer.title}</h3>
      <div className="flex flex-col sm:flex-row flex-wrap justify-center gap-2 sm:gap-4 mb-3 text-xs sm:text-sm">
        <a href={`mailto:${data.footer.email}`} className="hover:underline opacity-90 hover:opacity-100 transition-opacity">{data.footer.email}</a>
        <a href={`tel:${data.footer.phone.replace(/\s/g, "")}`} className="hover:underline opacity-90 hover:opacity-100 transition-opacity">{data.footer.phone}</a>
        <a href={`https://t.me/${data.footer.telegram.replace("@", "")}`} target="_blank" rel="noopener noreferrer" className="hover:underline opacity-90 hover:opacity-100 transition-opacity">{data.footer.telegram}</a>
      </div>
      <div className="flex flex-wrap justify-center gap-2 mb-3">
        {data.footer.sites.map((s: string, i: number) => (
          <a key={i} href={`https://${s}`} target="_blank" rel="noopener noreferrer" className="px-3 py-1 rounded-full bg-white/10 hover:bg-white/20 transition-colors text-xs">{s}</a>
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
