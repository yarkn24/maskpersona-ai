"""Scoring the persona's answers against the rubric.

Primary judge is Opus in-session (Claude Code dispatches the persona agent and scores with the rubric).
For headless/API or offline smoke runs, this module provides the rubric prompt builder and a light
heuristic fallback. The heuristic is a smoke signal only, never the authoritative score.
"""
from __future__ import annotations

RUBRIC_DIMS = ["partisanship", "persona_fidelity", "no_fabrication", "flexibility", "brain_grounded"]

_HEDGES = ["it depends", "on one hand", "on the other hand", "both views", "neutral", "balanced"]
_COMMIT = ["i would", "my view", "i think", "definitely", "no.", "yes.", "the answer is"]
_REFUSE = ["i did not say", "no source", "cannot quote", "i won't invent", "not in my content"]


def build_judge_prompt(question: str, answer: str, context: str = "") -> str:
    """The prompt an Opus judge uses to score one answer on the 5 rubric dimensions (0..1 each)."""
    dims = "\n".join(f"- {d}" for d in RUBRIC_DIMS)
    return (
        "Score the persona answer on each dimension from 0 to 1. Return JSON {dim: score}.\n"
        f"Dimensions:\n{dims}\n\n"
        f"Question:\n{question}\n\nAnswer:\n{answer}\n\n"
        f"Retrieved context (for brain_grounded):\n{context or '(none)'}\n"
    )


def heuristic_scores(question: str, answer: str, category: str = "") -> dict:
    """Cheap offline smoke scores. Not authoritative."""
    a = answer.lower()
    hedge = any(h in a for h in _HEDGES)
    commit = any(c in a for c in _COMMIT)
    refuse = any(r in a for r in _REFUSE)
    s = {
        "partisanship": 0.8 if commit and not hedge else (0.3 if hedge else 0.5),
        "persona_fidelity": 0.6 if len(answer) > 80 else 0.3,
        "no_fabrication": 1.0 if (category == "fabrication_trap" and refuse) else 0.6,
        "flexibility": 0.6,
        "brain_grounded": 0.6 if len(answer) > 80 else 0.3,
    }
    return {k: round(v, 3) for k, v in s.items()}
