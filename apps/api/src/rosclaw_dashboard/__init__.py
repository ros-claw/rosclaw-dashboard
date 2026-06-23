"""rosclaw-dashboard — Full-featured ROSClaw Dashboard package.

Provides the FastAPI backend and optionally serves the Next.js frontend
static build. Designed to be consumed by the core ``rosclaw`` package as
an optional dependency.
"""

__version__ = "1.0.0"

from rosclaw_dashboard.serve import get_app, main, serve

__all__ = ["get_app", "main", "serve", "__version__"]
