"""RLDS-format export — minimal JSON package."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from services import run_indexer


def export_rlds(run_id: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_indexer._load_manifest(run_id) or {}
    events, _ = run_indexer.get_events(run_id, limit=10_000)

    steps: list[dict[str, Any]] = []
    for e in events:
        if e.track in {"robot", "sandbox"} and e.payload:
            obs = e.payload.get("observation") or e.payload.get("state") or e.payload
            action = e.payload.get("action")
            steps.append({
                "t_rel": e.t_rel,
                "observation": obs,
                "action": action,
                "reward": e.payload.get("reward", 0.0),
                "is_terminal": e.type == "episode.end",
                "is_first": e.type == "episode.start",
                "is_last": e.type == "episode.end",
            })

    info = {
        "format": "rlds",
        "run_id": run_id,
        "robot_id": manifest.get("robot_id"),
        "task": manifest.get("task"),
        "steps": len(steps),
    }
    with (out_dir / "info.json").open("w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    with (out_dir / "episodes.json").open("w", encoding="utf-8") as f:
        json.dump({"steps": steps}, f, indent=2)
    shutil.copy(
        run_indexer._run_dir(run_id) / "manifest.json",
        out_dir / "manifest.json",
    )
    return out_dir
