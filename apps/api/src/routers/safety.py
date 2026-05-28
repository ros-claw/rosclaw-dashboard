from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db, SafetyAudit, SafetyRule
from models.schemas import SafetyAuditResponse, SafetyRuleResponse

router = APIRouter(prefix="/safety", tags=["safety"])


# --- Safety Audits ---

@router.get("/audits", response_model=list[SafetyAuditResponse])
def list_audits(
    skip: int = 0,
    limit: int = 100,
    robot_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SafetyAudit)
    if robot_id:
        query = query.filter(SafetyAudit.robot_id == robot_id)
    if status:
        query = query.filter(SafetyAudit.status == status)
    audits = query.order_by(SafetyAudit.conducted_at.desc()).offset(skip).limit(limit).all()
    return [SafetyAuditResponse.model_validate(a) for a in audits]


@router.get("/audits/{audit_id}", response_model=SafetyAuditResponse)
def read_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(SafetyAudit).filter(SafetyAudit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Safety audit not found")
    return SafetyAuditResponse.model_validate(audit)


# --- Safety Rules ---

@router.get("/rules", response_model=list[SafetyRuleResponse])
def list_rules(
    skip: int = 0,
    limit: int = 100,
    robot_id: str | None = None,
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SafetyRule)
    if robot_id:
        query = query.filter(SafetyRule.robot_id == robot_id)
    if active is not None:
        query = query.filter(SafetyRule.active == active)
    rules = query.order_by(SafetyRule.created_at.desc()).offset(skip).limit(limit).all()
    return [SafetyRuleResponse.model_validate(r) for r in rules]


@router.get("/rules/{rule_id}", response_model=SafetyRuleResponse)
def read_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(SafetyRule).filter(SafetyRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Safety rule not found")
    return SafetyRuleResponse.model_validate(rule)


@router.post("/rules/{rule_id}/toggle")
def toggle_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(SafetyRule).filter(SafetyRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Safety rule not found")
    rule.active = not rule.active
    db.commit()
    return SafetyRuleResponse.model_validate(rule)
