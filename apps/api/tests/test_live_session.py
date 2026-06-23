"""Tests for live session REST API."""

from __future__ import annotations

import pytest

from services.live_session_manager import LiveSessionManager


@pytest.fixture(autouse=True)
def _reset_live_singleton():
    """Give each test a fresh live session manager singleton."""
    LiveSessionManager._instance = None
    yield
    LiveSessionManager._instance = None


@pytest.mark.asyncio
async def test_create_and_list_sessions(client):
    resp = client.post("/api/live/sessions", json={"robot_id": "r1", "task": "pick cube"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_id"].startswith("live_")
    assert data["status"] == "live"

    resp = client.get("/api/live/sessions")
    assert resp.status_code == 200
    sessions = resp.json()["sessions"]
    assert len(sessions) >= 1
    assert any(s["session_id"] == data["session_id"] for s in sessions)


@pytest.mark.asyncio
async def test_get_session_and_attach_run(client):
    resp = client.post("/api/live/sessions", json={"robot_id": "r1"})
    session_id = resp.json()["session_id"]

    resp = client.get(f"/api/live/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["run_id"] is None

    resp = client.post(f"/api/live/{session_id}/attach-run", json={"run_id": "run_001"})
    assert resp.status_code == 200
    assert resp.json()["run_id"] == "run_001"


@pytest.mark.asyncio
async def test_close_missing_session_returns_404(client):
    resp = client.post("/api/live/nonexistent/close")
    assert resp.status_code == 404
