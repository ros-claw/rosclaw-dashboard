"""Runs router — practice run index, events, replay manifest and media."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from rosclaw_dashboard.models.database import get_db
from rosclaw_dashboard.models.schemas import (
    EventFilter,
    EventsResponse,
    FailuresResponse,
    FailureSummary,
    ReplayManifest,
    RunDetail,
    RunListResponse,
    RunSummary,
    TraceEvent,
    TraceTrack,
)
from rosclaw_dashboard.services import run_indexer
from rosclaw_dashboard.services.agent_daemon import AgentEvent, EventBus

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=RunListResponse)
def list_runs(
    status: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    runs, total = run_indexer.list_runs(db, status=status, limit=limit, offset=offset)
    return RunListResponse(runs=runs, total=total)


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: str, db: Session = Depends(get_db)):
    try:
        return run_indexer.get_run(db, run_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/events", response_model=EventsResponse)
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
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    events, total = run_indexer.get_events(
        run_id,
        track=track,
        severity=severity,
        type=type,
        entity=entity,
        tag=tag,
        start_t_rel=start_t_rel,
        end_t_rel=end_t_rel,
        q=q,
        limit=limit,
        offset=offset,
    )
    return EventsResponse(
        run_id=run_id,
        events=events,
        total=total,
        next_cursor=str(offset + len(events)) if offset + len(events) < total else None,
    )


@router.post("/{run_id}/events/filter", response_model=EventsResponse)
def filter_events(run_id: str, filt: EventFilter):
    events, total = run_indexer.get_events(
        run_id,
        track=filt.track,
        severity=filt.severity,
        type=filt.type,
        entity=filt.entity,
        tag=filt.tag,
        start_t_rel=filt.start_t_rel,
        end_t_rel=filt.end_t_rel,
        q=filt.q,
    )
    return EventsResponse(run_id=run_id, events=events, total=total)


@router.get("/{run_id}/events/search", response_model=EventsResponse)
def search_related(
    run_id: str,
    event_id: str,
    window_sec: float = Query(5.0, ge=0.0),
):
    related = run_indexer.search_related(run_id, event_id, window_sec=window_sec)
    return EventsResponse(run_id=run_id, events=related, total=len(related))


@router.get("/{run_id}/failures", response_model=FailuresResponse)
def get_failures(run_id: str):
    events = run_indexer.get_failures(run_id)
    failures = [
        FailureSummary(
            id=e.id,
            t_rel=e.t_rel,
            title=e.title,
            summary=e.summary,
            severity=e.severity,
            track=e.track,
        )
        for e in events
    ]
    return FailuresResponse(run_id=run_id, failures=failures)


@router.get("/{run_id}/replay", response_model=ReplayManifest)
def get_replay(run_id: str):
    data = run_indexer.get_replay_manifest(run_id)
    return ReplayManifest(**data)


def _resolve_run_file(run_id: str, relative_path: str) -> Path:
    run_dir = run_indexer._practice_dir() / run_id
    target = (run_dir / relative_path).resolve()
    run_dir_resolved = run_dir.resolve()
    try:
        target.relative_to(run_dir_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid media path")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return target


@router.get("/{run_id}/media/{path:path}")
def serve_media(run_id: str, path: str):
    target = _resolve_run_file(run_id, path)
    return FileResponse(target)


@router.get("/{run_id}/curves/{curve_name}")
def serve_curve(run_id: str, curve_name: str):
    samples = run_indexer.get_curve_samples(run_id, curve_name)
    return samples


@router.get("/{run_id}/trajectory")
def serve_trajectory(run_id: str):
    samples = run_indexer.get_trajectory_samples(run_id)
    return samples


# ── Live trace streaming ─────────────────────────────────────────────────────

_LIVE_RUN_ID = "__live__"
_LIVE_CLIENTS: list[WebSocket] = []


def _infer_track(event_type: str) -> TraceTrack:
    if event_type.startswith("agent.heartbeat"):
        return "runtime"
    prefix = event_type.split(".")[0]
    mapping: dict[str, TraceTrack] = {
        "task": "task",
        "skill": "agent",
        "tool": "tool",
        "provider": "provider",
        "sandbox": "sandbox",
        "runtime": "runtime",
        "robot": "robot",
        "critic": "critic",
        "memory": "memory",
        "failure": "failure",
        "safety": "failure",
    }
    return mapping.get(prefix, "auto")


def _infer_severity(event_type: str, payload: dict[str, Any]) -> str:
    if "failure" in event_type or "safety" in event_type or "error" in event_type:
        return "failure"
    if "warn" in event_type or payload.get("level") == "warning":
        return "warning"
    return payload.get("severity") or payload.get("level") or "info"


def _agent_event_to_trace(event: AgentEvent, start_ts: float) -> TraceEvent:
    t_rel = max(0.0, event.timestamp - start_ts)
    track = _infer_track(event.type)
    severity = _infer_severity(event.type, event.payload)
    title = event.payload.get("title") or event.type
    summary = event.payload.get("summary") or event.payload.get("message")
    entity = (
        event.payload.get("entity")
        or event.payload.get("robot_id")
        or event.robot_id
    )
    return TraceEvent(
        id=event.event_id,
        run_id=_LIVE_RUN_ID,
        ts=event.timestamp,
        t_rel=t_rel,
        source=event.source,
        type=event.type,
        track=track,
        severity=severity,
        title=title,
        summary=summary,
        entity=entity,
        payload=event.payload,
        links=None,
        tags=[event.type.split(".")[0]] if "." in event.type else None,
    )


def _broadcast_live(event: AgentEvent) -> None:
    if not _LIVE_CLIENTS:
        return
    now = time.time()
    trace = _agent_event_to_trace(event, now)
    data = trace.model_dump_json()
    for client in list(_LIVE_CLIENTS):
        try:
            asyncio.create_task(client.send_text(data))
        except Exception:
            pass


_live_bus = EventBus()
_live_bus.subscribe("*.*", _broadcast_live)
_live_bus.subscribe("agent.*", _broadcast_live)
_live_bus.subscribe("skill.*", _broadcast_live)
_live_bus.subscribe("safety.*", _broadcast_live)
_live_bus.subscribe("heuristic.*", _broadcast_live)


@router.websocket("/live")
async def live_trace_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    _LIVE_CLIENTS.append(websocket)
    start_ts = time.time()
    try:
        await websocket.send_text(
            json.dumps({"type": "live_start", "run_id": _LIVE_RUN_ID, "start_ts": start_ts})
        )
        while True:
            message = await websocket.receive_text()
            try:
                msg = json.loads(message)
                action = msg.get("action")
                if action == "ping":
                    await websocket.send_text(
                        json.dumps({"type": "pong", "timestamp": msg.get("timestamp")})
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _LIVE_CLIENTS:
            _LIVE_CLIENTS.remove(websocket)
