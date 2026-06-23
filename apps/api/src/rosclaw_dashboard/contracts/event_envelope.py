"""Contract helpers for runtime event envelopes.

Schemas live in ``models.schemas``; this module provides validation and
normalization helpers used by event bus adapters.
"""

from rosclaw_dashboard.models.schemas import RosclawEventEnvelope

__all__ = ["RosclawEventEnvelope", "validate_envelope"]


def validate_envelope(data: dict) -> RosclawEventEnvelope:
    """Validate a raw dict against the runtime event envelope contract."""
    return RosclawEventEnvelope.model_validate(data)
