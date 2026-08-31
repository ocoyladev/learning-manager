import pytest

from learning_manager.providers.llm.fake import FakeLLM


def test_fake_returns_json_and_tracks_prompt_and_calls() -> None:
    provider = FakeLLM(responses=['{"ok": true}'])

    response = provider.complete(
        system="system",
        user="prompt",
        schema_name="Result",
        json_schema={"type": "object"},
        temperature=0.8,
    )

    assert response.text == '{"ok": true}'
    assert response.parsed == {"ok": True}
    assert provider.calls == 1
    assert provider.last_user_prompt == "prompt"
    assert provider.last_temperature == 0.0


def test_fake_supports_callable_responses() -> None:
    provider = FakeLLM(responses=lambda prompt: prompt.upper())

    response = provider.complete(system="s", user="hello")

    assert response.text == "HELLO"
    assert response.parsed is None


def test_fake_raises_when_finite_responses_are_exhausted() -> None:
    provider = FakeLLM(responses=["only"])
    provider.complete(system="s", user="u")

    with pytest.raises(RuntimeError, match="exhausted"):
        provider.complete(system="s", user="u2")
