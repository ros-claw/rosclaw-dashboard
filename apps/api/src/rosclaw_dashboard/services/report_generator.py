"""Acceptance evidence report generator.

Collects run summary, module modes, timeline/safety/failure/replay/export evidence
and produces a Markdown + JSON report with a PASS / PARTIAL / FAIL verdict.
"""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from rosclaw_dashboard.core.config import settings
from rosclaw_dashboard.models.database import ExportJob, SessionLocal
from rosclaw_dashboard.models.schemas import (
    AcceptanceReport,
    AcceptanceReportArtifact,
    AcceptanceReportSection,
    AcceptanceVerdict,
)
from rosclaw_dashboard.services import evidence_graph, run_indexer


def _module_modes() -> dict[str, str]:
    """Snapshot current module modes from the status endpoint logic."""
    # Import locally to avoid circular imports at module load.
    from rosclaw_dashboard.adapters.eventbus import JsonlTailAdapter
    from rosclaw_dashboard.adapters.practice import LocalPracticeStoreAdapter
    from rosclaw_dashboard.core.config import settings as cfg

    event_bus_adapter = JsonlTailAdapter(cfg.events_dir)
    event_bus_adapter.connect()
    practice_adapter = LocalPracticeStoreAdapter()

    return {
        "dashboard": "real",
        "memory": "rule_based",
        "seekdb": "fixture",
        "registry": "fixture",
        "sandbox": "fixture",
        "practice": practice_adapter.mode,
        "event_bus": event_bus_adapter.mode,
        "runtime": "mock",
        "mcp_gateway": "mock",
        "provider_router": "mock",
    }


def _get_export_jobs(db: Session, run_id: str) -> list[ExportJob]:
    return db.query(ExportJob).filter(ExportJob.run_id == run_id).all()


def _verdict_from_failures_and_modes(
    run: Any,
    modes: dict[str, str],
    failures: list[Any],
) -> AcceptanceVerdict:
    if run.failure_count and run.failure_count > 0:
        return AcceptanceVerdict.FAIL
    if any(m == "unavailable" for m in modes.values()):
        return AcceptanceVerdict.PARTIAL
    if run.status == "success":
        return AcceptanceVerdict.PASS
    return AcceptanceVerdict.PARTIAL


def _report_dir(run_id: str) -> Path:
    path = settings.report_dir / "acceptance" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json(report: AcceptanceReport, run_id: str) -> Path:
    path = _report_dir(run_id) / "report.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2, default=str)
    return path


def _write_markdown(report: AcceptanceReport, run_id: str) -> Path:
    path = _report_dir(run_id) / "report.md"
    lines: list[str] = [
        f"# Acceptance Report — {run_id}",
        "",
        f"**Verdict:** {report.verdict}",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(report.generated_at))}",
        "",
        f"**Summary:** {report.summary}",
        "",
        "## Sections",
        "",
    ]
    for section in report.sections:
        lines.append(f"### {section.title} — {section.status.upper()}")
        for finding in section.findings:
            lines.append(f"- {finding}")
        if section.evidence:
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(section.evidence, indent=2, default=str))
            lines.append("```")
        lines.append("")

    lines.append("## Artifacts")
    lines.append("")
    for artifact in report.artifacts:
        lines.append(f"- `{artifact.name}` — {artifact.path}")

    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def _write_zip(run_id: str) -> Path:
    report_dir = _report_dir(run_id)
    zip_path = report_dir / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in report_dir.iterdir():
            if path.is_file() and path.name != "bundle.zip":
                zf.write(path, arcname=path.name)
    return zip_path


