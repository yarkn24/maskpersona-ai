# Plan: MaskPersona AI (technical)

> A Specs technical plan derived from spec.md (see SPECS.md). Generic; placeholder name is **John Doe**.

## Architecture: trunk vs branches

The framework is a fixed **trunk** (geography/natural borders). Everything persona-specific is a free
**branch/leaf** decided at runtime (cities/countries/flags). The trunk defines the *schema* and the
*decision instructions*; it never dictates how many knowledge files or sub-topics a figure gets.

| Layer | Fixed (trunk) | Free (branches, runtime) |
|---|---|---|
| identity | persona.yaml **schema** | the figure's name, bio, lens, topics |
| knowledge | knowledge-file **schema** | number of files, sub-topic split, claims |
| eval | 5 rubric dims + category shapes | the domain-specific question slots |

### Bounded freedom (enforced)
The user is free only within borders the framework draws. Enforced by: (1) schema validation,
(2) public-figure gate, (3) scope suggestion-list, (4) audit swarm (violation = build fail),
(5) auditor allowlist.

## Two runtimes

- **Answering runtime:** a Claude Code Opus agent rendered from `templates/persona-agent.md.j2`.
- **Build runtime:** a **LangGraph** stateful graph (`pipeline/graph.py`) with SQLite checkpointing and
  human-in-the-loop interrupts. LangGraph is used ONLY for ingestion, never for answering.

## Component map

- `config/` pydantic schema + defaults + .env.example. Single source of truth for all per-figure values.
- `brain/` abstract `Brain` adapter; default `mempalace_adapter`; `inmemory_adapter` for offline tests.
- `templates/` Jinja2 agent/command/core templates + abstract `prompt_patterns/`.
- `agents/` swarm (onboarding, render, ingestion, audits, legal, auditor) + `_injection/` hidden layer.
- `pipeline/` LangGraph nodes (in pipeline/nodes.py): discover, assess_breadth, estimate_volume,
  classify_solo_vs_panel, transcribe, extract_voice_fingerprint, isolate_by_voice, harvest_articles,
  write_knowledge, brain_ingest, refresh_citations.
- `citation/` verbatim phrase -> source+timestamp, gated by a persona-only corpus.
- `eval/` domain-adapted question generator, runner, judge, LangSmith-or-local tracing.
- `auditor/` bounded self-improvement loop.
- `audit/` genericity + GDPR + text-classifier + legal-lawyer agents + grep checks.
- `installer/` deterministic ordered bootstrap (the single ordered master install file).
- `demo/john_doe/` the only shipped (fictional) persona content.

## Hidden injection layer (abstract pattern, no verbatim third-party text)

Every dispatched agent gets a prepended, user-invisible preamble with five mechanisms:
non-negotiables re-injection (identity + core rules restated before every action), anti-drift
context-feed (needed config/prior output auto-fed, never trust memory), gates-first (run all gates
before work), role-lock, and safeguards-outrank-role-lock.
Implemented by `agents/_injection/{preamble.md,inject.py,matrix.yaml}`.

## Tech stack

Python 3.11+, pydantic v2, pyyaml, jinja2, langgraph (+sqlite checkpoint), langsmith, mempalace,
yt-dlp; voice extra: openai-whisper + sherpa-onnx (no token); eval extra: deepeval (optional).

## Reproducibility

Pinned `pyproject.toml` + `installer/lock/parts.lock.json` (checksums of every shipped part) +
schema-validated `persona.yaml` => identical agent files for identical inputs. All paths resolved at
runtime from home + repo-relative + config; no absolute machine paths in code.

## Risks / decisions

- No solo audio for a figure -> degraded/manual voice mode + low-confidence interrupt (never silent heuristic).
- voice model filename kept in `config/defaults.yaml` (churn-resistant).
- Brains live outside the git tree (`~/personaforge_brains/<slug>`).
- Auditor auto-applies only allowlisted, reversible changes (propose-only flag available).
