"""Documented placeholder for NotebookLM; unofficial MCP integrations are prohibited."""

from __future__ import annotations


class NotebookLMProvider:
    def research(self, topic: str, *, k: int = 8) -> list[object]:
        raise NotImplementedError(
            "NotebookLM is not implemented: unofficial MCP integrations are prohibited"
        )

    def fetch(self, source_id: str) -> str:
        raise NotImplementedError(
            "NotebookLM is not implemented: unofficial MCP integrations are prohibited"
        )
