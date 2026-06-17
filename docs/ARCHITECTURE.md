# Architecture

## Trunk vs branches
The framework is a fixed **trunk**: schema, pipeline logic, adapters, the templates' behavior skeleton,
the injection layer, audits, and the installer order. Everything persona-specific (how many knowledge
files, which sub-topics, the signature claims, the question pool) is a **branch** decided at runtime by
the ingestion/onboarding agents. The trunk defines the schema and the decision rules; it never dictates
the branching. See `specs/constitution.md` Article 7 and `specs/SPECS.md`.

## Two runtimes
- **Answering runtime:** a Claude Code Opus agent rendered from `templates/persona-agent.md.j2`. This is
  what answers the user. It queries the brain first, the web second, partisan and citation-disciplined.
- **Build runtime:** a stateful LangGraph pipeline (`pipeline/graph.py`) with SQLite checkpointing and
  human-in-the-loop gates. LangGraph orchestrates ONLY ingestion, never answering.

## Components
| Area | Path | Purpose |
|---|---|---|
| config | `config/` | pydantic schema + loader (single source of truth for per-figure values) |
| brain | `brain/` | swappable knowledge store (inmemory offline, mempalace default) |
| templates | `templates/` | persona agent/command/core + abstract prompt patterns |
| injection | `agents/_injection/` | hidden 5-mechanism preamble prepended to every agent |
| pipeline | `pipeline/` | LangGraph ingestion incl. voice-fingerprint isolation |
| citation | `citation/` | verbatim phrase to source, persona-only corpus gate |
| eval | `eval/` | domain-adapted questions, tracing, judging |
| auditor | `auditor/` | bounded self-improvement loop |
| audit | `audit/` | release audits (genericity, GDPR, text, legal) |
| installer | `installer/` | one deterministic ordered bootstrap |

## Build discipline
Built with **Specs** (`specs/SPECS.md`): constitution to spec to plan to verifiable tasks to gated
implement. Each phase ends with a gate (constitution check + tests).
