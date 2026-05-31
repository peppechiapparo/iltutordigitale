"""YouTube Monitor Agent — analizza le performance del canale YouTube.

Usa la YouTube Data API v3 (chiave API semplice, no OAuth) per:
- Elencare i video pubblicati del canale
- Raccogliere statistiche (views, likes, comments, durata)
- Identificare i video con migliori performance (CTR proxy, engagement rate)
- Generare finding actionable: argomenti da replicare, topic da evitare

NOTA: La YouTube Analytics API (retention, impressions, CTR reali) richiede
OAuth2. Questo agente usa solo la Data API v3 che è accessibile con chiave API.
Le metriche CTR/retention saranno disponibili in Sprint 3 con OAuth2.

Frequenza: settimanale (mercoledì 07:30) — dopo che ci sono video pubblicati.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from ..core.db import Database
from ..core.logging import get_logger
from .base import Agent, AgentReport, Finding, Status

log = get_logger(__name__)

YT_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeMonitorAgent(Agent):
    """Monitora le performance del canale YouTube Il Tutor Digitale.

    Non usa LLM: è deterministico. Raccoglie dati via YouTube Data API v3,
    calcola metriche, genera finding strutturati.
    """

    name = "youtube_monitor"

    # Soglie per finding (calibrate per un canale in crescita)
    HIGH_VIEWS_THRESHOLD = 500       # views considerate "alto engagement" per canale nuovo
    LOW_ENGAGEMENT_THRESHOLD = 0.02  # engagement rate < 2% = warning
    HIGH_ENGAGEMENT_THRESHOLD = 0.05 # engagement rate > 5% = top content

    def __init__(
        self,
        db: Database,
        api_key: str,
        channel_id: str,
        max_results: int = 20,
    ) -> None:
        super().__init__(db)
        self._api_key = api_key
        self._channel_id = channel_id
        self._max_results = max_results

    # ── Template Method ───────────────────────────────────────────────────────

    def collect(self) -> dict:
        """Raccoglie lista video + statistiche via YouTube Data API v3."""
        if not self._api_key:
            return {"error": "YOUTUBE_API_KEY non configurata.", "videos": []}
        if not self._channel_id:
            return {"error": "YOUTUBE_CHANNEL_ID non configurato.", "videos": []}

        videos = self._fetch_channel_videos()
        return {"videos": videos, "channel_id": self._channel_id}

    def analyze(self, raw: dict) -> tuple[Status, str, list[Finding]]:
        """Analizza le statistiche e genera finding actionable."""
        if "error" in raw:
            return "warning", raw["error"], [
                Finding(severity="warning", code="config_missing", message=raw["error"])
            ]

        videos = raw.get("videos", [])
        if not videos:
            return "ok", "Nessun video pubblicato ancora.", []

        findings: list[Finding] = []
        stats = self._compute_stats(videos)

        # 1. Top performer — da replicare
        for v in stats["top_videos"]:
            findings.append(Finding(
                severity="info",
                code="top_content",
                message=(
                    f"Top video: \"{v['title']}\" — "
                    f"{v['views']:,} views, engagement {v['engagement_rate']:.1%}. "
                    f"Proponi variante su stesso argomento."
                ),
                url=f"https://youtube.com/watch?v={v['id']}",
            ))

        # 2. Video con alto engagement rate
        for v in stats["high_engagement"]:
            findings.append(Finding(
                severity="info",
                code="high_engagement",
                message=(
                    f"Alto engagement: \"{v['title']}\" — "
                    f"{v['engagement_rate']:.1%} (commenti+like/views). "
                    f"Il pubblico vuole più contenuti su questo tema."
                ),
                url=f"https://youtube.com/watch?v={v['id']}",
            ))

        # 3. Video con basso engagement (possibili problemi di targeting)
        for v in stats["low_engagement"]:
            findings.append(Finding(
                severity="warning",
                code="low_engagement",
                message=(
                    f"Basso engagement: \"{v['title']}\" — "
                    f"{v['engagement_rate']:.1%}. "
                    f"Rivedi titolo/thumbnail o cambia approccio su questo tema."
                ),
                url=f"https://youtube.com/watch?v={v['id']}",
            ))

        # 4. Video recente (< 7gg) con views basse
        for v in stats["recent_low_views"]:
            findings.append(Finding(
                severity="warning",
                code="recent_low_views",
                message=(
                    f"Video recente con poche views: \"{v['title']}\" — "
                    f"{v['views']:,} views. "
                    f"Considera di condividerlo sui social / newsletter."
                ),
                url=f"https://youtube.com/watch?v={v['id']}",
            ))

        # Summary
        total_views = sum(v.get("views", 0) for v in videos)
        total_videos = len(videos)
        summary = (
            f"📺 Canale: {total_videos} video, {total_views:,} views totali. "
            f"Top: \"{stats['top_videos'][0]['title'][:40]}...\" "
            f"({stats['top_videos'][0]['views']:,} views)" if stats["top_videos"]
            else f"📺 Canale: {total_videos} video, {total_views:,} views totali."
        )

        status: Status = "warning" if any(f.severity == "warning" for f in findings) else "ok"
        return status, summary, findings

    # ── YouTube Data API v3 ───────────────────────────────────────────────────

    def _fetch_channel_videos(self) -> list[dict]:
        """Recupera lista video del canale con statistiche."""
        # Step 1: ottieni la playlist "uploads" del canale
        uploads_playlist_id = self._get_uploads_playlist_id()
        if not uploads_playlist_id:
            return []

        # Step 2: lista video dalla playlist
        video_ids = self._get_playlist_video_ids(uploads_playlist_id)
        if not video_ids:
            return []

        # Step 3: statistiche dettagliate per ogni video
        return self._get_videos_statistics(video_ids)

    def _get_uploads_playlist_id(self) -> str | None:
        """Recupera l'ID della playlist 'uploads' dal canale."""
        try:
            r = httpx.get(
                f"{YT_API_BASE}/channels",
                params={
                    "key": self._api_key,
                    "id": self._channel_id,
                    "part": "contentDetails",
                },
                timeout=15,
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            if not items:
                log.warning("youtube_channel_not_found", channel_id=self._channel_id)
                return None
            return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except httpx.HTTPError as exc:
            log.error("youtube_api_error", endpoint="channels", error=str(exc))
            return None

    def _get_playlist_video_ids(self, playlist_id: str) -> list[str]:
        """Recupera gli ID dei video dalla playlist uploads."""
        video_ids: list[str] = []
        next_page_token = None

        while len(video_ids) < self._max_results:
            params: dict = {
                "key": self._api_key,
                "playlistId": playlist_id,
                "part": "contentDetails",
                "maxResults": min(50, self._max_results - len(video_ids)),
            }
            if next_page_token:
                params["pageToken"] = next_page_token

            try:
                r = httpx.get(f"{YT_API_BASE}/playlistItems", params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
            except httpx.HTTPError as exc:
                log.error("youtube_api_error", endpoint="playlistItems", error=str(exc))
                break

            for item in data.get("items", []):
                vid_id = item.get("contentDetails", {}).get("videoId")
                if vid_id:
                    video_ids.append(vid_id)

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        return video_ids

    def _get_videos_statistics(self, video_ids: list[str]) -> list[dict]:
        """Recupera titolo, stats e snippet per lista di video IDs."""
        results: list[dict] = []

        # YouTube API: max 50 IDs per richiesta
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i + 50]
            try:
                r = httpx.get(
                    f"{YT_API_BASE}/videos",
                    params={
                        "key": self._api_key,
                        "id": ",".join(chunk),
                        "part": "snippet,statistics,contentDetails",
                    },
                    timeout=15,
                )
                r.raise_for_status()
                items = r.json().get("items", [])
            except httpx.HTTPError as exc:
                log.error("youtube_api_error", endpoint="videos", error=str(exc))
                continue

            for item in items:
                stats = item.get("statistics", {})
                snippet = item.get("snippet", {})
                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))
                engagement_rate = (likes + comments) / views if views > 0 else 0.0

                results.append({
                    "id": item["id"],
                    "title": snippet.get("title", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagement_rate": engagement_rate,
                    "duration": item.get("contentDetails", {}).get("duration", ""),
                    "tags": snippet.get("tags", []),
                })

        return results

    # ── Stats computation ─────────────────────────────────────────────────────

    def _compute_stats(self, videos: list[dict]) -> dict:
        """Calcola statistiche aggregate e identifica top/low performer."""
        from datetime import date, timedelta
        cutoff_recent = (date.today() - timedelta(days=7)).isoformat()

        sorted_by_views = sorted(videos, key=lambda v: v["views"], reverse=True)
        top_n = min(3, len(sorted_by_views))
        top_videos = sorted_by_views[:top_n]

        high_engagement = [
            v for v in videos
            if v["engagement_rate"] >= self.HIGH_ENGAGEMENT_THRESHOLD
            and v not in top_videos
        ][:3]

        low_engagement = [
            v for v in videos
            if v["engagement_rate"] < self.LOW_ENGAGEMENT_THRESHOLD
            and v["views"] >= 50  # almeno qualche view
        ][:3]

        recent_low_views = [
            v for v in videos
            if v.get("published_at", "") >= cutoff_recent
            and v["views"] < self.HIGH_VIEWS_THRESHOLD
        ][:2]

        return {
            "top_videos": top_videos,
            "high_engagement": high_engagement,
            "low_engagement": low_engagement,
            "recent_low_views": recent_low_views,
        }

    @classmethod
    def resolve_channel_id(cls, api_key: str, handle: str) -> str | None:
        """Risolve un handle (@iltutordigitale) nel Channel ID numerico.

        Chiama questo metodo una volta sola per ottenere il channel ID
        e salvarlo in YOUTUBE_CHANNEL_ID.
        """
        clean_handle = handle.lstrip("@")
        try:
            r = httpx.get(
                f"{YT_API_BASE}/channels",
                params={
                    "key": api_key,
                    "forHandle": clean_handle,
                    "part": "id,snippet",
                },
                timeout=15,
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            if items:
                cid = items[0]["id"]
                title = items[0]["snippet"]["title"]
                log.info("youtube_channel_resolved", handle=clean_handle, channel_id=cid, title=title)
                return cid
            log.warning("youtube_handle_not_found", handle=clean_handle)
            return None
        except httpx.HTTPError as exc:
            log.error("youtube_resolve_error", error=str(exc))
            return None
