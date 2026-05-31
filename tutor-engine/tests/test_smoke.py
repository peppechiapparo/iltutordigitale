"""Smoke tests — no network required."""

from pathlib import Path

from tutor import __version__
from tutor.adapters.notifier import NullNotifier, TelegramNotifier, build_notifier
from tutor.core.db import Database
from tutor.agents.seo_monitor import SEOMonitorAgent
from tutor.agents.calendar_agent import CalendarAgent, CONTENT_PILLARS, WEEKLY_SCHEDULE
from tutor.agents.content_agent import ContentAgent, FORMAT_TO_CONTENT_TYPE
from tutor.agents.weekly_report import WeeklyReportAgent


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_null_notifier() -> None:
    assert NullNotifier().send("subj", "body") is True


def test_null_notifier_approval() -> None:
    n = NullNotifier()
    assert n.send_with_approval("subj", "body", "drafts", 42) is True


def test_build_notifier_falls_back_to_null() -> None:
    n = build_notifier("", "")
    assert isinstance(n, NullNotifier)


def test_build_notifier_returns_telegram() -> None:
    n = build_notifier("token:123", "chat_456")
    assert isinstance(n, TelegramNotifier)


def test_database_migration(tmp_path: Path) -> None:
    migrations = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "test.db", migrations)
    db.init()
    db.init()  # idempotent
    with db.connect() as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    expected = {
        "agent_runs", "findings", "notifications_log",
        "editorial_calendar", "drafts", "approvals",
        "_migrations",
    }
    assert expected <= tables


def test_content_pillars() -> None:
    assert len(CONTENT_PILLARS) == 5
    assert "Smartphone" in CONTENT_PILLARS
    assert "Sicurezza online" in CONTENT_PILLARS


def test_weekly_schedule() -> None:
    assert "lunedì" in WEEKLY_SCHEDULE
    assert "venerdì" in WEEKLY_SCHEDULE
    assert WEEKLY_SCHEDULE["lunedì"]["primary"] == "YouTube lungo"


def test_format_to_content_type() -> None:
    assert FORMAT_TO_CONTENT_TYPE["YouTube lungo"] == "script_youtube"
    assert FORMAT_TO_CONTENT_TYPE["Articolo blog"] == "article"
    assert FORMAT_TO_CONTENT_TYPE["Reel IG + TikTok"] == "reel"


def test_calendar_agent_recent_topics_empty_db(tmp_path: Path) -> None:
    """CalendarAgent._get_recent_topics non crasha su DB vuoto."""
    migrations = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "test.db", migrations)
    db.init()
    agent = CalendarAgent(db=db, llm=None)  # type: ignore[arg-type]
    result = agent._get_recent_topics()
    assert isinstance(result, str)


def test_weekly_report_format_helpers() -> None:
    """I formatter del WeeklyReportAgent funzionano con dati vuoti."""
    assert "Nessuna" in WeeklyReportAgent._format_calendar([])
    assert "Nessuna" in WeeklyReportAgent._format_drafts([])
    assert "Nessuna" in WeeklyReportAgent._format_approvals([])
    assert "Nessuna" in WeeklyReportAgent._format_seo(None, [])


def test_content_agent_collect_empty_db(tmp_path: Path) -> None:
    """ContentAgent.collect() restituisce error dict se non c'è niente da elaborare."""
    migrations = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "test.db", migrations)
    db.init()
    agent = ContentAgent(db=db, llm=None, calendar_id=None)  # type: ignore[arg-type]
    result = agent.collect()
    assert "error" in result


# ── Sprint 2: YouTube Monitor + Telegram Polling ──────────────────────────────

def test_youtube_monitor_no_api_key(tmp_path):
    """YouTubeMonitorAgent restituisce warning se API key mancante."""
    _migs = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "t.db", _migs)
    db.init()

    from tutor.agents.youtube_monitor import YouTubeMonitorAgent
    agent = YouTubeMonitorAgent(db, api_key="", channel_id="")
    raw = agent.collect()
    assert "error" in raw
    status, summary, findings = agent.analyze(raw)
    assert status == "warning"
    assert len(findings) == 1
    assert findings[0].code == "config_missing"


def test_youtube_monitor_no_channel_id(tmp_path):
    """YouTubeMonitorAgent restituisce warning se channel_id mancante."""
    _migs = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "t.db", _migs)
    db.init()

    from tutor.agents.youtube_monitor import YouTubeMonitorAgent
    agent = YouTubeMonitorAgent(db, api_key="fake-key", channel_id="")
    raw = agent.collect()
    assert "error" in raw


def test_youtube_monitor_empty_videos(tmp_path):
    """YouTubeMonitorAgent gestisce lista video vuota."""
    _migs = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "t.db", _migs)
    db.init()

    from tutor.agents.youtube_monitor import YouTubeMonitorAgent
    agent = YouTubeMonitorAgent(db, api_key="fake", channel_id="UCfake")
    status, summary, findings = agent.analyze({"videos": []})
    assert status == "ok"
    assert findings == []


def test_youtube_monitor_stats_computation(tmp_path):
    """YouTubeMonitorAgent calcola correttamente top performer."""
    _migs = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "t.db", _migs)
    db.init()

    from tutor.agents.youtube_monitor import YouTubeMonitorAgent
    agent = YouTubeMonitorAgent(db, api_key="fake", channel_id="UCfake")

    videos = [
        {"id": "v1", "title": "Come usare WhatsApp", "views": 1500, "likes": 90, "comments": 20, "engagement_rate": 0.073, "published_at": "2024-01-01T00:00:00Z", "tags": []},
        {"id": "v2", "title": "Sicurezza PC Windows", "views": 200, "likes": 4, "comments": 1, "engagement_rate": 0.025, "published_at": "2024-01-05T00:00:00Z", "tags": []},
        {"id": "v3", "title": "App per foto", "views": 50, "likes": 0, "comments": 0, "engagement_rate": 0.0, "published_at": "2024-01-10T00:00:00Z", "tags": []},
    ]
    stats = agent._compute_stats(videos)
    assert stats["top_videos"][0]["id"] == "v1"
    assert len(stats["top_videos"]) == 3


def test_telegram_polling_handler_import():
    """TelegramPollingHandler importabile senza connessione di rete."""
    from tutor.adapters.telegram_polling import TelegramPollingHandler, build_polling_handler
    assert TelegramPollingHandler is not None
    assert build_polling_handler is not None


def test_telegram_polling_handler_no_token(tmp_path):
    """build_polling_handler accetta token vuoto senza eccezioni."""
    _migs = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "t.db", _migs)
    db.init()

    from tutor.adapters.telegram_polling import build_polling_handler
    handler = build_polling_handler(bot_token="", db=db)
    # start() con token vuoto: non avvia il thread, non lancia eccezioni
    handler.start()
    assert handler._thread is None


def test_telegram_decision_to_status_mapping():
    """Mappa decision→status corretta."""
    from tutor.adapters.telegram_polling import DECISION_TO_STATUS
    assert DECISION_TO_STATUS["approve"] == "approvato"
    assert DECISION_TO_STATUS["edit"] == "modificato"
    assert DECISION_TO_STATUS["discard"] == "scartato"
