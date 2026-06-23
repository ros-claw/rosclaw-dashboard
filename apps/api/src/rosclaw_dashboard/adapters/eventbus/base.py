"""EventBus adapter protocol.

Adapters let the dashboard consume events from multiple sources
(in-memory simulator, JSONL tail, Redis/NATS stream) behind a single
interface.
"""

from typing import Any, Callable, Protocol

from rosclaw_dashboard.contracts import RosclawEventEnvelope


class EventBusAdapter(Protocol):
    """Protocol for dashboard event bus adapters."""

    name: str
    mode: str  # real | mock | fixture | unavailable | degraded

    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def subscribe(
        self,
        topic_pattern: str,
        callback: Callable[[RosclawEventEnvelope], Any],
    ) -> None:
        ...

    def publish(self, envelope: RosclawEventEnvelope) -> None:
        ...

    def health(self) -> dict[str, Any]:
        ...
