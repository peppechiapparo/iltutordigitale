"""TrendResearchAgent — monitora trend Google per topic utili al pubblico over 45.

Usa SOLO endpoint pubblici (nessuna API key richiesta):
- Google Trends RSS: trending searches IT giornaliere
- Google Autocomplete: suggerimenti per keyword seed
Non usa LLM — logica completamente deterministica.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import httpx

from .base import Agent, AgentReport, Finding, Status
from ..core.logging import get_logger

if TYPE_CHECKING:
    from ..core.db import Database
    from ..core.events import EventBus

log = get_logger(__name__)

# Keyword seed: argomenti che interessano agli over 45-65 principianti
SEED_KEYWORDS: list[str] = [
    "WhatsApp anziani",
    "smartphone over 60",
    "sicurezza online",
    "SPID come funziona",
    "email truffa riconoscere",
    "backup foto smartphone",
    "videochiamate WhatsApp",
    "Zoom come funziona",
    "Facebook per anziani",
    "PayPal sicuro",
    "carta di credito online sicurezza",
    "foto smartphone stampare",
    "password sicura come creare",
    "truffa telefonica riconoscere",
    "aggiornamento smartphone come fare",
]

# Pillar mapping basato su keyword
PILLAR_MAP: dict[str, str] = {
    "truffa": "sicurezza-digitale",
    "sicurezza": "sicurezza-digitale",
    "password": "sicurezza-digitale",
    "phishing": "sicurezza-digitale",
    "spid": "identità-digitale",
    "cie": "identità-digitale",
    "fascicolo sanitario": "salute-digitale",
    "ricetta": "salute-digitale",
    "whatsapp": "app-essenziali",
    "zoom": "app-essenziali",
    "facebook": "app-essenziali",
    "instagram": "app-essenziali",
    "foto": "vita-digitale",
    "backup": "vita-digitale",
    "smartphone": "vita-digitale",
    "aggiornamento": "vita-digitale",
}

TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo=IT"
AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"
DEDUP_HOURS = 48  # Non riemettere trend visti nelle ultime N ore


def _detect_pillar(text: str) -> str:
    text_lower = text.lower()
    for kw, pillar in PILLAR_MAP.items():
        if kw in text_lower:
            return pillar
    return "tecnologia-semplice"


def _is_relevant(title: str, related: list[str]) -> bool:
    """Controlla se un trend è rilevante per il target demografico."""
    target_signals = [
        "anzian", "over 60", "over 65", "nonni", "nonna", "nonno",
        "principiant", "semplice", "facil", "aiuto",
        *[k.lower() for k in SEED_KEYWORDS],
    ]
    combined = (title + " " + " ".join(related)).lower()
    return any(sig in combined for sig in target_signals)


def _score_trend(title: str, related: list[str], autocomplete: list[str]) -> int:
    """Punteggio 0-10 basato su rilevanza demografica."""
    score = 0
    combined = (title + " " + " ".join(related + autocomplete)).lower()
    for kw in SEED_KEYWORDS:
        if kw.lower() in combined:
            score += 2
    # Segnali negativi (argomenti non adatti)
    negative = ["calcio", "serie a", "formula 1", "gossip", "cinema", "musica", "sport"]
    if any(n in combined for n in negative):
        score -= 5
    return max(0, min(10, score))


class TrendResearchAgent(Agent):
    """Agente deterministico per ricerca trend Google IT.

    Emette eventi `trend.found` sull'EventBus per ogni topic rilevante.
    Nessun LLM — pura logica di scraping e filtro.
    """

    name = "trend_agent"

    def __init__(
        self,
        db: "Database",
        bus: "EventBus | None" = None,
        http_timeout: float = 10.0,
    ) -> None:
        super().__init__(db)
        self._bus = bus
        self._http_timeout = http_timeout

    # ---- Template: collect -----------------------------------------------

    def collect(self) -> dict:
        """Scarica trend RSS + autocomplete per le keyword seed."""
        trending = self._fetch_trending_rss()
        autocomplete_results: dict[str, list[str]] = {}
        for seed in SEED_KEYWORDS[:6]:  # Limita le chiamate HTTP
            autocomplete_results[seed] = self._fetch_autocomplete(seed)

        return {
            "trending": trending,
            "autocomplete": autocomplete_results,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    # ---- Template: analyze -----------------------------------------------

    def analyze(self, raw: dict) -> tuple[Status, str, list[Finding]]:
        """Filtra i trend rilevanti ed emette eventi EventBus."""
        trending = raw.get("trending", [])
        autocomplete = raw.get("autocomplete", {})

        # Evita duplicati: carica gli ultimi DEDUP_HOURS eventi di tipo trend.found
        recent_topics = self._get_recent_trend_topics()

        emitted: list[str] = []
        findings: list[Finding] = []

        # --- Analizza trending RSS ---
        for item in trending:
            title = item.get("title", "")
            related = item.get("related", [])
            auto = []
            for seed, sugg in autocomplete.items():
                if any(kw.lower() in title.lower() for kw in seed.split()):
                    auto = sugg
                    break

            score = _score_trend(title, related, auto)
            if score < 2:
                continue

            if title.lower() in recent_topics:
                log.debug("trend_dedup_skip", topic=title)
                continue

            pillar = _detect_pillar(title + " " + " ".join(related))
            keywords = list({
                w for w in re.findall(r"\b\w{4,}\b", (title + " " + " ".join(related)).lower())
                if w not in {"come", "cosa", "sono", "anno", "dopo", "dove", "ogni", "nelle", "degli"}
            })[:8]

            payload = {
                "topic": title,
                "pillar": pillar,
                "keywords": keywords,
                "source": "google_trends_rss",
                "score": score,
            }

            if self._bus:
                from ..core.events import TREND_FOUND
                self._bus.emit(TREND_FOUND, payload)
                log.info("trend_emitted", topic=title, score=score, pillar=pillar)
            emitted.append(f"[{score}] {title} ({pillar})")
            findings.append(Finding(
                severity="info",
                code="trend.found",
                message=f"Trend trovato: {title}",
            ))

        # --- Fallback: analizza anche i suggerimenti autocomplete ---
        # Questo garantisce output anche quando il feed RSS non è disponibile
        for seed, suggestions in autocomplete.items():
            for suggestion in suggestions:
                # Scarta suggerimenti con numeri (codici corso, prezzi, ecc.)
                if re.search(r'\d{3,}', suggestion):
                    continue
                # Scarta argomenti chiaramente non pertinenti al target
                irrelevant = ["minecraft", "ecampus", "cyberbullismo", "sas ", "riassunto", "immagini"]
                if any(irr in suggestion.lower() for irr in irrelevant):
                    continue
                if suggestion.lower() in recent_topics:
                    continue
                if any(e.lower().endswith(suggestion.lower()) for e in emitted):
                    continue  # già emesso come RSS
                score = _score_trend(suggestion, [seed], [])
                if score < 2:  # soglia uguale a RSS — se viene da autocomplete della seed è già rilevante
                    continue
                pillar = _detect_pillar(suggestion + " " + seed)
                keywords = list({
                    w for w in re.findall(r"\b\w{4,}\b", (suggestion + " " + seed).lower())
                    if w not in {"come", "cosa", "sono", "anno", "dopo", "dove", "ogni"}
                })[:6]
                payload = {
                    "topic": suggestion,
                    "pillar": pillar,
                    "keywords": keywords,
                    "source": "google_autocomplete",
                    "score": score,
                }
                if self._bus:
                    from ..core.events import TREND_FOUND
                    self._bus.emit(TREND_FOUND, payload)
                    log.info("trend_autocomplete_emitted", topic=suggestion, score=score)
                emitted.append(f"[{score}] {suggestion} ({pillar})")
                findings.append(Finding(
                    severity="info",
                    code="trend.autocomplete",
                    message=f"Trend autocomplete: {suggestion}",
                ))

        if not emitted:
            summary = "Nessun trend rilevante trovato per il target over 45."
            status: Status = "ok"
        else:
            summary = (
                f"🔥 {len(emitted)} trend trovati e inoltrati agli agenti:\n"
                + "\n".join(f"• {e}" for e in emitted)
            )
            status = "ok"

        return status, summary, findings

    # ---- Private helpers -------------------------------------------------

    def _fetch_trending_rss(self) -> list[dict]:
        """Scarica e parsa il feed RSS di Google Trends IT."""
        try:
            resp = httpx.get(TRENDS_RSS_URL, timeout=self._http_timeout, follow_redirects=True)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            items = []
            for item in root.iter("item"):
                title_el = item.find("title")
                if title_el is None or not title_el.text:
                    continue
                related_queries = [
                    q.text for q in item.findall(".//{https://trends.google.com/trends/trendingsearches/daily}query_topics/{https://trends.google.com/trends/trendingsearches/daily}query")
                    if q.text
                ]
                items.append({"title": title_el.text.strip(), "related": related_queries})
            log.debug("trends_rss_fetched", count=len(items))
            return items
        except Exception as exc:  # noqa: BLE001
            log.warning("trends_rss_failed", error=str(exc))
            return []

    def _fetch_autocomplete(self, query: str) -> list[str]:
        """Scarica i suggerimenti autocomplete di Google per una query."""
        try:
            resp = httpx.get(
                AUTOCOMPLETE_URL,
                params={"client": "firefox", "hl": "it", "q": query},
                timeout=self._http_timeout,
                follow_redirects=True,
            )
            resp.raise_for_status()
            data = resp.json()
            # Format: [query, [suggestion1, suggestion2, ...]]
            suggestions: list[str] = data[1] if len(data) > 1 else []
            log.debug("autocomplete_fetched", query=query, count=len(suggestions))
            return suggestions[:5]
        except Exception as exc:  # noqa: BLE001
            log.warning("autocomplete_failed", query=query, error=str(exc))
            return []

    def _get_recent_trend_topics(self) -> set[str]:
        """Restituisce i topic già emessi nelle ultime DEDUP_HOURS ore."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=DEDUP_HOURS)).isoformat()
        try:
            with self._db.connect() as conn:
                rows = conn.execute(
                    "SELECT payload FROM events"
                    " WHERE event_type='trend.found' AND created_at >= ?",
                    (cutoff,),
                ).fetchall()
            topics: set[str] = set()
            for (payload_json,) in rows:
                try:
                    p = json.loads(payload_json)
                    if "topic" in p:
                        topics.add(p["topic"].lower())
                except (json.JSONDecodeError, KeyError):
                    pass
            return topics
        except Exception:  # noqa: BLE001
            return set()
