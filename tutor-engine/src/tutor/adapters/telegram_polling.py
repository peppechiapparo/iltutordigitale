"""Telegram Polling Handler — processa i callback_query dai bottoni inline.

Gira in un thread background separato (non-async, long-polling getUpdates).
Gestisce le decisioni umane ✅ Approva / ✏️ Modifica / ❌ Scarta sulle bozze
del calendario editoriale e sui draft generati dal ContentAgent.

Architettura:
- Thread daemon: si avvia nel lifespan FastAPI e si ferma con il server.
- Long-polling: getUpdates(timeout=30) — nessun webhook necessario (Pi in LAN).
- callback_data format: "{decision}:{ref_table}:{ref_id}"
  es. "approve:editorial_calendar:5", "discard:drafts:12"
- Ogni decisione: aggiorna DB → registra in approvals → answerCallbackQuery →
  edita il messaggio originale con il risultato.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING

import httpx

from ..core.logging import get_logger

if TYPE_CHECKING:
    from ..core.db import Database

log = get_logger(__name__)

TELEGRAM_API = "https://api.telegram.org"

# Mappa decision string → status nel DB
DECISION_TO_STATUS = {
    "approve": "approvato",
    "edit":    "modificato",
    "discard": "scartato",
}

DECISION_EMOJI = {
    "approve": "✅",
    "edit":    "✏️",
    "discard": "❌",
}

DECISION_LABEL = {
    "approve": "Approvato",
    "edit":    "Da modificare",
    "discard": "Scartato",
}


class TelegramPollingHandler:
    """Background thread che processa i callback_query di approvazione."""

    def __init__(self, bot_token: str, db: "Database", timeout: float = 10.0) -> None:
        self._token = bot_token
        self._db = db
        self._timeout = timeout
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_update_id: int = 0

    def start(self) -> None:
        if not self._token:
            log.warning("telegram_polling_disabled", reason="no bot token")
            return
        self._thread = threading.Thread(
            target=self._run,
            name="TelegramPolling",
            daemon=True,
        )
        self._thread.start()
        log.info("telegram_polling_started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            log.info("telegram_polling_stopped")

    def _run(self) -> None:
        """Loop principale: long-polling con backoff in caso di errori."""
        backoff = 1
        while not self._stop_event.is_set():
            try:
                updates = self._get_updates(poll_timeout=30)
                backoff = 1  # reset backoff on success
                for update in updates:
                    self._handle_update(update)
            except httpx.HTTPError as exc:
                log.warning("telegram_polling_error", error=str(exc), backoff=backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
            except Exception as exc:  # noqa: BLE001
                log.error("telegram_polling_unexpected", error=str(exc))
                time.sleep(5)

    def _get_updates(self, poll_timeout: int = 30) -> list[dict]:
        """Long-polling: aspetta max poll_timeout secondi per nuovi update."""
        url = f"{TELEGRAM_API}/bot{self._token}/getUpdates"
        params: dict = {
            "timeout": poll_timeout,
            "allowed_updates": ["callback_query"],
        }
        if self._last_update_id:
            params["offset"] = self._last_update_id + 1

        r = httpx.get(url, params=params, timeout=poll_timeout + 5)
        r.raise_for_status()
        data = r.json()
        updates = data.get("result", [])

        if updates:
            self._last_update_id = updates[-1]["update_id"]

        return updates

    def _handle_update(self, update: dict) -> None:
        """Processa un singolo update dal bot."""
        cq = update.get("callback_query")
        if not cq:
            return

        callback_id = cq["id"]
        callback_data = cq.get("data", "")
        message = cq.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        msg_id = message.get("message_id")
        user = cq.get("from", {})
        user_id = str(user.get("id", ""))
        user_name = user.get("username") or user.get("first_name", "utente")

        log.info(
            "telegram_callback",
            callback_data=callback_data,
            user=user_name,
        )

        parts = callback_data.split(":", 2)
        if len(parts) != 3:
            self._answer_callback(callback_id, "⚠️ Formato callback non riconosciuto.")
            return

        decision_key, ref_table, ref_id_str = parts
        if decision_key not in DECISION_TO_STATUS:
            self._answer_callback(callback_id, "⚠️ Azione non riconosciuta.")
            return

        try:
            ref_id = int(ref_id_str)
        except ValueError:
            self._answer_callback(callback_id, "⚠️ ID non valido.")
            return

        # Aggiorna DB
        new_status = DECISION_TO_STATUS[decision_key]
        ok = self._update_status(ref_table, ref_id, new_status, user_id)

        if not ok:
            self._answer_callback(callback_id, "⚠️ Record non trovato nel database.")
            return

        # Registra in approvals
        self._record_approval(ref_table, ref_id, decision_key, user_id, msg_id)

        # Answer callback (rimuove il "caricamento" sul bottone)
        emoji = DECISION_EMOJI[decision_key]
        label = DECISION_LABEL[decision_key]
        self._answer_callback(callback_id, f"{emoji} {label}")

        # Edita il messaggio originale per mostrare la decisione
        if chat_id and msg_id:
            self._edit_message_result(chat_id, msg_id, emoji, label, user_name, ref_table, ref_id)

    def _update_status(self, ref_table: str, ref_id: int, new_status: str, user_id: str) -> bool:
        """Aggiorna lo status del record nel DB. Ritorna True se trovato."""
        valid_tables = {"editorial_calendar", "drafts"}
        if ref_table not in valid_tables:
            log.warning("telegram_invalid_table", table=ref_table)
            return False

        approved_at = datetime.now().isoformat(timespec="seconds") if new_status == "approvato" else None

        with self._db.connect() as conn:
            if ref_table == "editorial_calendar":
                result = conn.execute(
                    "UPDATE editorial_calendar SET status = ?, approved_at = ? WHERE id = ?",
                    (new_status, approved_at, ref_id),
                )
            else:  # drafts
                result = conn.execute(
                    "UPDATE drafts SET status = ?, approved_at = ? WHERE id = ?",
                    (new_status, approved_at, ref_id),
                )

        updated = result.rowcount > 0
        if updated:
            log.info("status_updated", table=ref_table, ref_id=ref_id, status=new_status)
        else:
            log.warning("status_update_not_found", table=ref_table, ref_id=ref_id)
        return updated

    def _record_approval(
        self,
        ref_table: str,
        ref_id: int,
        decision_key: str,
        user_id: str,
        msg_id: int | None,
    ) -> None:
        """Inserisce un record nella tabella approvals (audit log)."""
        with self._db.connect() as conn:
            conn.execute(
                """INSERT INTO approvals
                   (ref_table, ref_id, telegram_msg_id, decision, decided_by, decided_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    ref_table,
                    ref_id,
                    msg_id,
                    DECISION_TO_STATUS[decision_key],
                    user_id,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

    def _answer_callback(self, callback_id: str, text: str) -> None:
        """Risponde al callback_query (obbligatorio per rimuovere lo spinner)."""
        try:
            httpx.post(
                f"{TELEGRAM_API}/bot{self._token}/answerCallbackQuery",
                json={"callback_query_id": callback_id, "text": text, "show_alert": False},
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            log.warning("telegram_answer_callback_failed", error=str(exc))

    def _edit_message_result(
        self,
        chat_id: int,
        msg_id: int,
        emoji: str,
        label: str,
        user_name: str,
        ref_table: str,
        ref_id: int,
    ) -> None:
        """Edita il messaggio originale aggiungendo il risultato della decisione.

        Rimuove i bottoni inline (reply_markup vuoto) e aggiunge riga finale.
        """
        try:
            # Prima legge il testo attuale del messaggio
            # (non possiamo recuperarlo direttamente, aggiungiamo solo la nota)
            footer = f"\n\n─────────────────\n{emoji} *{label}* da @{user_name}"
            httpx.post(
                f"{TELEGRAM_API}/bot{self._token}/editMessageReplyMarkup",
                json={
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "reply_markup": {"inline_keyboard": []},  # rimuove i bottoni
                },
                timeout=self._timeout,
            )
            # Appende footer al messaggio (richiede il testo originale — lo skippiamo
            # per semplicità: i bottoni rimossi già segnalano la decisione)
            log.info(
                "telegram_message_updated",
                chat_id=chat_id,
                msg_id=msg_id,
                decision=label,
            )
        except httpx.HTTPError as exc:
            log.warning("telegram_edit_message_failed", error=str(exc))


def build_polling_handler(
    bot_token: str,
    db: "Database",
) -> TelegramPollingHandler:
    """Factory — crea il polling handler. Se token mancante torna un no-op."""
    return TelegramPollingHandler(bot_token=bot_token, db=db)
