# Il Tutor Digitale — Documentazione di Progetto

> Stack: GitHub + GitHub Copilot Pro + Cloudflare Pages + VSCode  
> Dominio: acquistato su Aruba o Cloudflare Registrar  
> Aggiornato: Giugno 2026

---

## Struttura dei file di documentazione

```
tutor-digitale-docs/
├── README.md                    ← questo file
├── 01-ARCHITETTURA.md           ← stack tecnico completo e decisioni architetturali
├── 02-SETUP-AMBIENTE.md         ← configurazione VSCode, GitHub, Cloudflare passo per passo
├── 03-STRUTTURA-PROGETTO.md     ← struttura cartelle, file, naming conventions
├── 04-AGENTI-AI.md              ← prompt e configurazione di tutti gli agenti AI
├── 05-PORTALE-SPEC.md           ← specifiche funzionali del portale web
├── 06-BRAND-ASSETS.md           ← colori, font, logo, regole brand
├── 07-CONTENUTI-STRATEGY.md     ← piano editoriale, calendario, script formula
├── 08-MONETIZZAZIONE.md         ← fonti di guadagno, affiliate, sponsor, prodotti
├── 09-DEPLOY-WORKFLOW.md        ← CI/CD da VSCode a Cloudflare Pages via GitHub Actions
└── 10-CHECKLIST-LANCIO.md       ← checklist completa prima del go-live
```

---

## Visione del progetto

**Il Tutor Digitale** è un canale multi-piattaforma (YouTube, Facebook, Instagram, TikTok)  
che insegna tecnologia a italiani over 45 con poca esperienza digitale.

Il portale web centralizza:
- Link a tutti i canali social
- Catalogo video e tutorial
- Prodotti digitali (guide PDF, corsi)
- Link affiliate Amazon
- Form di contatto e newsletter
- Blog SEO per traffico organico da Google

---

## Team di agenti e responsabilità

| Agente | File di riferimento | Compito principale |
|--------|--------------------|--------------------|
| ScriptMaster | `04-AGENTI-AI.md` | Scrive script video YouTube e Reel |
| SEOMax | `04-AGENTI-AI.md` | Ottimizza titoli, descrizioni, hashtag |
| ContentCalendar | `04-AGENTI-AI.md` | Pianifica calendario editoriale mensile |
| CommunityPro | `04-AGENTI-AI.md` | Gestisce commenti e community |
| MoneyMax | `04-AGENTI-AI.md` | Monetizzazione, sponsor, affiliate |
| DevAgent | `02-SETUP-AMBIENTE.md` | Sviluppo portale, GitHub Copilot |

---

## Stack tecnologico in sintesi

```
Codice        → VSCode + GitHub Copilot Pro
Repository    → GitHub (account pro)
Hosting       → Cloudflare Pages (gratuito, CDN globale)
Dominio       → Aruba o Cloudflare Registrar
Framework     → Astro (SSG) o Next.js (SSR)
Stile         → Tailwind CSS
Deploy        → GitHub Actions → Cloudflare Pages (automatico)
Email         → Cloudflare Email Routing (gratuito)
Analytics     → Cloudflare Web Analytics (gratuito)
```

---

## Come usare questi file

1. Copia tutta la cartella `tutor-digitale-docs/` nella root del tuo repository GitHub
2. Aprila in VSCode — GitHub Copilot leggerà il contesto da questi file
3. Quando lavori con un agente, indica il file di riferimento nel prompt
4. Usa `10-CHECKLIST-LANCIO.md` per tracciare i progressi

---

*Tutti i file sono in Markdown standard, compatibili con VSCode, GitHub e qualsiasi AI agent.*
