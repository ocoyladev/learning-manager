from learning_manager.contracts import LLMResponse
from learning_manager.providers.llm.meter import PRICING, CostMeter


def test_meter_accumulates_tokens_cost_and_latency() -> None:
    meter = CostMeter()
    meter.record(
        LLMResponse(
            text="a",
            model="gemini-2.5-flash",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=120,
        )
    )
    meter.record(
        LLMResponse(
            text="b",
            model="gemini-2.5-flash",
            input_tokens=2000,
            output_tokens=100,
            latency_ms=80,
        )
    )

    totals = meter.totals()
    assert totals.calls == 2
    assert totals.input_tokens == 3000 and totals.output_tokens == 600
    assert totals.cost_usd == (3000 * PRICING["gemini-2.5-flash"][0] / 1_000_000) + (
        600 * PRICING["gemini-2.5-flash"][1] / 1_000_000
    )
    assert totals.latency_p50_ms == 100


def test_cache_hits_are_counted_but_cost_nothing() -> None:
    meter = CostMeter()
    meter.record(
        LLMResponse(
            text="a",
            model="gemini-2.5-flash",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1,
            cache_hit=True,
        )
    )

    totals = meter.totals()
    assert totals.calls == 1 and totals.cache_hits == 1
    assert totals.input_tokens == 1000 and totals.output_tokens == 500
    assert totals.cost_usd == 0.0


def test_unknown_model_does_not_crash_and_reports_zero_cost() -> None:
    meter = CostMeter()
    meter.record(LLMResponse(text="a", model="modelo-inventado", input_tokens=10, output_tokens=10))

    assert meter.totals().cost_usd == 0.0


def test_empty_meter_has_zero_percentiles() -> None:
    totals = CostMeter().totals()

    assert totals.calls == 0
    assert totals.latency_p50_ms == 0 and totals.latency_p95_ms == 0


def test_meter_reports_p95_for_multiple_latency_samples() -> None:
    meter = CostMeter()
    for latency in range(10, 21):
        meter.record(LLMResponse(text="x", model="fake", latency_ms=latency))

    assert meter.totals().latency_p95_ms == 19
