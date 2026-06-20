"""How recovery — generate recovery hints from failures."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db, MemoryEntry
from services import run_indexer

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
    failure_type = payload.get("failure_type") or failure.title

    hint, patch = _recovery_for(failure_type, payload)

    entry = MemoryEntry(
        id=f"how_{failure.id}",
        robot_id=payload.get("robot_id") or "unknown",
        memory_type="procedural",
        content_json=__import__("json").dumps({
            "run_id": req.run_id,
            "failure_event_id": failure.id,
            "failure_title": failure.title,
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
        reasoning=f"Based on failure type '{failure_type}' and related run events.",
    )


def _recovery_for(failure_type: str, payload: dict) -> tuple[str, dict]:
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
    if "fall" in failure_type or "unstable" in failure_type:
        return (
            "Reduce walking speed and shorten step length.",
            {"speed_factor": 0.6, "step_length_factor": 0.8},
        )
    return (
        "Review the failure context and retry with conservative parameters.",
        {"retry_with_conservative_parameters": True},
    )
