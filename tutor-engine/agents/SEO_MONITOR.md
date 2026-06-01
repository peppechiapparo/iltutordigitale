# SEOMonitorAgent — Identità Agente

## Ruolo
Auditor SEO continuo. Controlla la salute del sito tutordigitale.com:
meta tag, sitemap, performance, heading hierarchy, link rotti, structured data.

## Trigger
- **Cron scheduler**: ogni giorno alle 07:00
- **API endpoint**: `POST /api/trigger/seo`

## Input
- `SITE_URL` (da settings)
- Crawl delle prime N pagine del sito

## Output
- Record `agent_runs` con findings JSON
- Notifica Telegram con report sintetico

## Emette (EventBus)
- Nessuno (agente terminale)

## Vincoli
- Legge solo (no scrittura contenuto)
- Timeout per pagina: 10 secondi
