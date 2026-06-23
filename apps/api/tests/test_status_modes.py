"""Tests for module mode transparency in /api/status."""

import pytest


@pytest.mark.asyncio
async def test_status_includes_module_modes(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall"] in {"healthy", "degraded"}
    assert "modules" in data

    allowed_modes = {"real", "mock", "fixture", "rule_based", "unavailable", "degraded"}
    required_modules = {
        "runtime", "event_bus", "seekdb", "registry", "mcp_gateway",
        "provider_router", "sandbox", "practice", "memory", "dashboard",
    }

    module_names = {m["name"] for m in data["modules"]}
    assert required_modules.issubset(module_names)

    for mod in data["modules"]:
        assert "mode" in mod, f"module {mod['name']} missing mode"
        assert mod["mode"] in allowed_modes
        assert "status" in mod
        assert "last_updated" in mod


@pytest.mark.asyncio
async def test_dashboard_is_real_and_others_are_not(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()

    modes = {m["name"]: m["mode"] for m in data["modules"]}
    assert modes["dashboard"] == "real"
    # At least one external module should be honest about not being real yet.
    non_real = {k for k, v in modes.items() if k != "dashboard" and v != "real"}
    assert len(non_real) >= 1
