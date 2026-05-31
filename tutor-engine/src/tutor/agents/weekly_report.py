"""Weekly Report Agent — report narrativo domenicale.

Ogni domenica alle 18:00 raccoglie i dati della settimana (dal DB locale + GSC
se disponibile), li passa all'LLM che genera un report narrativo, e lo invia
su Telegram.

Pattern: Template Method (non ReAct — niente loop LLM con tool, solo
collect() + singola chiamata LLM per la narrativa).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from ..core.db import Database
from ..core.logging import get_logger
from .base import Agent, AgentReport, Finding, Status

log = get_logger(__name__)


REPORT_PROMPT = """\
Sei il data analyst de "Il Tutor Digitale". Produci un report settimanale
narrativo, in italiano, breve (max 300 parole) e orientato all'azione.

## Dati settimana {week_start} → {week_end}

### Calendario editoriale
{calendar_stats}

### Bozze contenuto
{drafts_stats}

### Stato approvazioni
{approvals_stats}

### SEO Monitor (ultima run)
{seo_stats}

{gsc_section}

## Formato output
Scrivi in 4 sezioni:
1. **📊 Cosa è successo questa settimana** (2-3 righe)
2. **✅ Risultati** (bullet: calendario, bozze, approvazioni)
3. **⚠️ Attenzione** (se ci sono problemi SEO, bozze scartate, slot vuoti)
4. **🎯 Priorità prossima settimana** (max 3 azioni concrete)

Sii diretto e pratico. Niente frasi generiche.
"""

GSC_SECTION_PLACEHOLDER = """\
### Google Search Console
Non ancora configurato. Configura `GSC_SERVICE_ACCOUNT_JSON` per ricevere
le metriche di traffico organico.
"""


class WeeklyReportAgent(Agent):
    """Report narrativo domenicale — usa LLM in singola chiamata (non ReAct)."""

    name = "weekly_report"

    def __init__(self, db: Database, llm: Any) -> None:
        super().__init__(db)
        self._llm = llm
        self._report_text: str = ""

    def collect(self) -> dict:
        """Raccoglie dati DB della settimana appena conclusa."""
        today = date.today()
        # Settimana scorsa: da lunedì a domenica
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + timedelta(days=6)

        week_start = last_monday.isoformat()
        week_end = last_sunday.isoformat()

        with self._db.connect() as conn:
            # Calendario editoriale
            cal_rows = conn.execute(
                """SELECT status, COUNT(*) as cnt
                   FROM editorial_calendar
                   WHERE date BETWEEN ? AND ?
                   GROUP BY status""",
                (week_start, week_end),
            ).fetchall()

            # Bozze generate
            drafts_rows = conn.execute(
                """SELECT content_type, status, COUNT(*) as cnt
                   FROM drafts
                   WHERE created_at BETWEEN ? AND ?
                   GROUP BY content_type, status""",
                (week_start + "T00:00:00", week_end + "T23:59:59"),
            ).fetchall()

            # Approvazioni gate umano
            approvals_rows = conn.execute(
                """SELECT decision, COUNT(*) as cnt
                   FROM approvals
                   WHERE decided_at BETWEEN ? AND ?
                   GROUP BY decision""",
                (week_start + "T00:00:00", week_end + "T23:59:59"),
            ).fetchall()

            # Ultima run SEO monitor
            seo_run = conn.execute(
                """SELECT status, summary, finished_at
                   FROM agent_runs WHERE agent = 'seo_monitor'
                   ORDER BY id DESC LIMIT 1""",
            ).fetchone()

            # Findings SEO critici/error
            seo_alerts: list = []
            if seo_run:
                seo_alerts = conn.execute(
                    """SELECT severity, code, message
                       FROM findings f
                       JOIN agent_runs r ON f.run_id = r.id
                       WHERE r.agent = 'seo_monitor'
                       AND f.severity IN ('critical', 'error')
                       ORDER BY r.id DESC LIMIT 5""",
                ).fetchall()

        return {
            "week_start": week_start,
            "week_end": week_end,
            "calendar": [dict(r) for r in cal_rows],
            "drafts": [dict(r) for r in drafts_rows],
            "approvals": [dict(r) for r in approvals_rows],
            "seo_run": dict(seo_run) if seo_run else None,
            "seo_alerts": [dict(r) for r in seo_alerts],
        }

    def analyze(self, raw: dict) -> tuple[Status, str, list[Finding]]:
        """Genera il report narrativo con una singola chiamata LLM."""
        # Formatta le sezioni
        cal_stats = self._format_calendar(raw["calendar"])
        drafts_stats = self._format_drafts(raw["drafts"])
        approvals_stats = self._format_approvals(raw["approvals"])
        seo_stats = self._format_seo(raw["seo_run"], raw["seo_alerts"])

        prompt = REPORT_PROMPT.format(
            week_start=raw["week_start"],
            week_end=raw["week_end"],
            calendar_stats=cal_stats,
            drafts_stats=drafts_stats,
            approvals_stats=approvals_stats,
            seo_stats=seo_stats,
            gsc_section=GSC_SECTION_PLACEHOLDER,
        )

        # Singola chiamata LLM (no tools, no loop)
        try:
            response = self._llm.complete(prompt, max_tokens=1024)
            self._report_text = response.text
        except Exception as exc:  # noqa: BLE001
            log.error("weekly_report_llm_error", error=str(exc))
            self._report_text = (
                f"⚠️ Errore generazione report: {exc}\n\n"
                f"Dati grezzi:\n{cal_stats}\n{drafts_stats}"
            )

        # Determina status in base ai finding SEO
        has_critical = any(
            a.get("severity") == "critical" for a in raw["seo_alerts"]
        )
        status: Status = "error" if has_critical else "ok"

        return status, self._report_text, []

    # ── Formatter helpers ──────────────────────────────────────────────────

    @staticmethod
    def _format_calendar(rows: list[dict]) -> str:
        if not rows:
            return "Nessuna voce di calendario questa settimana."
        total = sum(r["cnt"] for r in rows)
        by_status = {r["status"]: r["cnt"] for r in rows}
        parts = [f"Totale slot: {total}"]
        for s in ("proposto", "approvato", "modificato", "scartato", "prodotto", "pubblicato"):
            if s in by_status:
                parts.append(f"  - {s}: {by_status[s]}")
        return "\n".join(parts)

    @staticmethod
    def _format_drafts(rows: list[dict]) -> str:
        if not rows:
            return "Nessuna bozza generata questa settimana."
        lines = []
        for r in rows:
            lines.append(f"  - {r['content_type']} [{r['status']}]: {r['cnt']}")
        return "\n".join(lines)

    @staticmethod
    def _format_approvals(rows: list[dict]) -> str:
        if not rows:
            return "Nessuna approvazione questa settimana."
        return "\n".join(f"  - {r['decision']}: {r['cnt']}" for r in rows)

    @staticmethod
    def _format_seo(seo_run: dict | None, alerts: list[dict]) -> str:
        if not seo_run:
            return "Nessuna run SEO questa settimana."
        lines = [
            f"Status: {seo_run['status']}",
            f"Ultima run: {seo_run.get('finished_at', 'N/D')}",
            f"Sommario: {seo_run.get('summary', 'N/D')}",
        ]
        if alerts:
            lines.append(f"Alert critici ({len(alerts)}):")
            for a in alerts:
                lines.append(f"  - [{a['severity']}] {a['code']}: {a['message']}")
        return "\n".join(lines)
