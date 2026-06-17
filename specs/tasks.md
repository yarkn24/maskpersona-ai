# Tasks: MaskPersona AI (Specs verifiable task graph)

Dependency-ordered. Every task has `deps`, `verify`, `done`, `rollback`. A task is complete only when
`verify` passes. A phase cannot start until the previous phase's **Gate** is green (constitution check
+ tests). Status: `[ ]` todo, `[~]` in progress, `[x]` verified.

Legend per task: `verify:` command/check that proves it; `done:` the success criterion; `rollback:` how
to undo safely.

Note: unchecked `[ ]` tasks are roadmap items, not release blockers. The core framework (installer,
demo, injection layer, brain, pipeline, citation, eval, auditor, audit) is implemented and tested;
the task checkboxes were not retroactively ticked to preserve the verifiable task graph for future phases.

---

## Phase 0: Foundation

- [x] **T00 Repo skeleton** (deps: none)
  - `verify:` `git -C . rev-parse --is-inside-work-tree` true; root files present; `.gitignore` excludes work/, .env, content.
  - `done:` repo initialized, dir tree + README/LICENSE/DISCLAIMER/pyproject/Makefile exist.
  - `rollback:` remove the directory.

- [ ] **T01 Config layer** (deps: T00) -> `config/schema.py`, `config/persona.example.yaml`, `config/defaults.yaml`
  - `verify:` schema loads; example validates against schema; a deliberately malformed config is rejected.
  - `done:` every per-figure value has a schema field; all paths are home/repo-relative, no absolute paths.
  - `rollback:` delete config/ files; no other component depends yet.

- [ ] **T02 John Doe demo fixture** (deps: T01) -> `demo/john_doe/persona.yaml` + fictional `knowledge_src/*.md`
  - `verify:` demo persona.yaml validates; knowledge files match the knowledge-file schema; all marked FICTIONAL.
  - `done:` a self-contained fictional persona usable offline as the test fixture for everything downstream.
  - `rollback:` delete demo/john_doe/.

- [ ] **T03 Brain adapter** (deps: T01) -> `brain/base.py`, `mempalace_adapter.py`, `inmemory_adapter.py`, `registry.py`
  - `verify:` `inmemory` adapter mines demo knowledge and returns relevant hits for a query; registry selects by config.
  - `done:` abstract Brain interface (init/mine/search/status/sync) with two working backends.
  - `rollback:` delete brain/.

- [ ] **GATE 0:** constitution check + `pytest tests/test_config.py tests/test_brain.py` green.

## Phase 1: Persona surface

- [ ] **T04 Templates + prompt patterns** (deps: T01, T03) -> `templates/persona-agent.md.j2`, `command.md.j2`, `persona-core.md.j2`, `knowledge-file.md.j2`, `prompt_patterns/*`
  - `verify:` rendering with the John Doe config yields an agent file with no `{{ }}` left and a disclaimer line.
  - `done:` reusable behavior skeleton (source hierarchy, anti-fabrication, partisan, citation) with persona content as placeholders.
  - `rollback:` delete templates/.

- [ ] **T05 Hidden injection layer** (deps: T01) -> `agents/_injection/preamble.md`, `inject.py`, `matrix.yaml`
  - `verify:` `inject.py` prepends the preamble to a sample agent prompt; `matrix.yaml` selects per-agent extras; unit test asserts the five preamble mechanisms are present.
  - `done:` every dispatched agent provably receives re-injection + anti-drift context-feed + first-message + role-lock.
  - `rollback:` delete agents/_injection/.

- [ ] **T06 Citation system** (deps: T02, T03) -> `citation/cite.py`, `build_citations.py`, `corpus_gate.py`
  - `verify:` on demo data, a known fictional phrase maps to its source; an unrelated phrase returns no match (no false positive).
  - `done:` verbatim phrase -> source(+timestamp) gated by a persona-only corpus; language-config-driven normalization.
  - `rollback:` delete citation/.

- [ ] **GATE 1:** constitution + `pytest tests/test_templates.py tests/test_injection.py tests/test_citation.py` green.

## Phase 2: Build pipeline

- [ ] **T07 LangGraph pipeline** (deps: T01, T03, T06) -> `pipeline/state.py`, `pipeline/nodes.py`, `pipeline/interrupts.py`, `pipeline/checkpoint.py`, `pipeline/graph.py`, `pipeline/run_ingest.py`
  - `verify:` graph compiles; on a synthetic 2-speaker fixture `isolate_by_voice` keeps the right turns; kill+`--resume` continues from checkpoint without re-running completed nodes; `grep -c` for any vocab-heuristic == 0.
  - `done:` discover -> assess_breadth -> volume gate -> classify -> transcribe -> fingerprint -> isolate -> harvest -> write -> mine -> cite, with checkpointing and human interrupts.
  - `rollback:` delete pipeline/; nothing downstream is built yet.

- [ ] **GATE 2:** constitution + `pytest tests/test_pipeline.py` green.

## Phase 3: Evaluation and self-improvement

- [ ] **T08 Eval + tracing** (deps: T04, T03) -> `eval/RUBRIC.md`, `golden_seed.json`, `question_templates.yaml`, `gen_questions.py`, `run_eval.py`, `judge.py`, `tracing.py`
  - `verify:` generator emits ~100 domain-adapted questions for the demo domain; tracing writes to LangSmith if key set, else local JSONL (test both by unsetting the key).
  - `done:` self-generated domain-adapted eval over 5 generic rubric dims, traced.
  - `rollback:` delete eval/.

- [ ] **T09 Auditor loop** (deps: T08) -> `agents/auditor_agent.md`, `auditor/run_auditor.py`, `auditor/allowed_changes.yaml`
  - `verify:` one auditor round touches only allowlisted files (diff change_log/); a forbidden change is refused.
  - `done:` bounded, reversible, evidence-driven self-improvement loop with a clear stop condition.
  - `rollback:` revert via change_log/; delete auditor/.

- [ ] **GATE 3:** constitution + `pytest tests/test_eval.py tests/test_auditor.py` green.

## Phase 4: Install and docs

- [ ] **T10 Deterministic installer** (deps: all above) -> `installer/bootstrap.py`, `steps/*`, `helpers/*`, `lock/parts.lock.json`, `INSTALL.md`
  - `verify:` `make install --demo` in a temp clone stands up John Doe offline; parts.lock checksums match; ordered steps run dependencies-first.
  - `done:` one master installer (human `make` + agent `INSTALL.md`) producing identical output.
  - `rollback:` delete installer/ + INSTALL.md.

- [ ] **T11 Docs + CLAUDE.md** (deps: all above) -> `CLAUDE.md`, `docs/*`
  - `verify:` CLAUDE.md present and self-consistent; docs reference only real repo files; constitution clean.
  - `done:` architecture/pipeline/voice/patterns/onboarding/legal docs + the project CLAUDE.md.
  - `rollback:` delete docs/ + CLAUDE.md.

- [ ] **GATE 4:** constitution + tests + docs link-check.

## Phase 5: Release audit (the gate that ships)

- [ ] **T12 Audit swarm** (deps: all) -> `audit/run_audits.py`, `genericity_audit.md`, `gdpr_audit.md`, `text_classifier_audit.md`, `legal_lawyer_agent.md`
  - `verify:` `make audit` runs the four audits in parallel; all PASS; `audit/legal_report.md` produced.
  - `done:` no real-person/owner/machine trace; GDPR + legal posture documented; every text classified generic.
  - `rollback:` fix flagged items; re-run. Release is blocked until green.

- [ ] **RELEASE GATE:** all phase gates green + T12 PASS + final `make verify` green + git commit.
