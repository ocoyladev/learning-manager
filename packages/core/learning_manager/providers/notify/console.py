"""File-backed notification provider for local demos and replayable tests."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from learning_manager.contracts import Reply


class ConsoleProvider:
    """Write outbound messages to JSON and consume scripted JSONL replies."""

    def __init__(self, out_dir: str | Path = "./notifications") -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def send(self, *, user_ref: str, message: str, options: list[str] | None = None) -> str:
        ref = uuid.uuid4().hex
        payload = {
            "user_ref": user_ref,
            "message": message,
            "options": options or [],
            "sent_at": datetime.now(UTC).isoformat(),
        }
        (self.out_dir / f"{ref}.json").write_text(json.dumps(payload), encoding="utf-8")
        return ref

    def poll_replies(self) -> list[Reply]:
        path = self.out_dir / "replies.jsonl"
        if not path.exists():
            return []
        replies: list[Reply] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                replies.append(
                    Reply(
                        user_ref=item["user_ref"],
                        text=item["text"],
                        received_at=datetime.now(UTC),
                        message_ref=item.get("message_ref"),
                    )
                )
        return replies
