from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from learning_manager.providers.llm.cached import CachedLLMProvider
from learning_manager.providers.llm.factory import ConfigError, build_llm
from learning_manager.providers.llm.fake import FakeLLM
from learning_manager.providers.llm.gemini import GeminiProvider
from learning_manager.providers.llm.meter import CostMeter


class FakeResponse:
    text = '{"ok": true}'
    usage_metadata = SimpleNamespace(prompt_token_count=11, candidates_token_count=7)


class FakeModels:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.requests: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> object:
        self.requests.append(kwargs)
        response = self._responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class FakeClient:
    models: FakeModels

    def __init__(self, models: FakeModels) -> None:
        self.models = models


def test_json_schema_is_sent_as_structured_output() -> None:
    models = FakeModels([FakeResponse()])
    provider = GeminiProvider(api_key="secret", client=FakeClient(models))

    provider.complete(
        system="s",
        user="u",
        schema_name="NextSessionDecision",
        json_schema={"type": "object", "properties": {}},
        temperature=0.8,
    )

    config = models.requests[0]["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema == {"type": "object", "properties": {}}
    assert config.temperature == 0
    assert models.requests[0]["model"] == "gemini-2.5-flash"


def test_response_is_parsed_and_usage_is_captured() -> None:
    models = FakeModels([FakeResponse()])
    response = GeminiProvider(api_key="secret", client=FakeClient(models)).complete(
        system="s", user="u"
    )

    assert response.parsed == {"ok": True}
    assert response.input_tokens == 11
    assert response.output_tokens == 7
    assert response.latency_ms >= 0


def test_transient_error_is_retried_then_succeeds() -> None:
    transient = RuntimeError("temporary")
    transient.status_code = 503  # type: ignore[attr-defined]
    models = FakeModels([transient, FakeResponse()])
    sleeps: list[float] = []
    provider = GeminiProvider(api_key="secret", client=FakeClient(models), sleep=sleeps.append)

    response = provider.complete(system="s", user="u")

    assert response.text
    assert len(models.requests) == 2
    assert sleeps == [0.5]


def test_non_transient_error_is_not_retried() -> None:
    error = RuntimeError("bad request")
    error.status_code = 400  # type: ignore[attr-defined]
    models = FakeModels([error])
    provider = GeminiProvider(api_key="secret", client=FakeClient(models))

    with pytest.raises(RuntimeError, match="bad request"):
        provider.complete(system="s", user="u")

    assert len(models.requests) == 1


@dataclass
class Settings:
    llm_mode: str
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    cassette_dir: Path = Path("fixtures/cassettes")
    fake_responses: list[str] | None = None


def test_build_llm_respects_mode_and_records_once(tmp_path: Path) -> None:
    meter = CostMeter()
    events: list[tuple[str, dict[str, object]]] = []
    trajectory = SimpleNamespace(step=lambda name, **fields: events.append((name, fields)))

    provider = build_llm(
        Settings(llm_mode="fake", fake_responses=["ok"]), meter=meter, trajectory=trajectory
    )
    assert isinstance(provider, FakeLLM)
    provider.complete(system="s", user="u")

    assert meter.totals().calls == 1
    assert len(events) == 1 and events[0][0] == "llm_call"

    replay = build_llm(
        Settings(llm_mode="replay", cassette_dir=tmp_path), meter=CostMeter(), trajectory=trajectory
    )
    assert isinstance(replay, CachedLLMProvider)


def test_live_mode_without_api_key_fails_with_clear_message(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="GEMINI_API_KEY"):
        build_llm(
            Settings(llm_mode="live", cassette_dir=tmp_path),
            meter=CostMeter(),
            trajectory=None,
        )
