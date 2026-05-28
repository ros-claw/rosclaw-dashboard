"""Integration test: Runtime → agent_daemon → WebSocket → dashboard client."""

import asyncio
import json
import pytest
from httpx import AsyncClient, ASGITransport

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app
from services.agent_daemon import get_or_create_daemon, EventBus


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.mark.asyncio
async def test_runtime_status_api():
    daemon = get_or_create_daemon("test_robot_001")
    await daemon.start()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await asyncio.sleep(0.1)
            resp = await client.get("/api/runtime/test_robot_001/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["robot_id"] == "test_robot_001"
            assert data["online"] is True
            assert data["daemon_connected"] is True
            assert data["bridge_connected"] is True
            assert "active_tasks" in data
            assert "error_count" in data
    finally:
        await daemon.stop()


@pytest.mark.asyncio
async def test_agent_daemon_emits_events():
    bus = EventBus()
    received = []
    bus.subscribe("agent.*", lambda e: received.append(e))

    daemon = get_or_create_daemon("test_robot_002")
    await daemon.start()
    try:
        daemon.emit_task_started("mission_001", "navigate_to", {"target": "zone_B"})
        await asyncio.sleep(0.1)
        assert len(received) >= 2
        task_events = [e for e in received if e.type == "agent.task_started"]
        assert len(task_events) == 1
        assert task_events[0].payload["skill"] == "navigate_to"
    finally:
        await daemon.stop()


@pytest.mark.asyncio
async def test_websocket_event_stream():
    from fastapi.testclient import TestClient
    client = TestClient(app)
    with client.websocket_connect("/api/events/stream") as ws:
        daemon = get_or_create_daemon("test_robot_003")
        await daemon.start()
        try:
            daemon.emit_task_completed("mission_002", "grasp_object", {"success": True})
            await asyncio.sleep(0.2)
            messages = []
            for _ in range(10):
                try:
                    msg = ws.receive_text()
                    messages.append(json.loads(msg))
                except Exception:
                    break
            task_events = [m for m in messages if m.get("type") == "agent.task_completed"]
            assert len(task_events) >= 1
            assert task_events[0]["payload"]["skill"] == "grasp_object"
        finally:
            await daemon.stop()


@pytest.mark.asyncio
async def test_runtime_list_robots():
    daemon = get_or_create_daemon("test_robot_004")
    await daemon.start()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/runtime")
            assert resp.status_code == 200
            data = resp.json()
            robot_ids = [r["robot_id"] for r in data]
            assert "test_robot_004" in robot_ids
    finally:
        await daemon.stop()


@pytest.mark.asyncio
async def test_mcap_api_still_works():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/mcap")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
