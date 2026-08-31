import json
from datetime import date

import respx

from learning_manager.contracts import AuthorityType, LLMResponse
from learning_manager.providers.knowledge.live_search import LiveSearchProvider
from learning_manager.providers.knowledge.notebooklm_stub import NotebookLMProvider


class FakeLLM:
    def complete(self, **kwargs) -> LLMResponse:
        return LLMResponse(
            text=json.dumps({"urls": ["https://kubernetes.io/docs/x"]}), model="fake"
        )


@respx.mock
def test_urls_are_classified_and_pages_markdown() -> None:
    respx.get("https://kubernetes.io/robots.txt").respond(text="User-agent: *\nAllow: /")
    respx.get("https://kubernetes.io/docs/x").respond(
        text='<meta property="article:published_time" content="2026-06-01"><h1>T</h1><p>C</p>'
    )
    provider = LiveSearchProvider(FakeLLM())
    source = provider.research("services")[0]
    assert source.authority is AuthorityType.OFFICIAL and source.published_at == date(2026, 6, 1)
    assert "# T" in provider.fetch(source.id)


def test_notebooklm_stub_explains_policy() -> None:
    try:
        NotebookLMProvider().research("x")
    except NotImplementedError as exc:
        assert "unofficial" in str(exc)
