"""Tests for EventBus adapters."""

import json
from pathlib import Path

import pytest

from rosclaw_dashboard.adapters.eventbus import InMemoryEventBusAdapter, JsonlTailAdapter
from rosclaw_dashboard.contracts import RosclawEventEnvelope


def test_in_memory_adapter_mode_is_mock():
    adapter = InMemoryEventBusAdapter()
    assert adapter.mode == "mock"


def test_in_memory_adapter_round_trips_envelope():
    adapter = InMemoryEventBusAdapter()
    adapter.connect()
    received: list[RosclawEventEnvelope] = []
    adapter.subscribe("skill.*", received.append)

    envelope = RosclawEventEnvelope(
        event_id="evt_001",
        source="sandbox",
        type="skill.plan.completed",
        ts=1716900003.0,
        payload={"robot_id": "r1"},
    )
    adapter.publish(envelope)

    assert len(received) == 1
    assert received[0].type == "skill.plan.completed"


def test_jsonl_tail_adapter_mode_real_when_dir_exists(tmp_path: Path):
    adapter = JsonlTailAdapter(tmp_path)
    adapter.connect()
    assert adapter.mode == "real"


def test_jsonl_tail_adapter_mode_unavailable_when_dir_missing():
    adapter = JsonlTailAdapter("/nonexistent/rosclaw/events")
    assert adapter.mode == "unavailable"


def test_jsonl_tail_adapter_reads_new_lines(tmp_path: Path):
    adapter = JsonlTailAdapter(tmp_path)
    adapter.connect()

    event_file = tmp_path / "runtime.jsonl"
    event_file.write_text(
        json.dumps({
            "event_id": "evt_001",
            "source": "runtime",
            "type": "runtime.heartbeat",
            "ts": 1716900001.0,
            "payload": {"robot_id": "r1"},
        }) + "\n"
    )

    new = adapter.read_new()
    assert len(new) == 1
    assert new[0].event_id == "evt_001"
    # Second read should return nothing because cursor advanced.
    assert adapter.read_new() == []


def test_jsonl_tail_adapter_dead_letters_invalid_lines(tmp_path: Path):
    adapter = JsonlTailAdapter(tmp_path)
    adapter.connect()

    event_file = tmp_path / "runtime.jsonl"
    event_file.write_text("not-json\n")

    assert adapter.read_new() == []
    assert len(adapter._dead_letters) == 1


def test_jsonl_tail_adapter_publish_appends_to_dashboard_jsonl(tmp_path: Path):
    adapter = JsonlTailAdapter(tmp_path)
    adapter.connect()

    envelope = RosclawEventEnvelope(
        event_id="evt_pub",
        source="dashboard",
        type="dashboard.note",
        ts=1716900005.0,
        payload={"note": "hello"},
    )
    adapter.publish(envelope)

    dashboard_file = tmp_path / "dashboard.jsonl"
    assert dashboard_file.exists()
    lines = dashboard_file.read_text().strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event_id"] == "evt_pub"
