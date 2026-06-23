"""Dashboard contract layer.

Contracts are lightweight Pydantic schemas and normalization helpers shared
between ROSClaw runtime modules and the dashboard adapters.
"""

from rosclaw_dashboard.contracts.event_envelope import RosclawEventEnvelope, validate_envelope
from rosclaw_dashboard.contracts.module_status import ModuleMode, ModuleStatus
from rosclaw_dashboard.contracts.trace_event import event_envelope_to_trace_event

__all__ = [
    "ModuleMode",
    "ModuleStatus",
    "RosclawEventEnvelope",
    "event_envelope_to_trace_event",
    "validate_envelope",
]
