"""Smoke tests — no network required."""

from pathlib import Path

from shan import __version__
from shan.adapters.notifier import NullNotifier, build_notifier
from shan.core.db import Database


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_null_notifier() -> None:
    assert NullNotifier().send("subj", "body") is True


def test_build_notifier_falls_back_to_null() -> None:
    n = build_notifier("", "")
    assert isinstance(n, NullNotifier)


def test_database_migration(tmp_path: Path) -> None:
    migrations = Path(__file__).resolve().parents[1] / "migrations"
    db = Database(tmp_path / "test.db", migrations)
    db.init()
    db.init()  # idempotent
    with db.connect() as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    assert {"agent_runs", "findings", "notifications_log", "_migrations"} <= tables
