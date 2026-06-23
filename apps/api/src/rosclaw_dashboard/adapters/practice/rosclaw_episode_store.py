"""Adapter that exposes ROSClaw runtime episodes as dashboard runs.

ROSClaw writes finalized episodes to ``~/.rosclaw/artifacts/episodes/<id>/``.
This adapter reads the episode metadata and event JSONL files directly, without
taking a runtime dependency on the ``rosclaw`` package.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from rosclaw_dashboard.core.config import settings
from rosclaw_dashboard.core.workspace import resolve_rosclaw_home
from rosclaw_dashboard.models.schemas import ReplayManifest, RunDetail, RunSummary, TraceEvent


class RosclawEpisodeStoreAdapter:
    """Reads ROSClaw runtime episodes from the workspace artifact tree."""

    name = "rosclaw_episodes"
    mode = "real"

    def __init__(self, episodes_dir: str | Path | None = None) -> None:
        self._episodes_dir = Path(
            episodes_dir or settings.episodes_dir or resolve_rosclaw_home() / "artifacts" / "episodes"
        )
        if not self._episodes_dir.exists():
            self.mode = "unavailable"
        elif not self._episodes_dir.is_dir():
            self.mode = "degraded"

    def _episode_dir(self, run_id: str) -> Path:
        return self._episodes_dir / run_id

    def _load_metadata(self, run_id: str) -> dict[str, Any] | None:
        path = self._episode_dir(run_id) / "metadata.json"
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def _read_jsonl(self, run_id: str, filename: str) -> list[dict[str, Any]]:
        path = self._episode_dir(run_id) / filename
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass
        return rows

    def _list_episode_ids(self) -> list[str]:
        if not self._episodes_dir.exists():
            return []
        return sorted(
            d.name for d in self._episodes_dir.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        )

    def _metadata_to_summary(self, run_id: str, meta: dict[str, Any]) -> RunSummary:
        created_at = meta.get("created_at")
        finalized_at = meta.get("finalized_at")
        duration = meta.get("duration_sec")
        if duration is None and created_at is not None and finalized_at is not None:
            duration = float(finalized_at) - float(created_at)
        status = meta.get("status", "unknown")
        agent_request = meta.get("agent_request")
        praxis_event = meta.get("praxis_event", {})
        received = meta.get("received_events", [])
        return RunSummary(
            run_id=run_id,
            episode_id=run_id,
            task_id=praxis_event.get("event_id"),
            status=str(status).lower(),
            robot_id=meta.get("robot_id"),
            task=agent_request if isinstance(agent_request, str) else None,
            started_at=float(created_at) if created_at is not None else None,
            ended_at=float(finalized_at) if finalized_at is not None else None,
            duration_sec=float(duration) if duration is not None else None,
            event_count=len(received),
            failure_count=1 if str(status).lower() in {"failure", "blocked", "failed_runtime"} else 0,
            tracks=sorted(set(received)),
            has_trajectory=(self._episode_dir(run_id) / "trajectory.jsonl").exists(),
            has_media=False,
            has_curves=False,
            manifest_path=str(self._episode_dir(run_id) / "metadata.json"),
            agent_request=meta.get("agent_request") if isinstance(meta.get("agent_request"), dict) else None,
            provider_trace=None,
            sandbox_result=None,
            runtime_action=None,
            critic_result=None,
            memory_write_result=None,
            artifact_uri=f"rosclaw://artifacts/episodes/{run_id}",
        )

    def list_runs(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[RunSummary], int]:
        run_ids = self._list_episode_ids()
        summaries: list[RunSummary] = []
        for run_id in run_ids:
            meta = self._load_metadata(run_id)
            if meta is None:
                continue
            summaries.append(self._metadata_to_summary(run_id, meta))
        if status:
            summaries = [s for s in summaries if s.status == status]
        total = len(summaries)
        return summaries[offset:offset + limit], total

    def get_run(self, run_id: str) -> RunDetail:
        meta = self._load_metadata(run_id)
        if meta is None:
            raise HTTPException(status_code=404, detail=f"Episode {run_id} not found")
        summary = self._metadata_to_summary(run_id, meta)
        return RunDetail(**summary.model_dump(), manifest=meta)

    def read_timeline(self, run_id: str) -> list[dict[str, Any]]:
        meta = self._load_metadata(run_id)
        if meta is None:
            raise HTTPException(status_code=404, detail=f"Episode {run_id} not found")
        started_at = float(meta.get("created_at") or 0.0)
        events: list[dict[str, Any]] = []

        # ROSClaw events.jsonl only stores received event names; keep them as
        # lightweight timeline entries.
        for raw in self._read_jsonl(run_id, "events.jsonl"):
            ts = raw.get("timestamp") or started_at
            events.append(TraceEvent(
                id=raw.get("id") or str(uuid.uuid4()),
                run_id=run_id,
                ts=float(ts),
                t_rel=float(ts) - started_at,
                source=raw.get("source") or "rosclaw",
                type=raw.get("type") or "event",
                track="auto",
                severity="info",
                title=raw.get("type") or "Event",
                summary=None,
                entity=raw.get("robot_id"),
                payload={k: v for k, v in raw.items() if k not in {"timestamp", "type"}},
            ).model_dump())

        # Merge provider trace and trajectory entries when available.
        for source_file, track, severity in [
            ("provider_trace.jsonl", "provider", "info"),
            ("trajectory.jsonl", "robot", "info"),
        ]:
            for raw in self._read_jsonl(run_id, source_file):
                ts = raw.get("timestamp") or started_at
                events.append(TraceEvent(
                    id=raw.get("id") or str(uuid.uuid4()),
                    run_id=run_id,
                    ts=float(ts),
                    t_rel=float(ts) - started_at,
                    source=track,
                    type=raw.get("phase") or raw.get("type") or "event",
                    track=track,  # type: ignore[assignment]
                    severity=severity,
                    title=raw.get("phase") or raw.get("type") or "Event",
                    summary=None,
                    entity=None,
                    payload=raw,
                ).model_dump())

        events.sort(key=lambda e: e["t_rel"])
        return events

    def get_replay_manifest(self, run_id: str) -> ReplayManifest:
        meta = self._load_metadata(run_id)
        if meta is None:
            raise HTTPException(status_code=404, detail=f"Episode {run_id} not found")
        duration = meta.get("duration_sec") or 0.0
        trajectory_path = self._episode_dir(run_id) / "trajectory.jsonl"
        trajectory = None
        if trajectory_path.exists():
            trajectory = {
                "url": f"/api/runs/{run_id}/trajectory",
                "sample_count": len(self._read_jsonl(run_id, "trajectory.jsonl")),
            }
        return ReplayManifest(
            run_id=run_id,
            duration_sec=float(duration),
            media=[],
            curves=[],
            trajectory=trajectory,  # type: ignore[arg-type]
            sandbox_states=[],
            tracks=sorted(set(meta.get("received_events", []))),
        )

    def validate_run(self, run_id: str) -> dict[str, Any]:
        meta = self._load_metadata(run_id)
        if meta is None:
            return {"valid": False, "errors": ["missing metadata.json"]}
        errors: list[str] = []
        if not meta.get("episode_id"):
            errors.append("missing episode_id")
        if not self._episode_dir(run_id).is_dir():
            errors.append("missing episode directory")
        return {"valid": len(errors) == 0, "errors": errors}

    def health(self) -> dict[str, Any]:
        return {
            "episodes_dir": str(self._episodes_dir),
            "exists": self._episodes_dir.exists(),
            "run_count": len(self._list_episode_ids()),
        }
