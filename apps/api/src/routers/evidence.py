"""Evidence router — run-level evidence graphs and module evidence endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.schemas import (
    EvidenceGraph,
    HowRecovery,
    MemoryEvent,
    ProviderRouteTrace,
    SandboxDecision,
)
from services import evidence_graph

router = APIRouter(prefix="/runs", tags=["evidence"])


@router.get("/{run_id}/evidence", response_model=EvidenceGraph)
def get_run_evidence(run_id: str):
    try:
        return evidence_graph.build_evidence_graph(run_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/failures/{failure_id}/evidence", response_model=EvidenceGraph)
def get_failure_evidence(run_id: str, failure_id: str):
    try:
        return evidence_graph.build_evidence_graph(run_id, focus_event_id=failure_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/sandbox/decisions", response_model=list[SandboxDecision])
def get_sandbox_decisions(run_id: str):
    return evidence_graph.get_sandbox_decisions(run_id)


@router.get("/{run_id}/memory/events", response_model=list[MemoryEvent])
def get_memory_events(run_id: str):
    return evidence_graph.get_memory_events(run_id)


@router.get("/{run_id}/provider/traces", response_model=list[ProviderRouteTrace])
def get_provider_traces(run_id: str):
    return evidence_graph.get_provider_route_traces(run_id)


@router.get("/{run_id}/how/recoveries", response_model=list[HowRecovery])
def get_how_recoveries(run_id: str):
    return evidence_graph.get_how_recoveries(run_id)
