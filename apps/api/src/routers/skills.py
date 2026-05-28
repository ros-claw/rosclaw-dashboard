from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db, Skill, SkillRun
from models.schemas import SkillResponse, SkillRunResponse

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillResponse])
def list_skills(skip: int = 0, limit: int = 100, robot_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Skill)
    if robot_id:
        query = query.filter(Skill.robot_id == robot_id)
    skills = query.offset(skip).limit(limit).all()
    return [SkillResponse.model_validate(s) for s in skills]


@router.get("/{skill_id}", response_model=SkillResponse)
def read_skill(skill_id: str, db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillResponse.model_validate(skill)


@router.post("/{skill_id}/run")
def run_skill(skill_id: str, mission_id: str, db: Session = Depends(get_db)):
    run = SkillRun(
        id=f"{skill_id}_{mission_id}",
        mission_id=mission_id,
        skill_name=skill_id,
        status="running",
    )
    db.merge(run)
    db.commit()
    return SkillRunResponse.model_validate(run)


@router.get("/{skill_id}/runs")
def list_skill_runs(skill_id: str, db: Session = Depends(get_db)):
    runs = db.query(SkillRun).filter(SkillRun.skill_name == skill_id).all()
    return [SkillRunResponse.model_validate(r) for r in runs]
