"""Deterministic source citation metrics."""

from __future__ import annotations

from learning_manager.providers.knowledge.claim_check import ClaimVerdict
from pydantic import BaseModel


class SourceReport(BaseModel):
    source_support_rate: float
    outdated_claim_rate: float
    traceability: float


def grade_sources(lesson_claims: list[ClaimVerdict], case: dict[str, object],
                  corpus_ids: set[str]) -> SourceReport:
    del case
    if not lesson_claims:
        return SourceReport(source_support_rate=0.0, outdated_claim_rate=0.0, traceability=0.0)
    cited = [claim for claim in lesson_claims if claim.source_id]
    valid = [claim for claim in cited if claim.source_id in corpus_ids]
    return SourceReport(
        source_support_rate=sum(claim.verdict == "supported" and claim.source_id in corpus_ids
                                for claim in lesson_claims) / len(lesson_claims),
        outdated_claim_rate=sum(claim.verdict == "outdated" for claim in lesson_claims) / len(lesson_claims),
        traceability=len(valid) / len(cited) if cited else 0.0,
    )
