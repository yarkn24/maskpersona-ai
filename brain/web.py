"""Web search fallback for persona agents.

When the brain is thin, the persona searches the web. If EXA_API_KEY is set in the environment,
Exa is used (grounded, full-text results). Otherwise search() returns [] and the agent falls back
to its built-in WebSearch/WebFetch tools. This module is invoked from a persona agent's Bash call
(the rendered agent's web-fallback step), not from the ingestion graph.

Install the search extra to enable Exa:
    pip install "maskpersona-ai[search]"
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
    """Search the web. Uses Exa if EXA_API_KEY is set and exa-py is installed; returns [] otherwise.

    Callers should fall back to the agent's built-in WebSearch/WebFetch tools when this returns [].
    """
    api_key = os.environ.get("EXA_API_KEY", "").strip()
    if not api_key:
        return []
    try:
        from exa_py import Exa
    except ImportError:
        return []

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
