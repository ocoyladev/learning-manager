"""Frozen, deterministic knowledge corpus provider."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from learning_manager.contracts import Source

from .authority import score_source


class TopicNotInCorpusError(KeyError):
    """Raised when a requested topic has no frozen manifest."""


class CorpusProvider:
    def __init__(self, corpus_path: Path) -> None:
        self.corpus_path = corpus_path
        self._sources: dict[str, Source] = {}

    def research(self, topic: str, *, k: int = 8) -> list[Source]:
        manifest = self.corpus_path / topic / "manifest.json"
        if not manifest.is_file():
            raise TopicNotInCorpusError(topic)
        data = json.loads(manifest.read_text())
        sources = [Source.model_validate(item) for item in data]
        self._sources.update({source.id: source for source in sources})
        today = date.today()
        return sorted(sources, key=lambda source: (-score_source(source, today), source.id))[:k]

    def fetch(self, source_id: str) -> str:
        source = self._sources.get(source_id)
        if source is None:
            for manifest in self.corpus_path.glob("*/manifest.json"):
                for item in json.loads(manifest.read_text()):
                    if item["id"] == source_id:
                        source = Source.model_validate(item)
                        break
                if source is not None:
                    break
        if source is None or source.content_path is None:
            raise KeyError(source_id)
        return (self.corpus_path / source.content_path).read_text()
