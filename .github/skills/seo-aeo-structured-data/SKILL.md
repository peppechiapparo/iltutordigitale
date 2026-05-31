# SKILL: seo-aeo-structured-data

## Descrizione

Guida per generare **structured data (JSON-LD)** e ottimizzare i contenuti del portale
**Il Tutor Digitale** sia per la SEO classica sia per l'**AEO** (Answer Engine Optimization:
assistenti vocali e risposte AI).

Attivare questa skill quando si creano/modificano: pagine blog, pagine tutorial, home, schede video.

---

## Fonte di verità
```
docs/10-SEO-AEO.md   ← tecniche complete, tabella componenti, esempi
```

---

## Regole AEO chiave

1. **Risposta breve estraibile**: subito dopo l'H1, una risposta sintetica di **40-60 parole**
   in grassetto introdotta da "**In breve:**".
2. **Linguaggio conversazionale**: rispecchia come le persone *parlano* la domanda.
3. **Entità esplicite**: nomina app/modelli ("WhatsApp", "Samsung Galaxy A15").

---

## JSON-LD da iniettare (per tipo di pagina)

| Pagina | Schema |
|--------|--------|
| Blog | `Article` + `FAQPage` (se `faq[]`) |
| Tutorial passo-passo | `HowTo` (+`HowToStep`) + `FAQPage` + `VideoObject` |
| Pagina con embed YouTube | `VideoObject` |
| Home / Chi sono | `Person` / `Organization` |

### Esempio FAQPage
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    { "@type": "Question", "name": "DOMANDA",
      "acceptedAnswer": { "@type": "Answer", "text": "RISPOSTA" } }
  ]
}
```

### Esempio HowTo (estratto)
```json
{
  "@context": "https://schema.org", "@type": "HowTo", "name": "TITOLO",
  "step": [ { "@type": "HowToStep", "position": 1, "name": "Passo 1", "text": "..." } ]
}
```

---

## Checklist SEO on-page (ogni pagina)
- `<title>` ≤60 char, keyword all'inizio.
- `<meta description>` 120-160 char con keyword + benefit.
- `<link rel="canonical">`, `robots: index, follow`.
- Open Graph + Twitter Card (immagine 1200×630).
- Un solo H1 con keyword; heading gerarchici.
- ≥2 link interni; `alt` su immagini.
- Pagina inclusa in sitemap (automatica Astro).

---

## Validazione
- Verificare i JSON-LD con il Rich Results Test di Google prima del merge.
- Componenti dedicati: `SEOHead`, `ArticleSchema`, `FaqBlock`, `HowToSchema`, `VideoSchema`,
  `PersonSchema` (vedi `docs/10-SEO-AEO.md`).
