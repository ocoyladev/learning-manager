"""Deterministic token, cost, and latency accounting for LLM responses."""

from __future__ import annotations

from dataclasses import dataclass

from learning_manager.contracts import LLMResponse

# Google AI Gemini Developer API standard text pricing, verified 2026-08-31:
# USD 0.30 input and USD 2.50 output per million tokens for gemini-2.5-flash.
PRICING: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.30, 2.50),
}


@dataclass(frozen=True)
class CostSummary:
    """Immutable aggregate of provider responses recorded in one run."""

    calls: int
    cache_hits: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_p50_ms: int
    latency_p95_ms: int

    @property
    def total_cost_usd(self) -> float:
        """Compatibility alias for consumers that call the aggregate total explicit."""
        return self.cost_usd


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    if len(values) == 1:
        return values[0]
    # Inclusive linear interpolation is deterministic and gives 100 for [80, 120].
    rank = (len(values) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    fraction = rank - lower
    return int(round(values[lower] + fraction * (values[upper] - values[lower])))


class CostMeter:
    """Accumulate response accounting without changing the response contract."""

    def __init__(self) -> None:
        self._responses: list[LLMResponse] = []

    def record(self, response: LLMResponse) -> None:
        self._responses.append(response)

    def totals(self) -> CostSummary:
        latencies = sorted(response.latency_ms for response in self._responses)
        input_tokens = sum(response.input_tokens for response in self._responses)
        output_tokens = sum(response.output_tokens for response in self._responses)
        cost = 0.0
        for response in self._responses:
            if response.cache_hit:
                continue
            input_price, output_price = PRICING.get(response.model, (0.0, 0.0))
            cost += response.input_tokens * input_price / 1_000_000
            cost += response.output_tokens * output_price / 1_000_000
        return CostSummary(
            calls=len(self._responses),
            cache_hits=sum(response.cache_hit for response in self._responses),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_p50_ms=_percentile(latencies, 0.5),
            latency_p95_ms=_percentile(latencies, 0.95),
        )
