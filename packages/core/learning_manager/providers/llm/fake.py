"""Deterministic, network-free LLM provider for tests and local simulations."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import Protocol

from learning_manager.contracts import LLMResponse
from learning_manager.providers.llm.meter import CostMeter

type ResponseSource = Sequence[str] | Callable[[str], str]


class _Trajectory(Protocol):
    def step(self, step: str, **fields: object) -> None: ...


class FakeLLM:
    """Return a finite sequence or a function-derived response for each prompt."""

    def __init__(
        self,
        responses: ResponseSource,
        *,
        model: str = "fake",
        meter: CostMeter | None = None,
        trajectory: _Trajectory | None = None,
    ) -> None:
        self._responses = responses
        self._index = 0
        self._model = model
        self.calls = 0
        self.last_user_prompt: str | None = None
        self.last_temperature = 0.0
        self._meter = meter
        self._trajectory = trajectory

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema_name: str | None = None,
        json_schema: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        del system, json_schema
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

        response = LLMResponse(
            text=text,
            parsed=parsed,
            model=self._model,
            latency_ms=0,
        )
        if self._meter is not None:
            self._meter.record(response)
        if self._trajectory is not None:
            self._trajectory.step(
                "llm_call",
                model=response.model,
                cache_hit=response.cache_hit,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                latency_ms=response.latency_ms,
                schema_name=schema_name,
            )
        return response
