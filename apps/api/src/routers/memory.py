"""Memory API — list, read, stats and explain."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db, MemoryEntry
from models.schemas import MemoryEntryResponse
from services import run_indexer

router = APIRouter(prefix="/memory", tags=["memory"])


class ExplainRequest(BaseModel):
    question: str
    run_id: str | None = None
    robot_id: str | None = None


class ExplainResponse(BaseModel):
    question: str
    answer: str
    episode_id: str | None
    failure_stage: str | None
    key_events: list[str]
    evidence_artifact: str | None
    similar_history: list[str]
    recovery_suggestion: str | None
    confidence: float


@router.get("", response_model=list[MemoryEntryResponse])
def list_memory(
    skip: int = 0,
    limit: int = 100,
    robot_id: str | None = None,
    memory_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(MemoryEntry)
    if robot_id:
        query = query.filter(MemoryEntry.robot_id == robot_id)
    if memory_type:
        query = query.filter(MemoryEntry.memory_type == memory_type)
    entries = query.order_by(MemoryEntry.timestamp.desc()).offset(skip).limit(limit).all()
    return [MemoryEntryResponse.model_validate(e) for e in entries]


@router.get("/{entry_id}", response_model=MemoryEntryResponse)
def read_memory(entry_id: str, db: Session = Depends(get_db)):
    entry = db.query(MemoryEntry).filter(MemoryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return MemoryEntryResponse.model_validate(entry)


@router.get("/stats/summary")
def memory_stats(db: Session = Depends(get_db)):
    total = db.query(MemoryEntry).count()
    by_type = {}
    for row in db.query(MemoryEntry.memory_type).distinct().all():
        by_type[row[0]] = db.query(MemoryEntry).filter(MemoryEntry.memory_type == row[0]).count()
    return {"total_entries": total, "by_type": by_type}


@router.post("/explain", response_model=ExplainResponse)
def explain_memory(req: ExplainRequest, db: Session = Depends(get_db)):
    question = req.question.lower()
    run_id = req.run_id

    if not run_id:
        runs = run_indexer.list_run_ids()
        if runs:
            run_id = runs[-1]

    failures = run_indexer.get_failures(run_id) if run_id else []
    failure = failures[-1] if failures else None

    key_events = []
    evidence_artifact = None
    failure_stage = None
    recovery_suggestion = None

    if failure:
        key_events.append(f"{failure.type}: {failure.title}")
        failure_stage = failure.track
        payload = failure.payload or {}
        evidence_artifact = payload.get("artifact_uri") or payload.get("replay_id")
        related = run_indexer.search_related(run_id, failure.id, window_sec=5.0)
        key_events.extend([f"{e.type}: {e.title}" for e in related[:5]])

        recovery_suggestion = _suggest_recovery(failure.title, failure.payload or {})
        entry = MemoryEntry(
            id=f"memory_explain_{failure.id}",
            robot_id=req.robot_id or failure.payload.get("robot_id") or "unknown",
            memory_type="episodic",
            content_json=json.dumps({
                "question": req.question,
                "run_id": run_id,
                "failure_event_id": failure.id,
                "answer": recovery_suggestion,
            }),
            source_skill="memory_explain",
            confidence=0.82,
        )
        db.merge(entry)
        db.commit()

    answer = _build_answer(question, run_id, failure, recovery_suggestion)

    similar = db.query(MemoryEntry).filter(MemoryEntry.memory_type == "episodic").limit(3).all()
    similar_history = [json.loads(e.content_json or {}).get("question", e.id) for e in similar]

    return ExplainResponse(
        question=req.question,
        answer=answer,
        episode_id=run_id,
        failure_stage=failure_stage,
        key_events=key_events,
        evidence_artifact=evidence_artifact,
        similar_history=similar_history,
        recovery_suggestion=recovery_suggestion,
        confidence=0.82,
    )


def _build_answer(question: str, run_id: str | None, failure, recovery_suggestion: str | None) -> str:
    if not failure:
        return f"No failures found for run {run_id}. Everything appears to have completed successfully."
    if "why" in question or "happened" in question or "fail" in question:
        return (
            f"Run {run_id} failed at {failure.track}: {failure.title}. "
            f"{failure.summary or ''} Suggested recovery: {recovery_suggestion or 'review parameters and retry.'}"
        )
    if "provider" in question:
        return f"The failure involved provider actions around {failure.title}; check the provider trace for details."
    if "sandbox" in question:
        return f"Sandbox result is captured in the failure event '{failure.title}'; review the replay artifact."
    return f"Run {run_id}: {failure.title}. {failure.summary or ''}"


def _suggest_recovery(title: str, payload: dict) -> str:
    title_l = title.lower()
    if "grip" in title_l or "drop" in title_l:
        return "Lower approach height and increase grip force before retrying."
    if "workspace" in title_l or "collision" in title_l:
        return "Choose an alternative target pose within the robot workspace."
    if "pid" in title_l or "oscillat" in title_l:
        return "Reduce Kp and increase Kd."
    return "Retry with more conservative parameters."
