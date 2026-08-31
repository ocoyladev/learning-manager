"""Deterministic source authority, version, and freshness scoring."""

from __future__ import annotations

import re
from contextlib import suppress
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urlparse

from learning_manager.contracts import AuthorityType, Source

_OFFICIAL = {"kubernetes.io", "docs.docker.com", "docker.com", "nextjs.org"}
_VENDOR = {"cloud.google.com", "aws.amazon.com", "learn.microsoft.com"}
_VERSION = re.compile(
    r"(?i)(?:next\.js|kubernetes|docker\s*(?:compose)?|v)\s*v?([0-9]+(?:\.[0-9]+)*)"
)


def classify_authority(url: str, title: str) -> AuthorityType:
    host = urlparse(url).hostname or ""
    host = host.lower().removeprefix("www.")
    if host in _OFFICIAL or any(host.endswith("." + d) for d in _OFFICIAL):
        return AuthorityType.OFFICIAL
    if host in _VENDOR or any(host.endswith("." + d) for d in _VENDOR):
        return AuthorityType.VENDOR
    if host in {"stackoverflow.com", "stackexchange.com"}:
        return AuthorityType.FORUM
    if host in {"medium.com", "dev.to"}:
        return AuthorityType.BLOG
    if "tutorial" in host or "tutorial" in url.lower():
        return AuthorityType.TUTORIAL
    return AuthorityType.UNKNOWN


def extract_version(text: str, title: str) -> str | None:
    match = _VERSION.search(f"{title} {text}")
    return match.group(1) if match else None


class _DateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.value: date | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        raw = values.get("content") if tag == "meta" else None
        prop = values.get("property") or ""
        name = (values.get("name") or "").lower()
        if raw and (prop.endswith("published_time") or name in {"date", "datepublished"}):
            with suppress(ValueError):
                self.value = date.fromisoformat(raw[:10])


def extract_published_date(html: str) -> date | None:
    parser = _DateParser()
    parser.feed(html)
    return parser.value


def score_source(source: Source, today: date) -> float:
    authority_weight = {
        AuthorityType.OFFICIAL: 1.0,
        AuthorityType.VENDOR: 0.9,
        AuthorityType.BOOK: 0.8,
        AuthorityType.BLOG: 0.5,
        AuthorityType.TUTORIAL: 0.4,
        AuthorityType.FORUM: 0.3,
        AuthorityType.UNKNOWN: 0.2,
    }[source.authority]
    freshness = (
        0.5
        if source.published_at is None
        else max(0.1, 1.0 - max(0, (today - source.published_at).days) / 3650)
    )
    return authority_weight * freshness
