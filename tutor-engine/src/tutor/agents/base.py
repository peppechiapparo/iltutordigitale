"""Agent base classes — Template Method pattern."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from ..core.db import Database
from ..core.logging import get_logger

log = get_logger(__name__)

Severity = Literal["info", "warning", "error", "critical"]
Status = Literal["ok", "warning", "error", "running"]


@dataclass
class Finding:
    severity: Severity
    code: str
    message: str
    url: str | None = None
    payload: dict | None = None


@dataclass
class AgentReport:
    agent: str
    started_at: datetime
    finished_at: datetime
    status: Status
    summary: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def has_alerts(self) -> bool:
        return any(f.severity in ("error", "critical") for f in self.findings)


class Agent(ABC):
    """Template Method: run() = collect → analyze → persist → return.

    Subclasses implement `collect()` and `analyze()`.
    Persistence and timing are handled here.
    """

    name: str = "base"

    def __init__(self, db: Database) -> None:
        self._db = db

    # ---- Template steps to override --------------------------------------
    @abstractmethod
    def collect(self) -> dict:
        """Gather raw data from the world. Pure I/O, no analysis."""

    @abstractmethod
    def analyze(self, raw: dict) -> tuple[Status, str, list[Finding]]:
        """Turn raw data into (status, summary, findings)."""

    # ---- Template skeleton -----------------------------------------------
    def run(self) -> AgentReport:
        started = datetime.now()
        t0 = time.monotonic()
        log.info("agent_start", agent=self.name)
        try:
            raw = self.collect()
            status, summary, findings = self.analyze(raw)
        except Exception as exc:  # noqa: BLE001 — top-level safety net
            finished = datetime.now()
            log.exception("agent_crashed", agent=self.name)
            report = AgentReport(
                agent=self.name,
                started_at=started,
                finished_at=finished,
                status="error",
                summary=f"Agent crashed: {exc!r}",
                findings=[Finding(severity="critical", code="agent.crash", message=str(exc))],
            )
            self._persist(report)
            return report

        finished = datetime.now()
        report = AgentReport(
            agent=self.name,
            started_at=started,
            finished_at=finished,
            status=status,
            summary=summary,
            findings=findings,
        )
        self._persist(report)
        log.info(
            "agent_done",
            agent=self.name,
            status=status,
            findings=len(findings),
            elapsed_s=round(time.monotonic() - t0, 2),
        )
        return report

    # ---- Persistence -----------------------------------------------------
    def _persist(self, report: AgentReport) -> None:
        with self._db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO agent_runs(agent, started_at, finished_at, status, summary, details)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    report.agent,
                    report.started_at.isoformat(timespec="seconds"),
                    report.finished_at.isoformat(timespec="seconds"),
                    report.status,
                    report.summary,
                    json.dumps({"finding_count": len(report.findings)}),
                ),
            )
            run_id = cur.lastrowid
            for f in report.findings:
                conn.execute(
                    "INSERT INTO findings(run_id, severity, code, message, url, payload)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        run_id,
                        f.severity,
                        f.code,
                        f.message,
                        f.url,
                        json.dumps(f.payload) if f.payload else None,
                    ),
                )
            conn.commit()


class LLMAgent(Agent):
    """Agent with LLM-driven ReAct loop (Reason → Act → Observe → Repeat).

    Subclasses implement `collect()` to gather initial context and
    `build_system_prompt()` to define the agent's role and instructions.
    `analyze()` is implemented here via the agentic loop.
    """

    MAX_ITERATIONS = 15  # safety cap to avoid infinite loops

    def __init__(self, db: Database, llm: Any) -> None:
        super().__init__(db)
        self._llm = llm

    def build_system_prompt(self, context: dict) -> str:
        """Return the system prompt for this agent. Override in subclasses."""
        raise NotImplementedError

    def get_tools(self) -> list[dict]:
        """Return tool definitions for this agent. Override in subclasses."""
        raise NotImplementedError

    def analyze(self, raw: dict) -> tuple[Status, str, list[Finding]]:
        """Run the LLM agentic loop. raw = output of collect()."""
        from ..tools.web_tools import TOOL_DISPATCH

        system_prompt = self.build_system_prompt(raw)
        tools = self.get_tools()

        initial_message = self._build_initial_message(raw)
        messages: list[dict[str, Any]] = [{"role": "user", "content": initial_message}]

        findings: list[Finding] = []
        total_input_tokens = 0
        total_output_tokens = 0

        for iteration in range(self.MAX_ITERATIONS):
            log.info("agent_loop_step", agent=self.name, iteration=iteration + 1)

            response = self._llm.complete_with_tools(
                messages=messages,
                tools=tools,
                system=system_prompt,
                max_tokens=4096,
            )
            total_input_tokens += response.get("input_tokens", 0)
            total_output_tokens += response.get("output_tokens", 0)
            provider = response.get("provider", "anthropic")

            # Add assistant message to history (normalised per provider)
            messages.append(response["assistant_message"])

            if response["stop_reason"] == "end_turn" or not response["tool_uses"]:
                log.info("agent_loop_done", agent=self.name, reason="end_turn", iterations=iteration + 1)
                break

            # Execute tool calls
            tool_results = []
            for tool_call in response["tool_uses"]:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]

                if tool_name == "report_findings":
                    # Special: this tool ends the loop and captures findings
                    for f in tool_input.get("findings", []):
                        findings.append(Finding(
                            severity=f["severity"],
                            code=f["code"],
                            message=f["message"],
                            url=f.get("url"),
                        ))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": json.dumps({"ok": True, "recorded": len(findings)}),
                    })
                    self._append_tool_results(messages, tool_results, provider)
                    log.info(
                        "agent_loop_done",
                        agent=self.name,
                        reason="report_findings",
                        findings=len(findings),
                    )
                    break
                else:
                    try:
                        result_content = self._dispatch_tool(tool_name, tool_input)
                    except Exception as exc:  # noqa: BLE001
                        log.warning("tool_error", tool=tool_name, error=str(exc))
                        result_content = json.dumps({"error": str(exc)})

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": result_content,
                    })
            else:
                # for loop completed without report_findings break — continue outer loop
                self._append_tool_results(messages, tool_results, provider)
                continue

            # report_findings was called — exit outer loop
            break
        else:
            log.warning("agent_loop_max_iterations", agent=self.name, max=self.MAX_ITERATIONS)

        log.info(
            "agent_tokens",
            agent=self.name,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
        )

        status = self._overall_status(findings)
        summary = self._build_summary(status, findings)
        return status, summary, findings

    def _dispatch_tool(self, tool_name: str, tool_input: dict) -> str:
        """Dispatch a tool call to the appropriate implementation.

        Override in subclasses to handle agent-specific tools before
        falling back to the global TOOL_DISPATCH.
        """
        from ..tools.web_tools import TOOL_DISPATCH

        dispatch_fn = TOOL_DISPATCH.get(tool_name)
        if dispatch_fn is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        result = dispatch_fn(tool_input)
        return json.dumps(result)

    def _build_initial_message(self, context: dict) -> str:
        """Build the first user message. Override for custom context."""
        return f"Please audit the site: {context.get('site_url', 'unknown')}"

    @staticmethod
    def _append_tool_results(
        messages: list[dict],
        tool_results: list[dict],
        provider: str,
    ) -> None:
        """Append tool results to conversation history in provider-native format."""
        if provider == "openai":
            # OpenAI: one separate "tool" message per result
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_use_id"],
                    "content": tr["content"],
                })
        else:
            # Anthropic: single "user" message containing all tool_result blocks
            messages.append({"role": "user", "content": tool_results})

    @staticmethod
    def _overall_status(findings: list[Finding]) -> Status:
        if any(f.severity in ("critical", "error") for f in findings):
            return "error"
        if any(f.severity == "warning" for f in findings):
            return "warning"
        return "ok"

    @staticmethod
    def _build_summary(status: Status, findings: list[Finding]) -> str:
        parts = [f"status={status}"]
        for sev in ("critical", "error", "warning", "info"):
            count = sum(1 for f in findings if f.severity == sev)
            if count:
                parts.append(f"{sev}={count}")
        return " ".join(parts)
