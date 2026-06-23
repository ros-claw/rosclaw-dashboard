"""Local filesystem practice store backed by run_indexer."""

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from rosclaw_dashboard.adapters.practice.base import PracticeStoreAdapter
from rosclaw_dashboard.models.database import SessionLocal
from rosclaw_dashboard.models.schemas import ReplayManifest, RunDetail, RunSummary, TraceEvent
from rosclaw_dashboard.services import run_indexer


class LocalPracticeStoreAdapter:
    """Reads practice runs from the local ``ROSCLAW_PRACTICE_DIR``."""

    name = "local_practice"
    mode = "fixture"

    def __init__(self) -> None:
        self._db: Session | None = None

    def _get_db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def list_runs(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[RunSummary], int]:
        return run_indexer.list_runs(self._get_db(), status=status, limit=limit, offset=offset)

    def get_run(self, run_id: str) -> RunDetail:
        return run_indexer.get_run(self._get_db(), run_id)

    def read_timeline(self, run_id: str) -> list[dict[str, Any]]:
        manifest = run_indexer._load_manifest(run_id)
        if manifest is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        started_at = manifest.get("started_at") or manifest.get("start_ts") or 0.0
        events: list[dict[str, Any]] = []
        for raw in run_indexer._iter_events(run_id):
            norm = run_indexer._normalize_event(raw, run_id, float(started_at))
            events.append(TraceEvent(**norm).model_dump())
        events.sort(key=lambda e: e["t_rel"])
        return events

    def get_replay_manifest(self, run_id: str) -> ReplayManifest:
        data = run_indexer.get_replay_manifest(run_id)
        return ReplayManifest(**data)

    def validate_run(self, run_id: str) -> dict[str, Any]:
        manifest = run_indexer._load_manifest(run_id)
        if manifest is None:
            return {"valid": False, "errors": ["missing manifest"]}
        errors: list[str] = []
        if not manifest.get("run_id"):
            errors.append("missing run_id")
        if not manifest.get("task"):
            errors.append("missing task")
        if not (run_indexer._practice_dir() / run_id / "timeline.jsonl").exists():
            errors.append("missing timeline.jsonl")
        return {"valid": len(errors) == 0, "errors": errors}

    def health(self) -> dict[str, Any]:
        practice_dir = run_indexer._practice_dir()
        return {
            "practice_dir": str(practice_dir),
            "exists": practice_dir.exists(),
            "run_count": len(run_indexer.list_run_ids()),
        }
