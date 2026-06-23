"""Export job router."""

from __future__ import annotations

import zipfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from rosclaw_dashboard.core.config import settings
from rosclaw_dashboard.models.database import get_db
from rosclaw_dashboard.models.schemas import ExportJobCreate, ExportJobListResponse, ExportJobStatus
from rosclaw_dashboard.services import export_jobs

router = APIRouter(prefix="/export", tags=["export"])


@router.post("", response_model=ExportJobStatus, status_code=202)
def create_export(
    req: ExportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = export_jobs.create_job(db, req)
    return export_jobs.queue_job(job, background_tasks)


@router.get("/{job_id}", response_model=ExportJobStatus)
def get_export(job_id: str, db: Session = Depends(get_db)):
    job = export_jobs.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return export_jobs._to_status(job)


@router.get("", response_model=ExportJobListResponse)
def list_exports(
    run_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total = export_jobs.list_jobs(db, run_id=run_id, limit=limit, offset=offset)
    return ExportJobListResponse(
        jobs=[export_jobs._to_status(job) for job in rows],
        total=total,
    )


@router.get("/{job_id}/download")
def download_export(job_id: str, db: Session = Depends(get_db)):
    job = export_jobs.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    if job.state != "completed" or not job.result_path:
        raise HTTPException(status_code=400, detail="Export not ready")

    source = Path(job.result_path)
    if not source.exists():
        raise HTTPException(status_code=404, detail="Export package missing")

    if source.is_file():
        return FileResponse(source, filename=source.name)

    zip_path = source.with_suffix(".zip")
    if not zip_path.exists():
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in source.rglob("*"):
                if file.is_file():
                    zf.write(file, arcname=file.relative_to(source))
    return FileResponse(zip_path, filename=f"{job_id}.zip")
