"""Official Google Gen AI adapter for Gemini structured text generation."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Protocol, cast

from google import genai
from google.genai import types

from learning_manager.contracts import LLMResponse


class _ModelsClient(Protocol):
    def generate_content(self, **kwargs: object) -> object: ...


class _GenAIClient(Protocol):
    models: _ModelsClient


class _UsageMetadata(Protocol):
    prompt_token_count: int | None
    candidates_token_count: int | None


class _GeneratedResponse(Protocol):
    text: str | None
    usage_metadata: _UsageMetadata | None


def _status_code(error: BaseException) -> int | None:
    for name in ("status_code", "code"):
        value = getattr(error, name, None)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdecimal():
            return int(value)
    response = getattr(error, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def _token_count(usage: _UsageMetadata | None, name: str, fallback: int) -> int:
    value = getattr(usage, name, None) if usage is not None else None
    return value if isinstance(value, int) and value >= 0 else fallback


class GeminiProvider:
    """Generate JSON text using Gemini, with bounded transient-error retries."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout: int = 60,
        *,
        client: _GenAIClient | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self._sleep = sleep
        if client is None:
            client = cast(
                _GenAIClient,
                genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(timeout=timeout * 1000),
                ),
            )
        self._client = client

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema_name: str | None = None,
        json_schema: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        del schema_name, temperature
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=json_schema,
        )
        request: dict[str, object] = {
            "model": self.model,
            "contents": user,
            "config": config,
        }
        for attempt in range(3):
            started = time.monotonic_ns()
            try:
                raw = self._client.models.generate_content(**request)
            except Exception as error:
                status = _status_code(error)
                if status != 429 and not (status is not None and 500 <= status < 600):
                    raise
                if attempt == 2:
                    raise
                self._sleep(0.5 * (2**attempt))
                continue
            latency_ms = int((time.monotonic_ns() - started) / 1_000_000)
            response = cast(_GeneratedResponse, raw)
            text = response.text or ""
            parsed: dict[str, object] | None = None
            try:
                candidate = json.loads(text)
            except (TypeError, ValueError):
                candidate = None
            if isinstance(candidate, dict):
                parsed = candidate
            usage = response.usage_metadata
            input_tokens = _token_count(
                usage, "prompt_token_count", max(1, len(system + user) // 4)
            )
            output_tokens = _token_count(usage, "candidates_token_count", max(1, len(text) // 4))
            return LLMResponse(
                text=text,
                parsed=parsed,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )
        raise RuntimeError("Gemini request exhausted retry attempts")
