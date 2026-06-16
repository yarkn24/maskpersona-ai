"""Abstract Brain interface.

A Brain is the persona's knowledge store. The framework talks to it only through this interface, so
the backend is swappable (mempalace by default, inmemory for offline demo/tests) and testable.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Hit:
    text: str
    source: str
    score: float


@dataclass
class Chunk:
    text: str
    source: str


def read_knowledge_chunks(knowledge_dir: str | Path) -> list[Chunk]:
    """Split every knowledge_src/*.md into chunks (one per '##' section, else whole file).

    Shared by adapters so they agree on what a 'chunk' is. The schema is: a '# Title' line, a
    'Source:' line, a 'Confidence:' line, then '##' sections.
    """
    chunks: list[Chunk] = []
    for md in sorted(Path(knowledge_dir).glob("*.md")):
        text = md.read_text(encoding="utf-8")
        sections = re.split(r"\n(?=##\s)", text)
        for sec in sections:
            body = sec.strip()
            if len(body) >= 40:
                chunks.append(Chunk(text=body, source=md.name))
    return chunks


class Brain(ABC):
    """Knowledge store contract: init, mine a knowledge dir, search, report status, sync."""

    @abstractmethod
    def init(self) -> None:
        """Create/prepare an empty brain."""

    @abstractmethod
    def mine(self, knowledge_dir: str | Path) -> int:
        """Index all knowledge files under knowledge_dir. Returns number of items indexed."""

    @abstractmethod
    def search(self, query: str, k: int = 6) -> list[Hit]:
        """Return up to k relevant hits for query, most relevant first."""

    @abstractmethod
    def status(self) -> dict:
        """Return a small status dict (e.g. item count, backend name)."""

    def sync(self) -> None:
        """Reconcile/prune the index. Default: no-op."""
        return None
