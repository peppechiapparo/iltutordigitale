# Il Tutor Digitale — Documentazione di Progetto (rev. Tech Lead)

> Documentazione **rivista e potenziata** a partire dalla bozza in `tutor-digitale-docs/`
> (generata da un LLM gratuito a partire dal business plan).
> Questa cartella `docs/` è la **fonte di verità** per l'implementazione.
>
> Stack confermato: **Astro + Tailwind + TypeScript → Cloudflare Pages** (portale)
> + **content engine agentico Python** (automazione contenuti, opzionale Fase 2).
> Aggiornato: 31 maggio 2026 — Revision 1.0

---

## Cosa è cambiato rispetto alla bozza `tutor-digitale-docs/`

| Tema | Bozza originale | Revisione (questa cartella) |
|------|-----------------|------------------------------|
| **Agenti AI** | Prompt da copia-incollare manualmente in claude.ai | Due livelli: (a) prompt operativi + (b) **content engine agentico reale** riusando il blueprint `KNOW_HOW.md` (Template Method + ReAct + human-in-the-loop) |
| **Loop analitico** | Assente | Aggiunto **loop dati** (YouTube Analytics + Search Console + Cloudflare Analytics) che alimenta le decisioni editoriali |
| **SEO** | Solo SEO classico | Aggiunto **AEO** (Answer Engine Optimization) — riuso del know-how `shan-growth-agent` |
| **Doc mancanti** | 07-CONTENUTI e 08-MONETIZZAZIONE citati ma assenti | Creati e completati |
| **GDPR/Legale/Fisco** | Cenni sparsi | Documento dedicato (P.IVA, regime forfettario, double opt-in, disclosure affiliate) |
| **Persona creator** | "Abby, Toscana" (incoerente) | Persona da validare con l'utente prima del go-live |
| **Architettura** | Solo portale statico | Portale + (opzionale) engine; confini chiari tra deterministico e LLM |
| **Team agenti** | 6 prompt generici | Team ridisegnato e specializzato per il dominio content/web (vedi `.github/agents/`) |

---

## Indice documenti

| File | Contenuto |
|------|-----------|
| [00-ANALISI-CRITICA.md](00-ANALISI-CRITICA.md) | Analisi critica della bozza + decisioni di miglioramento |
| [01-VISIONE-STRATEGIA.md](01-VISIONE-STRATEGIA.md) | Visione, persona, posizionamento, differenziazione, KPI |
| [02-ARCHITETTURA.md](02-ARCHITETTURA.md) | Architettura tecnica (portale + content engine), confini, costi |
| [03-STRUTTURA-PROGETTO.md](03-STRUTTURA-PROGETTO.md) | Struttura cartelle, naming, config |
| [04-CONTENT-ENGINE.md](04-CONTENT-ENGINE.md) | Sistema agentico di automazione contenuti (Fase 2) |
| [05-PORTALE-SPEC.md](05-PORTALE-SPEC.md) | Specifiche funzionali del portale |
| [06-BRAND.md](06-BRAND.md) | Brand, palette, tipografia, asset, accessibilità |
| [07-CONTENUTI-STRATEGY.md](07-CONTENUTI-STRATEGY.md) | Piano editoriale, formula contenuti, calendario |
| [08-MONETIZZAZIONE.md](08-MONETIZZAZIONE.md) | Fonti di guadagno, pricing, fasi |
| [09-DEPLOY.md](09-DEPLOY.md) | CI/CD VSCode → GitHub → Cloudflare Pages |
| [10-SEO-AEO.md](10-SEO-AEO.md) | SEO classico + Answer Engine Optimization |
| [11-GDPR-LEGALE-FISCO.md](11-GDPR-LEGALE-FISCO.md) | Privacy, cookie, fisco, disclosure |
| [12-ROADMAP.md](12-ROADMAP.md) | Roadmap completa per fasi (da approvare) |
| [13-TEAM-AGENTI.md](13-TEAM-AGENTI.md) | Team agenti, skills e MCP del progetto |

---

## Principio guida (dal KNOW_HOW)

> Partire **sempre** da quick win read-only (basso rischio), costruire i mattoni condivisi,
> e abilitare le azioni che modificano il mondo (pubblicare, inviare email) **solo con gate umano**.
> Separare il **deterministico** (parsing, validazione, deploy) dall'**LLM** (ragiona e orchestra).
