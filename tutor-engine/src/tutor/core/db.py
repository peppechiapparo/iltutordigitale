"""SQLite persistence layer — minimal, thread-safe via short-lived connections."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .logging import get_logger

log = get_logger(__name__)

SCHEMA_FILES = ["001_init.sql"]


class Database:
    """Thin wrapper over sqlite3 with migration application."""

    def __init__(self, db_path: Path, migrations_dir: Path) -> None:
        self._db_path = db_path
        self._migrations_dir = migrations_dir

    def init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS _migrations ("
                "name TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            applied = {row[0] for row in conn.execute("SELECT name FROM _migrations")}
            for fname in SCHEMA_FILES:
                if fname in applied:
                    continue
                sql_path = self._migrations_dir / fname
                if not sql_path.is_file():
                    log.warning("migration_missing", file=str(sql_path))
                    continue
                log.info("migration_apply", file=fname)
                conn.executescript(sql_path.read_text(encoding="utf-8"))
                conn.execute("INSERT INTO _migrations(name) VALUES (?)", (fname,))
            conn.commit()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path, timeout=10.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
