"""System status endpoint — aggregates health of all ROSClaw subsystems."""

import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rosclaw_dashboard.adapters.eventbus import JsonlTailAdapter
from rosclaw_dashboard.adapters.practice import LocalPracticeStoreAdapter
from rosclaw_dashboard.core.config import settings
from rosclaw_dashboard.models.database import get_db, Robot, Mission, MemoryEntry
from rosclaw_dashboard.models.schemas import ModuleMode, ModuleStatus
from rosclaw_dashboard.services.agent_daemon import EventBus, list_daemons
from rosclaw_dashboard.services import run_indexer

router = APIRouter(prefix="/status", tags=["status"])


def _adapter_mode(name: str) -> tuple[ModuleMode, dict]:
    if name == "event_bus":
        adapter = JsonlTailAdapter(settings.events_dir)
        adapter.connect()
        return adapter.mode, adapter.health()  # type: ignore[return-value]
    if name == "practice":
        adapter = LocalPracticeStoreAdapter()
        return adapter.mode, adapter.health()  # type: ignore[return-value]
    return "mock", {}


def _module_status(
    name: str,
    mode: ModuleMode,
    healthy: bool,
    detail: dict | None = None,
    endpoint: str | None = None,
    message: str | None = None,
) -> dict:
    return {
        "name": name,
        "status": "healthy" if healthy else "degraded",
        "mode": mode,
        "message": message,
        "endpoint": endpoint,
        "last_updated": time.time(),
        "detail": detail or {},
    }


@router.get("")
def system_status(db: Session = Depends(get_db)):
    robots = db.query(Robot).all()
    robot_ids = [r.id for r in robots]
    online_daemons = [rid for rid in list_daemons() if get_daemon_status(rid)["online"]]

    event_bus = EventBus()
    recent_events = event_bus.get_history("*", limit=1)

    runs = run_indexer.list_run_ids()
    memory_count = db.query(MemoryEntry).count()
    mission_count = db.query(Mission).count()

    event_bus_mode, event_bus_detail = _adapter_mode("event_bus")
    practice_mode, practice_detail = _adapter_mode("practice")

    modules = [
        _module_status(
            "runtime", "mock", len(online_daemons) > 0 or len(robot_ids) == 0,
            detail={"robots": len(robot_ids), "online": len(online_daemons)},
            message="Runtime bridge not connected to real ROSClaw Runtime",
        ),
        _module_status(
            "event_bus", event_bus_mode, True,
            detail={"recent_events": len(recent_events), **event_bus_detail},
            message="JSONL-tail adapter" if event_bus_mode == "real" else "In-memory event bus (no external broker configured)",
        ),
        _module_status(
            "seekdb", "fixture", memory_count > 0,
            detail={"entries": memory_count},
            message="SQLite-backed memory store",
        ),
        _module_status(
            "registry", "fixture", len(robot_ids) > 0,
            detail={"robots": len(robot_ids)},
            message="Robot registry from local SQLite",
        ),
        _module_status(
            "mcp_gateway", "mock", True,
            detail={"tools": 8},
            message="MCP tools served over HTTP, no stdio/SSE MCP server",
        ),
        _module_status(
            "provider_router", "mock", True,
            detail={"providers": 6},
            message="Provider registry is mock/random metrics",
        ),
        _module_status(
            "sandbox", "fixture", len(runs) > 0,
            detail={"runs": len(runs)},
            message="Sandbox decisions from fixture/heuristic only",
        ),
        _module_status(
            "practice", practice_mode, practice_detail.get("exists", False) or len(runs) > 0,
            detail=practice_detail,
            message="Practice runs loaded from local filesystem fixtures",
        ),
        _module_status(
            "memory", "rule_based", True,
            detail={"entries": memory_count},
            message="Memory explain/recovery is rule-based",
        ),
        _module_status(
            "dashboard", "real", True,
            detail={"missions": mission_count},
            message="Dashboard UI and APIs are live",
        ),
    ]

    overall = "healthy" if all(m["status"] == "healthy" for m in modules) else "degraded"

    return {
        "overall": overall,
        "service": "rosclaw-api",
        "version": "0.1.0",
        "modules": modules,
    }


def get_daemon_status(robot_id: str) -> dict:
    from rosclaw_dashboard.services.agent_daemon import get_daemon
    import time
    daemon = get_daemon(robot_id)
    if daemon is None:
        return {"robot_id": robot_id, "online": False, "daemon_connected": False}
    state = daemon.state
    is_online = state.online and (time.time() - state.last_heartbeat) < 15.0
    return {"robot_id": robot_id, "online": is_online, "daemon_connected": state.daemon_connected}
