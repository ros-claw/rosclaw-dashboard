from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from rosclaw_dashboard.models.database import get_db, SafetyAudit, SafetyRule
from rosclaw_dashboard.models.schemas import SafetyAuditResponse, SafetyRuleResponse
from rosclaw_dashboard.services import run_indexer

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


@router.get("/blocks")
def list_firewall_blocks():
    """Scan practice runs for sandbox/firewall BLOCK decisions."""
    blocks = []
    for run_id in run_indexer.list_run_ids():
        manifest = run_indexer._load_manifest(run_id) or {}
        events, _ = run_indexer.get_events(run_id, limit=10_000)
        for event in events:
            payload = event.payload or {}
            decision = payload.get("decision") or payload.get("sandbox_decision")
            if decision == "BLOCK" or event.type == "SandboxActionBlocked":
                blocks.append({
                    "id": event.id,
                    "run_id": run_id,
                    "episode_id": manifest.get("episode_id") or run_id,
                    "robot_id": event.entity or manifest.get("robot_id"),
                    "t_rel": event.t_rel,
                    "decision": "BLOCK",
                    "reason": payload.get("reason") or payload.get("blocked_reason") or event.summary,
                    "risk_score": payload.get("risk_score"),
                    "checks": payload.get("checks") or payload.get("failed_checks"),
                    "replay_id": payload.get("replay_id") or f"sandbox://{run_id}/{event.id}",
                    "action_type": payload.get("action_type") or event.type,
                })
        sandbox_result = manifest.get("sandbox_result") or {}
        if sandbox_result.get("decision") == "BLOCK":
            blocks.append({
                "id": f"{run_id}_manifest",
                "run_id": run_id,
                "episode_id": manifest.get("episode_id") or run_id,
                "robot_id": manifest.get("robot_id"),
                "t_rel": 0.0,
                "decision": "BLOCK",
                "reason": sandbox_result.get("reason"),
                "risk_score": sandbox_result.get("risk_score"),
                "checks": sandbox_result.get("checks"),
                "replay_id": sandbox_result.get("replay_id") or f"sandbox://{run_id}",
                "action_type": "sandbox_validation",
            })
    blocks.sort(key=lambda b: b["t_rel"], reverse=True)
    return {"blocks": blocks}
