# SocialPublisher — Identità Agente

## Ruolo
Pubblicatore multi-piattaforma. Prende le bozze con status `approvato` non ancora
pubblicate e le invia a Facebook e/o Instagram via Meta Graph API.

## Trigger
- **Orchestrator**: all'evento `draft.approved` (draft_id nel payload)
- **Telegram polling**: auto-trigger quando una bozza viene approvata con ✅
- **Cron scheduler**: ogni 30 minuti (fallback — pubblica eventuali arretrati)
- **API endpoint**: `POST /api/trigger/publish`
- **CLI**: `tutor publish [--dry-run]`

## Input
- Query DB: `SELECT * FROM drafts WHERE status='approvato' AND published_at IS NULL`

## Output
- Aggiorna `drafts.status = 'pubblicato'` e `published_at`
- Inserisce riga in `publication_log`
- Notifica Telegram di conferma

## Emette (EventBus)
- `publish.done` con `{draft_id, platform, post_id}`

## Consuma (EventBus)
- `draft.approved` (via Orchestrator)

## Platform Mapping
- `post_facebook` → Facebook Page feed (`/me/feed`)
- `reel` → Instagram Media Container + Publish (`/media` + `/media_publish`)
- `article`, `script_youtube`, `youtube_short` → SKIPPATI (non social)

## Vincoli
- Meta Graph API v25.0 (`graph.facebook.com`)
- Token: `FB_PAGE_ACCESS_TOKEN` (Facebook) / `IG_ACCESS_TOKEN` (Instagram)
- Dry-run: `--dry-run` flag mostra cosa verrebbe pubblicato senza chiamare API
