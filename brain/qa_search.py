"""Hybrid (lexical + optional embedding) search over generated QA pairs.

Lexical (idf-weighted token overlap) matches `brain/inmemory_adapter.py`'s scoring exactly and has
0 extra dependencies, so QA search always works out of the box. If the optional `qa` extra
(sentence-transformers) is installed, a local multilingual embedding model
(`intfloat/multilingual-e5-small`, MIT license, 0-token/offline, ~100 languages) is blended in --
semantic paraphrase matches ("what phone do you carry" vs a chunk about "the device I use daily")
that pure lexical overlap misses. Model choice + benchmark evidence: see docs/QA_GENERATION.md.

Chosen over all-MiniLM-L6-v2 specifically because personas cover public figures in any language, not
English only, and multilingual-e5-small keeps that same lightweight sentence-transformers footprint
while adding ~100-language coverage (all-MiniLM is English-only and, per HN/Supermemory benchmarking,
weaker on modern retrieval-quality benchmarks besides).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .base import Hit
from .qa_pairs import QAPair

_TOKEN = re.compile(r"[a-z0-9]+")
EMBED_MODEL = "intfloat/multilingual-e5-small"


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


@dataclass
class _Embedder:
    """Lazy, optional sentence-transformers wrapper. None if the `qa` extra isn't installed."""
    model: object = None
    tried: bool = False

    def get(self):
        if not self.tried:
            self.tried = True
            try:
                from sentence_transformers import SentenceTransformer  # lazy, optional dep
                self.model = SentenceTransformer(EMBED_MODEL)
            except Exception:
                self.model = None
        return self.model


_embedder = _Embedder()


def _cosine(a, b) -> float:
    import numpy as np
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class QASearch:
    """In-memory hybrid index over a persona's qa_pairs. No network beyond the one-time (optional,
    cached-by-huggingface-hub) embedding model download; searches themselves are fully offline."""

    def __init__(self) -> None:
        self._pairs: list[QAPair] = []
        self._question_tokens: list[Counter] = []
        self._idf: dict[str, float] = {}
        self._embeddings = None  # np.ndarray [n_pairs, dim] once computed, else None

    def index(self, pairs: list[QAPair]) -> int:
        self._pairs = pairs
        self._question_tokens = [Counter(_tokens(p.question)) for p in pairs]
        n = max(1, len(pairs))
        df: Counter = Counter()
        for tc in self._question_tokens:
            for tok in tc:
                df[tok] += 1
        self._idf = {tok: math.log((n + 1) / (d + 0.5)) for tok, d in df.items()}

        self._embeddings = None
        model = _embedder.get()
        if model is not None and pairs:
            import numpy as np
            self._embeddings = np.asarray(model.encode(
                [f"query: {p.question}" for p in pairs], normalize_embeddings=False))
        return len(pairs)

    def _lexical_scores(self, query_tokens: list[str]) -> list[float]:
        return [sum(self._idf.get(tok, 0.0) for tok in query_tokens if tok in tc)
                for tc in self._question_tokens]

    def _embedding_scores(self, query: str) -> list[float] | None:
        model = _embedder.get()
        if model is None or self._embeddings is None:
            return None
        q_emb = model.encode([f"query: {query}"], normalize_embeddings=False)[0]
        return [_cosine(q_emb, row) for row in self._embeddings]

    def search(self, query: str, k: int = 3, min_score: float = 0.05) -> list[Hit]:
        """Best QA-pair matches, blending lexical + (if available) embedding similarity.

        An empty result means "no confident QA hit" -- the caller (persona runtime) should fall
        back to full brain chunk search rather than surface a weak/irrelevant QA answer.
        """
        if not self._pairs:
            return []
        q_tokens = _tokens(query)
        lex = self._lexical_scores(q_tokens)
        max_lex = max(lex) if any(lex) else 1.0
        lex_norm = [s / max_lex for s in lex]

        emb = self._embedding_scores(query)
        if emb is not None:
            blended = [0.5 * lx + 0.5 * eb for lx, eb in zip(lex_norm, emb)]
        else:
            blended = lex_norm

        hits = [Hit(text=p.answer, source=p.source, score=round(s, 4))
                for p, s in zip(self._pairs, blended) if s >= min_score]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]

    def status(self) -> dict:
        return {"pairs": len(self._pairs), "embeddings": self._embeddings is not None,
                "embed_model": EMBED_MODEL if self._embeddings is not None else None}


def search_qa_pairs(qa_pairs_path: str, query: str, k: int = 3, min_score: float = 0.05) -> list[Hit]:
    """One-shot convenience: load qa_pairs.jsonl, index, search. Used by the persona runtime via a
    single `python3 -c "..."` Bash call (see templates/persona-agent.md.j2), so re-indexing per call
    is intentional -- a persona's QA set is small enough (low hundreds) for this to be instant."""
    from .qa_pairs import read_qa_pairs
    idx = QASearch()
    idx.index(read_qa_pairs(qa_pairs_path))
    return idx.search(query, k=k, min_score=min_score)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa-pairs", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()
    for h in search_qa_pairs(args.qa_pairs, args.query, k=args.k):
        print(f"[{h.score}] {h.source}: {h.text}")

