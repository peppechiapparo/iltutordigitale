"""Orchestratore event-driven: ascolta EventBus e trigera gli agenti.

Nessuna dipendenza pesante (no CrewAI, no LangGraph).
Pattern: subscribe → handler in background thread.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from .events import (
    CALENDAR_APPROVED,
    DRAFT_APPROVED,
    TREND_FOUND,
    EventBus,
)
from .logging import get_logger

if TYPE_CHECKING:
    from ..adapters.llm import BaseLLMClient
    from ..adapters.meta_publisher import MetaPublisher
    from ..adapters.notifier import Notifier
    from ..core.config import Settings
    from .db import Database

log = get_logger(__name__)


class Orchestrator:
    """Collegamento tra EventBus e agenti.

    Registra handler su EventBus; ogni handler gira in un thread separato
    in modo da non bloccare il polling del bus.
    """

    def __init__(
        self,
        bus: EventBus,
        db: "Database",
        llm: "BaseLLMClient",
        notifier: "Notifier",
        publisher: "MetaPublisher",
        settings: "Settings",
    ) -> None:
        self._bus = bus
        self._db = db
        self._llm = llm
        self._notifier = notifier
        self._publisher = publisher
        self._settings = settings

    def start(self) -> None:
        """Registra tutti gli handler sull'EventBus."""
        self._bus.subscribe(DRAFT_APPROVED, self._on_draft_approved)
        self._bus.subscribe(CALENDAR_APPROVED, self._on_calendar_approved)
        self._bus.subscribe(TREND_FOUND, self._on_trend_found)
        log.info("orchestrator_started")

    # ------------------------------------------------------------------
    # Handler: bozza approvata → pubblica
    # ------------------------------------------------------------------
    def _on_draft_approved(self, event: dict) -> None:
        """Pubblica immediatamente i draft approvati."""
        event_id = event.get("id")
        draft_id = event.get("draft_id")
        thread = threading.Thread(
            target=self._run_publish,
            args=(event_id, draft_id),
            name=f"Orchestrator-publish-{draft_id}",
            daemon=True,
        )
        thread.start()

    def _run_publish(self, event_id: int | None, draft_id: int | None) -> None:
        from ..agents.social_publisher import SocialPublisherAgent
        try:
            agent = SocialPublisherAgent(
                db=self._db,
                publisher=self._publisher,
                dry_run=False,
            )
            report = agent.run()
            if report.summary:
                self._notifier.send("📤 Pubblicazione automatica", report.summary)
            log.info("orchestrator_publish_done", draft_id=draft_id, status=report.status)
            if event_id:
                self._bus.mark_done(event_id)
        except Exception as exc:  # noqa: BLE001
            log.error("orchestrator_publish_failed", draft_id=draft_id, error=str(exc))
            if event_id:
                self._bus.mark_failed(event_id)

    # ------------------------------------------------------------------
    # Handler: calendario approvato → genera bozze
    # ------------------------------------------------------------------
    def _on_calendar_approved(self, event: dict) -> None:
        """Genera draft per il giorno del calendario approvato."""
        event_id = event.get("id")
        calendar_id = event.get("calendar_id")
        thread = threading.Thread(
            target=self._run_content,
            args=(event_id, calendar_id),
            name=f"Orchestrator-content-{calendar_id}",
            daemon=True,
        )
        thread.start()

    def _run_content(self, event_id: int | None, calendar_id: int | None) -> None:
        from ..agents.content_agent import ContentAgent
        try:
            agent = ContentAgent(db=self._db, llm=self._llm, calendar_id=calendar_id)
            report = agent.run()
            if report.summary:
                self._notifier.send("✍️ Nuova bozza", report.summary)
            log.info("orchestrator_content_done", calendar_id=calendar_id)
            if event_id:
                self._bus.mark_done(event_id)
        except Exception as exc:  # noqa: BLE001
            log.error("orchestrator_content_failed", calendar_id=calendar_id, error=str(exc))
            if event_id:
                self._bus.mark_failed(event_id)

    # ------------------------------------------------------------------
    # Handler: trend trovato → calendario + contenuto
    # ------------------------------------------------------------------
    def _on_trend_found(self, event: dict) -> None:
        """Crea un entry di calendario da un trend e genera subito il draft."""
        event_id = event.get("id")
        trend_topic = event.get("topic", "")
        pillar = event.get("pillar", "tecnologia-semplice")
        keywords = event.get("keywords", [])
        thread = threading.Thread(
            target=self._run_trend_content,
            args=(event_id, trend_topic, pillar, keywords),
            name=f"Orchestrator-trend-{event_id}",
            daemon=True,
        )
        thread.start()

    def _run_trend_content(
        self,
        event_id: int | None,
        topic: str,
        pillar: str,
        keywords: list[str],
    ) -> None:
        from datetime import date
        import json as _json
        from ..agents.content_agent import ContentAgent
        try:
            today = date.today().isoformat()
            # Inserisce un entry di calendario con status 'approvato' (trend già validato)
            with self._db.connect() as conn:
                conn.execute(
                    """INSERT INTO editorial_calendar
                       (week_start, day, date, pillar, format, topic, keywords, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'approvato', ?)""",
                    (
                        today, "extra", today,
                        pillar, "post_facebook",
                        topic,
                        _json.dumps(keywords, ensure_ascii=False),
                        today,
                    ),
                )
                cal_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            agent = ContentAgent(db=self._db, llm=self._llm, calendar_id=cal_id)
            report = agent.run()
            if report.summary:
                self._notifier.send("🔥 Trend → Bozza creata", report.summary)
            log.info("orchestrator_trend_done", topic=topic, calendar_id=cal_id)
            if event_id:
                self._bus.mark_done(event_id)
        except Exception as exc:  # noqa: BLE001
            log.error("orchestrator_trend_failed", topic=topic, error=str(exc))
            if event_id:
                self._bus.mark_failed(event_id)
