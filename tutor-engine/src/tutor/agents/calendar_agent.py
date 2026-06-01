"""Calendar Agent — propone il calendario editoriale settimanale via LLM.

Pattern: Template Method + ReAct.
Il LLM ragiona sui pillar tematici e i formati e propone un piano per la settimana
successiva. L'umano approva via Telegram (gate umano).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from ..core.db import Database
from ..core.logging import get_logger
from .base import LLMAgent, AgentReport

log = get_logger(__name__)

# 5 pilastri tematici del Tutor Digitale (da docs/07-CONTENUTI-STRATEGY.md)
CONTENT_PILLARS = [
    "Smartphone",
    "WhatsApp & messaggistica",
    "Sicurezza online",
    "PC & internet",
    "App utili",
]

# Formati per giorno (calendario fisso — docs/07)
WEEKLY_SCHEDULE = {
    "lunedì":    {"primary": "YouTube lungo", "duration": "10-14 min"},
    "martedì":   {"primary": "Post community Facebook", "duration": "testo breve"},
    "mercoledì": {"primary": "Reel IG + TikTok", "duration": "45-60s"},
    "giovedì":   {"primary": "Reel Facebook", "duration": "45-60s"},
    "venerdì":   {"primary": "YouTube Short", "duration": "30-45s"},
}

CALENDAR_SYSTEM_PROMPT = """\
Sei il content strategist de "Il Tutor Digitale", portale di tutorial tecnologici
per italiani over 45-65 principianti. Creator: Giuseppe.

## Il tuo compito
Proponi il calendario editoriale per la settimana del {week_start} (da lunedì a venerdì).
Usa il formato fisso settimanale e i 5 pillar tematici. Varia i pillar nel corso della settimana.

## Formato fisso settimanale
- Lunedì: Video YouTube lungo (10-14 min)
- Martedì: Post community Facebook (domanda/discussione)
- Mercoledì: Reel IG + TikTok (45-60s, clip dal video di lunedì)
- Giovedì: Reel Facebook (stesso Reel del mercoledì)
- Venerdì: YouTube Short (tip veloce o teaser, 30-45s)

## 5 Pillar tematici
1. Smartphone — uso quotidiano (foto, app, impostazioni, spazio)
2. WhatsApp & messaggistica — videochiamate, gruppi, backup, state
3. Sicurezza online — truffe, password, SPID, phishing, SMS sospetti
4. PC & internet — email, navigazione, stampa, file, browser
5. App utili — banca, Fascicolo Sanitario, PagoPA, mappe, trasporti

## Criteri di scelta argomento
1. Problemi reali ad alto volume di ricerca (pensa a cosa cerca un over 60)
2. Domande frequenti (es. "come fare la videochiamata", "ho ricevuto SMS sospetto")
3. Stagionalità (estate 2026: SPID, dichiarazione redditi, vacanze con smartphone)
4. Argomenti correlati e continuativi (es. lunedì WhatsApp → mercoledì clip da quel video)

## Regola principale
Il Reel di mercoledì e giovedì deve essere derivato dal video di lunedì (riuso 1→7).

## Output richiesto
Usa il tool `save_calendar` per salvare il calendario proposto.
Per ogni giorno proponi: pillar, argomento specifico, keyword principali (2-3), breve note regia.

