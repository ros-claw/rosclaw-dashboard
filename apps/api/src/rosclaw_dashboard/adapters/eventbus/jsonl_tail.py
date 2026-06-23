"""JSONL tail adapter for local runtime event streams.

Watches ``events_dir/*.jsonl`` and emits ``RosclawEventEnvelope`` objects for
new lines. Invalid lines are recorded in a dead-letter counter/file.
"""

import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable

from rosclaw_dashboard.contracts import RosclawEventEnvelope, validate_envelope


class JsonlTailAdapter:
    """Tail local JSONL files produced by ROSClaw modules."""

    name = "jsonl_tail"

    def __init__(self, events_dir: str | Path) -> None:
        self._events_dir = Path(events_dir)
        self._callbacks: list[tuple[str, Callable[[RosclawEventEnvelope], Any]]] = []
        self._cursors: dict[Path, int] = {}
        self._connected = False
        self._dead_letters: list[dict[str, Any]] = []
        self._read_error: str | None = None

    @property
    def mode(self) -> str:
        if not self._events_dir.exists():
            return "unavailable"
        if self._read_error:
            return "degraded"
        return "real" if self._connected else "degraded"

    def connect(self) -> None:
        self._events_dir.mkdir(parents=True, exist_ok=True)
        self._connected = True
        self._read_error = None
        # Prime cursors so we only emit new lines after connect.
        for path in self._event_files():
            self._cursors[path] = self._count_lines(path)

    def disconnect(self) -> None:
        self._connected = False

    def subscribe(
        self,
        topic_pattern: str,
        callback: Callable[[RosclawEventEnvelope], Any],
    ) -> None:
        self._callbacks.append((topic_pattern, callback))

    def publish(self, envelope: RosclawEventEnvelope) -> None:
        if not self._events_dir.exists():
            return
        path = self._events_dir / "dashboard.jsonl"
        try:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(envelope.model_dump(), default=str) + "\n")
        except OSError as e:
            self._read_error = str(e)

    def health(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "events_dir": str(self._events_dir),
            "exists": self._events_dir.exists(),
            "files": len(self._event_files()),
            "dead_letters": len(self._dead_letters),
            "last_error": self._read_error,
        }

    def read_new(self) -> list[RosclawEventEnvelope]:
        """Read and return envelopes appended since the last call."""
        results: list[RosclawEventEnvelope] = []
        if not self._connected:
            return results

        for path in self._event_files():
            try:
                lines = self._read_lines(path)
            except OSError as e:
                self._read_error = str(e)
                continue

            previous = self._cursors.get(path, 0)
            if len(lines) < previous:
                # File was truncated; re-read from start.
                previous = 0

            for line in lines[previous:]:
                envelope = self._parse_line(line, path)
                if envelope is not None:
                    results.append(envelope)
                    self._dispatch(envelope)

            self._cursors[path] = len(lines)

        return results

    def _event_files(self) -> list[Path]:
        if not self._events_dir.exists():
            return []
        return sorted(self._events_dir.glob("*.jsonl"))

    @staticmethod
    def _count_lines(path: Path) -> int:
        try:
            with path.open("r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except OSError:
            return 0

    @staticmethod
    def _read_lines(path: Path) -> list[str]:
        with path.open("r", encoding="utf-8") as f:
            return [line for line in f]

    def _parse_line(self, line: str, path: Path) -> RosclawEventEnvelope | None:
        raw = line.strip()
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            self._dead_letters.append({"path": str(path), "line": raw, "error": str(e)})
            return None
        try:
            return validate_envelope(data)
        except Exception as e:  # noqa: BLE001
            self._dead_letters.append({"path": str(path), "line": raw, "error": str(e)})
            return None

    def _dispatch(self, envelope: RosclawEventEnvelope) -> None:
        topic = envelope.type
        for pattern, callback in self._callbacks:
            if self._match(pattern, topic):
                try:
                    callback(envelope)
                except Exception:
                    pass

    @staticmethod
    def _match(pattern: str, topic: str) -> bool:
        if pattern == "*" or pattern == "*.*":
            return True
        if pattern.endswith(".*"):
            return topic.startswith(pattern[:-1])
        return pattern == topic
