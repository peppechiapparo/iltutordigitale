"""Meta Graph API adapter — Facebook Page post + Instagram image/caption post.

Supporta:
- Facebook Page: POST /{page-id}/feed  (testo + link opzionale)
- Instagram: POST /{ig-user-id}/media → media_publish  (caption + image_url)

Ogni metodo ritorna un dict con:
  {"ok": True, "post_id": "...", "url": "..."}  — successo
  {"ok": False, "error": "..."}                   — errore

Documentazione:
  https://developers.facebook.com/docs/pages/publishing
  https://developers.facebook.com/docs/instagram-api/guides/content-publishing
"""

from __future__ import annotations

import httpx

from ..core.logging import get_logger

log = get_logger(__name__)

META_GRAPH_BASE = "https://graph.facebook.com/v19.0"
# Timeout per richieste Meta API (risponde di solito in < 3s)
_TIMEOUT = 20.0


class MetaPublisher:
    """Adapter per pubblicare su Facebook Page e Instagram via Meta Graph API."""

    def __init__(
        self,
        fb_page_id: str,
        fb_page_access_token: str,
        ig_user_id: str,
        ig_access_token: str,
    ) -> None:
        self._fb_page_id = fb_page_id
        self._fb_page_access_token = fb_page_access_token
        self._ig_user_id = ig_user_id
        self._ig_access_token = ig_access_token

    # ── Facebook ─────────────────────────────────────────────────────────────

    def post_facebook(
        self,
        message: str,
        link: str | None = None,
    ) -> dict:
        """Pubblica un post testuale sulla Page Facebook.

        Args:
            message: Testo del post (fino a ~63.206 caratteri).
            link: URL opzionale da allegare come anteprima.

        Returns:
            {"ok": True, "post_id": "...", "url": "..."}
            {"ok": False, "error": "..."}
        """
        if not self._fb_page_id or not self._fb_page_access_token:
            return {"ok": False, "error": "FB_PAGE_ID o FB_PAGE_ACCESS_TOKEN non configurati."}

        payload: dict = {
            "message": message,
            "access_token": self._fb_page_access_token,
        }
        if link:
            payload["link"] = link

        try:
            r = httpx.post(
                f"{META_GRAPH_BASE}/{self._fb_page_id}/feed",
                json=payload,
                timeout=_TIMEOUT,
            )
            data = r.json()
            if r.is_success and "id" in data:
                post_id = data["id"]
                url = f"https://www.facebook.com/{post_id.replace('_', '/posts/')}"
                log.info("facebook_published", post_id=post_id)
                return {"ok": True, "post_id": post_id, "url": url}
            error = data.get("error", {}).get("message", r.text[:200])
            log.warning("facebook_publish_failed", error=error)
            return {"ok": False, "error": error}
        except httpx.HTTPError as exc:
            log.error("facebook_http_error", error=str(exc))
            return {"ok": False, "error": str(exc)}

    # ── Instagram ─────────────────────────────────────────────────────────────

    def post_instagram(
        self,
        caption: str,
        image_url: str,
    ) -> dict:
        """Pubblica un post immagine su Instagram.

        Processo in 2 step (Media Container → Publish):
        1. Crea container: POST /{ig-user-id}/media
        2. Pubblica: POST /{ig-user-id}/media_publish

        Args:
            caption: Didascalia del post (fino a 2.200 caratteri).
            image_url: URL pubblico dell'immagine (JPEG/PNG, ratio 1.91:1 → 4:5).
                       Deve essere accessibile da internet (non localhost).

        Returns:
            {"ok": True, "post_id": "...", "url": "..."}
            {"ok": False, "error": "..."}
        """
        if not self._ig_user_id or not self._ig_access_token:
            return {"ok": False, "error": "IG_USER_ID o IG_ACCESS_TOKEN non configurati."}

        # Step 1: crea media container
        container_id = self._create_ig_container(caption, image_url)
        if not container_id:
            return {"ok": False, "error": "Impossibile creare media container Instagram."}

        # Step 2: pubblica il container
        return self._publish_ig_container(container_id)

    def _create_ig_container(self, caption: str, image_url: str) -> str | None:
        """Crea un media container Instagram. Ritorna l'ID o None."""
        try:
            r = httpx.post(
                f"{META_GRAPH_BASE}/{self._ig_user_id}/media",
                json={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self._ig_access_token,
                },
                timeout=_TIMEOUT,
            )
            data = r.json()
            if r.is_success and "id" in data:
                log.info("ig_container_created", container_id=data["id"])
                return data["id"]
            error = data.get("error", {}).get("message", r.text[:200])
            log.warning("ig_container_failed", error=error)
            return None
        except httpx.HTTPError as exc:
            log.error("ig_container_http_error", error=str(exc))
            return None

    def _publish_ig_container(self, container_id: str) -> dict:
        """Pubblica un container Instagram già creato."""
        try:
            r = httpx.post(
                f"{META_GRAPH_BASE}/{self._ig_user_id}/media_publish",
                json={
                    "creation_id": container_id,
                    "access_token": self._ig_access_token,
                },
                timeout=_TIMEOUT,
            )
            data = r.json()
            if r.is_success and "id" in data:
                post_id = data["id"]
                url = f"https://www.instagram.com/p/{post_id}/"
                log.info("ig_published", post_id=post_id)
                return {"ok": True, "post_id": post_id, "url": url}
            error = data.get("error", {}).get("message", r.text[:200])
            log.warning("ig_publish_failed", error=error)
            return {"ok": False, "error": error}
        except httpx.HTTPError as exc:
            log.error("ig_publish_http_error", error=str(exc))
            return {"ok": False, "error": str(exc)}

    # ── Capability check ──────────────────────────────────────────────────────

    @property
    def can_post_facebook(self) -> bool:
        return bool(self._fb_page_id and self._fb_page_access_token)

    @property
    def can_post_instagram(self) -> bool:
        return bool(self._ig_user_id and self._ig_access_token)


class NullMetaPublisher:
    """No-op publisher usato in assenza di credenziali o in test."""

    can_post_facebook = False
    can_post_instagram = False

    def post_facebook(self, message: str, link: str | None = None) -> dict:
        log.info("null_publisher_facebook_skip")
        return {"ok": False, "error": "NullMetaPublisher: credenziali non configurate."}

    def post_instagram(self, caption: str, image_url: str) -> dict:
        log.info("null_publisher_instagram_skip")
        return {"ok": False, "error": "NullMetaPublisher: credenziali non configurate."}


def build_meta_publisher(
    fb_page_id: str,
    fb_page_access_token: str,
    ig_user_id: str,
    ig_access_token: str,
) -> MetaPublisher | NullMetaPublisher:
    """Factory: ritorna MetaPublisher se almeno una credenziale è configurata."""
    has_fb = bool(fb_page_id and fb_page_access_token)
    has_ig = bool(ig_user_id and ig_access_token)
    if has_fb or has_ig:
        return MetaPublisher(fb_page_id, fb_page_access_token, ig_user_id, ig_access_token)
    return NullMetaPublisher()
