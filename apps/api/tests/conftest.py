"""Shared test fixtures for the ROSClaw Dashboard API."""

import os
import shutil
from pathlib import Path

import pytest

# Point the API at the golden fixture and temp paths *before* test modules import
# `main` during collection.
_fixtures = Path(__file__).parent / "fixtures" / "practice_runs"
os.environ.setdefault("ROSCLAW_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ROSCLAW_PRACTICE_DIR", str(_fixtures))
os.environ.setdefault("ROSCLAW_EXPORT_DIR", "/tmp/rosclaw-test-exports")


@pytest.fixture(scope="session", autouse=True)
def _configure_test_settings():
    """Re-assert test env values at runtime and initialize the in-memory DB."""
    fixtures = Path(__file__).parent / "fixtures" / "practice_runs"
    os.environ["ROSCLAW_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["ROSCLAW_PRACTICE_DIR"] = str(fixtures)
    os.environ["ROSCLAW_EXPORT_DIR"] = "/tmp/rosclaw-test-exports"

    # Import here so the env vars above are respected; init_db is idempotent.
    from rosclaw_dashboard.main import app  # noqa: F401
    from rosclaw_dashboard.models.database import init_db

    init_db()


@pytest.fixture(autouse=True)
def _clean_export_dir(tmp_path_factory, monkeypatch):
    """Give each test a fresh export directory."""
    export_dir = tmp_path_factory.mktemp("exports")
    monkeypatch.setenv("ROSCLAW_EXPORT_DIR", str(export_dir))

    # Re-bind the lazy module-level EXPORT_DIR if already imported.
    try:
        from rosclaw_dashboard.services import export_jobs
        export_jobs.EXPORT_DIR = export_dir
    except Exception:
        pass

    yield export_dir

    shutil.rmtree(export_dir, ignore_errors=True)


@pytest.fixture
def client():
    """Synchronous TestClient for REST endpoints with DB initialized."""
    import sys
    from pathlib import Path
    src = Path(__file__).parent.parent / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from fastapi.testclient import TestClient
    from rosclaw_dashboard.main import app
    from rosclaw_dashboard.models.database import init_db
    init_db()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def run_id():
    return "golden_pick_cube_failure"


@pytest.fixture
def blocked_run_id():
    return "golden_arm_blocked"
