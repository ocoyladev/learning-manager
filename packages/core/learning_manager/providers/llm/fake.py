"""Deterministic, network-free LLM provider for tests and local simulations."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence

from learning_manager.contracts import LLMResponse

type ResponseSource = Sequence[str] | Callable[[str], str]


class FakeLLM:
    """Return a finite sequence or a function-derived response for each prompt."""

    def __init__(self, responses: ResponseSource, *, model: str = "fake") -> None:
        self._responses = responses
        self._index = 0
        self._model = model
        self.calls = 0
        self.last_user_prompt: str | None = None
        self.last_temperature = 0.0

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema_name: str | None = None,
        json_schema: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        del system, schema_name, json_schema
        self.calls += 1
        self.last_user_prompt = user
        self.last_temperature = 0.0

        if callable(self._responses):
            text = self._responses(user)
        else:
            if self._index >= len(self._responses):
                raise RuntimeError("FakeLLM response list exhausted")
            text = self._responses[self._index]
            self._index += 1

        parsed: dict[str, object] | None = None
        try:
            candidate = json.loads(text)
        except (TypeError, ValueError):
            candidate = None
        if isinstance(candidate, dict):
            parsed = candidate

        return LLMResponse(
            text=text,
            parsed=parsed,
            model=self._model,
            latency_ms=0,
        )
