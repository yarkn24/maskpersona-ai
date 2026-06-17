"""Ingestion graph state passed between LangGraph nodes."""
from __future__ import annotations

from typing import Any, TypedDict


class VideoRef(TypedDict, total=False):
    id: str
    url: str
    title: str
    kind: str  # "solo" | "panel" | "unknown"


class IngestState(TypedDict, total=False):
    slug: str
    config: Any                       # PersonaConfig
    discovered: list[VideoRef]
    breadth: str                      # "niche" | "broad"
    scope_topics: list[str]           # chosen topics (broad figures)
    sizing: dict                      # est videos/hours/gb/files
    transcripts: dict                 # video_id -> transcript path
    fingerprint_path: str             # path to saved voice fingerprint
    isolated: dict                    # video_id -> list of kept turns (text)
    harvested_articles: list[dict]    # [{url, title, text, published_date, source}]
    knowledge_files: list[str]
    brain_status: dict
    citation_index: str
    errors: list[str]                 # non-fatal per-video skips
    approvals: dict                   # human gate answers (resume-safe)
