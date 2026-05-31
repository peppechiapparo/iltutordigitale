-- Shan Growth Agent — initial schema
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
