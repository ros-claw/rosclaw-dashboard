from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from models.database import get_db, Mission, SkillRun, AgentEvent
from models.schemas import MissionCreate, MissionResponse, ExecutionTraceResponse, AgentEventResponse, SkillRunResponse

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("", response_model=list[MissionResponse])
def list_missions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    missions = db.query(Mission).offset(skip).limit(limit).all()
    return [MissionResponse.model_validate(m) for m in missions]


@router.get("/{mission_id}", response_model=MissionResponse)
def read_mission(mission_id: str, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return MissionResponse.model_validate(mission)


@router.post("", response_model=MissionResponse, status_code=201)
def create_mission(mission: MissionCreate, db: Session = Depends(get_db)):
    db_mission = Mission(**mission.model_dump())
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    return MissionResponse.model_validate(db_mission)


@router.post("/{mission_id}/pause")
def pause_mission(mission_id: str, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission.status = "paused"
    db.commit()
    return MissionResponse.model_validate(mission)


@router.post("/{mission_id}/resume")
def resume_mission(mission_id: str, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission.status = "running"
    mission.started_at = mission.started_at or datetime.utcnow()
    db.commit()
    return MissionResponse.model_validate(mission)


@router.post("/{mission_id}/abort")
def abort_mission(mission_id: str, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission.status = "aborted"
    mission.ended_at = datetime.utcnow()
    db.commit()
    return MissionResponse.model_validate(mission)


@router.get("/{mission_id}/trace", response_model=ExecutionTraceResponse)
def get_mission_trace(mission_id: str, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    events = db.query(AgentEvent).filter(AgentEvent.mission_id == mission_id).all()
    skill_runs = db.query(SkillRun).filter(SkillRun.mission_id == mission_id).all()

    return ExecutionTraceResponse(
        mission=MissionResponse.model_validate(mission),
        events=[AgentEventResponse.model_validate(e) for e in events],
        skill_runs=[SkillRunResponse.model_validate(s) for s in skill_runs],
    )
