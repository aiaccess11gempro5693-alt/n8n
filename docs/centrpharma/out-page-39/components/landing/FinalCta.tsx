import { useState, type FormEvent } from "react";
import { ArrowRight, Check } from "lucide-react";
import content from "@/data/content.json";
import type { SiteContent } from "@/types/content";
import { Eyebrow, Reveal, Section, SectionTitle } from "@/components/Reveal";

const data = content as SiteContent;
const { finalCta } = data;

const FinalCta = () => {
  const [sent, setSent] = useState(false);

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const lead = {
      name: String(fd.get("name") ?? ""),
      company: String(fd.get("company") ?? ""),
      contact: String(fd.get("contact") ?? ""),
    };

    if (finalCta.endpoint) {
      fetch(finalCta.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lead),
      }).catch(() => undefined);
    } else {
      /* Приём заявок ещё не подключён — вместо тихой потери лида
         открываем письмо на почту из футера. */
      const body = `Имя: ${lead.name}\nКомпания: ${lead.company}\nКонтакт: ${lead.contact}`;
      window.location.href = `mailto:${data.footer.email}?subject=${encodeURIComponent(
        "Заявка с сайта",
      )}&body=${encodeURIComponent(body)}`;
    }

    setSent(true);
  };

  const inputClass =
    "w-full rounded-xl border border-border bg-background px-4 py-3.5 text-base text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20";

  return (
    <Section id="cta">
      <div className="grid gap-14 lg:grid-cols-2 lg:gap-20">
        <div>
          <SectionTitle>{finalCta.title}</SectionTitle>

          <Reveal delay={0.1}>
            <Eyebrow className="mt-10">{finalCta.listTitle}</Eyebrow>
          </Reveal>

          <ul className="mt-6 flex flex-col gap-4">
            {finalCta.list.map((item, i) => (
              <Reveal key={item} delay={0.15 + i * 0.07}>
                <li className="flex items-start gap-3 text-base font-medium leading-relaxed text-foreground">
                  <Check className="mt-0.5 h-5 w-5 shrink-0 text-primary" strokeWidth={2.5} />
                  {item}
                </li>
              </Reveal>
            ))}
          </ul>
        </div>

        <Reveal delay={0.15}>
          <div className="rounded-2xl bg-card p-7 shadow-elevated md:p-9">
            {sent ? (
              <div className="flex min-h-[18rem] flex-col justify-center gap-3">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                  <Check className="h-6 w-6 text-primary" strokeWidth={2.5} />
                </span>
                <h3 className="text-2xl font-extrabold tracking-tight text-foreground">
                  {finalCta.successTitle}
                </h3>
                <p className="text-base text-muted-foreground">{finalCta.successText}</p>
              </div>
            ) : (
              <form onSubmit={onSubmit} className="flex flex-col gap-5">
                <h3 className="text-2xl font-extrabold tracking-tight text-foreground">
                  {finalCta.formTitle}
                </h3>
                <input
                  required
                  name="name"
                  autoComplete="name"
                  placeholder={finalCta.fields.name}
                  className={inputClass}
                />
                <input
                  required
                  name="company"
                  autoComplete="organization"
                  placeholder={finalCta.fields.company}
                  className={inputClass}
                />
                <input
                  required
                  name="contact"
                  autoComplete="email"
                  placeholder={finalCta.fields.contact}
                  className={inputClass}
                />

                <label className="flex items-start gap-3 text-sm leading-relaxed text-muted-foreground">
                  <input
                    required
                    type="checkbox"
                    name="consent"
                    className="mt-0.5 h-4 w-4 shrink-0 accent-primary"
                  />
                  <span>
                    {finalCta.consent.text}{" "}
                    <a
                      href={finalCta.consent.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-semibold text-primary underline underline-offset-2"
                    >
                      {finalCta.consent.linkLabel}
                    </a>
                  </span>
                </label>

                <button
                  type="submit"
                  className="group mt-1 inline-flex items-center justify-center gap-3 rounded-full bg-primary px-8 py-4 text-base font-semibold text-primary-foreground shadow-card transition hover:shadow-elevated"
                >
                  {finalCta.cta}
                  <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                </button>
                <p className="text-center text-sm font-medium text-muted-foreground">
                  {finalCta.note}
                </p>
              </form>
            )}
          </div>
        </Reveal>
      </div>
    </Section>
  );
};

export default FinalCta;
