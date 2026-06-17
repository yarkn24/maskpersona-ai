"""Run the domain-adapted evaluation and trace it.

Core run_eval takes injectable answer_fn and judge_fn, so it is testable without any LLM:
- production answer_fn dispatches the persona agent (Opus in-session, or the Anthropic API),
- production judge_fn scores with the Opus judge (eval/judge.build_judge_prompt),
- tests pass fakes.
Every record is traced (LangSmith if configured, else local JSONL).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.gen_questions import generate  # noqa: E402
from eval.tracing import get_tracer  # noqa: E402
from eval.judge import heuristic_scores  # noqa: E402


def run_eval(cfg, answer_fn: Callable[[str], str], judge_fn: Callable[[dict, str], dict],
             n: int | None = None, tracer=None) -> list[dict]:
    tracer = tracer or get_tracer(cfg)
    records: list[dict] = []
    for q in generate(cfg, n):
        answer = answer_fn(q["question"])
        scores = judge_fn(q, answer)
        rec = {"id": q["id"], "category": q["category"], "question": q["question"],
               "answer": answer, "scores": scores}
        tracer.log(rec)
        records.append(rec)
    return records


def _dry_answer(_q: str) -> str:
    return "(dry-run: no model configured; wire an answer_fn that dispatches the persona agent)"


def _dry_judge(q: dict, answer: str) -> dict:
    return heuristic_scores(q["question"], answer, q.get("category", ""))


def main(argv: list[str] | None = None) -> int:
    import argparse
    from config import load_config
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", required=True,
                    help="path to a persona.yaml produced by onboarding")
    ap.add_argument("--n", type=int, default=None)
    args = ap.parse_args(argv)
    cfg = load_config(args.persona)
    tracer = get_tracer(cfg)
    recs = run_eval(cfg, _dry_answer, _dry_judge, n=args.n, tracer=tracer)
    print(f"eval: {len(recs)} questions, traced via {tracer.backend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
