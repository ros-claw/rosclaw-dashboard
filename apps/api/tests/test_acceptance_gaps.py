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
        "list_robots", "list_providers", "list_runs", "get_run_failures",
        "run_sandbox_task", "query_memory", "explain_failure", "compile_asset_bundle",
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
    assert data["episode_id"] == "ep_0001"
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
async def test_forge_bundle_detail_and_revalidate(client):
    compile_resp = client.post("/api/forge/compile", json={
        "sdk_doc": "Detail test SDK with safety limits.",
        "target": "skill_package",
        "staging": True,
    })
    assert compile_resp.status_code == 200
    bundle_id = compile_resp.json()["bundle_id"]

    detail_resp = client.get(f"/api/forge/bundles/{bundle_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["bundle_id"] == bundle_id
    assert detail["target"] == "skill_package"
    assert any(f["path"] == "skill.py" for f in detail["files"])

    reval_resp = client.post(f"/api/forge/bundles/{bundle_id}/validate")
    assert reval_resp.status_code == 200
    reval = reval_resp.json()
    assert reval["valid"] is True
    assert any(c["name"] == "required_files_present" and c["passed"] for c in reval["checks"])


@pytest.mark.asyncio
async def test_mcp_call_list_runs_and_failures(client, run_id):
    resp = client.post("/api/mcp/call", json={
        "tool": "list_runs",
        "arguments": {"limit": 10},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert any(r["run_id"] == run_id for r in data["data"]["runs"])

    resp = client.post("/api/mcp/call", json={
        "tool": "get_run_failures",
        "arguments": {"run_id": run_id},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert any(f["id"] == "evt_failure_001" for f in data["data"]["failures"])


@pytest.mark.asyncio
async def test_mcp_call_run_sandbox_task_decision(client):
    from rosclaw_dashboard.models.database import SessionLocal, Robot

    robot_resp = client.post("/api/robots", json={
        "id": "sandbox_bot",
        "name": "Sandbox Bot",
        "model": "mock",
        "eurdf_version": "v0.1.0",
    })
    assert robot_resp.status_code in {200, 201}

    try:
        resp = client.post("/api/mcp/call", json={
            "tool": "run_sandbox_task",
            "arguments": {
                "robot_id": "sandbox_bot",
                "task": "fast_move",
                "parameters": {"speed": 5.0},
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["decision"] == "BLOCK"
        assert data["data"]["risk_score"] > 0
    finally:
        db = SessionLocal()
        db.query(Robot).filter(Robot.id == "sandbox_bot").delete()
        db.commit()
        db.close()


@pytest.mark.asyncio
async def test_memory_explain_similar_history(client, run_id):
    resp = client.post("/api/memory/explain", json={
        "question": "Why did it fail?",
        "run_id": run_id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["similar_history"], list)
    assert data["confidence"] >= 0.5


@pytest.mark.asyncio
async def test_how_recovery_reasoning(client, run_id):
    resp = client.post("/api/how/recovery", json={"run_id": run_id})
    assert resp.status_code == 200
    data = resp.json()
    assert "failure type" in data["reasoning"].lower()
    assert data["failure_event_id"] == "evt_failure_001"


@pytest.mark.asyncio
async def test_safety_blocks_endpoint(client, blocked_run_id):
    resp = client.get("/api/safety/blocks")
    assert resp.status_code == 200
    data = resp.json()
    assert "blocks" in data
    assert any(b["run_id"] == blocked_run_id for b in data["blocks"])
    manifest_block = next(b for b in data["blocks"] if b["id"] == f"{blocked_run_id}_manifest")
    assert manifest_block["decision"] == "BLOCK"
    assert manifest_block["risk_score"] == 0.85
    event_block = next(b for b in data["blocks"] if b["id"] == "evt_blocked_001")
    assert event_block["action_type"] == "SandboxActionBlocked"


@pytest.mark.asyncio
async def test_run_detail_episode_fields(client, run_id):
    resp = client.get(f"/api/runs/{run_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["episode_id"] == "ep_0001"
    assert data["task_id"]
    assert data["trace_id"]
    assert data["sandbox_result"]
    assert data["agent_request"]
    assert data["provider_trace"]
    assert data["runtime_action"]
    assert data["critic_result"]
    assert data["memory_write_result"]
    assert data["artifact_uri"]
