# 00 — Analisi Critica della Bozza

> Revisione tecnica della documentazione generata dall'LLM gratuito.
> Obiettivo: identificare i punti deboli e definire i miglioramenti che guidano la cartella `docs/`.

---

## 1. Valutazione complessiva

La bozza in `tutor-digitale-docs/` è **un buon punto di partenza**: lo stack (Astro + Tailwind +
Cloudflare Pages) è solido, low-cost e adatto a un sito content-heavy; il focus sull'accessibilità
per il pubblico over 45 è corretto e rappresenta un vero **vantaggio competitivo**.

Tuttavia presenta **lacune strutturali** che, se non corrette, limitano la scalabilità del progetto
e sprecano il know-how già disponibile in `KNOW_HOW.md` (blueprint del sistema agentico Shan).

---

## 2. Punti di forza da mantenere

- ✅ **Stack low-cost** (~4€/mese + dominio): Astro statico su Cloudflare Pages è la scelta giusta.
- ✅ **Accessibilità over 45**: testo ≥17px, contrasto AA, mobile-first. Da rafforzare, non toccare.
- ✅ **Brand definito**: palette e tipografia coerenti, tono di voce chiaro.
- ✅ **CI/CD** GitHub Actions → Cloudflare Pages con preview per PR: corretto.
- ✅ **Privacy-first analytics** (Cloudflare Web Analytics, no cookie banner necessario).

---

## 3. Criticità identificate e correzioni

### 3.1 Gli "agenti" non sono agenti (CRITICO)
**Problema**: in `04-AGENTI-AI.md` gli agenti sono semplici **prompt da copiare a mano** in claude.ai.
Non c'è automazione, né persistenza, né loop di miglioramento. Il `KNOW_HOW.md` descrive invece un
sistema agentico maturo (Template Method `Agent.run()`, ReAct loop, provider LLM intercambiabili,
scheduler, human-in-the-loop) che **non viene sfruttato**.

**Correzione**: due livelli.
- **Livello 1 (subito)** — gli agenti restano prompt operativi, ma diventano **agenti VS Code**
  (`.github/agents/*.agent.md`) versionati e riusabili, non testo volante.
- **Livello 2 (Fase 2)** — un **content engine Python** opzionale (`engine/`) che automatizza
  generazione script → SEO/AEO → bozza pubblicazione, con **gate umano** prima di ogni pubblicazione.
  Vedi `04-CONTENT-ENGINE.md`.

### 3.2 Manca il loop analitico (CRITICO)
**Problema**: la bozza produce contenuti ma non misura **cosa funziona**. Il `KNOW_HOW.md` insiste
sulla "direzione C — loop analitico" come parte di un sistema maturo.

**Correzione**: introdurre un loop dati (YouTube Analytics API + Google Search Console + Cloudflare
Web Analytics) che alimenta `ContentCalendar` con i temi/formati più performanti. Vedi `07` e `10`.

### 3.3 Solo SEO, manca AEO
**Problema**: il pubblico over 45 usa sempre più **assistenti vocali e risposte AI** (Google AI
Overviews, Alexa, Siri). La bozza ottimizza solo per la SERP classica.

**Correzione**: aggiungere **AEO (Answer Engine Optimization)** — riuso diretto del know-how
`shan-growth-agent` (che è letteralmente un agente SEO/AEO). Contenuti strutturati a domanda/risposta,
FAQ schema, formato "risposta in 40 parole". Vedi `10-SEO-AEO.md`.

### 3.4 Documenti mancanti
**Problema**: il `README.md` della bozza cita `07-CONTENUTI-STRATEGY.md` e `08-MONETIZZAZIONE.md`
che **non esistono** nella cartella.

**Correzione**: creati e completati in `docs/07` e `docs/08`.

### 3.5 Aspetti legali/fiscali italiani sottovalutati
**Problema**: monetizzazione (affiliate, sponsor, prodotti digitali, consulenze) implica obblighi
fiscali (P.IVA, regime forfettario), GDPR (newsletter = double opt-in), disclosure affiliate
obbligatoria. La bozza ne parla solo di sfuggita.

**Correzione**: documento dedicato `11-GDPR-LEGALE-FISCO.md`.

### 3.6 Incoerenze e dati segnaposto
- **Persona creator**: "Abby ... Toscana" suona incoerente per un brand italiano; va **validata**
  con l'utente (nome reale/pseudonimo, voce, foto) prima del go-live.
- **Dominio**: `iltutordigitale.it` è hardcoded in più file ma il dominio è ancora **da acquistare**.
  Va centralizzato in una sola variabile (`PUBLIC_SITE_URL`) e verificata disponibilità + marchio.
- **Worker vs Pages**: `01-ARCHITETTURA` cita Workers per form/AI in "fase 2" — coerente con il
  `KNOW_HOW` (Worker ≠ Pages), ma va chiarito che il **sito** è Pages e i **Worker** sono servizi
  separati. Vedi `02-ARCHITETTURA`.

### 3.7 Confine deterministico vs LLM non definito
**Problema**: rischio di far fare all'LLM cose che funzioni pure risolvono meglio (parsing video
metadata, generazione sitemap, validazione form).

**Correzione**: regola esplicita — **l'LLM ragiona e orchestra; i tool/funzioni eseguono**
(parsing, validazione, deploy sono deterministici). Vedi `02` e `04`.

---

## 4. Decisioni di miglioramento (sintesi)

| # | Decisione | Documento |
|---|-----------|-----------|
| D1 | Agenti come file VS Code versionati, non prompt volanti | `13-TEAM-AGENTI.md` |
| D2 | Content engine agentico Python opzionale con gate umano (Fase 2) | `04-CONTENT-ENGINE.md` |
| D3 | Loop analitico dati → decisioni editoriali | `07`, `10` |
| D4 | AEO oltre alla SEO | `10-SEO-AEO.md` |
| D5 | Completare doc contenuti + monetizzazione | `07`, `08` |
| D6 | Documento legale/fiscale/GDPR italiano | `11` |
| D7 | Centralizzare dominio/persona come variabili da validare | `01`, `02` |
| D8 | Confine deterministico/LLM esplicito | `02`, `04` |
| D9 | Team agenti ridisegnato per il dominio (no TBOX/OpenWrt) | `.github/agents/` |

---

## 5. Anti-over-engineering (vincolo)

Dal `KNOW_HOW.md`: **non introdurre l'orchestrazione (Supervisor/Registry/Queue) finché non ci sono
almeno 3 agenti automatici attivi.** La Fase 1 è interamente **manuale + portale statico**.
Il content engine (Fase 2) si introduce solo quando il volume di pubblicazione lo giustifica.
Non costruire infrastruttura prima di averne bisogno.
