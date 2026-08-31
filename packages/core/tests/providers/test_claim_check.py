from datetime import date

from learning_manager.contracts import AuthorityType, LLMResponse, Source
from learning_manager.providers.knowledge.claim_check import check_claims


class Provider:
    def fetch(self, source_id: str) -> str:
        return "Route handlers live in app/api/*/route.ts"


class LLM:
    def complete(self, **kwargs) -> LLMResponse:
        return LLMResponse(text='{"verdict":"supported"}', model="fake")


def test_claim_supported_by_source() -> None:
    source = Source(
        id="s",
        url="https://nextjs.org/docs",
        title="Routes",
        authority=AuthorityType.OFFICIAL,
        retrieved_at=date(2026, 8, 30),
    )
    verdict = check_claims(
        ["Route handlers live in app/api/*/route.ts"],
        [source],
        Provider(),
        LLM(),
        date(2026, 8, 30),
    )[0]
    assert verdict.verdict == "supported" and verdict.source_id == "s"
