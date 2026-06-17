"""Exa-backed web search for public-figure article harvesting.

Lazy import: importing this module is safe even when exa-py is not installed.
The client only fails at *call time* if the package or API key is absent.
Falls back gracefully so nodes that use it can degrade without crashing.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchResult:
    url: str
    title: str
    text: str = ""
    published_date: Optional[str] = None


@dataclass
class ExaSearchClient:
    """Thin wrapper around exa-py's Exa client.

    Uses `EXA_API_KEY` from the environment (loaded from .env by the installer).
    Returns an empty list when the key is absent or the package is not installed,
    so callers do not need to guard against None.
    """
    api_key: str = field(default_factory=lambda: os.getenv("EXA_API_KEY", ""))
    result_count: int = 10
    use_autoprompt: bool = True

    def available(self) -> bool:
        """True only when both the package is installed and a key is configured."""
        if not self.api_key:
            return False
        try:
            import exa_py  # noqa: F401
            return True
        except ImportError:
            return False

    def search_person(self, name: str, topics: list[str]) -> list[SearchResult]:
        """Search for public content by a named person across given topics.

        Returns up to `result_count` results with full text when available.
        Never raises: errors are caught and logged to stderr.
        """
        if not self.available():
            return []
        try:
            from exa_py import Exa
            client = Exa(api_key=self.api_key)
            topic_str = ", ".join(topics[:4]) if topics else "public talks interviews"
            query = f'{name} talks about {topic_str}'
            response = client.search_and_contents(
                query,
                num_results=self.result_count,
                use_autoprompt=self.use_autoprompt,
                text=True,
            )
            return [
                SearchResult(
                    url=r.url,
                    title=r.title or "",
                    text=r.text or "",
                    published_date=getattr(r, "published_date", None),
                )
                for r in response.results
            ]
        except Exception as exc:
            import sys
            print(f"[search] exa error: {exc!r}", file=sys.stderr)
            return []

    def search_urls(self, urls: list[str]) -> list[SearchResult]:
        """Fetch full text for a known list of URLs via Exa's contents endpoint."""
        if not self.available() or not urls:
            return []
        try:
            from exa_py import Exa
            client = Exa(api_key=self.api_key)
            response = client.get_contents(urls, text=True)
            return [
                SearchResult(
                    url=r.url,
                    title=r.title or "",
                    text=r.text or "",
                    published_date=getattr(r, "published_date", None),
                )
                for r in response.results
            ]
        except Exception as exc:
            import sys
            print(f"[search] exa get_contents error: {exc!r}", file=sys.stderr)
            return []
