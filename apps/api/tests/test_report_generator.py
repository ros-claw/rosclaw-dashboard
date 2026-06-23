"""Tests for acceptance report generator and endpoints."""

import pytest

from rosclaw_dashboard.services.report_generator import generate_acceptance_report


@pytest.mark.asyncio
async def test_report_generator_produces_verdict(client, run_id):
    report = generate_acceptance_report(run_id)
    assert report.run_id == run_id
    assert report.verdict in {"PASS", "PARTIAL", "FAIL"}
    assert len(report.sections) >= 4
    assert any(a.name == "bundle.zip" for a in report.artifacts)


@pytest.mark.asyncio
async def test_report_endpoint(client, run_id):
    resp = client.post(f"/api/runs/{run_id}/report")
    assert resp.status_code == 200
    data = resp.json()
    assert data["report"]["run_id"] == run_id
    assert data["download_url"]


@pytest.mark.asyncio
async def test_report_download_endpoint(client, run_id):
    client.post(f"/api/runs/{run_id}/report")
    resp = client.get(f"/api/runs/{run_id}/report/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"


@pytest.mark.asyncio
async def test_get_report_endpoint(client, run_id):
    client.post(f"/api/runs/{run_id}/report")
    resp = client.get(f"/api/runs/{run_id}/report")
    assert resp.status_code == 200
    assert resp.json()["report"]["run_id"] == run_id
