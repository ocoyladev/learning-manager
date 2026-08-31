"""Factory wiring for the fake, replay, and live LLM modes."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

from learning_manager.contracts import LLMProvider
from learning_manager.providers.llm.cached import CachedLLMProvider
from learning_manager.providers.llm.fake import FakeLLM, ResponseSource
from learning_manager.providers.llm.gemini import GeminiProvider
from learning_manager.providers.llm.meter import CostMeter


class ConfigError(RuntimeError):
    """Raised when LLM configuration cannot construct the requested mode."""


class _Settings(Protocol):
    llm_mode: str
    gemini_api_key: str | None
    gemini_model: str
    cassette_dir: Path


class _Trajectory(Protocol):
    def step(self, step: str, **fields: object) -> None: ...


def _value(settings: object, name: str, default: object) -> object:
    value = getattr(settings, name, default)
    return value


def build_llm(
    settings: _Settings,
    meter: CostMeter,
    trajectory: _Trajectory | None,
) -> LLMProvider:
    """Build an instrumented provider from the caller's authoritative settings."""
    mode = cast(str, _value(settings, "llm_mode", "replay"))
    model = cast(str, _value(settings, "gemini_model", "gemini-2.5-flash"))
    cassette_dir = Path(cast(Path | str, _value(settings, "cassette_dir", "fixtures/cassettes")))
    if mode == "fake":
        configured = _value(settings, "fake_responses", None)
        responses: ResponseSource
        if isinstance(configured, Sequence) and not isinstance(configured, (str, bytes)):
            responses = [str(item) for item in configured]
        else:

            def default_response(_prompt: str) -> str:
                return "{}"

            responses = default_response
        provider: LLMProvider = FakeLLM(responses, model="fake", meter=meter, trajectory=trajectory)
    elif mode == "replay":
        provider = CachedLLMProvider(
            inner=None,
            cassette_dir=cassette_dir,
            mode="replay",
            model=model,
            meter=meter,
            trajectory=trajectory,
        )
    elif mode == "live":
        api_key = cast(str | None, _value(settings, "gemini_api_key", None))
        if not api_key:
            raise ConfigError("LLM_MODE=live requires GEMINI_API_KEY")
        provider = CachedLLMProvider(
            inner=GeminiProvider(api_key=api_key, model=model),
            cassette_dir=cassette_dir,
            mode="live",
            model=model,
            meter=meter,
            trajectory=trajectory,
        )
    else:
        raise ConfigError(f"Unsupported LLM_MODE: {mode}")
    return provider
