import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db, MCAPFile
from models.schemas import MCAPFileBase, MCAPFileResponse

router = APIRouter(prefix="/mcap", tags=["mcap"])


def _parse_mcap_topics(path: str) -> list[dict]:
    """Parse actual MCAP file and extract topics with statistics."""
    topics = []
    if not os.path.exists(path):
        return topics

    try:
        from mcap.reader import make_reader
        with open(path, "rb") as f:
            reader = make_reader(f)
            summary = reader.get_summary()
            if summary is None:
                return topics

            channel_counts = {}
            channel_schemas = {}
            channel_time_ranges = {}

            for channel_id, count in (summary.statistics.channel_message_counts or {}).items():
                channel_counts[channel_id] = count

            for channel in summary.channels.values():
                schema = summary.schemas.get(channel.schema_id)
                schema_name = schema.name if schema else "unknown"
                channel_schemas[channel.id] = schema_name

            for msg in reader.iter_messages():
                ch_id = msg.channel_id
                ts = msg.log_time
                if ch_id not in channel_time_ranges:
                    channel_time_ranges[ch_id] = [ts, ts]
                else:
                    channel_time_ranges[ch_id][0] = min(channel_time_ranges[ch_id][0], ts)
                    channel_time_ranges[ch_id][1] = max(channel_time_ranges[ch_id][1], ts)

            for channel in summary.channels.values():
                ch_id = channel.id
                count = channel_counts.get(ch_id, 0)
                ts_range = channel_time_ranges.get(ch_id, [0, 0])
                duration_sec = (ts_range[1] - ts_range[0]) / 1e9 if ts_range[1] > ts_range[0] else 0
                avg_hz = count / duration_sec if duration_sec > 0 else 0

                topics.append({
                    "topic": channel.topic,
                    "schema": channel_schemas.get(ch_id, "unknown"),
                    "message_count": count,
                    "avg_hz": round(avg_hz, 2),
                    "first_timestamp": ts_range[0] / 1e9 if ts_range[0] else None,
                    "last_timestamp": ts_range[1] / 1e9 if ts_range[1] else None,
                })
    except Exception as e:
        return [{"error": str(e), "topic": "parse_failed"}]

    return topics


@router.get("", response_model=list[MCAPFileResponse])
def list_mcap_files(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    files = db.query(MCAPFile).offset(skip).limit(limit).all()
    return [MCAPFileResponse.model_validate(f) for f in files]


@router.get("/{mcap_id}", response_model=MCAPFileResponse)
def read_mcap_file(mcap_id: str, db: Session = Depends(get_db)):
    file = db.query(MCAPFile).filter(MCAPFile.id == mcap_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="MCAP file not found")
    return MCAPFileResponse.model_validate(file)


@router.post("/import", response_model=MCAPFileResponse, status_code=201)
def import_mcap(data: MCAPFileBase, db: Session = Depends(get_db)):
    existing = db.query(MCAPFile).filter(MCAPFile.id == data.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="MCAP file already exists")

    topics = _parse_mcap_topics(data.path)
    if topics and "error" not in topics[0]:
        if data.start_time is None and topics:
            data.start_time = topics[0].get("first_timestamp")
        if data.end_time is None and topics:
            data.end_time = topics[0].get("last_timestamp")

    db_file = MCAPFile(**data.model_dump())
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return MCAPFileResponse.model_validate(db_file)


@router.get("/{mcap_id}/topics")
def get_mcap_topics(mcap_id: str, db: Session = Depends(get_db)):
    file = db.query(MCAPFile).filter(MCAPFile.id == mcap_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="MCAP file not found")

    topics = _parse_mcap_topics(file.path)
    return {
        "mcap_id": mcap_id,
        "path": file.path,
        "topics": topics,
    }


@router.get("/{mcap_id}/foxglove-layout")
def get_foxglove_layout(mcap_id: str, db: Session = Depends(get_db)):
    file = db.query(MCAPFile).filter(MCAPFile.id == mcap_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="MCAP file not found")

    # Generate a basic Foxglove layout from robot sensors
    layout = {
        "layout": {
            "direction": "row",
            "first": {
                "direction": "column",
                "first": {"url": "./Image", "topic": "/camera/color/image_raw"},
                "second": {"url": "./3D", "topic": "/tf"},
                "splitPercentage": 50,
            },
            "second": {
                "direction": "column",
                "first": {"url": "./Plot", "topic": "/joint_states"},
                "second": {"url": "./RawMessages", "topic": "/rosclaw/agent_events"},
                "splitPercentage": 50,
            },
            "splitPercentage": 50,
        }
    }
    return {"mcap_id": mcap_id, "layout": layout}
