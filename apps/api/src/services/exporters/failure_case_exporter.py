"""Failure-case export — extracts windows around every failure event."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from services import run_indexer


def export_failure_case(run_id: str, out_dir: Path, window_sec: float = 5.0) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_indexer._load_manifest(run_id) or {}
    all_events, _ = run_indexer.get_events(run_id, limit=10_000)
    failures = [
        e for e in all_events
        if e.severity in {"error", "critical", "fatal", "failure"} or e.track == "failure"
    ]

    cases: list[dict[str, Any]] = []
    for failure in failures:
        window = [
            e.model_dump()
            for e in all_events
            if abs(e.t_rel - failure.t_rel) <= window_sec
        ]
        cases.append({
            "failure_event": failure.model_dump(),
            "window_sec": window_sec,
            "events": window,
        })

    package = {
        "format": "failure_case",
        "run_id": run_id,
        "robot_id": manifest.get("robot_id"),
        "task": manifest.get("task"),
        "failure_count": len(cases),
        "cases": cases,
    }
    with (out_dir / "failure_case.json").open("w", encoding="utf-8") as f:
        json.dump(package, f, indent=2)
    shutil.copy(
        run_indexer._run_dir(run_id) / "manifest.json",
        out_dir / "manifest.json",
    )
    return out_dir
