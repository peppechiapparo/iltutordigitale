"""Notifier interface + Telegram implementation (Strategy pattern).

Supporta:
- send()                  — messaggio semplice (Markdown)
- send_with_approval()    — messaggio con bottoni inline ✅/✏️/❌ (gate umano)
"""

from __future__ import annotations

from typing import Protocol

import httpx

from ..core.logging import get_logger

log = get_logger(__name__)


class Notifier(Protocol):
    """Anything that can deliver a short message to a human."""

    def send(self, subject: str, body: str) -> bool: ...


class NullNotifier:
    """Used when no channel is configured — logs only."""

    def send(self, subject: str, body: str) -> bool:
        log.info("notify_null", subject=subject, body_preview=body[:120])
        return True

    def send_with_approval(
        self,
        subject: str,
        body: str,
        ref_table: str,
        ref_id: int,
    ) -> bool:
        log.info(
            "notify_null_approval",
            subject=subject,
            ref_table=ref_table,
            ref_id=ref_id,
        )
        return True


class TelegramNotifier:
    """Sends messages via Telegram Bot API.

    Token & chat_id are passed explicitly (DI) — no global state.
    """

    API = "https://api.telegram.org"

    def __init__(self, bot_token: str, chat_id: str, timeout: float = 10.0) -> None:
        self._token = bot_token
        self._chat_id = chat_id
        self._timeout = timeout

    def _post(self, endpoint: str, payload: dict) -> bool:
        if not self._token or not self._chat_id:
            log.warning("telegram_not_configured")
            return False
        url = f"{self.API}/bot{self._token}/{endpoint}"
        try:
            r = httpx.post(url, json=payload, timeout=self._timeout)
            r.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            log.error("telegram_send_failed", endpoint=endpoint, error=str(exc))
            return False

    def send(self, subject: str, body: str) -> bool:
        """Invia un messaggio Markdown semplice."""
        text = f"*{subject}*\n\n{body}"
        if len(text) > 4000:
            text = text[:3990] + "\n…(troncato)"
        return self._post("sendMessage", {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        })

    def send_with_approval(
        self,
        subject: str,
        body: str,
        ref_table: str,
        ref_id: int,
    ) -> bool:
        """Invia un messaggio con bottoni inline ✅ Approva / ✏️ Modifica / ❌ Scarta.

        Il callback_data ha formato: "approve:{ref_table}:{ref_id}" ecc.
        Un handler separato (polling) deve processare i callback_query.
        """
        text = f"*{subject}*\n\n{body}"
        if len(text) > 4000:
            text = text[:3990] + "\n…(troncato)"
        keyboard = {
            "inline_keyboard": [[
                {
                    "text": "✅ Approva",
                    "callback_data": f"approve:{ref_table}:{ref_id}"
                },
                {
                    "text": "✏️ Modifica",
                    "callback_data": f"edit:{ref_table}:{ref_id}"
                },
                {
                    "text": "❌ Scarta",
                    "callback_data": f"discard:{ref_table}:{ref_id}"
                },
            ]]
        }
        return self._post("sendMessage", {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
            "reply_markup": keyboard,
        })


def build_notifier(bot_token: str, chat_id: str) -> TelegramNotifier | NullNotifier:
    """Factory — picks the right notifier based on configuration."""
    if bot_token and chat_id:
        return TelegramNotifier(bot_token, chat_id)
    return NullNotifier()
