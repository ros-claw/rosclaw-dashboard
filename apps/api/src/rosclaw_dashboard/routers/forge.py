"""Forge / sdk_to_mcp — generate and validate ROSClaw-native asset bundles."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from rosclaw_dashboard.core.config import settings
from rosclaw_dashboard.models.database import get_db, MemoryEntry

router = APIRouter(prefix="/forge", tags=["forge"])


class CompileRequest(BaseModel):
    sdk_doc: str
    target: str = "mcp_server"  # mcp_server, skill_package, provider_manifest, eurdf_patch, sandbox_spec
    staging: bool = True


class ValidateRequest(BaseModel):
    bundle_id: str
    bundle: dict


class BundleResponse(BaseModel):
    bundle_id: str
    target: str
    status: str
    files: list[dict]
    validation: dict
    staging_path: str | None


class ValidationResponse(BaseModel):
    bundle_id: str
    valid: bool
    checks: list[dict]
    errors: list[str]
    warnings: list[str]


@router.post("/compile", response_model=BundleResponse)
def compile_bundle(req: CompileRequest, db: Session = Depends(get_db)):
    bundle_id = _bundle_id(req.sdk_doc, req.target)
    files = _generate_files(req.target, req.sdk_doc, bundle_id)

    validation = _validate_bundle(req.target, files, sdk_doc=req.sdk_doc)
    valid = validation["valid"]

    staging_path = None
    if req.staging and valid:
        staging_path = _write_staging(bundle_id, files)

    if valid:
        entry = MemoryEntry(
            id=f"forge_{bundle_id}",
            robot_id="forge",
            memory_type="semantic",
            content_json=json.dumps({
                "bundle_id": bundle_id,
                "target": req.target,
                "files": [f["path"] for f in files],
                "validation": validation,
            }),
            source_skill="forge_compile",
            confidence=0.9,
        )
        db.merge(entry)
        db.commit()

    return BundleResponse(
        bundle_id=bundle_id,
        target=req.target,
        status="validated" if valid else "blocked",
        files=files,
        validation=validation,
        staging_path=staging_path,
    )


@router.post("/validate", response_model=ValidationResponse)
def validate_bundle(req: ValidateRequest):
    target = req.bundle.get("target", "unknown")
    files = req.bundle.get("files", [])
    validation = _validate_bundle(target, files)
    return ValidationResponse(
        bundle_id=req.bundle_id,
        valid=validation["valid"],
        checks=validation["checks"],
        errors=validation["errors"],
        warnings=validation["warnings"],
    )


@router.get("/bundles")
def list_bundles(db: Session = Depends(get_db)):
    entries = db.query(MemoryEntry).filter(MemoryEntry.source_skill == "forge_compile").all()
    bundles = []
    for e in entries:
        try:
            content = json.loads(e.content_json or "{}")
        except json.JSONDecodeError:
            content = {}
        bundles.append({
            "bundle_id": content.get("bundle_id", e.id),
            "target": content.get("target"),
            "files": content.get("files", []),
            "validation": content.get("validation", {}),
            "created_at": e.timestamp.isoformat() if e.timestamp else None,
        })
    return {"bundles": bundles}


@router.get("/bundles/{bundle_id}")
def get_bundle(bundle_id: str, db: Session = Depends(get_db)):
    entry = db.query(MemoryEntry).filter(
        MemoryEntry.source_skill == "forge_compile",
        MemoryEntry.id == f"forge_{bundle_id}",
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Bundle not found")
    try:
        content = json.loads(entry.content_json or "{}")
    except json.JSONDecodeError:
        content = {}
    staging_path = Path(settings.export_dir) / "staging" / bundle_id
    files = content.get("files", [])
    file_contents = []
    if staging_path.exists():
        for rel_path in files:
            full_path = staging_path / rel_path
            if full_path.is_file() and full_path.is_relative_to(staging_path):
                file_contents.append({
                    "path": rel_path,
                    "content": full_path.read_text(encoding="utf-8"),
                    "size": full_path.stat().st_size,
                })
    return {
        "bundle_id": content.get("bundle_id", bundle_id),
        "target": content.get("target"),
        "status": "validated" if content.get("validation", {}).get("valid") else "blocked",
        "files": file_contents,
        "validation": content.get("validation", {}),
        "created_at": entry.timestamp.isoformat() if entry.timestamp else None,
    }


@router.post("/bundles/{bundle_id}/validate", response_model=ValidationResponse)
def revalidate_bundle(bundle_id: str, db: Session = Depends(get_db)):
    entry = db.query(MemoryEntry).filter(
        MemoryEntry.source_skill == "forge_compile",
        MemoryEntry.id == f"forge_{bundle_id}",
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Bundle not found")
    try:
        content = json.loads(entry.content_json or "{}")
    except json.JSONDecodeError:
        content = {}
    target = content.get("target", "unknown")
    staging_path = Path(settings.export_dir) / "staging" / bundle_id
    files = []
    if staging_path.exists():
        for rel_path in content.get("files", []):
            full_path = staging_path / rel_path
            if full_path.is_file() and full_path.is_relative_to(staging_path):
                files.append({"path": rel_path, "content": full_path.read_text(encoding="utf-8")})
    validation = _validate_bundle(target, files)
    return ValidationResponse(
        bundle_id=bundle_id,
        valid=validation["valid"],
        checks=validation["checks"],
        errors=validation["errors"],
        warnings=validation["warnings"],
    )


def _bundle_id(sdk_doc: str, target: str) -> str:
    h = hashlib.sha256(f"{sdk_doc}:{target}".encode()).hexdigest()[:12]
    return f"{target}_{h}"


def _generate_files(target: str, sdk_doc: str, bundle_id: str) -> list[dict]:
    common = [
        {"path": "README.md", "content": f"# {bundle_id}\n\nGenerated from SDK doc ({len(sdk_doc)} chars).\n"},
        {"path": "manifest.json", "content": json.dumps({"bundle_id": bundle_id, "target": target, "generated_at": _now()}, indent=2)},
        {"path": "SDK.md", "content": sdk_doc},
    ]
    if target == "mcp_server":
        return common + [
            {"path": "server.py", "content": "from mcp.server import Server\n\napp = Server('rosclaw_generated')\n"},
            {"path": "tests/test_server.py", "content": "def test_server():\n    assert True\n"},
        ]
    if target == "skill_package":
        return common + [
            {"path": "skill.py", "content": "class GeneratedSkill:\n    def run(self, robot_id, params):\n        return {'status': 'ok'}\n"},
            {"path": "skill_manifest.json", "content": json.dumps({"name": bundle_id, "approval_required": True}, indent=2)},
        ]
    if target == "provider_manifest":
        return common + [
            {"path": "provider.yaml", "content": f"name: {bundle_id}\ntype: generated\nasync: true\n"},
        ]
    if target == "eurdf_patch":
        return common + [
            {"path": "robot.patch.yaml", "content": "sensors:\n  generated_sensor:\n    type: generic\n"},
        ]
    if target == "sandbox_spec":
        return common + [
            {"path": "sandbox_spec.yaml", "content": "firewall:\n  mode: ALLOW\n  preemption: true\n"},
        ]
    return common


_TARGET_REQUIRED_FILES = {
    "mcp_server": {"server.py"},
    "skill_package": {"skill.py", "skill_manifest.json"},
    "provider_manifest": {"provider.yaml"},
    "eurdf_patch": {"robot.patch.yaml"},
    "sandbox_spec": {"sandbox_spec.yaml"},
}


def _validate_bundle(target: str, files: list[dict], sdk_doc: str = "") -> dict:
    checks = []
    errors = []
    warnings = []

    # Gather all file contents as a single searchable corpus.
    contents = "\n".join(f.get("content") or "" for f in files)
    searchable = f"{contents}\n{sdk_doc}".lower()

    paths = {f["path"] for f in files}
    has_readme = "README.md" in paths
    has_manifest = "manifest.json" in paths
    has_async = "async" in searchable
    has_safety = bool(re.search(r"\bsafety\b|\bfirewall\b|\bpreemption\b|\bapproval\b|\blimit\b|\bconstraint\b", searchable, re.I))
    has_tests = any("test" in f["path"] for f in files)

    required = _TARGET_REQUIRED_FILES.get(target, set())
    missing_required = required - paths

    checks.append({"name": "readme_present", "passed": has_readme})
    checks.append({"name": "manifest_present", "passed": has_manifest})
    checks.append({"name": "async_or_schema", "passed": has_async or has_manifest})
    checks.append({"name": "safety_or_firewall", "passed": has_safety})
    checks.append({"name": "tests_present", "passed": has_tests})
    checks.append({"name": "required_files_present", "passed": not missing_required})
    checks.append({"name": "target_recognized", "passed": target in _TARGET_REQUIRED_FILES})

    if not has_readme:
        warnings.append("README.md missing")
    if not has_safety:
        errors.append("Safety/firewall constraints missing — bundle blocked from runtime.")
    if not has_tests:
        warnings.append("No tests found")
    if missing_required:
        errors.append(f"Missing required files for {target}: {', '.join(sorted(missing_required))}")
    if target not in _TARGET_REQUIRED_FILES:
        errors.append(f"Unknown target '{target}'.")

    valid = len(errors) == 0
    return {"valid": valid, "checks": checks, "errors": errors, "warnings": warnings}


def _write_staging(bundle_id: str, files: list[dict]) -> str:
    staging = Path(settings.export_dir) / "staging" / bundle_id
    staging.mkdir(parents=True, exist_ok=True)
    for f in files:
        path = staging / f["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f["content"], encoding="utf-8")
    return str(staging)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
