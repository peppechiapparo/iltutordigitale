# Tutor Engine

Content engine agentico per **Il Tutor Digitale** — tutordigitale.com.
Gira su Raspberry Pi (ARM64/ARMv7), Docker, Python 3.12.

## Agenti attivi

| Agente | Trigger | Cosa fa |
|--------|---------|---------|
| `SEOMonitorAgent` | Giornaliero 07:00 | Audita il sito (meta, TLS, sitemap, JSON-LD, AEO signals) |
| `CalendarAgent` | Lunedì 06:30 | Propone il calendario editoriale della settimana successiva |

## Agenti pianificati (roadmap)

| Agente | Sprint | Cosa farà |
|--------|--------|-----------|
| `ContentAgent` | Sprint 1 | Genera bozze articoli blog + script YouTube da una keyword |
| `WeeklyReport` | Sprint 1 | Domenica: top query GSC + metriche + 3 opportunità keyword |
| `YouTubeMonitor` | Sprint 2 | Monitora retention/CTR per guidare le decisioni editoriali |
| `SocialPublisher` | Sprint 2+ | Pubblica su Instagram/FB via Meta Graph API (gate umano) |

## Stack

- **Python 3.12** + FastAPI + APScheduler + SQLite (WAL)
- **LLM**: GitHub Models `gpt-4.1` (free tier) → fallback OpenAI/Anthropic
- **Gate umano**: Telegram bot con bottoni inline ✅/✏️/❌
- **Deploy**: Docker `restart: unless-stopped` su Raspberry Pi

## Avvio rapido

```bash
# 1. Copia .env.example → .env e compila i valori
cp .env.example .env && nano .env

# 2. Build e avvio
docker compose up -d

# 3. Dashboard locale
http://<ip-raspberry>:8765/

# 4. Run manuale agenti
docker compose exec tutor tutor seo --notify
docker compose exec tutor tutor calendar --notify
```

## Struttura DB (SQLite)

| Tabella | Contenuto |
|---------|-----------|
| `agent_runs` | Log ogni esecuzione agente |
| `findings` | Finding SEO/AEO per run |
| `editorial_calendar` | Calendario settimanale proposto/approvato |
| `drafts` | Bozze contenuti generate dall'LLM |
| `approvals` | Log decisioni umane (gate Telegram) |
| `notifications_log` | Log notifiche Telegram inviate |

## Gate umano

Il `CalendarAgent` invia il piano settimanale su Telegram ogni lunedì alle 06:30.
Ogni voce può essere ✅ approvata, ✏️ modificata o ❌ scartata.
Solo i contenuti approvati vengono passati al `ContentAgent` per la generazione.

## Sicurezza

- Dashboard: bind su LAN (porta 8765), protetta da `TUTOR_API_TOKEN` opzionale
- Container gira come utente non-root `tutor`
- Firewall UFW: solo LAN 192.168.x.0/24 → porta 8765
- Segreti solo in `.env` (chmod 600), mai nel codice o nei log
