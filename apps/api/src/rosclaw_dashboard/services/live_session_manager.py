"""Live session manager — bridge runtime events to offline practice runs.

A session is a transient live trace. While ``status == "live"`` events are
streamed to WebSocket clients. When the session is closed, buffered events can
be written to disk and re-indexed as a practice run (live-to-offline).
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import WebSocket
from sqlalchemy.orm import Session

from rosclaw_dashboard.adapters.eventbus.base import EventBusAdapter
from rosclaw_dashboard.adapters.practice.base import PracticeStoreAdapter
from rosclaw_dashboard.contracts import RosclawEventEnvelope, event_envelope_to_trace_event
from rosclaw_dashboard.core.config import settings
from rosclaw_dashboard.models.database import LiveSession as LiveSessionRow, SessionLocal
from rosclaw_dashboard.models.schemas import LiveSessionResponse, TraceEvent
from rosclaw_dashboard.services import run_indexer


@dataclass
class _SessionRuntime:
    start_ts: float
    clients: list[WebSocket] = field(default_factory=list)
    events: list[TraceEvent] = field(default_factory=list)
    queue: asyncio.Queue[RosclawEventEnvelope] = field(default_factory=asyncio.Queue)
    closed: bool = False


class LiveSessionManager:
    """Singleton manager for live trace sessions."""

    _instance: LiveSessionManager | None = None

    def __new__(cls, *args: Any, **kwargs: Any) -> LiveSessionManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        event_bus: EventBusAdapter | None = None,
        practice_store: PracticeStoreAdapter | None = None,
    ) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._bus = event_bus
        self._store = practice_store
        self._sessions: dict[str, _SessionRuntime] = {}
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if self._task is not None:
            return
        if self._bus:
            self._bus.subscribe("*", self._on_bus_event)
            self._bus.connect()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._bus:
            self._bus.disconnect()

    def _on_bus_event(self, envelope: RosclawEventEnvelope) -> None:
        for rt in self._sessions.values():
            if not rt.closed:
                try:
                    rt.queue.put_nowait(envelope)
                except asyncio.QueueFull:
                    pass

    async def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._tick()
            except Exception:
                pass
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=0.5)
            except asyncio.TimeoutError:
                pass

    async def _tick(self) -> None:
        # Poll JSONL tail adapter for new lines.
        if hasattr(self._bus, "read_new"):
            try:
                new_envelopes = self._bus.read_new()
            except Exception:
                new_envelopes = []
            for envelope in new_envelopes:
                self._on_bus_event(envelope)

        # Drain per-session queues and broadcast.
        for session_id, rt in list(self._sessions.items()):
            drained: list[RosclawEventEnvelope] = []
            while not rt.queue.empty():
                try:
                    drained.append(rt.queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            for envelope in drained:
                trace = self._envelope_to_trace(envelope, session_id, rt.start_ts)
                rt.events.append(trace)
                await self._broadcast(session_id, trace.model_dump())

    def _envelope_to_trace(
        self,
        envelope: RosclawEventEnvelope,
        session_id: str,
        start_ts: float,
    ) -> TraceEvent:
        t_rel = max(0.0, envelope.ts - start_ts)
        return event_envelope_to_trace_event(
            envelope,
            run_id=session_id,
            t_rel=t_rel,
        )

    async def _broadcast(self, session_id: str, payload: dict[str, Any]) -> None:
        rt = self._sessions.get(session_id)
        if not rt:
            return
        data = json.dumps(payload, default=str)
        for client in list(rt.clients):
            try:
                await client.send_text(data)
            except Exception:
                pass

    def _db(self) -> Session:
        return SessionLocal()

    def create_session(
        self,
        robot_id: str | None = None,
        task: str | None = None,
        run_id: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> LiveSessionRow:
        session_id = f"live_{uuid.uuid4().hex[:12]}"
        db = self._db()
        row = LiveSessionRow(
            session_id=session_id,
            run_id=run_id,
            status="live",
            config_json=json.dumps(
                {
                    "robot_id": robot_id,
                    "task": task,
                    **(config or {}),
                },
                default=str,
            ),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        self._sessions[session_id] = _SessionRuntime(start_ts=time.time())
        return row

    def list_sessions(self) -> list[LiveSessionRow]:
        db = self._db()
        return db.query(LiveSessionRow).order_by(LiveSessionRow.created_at.desc()).all()

    def get_session(self, session_id: str) -> LiveSessionRow | None:
        db = self._db()
        return db.query(LiveSessionRow).filter(LiveSessionRow.session_id == session_id).first()

    def attach_run(self, session_id: str, run_id: str) -> LiveSessionRow | None:
        db = self._db()
        row = db.query(LiveSessionRow).filter(LiveSessionRow.session_id == session_id).first()
        if row is None:
            return None
        row.run_id = run_id
        db.commit()
        db.refresh(row)
        return row

    async def close_session(self, session_id: str) -> LiveSessionRow | None:
        rt = self._sessions.get(session_id)
        if rt:
            rt.closed = True

        db = self._db()
        row = db.query(LiveSessionRow).filter(LiveSessionRow.session_id == session_id).first()
        if row is None:
            return None

        row.status = "closing"
        db.commit()

        offline_run_id = row.run_id or session_id
        # Write buffered events to disk as a practice run if any were received.
        if rt and rt.events:
            await asyncio.to_thread(self._persist_run, offline_run_id, rt.events, row)

        # Re-index so the run appears in offline viewers immediately.
        try:
            await asyncio.to_thread(run_indexer.index_run, db, offline_run_id)
        except Exception:
            pass

        row.status = "offline"
        row.closed_at = datetime.utcnow()  # type: ignore[name-defined]
        row.offline_run_id = offline_run_id
        db.commit()
        db.refresh(row)

        await self._broadcast(
            session_id,
            {
                "type": "offline_ready",
                "session_id": session_id,
                "offline_run_id": offline_run_id,
            },
        )
        return row

    def _persist_run(
        self,
        run_id: str,
        events: list[TraceEvent],
        row: LiveSessionRow,
    ) -> None:
        run_dir = run_indexer._practice_dir() / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        timeline_path = run_dir / "timeline.jsonl"
        with timeline_path.open("w", encoding="utf-8") as f:
            for trace in events:
                f.write(json.dumps(trace.model_dump(), default=str) + "\n")

        manifest = {
            "run_id": run_id,
            "status": "completed",
            "robot_id": row.config_json and json.loads(row.config_json).get("robot_id"),
            "task": row.config_json and json.loads(row.config_json).get("task") or "live session",
            "started_at": events[0].ts if events else time.time(),
            "ended_at": events[-1].ts if events else time.time(),
            "duration_sec": (events[-1].t_rel if events else 0.0),
            "source": "live_session",
            "session_id": row.session_id,
        }
        with (run_dir / "manifest.json").open("w", encoding="utf-8") as f:
            json.dump(manifest, f, default=str)

    async def register_client(self, session_id: str, websocket: WebSocket) -> None:
        rt = self._sessions.setdefault(session_id, _SessionRuntime(start_ts=time.time()))
        if websocket not in rt.clients:
            rt.clients.append(websocket)
        await self._broadcast(
            session_id,
            {"type": "live_start", "session_id": session_id, "start_ts": rt.start_ts},
        )

    def unregister_client(self, session_id: str, websocket: WebSocket) -> None:
        rt = self._sessions.get(session_id)
        if not rt:
            return
        if websocket in rt.clients:
            rt.clients.remove(websocket)


# Import datetime late to satisfy the inline reference above.
from datetime import datetime  # noqa: E402,F401


def get_live_session_manager() -> LiveSessionManager:
    from rosclaw_dashboard.adapters.eventbus import InMemoryEventBusAdapter, JsonlTailAdapter
    from rosclaw_dashboard.adapters.practice import LocalPracticeStoreAdapter

    # Compose a hybrid adapter: in-memory for demos + JSONL tail for real streams.
    # The manager currently consumes one primary adapter; use JSONL tail when
    # available, otherwise fall back to in-memory.
    events_dir = Path(os.environ.get("ROSCLAW_EVENTS_DIR", settings.events_dir))
    jsonl = JsonlTailAdapter(events_dir)
    jsonl.connect()
    bus: EventBusAdapter = jsonl if jsonl.mode == "real" else InMemoryEventBusAdapter()
    bus.connect()
    store = LocalPracticeStoreAdapter()
    return LiveSessionManager(event_bus=bus, practice_store=store)
