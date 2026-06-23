"""Tests for the Physical Trace Viewer run indexer and runs router."""

import pytest


@pytest.mark.asyncio
async def test_list_runs_includes_golden_fixture(client, run_id):
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    ids = [r["run_id"] for r in data["runs"]]
    assert run_id in ids


@pytest.mark.asyncio
async def test_get_run_detail(client, run_id):
    resp = client.get(f"/api/runs/{run_id}")
    assert resp.status_code == 200
    run = resp.json()
    assert run["run_id"] == run_id
    assert run["status"] == "failure"
    assert run["robot_id"] == "ur5e_table_01"
    assert run["event_count"] == 13
    assert run["failure_count"] == 1
    assert "failure" in run["tracks"]
    assert run["has_media"] is True
    assert run["has_trajectory"] is True
    assert run["has_curves"] is True
    # P0 episode structure fields
    assert run["episode_id"] == "ep_0001"
    assert run["task_id"] == "task_pick_red_cube_001"
    assert run["trace_id"] == "trace_ep_0001"
    assert run["artifact_uri"] == "rosclaw://practice/runs/golden_pick_cube_failure"
    assert run["agent_request"]["goal"] == "Pick red cube from bin A and place on conveyor"
    assert run["sandbox_result"]["decision"] == "ALLOW"
    assert run["critic_result"]["success"] is False
    assert run["memory_write_result"]["episodic_id"] == "memory_explain_evt_failure_001"


@pytest.mark.asyncio
async def test_get_run_not_found(client):
    resp = client.get("/api/runs/does_not_exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_events_sorted_and_paginated(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/events?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert len(data["events"]) == 5
    assert data["total"] == 13
    assert data["next_cursor"] == "5"
    times = [e["t_rel"] for e in data["events"]]
    assert times == sorted(times)


@pytest.mark.asyncio
async def test_filter_events_by_track(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/events?track=tool")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert all(e["track"] == "tool" for e in data["events"])


@pytest.mark.asyncio
async def test_filter_events_by_severity(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/events?severity=failure")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["events"][0]["id"] == "evt_failure_001"


@pytest.mark.asyncio
async def test_filter_events_post_body(client, run_id):
    resp = client.post(
        f"/api/runs/{run_id}/events/filter",
        json={"track": "failure", "q": "dropped"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["events"][0]["track"] == "failure"


@pytest.mark.asyncio
async def test_get_failures(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/failures")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert len(data["failures"]) == 1
    failure = data["failures"][0]
    assert failure["id"] == "evt_failure_001"
    assert failure["severity"] == "failure"
    assert failure["track"] == "failure"
    assert failure["t_rel"] == 42.5


@pytest.mark.asyncio
async def test_search_related_events_for_failure(client, run_id):
    resp = client.get(
        f"/api/runs/{run_id}/events/search",
        params={"event_id": "evt_failure_001", "window_sec": 10.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    related_ids = {e["id"] for e in data["events"]}
    # The failure links to tool_002, critic_001 and provider_002.
    assert "evt_tool_002" in related_ids
    assert "evt_critic_001" in related_ids
    assert "evt_provider_002" in related_ids
    assert "evt_failure_001" not in related_ids


@pytest.mark.asyncio
async def test_replay_manifest(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/replay")
    assert resp.status_code == 200
    manifest = resp.json()
    assert manifest["run_id"] == run_id
    assert manifest["duration_sec"] == 42.5
    assert len(manifest["media"]) == 1
    assert manifest["media"][0]["url"].endswith("media/camera_rgb.mp4")
    assert len(manifest["curves"]) == 1
    assert manifest["curves"][0]["name"] == "gripper_force"
    assert manifest["trajectory"]["url"].endswith("trajectory")
    assert "failure" in manifest["tracks"]


@pytest.mark.asyncio
async def test_serve_media(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/media/media/camera_rgb.mp4")
    assert resp.status_code == 200
    assert resp.headers["content-type"] in ("video/mp4", "application/mp4")


@pytest.mark.asyncio
async def test_serve_curve(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/curves/gripper_force")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 4
    assert data[0]["t_rel"] == 0.0


@pytest.mark.asyncio
async def test_serve_trajectory(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/trajectory")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 4
    assert data[-1]["t_rel"] == 42.5


@pytest.mark.asyncio
async def test_serve_media_path_traversal_blocked(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/media/%2e%2e/manifest.json")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_websocket_live_trace(client):
    """Live endpoint should accept connection and send a live_start message."""
    with client.websocket_connect("/api/runs/live") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "live_start"
        assert "run_id" in msg
        ws.send_json({"action": "ping", "timestamp": 12345})
        pong = ws.receive_json()
        assert pong["type"] == "pong"
        assert pong["timestamp"] == 12345
