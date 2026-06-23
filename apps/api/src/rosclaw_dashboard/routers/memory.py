"""Memory API — list, read, stats and explain."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from rosclaw_dashboard.models.database import get_db, MemoryEntry
from rosclaw_dashboard.models.schemas import MemoryEntryResponse
from rosclaw_dashboard.services import run_indexer

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
    robot_id = req.robot_id

    # Resolve run_id: explicit > robot recent > global recent.
    if not run_id:
        run_ids = run_indexer.list_run_ids()
        if robot_id:
            for rid in reversed(run_ids):
                manifest = run_indexer._load_manifest(rid)
                if manifest and manifest.get("robot_id") == robot_id:
                    run_id = rid
                    break
        if not run_id and run_ids:
            run_id = run_ids[-1]

    failures = run_indexer.get_failures(run_id) if run_id else []
    failure = failures[-1] if failures else None

    run_manifest = run_indexer._load_manifest(run_id) if run_id else None
    episode_id = run_manifest.get("episode_id") if run_manifest else run_id
    if not robot_id and run_manifest:
        robot_id = run_manifest.get("robot_id")
    task_id = run_manifest.get("task_id") if run_manifest else None

    key_events = []
    evidence_artifact = None
    failure_stage = None
    failure_type = None
    recovery_suggestion = None

    if failure:
        failure_stage = failure.track
        failure_type = _failure_type_from(failure.title, failure.payload)
        payload = failure.payload or {}
        key_events.append(f"{failure.type}: {failure.title}")
        evidence_artifact = payload.get("artifact_uri") or payload.get("replay_id")
        related = run_indexer.search_related(run_id, failure.id, window_sec=5.0)
        key_events.extend([f"{e.track}/{e.type}: {e.title}" for e in related[:5]])

        recovery_suggestion = _suggest_recovery(failure.title, failure.payload or {})
        entry = MemoryEntry(
            id=f"memory_explain_{failure.id}",
            robot_id=robot_id or failure.payload.get("robot_id") or "unknown",
            memory_type="episodic",
            content_json=json.dumps({
                "question": req.question,
                "run_id": run_id,
                "episode_id": episode_id,
                "failure_event_id": failure.id,
                "failure_stage": failure_stage,
                "failure_type": failure_type,
                "answer": recovery_suggestion,
            }),
            source_skill="memory_explain",
            confidence=0.82,
        )
        db.merge(entry)
        db.commit()

    # Search memory for similar history.
    similar_history = _find_similar_history(
        db,
        robot_id=robot_id,
        task_id=task_id,
        failure_type=failure_type,
        failure_stage=failure_stage,
        exclude_run_id=run_id,
        limit=5,
    )

    answer = _build_answer(
        question,
        run_id,
        episode_id,
        failure,
        failure_type,
        recovery_suggestion,
        similar_history,
        run_manifest,
    )

    confidence = _compute_confidence(
        has_failure=bool(failure),
        related_count=len(key_events),
        similar_count=len(similar_history),
        has_artifact=bool(evidence_artifact),
    )

    return ExplainResponse(
        question=req.question,
        answer=answer,
        episode_id=episode_id,
        failure_stage=failure_stage,
        key_events=key_events,
        evidence_artifact=evidence_artifact,
        similar_history=similar_history,
        recovery_suggestion=recovery_suggestion,
        confidence=confidence,
    )


def _failure_type_from(title: str, payload: dict | None) -> str | None:
    payload = payload or {}
    ft = payload.get("failure_type") or payload.get("type") or title
    return (ft or "").lower().strip() or None


def _build_answer(
    question: str,
    run_id: str | None,
    episode_id: str | None,
    failure,
    failure_type: str | None,
    recovery_suggestion: str | None,
    similar_history: list[str],
    run_manifest: dict | None,
) -> str:
    if not failure:
        return f"No failures found for run {run_id or episode_id}. Everything appears to have completed successfully."

    parts = []
    if episode_id:
        parts.append(f"Episode {episode_id}")
    elif run_id:
        parts.append(f"Run {run_id}")
    parts.append(f"failed at stage '{failure.track}': {failure.title}.")
    if failure.summary:
        parts.append(failure.summary)

    if "why" in question or "happened" in question or "fail" in question or "what" in question:
        parts.append(f"Failure type: {failure_type or 'unknown'}.")
        if run_manifest:
            sandbox = run_manifest.get("sandbox_result") or {}
            if sandbox.get("decision"):
                parts.append(f"Sandbox decision: {sandbox['decision']} (risk {sandbox.get('risk_score', 'n/a')}).")
            provider = run_manifest.get("provider_trace") or {}
            if provider.get("provider_id"):
                parts.append(f"Provider: {provider['provider_id']}.")
        if recovery_suggestion:
            parts.append(f"Suggested recovery: {recovery_suggestion}")
        if similar_history:
            parts.append(f"Similar history ({len(similar_history)} cases): {', '.join(similar_history[:3])}.")
        return " ".join(parts)

    if "provider" in question:
        return f"The failure involved provider actions around {failure.title}; check the provider trace for details."
    if "sandbox" in question:
        return f"Sandbox result is captured in the failure event '{failure.title}'; review the replay artifact."
    return " ".join(parts)


def _suggest_recovery(title: str, payload: dict) -> str:
    title_l = title.lower()
    if "grip" in title_l or "drop" in title_l or "grasp" in title_l:
        return "Lower approach height and increase grip force before retrying."
    if "workspace" in title_l or "collision" in title_l or "boundary" in title_l:
        return "Choose an alternative target pose within the robot workspace."
    if "pid" in title_l or "oscillat" in title_l:
        return "Reduce proportional gain and increase derivative gain."
    if "fall" in title_l or "unstable" in title_l or "gait" in title_l:
        return "Reduce walking speed and shorten step length."
    if "reach" in title_l or "target" in title_l:
        return "Retarget to a closer reachable pose and slow the approach."
    return "Retry with more conservative parameters."


def _find_similar_history(
    db: Session,
    robot_id: str | None,
    task_id: str | None,
    failure_type: str | None,
    failure_stage: str | None,
    exclude_run_id: str | None,
    limit: int,
) -> list[str]:
    candidates = db.query(MemoryEntry).order_by(MemoryEntry.timestamp.desc()).limit(200).all()
    scored = []
    for entry in candidates:
        try:
            content = json.loads(entry.content_json or "{}")
        except json.JSONDecodeError:
            continue
        score = 0
        desc = content.get("question") or content.get("answer") or content.get("failure_event_id") or entry.id
        if robot_id and entry.robot_id == robot_id:
            score += 2
        if task_id and content.get("task_id") == task_id:
            score += 2
        if failure_type and failure_type in (content.get("failure_type") or "").lower():
            score += 3
            desc = f"[{failure_type}] {desc}"
        if failure_stage and content.get("failure_stage") == failure_stage:
            score += 1
        if content.get("run_id") == exclude_run_id:
            continue
        if score > 0:
            scored.append((score, desc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [desc for _, desc in scored[:limit]]


def _compute_confidence(
    has_failure: bool,
    related_count: int,
    similar_count: int,
    has_artifact: bool,
) -> float:
    base = 0.5
    if has_failure:
        base += 0.15
    base += min(related_count * 0.03, 0.15)
    base += min(similar_count * 0.04, 0.15)
    if has_artifact:
        base += 0.05
    return round(min(base, 0.98), 2)
