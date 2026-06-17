# Spec: MaskPersona AI

> A Specs specification (MaskPersona AI's own spec-driven system; see SPECS.md). Generic and
> self-contained: no real person, path, or dataset appears here. Where an example name is unavoidable,
> the fictional placeholder **John Doe** is used.

## Problem

People want to consult the thinking of a public figure (an investor, a scientist, a founder, an author)
when making decisions, but that figure is not available. Generic chatbots answer in a neutral,
non-committal voice and fabricate quotes. We want a tool that, from a public figure's **public**
content, produces a grounded, partisan, citation-disciplined advisor bot, with one command, for any
figure, on any machine, lawfully.

## Goals

- **G1.** From a single input (a name), stand up a working persona advisor bot.
- **G2.** Ground every answer in the figure's public content (brain first, web second); refuse to fabricate.
- **G3.** Work for any public figure and any domain, in any language, with zero per-figure code changes.
- **G4.** Be reproducible: the same install produces the same system on every machine.
- **G5.** Be lawful by construction: public figures only, no bundled third-party content, clear disclaimers.

## Non-goals

- Modeling private individuals (explicitly refused).
- Redistributing anyone's copyrighted transcripts or audio.
- Replacing legal/financial/medical advice.

## User stories

- **US1.** As a user, I type a name and confirm "X (role), correct? (y/n)" once; the system does the rest.
- **US2.** As a user modeling a broad figure (e.g. John Doe, active across many fields), I am asked which
  topics to focus on, and shown an estimated volume ("~N videos, ~H hours, ~Z GB") before anything heavy runs.
- **US3.** As a user, if ingestion is interrupted, I can resume from where it stopped without re-downloading.
- **US4.** As a user, I get a bot that takes a clear stance in the figure's voice, cites sources, and
  refuses to invent quotes; it carries a standing "unendorsed persona" disclaimer.

## Functional requirements

- **FR1 Onboarding.** Accept a name; web-lookup; identity confirm gate; **public-figure gate** (refuse
  private individuals); infer domain + topics.
- **FR2 Adaptive scope.** Detect breadth. Narrow -> ingest all. Broad -> ask which topics to fix on.
- **FR3 Volume estimate.** After scope, estimate videos/hours/GB/files and require explicit approval.
- **FR4 Voice-fingerprint isolation.** Build the figure's voice embedding from solo videos; isolate
  their turns in panels by biometric match. No keyword/vocabulary heuristic.
- **FR5 Knowledge build.** Transcribe + diarize public videos; harvest public articles; write knowledge
  files; mine into an isolated brain. **The number and sub-topic split of knowledge files is decided at
  runtime by the ingestion agent, not fixed by the framework.**
- **FR6 Persona runtime.** Render a Claude Code agent that answers brain-first, partisan, cited, anti-fabrication.
- **FR7 Self-evaluation.** Generate ~100 domain-adapted questions; score on 5 generic dimensions; trace runs.
- **FR8 Auditor loop.** A bounded, evidence-driven loop that improves the persona within an allowlist.
- **FR9 Audit swarm.** Genericity, GDPR/legal, and generic-vs-case-specific text audits gate every release.
- **FR10 Deterministic install.** One master installer; pinned + locked parts; reproducible output.

## Constraints

- **C1.** English throughout the repo. Persona output language is configurable.
- **C2.** Zero real-person/owner/machine traces in the repo (enforced by audit + grep).
- **C3.** Brain backend = mempalace (public PyPI) by default, behind a swappable adapter.
- **C4.** No mandatory manual step or access token: the demo and core run with none, and the voice
  extra uses a public ONNX speaker model (no account/token). Optional extras (Exa, LangSmith) self-gate.

## Acceptance criteria

- **AC1.** `make demo` stands up the fictional John Doe persona offline (no network) and answers a
  question grounded + partisan + cited + with the disclaimer line.
- **AC2.** `grep` over the repo for real-person/owner/machine traces returns zero matches (only "John Doe").
- **AC3.** A malformed `persona.yaml` is rejected by schema validation; a valid one round-trips.
- **AC4.** Ingestion can be killed mid-run and resumed from checkpoint without re-downloading.
- **AC5.** `make audit` dispatches genericity + GDPR + legal + text-classifier agents for in-session
  review, writes `audit/legal_report.md` (a skeleton for the legal-lawyer agent to fill), and all four
  agents PASS when run by a reviewer.
- **AC6.** Every dispatched build/runtime agent receives the hidden injection preamble (verified by test).
