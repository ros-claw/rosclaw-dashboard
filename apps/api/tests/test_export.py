"""Tests for export jobs and all four export formats."""

import io
import time
import zipfile

import pytest


FORMATS = ["rlds", "lerobot", "failure_case", "skill_candidate"]


def _poll_job(client, job_id, timeout: float = 5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/export/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data["state"] in {"completed", "failed"}:
            return data
        time.sleep(0.05)
    raise TimeoutError(f"Export job {job_id} did not finish")


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", FORMATS)
async def test_export_format_completes_and_downloads(client, run_id, fmt):
    resp = client.post("/api/export", json={"run_id": run_id, "format": fmt})
    assert resp.status_code == 202
    job = resp.json()
    assert job["run_id"] == run_id
    assert job["format"] == fmt
    assert job["state"] in {"queued", "running"}

    status = _poll_job(client, job["job_id"])
    assert status["state"] == "completed"
    assert status["progress"] == 1.0
    assert status["result_url"].endswith(f"/api/export/{job['job_id']}/download")

    dl = client.get(status["result_url"])
    assert dl.status_code == 200
    assert dl.headers["content-type"] in ("application/zip", "application/x-zip-compressed")

    buf = io.BytesIO(dl.content)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        assert "manifest.json" in names


@pytest.mark.asyncio
async def test_rlds_export_content(client, run_id):
    resp = client.post("/api/export", json={"run_id": run_id, "format": "rlds"})
    job = _poll_job(client, resp.json()["job_id"])

    dl = client.get(job["result_url"])
    with zipfile.ZipFile(io.BytesIO(dl.content)) as zf:
        info = __import__("json").loads(zf.read("info.json"))
        episodes = __import__("json").loads(zf.read("episodes.json"))

    assert info["format"] == "rlds"
    assert info["run_id"] == run_id
    assert info["robot_id"] == "ur5e_table_01"
    assert len(episodes["steps"]) == 2
    assert episodes["steps"][0]["t_rel"] == 6.0
    assert "observation" in episodes["steps"][0]


@pytest.mark.asyncio
async def test_failure_case_export_content(client, run_id):
    resp = client.post("/api/export", json={"run_id": run_id, "format": "failure_case"})
    job = _poll_job(client, resp.json()["job_id"])

    dl = client.get(job["result_url"])
    with zipfile.ZipFile(io.BytesIO(dl.content)) as zf:
        package = __import__("json").loads(zf.read("failure_case.json"))

    assert package["format"] == "failure_case"
    assert package["failure_count"] == 1
    failure = package["cases"][0]["failure_event"]
    assert failure["id"] == "evt_failure_001"
    assert failure["severity"] == "failure"


@pytest.mark.asyncio
async def test_export_invalid_format_returns_400(client, run_id):
    resp = client.post("/api/export", json={"run_id": run_id, "format": "unknown"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_missing_export_returns_404(client):
    resp = client.get("/api/export/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_exports_by_run(client, run_id):
    resp = client.post("/api/export", json={"run_id": run_id, "format": "rlds"})
    job_id = _poll_job(client, resp.json()["job_id"])["job_id"]

    resp = client.get("/api/export", params={"run_id": run_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(j["job_id"] == job_id for j in data["jobs"])
