"""Social Publisher Agent — pubblica bozze approvate sui canali Meta.

Processo:
  1. collect()  → lista bozze con status='approvato' non ancora pubblicate
  2. analyze()  → per ogni bozza: determina la piattaforma, chiama Meta API,
                  aggiorna status a 'pubblicato' nel DB, inserisce in publication_log
  3. Findings:  un finding per ogni pubblicazione (ok/error/skipped)

Content type → Piattaforma:
  - post_facebook → Facebook Page (testo + link)
  - reel          → Instagram (caption + image_url, se disponibile)
  - post (generico) → Facebook
  - altri         → skip (warning finding)

L'agente è DETERMINISTICO: nessun LLM, solo Meta Graph API + DB.

Gate umano: le bozze arrivano qui già approvate via Telegram (status='approvato').
L'agente non ri-chiede approvazione: pubblica direttamente.
Per un'ulteriore conferma prima di pubblicare, usa --dry-run da CLI.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ..adapters.meta_publisher import MetaPublisher, NullMetaPublisher, build_meta_publisher
from ..core.db import Database
from ..core.logging import get_logger
from .base import Agent, AgentReport, Finding, Status

if TYPE_CHECKING:
    pass

log = get_logger(__name__)

# Quale piattaforma usare per ciascun content_type
PLATFORM_MAP: dict[str, str] = {
    "post_facebook": "facebook",
    "reel":          "instagram",
    "post":          "facebook",  # generico
    "article":       "skip",      # va sul portale web, non social
    "script_youtube": "skip",     # YouTube upload richiede OAuth2 separato
    "script_short":   "skip",     # YouTube Short, idem
}


class SocialPublisherAgent(Agent):
    """Pubblica bozze approvate su Facebook Page e/o Instagram.

    Parametri:
        publisher: adapter Meta (MetaPublisher o NullMetaPublisher)
        dry_run:   se True, non chiama l'API Meta — utile per test
    """

    name = "social_publisher"

    def __init__(
        self,
        db: Database,
        publisher: "MetaPublisher | NullMetaPublisher",
        dry_run: bool = False,
    ) -> None:
        super().__init__(db)
        self._publisher = publisher
        self._dry_run = dry_run

    # ── Template Method ───────────────────────────────────────────────────────

    def collect(self) -> dict:
        """Carica dal DB le bozze approvate non ancora pubblicate."""
        with self._db.connect() as conn:
            rows = conn.execute(
                """SELECT id, calendar_id, content_type, title, body, seo_title,
                          meta_desc, notes
                   FROM drafts
                   WHERE status = 'approvato'
                     AND (published_at IS NULL OR published_at = '')
                   ORDER BY approved_at ASC
                   LIMIT 10"""
            ).fetchall()

        drafts = [dict(r) for r in rows]
        log.info("social_publisher_collect", found=len(drafts))
        return {"drafts": drafts}

    def analyze(self, raw: dict) -> tuple[Status, str, list[Finding]]:
        """Pubblica ogni bozza e genera findings con l'esito."""
        drafts = raw.get("drafts", [])

        if not drafts:
            return "ok", "Nessuna bozza approvata da pubblicare.", []

        findings: list[Finding] = []
        published = 0
        skipped = 0
        errors = 0

        for draft in drafts:
            finding = self._process_draft(draft)
            findings.append(finding)
            if finding.code == "published":
                published += 1
            elif finding.code in ("skipped", "dry_run", "credentials_missing"):
                skipped += 1
            else:
                errors += 1

        parts: list[str] = []
        if published:
            parts.append(f"✅ {published} pubblicat{'o' if published == 1 else 'i'}")
        if skipped:
            parts.append(f"⏭️ {skipped} saltati")
        if errors:
            parts.append(f"❌ {errors} errori")

        summary = "📤 Social Publisher: " + ", ".join(parts) if parts else "Nessuna azione eseguita."
        status: Status = "error" if errors and not published else ("warning" if errors else "ok")
        return status, summary, findings

    # ── Core logic ────────────────────────────────────────────────────────────

    def _process_draft(self, draft: dict) -> Finding:
        """Decide la piattaforma e pubblica (o skippa) una singola bozza."""
        draft_id = draft["id"]
        content_type = draft.get("content_type", "")
        title = draft.get("title", "")
        body = draft.get("body", "")
        notes = draft.get("notes") or ""
        platform = PLATFORM_MAP.get(content_type, "skip")

        # Estrai image_url dalle notes se presente (formato: "image_url: https://...")
        image_url = self._extract_image_url(notes)

        # Skip: piattaforma non gestita
        if platform == "skip":
            log.info("social_publisher_skip", draft_id=draft_id, content_type=content_type)
            self._log_publication(draft_id, platform or "none", content_type, status="skipped")
            return Finding(
                severity="info",
                code="skipped",
                message=f"Bozza #{draft_id} \"{title[:50]}\" saltata ({content_type} non gestito da SocialPublisher).",
            )

        # Dry run
        if self._dry_run:
            log.info("social_publisher_dry_run", draft_id=draft_id, platform=platform)
            return Finding(
                severity="info",
                code="dry_run",
                message=f"[DRY RUN] Bozza #{draft_id} \"{title[:50]}\" → {platform} (non pubblicata).",
            )

        # Verifica credenziali
        if platform == "facebook" and not self._publisher.can_post_facebook:
            self._log_publication(draft_id, platform, content_type, status="skipped")
            return Finding(
                severity="warning",
                code="credentials_missing",
                message=f"Bozza #{draft_id}: FB_PAGE_ID/FB_PAGE_ACCESS_TOKEN non configurati — skip.",
            )
        if platform == "instagram" and not self._publisher.can_post_instagram:
            self._log_publication(draft_id, platform, content_type, status="skipped")
            return Finding(
                severity="warning",
                code="credentials_missing",
                message=f"Bozza #{draft_id}: IG_USER_ID/IG_ACCESS_TOKEN non configurati — skip.",
            )

        # Pubblica
        result = self._publish(platform, title, body, image_url)

        if result["ok"]:
            post_id = result.get("post_id", "")
            post_url = result.get("url", "")
            self._mark_published(draft_id)
            self._log_publication(
                draft_id, platform, content_type,
                status="ok", post_id=post_id, post_url=post_url,
            )
            return Finding(
                severity="info",
                code="published",
                message=f"✅ Bozza #{draft_id} \"{title[:50]}\" pubblicata su {platform}.",
                url=post_url,
            )
        else:
            error = result.get("error", "Errore sconosciuto")
            self._log_publication(draft_id, platform, content_type, status="error", error_message=error)
            return Finding(
                severity="error",
                code="publish_error",
                message=f"❌ Bozza #{draft_id} \"{title[:50]}\" — errore {platform}: {error}",
            )

    def _publish(self, platform: str, title: str, body: str, image_url: str | None) -> dict:
        """Chiama l'API giusta in base alla piattaforma."""
        if platform == "facebook":
            # Usa body come testo del post; aggiungi il titolo come prima riga se diverso
            message = body if body.startswith(title) else f"{title}\n\n{body}"
            # Tronca a 63.206 caratteri (limite Meta)
            return self._publisher.post_facebook(message[:63000])

        if platform == "instagram":
            caption = f"{title}\n\n{body}"[:2200]
            if not image_url:
                return {"ok": False, "error": "image_url mancante nelle notes della bozza (necessario per Instagram)."}
            return self._publisher.post_instagram(caption, image_url)

        return {"ok": False, "error": f"Piattaforma sconosciuta: {platform}"}

    def _mark_published(self, draft_id: int) -> None:
        """Aggiorna lo status della bozza a 'pubblicato'."""
        now = datetime.now().isoformat(timespec="seconds")
        with self._db.connect() as conn:
            conn.execute(
                "UPDATE drafts SET status = 'pubblicato', published_at = ? WHERE id = ?",
                (now, draft_id),
            )

    def _log_publication(
        self,
        draft_id: int,
        platform: str,
        content_type: str,
        status: str,
        post_id: str = "",
        post_url: str = "",
        error_message: str = "",
    ) -> None:
        """Inserisce un record nella tabella publication_log."""
        now = datetime.now().isoformat(timespec="seconds")
        with self._db.connect() as conn:
            conn.execute(
                """INSERT INTO publication_log
                   (draft_id, platform, content_type, platform_post_id, post_url,
                    status, error_message, published_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (draft_id, platform, content_type, post_id or None, post_url or None,
                 status, error_message or None, now),
            )

    @staticmethod
    def _extract_image_url(notes: str) -> str | None:
        """Estrae image_url dalle notes della bozza se presente.

        Formato atteso nelle notes: "image_url: https://example.com/img.jpg"
        """
        for line in notes.splitlines():
            if line.strip().startswith("image_url:"):
                url = line.split(":", 1)[1].strip()
                if url.startswith("http"):
                    return url
        return None
