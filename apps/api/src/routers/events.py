"""WebSocket endpoint for real-time event streaming."""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.agent_daemon import EventBus, AgentEvent

router = APIRouter(prefix="/events", tags=["events"])

_clients: list[WebSocket] = []


def _event_to_dict(event: AgentEvent) -> dict:
    return {
        "event_id": event.event_id,
        "robot_id": event.robot_id,
        "mission_id": event.mission_id,
        "timestamp": event.timestamp,
        "type": event.type,
        "source": event.source,
        "payload": event.payload,
    }


def _broadcast(event: AgentEvent) -> None:
    if not _clients:
        return
    data = json.dumps(_event_to_dict(event))
    for client in list(_clients):
        try:
            asyncio.create_task(client.send_text(data))
        except Exception:
            pass


_bus = EventBus()
_bus.subscribe("*.*", _broadcast)
_bus.subscribe("agent.*", _broadcast)
_bus.subscribe("skill.*", _broadcast)
_bus.subscribe("safety.*", _broadcast)
_bus.subscribe("heuristic.*", _broadcast)


@router.websocket("/stream")
async def event_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.append(websocket)

    history = _bus.get_history("*", limit=50)
    for event in history:
        try:
            await websocket.send_text(json.dumps(_event_to_dict(event)))
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
                    topic = msg.get("topic", "*")
                    await websocket.send_text(json.dumps({"type": "subscribed", "topic": topic}))
                elif action == "history":
                    topic = msg.get("topic", "*")
                    limit = msg.get("limit", 50)
                    events = _bus.get_history(topic, limit)
                    await websocket.send_text(json.dumps({
                        "type": "history",
                        "topic": topic,
                        "events": [_event_to_dict(e) for e in events],
                    }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _clients:
            _clients.remove(websocket)
