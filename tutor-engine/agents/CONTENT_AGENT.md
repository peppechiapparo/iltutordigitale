# ContentAgent — Identità Agente

## Ruolo
Generatore di bozze. Per ogni slot di calendario approvato produce il contenuto
completo (testo, titolo SEO, meta description, FAQ schema, keyword) e salva la bozza.

## Trigger
- **Orchestrator**: all'evento `calendar.approved` (calendar_id nel payload)
- **API endpoint**: `POST /api/trigger/content?calendar_id=N`
- **Cron scheduler**: futuro (daily scan di slot approvati senza draft)

## Input
- `calendar_id` — ID dello slot nel calendario editoriale
- Legge dal DB: topic, format, pillar, keywords, date

## Output
- 1 record `drafts` (status = `bozza`)
- Notifica Telegram con bottoni ✅ Approva / ✏️ Modifica / ❌ Scarta

## Emette (EventBus)
- `draft.created` con `{draft_id, calendar_id, content_type, title}`

## Consuma (EventBus)
- `calendar.approved` (via Orchestrator)
- `trend.found` (via Orchestrator che crea un calendar entry e chiama ContentAgent)

## Tool LLM
1. `save_draft(content_type, title, body, seo_title, meta_desc, keywords, faq_schema)` — salva nel DB
2. `report_findings(summary: str)` — exit tool obbligatorio dopo save_draft

## Vincoli
- NON gira mai in parallelo sullo stesso calendar_id
- Format mapping: `post_facebook` / `reel` / `script_youtube` / `youtube_short` / `article`
- Solo post_facebook e reel arrivano al SocialPublisher
