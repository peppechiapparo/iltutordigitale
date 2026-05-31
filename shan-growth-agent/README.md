# Shan Growth Agent

> Sistema agentico leggero per il monitoraggio SEO, la produzione assistita di contenuti, l'ottimizzazione AEO e l'integrazione social della **Scuola di Kung Fu Maestro Cipriani**.

Edge runtime su Raspberry Pi 4 (`192.168.1.30`). Orchestra agenti che osservano [scuolakungfucipriani.it](https://www.scuolakungfucipriani.it), generano report e suggerimenti, e — quando autorizzati — bozze di contenuti per sito e Instagram.

---

## Principi

- **Human-in-the-loop**: nessun agente pubblica o modifica nulla in produzione senza approvazione esplicita.
- **Edge-light**: il Pi orchestra; l'inferenza LLM è delegata a Claude/OpenAI API.
- **Niente bot di scraping/spam Instagram**: solo Graph API ufficiale, account Business/Creator.
- **NIS2-aware**: dashboard solo in LAN, secret in `.env` (mode 600), firewall UFW, container non-root.

## Architettura

```
┌────────────────── Raspberry Pi (192.168.1.30) ──────────────────┐
│  docker compose                                                  │
│  ┌───────────────────── shan container ────────────────────────┐ │
│  │  FastAPI (8765)  ──┐                                        │ │
│  │                    ├── Scheduler (APScheduler)              │ │
│  │  SQLite ◄──────────┤                                        │ │
│  │                    └── Agents:                              │ │
│  │                         • seo_monitor   (MVP)               │ │
│  │                         • content_growth  [w3]              │ │
│  │                         • structured_data [w3]              │ │
│  │                         • instagram_bridge [w4]             │ │
│  │                         • indexing                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────────────────────────┘
               │ Adapters
   ┌───────────┼───────────┬──────────────┬─────────────┐
   ▼           ▼           ▼              ▼             ▼
Telegram   Claude API   OpenAI API   Search Console   IndexNow
                                     PageSpeed API    Instagram
                                                      Graph API
```

## Stack

| Layer | Tech |
|-------|------|
| Lang | Python 3.12 |
| HTTP | httpx, BeautifulSoup4/lxml |
| Web | FastAPI + Uvicorn |
| Sched | APScheduler (cron triggers) |
| DB | SQLite (WAL) |
| Logs | structlog |
| LLM | anthropic, openai (Strategy pattern) |
| Container | Docker + Compose v2 (ARM64) |

## Design patterns

- **Strategy** — `Notifier` / `LLMClient` con implementazioni intercambiabili
- **Adapter** — ogni API esterna ha un wrapper dedicato
- **Factory** — `build_notifier`, `build_llm_client`, `build_scheduler`
- **Template Method** — `Agent.run()` → `collect() → analyze() → persist()`
- **DI** — tutte le dipendenze passate per costruttore (no globali, no singleton applicativi)

## Quickstart (dev locale)

```bash
cd shan-growth-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # poi modifica
shan seo               # singola run del SEO monitor → stdout JSON
shan serve             # FastAPI su http://localhost:8765
```

## Deploy sul Raspberry

```bash
# Dal tuo PC: package + scp
cd /opt/TPZ/src/scuola_cipriani/shan-growth-agent
tar czf /tmp/shan.tar.gz --exclude=.venv --exclude=data --exclude=__pycache__ .
scp /tmp/shan.tar.gz giuseppe@192.168.1.30:/tmp/

# Sul Pi
ssh giuseppe@192.168.1.30
sudo mkdir -p /opt/shan-growth-agent
sudo tar xzf /tmp/shan.tar.gz -C /opt/shan-growth-agent
sudo /opt/shan-growth-agent/deploy/install-pi.sh
# poi modifica /opt/shan-growth-agent/.env e:
cd /opt/shan-growth-agent && sudo docker compose up -d
```

Dashboard: `http://192.168.1.30:8765/`

## CLI

| Comando | Descrizione |
|---------|-------------|
| `shan seo` | Esegue una run del SEO monitor e stampa JSON |
| `shan seo --notify` | Come sopra + invia notifica Telegram |
| `shan serve` | Avvia FastAPI + scheduler (entrypoint container) |
| `shan version` | Stampa versione |

## API

| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/` | Dashboard HTML |
| GET | `/healthz` | Liveness probe |
| GET | `/api/runs?limit=50` | Lista run recenti |
| GET | `/api/runs/{id}` | Dettaglio run + findings |
| POST | `/api/agents/seo_monitor/run` | Trigger manuale |

Auth opzionale: imposta `SHAN_API_TOKEN` in `.env`, poi `Authorization: Bearer <token>`.

## Roadmap

| Settimana | Stato | Deliverable |
|-----------|-------|-------------|
| 1 | ✅ MVP | Scaffolding + `seo_monitor` + Telegram + dashboard |
| 2 | ⏳ | PageSpeed/Lighthouse, 404 crawler, audit alt-text |
| 3 | ⏳ | `content_growth` + `structured_data` (JSON-LD generator) |
| 4 | ⏳ | `instagram_bridge` (read + draft caption, no auto-publish) |

## Sicurezza

- Container come utente non-root
- Secret solo in `.env` (chmod 600) e `./secrets/` (chmod 700)
- Dashboard bindata su 0.0.0.0 ma esposta solo in LAN via UFW (192.168.1.0/24)
- Healthcheck Docker integrato
- Nessuna porta esposta su internet, nessun reverse proxy in fase MVP
- Token API opzionale per dashboard

## Licenza

Proprietary — uso interno Scuola Cipriani.
