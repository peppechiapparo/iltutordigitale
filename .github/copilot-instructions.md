# Il Tutor Digitale — Istruzioni per Copilot

Portale web + canale multi-piattaforma di **tutorial tecnologici per italiani over 45-65 principianti**.
Creator/persona: **Giuseppe**. Dominio: **tutordigitale.com** (Cloudflare Pages).

## Lingua
Tutto il codice, i commenti, i commit e i contenuti sono in **italiano**.

## Stack
- **Portale** (`web/`): Astro 5 + Tailwind 3 + TypeScript strict → Cloudflare Pages (SSG, `output: static`).
- **Content engine** (`engine/`, Fase 4, predisposto ma non ancora attivo): Python 3.12.
- **Deploy**: GitHub Actions → Cloudflare Pages (automatico). Nessun deploy manuale.

## Regole di codice
- TypeScript **strict**: niente `any` implicito, tipi espliciti.
- Componenti UI in `web/src/components/` (`.astro`), UI base in `components/ui/`.
- Dati centralizzati in `web/src/data/site.ts`. URL sito da `PUBLIC_SITE_URL`.
- Token brand **solo** via classi `brand-*` di Tailwind (vedi `tailwind.config.mjs`). Mai colori inline.

## Accessibilità (pubblico over 45) — NON negoziabile
- Testo corpo minimo **17px**, interlinea ≥ 1.6.
- Target tocco ≥ **48px**. Focus sempre visibile (outline arancione 3px).
- Contrasto WCAG **AA**. Mobile-first. Linguaggio semplice, niente gergo tecnico non spiegato.

## SEO / AEO
- Ogni pagina usa `SEOHead.astro` (meta, OG, canonical, JSON-LD).
- Articoli/tutorial: dopo l'H1 una **risposta sintetica "In breve"** (40-60 parole).
- Structured data: Article, FAQPage, HowTo, Video, Person. Vedi skill `seo-aeo-structured-data`.

## Compliance
- **GDPR + fisco IT** (no NIS2/ECSS): double opt-in newsletter, disclosure affiliate, P.IVA in monetizzazione.
- Segreti solo in `.env.local` / Secrets Cloudflare-GitHub. Mai nel codice o nei log.

## Riferimenti
- Documentazione completa in `docs/`. Fonte di verità per visione, architettura, brand, contenuti.
- Skill di progetto: `.github/skills/tutor-digitale-design`, `.github/skills/seo-aeo-structured-data`.
