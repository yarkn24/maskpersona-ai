"""Persona-only corpus gate.

Answers: does this text actually come from the persona's own knowledge corpus? Used to stop a segment
(e.g. a panel turn that might belong to another speaker, or an invented line) from being attributed to
the persona. In MaskPersona AI the primary speaker separation is biometric (voice fingerprint); this
text gate is a second, cheap safety net.
"""
from __future__ import annotations

from pathlib import Path

from .cite import _tokens, normalize
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain.base import read_knowledge_chunks  # noqa: E402


def is_persona_segment(text: str, knowledge_dir: str | Path,
                       diacritic_map: dict[str, str] | None = None,
                       min_overlap: float = 0.5) -> bool:
    """True if text substantially appears in the persona's corpus (token overlap >= min_overlap)."""
    qt = set(_tokens(text))
    if not qt:
        return False
    ntext = normalize(text, diacritic_map)
    for chunk in read_knowledge_chunks(knowledge_dir):
        nchunk = normalize(chunk.text, diacritic_map)
        if ntext and ntext in nchunk:
            return True
        present = sum(1 for w in qt if w in nchunk)
        if present / len(qt) >= min_overlap:
            return True
    return False
