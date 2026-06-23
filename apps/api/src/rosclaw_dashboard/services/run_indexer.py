"""Run indexer — scan practice run directories and serve trace events from disk."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from rosclaw_dashboard.core.config import settings
from rosclaw_dashboard.models.database import TraceRun
from rosclaw_dashboard.models.schemas import RunDetail, RunSummary, TraceEvent


def _practice_dir() -> Path:
    """Read practice directory lazily so tests can set env vars before import."""
    return Path(os.environ.get("ROSCLAW_PRACTICE_DIR", settings.practice_dir))


def _run_dir(run_id: str) -> Path:
    return _practice_dir() / run_id


def _load_manifest(run_id: str) -> dict[str, Any] | None:
    path = _run_dir(run_id) / "manifest.json"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _event_files(run_id: str) -> list[Path]:
    run_dir = _run_dir(run_id)
    files: list[Path] = []
    timeline = run_dir / "timeline.jsonl"
    if timeline.exists():
        files.append(timeline)
    events_dir = run_dir / "events"
    if events_dir.is_dir():
        files.extend(sorted(events_dir.glob("*.jsonl")))
    return files


def _iter_events(run_id: str) -> Iterable[dict[str, Any]]:
    for path in _event_files(run_id):
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue


def _normalize_event(raw: dict[str, Any], run_id: str, started_at: float) -> dict[str, Any]:
    ts = raw.get("ts") or raw.get("timestamp") or started_at
    t_rel = raw.get("t_rel")
    if t_rel is None and ts is not None and started_at is not None:
        t_rel = float(ts) - float(started_at)
    if t_rel is None:
        t_rel = 0.0
    track = raw.get("track") or raw.get("source") or "auto"
    if track not in {
        "task", "agent", "tool", "provider", "sandbox", "runtime", "robot",
        "critic", "memory", "auto", "failure",
    }:
        track = "auto"
    return {
        "id": raw.get("id") or str(uuid.uuid4()),
        "run_id": run_id,
        "ts": float(ts) if ts is not None else 0.0,
        "t_rel": float(t_rel),
        "source": raw.get("source") or "unknown",
        "type": raw.get("type") or "event",
        "track": track,
        "severity": raw.get("severity") or "info",
        "title": raw.get("title") or raw.get("type") or "Event",
        "summary": raw.get("summary"),
        "entity": raw.get("entity"),
        "payload": raw.get("payload") or raw.get("data") or {},
        "links": raw.get("links") or [],
        "tags": raw.get("tags") or [],
    }


def _episode_fields(manifest: dict[str, Any]) -> dict[str, Any]:
    """Extract P0 episode structure fields from manifest."""
    return {
        "episode_id": manifest.get("episode_id") or manifest.get("run_id"),
        "task_id": manifest.get("task_id") or manifest.get("task"),
        "trace_id": manifest.get("trace_id"),
        "agent_request": manifest.get("agent_request"),
        "provider_trace": manifest.get("provider_trace"),
        "sandbox_result": manifest.get("sandbox_result"),
        "runtime_action": manifest.get("runtime_action"),
        "critic_result": manifest.get("critic_result"),
        "memory_write_result": manifest.get("memory_write_result"),
        "artifact_uri": manifest.get("artifact_uri"),
    }


def _summarize_run(run_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
    started_at = manifest.get("started_at") or manifest.get("start_ts") or 0.0
    ended_at = manifest.get("ended_at") or manifest.get("end_ts")
    duration = manifest.get("duration_sec")
    if duration is None and ended_at is not None and started_at is not None:
        duration = float(ended_at) - float(started_at)

    tracks: set[str] = set()
    failure_count = 0
    event_count = 0
    for raw in _iter_events(run_id):
        event_count += 1
        norm = _normalize_event(raw, run_id, float(started_at) if started_at else 0.0)
        tracks.add(norm["track"])
        if norm["severity"] in {"error", "critical", "fatal", "failure"} or norm["track"] == "failure":
            failure_count += 1

    media = manifest.get("media", [])
    curves = manifest.get("curves", [])
    trajectory = manifest.get("trajectory") or manifest.get("robot_trajectory")
    sandbox_states = manifest.get("sandbox_states", [])

    return {
        "run_id": run_id,
        "status": manifest.get("status", "unknown"),
        "robot_id": manifest.get("robot_id"),
        "task": manifest.get("task"),
        "started_at": float(started_at) if started_at is not None else None,
        "ended_at": float(ended_at) if ended_at is not None else None,
        "duration_sec": float(duration) if duration is not None else None,
        "event_count": event_count,
        "failure_count": failure_count,
        "tracks": sorted(tracks),
        "has_media": bool(media),
        "has_trajectory": bool(trajectory),
        "has_curves": bool(curves),
        "manifest_path": str(_run_dir(run_id) / "manifest.json"),
    } | _episode_fields(manifest)


def index_run(db: Session, run_id: str) -> TraceRun:
    manifest = _load_manifest(run_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    summary = _summarize_run(run_id, manifest)
    row = db.query(TraceRun).filter(TraceRun.run_id == run_id).first()
    if row is None:
        row = TraceRun(run_id=run_id)
        db.add(row)

    row.status = summary["status"]
    row.robot_id = summary["robot_id"]
    row.task = summary["task"]
    row.started_at = summary["started_at"]
    row.ended_at = summary["ended_at"]
    row.duration_sec = summary["duration_sec"]
    row.event_count = summary["event_count"]
    row.failure_count = summary["failure_count"]
    row.tracks = ",".join(summary["tracks"])
    row.manifest_json = json.dumps(manifest)
    db.commit()
    db.refresh(row)
    return row


def ensure_indexed(db: Session, run_id: str) -> TraceRun:
    row = db.query(TraceRun).filter(TraceRun.run_id == run_id).first()
    if row is None:
        return index_run(db, run_id)
    return row


def list_run_ids() -> list[str]:
    practice_dir = _practice_dir()
    if not practice_dir.exists():
        return []
    return sorted(
        d.name for d in practice_dir.iterdir()
        if d.is_dir() and (d / "manifest.json").exists()
    )


def list_runs(
    db: Session,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[RunSummary], int]:
    run_ids = list_run_ids()
    for run_id in run_ids:
        ensure_indexed(db, run_id)

    query = db.query(TraceRun)
    if status:
        query = query.filter(TraceRun.status == status)
    total = query.count()
    rows = query.order_by(TraceRun.started_at.desc()).offset(offset).limit(limit).all()

    summaries: list[RunSummary] = []
    for row in rows:
        manifest = json.loads(row.manifest_json) if row.manifest_json else {}
        summaries.append(RunSummary(
            run_id=row.run_id,
            status=row.status,
            robot_id=row.robot_id,
            task=row.task,
            started_at=row.started_at,
            ended_at=row.ended_at,
            duration_sec=row.duration_sec,
            event_count=row.event_count or 0,
            failure_count=row.failure_count or 0,
            tracks=row.tracks.split(",") if row.tracks else [],
            has_media=bool(manifest.get("media")),
            has_trajectory=bool(manifest.get("trajectory") or manifest.get("robot_trajectory")),
            has_curves=bool(manifest.get("curves")),
            manifest_path=str(_run_dir(row.run_id) / "manifest.json"),
            **_episode_fields(manifest),
        ))
    return summaries, total


def get_run(db: Session, run_id: str) -> RunDetail:
    row = ensure_indexed(db, run_id)
    manifest = json.loads(row.manifest_json) if row.manifest_json else {}
    return RunDetail(
        run_id=row.run_id,
        status=row.status,
        robot_id=row.robot_id,
        task=row.task,
        started_at=row.started_at,
        ended_at=row.ended_at,
        duration_sec=row.duration_sec,
        event_count=row.event_count or 0,
        failure_count=row.failure_count or 0,
        tracks=row.tracks.split(",") if row.tracks else [],
        has_media=bool(manifest.get("media")),
        has_trajectory=bool(manifest.get("trajectory") or manifest.get("robot_trajectory")),
        has_curves=bool(manifest.get("curves")),
        manifest_path=str(_run_dir(row.run_id) / "manifest.json"),
        manifest=manifest,
        **_episode_fields(manifest),
    )


def get_events(
    run_id: str,
    track: str | None = None,
    severity: str | None = None,
    type: str | None = None,
    entity: str | None = None,
    tag: str | None = None,
    start_t_rel: float | None = None,
    end_t_rel: float | None = None,
    q: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[TraceEvent], int]:
    manifest = _load_manifest(run_id)
    started_at = manifest.get("started_at") or manifest.get("start_ts") or 0.0 if manifest else 0.0
    events: list[TraceEvent] = []
    for raw in _iter_events(run_id):
        norm = _normalize_event(raw, run_id, float(started_at) if started_at else 0.0)
        if track and norm["track"] != track:
            continue
        if severity and norm["severity"] != severity:
            continue
        if type and norm["type"] != type:
            continue
        if entity and norm.get("entity") != entity:
            continue
        if tag and tag not in (norm.get("tags") or []):
            continue
        if start_t_rel is not None and norm["t_rel"] < start_t_rel:
            continue
        if end_t_rel is not None and norm["t_rel"] > end_t_rel:
            continue
        if q:
            hay = " ".join([
                norm.get("title", ""),
                norm.get("summary") or "",
                norm.get("entity") or "",
                " ".join(norm.get("tags") or []),
                json.dumps(norm.get("payload") or {}),
            ]).lower()
            if q.lower() not in hay:
                continue
        events.append(TraceEvent(**norm))

    total = len(events)
    events.sort(key=lambda e: e.t_rel)
    return events[offset:offset + limit], total


def get_failures(run_id: str) -> list[TraceEvent]:
    events, _ = get_events(run_id, limit=10_000)
    return [
        e for e in events
        if e.severity in {"error", "critical", "fatal", "failure"} or e.track == "failure"
    ]


def search_related(
    run_id: str,
    event_id: str,
    window_sec: float = 5.0,
) -> list[TraceEvent]:
    all_events, _ = get_events(run_id, limit=10_000)
    target: TraceEvent | None = None
    for e in all_events:
        if e.id == event_id:
            target = e
            break
    if target is None:
        return []

    related: list[TraceEvent] = []
    target_links = set(target.links or [])
    target_tags = set(target.tags or [])
    for e in all_events:
        if e.id == target.id:
            continue
        e_links = set(e.links or [])
        e_tags = set(e.tags or [])
        is_linked = e.id in target_links or target_links.intersection(e_links)
        in_window = abs(e.t_rel - target.t_rel) <= window_sec
        if is_linked or (
            in_window
            and (
                (target.entity and e.entity == target.entity)
                or target_tags.intersection(e_tags)
            )
        ):
            related.append(e)
    related.sort(key=lambda e: e.t_rel)
    return related


def get_replay_manifest(run_id: str) -> dict[str, Any]:
    manifest = _load_manifest(run_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    duration = manifest.get("duration_sec")
    if duration is None:
        started_at = manifest.get("started_at") or manifest.get("start_ts")
        ended_at = manifest.get("ended_at") or manifest.get("end_ts")
        if started_at is not None and ended_at is not None:
            duration = float(ended_at) - float(started_at)
    if duration is None:
        duration = 0.0

    def media_url(path: str) -> str:
        return f"/api/runs/{run_id}/media/{path}"

    def curve_url(name: str) -> str:
        return f"/api/runs/{run_id}/curves/{name}"

    def trajectory_url() -> str:
        return f"/api/runs/{run_id}/trajectory"

    def media_name(m: dict[str, Any]) -> str:
        name = m.get("name")
        if name:
            return name
        return Path(m["path"]).name

    media = [
        {
            "kind": m.get("kind", "video"),
            "path": m.get("path"),
            "name": media_name(m),
            "url": media_url(m["path"]),
            "mime_type": m.get("mime_type"),
            "start_t_rel": m.get("start_t_rel"),
            "end_t_rel": m.get("end_t_rel"),
        }
        for m in manifest.get("media", [])
        if m.get("path")
    ]
    curves = [
        {
            "name": c.get("name"),
            "url": curve_url(c["name"]),
            "sample_count": c.get("sample_count"),
            "start_t_rel": c.get("start_t_rel"),
            "end_t_rel": c.get("end_t_rel"),
        }
        for c in manifest.get("curves", [])
        if c.get("name")
    ]
    trajectory = manifest.get("trajectory") or manifest.get("robot_trajectory")
    trajectory_out = None
    if trajectory and trajectory.get("path"):
        trajectory_out = {
            "url": trajectory_url(),
            "sample_count": trajectory.get("sample_count"),
            "start_t_rel": trajectory.get("start_t_rel"),
            "end_t_rel": trajectory.get("end_t_rel"),
        }

    events, _ = get_events(run_id, limit=10_000)
    tracks = sorted({e.track for e in events})

    return {
        "run_id": run_id,
        "duration_sec": float(duration),
        "media": media,
        "curves": curves,
        "trajectory": trajectory_out,
        "sandbox_states": manifest.get("sandbox_states", []),
        "tracks": tracks,
    }


def get_curve_samples(run_id: str, curve_name: str) -> list[dict[str, Any]]:
    manifest = _load_manifest(run_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    for curve in manifest.get("curves", []):
        if curve.get("name") == curve_name:
            path = _run_dir(run_id) / curve.get("path", "")
            return _read_jsonl(path)
    raise HTTPException(status_code=404, detail=f"Curve {curve_name} not found")


def get_trajectory_samples(run_id: str) -> list[dict[str, Any]]:
    manifest = _load_manifest(run_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    trajectory = manifest.get("trajectory") or manifest.get("robot_trajectory")
    if not trajectory or not trajectory.get("path"):
        raise HTTPException(status_code=404, detail="Trajectory not found")
    path = _run_dir(run_id) / trajectory["path"]
    return _read_jsonl(path)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        raise HTTPException(status_code=404, detail="Sample file not found")
    return samples
