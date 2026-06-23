"""Tests for live-to-offline switch."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from rosclaw_dashboard.adapters.eventbus import InMemoryEventBusAdapter
from rosclaw_dashboard.adapters.practice import LocalPracticeStoreAdapter
from rosclaw_dashboard.contracts import RosclawEventEnvelope
from rosclaw_dashboard.services.live_session_manager import LiveSessionManager


@pytest.fixture
def isolated_manager(tmp_path: Path, monkeypatch):
    """Provide a fresh live session manager backed by in-memory bus and temp store."""
    monkeypatch.setenv("ROSCLAW_PRACTICE_DIR", str(tmp_path))
    original = LiveSessionManager._instance
    LiveSessionManager._instance = None
    manager = LiveSessionManager(
        event_bus=InMemoryEventBusAdapter(),
        practice_store=LocalPracticeStoreAdapter(),
    )
    manager._bus.connect()
    manager._bus.subscribe("*", manager._on_bus_event)
    yield manager
    LiveSessionManager._instance = original


@pytest.mark.asyncio
async def test_close_session_persists_run(isolated_manager: LiveSessionManager, tmp_path: Path):
    manager = isolated_manager
    row = manager.create_session(robot_id="r1", task="live pick")
    session_id = row.session_id

    envelope = RosclawEventEnvelope(
        event_id="evt_live_001",
        source="sandbox",
        type="sandbox.action.blocked",
        ts=1716900003.0,
        payload={"robot_id": "r1", "reason": "boundary"},
    )
    manager._bus.publish(envelope)

    # Drain the queue deterministically before closing.
    await manager._tick()
    assert len(manager._sessions[session_id].events) == 1

    closed = await manager.close_session(session_id)
    assert closed is not None
    assert closed.status == "offline"
    offline_run_id = closed.offline_run_id
    assert offline_run_id

    run_dir = tmp_path / offline_run_id
    assert run_dir.exists()
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "timeline.jsonl").exists()

    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["source"] == "live_session"
    assert manifest["session_id"] == session_id
