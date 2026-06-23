"""ROSClaw workspace resolution.

The dashboard is designed to be consumed as an optional package by the core
``rosclaw`` runtime, so it must read from the same workspace layout. This
module mirrors ``rosclaw.firstboot.workspace.resolve_home`` without taking a
hard dependency on ``rosclaw``.
"""

from __future__ import annotations

import os
from pathlib import Path


def resolve_rosclaw_home(path: str | Path | None = None) -> Path:
    """Resolve the ROSClaw workspace root.

    Priority: explicit ``path`` > ``ROSCLAW_HOME`` env > ``~/.rosclaw``.
    """
    raw = path or os.environ.get("ROSCLAW_HOME") or "~/.rosclaw"
    return Path(raw).expanduser().resolve()


def rosclaw_dir(*parts: str) -> Path:
    """Return a path inside the resolved ROSClaw workspace."""
    return resolve_rosclaw_home().joinpath(*parts)
