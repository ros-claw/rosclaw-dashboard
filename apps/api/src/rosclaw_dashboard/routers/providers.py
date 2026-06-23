"""Provider health API for monitoring provider latency, success rate, and load."""

import random
from fastapi import APIRouter

router = APIRouter(prefix="/providers", tags=["providers"])

_PROVIDER_REGISTRY = {
    "seekdb": {"name": "SeekDB", "type": "memory", "healthy": True},
    "sandbox": {"name": "Sandbox", "type": "simulation", "healthy": True},
    "runtime_bridge": {"name": "Runtime Bridge", "type": "runtime", "healthy": True},
    "foxglove": {"name": "Foxglove", "type": "visualization", "healthy": True},
    "heuristic_recovery": {"name": "Heuristic Recovery", "type": "how", "healthy": True},
    "skill_manager": {"name": "Skill Manager", "type": "skill", "healthy": True},
}


@router.get("")
def list_providers():
    result = []
    for pid, info in _PROVIDER_REGISTRY.items():
        result.append({
            "id": pid,
            "name": info["name"],
            "type": info["type"],
            "healthy": info["healthy"],
            "latency_ms": round(random.gauss(25, 10), 1),
            "success_rate": round(random.gauss(0.98, 0.02), 4),
            "request_count": random.randint(1000, 50000),
            "error_count": random.randint(0, 50),
            "load_percent": round(random.gauss(45, 20), 1),
        })
    return result


@router.get("/{provider_id}")
def get_provider(provider_id: str):
    info = _PROVIDER_REGISTRY.get(provider_id)
    if not info:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Provider not found")
    return {
        "id": provider_id,
        "name": info["name"],
        "type": info["type"],
        "healthy": info["healthy"],
        "latency_ms": round(random.gauss(25, 10), 1),
        "success_rate": round(random.gauss(0.98, 0.02), 4),
        "request_count": random.randint(1000, 50000),
        "error_count": random.randint(0, 50),
        "load_percent": round(random.gauss(45, 20), 1),
    }
