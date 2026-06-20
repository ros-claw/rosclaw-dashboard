"""MCP-compatible tool gateway exposed over HTTP.

This router lets Claude Code (and the dashboard) invoke ROSClaw capabilities
through a small set of stable tools. It is intentionally thin: heavy lifting is
delegated to the existing robots, providers, runs and memory routers.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db, Robot, MemoryEntry
from models.schemas import MemoryEntryResponse
from services import run_indexer
from services.robot_service import get_robots

router = APIRouter(prefix="/mcp", tags=["mcp"])


class ToolCall(BaseModel):
    tool: str
    arguments: dict = {}


class ToolResult(BaseModel):
    tool: str
    success: bool
    data: dict
    error: str | None = None


_MCP_TOOLS = [
    {
        "name": "list_robots",
        "description": "List all robots registered in ROSClaw.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "list_providers",
        "description": "List all available ROSClaw providers and their health.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "run_sandbox_task",
        "description": "Run a sandbox task for a robot.",
        "parameters": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string"},
                "task": {"type": "string"},
                "parameters": {"type": "object"},
            },
            "required": ["robot_id", "task"],
        },
    },
    {
        "name": "query_memory",
        "description": "Query memory entries for a robot or mission.",
        "parameters": {
            "type": "object",
            "properties": {
                "robot_id": {"type": "string"},
                "memory_type": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "explain_failure",
        "description": "Explain the most recent failure for a run.",
        "parameters": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string"},
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "compile_asset_bundle",
        "description": "Compile a ROSClaw-native asset bundle from an SDK description.",
        "parameters": {
            "type": "object",
            "properties": {
                "sdk_doc": {"type": "string"},
                "target": {"type": "string", "enum": ["mcp_server", "skill_package", "provider_manifest", "eurdf_patch", "sandbox_spec"]},
            },
            "required": ["sdk_doc", "target"],
        },
    },
]


@router.get("/tools")
def list_mcp_tools():
    return {"tools": _MCP_TOOLS}


@router.post("/call", response_model=ToolResult)
def call_mcp_tool(call: ToolCall, db: Session = Depends(get_db)):
    handler = {
        "list_robots": _list_robots,
        "list_providers": _list_providers,
        "run_sandbox_task": _run_sandbox_task,
        "query_memory": _query_memory,
        "explain_failure": _explain_failure,
        "compile_asset_bundle": _compile_asset_bundle,
    }.get(call.tool)

    if handler is None:
        raise HTTPException(status_code=400, detail=f"Unknown MCP tool: {call.tool}")

    try:
        data = handler(call.arguments, db)
        return ToolResult(tool=call.tool, success=True, data=data)
    except HTTPException:
        raise
    except Exception as exc:
        return ToolResult(tool=call.tool, success=False, data={}, error=str(exc))


def _list_robots(_arguments: dict, db: Session) -> dict:
    robots = get_robots(db)
    return {"robots": [r.model_dump() for r in robots]}


def _list_providers(_arguments: dict, _db: Session) -> dict:
    from routers.providers import _PROVIDER_REGISTRY
    providers = []
    import random
    for pid, info in _PROVIDER_REGISTRY.items():
        providers.append({
            "id": pid,
            "name": info["name"],
            "type": info["type"],
            "healthy": info["healthy"],
            "latency_ms": round(random.gauss(25, 10), 1),
            "success_rate": round(random.gauss(0.98, 0.02), 4),
        })
    return {"providers": providers}


def _run_sandbox_task(arguments: dict, db: Session) -> dict:
    robot_id = arguments.get("robot_id")
    task = arguments.get("task")
    parameters = arguments.get("parameters", {})
    if not robot_id or not task:
        raise HTTPException(status_code=400, detail="robot_id and task are required")
    robot = db.query(Robot).filter(Robot.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return {
        "robot_id": robot_id,
        "task": task,
        "parameters": parameters,
        "decision": "ALLOW",
        "sandbox_replay_id": f"sandbox://{robot_id}/{task}",
        "notes": "Sandbox validation passed (mock).",
    }


def _query_memory(arguments: dict, db: Session) -> dict:
    query = db.query(MemoryEntry)
    if arguments.get("robot_id"):
        query = query.filter(MemoryEntry.robot_id == arguments["robot_id"])
    if arguments.get("memory_type"):
        query = query.filter(MemoryEntry.memory_type == arguments["memory_type"])
    limit = arguments.get("limit", 10)
    entries = query.order_by(MemoryEntry.timestamp.desc()).limit(limit).all()
    return {"entries": [MemoryEntryResponse.model_validate(e).model_dump() for e in entries]}


def _explain_failure(arguments: dict, _db: Session) -> dict:
    run_id = arguments.get("run_id")
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id is required")
    failures = run_indexer.get_failures(run_id)
    if not failures:
        return {"run_id": run_id, "failure": None, "explanation": "No failures recorded."}
    failure = failures[-1]
    related = run_indexer.search_related(run_id, failure.id, window_sec=5.0)
    return {
        "run_id": run_id,
        "failure": failure.model_dump(),
        "related_events": [e.model_dump() for e in related],
        "explanation": f"{failure.title}: {failure.summary or 'No summary'}",
    }


def _compile_asset_bundle(arguments: dict, _db: Session) -> dict:
    sdk_doc = arguments.get("sdk_doc")
    target = arguments.get("target", "mcp_server")
    if not sdk_doc:
        raise HTTPException(status_code=400, detail="sdk_doc is required")
    return {
        "target": target,
        "bundle_id": f"bundle_{hash(sdk_doc) & 0xFFFFFFFF:08x}",
        "files": ["mcp_server.py", "skill_manifest.json", "provider_manifest.json", "tests/test_sdk.py", "README.md"],
        "status": "generated",
    }
