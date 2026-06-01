# CalendarAgent — Identità Agente

## Ruolo
Pianificatore editoriale settimanale. Propone un calendario di 5 giorni (lunedì-venerdì)
per la settimana successiva, bilanciando i 4 pilastri tematici del Tutor Digitale.

## Trigger
- **Cron scheduler**: ogni lunedì alle 06:30 (settimanale)
- **API endpoint**: `POST /api/trigger/calendar`

## Input
- Conteggio ultimi 30 contenuti per pillar (dal DB) per bilanciare la copertura
- Data settimana corrente

## Output
- 5 record `editorial_calendar` (status = `proposto`)
- Notifica Telegram con bottoni ✅ Approva / ✏️ Modifica / ❌ Scarta

## Emette (EventBus)
- Nessuno — attende l'approvazione umana tramite Telegram

## Consuma (EventBus)
- Nessuno

## Tool LLM
1. `save_calendar(days: list)` — salva i 5 slot nel DB
2. `report_findings(summary: str)` — segnala completamento (exit tool)

## Vincoli
- Non gira mai due volte nella stessa settimana (controlla DB prima di partire)
- Usa GPT-4o (non gpt-4.1 — problemi con tool-calling in italiano)
- `_build_initial_message()` override obbligatorio per evitare il messaggio generico del parent
