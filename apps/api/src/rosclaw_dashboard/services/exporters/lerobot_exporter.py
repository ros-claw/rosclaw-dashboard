"""LeRobot-format export — minimal JSON package."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from rosclaw_dashboard.services import run_indexer


def export_lerobot(run_id: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_indexer._load_manifest(run_id) or {}
    events, _ = run_indexer.get_events(run_id, limit=10_000)

    frames: list[dict[str, Any]] = []
    for e in events:
        if e.track in {"robot", "sandbox"} and e.payload:
            frames.append({
                "timestamp": e.t_rel,
                "observation": e.payload.get("observation") or e.payload.get("state") or e.payload,
                "action": e.payload.get("action"),
                "task": manifest.get("task"),
            })

    meta = {
        "hub": "rosclaw",
        "robot_type": manifest.get("robot_id"),
        "task": manifest.get("task"),
        "fps": manifest.get("fps", 10),
        "num_frames": len(frames),
        "features": {
            "observation": {"dtype": "float32"},
            "action": {"dtype": "float32"},
        },
    }
    (out_dir / "meta").mkdir(exist_ok=True)
    with (out_dir / "meta" / "info.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    (out_dir / "data").mkdir(exist_ok=True)
    with (out_dir / "data" / "chunk-000.json").open("w", encoding="utf-8") as f:
        json.dump({"frames": frames}, f, indent=2)
    shutil.copy(
        run_indexer._run_dir(run_id) / "manifest.json",
        out_dir / "manifest.json",
    )
    return out_dir
