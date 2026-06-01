"""EventBus leggero basato su SQLite WAL.

Pattern: emit → eventi persistono su DB → consume/subscribe via polling.
Nessuna dipendenza esterna (no Redis, no RabbitMQ).
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from typing import TYPE_CHECKING, Callable

from .logging import get_logger

if TYPE_CHECKING:
    from .db import Database

log = get_logger(__name__)

# Tipi di evento usati nel sistema
DRAFT_APPROVED   = "draft.approved"
DRAFT_CREATED    = "draft.created"
CALENDAR_APPROVED = "calendar.approved"
TREND_FOUND      = "trend.found"
PUBLISH_DONE     = "publish.done"


class EventBus:
    """Bus eventi persistente su SQLite."""

    def __init__(self, db: "Database") -> None:
        self._db = db
        self._subscribers: dict[str, list[Callable[[dict], None]]] = {}
        self._lock = threading.Lock()

    def emit(self, event_type: str, payload: dict | None = None) -> int:
        """Persiste un evento nel DB e lo consegna in-process ai subscriber."""
        payload = payload or {}
        now = datetime.now().isoformat(timespec="seconds")
        with self._db.connect() as conn:
            conn.execute(
                "INSERT INTO events (event_type, payload, status, created_at)"
                " VALUES (?, ?, 'pending', ?)",
                (event_type, json.dumps(payload, ensure_ascii=False), now),
            )
            event_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        log.info("event_emitted", event_type=event_type, event_id=event_id, payload=payload)

        # Consegna in-process ai subscriber registrati (fire-and-forget)
        handlers = self._get_handlers(event_type)
        for handler in handlers:
            try:
                handler({"id": event_id, "event_type": event_type, **payload})
            except Exception as exc:  # noqa: BLE001
                log.error("event_handler_failed", event_type=event_type, error=str(exc))

        return event_id

    def subscribe(self, event_type: str, handler: Callable[[dict], None]) -> None:
        """Registra un handler per il tipo di evento specificato."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
        log.debug("event_subscribed", event_type=event_type)

    def mark_done(self, event_id: int) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._db.connect() as conn:
            conn.execute(
                "UPDATE events SET status='done', processed_at=? WHERE id=?",
                (now, event_id),
            )

    def mark_failed(self, event_id: int) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._db.connect() as conn:
            conn.execute(
                "UPDATE events SET status='failed', processed_at=? WHERE id=?",
                (now, event_id),
            )

    def _get_handlers(self, event_type: str) -> list[Callable[[dict], None]]:
        with self._lock:
            return list(self._subscribers.get(event_type, []))
