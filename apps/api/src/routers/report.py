"""Acceptance report router."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from models.schemas import AcceptanceReport, AcceptanceReportResponse
from services.report_generator import generate_acceptance_report, get_report_path

router = APIRouter(prefix="/runs", tags=["reports"])


@router.post("/{run_id}/report", response_model=AcceptanceReportResponse)
def create_report(run_id: str):
    try:
        report = generate_acceptance_report(run_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    download_url = f"/api/runs/{run_id}/report/download"
    return AcceptanceReportResponse(report=report, download_url=download_url)


@router.get("/{run_id}/report", response_model=AcceptanceReportResponse)
def get_report(run_id: str):
    path = get_report_path(run_id, "report.json")
    if path is None:
        raise HTTPException(status_code=404, detail="Report not found; generate it first")
    import json
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    from models.schemas import AcceptanceReport
    report = AcceptanceReport(**data)
    download_url = f"/api/runs/{run_id}/report/download"
    return AcceptanceReportResponse(report=report, download_url=download_url)


@router.get("/{run_id}/report/download")
def download_report(run_id: str):
    path = get_report_path(run_id, "bundle.zip")
    if path is None:
        raise HTTPException(status_code=404, detail="Report not found; generate it first")
    return FileResponse(path, filename=f"{run_id}_acceptance_report.zip", media_type="application/zip")
