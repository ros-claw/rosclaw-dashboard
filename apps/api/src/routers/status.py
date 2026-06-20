"""System status endpoint — aggregates health of all ROSClaw subsystems."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import get_db, Robot, Mission, MemoryEntry
from services.agent_daemon import EventBus, list_daemons
from services import run_indexer

router = APIRouter(prefix="/status", tags=["status"])


def _module_health(name: str, healthy: bool, detail: dict | None = None) -> dict:
    return {"name": name, "status": "healthy" if healthy else "degraded", "detail": detail or {}}


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

    modules = [
        _module_health("runtime", len(online_daemons) > 0 or len(robot_ids) == 0, {
            "robots": len(robot_ids),
            "online": len(online_daemons),
        }),
        _module_health("event_bus", True, {"recent_events": len(recent_events)}),
        _module_health("seekdb", memory_count > 0, {"entries": memory_count}),
        _module_health("registry", len(robot_ids) > 0, {"robots": len(robot_ids)}),
        _module_health("mcp_gateway", True, {"tools": 6}),
        _module_health("provider_router", True, {"providers": 6}),
        _module_health("sandbox", len(runs) > 0, {"runs": len(runs)}),
        _module_health("practice", len(runs) > 0, {"runs": len(runs)}),
        _module_health("memory", True, {"entries": memory_count}),
        _module_health("dashboard", True, {"missions": mission_count}),
    ]

    overall = "healthy" if all(m["status"] == "healthy" for m in modules) else "degraded"

    return {
        "overall": overall,
        "service": "rosclaw-api",
        "version": "0.1.0",
        "modules": modules,
    }


def get_daemon_status(robot_id: str) -> dict:
    from services.agent_daemon import get_daemon
    import time
    daemon = get_daemon(robot_id)
    if daemon is None:
        return {"robot_id": robot_id, "online": False, "daemon_connected": False}
    state = daemon.state
    is_online = state.online and (time.time() - state.last_heartbeat) < 15.0
    return {"robot_id": robot_id, "online": is_online, "daemon_connected": state.daemon_connected}
