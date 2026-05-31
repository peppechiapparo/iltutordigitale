"""Tool definitions and implementations for web/SEO agents.

Each tool is:
  - A JSON schema (for Anthropic tool_use API)
  - A Python implementation (callable)
"""

from __future__ import annotations

import json
import socket
import ssl
from collections.abc import Callable
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse  # noqa: F401

import httpx
from bs4 import BeautifulSoup

from ..core.logging import get_logger

log = get_logger(__name__)

USER_AGENT = "ShanGrowthAgent/0.1 (+https://www.scuolakungfucipriani.it)"
HTTP_TIMEOUT = 15.0

# --- Tool JSON schemas (Anthropic format) ---

TOOLS: list[dict] = [
    {
        "name": "fetch_url",
        "description": (
            "Fetch a URL over HTTP/HTTPS. Returns HTTP status code, response text (HTML/plain), "
            "and key response headers. Use this to retrieve any page, robots.txt, sitemap.xml, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The full URL to fetch (must include scheme)"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "extract_seo_meta",
        "description": (
            "Parse HTML and extract SEO metadata: <title>, <meta name=description>, all <h1>-<h2> tags, "
            "<link rel=canonical>, Open Graph tags, JSON-LD scripts, all <a> anchor hrefs. "
            "Pass the raw HTML obtained from fetch_url."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "html": {"type": "string", "description": "Raw HTML string to parse"},
                "base_url": {"type": "string", "description": "Base URL for resolving relative links"},
            },
            "required": ["html"],
        },
    },
    {
        "name": "check_tls",
        "description": (
            "Verify TLS certificate for a hostname: check validity, days remaining until expiry, and issuer. "
            "Pass just the domain name (e.g. 'www.scuolakungfucipriani.it'), not the full URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain name to check (no scheme, no path)"},
            },
            "required": ["domain"],
        },
    },
    {
        "name": "check_sitemap",
        "description": (
            "Fetch and parse a sitemap.xml file. Returns whether it exists, the number of <url> entries, "
            "and a sample of up to 5 URLs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to the sitemap (e.g. https://domain/sitemap.xml)"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "report_findings",
        "description": (
            "Submit the final list of SEO findings and end the audit. "
            "Call this ONCE when you have completed all checks. "
            "Each finding must have: severity ('info'|'warning'|'error'|'critical'), "
            "code (dot.notation string like 'seo.title_too_long'), "
            "message (human-readable explanation). "
            "If everything is OK, pass an empty list."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "severity": {"type": "string", "enum": ["info", "warning", "error", "critical"]},
                            "code": {"type": "string"},
                            "message": {"type": "string"},
                            "url": {"type": "string"},
                        },
                        "required": ["severity", "code", "message"],
                    },
                    "description": "List of findings. Empty list means no issues found.",
                }
            },
            "required": ["findings"],
        },
    },
]

# --- Python implementations ---


def tool_fetch_url(url: str) -> dict:
    """Fetch URL and return structured result."""
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            r = client.get(url)
            ct = r.headers.get("content-type", "")
            is_text = "text" in ct or url.endswith((".txt", ".xml", ".html"))
            return {
                "ok": r.status_code < 400,
                "status_code": r.status_code,
                "final_url": str(r.url),
                "content_type": ct,
                "bytes": len(r.content),
                "text": r.text if is_text else f"[binary content, {len(r.content)} bytes]",
                "headers": dict(r.headers),
            }
    except httpx.HTTPError as exc:
        return {"ok": False, "status_code": 0, "error": str(exc), "text": "", "final_url": url}


def tool_extract_seo_meta(html: str, base_url: str = "") -> dict:  # noqa: ARG001
    """Parse HTML and extract SEO metadata."""
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.title
    title = (title_tag.string or "").strip() if title_tag and title_tag.string else ""

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href", "") if canonical_tag else ""

    og_tags = {
        tag.get("property", ""): tag.get("content", "")
        for tag in soup.find_all("meta", property=lambda p: p and p.startswith("og:"))
    }

    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]

    json_ld = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            json_ld.append(json.loads(script.string or "{}"))
        except (json.JSONDecodeError, TypeError):
            pass

    all_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    social_links = [
        href for href in all_links
        if any(s in href for s in ("instagram.com", "facebook.com", "youtube.com", "tiktok.com"))
    ]

    return {
        "title": title,
        "title_length": len(title),
        "meta_description": meta_desc,
        "meta_description_length": len(meta_desc),
        "canonical": canonical,
        "h1_tags": h1s,
        "h1_count": len(h1s),
        "h2_tags": h2s[:5],
        "h2_count": len(h2s),
        "open_graph": og_tags,
        "json_ld_schemas": [ld.get("@type", "unknown") for ld in json_ld],
        "json_ld_count": len(json_ld),
        "social_links": social_links,
        "total_links": len(all_links),
    }


def tool_check_tls(domain: str) -> dict:
    """Check TLS certificate."""
    # NOSONAR: create_default_context() is the recommended secure-by-default API.
    ctx = ssl.create_default_context()
    try:
        with (
            socket.create_connection((domain, 443), timeout=HTTP_TIMEOUT) as sock,
            ctx.wrap_socket(sock, server_hostname=domain) as ssock,
        ):
            cert = ssock.getpeercert()
    except OSError as exc:
        return {"ok": False, "error": str(exc)}

    not_after = cert.get("notAfter", "")
    try:
        expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        return {"ok": False, "error": f"cannot parse notAfter: {not_after}"}

    days_left = (expires - datetime.now(timezone.utc)).days
    issuer = {k: v for x in cert.get("issuer", []) for k, v in x}
    return {
        "ok": True,
        "valid": days_left > 0,
        "days_remaining": days_left,
        "expires_at": expires.isoformat(),
        "issuer": issuer.get("organizationName", issuer.get("commonName", "unknown")),
    }


def tool_check_sitemap(url: str) -> dict:
    """Fetch and parse sitemap."""
    result = tool_fetch_url(url)
    if not result.get("ok"):
        return {"present": False, "error": result.get("error", f"HTTP {result.get('status_code')}")}

    soup = BeautifulSoup(result.get("text", ""), "lxml-xml")
    urls = [loc.get_text(strip=True) for loc in soup.find_all("loc")]
    return {
        "present": True,
        "url_count": len(urls),
        "sample_urls": urls[:5],
    }


# Tool dispatch table
TOOL_DISPATCH: dict[str, Callable[..., dict]] = {
    "fetch_url": lambda args: tool_fetch_url(**args),
    "extract_seo_meta": lambda args: tool_extract_seo_meta(**args),
    "check_tls": lambda args: tool_check_tls(**args),
    "check_sitemap": lambda args: tool_check_sitemap(**args),
    # report_findings is handled by the agent loop, not dispatched here
}
