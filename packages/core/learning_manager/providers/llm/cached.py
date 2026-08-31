"""Record/replay wrapper used to make LLM runs deterministic and auditable."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import ValidationError

from learning_manager.contracts import LLMProvider, LLMResponse
from learning_manager.providers.llm.meter import CostMeter

CacheMode = Literal["replay", "live"]


class _Trajectory(Protocol):
    def step(self, step: str, **fields: object) -> None: ...


class CassetteError(RuntimeError):
    """A cassette exists but cannot be read as a valid recorded response."""


class CassetteMissError(CassetteError):
    """No cassette exists for a request in replay mode."""


def _canonical_request(
    *,
    model: str,
    system: str,
    user: str,
    schema_name: str | None,
    temperature: float,
) -> str:
    """Serialize key fields unambiguously before hashing them."""
    return json.dumps(
        {
            "model": model,
            "system": system,
            "user": user,
            "schema_name": schema_name,
            "temperature": str(temperature),
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


class CachedLLMProvider:
    """Persist responses in live mode and serve them without an inner provider in replay."""

    def __init__(
        self,
        inner: LLMProvider | None,
        cassette_dir: Path,
        mode: CacheMode,
        model: str = "gemini-2.5-flash",
        *,
        meter: CostMeter | None = None,
        trajectory: _Trajectory | None = None,
    ) -> None:
        if mode not in ("live", "replay"):
            raise ValueError(f"Unsupported cassette mode: {mode}")
        if mode == "live" and inner is None:
            raise ValueError("Live cassette mode requires an inner LLM provider")
        self._inner = inner
        self._cassette_dir = Path(cassette_dir)
        self._mode = mode
        self._model = model
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
        request: dict[str, object] = {
            "model": self._model,
            "system": system,
            "user": user,
            "schema_name": schema_name,
            "json_schema": json_schema,
            "temperature": temperature,
        }
        key_material = _canonical_request(
            model=self._model,
            system=system,
            user=user,
            schema_name=schema_name,
            temperature=temperature,
        )
        key = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
        cassette_path = self._cassette_dir / f"{key[:16]}.json"

        if self._mode == "replay":
            return self._read(cassette_path, key, schema_name)

        if self._inner is None:
            raise RuntimeError("Live cassette mode requires an inner LLM provider")
        response = self._inner.complete(
            system=system,
            user=user,
            schema_name=schema_name,
            json_schema=json_schema,
            temperature=temperature,
        )
        self._write(cassette_path, request, response)
        return self._record(response.model_copy(update={"cache_hit": False}), schema_name)

    def _read(self, path: Path, key: str, schema_name: str | None) -> LLMResponse:
        if not path.exists():
            raise CassetteMissError(
                f"Cassette no encontrado para {key}. Ejecuta 'make record' con GEMINI_API_KEY, "
                "o usa LLM_MODE=live."
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            request = payload["request"]
            response = payload["response"]
            recorded_at = payload["recorded_at"]
            if not isinstance(request, dict) or not isinstance(response, dict):
                raise TypeError("request and response must be objects")
            if not isinstance(recorded_at, str):
                raise TypeError("recorded_at must be a string")
            loaded = LLMResponse.model_validate(response)
        except (OSError, KeyError, TypeError, ValueError, ValidationError) as exc:
            raise CassetteError(f"Cassette malformed: {path.name}") from exc
        return self._record(loaded.model_copy(update={"cache_hit": True}), schema_name)

    def _record(self, response: LLMResponse, schema_name: str | None) -> LLMResponse:
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

    def _write(self, path: Path, request: dict[str, object], response: LLMResponse) -> None:
        self._cassette_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "request": request,
            "response": response.model_dump(mode="json"),
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._cassette_dir,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_name = temporary.name
                temporary.write(serialized)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, path)
            temporary_name = None
        finally:
            if temporary_name is not None:
                with suppress(FileNotFoundError):
                    os.unlink(temporary_name)
