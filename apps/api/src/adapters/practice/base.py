"""Practice store adapter protocol.

Abstracts how the dashboard discovers and reads practice runs.
"""

from typing import Any, Protocol

from models.schemas import ReplayManifest, RunDetail, RunSummary


class PracticeStoreAdapter(Protocol):
    """Protocol for practice run storage backends."""

    name: str
    mode: str  # real | mock | fixture | rule_based | unavailable | degraded

    def list_runs(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[RunSummary], int]:
        ...

    def get_run(self, run_id: str) -> RunDetail:
        ...

    def read_timeline(self, run_id: str) -> list[dict[str, Any]]:
        ...

    def get_replay_manifest(self, run_id: str) -> ReplayManifest:
        ...

    def validate_run(self, run_id: str) -> dict[str, Any]:
        ...

    def health(self) -> dict[str, Any]:
        ...
