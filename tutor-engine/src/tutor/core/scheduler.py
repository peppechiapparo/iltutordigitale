"""APScheduler-based job orchestrator (Factory + DI).

Schedules:
- seo_monitor:      giornaliero alle 07:00 (Europe/Rome)
- calendar_agent:   ogni lunedì alle 06:30 (propone calendario settimana successiva)
- trend_agent:      ogni 4 ore (Google Trends IT → EventBus trend.found)
- social_publisher: ogni 30 minuti (fallback pubblicazione bozze approvate)
- weekly_report:    domenica 18:00 (metriche + opportunity keyword GSC)
- youtube_monitor:  mercoledì 07:30 (quando il canale è attivo)
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import Settings
from .db import Database
from .events import EventBus
from .logging import get_logger
from ..adapters.notifier import Notifier
from ..adapters.meta_publisher import MetaPublisher
from ..agents.base import Agent, AgentReport
from ..agents.seo_monitor import SEOMonitorAgent
from ..agents.calendar_agent import CalendarAgent
from ..agents.content_agent import ContentAgent
from ..agents.weekly_report import WeeklyReportAgent
from ..agents.youtube_monitor import YouTubeMonitorAgent
from ..agents.trend_agent import TrendResearchAgent
from ..agents.social_publisher import SocialPublisherAgent
from ..adapters.llm import LLMClient

log = get_logger(__name__)


def _format_report_for_telegram(r: AgentReport) -> tuple[str, str]:
    subject = f"[{r.status.upper()}] {r.agent}"
    lines = [r.summary, ""]
    # Only include alert-level findings to keep messages short
    alerts = [f for f in r.findings if f.severity in ("critical", "error", "warning")]
    if not alerts:
        lines.append("Nessun problema rilevato.")
    else:
        for f in alerts[:15]:
            lines.append(f"• [{f.severity}] {f.code}: {f.message}")
        if len(alerts) > 15:
            lines.append(f"…e altri {len(alerts) - 15}.")
    return subject, "\n".join(lines)


def _run_agent_and_notify(agent: Agent, notifier: Notifier, notify_on_ok: bool = False) -> None:
    report = agent.run()
    if report.status != "ok" or notify_on_ok:
        subject, body = _format_report_for_telegram(report)
        notifier.send(subject, body)


def _run_calendar_agent(agent: CalendarAgent, notifier: Notifier) -> None:
    """Esegue il CalendarAgent e invia il riepilogo su Telegram per approvazione."""
    report = agent.run()
    subject = f"📅 Calendario proposto — {report.status.upper()}"
    notifier.send(subject, report.summary)


def build_scheduler(
    settings: Settings,
    db: Database,
    notifier: Notifier,
    llm: LLMClient,
    bus: "EventBus | None" = None,
    publisher: "MetaPublisher | None" = None,
) -> BackgroundScheduler:
    """Factory — builds an APScheduler with all jobs wired and ready to start."""
    sched = BackgroundScheduler(timezone=settings.tutor_timezone)

    # ── SEO Monitor: giornaliero alle 07:00 ───────────────────────────────────
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

    # ── Calendar Agent: ogni lunedì alle 06:30 ────────────────────────────────
    calendar_agent = CalendarAgent(db=db, llm=llm)
    sched.add_job(
        _run_calendar_agent,
        trigger=CronTrigger(day_of_week="mon", hour=6, minute=30),
        kwargs={"agent": calendar_agent, "notifier": notifier},
        id="calendar_agent_weekly",
        name="Calendar Agent (Monday 06:30)",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    # ── Weekly Report: ogni domenica alle 18:00 ──────────────────────────────
    weekly_agent = WeeklyReportAgent(db=db, llm=llm)
    sched.add_job(
        _run_agent_and_notify,
        trigger=CronTrigger(day_of_week="sun", hour=18, minute=0),
        kwargs={"agent": weekly_agent, "notifier": notifier, "notify_on_ok": True},
        id="weekly_report_sunday",
        name="Weekly Report (Sunday 18:00)",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    # ── YouTube Monitor: mercoledì 07:30 (solo se canale attivo) ──────────────
    if settings.youtube_api_key and settings.youtube_channel_id:
        yt_agent = YouTubeMonitorAgent(
            db=db,
            api_key=settings.youtube_api_key,
            channel_id=settings.youtube_channel_id,
        )
        sched.add_job(
            _run_agent_and_notify,
            trigger=CronTrigger(day_of_week="wed", hour=7, minute=30),
            kwargs={"agent": yt_agent, "notifier": notifier},
            id="youtube_monitor_weekly",
            name="YouTube Monitor (Wednesday 07:30)",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        log.info("youtube_monitor_scheduled")
    else:
        log.info("youtube_monitor_skipped", reason="YOUTUBE_API_KEY or YOUTUBE_CHANNEL_ID not set")

    # ── Trend Agent: ogni 4 ore ────────────────────────────────────────────────
    trend_agent = TrendResearchAgent(db=db, bus=bus)
    sched.add_job(
        _run_agent_and_notify,
        trigger=IntervalTrigger(hours=4),
        kwargs={"agent": trend_agent, "notifier": notifier, "notify_on_ok": True},
        id="trend_agent_4h",
        name="Trend Research Agent (ogni 4 ore)",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    # ── Social Publisher: ogni 30 minuti (fallback per bozze arretrate) ────────
    if publisher:
        pub_agent = SocialPublisherAgent(db=db, publisher=publisher, dry_run=False)
        sched.add_job(
            _run_agent_and_notify,
            trigger=IntervalTrigger(minutes=30),
            kwargs={"agent": pub_agent, "notifier": notifier},
            id="social_publisher_30m",
            name="Social Publisher (fallback ogni 30 min)",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
    else:
        log.info("social_publisher_skipped", reason="publisher non configurato")

    log.info("scheduler_built", jobs=[j.id for j in sched.get_jobs()])
    return sched
