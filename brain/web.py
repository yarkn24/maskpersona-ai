"""Web search fallback for persona agents.

When the brain is thin, the persona searches the web. If EXA_API_KEY is set in the environment,
Exa is used (grounded, full-text results). Otherwise the agent falls back to its built-in
WebSearch/WebFetch tools. This module is called by the ingestion pipeline and by agent Bash calls.

Install the search extra to enable Exa:
    pip install "persona-forge[search]"
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class WebResult:
    title: str
    url: str
    text: str


def search(query: str, num_results: int = 5) -> list[WebResult]:
    """Search the web. Uses Exa if EXA_API_KEY is set, else raises with a clear message."""
    api_key = os.environ.get("EXA_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "EXA_API_KEY not set. Add it to .env and install: pip install 'persona-forge[search]'. "
            "Without it, use the agent's built-in WebSearch/WebFetch tools instead."
        )
    try:
        from exa_py import Exa
    except ImportError as exc:
        raise ImportError(
            "exa-py is not installed. Run: pip install 'persona-forge[search]'"
        ) from exc

    client = Exa(api_key=api_key)
    response = client.search_and_contents(query, num_results=num_results, text=True)
    return [
        WebResult(title=r.title or "", url=r.url, text=(r.text or "").strip())
        for r in response.results
    ]


def available() -> bool:
    """True if EXA_API_KEY is set and exa-py is installed."""
    if not os.environ.get("EXA_API_KEY", "").strip():
        return False
    try:
        import exa_py  # noqa: F401
        return True
    except ImportError:
        return False
