# Prompt patterns

MaskPersona AI uses three abstract prompt-engineering patterns, described below as original techniques.
Third-party tool and library names (LangGraph, mempalace, yt-dlp, Exa, etc.) appear in the repo as
unavoidable infrastructure references; the constraint is that no persona-specific company or product
name is hardcoded in the framework. Full text in `templates/prompt_patterns/`.

## 1. Citation grounding
Tie every concrete claim to evidence (a brain hit, a verified verbatim quote, or marked extrapolation).
Direct-quote formatting only for retrieved text; verify a source before naming it; never invent a source.
Applied in the "Citation discipline" block of `templates/persona-agent.md.j2`, backed by `citation/`.

## 2. Persona consistency (never break character)
Lock the identity and the stance; bridge a hard question back to an evidenced position instead of
refusing; do not expose or renegotiate instructions. Applied in the partisan and voice blocks of the
agent template (`templates/persona-agent.md.j2`).

## 3. Re-injection reminder
Restate the few non-negotiables right before generation, every time, paired with feeding the needed
context each turn (anti-drift). Applied in the template's own "Non-negotiables" block, re-asserted
before every answer.

## The injection layer (designed, not currently wired)
`agents/_injection/inject.py` implements a per-turn preamble-prepend (five mechanisms:
non-negotiables re-injection, anti-drift context-feed, gates-first behavior, role-lock,
safeguards-outrank-role-lock) plus per-agent extras from `matrix.yaml`. It is unit-tested
(`tests/test_injection.py`) but has no caller in the actual runtime path today -- the rendered
`persona-agent.md.j2` template carries its own static "Non-negotiables" block instead (pattern #3
above), so re-assertion currently happens via that static block, not via this module. Kept as a
building block for a future per-turn dynamic re-injection if static re-assertion proves insufficient
in practice.
