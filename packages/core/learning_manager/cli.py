"""Small reproducible command-line tools for corpus maintenance."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import httpx
import typer

from learning_manager.providers.knowledge.authority import (
    classify_authority,
    extract_published_date,
    extract_version,
)
from learning_manager.providers.knowledge.live_search import LiveSearchProvider

app = typer.Typer()


def _topics(path: Path) -> dict[str, list[str]]:
    """Read the intentionally small ``topic: [url, ...]`` YAML subset."""
    result: dict[str, list[str]] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        topic, values = line.split(":", 1)
        result[topic.strip()] = [
            v.strip().strip("'\"") for v in values.strip().strip("[]").split(",") if v.strip()
        ]
    return result


@app.command("build-corpus")
def build_corpus(topics_file: Path, corpus_path: Path = Path("corpus")) -> None:
    """Capture configured URLs into a deterministic, auditable corpus."""
    captured = date.today().isoformat()
    for topic, urls in _topics(topics_file).items():
        folder = corpus_path / topic
        folder.mkdir(parents=True, exist_ok=True)
        manifest: list[dict[str, object]] = []
        with httpx.Client(
            timeout=15, follow_redirects=True, headers={"User-Agent": "LearningManager/0.1"}
        ) as client:
            for index, url in enumerate(urls, start=1):
                response = client.get(url)
                response.raise_for_status()
                html = response.text
                title = (
                    LiveSearchProvider._title(html) or urlparse(url).path.rsplit("/", 1)[-1] or url
                )
                source_id = f"{topic}-{index:02d}"
                filename = f"{index:02d}.md"
                (folder / filename).write_text(LiveSearchProvider._markdown(html) + "\n")
                published = extract_published_date(html)
                manifest.append(
                    {
                        "id": source_id,
                        "url": url,
                        "title": title,
                        "authority": classify_authority(url, title).value,
                        "version": extract_version(html, title),
                        "published_at": published.isoformat() if published else None,
                        "retrieved_at": captured,
                        "content_path": f"{topic}/{filename}",
                    }
                )
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        typer.echo(f"captured {len(manifest)} sources for {topic}")


if __name__ == "__main__":
    app()
