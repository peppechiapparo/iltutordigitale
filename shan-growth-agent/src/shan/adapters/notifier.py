"""Notifier interface + Telegram implementation (Strategy pattern)."""

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


class TelegramNotifier:
    """Sends messages via Telegram Bot API.

    Token & chat_id are passed explicitly (DI) — no global state.
    """

    API = "https://api.telegram.org"

    def __init__(self, bot_token: str, chat_id: str, timeout: float = 10.0) -> None:
        self._token = bot_token
        self._chat_id = chat_id
        self._timeout = timeout

    def send(self, subject: str, body: str) -> bool:
        if not self._token or not self._chat_id:
            log.warning("telegram_not_configured")
            return False
        text = f"*{subject}*\n\n{body}"
        # Telegram hard limit ~4096 chars
        if len(text) > 4000:
            text = text[:3990] + "\n…(truncated)"
        url = f"{self.API}/bot{self._token}/sendMessage"
        try:
            r = httpx.post(
                url,
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
                timeout=self._timeout,
            )
            r.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            log.error("telegram_send_failed", error=str(exc))
            return False


def build_notifier(bot_token: str, chat_id: str) -> Notifier:
    """Factory — picks the right notifier based on configuration."""
    if bot_token and chat_id:
        return TelegramNotifier(bot_token, chat_id)
    return NullNotifier()
