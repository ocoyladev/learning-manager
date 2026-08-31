from datetime import date

import pytest

from learning_manager.contracts import AuthorityType, Source
from learning_manager.providers.knowledge.authority import (
    classify_authority,
    extract_version,
    score_source,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://kubernetes.io/docs/x", AuthorityType.OFFICIAL),
        ("https://stackoverflow.com/questions/1", AuthorityType.FORUM),
        ("https://medium.com/x", AuthorityType.BLOG),
        ("https://x.example/k8s", AuthorityType.UNKNOWN),
    ],
)
def test_authority_classification(url: str, expected: AuthorityType) -> None:
    assert classify_authority(url, "t") is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("Next.js 15 introduces", "15"), ("Kubernetes v1.31", "1.31"), ("No version", None)],
)
def test_version_extraction(text: str, expected: str | None) -> None:
    assert extract_version(text, "") == expected


def test_official_recent_beats_old_blog() -> None:
    today = date(2026, 8, 30)
    official = Source(
        id="a",
        url="https://kubernetes.io/docs/x",
        title="t",
        authority=AuthorityType.OFFICIAL,
        published_at=date(2026, 6, 1),
        retrieved_at=today,
    )
    blog = official.model_copy(
        update={"id": "b", "authority": AuthorityType.BLOG, "published_at": date(2022, 1, 1)}
    )
    assert score_source(official, today) > score_source(blog, today)
