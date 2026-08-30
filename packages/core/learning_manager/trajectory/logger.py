"""JSONL trajectory logging for agent executions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


class AgentTrajectory:
    """Append structured execution steps to one agent's JSONL file."""

    def __init__(self, path: Path, agent: str) -> None:
        self._path = path
        self._agent = agent
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def step(self, step: str, **fields: object) -> None:
        """Write one timestamped step and its arbitrary JSON-compatible fields."""
        record: dict[str, object] = dict(fields)
        record.update(
            {
                "ts": datetime.now(UTC).isoformat(),
                "agent": self._agent,
                "step": step,
            }
        )
        with self._path.open("a", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


class TrajectoryLogger:
    """Create per-agent trajectory writers under a run-specific directory."""

    def __init__(self, run_dir: Path, run_id: str) -> None:
        self._dir = Path(run_dir) / run_id

    def for_agent(self, agent: str) -> AgentTrajectory:
        """Return the trajectory writer for an agent in this run."""
        return AgentTrajectory(self._dir / f"{agent}.jsonl", agent)
