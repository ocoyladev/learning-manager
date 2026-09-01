"""Frozen, stateless single-prompt baseline used for comparison."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learning_manager.contracts import LLMProvider, NextSessionDecision



_PROMPT = Path(__file__).with_name("prompt.md").read_text(encoding="utf-8")


def run_baseline(case: dict[str, Any], llm: LLMProvider) -> NextSessionDecision:
    """Ask the model once with the complete case and parse its unverified decision."""
    response = llm.complete(
        system=_PROMPT.split("\nINPUT:", maxsplit=1)[0],
        user=_PROMPT + "\n" + json.dumps(case, sort_keys=True, default=str),
        schema_name="NextSessionDecision",
        temperature=0.0,
    )
    payload = response.parsed or json.loads(response.text)
    return NextSessionDecision.model_validate(payload)
