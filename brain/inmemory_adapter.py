"""In-memory Brain: offline, dependency-free, for the demo and tests.

Indexes knowledge chunks and ranks them by idf-weighted token overlap. No network, no external
service, so `make demo` and CI work anywhere without installing mempalace.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from .base import Brain, Chunk, Hit, read_knowledge_chunks

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class InMemoryBrain(Brain):
    def __init__(self, wing: str = "default") -> None:
        self.wing = wing
        self._chunks: list[Chunk] = []
        self._chunk_tokens: list[Counter] = []
        self._idf: dict[str, float] = {}

    def init(self) -> None:
        self._chunks = []
        self._chunk_tokens = []
        self._idf = {}

    def mine(self, knowledge_dir: str | Path) -> int:
        chunks = read_knowledge_chunks(knowledge_dir)
        self._chunks = chunks
        self._chunk_tokens = [Counter(_tokens(c.text)) for c in chunks]
        # idf over chunks
        n = max(1, len(chunks))
        df: Counter = Counter()
        for tc in self._chunk_tokens:
            for tok in tc:
                df[tok] += 1
        self._idf = {tok: math.log((n + 1) / (d + 0.5)) for tok, d in df.items()}
        return len(chunks)

    def search(self, query: str, k: int = 6) -> list[Hit]:
        q = _tokens(query)
        if not q or not self._chunks:
            return []
        scored: list[Hit] = []
        for chunk, tc in zip(self._chunks, self._chunk_tokens):
            score = sum(self._idf.get(tok, 0.0) for tok in q if tok in tc)
            if score > 0:
                scored.append(Hit(text=chunk.text, source=chunk.source, score=round(score, 4)))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:k]

    def status(self) -> dict:
        return {"backend": "inmemory", "wing": self.wing, "items": len(self._chunks)}
