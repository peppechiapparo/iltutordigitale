"""Command-line entrypoint: `tutor <subcommand>`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .adapters.notifier import build_notifier
from .agents.seo_monitor import SEOMonitorAgent
from .agents.calendar_agent import CalendarAgent
from .agents.content_agent import ContentAgent
from .agents.weekly_report import WeeklyReportAgent
from .agents.youtube_monitor import YouTubeMonitorAgent
from .agents.social_publisher import SocialPublisherAgent
from .adapters.meta_publisher import build_meta_publisher
from .core.config import get_settings
from .core.db import Database
from .core.logging import configure_logging, get_logger

_src_migrations = Path(__file__).resolve().parents[2] / "migrations"
MIGRATIONS_DIR = _src_migrations if _src_migrations.exists() else Path("/app/migrations")

log = get_logger(__name__)


def cmd_run_seo(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    db = Database(settings.db_path, MIGRATIONS_DIR)
    db.init()

    agent = SEOMonitorAgent(db, settings.site_url, settings.site_instagram_handle)
    report = agent.run()

    payload = {
        "agent": report.agent,
        "status": report.status,
        "summary": report.summary,
        "findings": [
            {"severity": f.severity, "code": f.code, "message": f.message, "url": f.url}
            for f in report.findings
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.notify:
        notifier = build_notifier(settings.telegram_bot_token, settings.telegram_chat_id)
        subject = f"[{report.status.upper()}] {report.agent} (manual)"
        notifier.send(subject, report.summary)

    return 0 if report.status in ("ok", "warning") else 1


def cmd_run_calendar(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    db = Database(settings.db_path, MIGRATIONS_DIR)
    db.init()

    from .adapters.llm import build_llm_client
    llm = build_llm_client(
        settings.llm_provider,
        settings.anthropic_api_key,
        settings.anthropic_model,
        settings.openai_api_key,
        settings.openai_model,
        settings.github_token,
        settings.github_model,
    )
    agent = CalendarAgent(db, llm)
    report = agent.run()
    print(report.summary)

    if args.notify:
        notifier = build_notifier(settings.telegram_bot_token, settings.telegram_chat_id)
        notifier.send(f"[{report.status.upper()}] {report.agent}", report.summary)

    return 0 if report.status in ("ok", "warning") else 1


def cmd_run_content(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    db = Database(settings.db_path, MIGRATIONS_DIR)
    db.init()

    from .adapters.llm import build_llm_client
    llm = build_llm_client(
        settings.llm_provider,
        settings.anthropic_api_key,
        settings.anthropic_model,
        settings.openai_api_key,
        settings.openai_model,
        settings.github_token,
        settings.github_model,
    )
    calendar_id = getattr(args, "calendar_id", None)
    agent = ContentAgent(db, llm, calendar_id=calendar_id)
    report = agent.run()
    print(report.summary)

    if args.notify:
        notifier = build_notifier(settings.telegram_bot_token, settings.telegram_chat_id)
        notifier.send_with_approval(
            f"[{report.status.upper()}] {report.agent}",
            report.summary,
            ref_table="drafts",
            ref_id=0,  # il draft ID è nel summary
        )
    return 0 if report.status in ("ok", "warning") else 1


def cmd_weekly_report(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    db = Database(settings.db_path, MIGRATIONS_DIR)
    db.init()

    from .adapters.llm import build_llm_client
    llm = build_llm_client(
        settings.llm_provider,
        settings.anthropic_api_key,
        settings.anthropic_model,
        settings.openai_api_key,
        settings.openai_model,
        settings.github_token,
        settings.github_model,
    )
    agent = WeeklyReportAgent(db, llm)
    report = agent.run()
    print(report.summary)

    if args.notify:
        notifier = build_notifier(settings.telegram_bot_token, settings.telegram_chat_id)
        notifier.send(f"[{report.status.upper()}] {report.agent}", report.summary)
    return 0 if report.status in ("ok", "warning") else 1


def cmd_youtube(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    db = Database(settings.db_path, MIGRATIONS_DIR)
    db.init()

    if not settings.youtube_api_key:
        print("⚠️  YOUTUBE_API_KEY non configurata. Aggiungila nel .env.")
        return 1
    if not settings.youtube_channel_id:
        print("⚠️  YOUTUBE_CHANNEL_ID non configurato. Usa: tutor resolve-channel-id")
        return 1

    agent = YouTubeMonitorAgent(db, settings.youtube_api_key, settings.youtube_channel_id)
    report = agent.run()
    print(report.summary)
    for f in report.findings:
        print(f"  [{f.severity}] {f.code}: {f.message}")

    if args.notify:
        notifier = build_notifier(settings.telegram_bot_token, settings.telegram_chat_id)
        from .core.scheduler import _format_report_for_telegram
        subject, body = _format_report_for_telegram(report)
        notifier.send(subject, body)
    return 0 if report.status in ("ok", "warning") else 1


def cmd_resolve_channel_id(args: argparse.Namespace) -> int:
    settings = get_settings()
    handle = getattr(args, "handle", None) or settings.youtube_channel_handle
    if not settings.youtube_api_key:
        print("⚠️  YOUTUBE_API_KEY non configurata.")
        return 1
    channel_id = YouTubeMonitorAgent.resolve_channel_id(settings.youtube_api_key, handle)
    if channel_id:
        print(f"✅ Channel ID per @{handle}: {channel_id}")
        print(f"   → Aggiungi nel .env: YOUTUBE_CHANNEL_ID={channel_id}")
    else:
        print(f"⚠️  Impossibile risolvere @{handle}. Verifica il handle e la API key.")
    return 0 if channel_id else 1


def cmd_publish(args: argparse.Namespace) -> int:
    settings = get_settings()
    settings.ensure_dirs()
    db = Database(settings.db_path, MIGRATIONS_DIR)
    db.init()

    publisher = build_meta_publisher(
        settings.fb_page_id,
        settings.fb_page_access_token,
        settings.ig_user_id,
        settings.ig_access_token,
    )
    dry_run = getattr(args, "dry_run", False)
    agent = SocialPublisherAgent(db, publisher, dry_run=dry_run)
    report = agent.run()
    print(report.summary)
    for f in report.findings:
        icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🔴"}.get(f.severity, "•")
        print(f"  {icon} [{f.code}] {f.message}")
        if f.url:
            print(f"      → {f.url}")

    if args.notify:
        notifier = build_notifier(settings.telegram_bot_token, settings.telegram_chat_id)
        from .core.scheduler import _format_report_for_telegram
        subject, body = _format_report_for_telegram(report)
        notifier.send(subject, body)
    return 0 if report.status in ("ok", "warning") else 1


def cmd_serve(_: argparse.Namespace) -> int:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "tutor.api.main:app",
        host=settings.tutor_api_host,
        port=settings.tutor_api_port,
        log_level=settings.tutor_log_level.lower(),
        access_log=False,
    )
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tutor", description="Tutor Engine — Il Tutor Digitale")
    sub = p.add_subparsers(dest="command", required=True)

    sp_seo = sub.add_parser("seo", help="Run SEO monitor once and print JSON report")
    sp_seo.add_argument("--notify", action="store_true", help="Also send Telegram notification")
    sp_seo.set_defaults(func=cmd_run_seo)

    sp_serve = sub.add_parser("serve", help="Start FastAPI dashboard + scheduler")
    sp_serve.set_defaults(func=cmd_serve)

    sp_cal = sub.add_parser("calendar", help="Genera il calendario editoriale settimanale")
    sp_cal.add_argument("--notify", action="store_true", help="Invia anche notifica Telegram")
    sp_cal.set_defaults(func=cmd_run_calendar)

    sp_cnt = sub.add_parser("content", help="Genera bozza contenuto da voce calendario approvata")
    sp_cnt.add_argument("--calendar-id", type=int, dest="calendar_id", help="ID specifico del calendario")
    sp_cnt.add_argument("--notify", action="store_true", help="Invia notifica Telegram con bottoni approvazione")
    sp_cnt.set_defaults(func=cmd_run_content)

    sp_rep = sub.add_parser("report", help="Genera il report settimanale (domenica)")
    sp_rep.add_argument("--notify", action="store_true", help="Invia anche notifica Telegram")
    sp_rep.set_defaults(func=cmd_weekly_report)

    sp_yt = sub.add_parser("youtube", help="Analizza performance canale YouTube")
    sp_yt.add_argument("--notify", action="store_true", help="Invia notifica Telegram")
    sp_yt.set_defaults(func=cmd_youtube)

    sp_rid = sub.add_parser("resolve-channel-id", help="Risolve @handle YouTube → Channel ID")
    sp_rid.add_argument("--handle", help="@handle YouTube (default: da config)")
    sp_rid.set_defaults(func=cmd_resolve_channel_id)

    sp_pub = sub.add_parser("publish", help="Pubblica bozze approvate sui canali Meta")
    sp_pub.add_argument("--notify", action="store_true", help="Invia report su Telegram")
    sp_pub.add_argument("--dry-run", action="store_true", help="Non pubblica, mostra solo cosa farebbe")
    sp_pub.set_defaults(func=cmd_publish)

    sp_ver = sub.add_parser("version", help="Print version and exit")
    sp_ver.set_defaults(func=cmd_version)

    return p


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.tutor_log_level)
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
