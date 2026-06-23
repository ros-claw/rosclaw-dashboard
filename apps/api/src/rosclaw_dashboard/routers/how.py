"""How recovery — generate recovery hints from failures."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from rosclaw_dashboard.models.database import get_db, MemoryEntry
from rosclaw_dashboard.services import run_indexer

router = APIRouter(prefix="/how", tags=["how"])


class RecoveryRequest(BaseModel):
    run_id: str
    failure_event_id: str | None = None


class RecoveryResponse(BaseModel):
    run_id: str
    failure_event_id: str | None
    failure_title: str | None
    recovery_hint: str
    parameter_patch: dict
    confidence: float
    reasoning: str


@router.post("/recovery", response_model=RecoveryResponse)
def generate_recovery(req: RecoveryRequest, db: Session = Depends(get_db)):
    failures = run_indexer.get_failures(req.run_id)
    if not failures:
        raise HTTPException(status_code=404, detail="No failures found for run")

    failure = None
    if req.failure_event_id:
        failure = next((f for f in failures if f.id == req.failure_event_id), None)
    if failure is None:
        failure = failures[-1]

    payload = failure.payload or {}
    failure_type = _failure_type(failure.title, payload)
    robot_id = payload.get("robot_id") or _robot_from_run(req.run_id) or "unknown"

    # Look up previous procedural memories for the same failure type.
    prior_hints = _prior_recovery_hints(db, failure_type, robot_id)

    hint, patch = _recovery_for(failure_type, payload, prior_hints)

    reasoning_parts = [
        f"Failure type '{failure_type}' at stage '{failure.track}'.",
    ]
    if prior_hints:
        reasoning_parts.append(f"Referenced {len(prior_hints)} similar recovery memory entries.")
    related = run_indexer.search_related(req.run_id, failure.id, window_sec=5.0)
    if related:
        reasoning_parts.append(f"Considered {len(related)} related events.")
    reasoning = " ".join(reasoning_parts)

    entry = MemoryEntry(
        id=f"how_{failure.id}",
        robot_id=robot_id,
        memory_type="procedural",
        content_json=json.dumps({
            "run_id": req.run_id,
            "failure_event_id": failure.id,
            "failure_title": failure.title,
            "failure_type": failure_type,
            "recovery_hint": hint,
            "parameter_patch": patch,
        }),
        source_skill="how_recovery",
        confidence=0.85,
    )
    db.merge(entry)
    db.commit()

    return RecoveryResponse(
        run_id=req.run_id,
        failure_event_id=failure.id,
        failure_title=failure.title,
        recovery_hint=hint,
        parameter_patch=patch,
        confidence=0.85,
        reasoning=reasoning,
    )


def _failure_type(title: str, payload: dict) -> str:
    return (payload.get("failure_type") or payload.get("type") or title or "unknown").lower()


def _robot_from_run(run_id: str) -> str | None:
    manifest = run_indexer._load_manifest(run_id)
    return manifest.get("robot_id") if manifest else None


def _prior_recovery_hints(db: Session, failure_type: str, robot_id: str) -> list[str]:
    entries = (
        db.query(MemoryEntry)
        .filter(MemoryEntry.source_skill == "how_recovery")
        .order_by(MemoryEntry.timestamp.desc())
        .limit(20)
        .all()
    )
    hints = []
    for e in entries:
        try:
            content = json.loads(e.content_json or "{}")
        except json.JSONDecodeError:
            continue
        ft = content.get("failure_type", "")
        if failure_type in ft or ft in failure_type:
            hints.append(content.get("recovery_hint", ""))
    return hints[:3]


def _recovery_for(failure_type: str, payload: dict, prior_hints: list[str]) -> tuple[str, dict]:
    failure_type = (failure_type or "").lower()

    if "grip" in failure_type or "drop" in failure_type or "grasp" in failure_type:
        return (
            "Lower approach height, increase grip force, and reduce lateral velocity.",
            {"approach_z_offset_m": -0.02, "grip_force_percent": 1.15, "lateral_speed_factor": 0.7},
        )
    if "workspace" in failure_type or "collision" in failure_type or "boundary" in failure_type:
        return (
            "Retarget to a safe alternative pose and reduce approach speed.",
            {"approach_speed_factor": 0.5, "use_alternative_target": True},
        )
    if "pid" in failure_type or "oscillat" in failure_type:
        return (
            "Reduce proportional gain and increase derivative gain.",
            {"Kp_factor": 0.7, "Kd_factor": 1.3},
        )
    if "fall" in failure_type or "unstable" in failure_type or "gait" in failure_type:
        return (
            "Reduce walking speed and shorten step length.",
            {"speed_factor": 0.6, "step_length_factor": 0.8},
        )
    if "reach" in failure_type or "target" in failure_type:
        return (
            "Retarget to a closer reachable pose and slow the approach.",
            {"target_distance_factor": 0.8, "approach_speed_factor": 0.6},
        )

    if prior_hints:
        return (
            f"Apply a previously successful recovery: {prior_hints[0]}",
            {"retry_with_conservative_parameters": True},
        )

    return (
        "Review the failure context and retry with conservative parameters.",
        {"retry_with_conservative_parameters": True},
    )
