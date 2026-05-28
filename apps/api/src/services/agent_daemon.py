"""rosclaw-agent-daemon — minimal viable runtime connector.

Publishes heartbeat and agent events to an in-memory EventBus.
In production this would connect to the actual ROSClaw Runtime.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AgentEvent:
    event_id: str
    robot_id: str
    mission_id: str | None
    timestamp: float
    type: str
    source: str
    payload: dict[str, Any]


class EventBus:
    """In-memory pub/sub event bus for agent/skill/safety/heuristic events."""

    _instance: "EventBus | None" = None

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subs: dict[str, list[Callable[[AgentEvent], Any]]] = {}
            cls._instance._history: list[AgentEvent] = []
        return cls._instance

    def subscribe(self, topic_pattern: str, callback: Callable[[AgentEvent], Any]) -> None:
        if topic_pattern not in self._subs:
            self._subs[topic_pattern] = []
        self._subs[topic_pattern].append(callback)

    def publish(self, event: AgentEvent) -> None:
        self._history.append(event)
        if len(self._history) > 10_000:
            self._history = self._history[-10_000:]

        topic = event.type
        for pattern, callbacks in self._subs.items():
            if self._match(pattern, topic):
                for cb in callbacks:
                    try:
                        cb(event)
                    except Exception:
                        pass

    def _match(self, pattern: str, topic: str) -> bool:
        if pattern == "*" or pattern == "*.*":
            return True
        if pattern.endswith(".*"):
            return topic.startswith(pattern[:-1])
        return pattern == topic

    def get_history(self, topic_pattern: str = "*", limit: int = 100) -> list[AgentEvent]:
        matching = [e for e in self._history if self._match(topic_pattern, e.type)]
        return matching[-limit:]


@dataclass
class RobotRuntimeState:
    robot_id: str
    online: bool = False
    last_heartbeat: float = 0.0
    active_tasks: int = 0
    error_count: int = 0
    bridge_connected: bool = False
    daemon_connected: bool = False
    topics: list[str] = field(default_factory=list)


class AgentDaemon:
    """Minimal agent daemon that simulates a real runtime connector."""

    def __init__(self, robot_id: str):
        self.robot_id = robot_id
        self.bus = EventBus()
        self.state = RobotRuntimeState(robot_id=robot_id)
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        self._publish("agent.daemon_started", {"robot_id": self.robot_id})

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.state.online = False
        self._publish("agent.daemon_stopped", {"robot_id": self.robot_id})

    async def _heartbeat_loop(self) -> None:
        while self._running:
            self.state.last_heartbeat = time.time()
            self.state.online = True
            self.state.daemon_connected = True
            self.state.bridge_connected = True
            self._publish("agent.heartbeat", {
                "robot_id": self.robot_id,
                "online": True,
                "active_tasks": self.state.active_tasks,
                "error_count": self.state.error_count,
            })
            await asyncio.sleep(5.0)

    def emit_task_started(self, mission_id: str, skill: str, args: dict[str, Any] | None = None) -> None:
        self.state.active_tasks += 1
        self._publish("agent.task_started", {
            "robot_id": self.robot_id,
            "mission_id": mission_id,
            "skill": skill,
            "arguments": args or {},
        })

    def emit_task_completed(self, mission_id: str, skill: str, result: dict[str, Any] | None = None) -> None:
        self.state.active_tasks = max(0, self.state.active_tasks - 1)
        self._publish("agent.task_completed", {
            "robot_id": self.robot_id,
            "mission_id": mission_id,
            "skill": skill,
            "result": result or {},
        })

    def emit_error(self, mission_id: str | None, error_type: str, message: str) -> None:
        self.state.error_count += 1
        self._publish("agent.error", {
            "robot_id": self.robot_id,
            "mission_id": mission_id,
            "error_type": error_type,
            "message": message,
        })

    def emit_skill_event(self, skill_name: str, event_subtype: str, payload: dict[str, Any]) -> None:
        self._publish(f"skill.{event_subtype}", {
            "robot_id": self.robot_id,
            "skill_name": skill_name,
            **payload,
        })

    def emit_safety_event(self, rule_id: str, event_subtype: str, payload: dict[str, Any]) -> None:
        self._publish(f"safety.{event_subtype}", {
            "robot_id": self.robot_id,
            "rule_id": rule_id,
            **payload,
        })

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        event = AgentEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            robot_id=self.robot_id,
            mission_id=payload.get("mission_id"),
            timestamp=time.time(),
            type=event_type,
            source="rosclaw-agent-daemon",
            payload=payload,
        )
        self.bus.publish(event)


_daemon_registry: dict[str, AgentDaemon] = {}


def get_or_create_daemon(robot_id: str) -> AgentDaemon:
    if robot_id not in _daemon_registry:
        _daemon_registry[robot_id] = AgentDaemon(robot_id)
    return _daemon_registry[robot_id]


def get_daemon(robot_id: str) -> AgentDaemon | None:
    return _daemon_registry.get(robot_id)


def list_daemons() -> list[str]:
    return list(_daemon_registry.keys())
