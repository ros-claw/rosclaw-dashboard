"""Export job orchestration and state machine."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from rosclaw_dashboard.core.config import settings
from rosclaw_dashboard.models.database import ExportJob, SessionLocal
from rosclaw_dashboard.models.schemas import ExportJobCreate, ExportJobStatus
from rosclaw_dashboard.services.exporters.failure_case_exporter import export_failure_case
from rosclaw_dashboard.services.exporters.lerobot_exporter import export_lerobot
from rosclaw_dashboard.services.exporters.rlds_exporter import export_rlds
from rosclaw_dashboard.services.exporters.skill_candidate_exporter import export_skill_candidate

EXPORTERS = {
    "rlds": export_rlds,
    "lerobot": export_lerobot,
    "failure_case": export_failure_case,
    "skill_candidate": export_skill_candidate,
}

# Tests can rebind this variable to a temporary directory.
EXPORT_DIR: Path | None = None


def _export_dir() -> Path:
    if EXPORT_DIR is not None:
        return EXPORT_DIR
    return Path(os.environ.get("ROSCLAW_EXPORT_DIR", settings.export_dir))


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def create_job(db: Session, req: ExportJobCreate) -> ExportJob:
    if req.format not in EXPORTERS:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {req.format}")

    job = ExportJob(
        job_id=str(uuid.uuid4()),
        run_id=req.run_id,
        format=req.format,
        state="queued",
        progress=0.0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> ExportJob | None:
    return db.query(ExportJob).filter(ExportJob.job_id == job_id).first()


def list_jobs(db: Session, run_id: str | None = None, limit: int = 100, offset: int = 0):
    query = db.query(ExportJob)
    if run_id:
        query = query.filter(ExportJob.run_id == run_id)
    total = query.count()
    rows = query.order_by(ExportJob.created_at.desc()).offset(offset).limit(limit).all()
    return rows, total


def _to_status(job: ExportJob) -> ExportJobStatus:
    return ExportJobStatus(
        job_id=job.job_id,
        run_id=job.run_id,
        format=job.format,
        state=job.state,
        progress=job.progress,
        result_url=f"/api/export/{job.job_id}/download" if job.state == "completed" and job.result_path else None,
        error=job.error,
        created_at=job.created_at.timestamp() if job.created_at else _now_ts(),
        updated_at=job.updated_at.timestamp() if job.updated_at else _now_ts(),
    )


async def _run_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = get_job(db, job_id)
        if job is None:
            return

        async def _update(state: str, progress: float, result: str | None = None, error: str | None = None):
            job.state = state
            job.progress = progress
            if result is not None:
                job.result_path = result
            if error is not None:
                job.error = error
            db.commit()
            await asyncio.sleep(0)

        try:
            await _update("running", 0.1)
            export_dir = _export_dir()
            export_dir.mkdir(parents=True, exist_ok=True)
            out_dir = export_dir / job.job_id
            exporter = EXPORTERS[job.format]
            package_path = exporter(job.run_id, out_dir)
            await _update("validating", 0.8)
            if not package_path.exists():
                raise RuntimeError("Exporter did not create a package")
            await _update("packaging", 0.95)
            await _update("completed", 1.0, result=str(package_path))
        except Exception as exc:
            await _update("failed", job.progress, error=str(exc))
    finally:
        db.close()


def queue_job(job: ExportJob, background_tasks: BackgroundTasks) -> ExportJobStatus:
    background_tasks.add_task(_run_job, job.job_id)
    return _to_status(job)
