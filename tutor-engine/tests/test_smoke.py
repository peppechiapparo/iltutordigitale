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
