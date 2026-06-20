"""Tests for status, MCP, memory explain, How recovery and Forge endpoints."""

import pytest


@pytest.mark.asyncio
async def test_system_status(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "rosclaw-api"
    assert data["overall"] in {"healthy", "degraded"}
    names = {m["name"] for m in data["modules"]}
    assert {
        "runtime", "event_bus", "seekdb", "registry", "mcp_gateway",
        "provider_router", "sandbox", "practice", "memory", "dashboard",
    }.issubset(names)


@pytest.mark.asyncio
async def test_mcp_tools_list(client):
    resp = client.get("/api/mcp/tools")
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    names = {t["name"] for t in tools}
    assert {
        "list_robots", "list_providers", "run_sandbox_task",
        "query_memory", "explain_failure", "compile_asset_bundle",
    }.issubset(names)


@pytest.mark.asyncio
async def test_mcp_call_list_robots(client):
    resp = client.post("/api/mcp/call", json={"tool": "list_robots", "arguments": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "robots" in data["data"]


@pytest.mark.asyncio
async def test_mcp_call_explain_failure(client, run_id):
    resp = client.post("/api/mcp/call", json={
        "tool": "explain_failure",
        "arguments": {"run_id": run_id},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["failure"]["id"] == "evt_failure_001"


@pytest.mark.asyncio
async def test_mcp_call_compile_asset_bundle(client):
    resp = client.post("/api/mcp/call", json={
        "tool": "compile_asset_bundle",
        "arguments": {"sdk_doc": "A simple sensor SDK", "target": "mcp_server"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["target"] == "mcp_server"


@pytest.mark.asyncio
async def test_memory_explain(client, run_id):
    resp = client.post("/api/memory/explain", json={
        "question": "What happened?",
        "run_id": run_id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["episode_id"] == run_id
    assert "failure" in data["answer"].lower()
    assert data["recovery_suggestion"]
    assert data["confidence"] > 0


@pytest.mark.asyncio
async def test_how_recovery(client, run_id):
    resp = client.post("/api/how/recovery", json={"run_id": run_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["failure_event_id"] == "evt_failure_001"
    assert data["recovery_hint"]
    assert "grip" in data["parameter_patch"] or "approach" in data["recovery_hint"].lower()
    assert data["confidence"] > 0


@pytest.mark.asyncio
async def test_forge_compile_mcp_server(client):
    resp = client.post("/api/forge/compile", json={
        "sdk_doc": "A simple sensor SDK with safety limits.",
        "target": "mcp_server",
        "staging": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["bundle_id"]
    assert data["target"] == "mcp_server"
    assert data["status"] == "validated"
    assert data["staging_path"]
    assert any(f["path"] == "server.py" for f in data["files"])
    assert data["validation"]["valid"] is True


@pytest.mark.asyncio
async def test_forge_compile_blocked_without_safety(client):
    resp = client.post("/api/forge/compile", json={
        "sdk_doc": "unsafe raw physical action SDK with no constraints",
        "target": "mcp_server",
        "staging": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "blocked"
    assert data["validation"]["valid"] is False


@pytest.mark.asyncio
async def test_forge_validate_endpoint(client):
    bundle = {
        "target": "mcp_server",
        "files": [
            {"path": "server.py", "content": "async def call(): # approval required\n    pass"},
            {"path": "README.md", "content": "# safe"},
            {"path": "manifest.json", "content": "{}"},
            {"path": "tests/test.py", "content": "def test(): pass"},
        ],
    }
    resp = client.post("/api/forge/validate", json={"bundle_id": "test_bundle", "bundle": bundle})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert any(c["name"] == "safety_or_firewall" and c["passed"] for c in data["checks"])


@pytest.mark.asyncio
async def test_forge_list_bundles(client):
    client.post("/api/forge/compile", json={
        "sdk_doc": "List test SDK",
        "target": "skill_package",
        "staging": False,
    })
    resp = client.get("/api/forge/bundles")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["bundles"]) >= 1
