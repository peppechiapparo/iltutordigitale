# 13 — Team Agenti, Skills e MCP

> Analisi della "forza lavoro" e ridisegno per il dominio **content/web** di Il Tutor Digitale.
> Il team preesistente era interamente tarato su **TBOX/SATCOM/OpenWrt** (NIS2, pumbaa, tmon, EDGE
> Next.js): **non riutilizzabile**. Qui il team nuovo.

---

## 1. Agenti

### Agenti creati per questo progetto (`.github/agents/`)

| Agente | Ruolo | Modello consigliato |
|--------|-------|---------------------|
| `content-strategist` | Calendario editoriale + ricerca temi data-driven | Sonnet / GPT-5 |
| `script-writer` | Script video YouTube/Reel/Short | Sonnet / GPT-5 |
| `seo-aeo-specialist` | SEO classico + AEO + structured data | Sonnet / GPT-5 |
| `community-manager` | Risposte community empatiche | GPT-5 / Sonnet |
| `monetization-advisor` | Affiliate, prodotti, sponsor, media kit | Sonnet / GPT-5 |
| `astro-developer` | Sviluppo portale Astro/Tailwind/TS | Sonnet / GPT-5 |
| `web-reviewer` | Code review portale | Sonnet / GPT-5 |
| `web-tester` | Build/typecheck/Lighthouse/a11y/link | Sonnet / GPT-4.1 |
| `content-engine-developer` | Backend Python content engine (Fase 2) | Sonnet / GPT-5 |

### Agenti riutilizzati (leggeri, già presenti)
| Agente | Stato |
|--------|-------|
| `git-ops` | **Riutilizzabile** così com'è (operazioni git generiche). |
| `deploy-ops` | **Non serve**: il deploy è automatico via GitHub Actions → Cloudflare Pages (vedi `09`). Da non usare per questo progetto. |

### Agenti da ritirare per questo progetto
`planner`, `developer`, `python-edge-developer`, `reviewer`, `tester` (tarati su TBOX/Next.js/EDGE) e
il `tech-lead` con istruzioni TBOX/NIS2. **Per questo workspace** vanno sostituiti dagli agenti sopra.
Va creato un `tech-lead` di progetto (vedi §4) che orchestri il nuovo team.

### Mappa: bozza → team nuovo
| Agente bozza | Sostituito da |
|--------------|---------------|
| ScriptMaster | `script-writer` |
| SEOMax | `seo-aeo-specialist` (+AEO) |
| ContentCalendar | `content-strategist` (+loop dati) |
| CommunityPro | `community-manager` |
| MoneyMax | `monetization-advisor` |
| DevAgent | `astro-developer` |
| — (nuovo) | `web-reviewer`, `web-tester`, `content-engine-developer` |

---

## 2. Skills (`.github/skills/`)

| Skill | Stato | Uso |
|-------|-------|-----|
| `tutor-digitale-design` | **Creata** | Design system del portale (brand+a11y) |
| `seo-aeo-structured-data` | **Creata** | JSON-LD e ottimizzazione AEO |
| `ui-ux-pro-max` | **Non riutilizzabile** | Punta al design system Telespazio NOVA EDGE; sostituita da `tutor-digitale-design` |
| `code-quality-metrics` | **Riutilizzabile** | Metriche qualità codice (generica) |
| `ecss-documentation-writer` | **Non pertinente** | Standard spaziali ECSS, fuori dominio |

> Skill futura opzionale: `content-writing-italiano-over45` (linee guida di tono) se si vuole
> formalizzare ulteriormente lo stile editoriale oltre a quanto già in `script-writer` + doc 07.

---

## 3. MCP (Model Context Protocol) consigliati

| MCP | Fase | A cosa serve |
|-----|------|--------------|
| **GitHub** (già disponibile via integrazione PR) | 1 | Issue/PR, tracking task |
| **Cloudflare MCP** | 1 | Gestire Pages, DNS, Email Routing, Web Analytics da agente |
| **Fetch / Web** (già disponibile) | 1 | Ricerca keyword, verifica SERP, controllo trend |
| **Google Search Console MCP** (o API) | 1-2 | Loop dati SEO: query in posizione 5-15, CTR |
| **YouTube Data API MCP** (o API) | 2 | Loop dati: retention, CTR, video top → calendario |
| **Brevo MCP** (o API) | 1-2 | Newsletter, double opt-in, lista contatti |

> Approccio: in Fase 1 bastano gli MCP/strumenti già disponibili (GitHub, Fetch). Cloudflare MCP è
> il primo da aggiungere. Gli MCP dati (GSC, YouTube) entrano quando si attiva il loop analitico.
> Dove un MCP non esiste/non è necessario, si usa la rispettiva **API** dentro il content engine (Fase 2).

---

## 4. Tech Lead di progetto (da creare)

Va creato `tech-lead` (Il Tutor Digitale) che:
- Orchestra il workflow: analisi → implementazione → review → test → (deploy automatico).
- Delega: contenuti agli agenti editoriali; portale a `astro-developer`; review a `web-reviewer`;
  test a `web-tester`; git a `git-ops`; engine a `content-engine-developer` (Fase 2).
- Applica i principi del `KNOW_HOW.md`: gate umano, quick-win-first, deterministico vs LLM, model routing.
- **Non** applica NIS2/ECSS (contesto diverso dal TBOX): per questo progetto valgono GDPR/fisco IT (`11`).
