"""Runtime status API for live robot state."""

from fastapi import APIRouter, HTTPException

from services.agent_daemon import get_daemon, list_daemons

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("")
def list_runtime_robots():
    return [
        {
            "robot_id": rid,
            "daemon_connected": get_daemon(rid).state.daemon_connected if get_daemon(rid) else False,
        }
        for rid in list_daemons()
    ]


@router.get("/{robot_id}/status")
def get_runtime_status(robot_id: str):
    daemon = get_daemon(robot_id)
    if daemon is None:
        raise HTTPException(status_code=404, detail=f"No runtime daemon found for robot {robot_id}")

    state = daemon.state
    import time
    now = time.time()
    is_online = state.online and (now - state.last_heartbeat) < 15.0

    return {
        "robot_id": robot_id,
        "online": is_online,
        "last_heartbeat": state.last_heartbeat,
        "active_tasks": state.active_tasks,
        "error_count": state.error_count,
        "bridge_connected": state.bridge_connected,
        "daemon_connected": state.daemon_connected,
        "topics": state.topics,
    }
