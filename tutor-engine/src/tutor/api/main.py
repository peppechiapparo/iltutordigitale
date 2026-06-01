"""FastAPI dashboard + control endpoints."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse

from .. import __version__
from ..adapters.llm import build_llm_client
from ..adapters.notifier import build_notifier
from ..adapters.telegram_polling import build_polling_handler
from ..agents.seo_monitor import SEOMonitorAgent
from ..agents.calendar_agent import CalendarAgent
from ..agents.content_agent import ContentAgent
from ..agents.weekly_report import WeeklyReportAgent
from ..agents.youtube_monitor import YouTubeMonitorAgent
from ..agents.social_publisher import SocialPublisherAgent
from ..adapters.meta_publisher import build_meta_publisher
from ..core.config import Settings, get_settings
from ..core.db import Database
from ..core.events import EventBus
from ..core.logging import configure_logging, get_logger
from ..core.orchestrator import Orchestrator
from ..core.scheduler import build_scheduler

log = get_logger(__name__)

# In development: relative to source tree. In production (installed package): /app/migrations.
_src_migrations = Path(__file__).resolve().parents[3] / "migrations"
MIGRATIONS_DIR = _src_migrations if _src_migrations.exists() else Path("/app/migrations")


def _require_token(settings: Settings, authorization: str | None) -> None:
    if not settings.tutor_api_token:
        return
    expected = f"Bearer {settings.tutor_api_token}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.tutor_log_level)
    settings.ensure_dirs()

    db = Database(settings.db_path, MIGRATIONS_DIR)
    db.init()

    notifier = build_notifier(settings.telegram_bot_token, settings.telegram_chat_id)

    llm_client = build_llm_client(
        settings.llm_provider,
        settings.anthropic_api_key,
        settings.anthropic_model,
        settings.openai_api_key,
        settings.openai_model,
        settings.github_token,
        settings.github_model,
    )
    app.state.llm = llm_client

    # EventBus SQLite — collegamento event-driven tra agenti
    bus = EventBus(db)

    # MetaPublisher — usato da Orchestrator, Scheduler e auto-publish callback
    meta = build_meta_publisher(settings)

    # Orchestrator — ascolta EventBus e trigera gli agenti
    orchestrator = Orchestrator(
        bus=bus, db=db, llm=llm_client, notifier=notifier,
        publisher=meta, settings=settings,
    )
    orchestrator.start()
    app.state.bus = bus
    app.state.orchestrator = orchestrator

    scheduler = build_scheduler(settings, db, notifier, llm_client, bus=bus, publisher=meta)
    scheduler.start()

    # Callback: quando una bozza viene approvata via Telegram → pubblica subito
    def _auto_publish_draft(draft_id: int) -> None:
        """Triggera la pubblicazione di una singola bozza approvata."""
        try:
            from ..agents.social_publisher import SocialPublisherAgent
            agent = SocialPublisherAgent(db=db, publisher=meta, dry_run=False)
            report = agent.run()
            if report.summary:
                notifier.send("📤 Pubblicazione automatica", report.summary)
            log.info("auto_publish_done", draft_id=draft_id, status=report.status)
        except Exception as exc:  # noqa: BLE001
            log.error("auto_publish_error", draft_id=draft_id, error=str(exc))
            notifier.send("⚠️ Errore pubblicazione automatica", str(exc))

    # Telegram polling handler — processa ✅/✏️/❌ dalle bozze/calendario
    polling = build_polling_handler(
        settings.telegram_bot_token, db, on_draft_approved=_auto_publish_draft
    )
    polling.start()
    app.state.polling = polling

    log.info("tutor_started", version=__version__, env=settings.tutor_env)

    app.state.settings = settings
    app.state.db = db
    app.state.notifier = notifier
    app.state.scheduler = scheduler

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        if hasattr(app.state, 'polling'):
            app.state.polling.stop()
        log.info("tutor_stopped")


app = FastAPI(
    title="Tutor Engine",
    version=__version__,
    description="Content engine agenttico per Il Tutor Digitale — SEO monitor, calendario, bozze.",
    lifespan=lifespan,
)


def get_db() -> Database:
    return app.state.db  # type: ignore[no-any-return]


DbDep = Annotated[Database, Depends(get_db)]
AuthHeader = Annotated[str | None, Header(alias="Authorization")]


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/api/runs")
def list_runs(db: DbDep, authorization: AuthHeader = None, limit: int = 50) -> JSONResponse:
    _require_token(app.state.settings, authorization)
    limit = max(1, min(limit, 500))
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, agent, started_at, finished_at, status, summary"
            " FROM agent_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return JSONResponse([dict(r) for r in rows])


@app.get(
    "/api/runs/{run_id}",
    responses={404: {"description": "Run not found"}},
)
def get_run(run_id: int, db: DbDep, authorization: AuthHeader = None) -> JSONResponse:
    _require_token(app.state.settings, authorization)
    with db.connect() as conn:
        run = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        findings = conn.execute(
            "SELECT severity, code, message, url, payload FROM findings WHERE run_id = ?",
            (run_id,),
        ).fetchall()
    payload = dict(run)
    payload["findings"] = [
        {**dict(f), "payload": json.loads(f["payload"]) if f["payload"] else None}
        for f in findings
    ]
    return JSONResponse(payload)


@app.post("/api/agents/seo_monitor/run")
def trigger_seo_monitor(db: DbDep, authorization: AuthHeader = None) -> JSONResponse:
    """Manual on-demand run of the SEO monitor."""
    _require_token(app.state.settings, authorization)
    settings: Settings = app.state.settings
    agent = SEOMonitorAgent(db, app.state.llm, settings.site_url, settings.site_instagram_handle)
    report = agent.run()
    return JSONResponse({
        "agent": report.agent,
        "status": report.status,
        "summary": report.summary,
        "findings": [
            {"severity": f.severity, "code": f.code, "message": f.message, "url": f.url}
            for f in report.findings
        ],
    })


@app.post("/api/agents/calendar/run")
def trigger_calendar_agent(db: DbDep, authorization: AuthHeader = None) -> JSONResponse:
    """Manual on-demand run del CalendarAgent."""
    _require_token(app.state.settings, authorization)
    agent = CalendarAgent(db=db, llm=app.state.llm)
    report = agent.run()
    return JSONResponse({
        "agent": report.agent,
        "status": report.status,
        "summary": report.summary,
    })


@app.post("/api/agents/content/run")
def trigger_content_agent(
    db: DbDep,
    authorization: AuthHeader = None,
    calendar_id: int | None = None,
) -> JSONResponse:
    """Manual on-demand run del ContentAgent."""
    _require_token(app.state.settings, authorization)
    agent = ContentAgent(db=db, llm=app.state.llm, calendar_id=calendar_id)
    report = agent.run()
    return JSONResponse({
        "agent": report.agent,
        "status": report.status,
        "summary": report.summary,
    })


@app.post("/api/agents/weekly_report/run")
def trigger_weekly_report(db: DbDep, authorization: AuthHeader = None) -> JSONResponse:
    """Manual on-demand run del WeeklyReportAgent."""
    _require_token(app.state.settings, authorization)
    agent = WeeklyReportAgent(db=db, llm=app.state.llm)
    report = agent.run()
    return JSONResponse({
        "agent": report.agent,
        "status": report.status,
        "summary": report.summary,
    })


@app.post("/api/agents/trends/run")
def trigger_trends(db: DbDep, authorization: AuthHeader = None) -> JSONResponse:
    """Manual on-demand run del TrendResearchAgent."""
    from ..agents.trend_agent import TrendResearchAgent
    _require_token(app.state.settings, authorization)
    bus = getattr(app.state, "bus", None)
    agent = TrendResearchAgent(db=db, bus=bus)
    report = agent.run()
    return JSONResponse({
        "agent": report.agent,
        "status": report.status,
        "summary": report.summary,
    })


@app.get("/api/calendar")
def list_calendar(db: DbDep, authorization: AuthHeader = None, limit: int = 20) -> JSONResponse:
    """Elenco voci calendario editoriale."""
    _require_token(app.state.settings, authorization)
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, week_start, day, date, pillar, format, topic, status"
            " FROM editorial_calendar ORDER BY date DESC LIMIT ?",
            (max(1, min(limit, 200)),),
        ).fetchall()
    return JSONResponse([dict(r) for r in rows])


@app.get("/api/drafts")
def list_drafts(db: DbDep, authorization: AuthHeader = None, limit: int = 20) -> JSONResponse:
    """Elenco bozze generate."""
    _require_token(app.state.settings, authorization)
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, calendar_id, agent, content_type, title, status, created_at"
            " FROM drafts ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 200)),),
        ).fetchall()
    return JSONResponse([dict(r) for r in rows])


@app.get("/", response_class=HTMLResponse)
def dashboard(db: DbDep) -> HTMLResponse:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, agent, started_at, status, summary"
            " FROM agent_runs ORDER BY id DESC LIMIT 25"
        ).fetchall()
    settings: Settings = app.state.settings
    items = "".join(
        f"<tr><td>{r['id']}</td><td>{r['agent']}</td><td>{r['started_at']}</td>"
        f"<td class='s-{r['status']}'>{r['status']}</td><td>{r['summary'] or ''}</td></tr>"
        for r in rows
    )
    return HTMLResponse(f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <title>Tutor Engine — Il Tutor Digitale</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem; color: #222; }}
    h1 {{ margin: 0 0 .5rem 0; }}
    .sub {{ color: #666; margin-bottom: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ text-align: left; padding: .5rem .75rem; border-bottom: 1px solid #eee; }}
    th {{ background: #fafafa; font-weight: 600; }}
    .s-ok {{ color: #1a7f37; font-weight: 600; }}
    .s-warning {{ color: #b08800; font-weight: 600; }}
    .s-error, .s-critical {{ color: #b42318; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Tutor Engine <small style="font-size:.6em;color:#888">v{__version__}</small></h1>
  <div class="sub">🎓 <strong>Il Tutor Digitale</strong> — Target: <a href="{settings.site_url}">{settings.site_url}</a></div>
  <table>
    <thead><tr><th>#</th><th>Agent</th><th>Started</th><th>Status</th><th>Summary</th></tr></thead>
    <tbody>{items or '<tr><td colspan=5><em>No runs yet.</em></td></tr>'}</tbody>
  </table>
</body>
</html>""")
