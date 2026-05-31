-- Tutor Engine — migration 002: publication log
-- Traccia ogni pubblicazione effettuata sui canali social.

CREATE TABLE IF NOT EXISTS publication_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id        INTEGER REFERENCES drafts(id) ON DELETE SET NULL,
    platform        TEXT NOT NULL,  -- "facebook", "instagram", "youtube_short", ecc.
    content_type    TEXT NOT NULL,  -- "post_facebook", "reel", ecc.
    platform_post_id TEXT,          -- ID post restituito dall'API della piattaforma
    post_url        TEXT,           -- URL diretto al post pubblicato
    status          TEXT NOT NULL CHECK (status IN ('ok', 'error', 'skipped')),
    error_message   TEXT,
    published_at    TEXT NOT NULL   -- ISO timestamp
);

CREATE INDEX IF NOT EXISTS idx_publog_draft ON publication_log(draft_id);
CREATE INDEX IF NOT EXISTS idx_publog_platform ON publication_log(platform, published_at DESC);
