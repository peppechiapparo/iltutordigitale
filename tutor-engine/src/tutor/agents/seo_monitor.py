"""SEO Monitor Agent — LLM-powered with ReAct tool_use loop.

The LLM autonomously decides which tools to call, in what order,
and produces a structured list of SEO findings.
"""

from __future__ import annotations

from typing import Any

from ..core.db import Database
from ..core.logging import get_logger
from ..tools.web_tools import TOOLS
from .base import LLMAgent

log = get_logger(__name__)

SEO_SYSTEM_PROMPT = """\
You are an expert SEO auditor. Your task is to perform a comprehensive SEO health check
on a website using the available tools.

## What to check (use the tools to verify each point):

1. **Reachability** — fetch the homepage (HTTP 200? fast redirect?)
2. **TLS/HTTPS** — check certificate validity and days remaining
3. **robots.txt** — present? allows crawling? (Disallow: / for * means blocked)
4. **sitemap.xml** — present? has URLs?
5. **HTML meta tags** — <title> (30-65 chars), <meta description> (70-160 chars)
6. **H1 tag** — exactly one H1 present on homepage
7. **Canonical URL** — <link rel=canonical> present?
8. **Structured data** — JSON-LD present (WebSite, Person, Article, FAQPage, HowTo)?
9. **Open Graph** — og:title, og:description, og:image present?
10. **Social links** — YouTube (youtube.com/@iltutordigitale), Instagram, Facebook links present?
11. **AEO signals** — FAQ sections, "In breve" answer boxes, HowTo schema present?
12. **Accessibility** — html lang="it", viewport meta, font-size hints in CSS

## SEO severity guidelines:
- **critical**: site unreachable, TLS expired, robots blocks all crawlers
- **error**: missing canonical, missing JSON-LD, HTTP 4xx/5xx, missing og:image
- **warning**: title/meta length out of range, missing H1, missing social links,
  TLS expires in < 30 days, missing AEO signals (FAQ, HowTo schema)
- **info**: minor recommendations (optional improvements)

## Instructions:
1. Start by fetching the homepage.
2. Extract SEO/AEO metadata from the HTML.
3. Then check TLS, robots.txt, sitemap.xml.
4. Reason about what you found. Apply the severity guidelines.
5. When you have completed all checks, call `report_findings` with your complete list.
   If there are no issues, call `report_findings` with an empty list.
6. Do NOT make up findings — only report what the tools confirmed.
"""


class SEOMonitorAgent(LLMAgent):
    name = "seo_monitor"

    def __init__(
        self,
        db: Database,
        llm: Any,
        site_url: str,
        instagram_handle: str,
        extra_paths: list[str] | None = None,
    ) -> None:
        super().__init__(db, llm)
        self._site_url = site_url.rstrip("/") + "/"
        self._instagram_handle = instagram_handle.lower().lstrip("@")
        self._extra_paths = extra_paths or []

    def collect(self) -> dict:
        """Collect initial context — the LLM will drive the actual fetching via tools."""
        return {
            "site_url": self._site_url,
            "instagram_handle": self._instagram_handle,
        }

    def build_system_prompt(self, context: dict) -> str:
        ig_handle = context.get("instagram_handle", "iltutordigitale")
        return SEO_SYSTEM_PROMPT.replace(
            "instagram.com/iltutordigitale",
            f"instagram.com/{ig_handle}",
        )

    def get_tools(self) -> list[dict]:
        return TOOLS
