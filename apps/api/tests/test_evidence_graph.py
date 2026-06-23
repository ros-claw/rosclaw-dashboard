"""Tests for evidence graph builder and endpoints."""

import pytest

from services.evidence_graph import (
    build_evidence_graph,
    get_how_recoveries,
    get_memory_events,
    get_provider_route_traces,
    get_sandbox_decisions,
)


@pytest.mark.asyncio
async def test_run_evidence_endpoint(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert len(data["nodes"]) > 0
    assert any(e["relation"] == "next" for e in data["edges"])


@pytest.mark.asyncio
async def test_failure_evidence_focus(client, run_id):
    failures = client.get(f"/api/runs/{run_id}/failures").json()["failures"]
    if not failures:
        pytest.skip("no failures in fixture")
    failure_id = failures[0]["id"]
    resp = client.get(f"/api/runs/{run_id}/failures/{failure_id}/evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert data["focus_event_id"] == failure_id
    assert any(n["id"] == failure_id for n in data["nodes"])


@pytest.mark.asyncio
async def test_sandbox_decisions_endpoint(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/sandbox/decisions")
    assert resp.status_code == 200
    decisions = resp.json()
    # Fixture may or may not contain sandbox decisions.
    assert isinstance(decisions, list)


@pytest.mark.asyncio
async def test_memory_events_endpoint(client, run_id):
    resp = client.get(f"/api/runs/{run_id}/memory/events")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)


@pytest.mark.asyncio
async def test_evidence_graph_functions(run_id):
    graph = build_evidence_graph(run_id)
    assert graph.run_id == run_id
    assert len(graph.nodes) > 0

    assert isinstance(get_sandbox_decisions(run_id), list)
    assert isinstance(get_memory_events(run_id), list)
    assert isinstance(get_provider_route_traces(run_id), list)
    assert isinstance(get_how_recoveries(run_id), list)
