"""Tests for dashboard contract layer."""

import pytest

from rosclaw_dashboard.contracts import (
    ModuleMode,
    ModuleStatus,
    RosclawEventEnvelope,
    event_envelope_to_trace_event,
    validate_envelope,
)


def test_module_mode_literal_values():
    # ModuleMode is a Literal; the schema values must match the spec.
    allowed = {"real", "mock", "fixture", "rule_based", "unavailable", "degraded"}
    assert set(ModuleMode.__args__) == allowed  # type: ignore[attr-defined]


def test_module_status_schema():
    status = ModuleStatus(
        name="dashboard",
        status="healthy",
        mode="real",
        endpoint="/api/status",
        message="ok",
        evidence={"missions": 3},
    )
    dumped = status.model_dump()
    assert dumped["name"] == "dashboard"
    assert dumped["mode"] == "real"


def test_validate_envelope():
    raw = {
        "event_id": "evt_001",
        "source": "sandbox",
        "type": "SandboxActionBlocked",
        "ts": 1716900003.0,
        "payload": {"decision": "BLOCK", "risk_score": 0.85},
    }
    envelope = validate_envelope(raw)
    assert isinstance(envelope, RosclawEventEnvelope)
    assert envelope.source == "sandbox"
    assert envelope.payload["decision"] == "BLOCK"


def test_event_envelope_to_trace_event_maps_sandbox_failure():
    envelope = RosclawEventEnvelope(
        event_id="evt_001",
        source="firewall",
        type="SandboxActionBlocked",
        ts=1716900003.0,
        payload={
            "decision": "BLOCK",
            "reason": "workspace_boundary",
            "risk_score": 0.85,
            "robot_id": "ur5e_table_01",
        },
    )
    trace = event_envelope_to_trace_event(envelope, run_id="run_001", t_rel=3.0)
    assert trace.run_id == "run_001"
    assert trace.track == "sandbox"
    assert trace.severity == "error"
    assert trace.entity == "ur5e_table_01"


def test_event_envelope_to_trace_event_maps_provider():
    envelope = RosclawEventEnvelope(
        event_id="evt_002",
        source="provider",
        type="provider.inference.completed",
        ts=1716900004.0,
        payload={"provider": "qwen-vla", "latency_ms": 42},
    )
    trace = event_envelope_to_trace_event(envelope, run_id="run_001", t_rel=4.0)
    assert trace.track == "provider"
    assert trace.severity == "success"
    assert trace.payload["provider"] == "qwen-vla"
