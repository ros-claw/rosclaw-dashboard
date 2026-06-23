"""In-memory EventBus adapter backed by the existing agent daemon EventBus."""

from typing import Any, Callable

from rosclaw_dashboard.contracts import RosclawEventEnvelope
from rosclaw_dashboard.services.agent_daemon import AgentEvent, EventBus


class InMemoryEventBusAdapter:
    """Adapter wrapping the singleton in-memory EventBus used by demos/tests."""

    name = "in_memory"
    mode = "mock"

    def __init__(self) -> None:
        self._bus = EventBus()
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def subscribe(
        self,
        topic_pattern: str,
        callback: Callable[[RosclawEventEnvelope], Any],
    ) -> None:
        def _wrapper(agent_event: AgentEvent) -> None:
            envelope = RosclawEventEnvelope(
                event_id=agent_event.event_id,
                trace_id=agent_event.payload.get("trace_id"),
                run_id=agent_event.payload.get("run_id"),
                source=agent_event.source,
                type=agent_event.type,
                ts=agent_event.timestamp,
                severity=agent_event.payload.get("severity", "info"),
                payload=agent_event.payload,
            )
            callback(envelope)

        self._bus.subscribe(topic_pattern, _wrapper)

    def publish(self, envelope: RosclawEventEnvelope) -> None:
        agent_event = AgentEvent(
            event_id=envelope.event_id,
            robot_id=(envelope.payload or {}).get("robot_id", ""),
            mission_id=(envelope.payload or {}).get("mission_id"),
            timestamp=envelope.ts,
            type=envelope.type,
            source=envelope.source,
            payload=envelope.payload or {},
        )
        self._bus.publish(agent_event)

    def health(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "subscribers": len(self._bus._subs),
            "history_size": len(self._bus._history),
        }
