"""Command-line entrypoint: `shan <subcommand>`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .adapters.notifier import build_notifier
from .agents.seo_monitor import SEOMonitorAgent
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


def cmd_serve(_: argparse.Namespace) -> int:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "shan.api.main:app",
        host=settings.shan_api_host,
        port=settings.shan_api_port,
        log_level=settings.shan_log_level.lower(),
        access_log=False,
    )
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shan", description="Shan Growth Agent")
    sub = p.add_subparsers(dest="command", required=True)

    sp_seo = sub.add_parser("seo", help="Run SEO monitor once and print JSON report")
    sp_seo.add_argument("--notify", action="store_true", help="Also send Telegram notification")
    sp_seo.set_defaults(func=cmd_run_seo)

    sp_serve = sub.add_parser("serve", help="Start FastAPI dashboard + scheduler")
    sp_serve.set_defaults(func=cmd_serve)

    sp_ver = sub.add_parser("version", help="Print version and exit")
    sp_ver.set_defaults(func=cmd_version)

    return p


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.shan_log_level)
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
