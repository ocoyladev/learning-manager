import json
from pathlib import Path

import pytest

from learning_manager.providers.llm.cached import (
    CachedLLMProvider,
    CassetteError,
    CassetteMissError,
)
from learning_manager.providers.llm.fake import FakeLLM


def test_live_mode_records_and_replay_mode_reads(tmp_path: Path) -> None:
    inner = FakeLLM(responses=['{"ok": true}'])
    live = CachedLLMProvider(inner=inner, cassette_dir=tmp_path, mode="live")

    first = live.complete(system="s", user="u", schema_name="X")
    replay = CachedLLMProvider(inner=None, cassette_dir=tmp_path, mode="replay")
    second = replay.complete(system="s", user="u", schema_name="X")

    assert first.cache_hit is False and inner.calls == 1
    assert second.cache_hit is True
    assert second.text == first.text
    assert second.parsed == first.parsed


def test_replay_mode_never_calls_inner_provider(tmp_path: Path) -> None:
    writer = CachedLLMProvider(
        inner=FakeLLM(responses=["saved"]), cassette_dir=tmp_path, mode="live"
    )
    writer.complete(system="s", user="u")
    inner = FakeLLM(responses=["must not be used"])
    reader = CachedLLMProvider(inner=inner, cassette_dir=tmp_path, mode="replay")

    reader.complete(system="s", user="u")

    assert inner.calls == 0


def test_replay_mode_raises_a_helpful_error_on_a_miss(tmp_path: Path) -> None:
    replay = CachedLLMProvider(inner=None, cassette_dir=tmp_path, mode="replay")

    with pytest.raises(CassetteMissError) as exc:
        replay.complete(system="s", user="unknown", schema_name="X")

    assert "Cassette no encontrado" in str(exc.value)
    assert "make record" in str(exc.value)
    assert "GEMINI_API_KEY" in str(exc.value)


def test_key_changes_when_request_fields_change(tmp_path: Path) -> None:
    provider = CachedLLMProvider(
        inner=FakeLLM(responses=["a", "b", "c", "d"]),
        cassette_dir=tmp_path,
        mode="live",
        model="model-a",
    )
    provider.complete(system="s", user="u", schema_name="X", temperature=0)
    CachedLLMProvider(
        inner=FakeLLM(responses=["b"]), cassette_dir=tmp_path, mode="live", model="model-b"
    ).complete(system="s", user="u", schema_name="X", temperature=0)
    provider.complete(system="s2", user="u", schema_name="X", temperature=0)
    provider.complete(system="s", user="u2", schema_name="X", temperature=0)
    provider.complete(system="s", user="u", schema_name="Y", temperature=0)
    assert len(list(tmp_path.glob("*.json"))) == 5


def test_special_characters_cannot_collide_in_key(tmp_path: Path) -> None:
    provider = CachedLLMProvider(
        inner=FakeLLM(responses=["a", "b"]), cassette_dir=tmp_path, mode="live"
    )
    provider.complete(system="ab", user="c")
    provider.complete(system="a", user="bc")

    assert len(list(tmp_path.glob("*.json"))) == 2


def test_cassette_file_is_human_readable_and_contains_complete_request(tmp_path: Path) -> None:
    provider = CachedLLMProvider(
        inner=FakeLLM(responses=['{"ok": 1}']),
        cassette_dir=tmp_path,
        mode="live",
        model="gemini-2.5-flash",
    )
    provider.complete(
        system="sys",
        user="usr",
        schema_name="X",
        json_schema={"type": "object"},
        temperature=0.0,
    )

    cassette = next(tmp_path.glob("*.json"))
    raw = cassette.read_text()
    data = json.loads(raw)
    assert raw.endswith("\n")
    assert data["request"] == {
        "model": "gemini-2.5-flash",
        "system": "sys",
        "user": "usr",
        "schema_name": "X",
        "json_schema": {"type": "object"},
        "temperature": 0.0,
    }
    assert "response" in data and "recorded_at" in data


def test_malformed_cassette_is_reported_as_typed_error(tmp_path: Path) -> None:
    writer = CachedLLMProvider(inner=FakeLLM(responses=["ok"]), cassette_dir=tmp_path, mode="live")
    writer.complete(system="s", user="u")
    malformed = next(tmp_path.glob("*.json"))
    malformed.write_text("not json\n")
    reader = CachedLLMProvider(inner=None, cassette_dir=tmp_path, mode="replay")

    with pytest.raises(CassetteError, match="malformed"):
        reader.complete(system="s", user="u")
