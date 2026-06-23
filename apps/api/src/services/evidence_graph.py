"""Evidence graph builder for runtime trace events.

Correlates trace events into a graph that can be rendered as a causal chain:
Task → Plan → Provider → Action → Sandbox → Failure → Memory → How.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from models.schemas import (
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    HowRecovery,
    MemoryEvent,
    ProviderRouteTrace,
    SandboxDecision,
    TraceEvent,
)
from services import run_indexer


def _node_from_event(event: TraceEvent) -> EvidenceNode:
    label = event.title or event.type
    return EvidenceNode(
        id=event.id,
        type=event.type,
        track=event.track,
        label=label,
        t_rel=event.t_rel,
        severity=event.severity,
        payload=event.payload or {},
    )


def _maybe(value: Any) -> Any:
    return value if value is not None else {}


def build_evidence_graph(run_id: str, focus_event_id: str | None = None) -> EvidenceGraph:
    events, _ = run_indexer.get_events(run_id, limit=10_000)
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for run {run_id}")

    events.sort(key=lambda e: e.t_rel)
    nodes = [_node_from_event(e) for e in events]
    node_ids = {n.id for n in nodes}

    edges: list[EvidenceEdge] = []

    # Temporal next edges within the run.
    for i in range(len(events) - 1):
        edges.append(EvidenceEdge(
            source=events[i].id,
            target=events[i + 1].id,
            relation="next",
        ))

    # Same-entity correlation.
    entity_events: dict[str, list[TraceEvent]] = {}
    for e in events:
        entity = e.entity or e.payload.get("robot_id") if e.payload else None
        if entity:
            entity_events.setdefault(entity, []).append(e)
    for group in entity_events.values():
        group.sort(key=lambda e: e.t_rel)
        for i in range(len(group) - 1):
            edges.append(EvidenceEdge(
                source=group[i].id,
                target=group[i + 1].id,
                relation="same_entity",
            ))

    # Explicit links declared on events.
    for e in events:
        for link_id in e.links or []:
            if link_id in node_ids:
                edges.append(EvidenceEdge(
                    source=e.id,
                    target=link_id,
                    relation="linked",
                ))

    # Focus subgraph: keep focus node, its neighbors, and events within 2 seconds.
    if focus_event_id and focus_event_id in node_ids:
        neighbor_ids = {focus_event_id}
        focus_event = next(e for e in events if e.id == focus_event_id)
        for e in events:
            if abs(e.t_rel - focus_event.t_rel) <= 2.0:
                neighbor_ids.add(e.id)
            if e.id in {focus_event.id} | set(focus_event.links or []):
                neighbor_ids.add(e.id)
        nodes = [n for n in nodes if n.id in neighbor_ids]
        edges = [e for e in edges if e.source in neighbor_ids and e.target in neighbor_ids]

    return EvidenceGraph(
        run_id=run_id,
        focus_event_id=focus_event_id,
        nodes=nodes,
        edges=edges,
    )


def get_sandbox_decisions(run_id: str) -> list[SandboxDecision]:
    events, _ = run_indexer.get_events(run_id, limit=10_000)
    decisions: list[SandboxDecision] = []
    for e in events:
        if e.track != "sandbox" and "sandbox" not in e.type.lower():
            continue
        payload = _maybe(e.payload)
        decision = (
            payload.get("decision")
            or payload.get("action")
            or ("BLOCK" if "block" in e.type.lower() else "ALLOW")
        )
        decisions.append(SandboxDecision(
            event_id=e.id,
            t_rel=e.t_rel,
            decision=decision,
            reason=payload.get("reason"),
            risk_score=payload.get("risk_score"),
            entity=e.entity or payload.get("robot_id"),
            payload=payload,
        ))
    return decisions


def get_memory_events(run_id: str) -> list[MemoryEvent]:
    events, _ = run_indexer.get_events(run_id, limit=10_000)
    memory_events: list[MemoryEvent] = []
    for e in events:
        if e.track != "memory" and "memory" not in e.type.lower():
            continue
        payload = _maybe(e.payload)
        memory_events.append(MemoryEvent(
            event_id=e.id,
            t_rel=e.t_rel,
            memory_type=payload.get("memory_type") or payload.get("type") or "unknown",
            entity=e.entity or payload.get("robot_id"),
            summary=e.summary,
            payload=payload,
        ))
    return memory_events


def get_provider_route_traces(run_id: str) -> list[ProviderRouteTrace]:
    events, _ = run_indexer.get_events(run_id, limit=10_000)
    traces: list[ProviderRouteTrace] = []
    for e in events:
        if e.track != "provider" and "provider" not in e.type.lower():
            continue
        payload = _maybe(e.payload)
        traces.append(ProviderRouteTrace(
            event_id=e.id,
            t_rel=e.t_rel,
            provider=payload.get("provider"),
            latency_ms=payload.get("latency_ms"),
            decision=payload.get("decision"),
            payload=payload,
        ))
    return traces


def get_how_recoveries(run_id: str) -> list[HowRecovery]:
    events, _ = run_indexer.get_events(run_id, limit=10_000)
    recoveries: list[HowRecovery] = []
    for e in events:
        if e.track != "auto" and "how" not in e.type.lower() and "recovery" not in e.type.lower():
            continue
        payload = _maybe(e.payload)
        recoveries.append(HowRecovery(
            event_id=e.id,
            t_rel=e.t_rel,
            recovery_type=payload.get("recovery_type") or e.type,
            suggestion=payload.get("suggestion") or payload.get("plan"),
            payload=payload,
        ))
    return recoveries
