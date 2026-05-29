"""Runtime status API for live robot state."""

import asyncio
import json
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from services.agent_daemon import get_daemon, list_daemons, EventBus, AgentEvent

router = APIRouter(prefix="/runtime", tags=["runtime"])

# Connected WebSocket clients for runtime status streaming
_runtime_ws_clients: list[WebSocket] = []


def _status_payload(robot_id: str) -> dict:
    daemon = get_daemon(robot_id)
    if daemon is None:
        return {"robot_id": robot_id, "online": False, "daemon_connected": False}
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


def _broadcast_runtime_status(event: AgentEvent) -> None:
    if event.type != "agent.heartbeat":
        return
    robot_id = event.payload.get("robot_id")
    if not robot_id:
        return
    payload = _status_payload(robot_id)
    data = json.dumps({"type": "runtime.status", "timestamp": event.timestamp, "data": payload})
    for client in list(_runtime_ws_clients):
        try:
            asyncio.create_task(client.send_text(data))
        except Exception:
            pass


# Subscribe EventBus to push runtime status updates
_bus = EventBus()
_bus.subscribe("agent.heartbeat", _broadcast_runtime_status)


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
    return _status_payload(robot_id)


@router.websocket("/status/stream")
async def runtime_status_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    _runtime_ws_clients.append(websocket)

    # Send current snapshot for all known robots
    for rid in list_daemons():
        try:
            await websocket.send_text(json.dumps({
                "type": "runtime.status",
                "timestamp": asyncio.get_event_loop().time(),
                "data": _status_payload(rid),
            }))
        except Exception:
            break

    try:
        while True:
            message = await websocket.receive_text()
            try:
                msg = json.loads(message)
                action = msg.get("action")
                if action == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": msg.get("timestamp")}))
                elif action == "subscribe":
                    robot_id = msg.get("robot_id")
                    await websocket.send_text(json.dumps({"type": "subscribed", "robot_id": robot_id}))
                    # Send immediate snapshot for the requested robot
                    if robot_id:
                        await websocket.send_text(json.dumps({
                            "type": "runtime.status",
                            "timestamp": asyncio.get_event_loop().time(),
                            "data": _status_payload(robot_id),
                        }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _runtime_ws_clients:
            _runtime_ws_clients.remove(websocket)
