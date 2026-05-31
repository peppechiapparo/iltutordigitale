# 02 — Architettura Tecnica

## Principi

1. **Separare deterministico da LLM**: parsing, validazione, sitemap, deploy = funzioni pure/tool.
   L'LLM ragiona e orchestra, non esegue compiti che il codice risolve meglio.
2. **Quick win read-only prima**: portale statico (Fase 1) prima di qualsiasi automazione (Fase 2).
3. **Gate umano sulle azioni**: nessuna pubblicazione/invio email automatico senza approvazione.
4. **Proprietà vs piattaforme**: il portale e la newsletter sono asset di proprietà; i social no.

---

## Stack confermato

### Portale (Fase 1 — il cuore del progetto)
| Layer | Tecnologia | Note |
|-------|-----------|------|
| Framework | **Astro 4.x** (SSG, output statico) | SEO/perf eccellenti su contenuti |
| UI interattiva | React (solo dove serve) via `@astrojs/react` | islands architecture |
| Stile | **Tailwind CSS 3.x** | mobile-first, scala tipografica accessibile |
| Linguaggio | **TypeScript** strict | no `any` impliciti |
| Hosting | **Cloudflare Pages** (free) | CDN globale, SSL automatico, preview per PR |
| Email routing | Cloudflare Email Routing (free) | `info@<dominio>` → casella personale |
| Analytics | Cloudflare Web Analytics (free, privacy-first) | no cookie banner necessario |
| Form | Cloudflare Worker **oppure** Web3Forms/Formspree | vedi §"Worker vs Pages" |
| Newsletter | Brevo (free tier) | double opt-in GDPR |

### Content Engine (Fase 2 — opzionale, automazione)
| Layer | Tecnologia | Note |
|-------|-----------|------|
| Runtime | Python 3.12 | riuso blueprint `KNOW_HOW.md` |
| Agenti | Template Method `Agent.run()` + ReAct loop | `collect→analyze→persist` |
| LLM | Strategy+Factory: Anthropic / OpenAI / **GitHub Models (free)** / Null | provider-agnostic |
| Scheduler | APScheduler | job editoriali ricorrenti |
| Persistenza | SQLite (WAL) | runs + findings |
| Gate umano | Telegram bot (polling) o dashboard | ✅ Approva / ✏️ Modifica / ❌ Scarta |
| Deploy | Docker su nodo edge o VPS economico | `restart: unless-stopped` |

> **Anti-over-engineering**: la Fase 2 si avvia **solo** quando il volume manuale diventa insostenibile.

---

## Diagramma architetturale

```
┌──────────────────────────────────────────────────────────────┐
│                        UTENTE FINALE                          │
└───────────────┬──────────────────────────┬───────────────────┘
                │ HTTPS                      │ social
┌───────────────▼──────────────┐   ┌────────▼──────────────────┐
│   CLOUDFLARE (Edge/CDN/SSL)  │   │ YouTube / FB / IG / TikTok│
│   + Web Analytics + Email    │   └───────────────────────────┘
└───────────────┬──────────────┘
                │
┌───────────────▼──────────────┐
│      CLOUDFLARE PAGES        │  ← sito statico Astro (output: static)
│  deploy auto da GitHub main  │
└───────────────┬──────────────┘
                │ git push / PR (preview deploy)
┌───────────────▼──────────────┐
│       GITHUB REPOSITORY      │  ← source, GitHub Actions, Copilot, Issues
└───────────────┬──────────────┘
                │ sviluppo locale
┌───────────────▼──────────────┐
│         VSCODE + COPILOT      │  ← astro-developer agent, ui-ux skill
└──────────────────────────────┘

  (Fase 2, separato dal sito)
┌──────────────────────────────┐      ┌───────────────────────┐
│  CONTENT ENGINE (Python/Docker)│───►│  Gate umano (Telegram) │
│  script→SEO/AEO→bozze         │     └───────────────────────┘
│  loop dati (YT/GSC/CF Analytics)│
└──────────────────────────────┘
```

---

## Worker vs Pages (lezione dal KNOW_HOW)

> ⚠️ **Worker ≠ Pages.** Sono due prodotti Cloudflare diversi. Confonderli fa perdere ore.

- Il **sito** è servito da **Cloudflare Pages** (deploy automatico da GitHub, build `astro build` → `dist`).
- I **servizi dinamici** (gestione form contatti, eventuale endpoint AI) sono **Cloudflare Workers**
  separati, oppure servizi terzi (Web3Forms/Formspree per i form, Brevo per la newsletter).
- **Non** mescolare le due cose: niente `wrangler pages deploy` se usiamo la integrazione Git di Pages.

---

## Costi

| Servizio | Piano | Costo |
|----------|-------|-------|
| Dominio (.it/.com) | Aruba o Cloudflare Registrar | ~10-15€/anno |
| Cloudflare Pages/CDN/SSL/Email/Analytics | Free | 0€ |
| GitHub Pro + Copilot Pro | Pro | ~4€/mese |
| Brevo (newsletter) | Free (300 email/giorno) | 0€ |
| LLM (Fase 2) | **GitHub Models free tier** per prototipi | 0€ → API a consumo se scala |
| Hosting engine (Fase 2) | VPS economico / nodo edge | ~5€/mese se attivato |
| **Totale Fase 1** | | **~4€/mese + dominio** |

---

## Sicurezza (dal KNOW_HOW, adattata al contesto)

- **Nessun segreto nel codice**: chiavi solo in `.env.local` (locale) e Cloudflare/GitHub Secrets (prod).
- **`.gitignore`** include `.env*`, `node_modules/`, `dist/`.
- **Validazione form** lato client e lato server (Worker o servizio terzo).
- **Rate limiting** Cloudflare sui form per prevenire spam/abuso.
- **HTTPS obbligatorio** (automatico su Cloudflare).
- **Disclosure affiliate** e consensi GDPR (vedi `11`).
- (Fase 2) **Token rotation** e secret store per le API LLM/social; mai loggare prompt con segreti.

---

## Variabili d'ambiente

```env
# .env.local — NON committare
PUBLIC_SITE_URL=https://tutordigitale.com
AMAZON_AFFILIATE_TAG=____________
BREVO_API_KEY=____________
YOUTUBE_API_KEY=____________        # Fase 2 (loop dati)
# Fase 2 content engine:
LLM_PROVIDER=github_models           # anthropic | openai | github_models | null
GITHUB_MODELS_TOKEN=____________     # PAT per GitHub Models (free tier)
```
