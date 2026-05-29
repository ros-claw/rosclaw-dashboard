"""Episode / practice timeline API for mission trace and timeline data."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db, Mission, SkillRun, AgentEvent

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.get("")
def list_episodes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    missions = db.query(Mission).offset(skip).limit(limit).all()
    result = []
    for m in missions:
        skill_runs = db.query(SkillRun).filter(SkillRun.mission_id == m.id).all()
        events = db.query(AgentEvent).filter(AgentEvent.mission_id == m.id).order_by(AgentEvent.timestamp).all()
        result.append({
            "mission_id": m.id,
            "robot_id": m.robot_id,
            "agent_id": m.agent_id,
            "title": m.title,
            "status": m.status,
            "started_at": m.started_at.isoformat() if m.started_at else None,
            "ended_at": m.ended_at.isoformat() if m.ended_at else None,
            "skill_count": len(skill_runs),
            "event_count": len(events),
            "skills": [{"name": s.skill_name, "status": s.status} for s in skill_runs],
            "timeline": [{"type": e.event_type, "timestamp": e.timestamp.isoformat() if e.timestamp else None} for e in events[:20]],
        })
    return result


@router.get("/{mission_id}/trace")
def get_episode_trace(mission_id: str, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    skill_runs = db.query(SkillRun).filter(SkillRun.mission_id == mission_id).all()
    events = db.query(AgentEvent).filter(AgentEvent.mission_id == mission_id).order_by(AgentEvent.timestamp).all()

    trace = []
    trace.append({
        "stage": "agent_input",
        "label": "Agent Input",
        "description": mission.title,
        "timestamp": mission.started_at.isoformat() if mission.started_at else None,
    })
    for sr in skill_runs:
        trace.append({
            "stage": "skill_execution",
            "label": f"Skill: {sr.skill_name}",
            "status": sr.status,
            "timestamp": sr.started_at.isoformat() if sr.started_at else None,
        })
    for ev in events:
        trace.append({
            "stage": "event",
            "label": ev.event_type,
            "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
        })
    trace.append({
        "stage": "robot_execution",
        "label": "Robot Execution",
        "status": mission.status,
        "timestamp": mission.ended_at.isoformat() if mission.ended_at else None,
    })

    return {
        "mission_id": mission_id,
        "robot_id": mission.robot_id,
        "title": mission.title,
        "status": mission.status,
        "trace": trace,
    }
