import json

import pytest

from learning_manager.contracts import AuthorityType
from learning_manager.providers.knowledge.corpus import CorpusProvider, TopicNotInCorpusError


@pytest.fixture
def tmp_corpus(tmp_path):
    topic = tmp_path / "kubernetes-services"
    topic.mkdir()
    manifest = [
        {
            "id": "official",
            "url": "https://kubernetes.io/docs/x",
            "title": "Official",
            "authority": "official",
            "published_at": "2026-06-01",
            "retrieved_at": "2026-08-30",
            "content_path": "kubernetes-services/official.md",
        },
        {
            "id": "blog",
            "url": "https://medium.com/x",
            "title": "Blog",
            "authority": "blog",
            "published_at": "2022-01-01",
            "retrieved_at": "2026-08-30",
            "content_path": "kubernetes-services/blog.md",
        },
    ]
    (topic / "manifest.json").write_text(json.dumps(manifest))
    (topic / "official.md").write_text("ClusterIP content")
    (topic / "blog.md").write_text("Blog content")
    return tmp_path


def test_research_returns_ranked_sources(tmp_corpus) -> None:
    sources = CorpusProvider(tmp_corpus).research("kubernetes-services", k=2)
    assert sources[0].authority is AuthorityType.OFFICIAL


def test_fetch_returns_markdown(tmp_corpus) -> None:
    provider = CorpusProvider(tmp_corpus)
    provider.research("kubernetes-services")
    assert "ClusterIP" in provider.fetch("official")


def test_unknown_topic_raises(tmp_corpus) -> None:
    with pytest.raises(TopicNotInCorpusError):
        CorpusProvider(tmp_corpus).research("missing")
