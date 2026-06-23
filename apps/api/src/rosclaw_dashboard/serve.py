"""Entry points for the rosclaw-dashboard package."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _mount_static(app: Any) -> Any:
    """Mount built static frontend files at / if they exist."""
    static_dir = Path(__file__).with_suffix("").parent / "static"
    if static_dir.exists() and static_dir.is_dir():
        from fastapi.staticfiles import StaticFiles

        # API routes are registered before this; static files act as a catch-all
        # for the SPA, but we must not shadow /api or /docs.
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    return app


def get_app() -> Any:
    """Return the configured FastAPI app with static files mounted."""
    from rosclaw_dashboard.main import app

    return _mount_static(app)


def serve(host: str = "0.0.0.0", port: int = 8765, workspace: str | Path | None = None) -> None:
    """Serve the dashboard.

    Args:
        host: Bind host.
        port: Bind port.
        workspace: ROSClaw workspace root. If given, sets ``ROSCLAW_HOME`` before
            loading configuration so the dashboard reads the same data as the
            runtime.
    """
    import uvicorn

    if workspace is not None:
        os.environ["ROSCLAW_HOME"] = str(workspace)

    app = get_app()
    uvicorn.run(app, host=host, port=port, log_level="info")


def main() -> None:
    """CLI entry point used by ``rosclaw-dashboard-serve``."""
    import argparse

    parser = argparse.ArgumentParser("rosclaw-dashboard-serve")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--workspace", default=None, help="ROSClaw workspace root")
    args = parser.parse_args()
    serve(host=args.host, port=args.port, workspace=args.workspace)
