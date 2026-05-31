# 10 — SEO + AEO

> Miglioramento chiave rispetto alla bozza: oltre alla SEO classica introduciamo l'**AEO**
> (Answer Engine Optimization). Riuso del know-how del progetto `shan-growth-agent` (agente SEO/AEO).

## Perché AEO conta per questo pubblico

Gli over 45 usano sempre più **assistenti vocali** (Siri, Google Assistant, Alexa) e vedono le
**risposte AI** in cima a Google (AI Overviews). Chi viene citato dall'assistente vince la fiducia.
La SEO classica porta in SERP; l'AEO fa diventare il contenuto **la risposta**.

## SEO classico (baseline)

### On-page (ogni pagina)
- `<title>` ≤60 caratteri, keyword principale all'inizio.
- `<meta name="description">` 120-160 caratteri con keyword + benefit.
- `<link rel="canonical">`, `robots: index, follow`.
- Open Graph + Twitter Card (immagine 1200×630).
- Heading gerarchici (un solo H1, keyword in H1).
- Link interni: ogni articolo linka ≥2 contenuti correlati.
- Immagini con `alt` descrittivo; nomi file parlanti.
- Sitemap XML automatica (Astro) + RSS; invio a Google Search Console.

### Keyword strategy
Priorità a query del pubblico non tecnico: *"come fare…", "guida…", "passo per passo",
"per principianti", "semplice", "senza problemi"*. Long-tail italiane ad alta intenzione.

## AEO (Answer Engine Optimization)

### Tecniche
1. **Formato domanda → risposta**: ogni contenuto risponde a una domanda esplicita; risposta
   sintetica in **40-60 parole** subito dopo l'H1 (estraibile da assistenti e AI Overviews).
2. **FAQ structured data**: campo `faq[]` nel front-matter (vedi `03`) → componente `FaqBlock`
   che rende accordion + inietta `FAQPage` JSON-LD.
3. **`HowTo` schema** sui tutorial passo-passo (step numerati con `HowToStep`).
4. **`Article` schema** sugli articoli blog; **`Person`/`Organization`** sulla home.
5. **`VideoObject` schema** sulle pagine con embed YouTube (titolo, descrizione, thumbnail, durata).
6. **Linguaggio naturale e conversazionale**: rispecchia come le persone *parlano* la domanda.
7. **Entità chiare**: nominare esplicitamente app/modelli ("WhatsApp", "Samsung Galaxy A15") per
   farsi associare alle entità giuste.

### Esempio struttura articolo AEO-ready
```markdown
# Come fare il backup del telefono Android (guida 2026)

**In breve:** per fare il backup vai in Impostazioni → Google → Backup e attiva
"Backup su Google One". I tuoi dati si salvano automaticamente nel cloud. (≈40 parole)

## Passo per passo
1. ...
## Domande frequenti
(generate dal campo faq[] → FAQPage schema)
```

## Loop dati SEO/AEO (chiude il ciclo)

Mensile, con Google Search Console:
- Query in **posizione 5-15** con buone impressioni → ottimizza/espandi il contenuto (quick win).
- Pagine con **alto CTR** → replica il pattern di titolo.
- **AI Overviews / featured snippet** persi → ristruttura in formato risposta breve + FAQ.

## Schema dei componenti SEO da implementare

| Componente | Schema iniettato | Dove |
|------------|------------------|------|
| `SEOHead.astro` | meta + OG + Twitter + canonical | tutte le pagine |
| `ArticleSchema.astro` | `Article` | blog |
| `FaqBlock.astro` | `FAQPage` | blog/tutorial con `faq[]` |
| `HowToSchema.astro` | `HowTo` | tutorial passo-passo |
| `VideoSchema.astro` | `VideoObject` | pagine con embed YouTube |
| `PersonSchema.astro` | `Person`/`Organization` | home, chi-sono |

## Target

| Metrica | Target |
|---------|--------|
| Lighthouse SEO | 100 |
| Pagine con structured data valido | 100% |
| Core Web Vitals | Pass |
| Tempo di indicizzazione nuovo articolo | < 7 giorni (con GSC) |
