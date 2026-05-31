"""APScheduler-based job orchestrator (Factory + DI).

Schedules:
- seo_monitor: daily at 07:00 local time
Future:
- content_growth (weekly)
- instagram_bridge (daily morning)
- weekly_report (Sunday 18:00)
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Settings
from .db import Database
from .logging import get_logger
from ..adapters.notifier import Notifier
from ..agents.base import Agent, AgentReport
from ..agents.seo_monitor import SEOMonitorAgent
from ..adapters.llm import LLMClient

log = get_logger(__name__)


def _format_report_for_telegram(r: AgentReport) -> tuple[str, str]:
    subject = f"[{r.status.upper()}] {r.agent}"
    lines = [r.summary, ""]
    # Only include alert-level findings to keep messages short
    alerts = [f for f in r.findings if f.severity in ("critical", "error", "warning")]
    if not alerts:
        lines.append("No alerts.")
    else:
        for f in alerts[:15]:
            lines.append(f"• [{f.severity}] {f.code}: {f.message}")
        if len(alerts) > 15:
            lines.append(f"…and {len(alerts) - 15} more.")
    return subject, "\n".join(lines)


def _run_agent_and_notify(agent: Agent, notifier: Notifier, notify_on_ok: bool = False) -> None:
    report = agent.run()
    if report.status != "ok" or notify_on_ok:
        subject, body = _format_report_for_telegram(report)
        notifier.send(subject, body)


def build_scheduler(settings: Settings, db: Database, notifier: Notifier, llm: LLMClient) -> BackgroundScheduler:
    """Factory — builds an APScheduler with all jobs wired and ready to start."""
    sched = BackgroundScheduler(timezone=settings.shan_timezone)

    seo_agent = SEOMonitorAgent(
        db=db,
        llm=llm,
        site_url=settings.site_url,
        instagram_handle=settings.site_instagram_handle,
    )

    sched.add_job(
        _run_agent_and_notify,
        trigger=CronTrigger(hour=7, minute=0),
        kwargs={"agent": seo_agent, "notifier": notifier},
        id="seo_monitor_daily",
        name="SEO Monitor (daily 07:00)",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    log.info("scheduler_built", jobs=[j.id for j in sched.get_jobs()])
    return sched
