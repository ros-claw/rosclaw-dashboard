"""Trace event contract helpers.

Convert runtime event envelopes into dashboard TraceEvents.
"""

from models.schemas import RosclawEventEnvelope, TraceEvent, TraceTrack

__all__ = ["event_envelope_to_trace_event"]


def _infer_track(source: str, event_type: str) -> TraceTrack:
    """Map a runtime source/type to a dashboard track lane."""
    source_lower = source.lower()
    type_lower = event_type.lower()

    if "failure" in type_lower or "error" in type_lower:
        return "failure"
    if source_lower in {"task", "agent", "planner"}:
        return "agent"
    if source_lower in {"tool", "mcp"}:
        return "tool"
    if source_lower in {"provider", "llm", "vlm", "skill", "critic"}:
        return "provider"
    if source_lower in {"sandbox", "firewall"}:
        return "sandbox"
    if source_lower in {"runtime", "bridge", "ros", "ros2"}:
        return "runtime"
    if source_lower in {"robot", "joint", "sensor", "actuator"}:
        return "robot"
    if source_lower in {"memory", "seekdb"}:
        return "memory"
    if source_lower in {"how", "recovery"}:
        return "auto"
    return "auto"


def _infer_severity(event_type: str) -> str:
    """Infer severity from event type keywords."""
    t = event_type.lower()
    if any(k in t for k in ("blocked", "veto", "fatal", "error", "failed")):
        return "error"
    if any(k in t for k in ("warn", "modify", "confirm", "risk")):
        return "warning"
    if any(k in t for k in ("success", "completed", "allowed")):
        return "success"
    return "info"


def event_envelope_to_trace_event(
    envelope: RosclawEventEnvelope,
    run_id: str,
    t_rel: float,
) -> TraceEvent:
    """Normalize a runtime envelope into a dashboard ``TraceEvent``.

    Parameters
    ----------
    envelope:
        Runtime event envelope.
    run_id:
        Dashboard run identifier to attach.
    t_rel:
        Relative timestamp within the run.
    """
    payload = envelope.payload or {}
    title = payload.get("title") or f"{envelope.source}.{envelope.type}"
    summary = payload.get("summary") or payload.get("message")

    return TraceEvent(
        id=envelope.event_id,
        run_id=run_id,
        ts=envelope.ts,
        t_rel=t_rel,
        source=envelope.source,
        type=envelope.type,
        track=_infer_track(envelope.source, envelope.type),
        severity=_infer_severity(envelope.type),
        title=title,
        summary=summary,
        entity=payload.get("entity") or payload.get("robot_id"),
        payload=payload,
        links=payload.get("links"),
        tags=payload.get("tags") or [envelope.source],
    )
