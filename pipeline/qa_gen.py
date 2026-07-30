"""Generate QA pairs from a persona's knowledge_src chunks (schema + anti-fabrication design in
`brain/qa_pairs.py`: the answer is always the chunk's own text, never LLM-written).

Mirrors `eval/run_eval.py`'s pattern exactly: `run()` takes an injectable `ask_fn` so it is testable
without any model. Production wiring is a Claude Code session dispatching a Sonnet/Haiku subagent per
chunk to phrase candidate questions (QA phrasing is grunt work; Opus is never used here, matching the
model-tiering already used for `eval.judge`'s heuristic/Opus split). A standalone CLI run without an
`ask_fn` wired is a dry-run stub (0 pairs), same shape as `eval.run_eval`'s `_dry_answer`.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brain.base import read_knowledge_chunks  # noqa: E402
from brain.qa_pairs import generate_qa_pairs, write_qa_knowledge_md, write_qa_pairs  # noqa: E402


def _dry_ask(_chunk_text: str) -> list[str]:
    return []  # dry-run: no model configured; wire an ask_fn that dispatches Sonnet/Haiku


def run(knowledge_dir: str | Path, out_path: str | Path,
       ask_fn: Callable[[str], list[str]] = _dry_ask, questions_per_chunk: int = 2) -> int:
    chunks = read_knowledge_chunks(knowledge_dir)
    pairs = generate_qa_pairs(chunks, ask_fn, questions_per_chunk)
    write_qa_pairs(pairs, out_path)
    # Materialize into the SAME knowledge_dir so the next brain_ingest (mine()) call picks up the
    # QA pairs automatically, same as any other knowledge_src file -- no Brain interface change.
    write_qa_knowledge_md(pairs, knowledge_dir)
    return len(pairs)


def main(argv: list[str] | None = None) -> int:
    import argparse
    from config import load_config
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", required=True, help="path to a persona.yaml")
    args = ap.parse_args(argv)
    cfg = load_config(args.persona)
    kdir = cfg.work_dir / "knowledge_src"
    n = run(kdir, cfg.qa.qa_pairs_path, questions_per_chunk=cfg.qa.questions_per_chunk)
    print(f"qa_gen: {n} QA pairs written to {cfg.qa.qa_pairs_path} "
         f"(dry-run: 0 unless an ask_fn dispatching a model is wired)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