La settimana di riferimento è: {week_start} (lunedì) — {week_end} (venerdì).
Contesto storico (pubblicazioni recenti): {recent_topics}
"""

CALENDAR_TOOLS = [
    {
        "name": "save_calendar",
        "description": "Salva il calendario editoriale proposto per la settimana.",
        "input_schema": {
            "type": "object",
            "properties": {
                "week_start": {
                    "type": "string",
                    "description": "Data di inizio settimana (lunedì) in formato YYYY-MM-DD"
                },
                "days": {
                    "type": "array",
                    "description": "Lista di 5 voci (lun-ven), una per giorno",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day":      {"type": "string", "description": "Nome giorno in italiano"},
                            "date":     {"type": "string", "description": "Data YYYY-MM-DD"},
                            "pillar":   {"type": "string", "description": "Pillar tematico"},
                            "format":   {"type": "string", "description": "Formato contenuto"},
                            "topic":    {"type": "string", "description": "Argomento specifico (titolo bozza)"},
                            "keywords": {"type": "array", "items": {"type": "string"}, "description": "2-3 keyword principali"},
                            "notes":    {"type": "string", "description": "Brevi note aggiuntive (max 1 riga)"}
                        },
                        "required": ["day", "date", "pillar", "format", "topic", "keywords"]
                    }
                }
            },
            "required": ["week_start", "days"]
        }
    }
]


class CalendarAgent(LLMAgent):
    """Propone il calendario editoriale settimanale.

    Ogni lunedì mattina (06:30) genera il piano per la settimana successiva
    e lo invia su Telegram per approvazione umana.
    """

    name = "calendar_agent"

    def __init__(self, db: Database, llm: Any) -> None:
        super().__init__(db, llm)
        self._calendar_result: list[dict] | None = None
        self._week_start: str = ""

    def collect(self) -> dict:
        """Calcola la settimana target e recupera i topic recenti per evitare ripetizioni."""
        today = date.today()
        # Propone per la prossima settimana (da lunedì prossimo)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        self._week_start = next_monday.isoformat()

        # Recupera i topic delle ultime 2 settimane per evitare ripetizioni
        recent = self._get_recent_topics()
        return {
            "week_start": self._week_start,
            "week_end": (next_monday + timedelta(days=4)).isoformat(),
            "recent_topics": recent,
        }

    def _get_recent_topics(self) -> str:
        """Legge i topic degli ultimi 14 giorni dal DB."""
        cutoff = (date.today() - timedelta(days=14)).isoformat()
        try:
            with self._db.connect() as conn:
                rows = conn.execute(
                    "SELECT day, topic FROM editorial_calendar WHERE date >= ? ORDER BY date DESC",
                    (cutoff,),
                ).fetchall()
            if not rows:
                return "Nessuna pubblicazione recente."
            return "; ".join(f"{r['day']}: {r['topic']}" for r in rows)
        except Exception:  # noqa: BLE001
            return "Dati non disponibili."

    def build_system_prompt(self, context: dict) -> str:
        return CALENDAR_SYSTEM_PROMPT.format(
            week_start=context["week_start"],
            week_end=context["week_end"],
            recent_topics=context["recent_topics"],
        )

    def get_tools(self) -> list[dict]:
        return CALENDAR_TOOLS

    def _build_initial_message(self, context: dict) -> str:
        week_start = context["week_start"]
        week_end = context["week_end"]
        recent = context["recent_topics"]
        return (
            f"Proponi il calendario editoriale per la settimana {week_start}–{week_end}. "
            f"Topic recenti da evitare: {recent}. "
            "Chiama save_calendar con le 5 voci (lun-ven), poi chiama report_findings con lista vuota."
        )

    def _dispatch_tool(self, tool_name: str, tool_input: dict) -> str:
        """Intercetta save_calendar (agent-specific) prima del dispatch globale."""
        if tool_name != "save_calendar":
            return super()._dispatch_tool(tool_name, tool_input)

        week_start = tool_input["week_start"]
        days = tool_input["days"]
        from datetime import datetime
        now = datetime.now().isoformat(timespec="seconds")

        with self._db.connect() as conn:
            for day_data in days:
                conn.execute(
                    """INSERT INTO editorial_calendar
                       (week_start, day, date, pillar, format, topic, keywords,
                        status, notes, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'proposto', ?, ?)""",
                    (
                        week_start,
                        day_data["day"],
                        day_data["date"],
                        day_data["pillar"],
                        day_data["format"],
                        day_data["topic"],
                        json.dumps(day_data.get("keywords", []), ensure_ascii=False),
                        day_data.get("notes", ""),
                        now,
                    ),
                )

        self._calendar_result = days
        log.info("calendar_saved", week_start=week_start, days=len(days))
        return f"Calendario salvato: {len(days)} voci per settimana {week_start}."

    def _build_summary(self, status: object, findings: object) -> str:
        """Costruisce il testo del report finale (per Telegram e DB)."""
        if not self._calendar_result:
            return "Nessun calendario generato."

        week = self._week_start
        lines = [f"📅 *Calendario settimana {week}*\n"]
        for day in self._calendar_result:
            kw = ", ".join(day.get("keywords", []))
            lines.append(
                f"*{day['day'].capitalize()} {day['date']}*\n"
                f"  🎯 {day['pillar']} — {day['format']}\n"
                f"  📌 {day['topic']}\n"
                f"  🔑 {kw}"
            )
        lines.append("\nRispondi con ✅ Approva, ✏️ Modifica o ❌ Scarta.")
        return "\n".join(lines)
