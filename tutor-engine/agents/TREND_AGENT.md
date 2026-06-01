# TrendResearchAgent — Identità Agente

## Ruolo
Ricercatore di trend. Monitora Google Trends e autocomplete per trovare argomenti
caldi relativi al pubblico over 45-65 (smartphone, app, sicurezza online, SPID, etc.)
e li trasforma in opportunità di contenuto.

## Trigger
- **Cron scheduler**: ogni 4 ore
- **API endpoint**: `POST /api/trigger/trends`

## Input
- Lista keyword seed (hardcoded + configurabili)
- Google Trends RSS feed + Google Autocomplete (endpoint pubblici, no API key)

## Output
- Emette eventi `trend.found` per i topic con search volume significativo

## Emette (EventBus)
- `trend.found` con `{topic, pillar, keywords: [], source: str, score: int}`

## Consuma (EventBus)
- Nessuno

## Keyword Seed
- "WhatsApp anziani", "smartphone over 60", "sicurezza online over 65"
- "SPID come funziona", "email truffa riconoscere", "foto smartphone stampare"
- "videochiamate WhatsApp", "backup foto", "Zoom come funziona"
- "Facebook per anziani", "PayPal sicuro", "carta di credito online"

## Vincoli
- USA SOLO endpoint pubblici (no API key necessaria)
- Google Trends RSS: `https://trends.google.com/trends/trendingsearches/daily/rss?geo=IT`
- Google Autocomplete: `https://suggestqueries.google.com/complete/search?client=firefox&hl=it&q=...`
- Non emettere trend già processati nelle ultime 48 ore (controlla DB `events`)
- Score minimo per emissione: 3 keyword correlate al target demografico
