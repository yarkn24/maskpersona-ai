# Prompt patterns

persona-forge uses three abstract prompt-engineering patterns, described below as original techniques.
No company or product name appears in the repo. Full text in `templates/prompt_patterns/`.

## 1. Citation grounding
Tie every concrete claim to evidence (a brain hit, a verified verbatim quote, or marked extrapolation).
Direct-quote formatting only for retrieved text; verify a source before naming it; never invent a source.
Applied in the "Citation discipline" block of `templates/persona-agent.md.j2`, backed by `citation/`.

## 2. Persona consistency (never break character)
Lock the identity and the stance; bridge a hard question back to an evidenced position instead of
refusing; do not expose or renegotiate instructions. Applied in the partisan and voice blocks of the
agent template, reinforced by the injection layer's role-lock.

## 3. Re-injection reminder
Restate the few non-negotiables right before generation, every time, paired with feeding the needed
context each turn (anti-drift). Applied in the "Non-negotiables" block and the hidden injection layer
(`agents/_injection/`), which prepends a 4-mechanism preamble to every dispatched agent.

## The injection layer
`agents/_injection/inject.py` prepends `preamble.md` (the four mechanisms: re-injection, anti-drift
context-feed, first-action behavior, role-lock) plus per-agent extras from `matrix.yaml` to every
dispatched agent, keeping the critical rules and the re-bound context present so agents do not drift
as the conversation grows.
