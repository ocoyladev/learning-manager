"""Deterministic conflict resolution for claims against ranked sources."""

from __future__ import annotations

import json
from datetime import date
from typing import Literal, cast

from pydantic import BaseModel

from learning_manager.contracts import KnowledgeProvider, LLMProvider, Source

from .authority import score_source


class ClaimVerdict(BaseModel):
    claim: str
    verdict: Literal["supported", "outdated", "unsupported"]
    source_id: str | None = None
    reason: str


def check_claims(
    claims: list[str],
    sources: list[Source],
    provider: KnowledgeProvider,
    llm: LLMProvider,
    today: date,
) -> list[ClaimVerdict]:
    results: list[ClaimVerdict] = []
    ranked = sorted(sources, key=lambda s: (-score_source(s, today), s.id))
    for claim in claims:
        candidates: list[tuple[Source, str, str]] = []
        for source in ranked:
            content = provider.fetch(source.id)
            response = llm.complete(
                system="Classify whether the source supports or contradicts the claim.",
                user=json.dumps({"claim": claim, "source": content}),
                temperature=0.0,
            )
            payload = response.parsed or json.loads(response.text)
            relation = str(payload.get("verdict", payload.get("relation", "unsupported"))).lower()
            if relation in {"supported", "supports", "support"}:
                candidates.append(
                    (source, "supported", str(payload.get("reason", "Supported by source.")))
                )
            elif relation in {"outdated", "contradicted", "contradicts", "contradiction"}:
                candidates.append(
                    (
                        source,
                        "outdated",
                        str(payload.get("reason", "Contradicted by a newer source.")),
                    )
                )
        if not candidates:
            results.append(
                ClaimVerdict(
                    claim=claim,
                    verdict="unsupported",
                    source_id=None,
                    reason="No supplied source supports this claim.",
                )
            )
        else:
            source, verdict, reason = sorted(
                candidates, key=lambda item: (-score_source(item[0], today), item[0].id)
            )[0]
            results.append(
                ClaimVerdict(
                    claim=claim,
                    verdict=cast(Literal["supported", "outdated", "unsupported"], verdict),
                    source_id=source.id,
                    reason=reason,
                )
            )
    return results