def generate_acceptance_report(run_id: str) -> AcceptanceReport:
    try:
        db = SessionLocal()
        run = run_indexer.get_run(db, run_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    modes = _module_modes()
    failures = evidence_graph.build_evidence_graph(run_id).nodes
    failure_nodes = [n for n in failures if n.track == "failure" or n.severity in {"error", "failure"}]
    sandbox_decisions = evidence_graph.get_sandbox_decisions(run_id)
    memory_events = evidence_graph.get_memory_events(run_id)
    provider_traces = evidence_graph.get_provider_route_traces(run_id)
    how_recoveries = evidence_graph.get_how_recoveries(run_id)
    export_jobs = _get_export_jobs(db, run_id)

    verdict = _verdict_from_failures_and_modes(run, modes, failure_nodes)

    sections: list[AcceptanceReportSection] = [
        AcceptanceReportSection(
            title="Run Summary",
            status="pass" if run.status == "success" else "partial" if run.status == "running" else "fail",
            findings=[
                f"Run status: {run.status}",
                f"Robot: {run.robot_id or 'unknown'}",
                f"Task: {run.task or 'unknown'}",
                f"Events: {run.event_count}",
                f"Failures: {run.failure_count}",
                f"Duration: {run.duration_sec:.2f}s" if run.duration_sec else "Duration: unknown",
            ],
            evidence=run.manifest,
        ),
        AcceptanceReportSection(
            title="Module Modes",
            status="pass" if all(m in {"real", "rule_based", "fixture"} for m in modes.values()) else "partial",
            findings=[f"{name}: {mode}" for name, mode in modes.items()],
            evidence={"modes": modes},
        ),
        AcceptanceReportSection(
            title="Sandbox Decisions",
            status="pass" if not any(d.decision == "BLOCK" for d in sandbox_decisions) else "fail",
            findings=[
                f"{d.decision} at {d.t_rel:.2f}s ({d.reason or 'no reason'})"
                for d in sandbox_decisions
            ] or ["No sandbox decisions recorded"],
            evidence={"decisions": [d.model_dump() for d in sandbox_decisions]},
        ),
        AcceptanceReportSection(
            title="Memory / How Recovery",
            status="pass" if memory_events or how_recoveries else "info",
            findings=[
                f"Memory events: {len(memory_events)}",
                f"How recoveries: {len(how_recoveries)}",
            ],
            evidence={
                "memory_events": [m.model_dump() for m in memory_events],
                "how_recoveries": [h.model_dump() for h in how_recoveries],
            },
        ),
        AcceptanceReportSection(
            title="Provider Routing",
            status="pass" if provider_traces else "info",
            findings=[
                f"Provider {t.provider}: {t.latency_ms}ms" for t in provider_traces
            ] or ["No provider traces recorded"],
            evidence={"traces": [t.model_dump() for t in provider_traces]},
        ),
        AcceptanceReportSection(
            title="Export Jobs",
            status="pass" if any(j.state == "completed" for j in export_jobs) else "info",
            findings=[
                f"{j.format}: {j.state}" for j in export_jobs
            ] or ["No export jobs recorded"],
            evidence={"jobs": [{"job_id": j.job_id, "format": j.format, "state": j.state} for j in export_jobs]},
        ),
    ]

    summary = (
        f"Run {run_id} ({run.status}) with {run.failure_count or 0} failures "
        f"and {len(sandbox_decisions)} sandbox decisions. Verdict: {verdict.value}."
    )

    report = AcceptanceReport(
        run_id=run_id,
        generated_at=time.time(),
        verdict=verdict,
        summary=summary,
        sections=sections,
        artifacts=[],
    )

    json_path = _write_json(report, run_id)
    md_path = _write_markdown(report, run_id)
    zip_path = _write_zip(run_id)

    report.artifacts = [
        AcceptanceReportArtifact(name="report.json", path=str(json_path), mime_type="application/json"),
        AcceptanceReportArtifact(name="report.md", path=str(md_path), mime_type="text/markdown"),
        AcceptanceReportArtifact(name="bundle.zip", path=str(zip_path), mime_type="application/zip"),
    ]

    # Rewrite JSON with artifact list.
    _write_json(report, run_id)
    return report


def get_report_path(run_id: str, name: str = "report.md") -> Path | None:
    path = _report_dir(run_id) / name
    return path if path.exists() else None
