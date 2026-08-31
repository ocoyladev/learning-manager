"""Grounded URL discovery and bounded, robots-aware page fetching."""

from __future__ import annotations

import json
from datetime import date
from html.parser import HTMLParser
from typing import cast
from urllib.parse import urljoin

import httpx

from learning_manager.contracts import LLMProvider, Source

from .authority import classify_authority, extract_published_date, extract_version, score_source


class _MarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self._heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._heading = tag in {"h1", "h2", "h3"}

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self.lines.append(("# " if self._heading else "") + value)

    def handle_endtag(self, tag: str) -> None:
        self._heading = False


class LiveSearchProvider:
    def __init__(
        self, llm: LLMProvider, *, timeout: float = 15.0, user_agent: str = "LearningManager/0.1"
    ) -> None:
        self.llm = llm
        self.timeout = timeout
        self.user_agent = user_agent
        self._pages: dict[str, str] = {}

    def research(self, topic: str, *, k: int = 8) -> list[Source]:
        response = self.llm.complete(
            system="Discover authoritative sources.", user=topic, temperature=0.0
        )
        payload = response.parsed or json.loads(response.text)
        sources: list[Source] = []
        urls = cast(list[str], payload.get("urls", []))
        for url in urls[: min(k, 10)]:
            try:
                page = self._fetch_url(url)
            except (httpx.HTTPError, ValueError):
                continue
            title = self._title(page) or url
            retrieved = date.today()
            source = Source(
                id=f"live-{abs(hash(url))}",
                url=url,
                title=title,
                authority=classify_authority(url, title),
                version=extract_version(page, title),
                published_at=extract_published_date(page),
                retrieved_at=retrieved,
            )
            self._pages[source.id] = self._markdown(page)
            sources.append(source)
        return sorted(sources, key=lambda s: (-score_source(s, date.today()), s.id))[:k]

    def fetch(self, source_id: str) -> str:
        return self._pages[source_id]

    def _fetch_url(self, url: str) -> str:
        robots = urljoin(url, "/robots.txt")
        with httpx.Client(
            timeout=self.timeout, headers={"User-Agent": self.user_agent}, follow_redirects=True
        ) as client:
            robots_text = client.get(robots).text
            if any(line.strip().lower() == "disallow: /" for line in robots_text.splitlines()):
                raise ValueError("robots.txt disallows fetching")
            return client.get(url).text

    @staticmethod
    def _markdown(html: str) -> str:
        parser = _MarkdownParser()
        parser.feed(html)
        return "\n\n".join(parser.lines)

    @staticmethod
    def _title(html: str) -> str | None:
        parser = _MarkdownParser()
        parser.feed(html)
        return next((line[2:] for line in parser.lines if line.startswith("# ")), None)
