# 01 — Architettura Tecnica

## Decisione stack

### Perché Astro (raccomandato)
- Genera HTML statico → velocissimo su Cloudflare Pages
- Supporta componenti React/Vue dove serve interattività
- SEO eccellente out of the box
- Ottimo per siti content-heavy (blog, tutorial, portale)
- Integra Markdown nativo per i contenuti

### Alternativa: Next.js
- Sceglilo solo se hai bisogno di SSR (es. dashboard utente con login)
- Più pesante da configurare su Cloudflare
- Usa `@cloudflare/next-on-pages` adapter

**Raccomandazione: usa Astro per il portale Il Tutor Digitale.**

---

## Architettura completa

```
┌─────────────────────────────────────────────────────┐
│                   UTENTE FINALE                      │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────┐
│              CLOUDFLARE (Edge Network)               │
│  - CDN globale                                       │
│  - DDoS protection                                   │
│  - SSL/TLS automatico                                │
│  - Web Analytics                                     │
│  - Email Routing                                     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              CLOUDFLARE PAGES                        │
│  - Hosting gratuito illimitato                       │
│  - Deploy automatico da GitHub                       │
│  - Preview deploy per ogni PR                        │
│  - Environment variables                             │
└──────────────────────┬──────────────────────────────┘
                       │ trigger
┌──────────────────────▼──────────────────────────────┐
│                 GITHUB REPOSITORY                    │
│  - Source code (branch: main = production)          │
│  - GitHub Actions (CI/CD)                            │
│  - GitHub Copilot Pro (AI coding assistant)          │
│  - Issues per task tracking                          │
└──────────────────────┬──────────────────────────────┘
                       │ sviluppo locale
┌──────────────────────▼──────────────────────────────┐
│                  VSCODE (locale)                     │
│  - Astro extension                                   │
│  - Tailwind IntelliSense                             │
│  - GitHub Copilot (chat + autocomplete)              │
│  - GitLens                                           │
└─────────────────────────────────────────────────────┘
```

---

## Servizi e costi

| Servizio | Piano | Costo |
|----------|-------|-------|
| Dominio (Aruba) | .it o .com | ~10–15€/anno |
| Cloudflare Pages | Free | 0€ |
| Cloudflare CDN + SSL | Free | 0€ |
| Cloudflare Email Routing | Free | 0€ |
| Cloudflare Web Analytics | Free | 0€ |
| GitHub Pro | Pro | ~4€/mese |
| GitHub Copilot Pro | Incluso in GitHub Pro | 0€ aggiuntivi |
| **Totale mensile** | | **~4€/mese + dominio** |

---

## Flusso dati e integrazioni

```
YouTube API  ──────────────────────┐
Facebook Graph API  ───────────────┤──► Portale Astro ──► Cloudflare Pages
Gumroad / Stripe (prodotti) ───────┤
Mailchimp / Brevo (newsletter) ────┘

Anthropic API ──► AI Agents (lato server Cloudflare Workers, opzionale)
Amazon Affiliate links ──► HTML statico (no API necessaria)
```

---

## Cloudflare Workers (opzionale, fase 2)

Per funzionalità dinamiche senza server:
- Form di contatto → Worker invia email
- Generatore script AI nel portale → Worker chiama Anthropic API
- Newsletter signup → Worker salva in D1 (database edge)

Tutto gratuito nel piano Cloudflare Free fino a 100.000 richieste/giorno.

---

## DNS e dominio

### Se acquisti da Aruba:
1. Acquista dominio su aruba.it
2. Vai su Cloudflare → Add Site → inserisci il dominio
3. Cloudflare ti dà 2 nameserver (es. `ada.ns.cloudflare.com`)
4. Torna su Aruba → pannello DNS → sostituisci i nameserver con quelli Cloudflare
5. Attendi 24–48h propagazione
6. Da Cloudflare Pages → Custom Domain → collega il tuo dominio

### Se acquisti da Cloudflare Registrar:
- Tutto è già nello stesso pannello, nessuna configurazione DNS manuale
- **Raccomandato** per semplicità

---

## Variabili d'ambiente necessarie

```env
# .env.local (NON committare su GitHub)
ANTHROPIC_API_KEY=sk-ant-...
AMAZON_AFFILIATE_TAG=iltutordigit-21
BREVO_API_KEY=...
YOUTUBE_API_KEY=...

# Su Cloudflare Pages → Settings → Environment Variables
# (stesse variabili, inserite dal pannello Cloudflare)
```

---

## Sicurezza

- Nessuna chiave API nel codice sorgente (usa `.env` + Cloudflare env vars)
- `.gitignore` deve includere `.env`, `.env.local`, `node_modules/`
- Cloudflare gestisce SSL automaticamente (certificato gratuito Let's Encrypt)
- Rate limiting gratuito su Cloudflare per proteggere i form
