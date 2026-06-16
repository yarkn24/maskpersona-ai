"""Map a phrase to its source in the persona's own knowledge corpus.

Generic re-implementation: instead of guessing, the persona's quotes are checked against the corpus of
its OWN knowledge files. A phrase that appears verbatim in the corpus gets a source; one that does not
gets no match. This is the anti-fabrication backbone for citations.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain.base import read_knowledge_chunks  # noqa: E402

_NONWORD = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")


def normalize(text: str, diacritic_map: dict[str, str] | None = None) -> str:
    t = text.lower()
    if diacritic_map:
        for k, v in diacritic_map.items():
            t = t.replace(k, v)
    t = _NONWORD.sub(" ", t)
    return _WS.sub(" ", t).strip()


def _tokens(text: str) -> list[str]:
    return [w for w in normalize(text).split() if len(w) >= 3]


@dataclass
class Citation:
    source: str
    kind: str   # "verbatim" | "approximate"
    snippet: str
    score: float


def cite(phrase: str, knowledge_dir: str | Path, k: int = 3,
         diacritic_map: dict[str, str] | None = None,
         approx_threshold: float = 0.6) -> list[Citation]:
    """Return citations for a phrase, verbatim matches first. Empty list if not grounded."""
    nphrase = normalize(phrase, diacritic_map)
    qtokens = [w for w in nphrase.split() if len(w) >= 3]
    if not qtokens:
        return []
    out: list[Citation] = []
    for chunk in read_knowledge_chunks(knowledge_dir):
        nchunk = normalize(chunk.text, diacritic_map)
        snippet = chunk.text.strip().splitlines()[0][:120]
        if nphrase and nphrase in nchunk:
            out.append(Citation(chunk.source, "verbatim", snippet, 1.0))
            continue
        present = sum(1 for w in set(qtokens) if w in nchunk)
        frac = present / len(set(qtokens))
        if frac >= approx_threshold:
            out.append(Citation(chunk.source, "approximate", snippet, round(frac, 3)))
    out.sort(key=lambda c: (c.kind != "verbatim", -c.score))
    return out[:k]


if __name__ == "__main__":
    import json
    if len(sys.argv) < 3:
        print("usage: python -m citation.cite '<phrase>' <knowledge_dir>")
        raise SystemExit(2)
    res = cite(sys.argv[1], sys.argv[2])
    print(json.dumps([c.__dict__ for c in res], indent=2))
