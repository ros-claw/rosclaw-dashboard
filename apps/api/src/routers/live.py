"""Live session router.

Provides REST endpoints and WebSocket streaming for live trace sessions.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from models.database import LiveSession as LiveSessionRow, get_db
from models.schemas import (
    LiveSessionCreate,
    LiveSessionListResponse,
    LiveSessionResponse,
)
from services.live_session_manager import LiveSessionManager, get_live_session_manager

router = APIRouter(prefix="/live", tags=["live"])


def _row_to_response(row: LiveSessionRow) -> LiveSessionResponse:
    config: dict[str, Any] | None = None
    if row.config_json:
        try:
            config = json.loads(row.config_json)
        except json.JSONDecodeError:
            config = None
    return LiveSessionResponse(
        session_id=row.session_id,
        run_id=row.run_id,
        status=row.status,
        config=config,
        created_at=row.created_at.timestamp() if row.created_at else None,
        closed_at=row.closed_at.timestamp() if row.closed_at else None,
        offline_run_id=row.offline_run_id,
    )


@router.get("/sessions", response_model=LiveSessionListResponse)
def list_sessions(db: Session = Depends(get_db)):
    manager = get_live_session_manager()
    rows = manager.list_sessions()
    return LiveSessionListResponse(
        sessions=[_row_to_response(r) for r in rows],
        total=len(rows),
    )


@router.post("/sessions", response_model=LiveSessionResponse, status_code=201)
def create_session(data: LiveSessionCreate):
    manager = get_live_session_manager()
    row = manager.create_session(
        robot_id=data.robot_id,
        task=data.task,
        run_id=data.run_id,
        config=data.config or {},
    )
    return _row_to_response(row)


@router.get("/{session_id}", response_model=LiveSessionResponse)
def get_session(session_id: str):
    manager = get_live_session_manager()
    row = manager.get_session(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _row_to_response(row)


@router.post("/{session_id}/attach-run", response_model=LiveSessionResponse)
def attach_run(session_id: str, payload: dict[str, Any]):
    run_id = payload.get("run_id")
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id required")
    manager = get_live_session_manager()
    row = manager.attach_run(session_id, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _row_to_response(row)


@router.post("/{session_id}/close", response_model=LiveSessionResponse)
async def close_session(session_id: str):
    manager = get_live_session_manager()
    row = await manager.close_session(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _row_to_response(row)


@router.websocket("/{session_id}/events")
async def live_events_websocket(websocket: WebSocket, session_id: str):
    manager = get_live_session_manager()
    row = manager.get_session(session_id)
    if row is None:
        await websocket.close(code=1008, reason="session not found")
        return

    await websocket.accept()
    await manager.register_client(session_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            try:
                msg = json.loads(message)
            except json.JSONDecodeError:
                continue
            action = msg.get("action")
            if action == "ping":
                await websocket.send_text(
                    json.dumps({"type": "pong", "timestamp": msg.get("timestamp")})
                )
            elif action == "close":
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.unregister_client(session_id, websocket)
        try:
            await websocket.close()
        except Exception:
            pass
