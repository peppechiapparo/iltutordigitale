# 05 — Specifiche Funzionali del Portale

## Pagine del portale

### Homepage (`/`)
**Obiettivo**: convertire visitatori in follower e clienti

Sezioni in ordine:
1. **Hero** — headline forte, foto creator, CTA principale ("Guarda i tutorial →")
2. **Problema/Soluzione** — "Hai paura della tecnologia? Sei nel posto giusto."
3. **Video in evidenza** — griglia 3 video YouTube più visti (embed o thumbnail+link)
4. **Chi sono** — breve bio con foto, storia, approccio didattico
5. **Prodotti consigliati** — 3-4 prodotti Amazon affiliate con breve descrizione
6. **Social links** — bottoni grandi verso YouTube, Facebook, Instagram, TikTok
7. **Newsletter** — form iscrizione con lead magnet ("Scarica gratis: Guida Smartphone per Principianti")
8. **Ultimi articoli blog** — 3 articoli recenti

---

### Tutorial (`/tutorial`)
**Obiettivo**: SEO Google + hub risorse per il pubblico

Struttura:
- Filtri per categoria: Smartphone / PC / WhatsApp / Sicurezza / App
- Griglia di card con thumbnail YouTube, titolo, durata, categoria
- Ogni card linka alla pagina video (`/tutorial/nome-video`) o direttamente YouTube

Pagina video singolo (`/tutorial/[slug]`):
- Embed video YouTube
- Trascrizione / sommario scritto (ottimo per SEO)
- Passi del tutorial numerati
- Prodotti affiliate correlati
- Link agli altri video della stessa categoria
- Form commento / domanda

---

### Blog (`/blog`)
**Obiettivo**: traffico organico Google — articoli ottimizzati SEO

Ogni articolo deve avere:
- Titolo H1 con keyword principale
- Meta description (max 160 caratteri)
- Immagine hero con alt text
- Testo minimo 800 parole (meglio 1200-1500)
- Video YouTube correlato embed
- Link interno ad almeno 2 altri articoli
- Call to action finale (newsletter o prodotto)
- Structured data (Article schema)

Esempi argomenti blog:
- "Come fare il backup del telefono Android: guida 2026"
- "Le 5 truffe WhatsApp più comuni e come riconoscerle"
- "Smartphone per anziani: quale scegliere nel 2026"
- "Come liberare spazio sul telefono senza perdere le foto"

---

### Prodotti (`/prodotti`)
**Obiettivo**: monetizzazione affiliate + vendita prodotti digitali propri

Sezioni:
1. **Prodotti digitali** (guide PDF, corsi) — con Gumroad/Payhip embed
2. **Smartphone consigliati** — link Amazon affiliate
3. **Accessori utili** — cuffie, caricatori, cover — link Amazon affiliate
4. **App gratuite consigliate** — lista con descrizione

Ogni prodotto ha:
- Immagine
- Nome e breve descrizione
- Prezzo
- Bottone CTA ("Vedi su Amazon" / "Scarica la guida")
- Nota "come scelgo i prodotti" (trasparenza affiliate)

---

### Chi sono (`/chi-sono`)
**Obiettivo**: costruire fiducia e connessione personale

Contenuto:
- Foto grande creator
- Storia personale: come e perché ho iniziato
- Mission: "Voglio che nessuno si senta escluso dalla tecnologia"
- Cosa trovi sul canale
- Media kit (link a PDF scaricabile per brand interessati)
- Contatti

---

### Contatti (`/contatti`)
**Obiettivo**: gestire richieste sponsor, collaborazioni, domande

Form con campi:
- Nome (required)
- Email (required)
- Tipo richiesta: [dropdown] Domanda tecnica / Collaborazione brand / Corso privato / Altro
- Messaggio (required)
- Consenso privacy (required)

Backend form:
- Cloudflare Worker riceve il form → invia email a `info@iltutordigitale.it`
- Oppure servizio esterno: Formspree (gratuito fino 50 invii/mese) o Web3Forms

---

## Componenti UI — specifiche

### Header
```
Logo + nome canale | navigazione | bottone CTA "Iscriviti al canale"
Mobile: hamburger menu
Colore: bianco con border-bottom brand-blue leggero
Sticky (rimane in cima durante lo scroll)
```

### Footer
```
Col 1: Logo + tagline + social icons
Col 2: Link utili (Tutorial, Blog, Prodotti, Chi sono)
Col 3: Newsletter signup mini
Bottom bar: copyright | privacy policy | cookie policy | P.IVA (quando disponibile)
Colore: brand-dark (#2C2C2A) con testo chiaro
```

### VideoCard
```
- Thumbnail YouTube (caricamento lazy)
- Badge categoria (colore per categoria)
- Titolo (max 2 righe, poi ellipsis)
- Durata video
- Data pubblicazione
- Link alla pagina video
- Hover: leggero lift + overlay play button
```

### Newsletter form
```
- Lead magnet chiaro: "Scarica gratis la Guida Smartphone"
- Campo email + bottone "Scarica gratis"
- Sotto: "Niente spam. Solo tutorial utili ogni settimana."
- Provider: Brevo (ex Sendinblue) — piano gratuito 300 email/giorno
```

---

## SEO tecnico

### Meta tag base (ogni pagina)
```html
<title>Titolo pagina — Il Tutor Digitale</title>
<meta name="description" content="Descrizione 120-160 caratteri con keyword">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://iltutordigitale.it/pagina">

<!-- Open Graph (Facebook, WhatsApp) -->
<meta property="og:title" content="Titolo">
<meta property="og:description" content="Descrizione">
<meta property="og:image" content="https://iltutordigitale.it/og-image.jpg">
<meta property="og:url" content="https://iltutordigitale.it/pagina">
<meta property="og:type" content="website">

<!-- Twitter/X Card -->
<meta name="twitter:card" content="summary_large_image">
```

### Structured data (homepage)
```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Abby — Il Tutor Digitale",
  "url": "https://iltutordigitale.it",
  "sameAs": [
    "https://youtube.com/@iltutordigitale",
    "https://facebook.com/iltutordigitale",
    "https://instagram.com/iltutordigitale"
  ],
  "jobTitle": "Content Creator — Tecnologia per Principianti"
}
```

---

## Performance targets

| Metrica | Target | Tool di verifica |
|---------|--------|-----------------|
| Lighthouse Performance | > 90 | Chrome DevTools |
| Lighthouse SEO | 100 | Chrome DevTools |
| Lighthouse Accessibility | > 95 | Chrome DevTools |
| First Contentful Paint | < 1.5s | PageSpeed Insights |
| Time to Interactive | < 3s | PageSpeed Insights |
| Core Web Vitals | Pass | Google Search Console |

---

## Privacy e GDPR

Obbligatorio per sito italiano:
- **Cookie banner** — usa Cookieyes (piano gratuito) o Iubenda
- **Privacy Policy** — genera con Iubenda (piano gratuito base)
- **Cookie Policy** — inclusa in Privacy Policy
- **Form consenso** — checkbox esplicita + link privacy policy
- **Analytics** — Cloudflare Web Analytics è privacy-first (no cookies, GDPR compliant)
- **Google Analytics** — se lo usi, richiede cookie banner e consenso esplicito

Nota: Cloudflare Web Analytics è sufficiente per iniziare e non richiede cookie banner.
