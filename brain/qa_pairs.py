"""QA pairs: (question, answer, citation) triples generated from knowledge chunks, so the persona
can answer a semantically-matched question with the EXACT source text instead of a paraphrase.

Anti-fabrication by construction: the answer is always the chunk's own text, verbatim -- never
LLM-written. The only LLM-dependent step is phrasing plausible QUESTIONS a reader might ask that a
given chunk would answer (grunt work: Sonnet/Haiku, never Opus), injected via `ask_fn` so this
module stays testable without any model and the production wiring (an in-session Claude Code
dispatch, mirroring eval/judge.py's "Opus in-session" pattern) lives at the call site.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .base import Chunk


@dataclass
class QAPair:
    id: str
    question: str
    answer: str    # verbatim chunk text -- never generated, so it can never be fabricated
    source: str    # knowledge_src filename this was mined from (matches Chunk.source)


def generate_qa_pairs(chunks: list[Chunk], ask_fn: Callable[[str], list[str]],
                      questions_per_chunk: int = 2) -> list[QAPair]:
    """Generate QA pairs from knowledge chunks.

    `ask_fn(chunk_text)` returns candidate questions for that chunk. Production wiring dispatches a
    Sonnet/Haiku subagent (see docs/QA_GENERATION.md); a bad or hallucinated question from ask_fn can
    at worst mis-phrase what's being asked -- the answer stays the real chunk text regardless.
    """
    pairs: list[QAPair] = []
    for i, chunk in enumerate(chunks):
        questions = [q.strip() for q in ask_fn(chunk.text) if q.strip()][:questions_per_chunk]
        for j, q in enumerate(questions):
            pairs.append(QAPair(id=f"qa_{i:04d}_{j}", question=q, answer=chunk.text, source=chunk.source))
    return pairs


def write_qa_pairs(pairs: list[QAPair], out_path: str | Path) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(asdict(pair), ensure_ascii=False) + "\n")


def write_qa_knowledge_md(pairs: list[QAPair], knowledge_dir: str | Path) -> list[str]:
    """Materialize QA pairs as knowledge_src/*.md files, so the SAME `brain.mine(knowledge_dir)`
    call that already indexes transcripts/articles also feeds mempalace drawers (or the inmemory
    index) from qa_pairs -- no Brain interface change needed. The question becomes the file's
    title (a lexical-match boost even outside the dedicated qa_search hybrid index); the body is
    the verbatim answer/chunk text.
    """
    kdir = Path(knowledge_dir)
    kdir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for pair in pairs:
        path = kdir / f"qa_{pair.id}.md"
        path.write_text(f"# {pair.question}\nsource: qa:{pair.source}\n\n{pair.answer}\n",
                        encoding="utf-8")
        written.append(str(path))
    return written


def read_qa_pairs(path: str | Path) -> list[QAPair]:
    p = Path(path)
    if not p.exists():
        return []
    out: list[QAPair] = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(QAPair(**json.loads(line)))
    return out
