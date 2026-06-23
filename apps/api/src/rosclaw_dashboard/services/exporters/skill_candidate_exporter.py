"""Skill-candidate export — extracts a successful segment as a reusable package."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from rosclaw_dashboard.services import run_indexer


def export_skill_candidate(run_id: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_indexer._load_manifest(run_id) or {}
    all_events, _ = run_indexer.get_events(run_id, limit=10_000)

    # Prefer the segment between the first successful critic/auto event and the episode end.
    start_event = next(
        (e for e in all_events if e.track in {"critic", "auto"} and "success" in e.tags),
        None,
    )
    if start_event is None:
        start_event = next(
            (e for e in all_events if e.type in {"episode.start", "task.start"}),
            all_events[0] if all_events else None,
        )
    end_event = next(
        (e for e in reversed(all_events) if e.type in {"episode.end", "task.end"}),
        all_events[-1] if all_events else None,
    )
    start_t = start_event.t_rel if start_event else 0.0
    end_t = end_event.t_rel if end_event else start_t

    segment = [e for e in all_events if start_t <= e.t_rel <= end_t]
    steps = [
        {
            "t_rel": e.t_rel,
            "observation": e.payload.get("observation") or e.payload.get("state") if e.payload else None,
            "action": e.payload.get("action") if e.payload else None,
        }
        for e in segment
        if e.track in {"robot", "sandbox"}
    ]

    package = {
        "format": "skill_candidate",
        "run_id": run_id,
        "robot_id": manifest.get("robot_id"),
        "task": manifest.get("task"),
        "start_t_rel": start_t,
        "end_t_rel": end_t,
        "steps": len(steps),
        "demo": steps,
    }
    with (out_dir / "skill_candidate.json").open("w", encoding="utf-8") as f:
        json.dump(package, f, indent=2)
    shutil.copy(
        run_indexer._run_dir(run_id) / "manifest.json",
        out_dir / "manifest.json",
    )
    return out_dir
