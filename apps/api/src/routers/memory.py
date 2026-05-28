from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db, MemoryEntry
from models.schemas import MemoryEntryResponse

router = APIRouter(prefix="/memory", tags=["memory"])


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
