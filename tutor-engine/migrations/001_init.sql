-- Tutor Engine — initial schema
-- All timestamps are stored as ISO-8601 strings (Europe/Rome local time).

CREATE TABLE IF NOT EXISTS agent_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent       TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    status      TEXT NOT NULL CHECK (status IN ('ok', 'warning', 'error', 'running')),
    summary     TEXT,
    details     TEXT  -- JSON blob
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_started
    ON agent_runs(agent, started_at DESC);

CREATE TABLE IF NOT EXISTS findings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    severity    TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    code        TEXT NOT NULL,
    message     TEXT NOT NULL,
    url         TEXT,
    payload     TEXT  -- JSON blob
);

CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(run_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);

CREATE TABLE IF NOT EXISTS notifications_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    channel     TEXT NOT NULL,
    sent_at     TEXT NOT NULL,
    subject     TEXT,
    body        TEXT NOT NULL,
    ok          INTEGER NOT NULL DEFAULT 1
);

-- Calendario editoriale proposto dagli agenti
CREATE TABLE IF NOT EXISTS editorial_calendar (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start   TEXT NOT NULL,  -- es. "2026-06-02" (lunedì)
    day          TEXT NOT NULL,  -- "lunedì", "martedì", ...
    date         TEXT NOT NULL,  -- ISO date "2026-06-02"
    pillar       TEXT NOT NULL,  -- "Smartphone", "WhatsApp", ecc.
    format       TEXT NOT NULL,  -- "YouTube lungo", "Reel", "Articolo blog", ...
    topic        TEXT NOT NULL,  -- titolo/argomento proposto
    keywords     TEXT,           -- JSON array di keyword
    status       TEXT NOT NULL DEFAULT 'proposto'
                 CHECK (status IN ('proposto', 'approvato', 'modificato', 'scartato', 'prodotto', 'pubblicato')),
    approved_at  TEXT,
    notes        TEXT,
    created_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_calendar_week ON editorial_calendar(week_start);
CREATE INDEX IF NOT EXISTS idx_calendar_status ON editorial_calendar(status);

-- Bozze di contenuto generate dall'LLM (articoli blog, script YouTube, ecc.)
CREATE TABLE IF NOT EXISTS drafts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    calendar_id  INTEGER REFERENCES editorial_calendar(id),
    agent        TEXT NOT NULL,          -- "content_agent", "script_agent", ecc.
    content_type TEXT NOT NULL,          -- "article", "script", "reel", "short"
    title        TEXT NOT NULL,
    body         TEXT NOT NULL,          -- testo generato
    seo_title    TEXT,
    meta_desc    TEXT,
    keywords     TEXT,                   -- JSON array
    faq_schema   TEXT,                   -- JSON blob strutturato
    status       TEXT NOT NULL DEFAULT 'bozza'
                 CHECK (status IN ('bozza', 'approvato', 'modificato', 'scartato', 'pubblicato')),
    created_at   TEXT NOT NULL,
    approved_at  TEXT,
    published_at TEXT,
    notes        TEXT
);

CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
CREATE INDEX IF NOT EXISTS idx_drafts_type ON drafts(content_type);

-- Log di approvazione umana (gate umano Telegram)
CREATE TABLE IF NOT EXISTS approvals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ref_table    TEXT NOT NULL,   -- "editorial_calendar" o "drafts"
    ref_id       INTEGER NOT NULL,
    telegram_msg_id INTEGER,
    decision     TEXT NOT NULL CHECK (decision IN ('approvato', 'modificato', 'scartato')),
    decided_by   TEXT,            -- telegram user_id
    decided_at   TEXT NOT NULL,
    notes        TEXT             -- commento eventuale
);

CREATE INDEX IF NOT EXISTS idx_approvals_ref ON approvals(ref_table, ref_id);
