# Specs: MaskPersona AI's spec-driven build system

**Specs** is MaskPersona AI's own methodology for turning intent into a verified, reproducible build.
It uses a spec-first approach (write the specification before the code) and adds five things that
ordinary spec-then-tasks flows lack. It is self-contained and ships with the repo;
you do not need any external tool to use it.

## Why Specs exists (what it adds over a plain spec-then-tasks flow)

A plain flow is: spec -> plan -> task checklist -> run tasks, halt on failure. That is a good spine but
it drifts, it is not reproducible, and "done" is whatever the author says it is. Specs hardens all four:

1. **Enforced Constitution.** A short, binding set of non-negotiables (`constitution.md`) that *gates*
   every task. Violating the constitution fails the build; it is not advisory. (A plain flow keeps
   principles as prose nobody checks.)
2. **Verifiable Tasks.** Every task carries an explicit `verify:` command and a `done:` criterion and a
   `rollback:` note, not just a checkbox. A task is complete only when its `verify` passes, not when the
   author edits a `[ ]` to `[x]`.
3. **Phase Gates.** Tasks are grouped into phases; a phase cannot start until the previous phase's
   **gate** passes (schema validity + tests green). Gates make failure local and loud.
4. **Anti-drift Execution.** Before working a task, the executor re-binds the live context it needs
   (constitution + spec slice + the prior task's real output) instead of trusting memory. The executor
   feeds the needed context every turn rather than relying on what it remembers.
5. **Determinism Lock.** When a task produces a shippable artifact, its checksum is recorded. Re-running
   the build on another machine must reproduce the same artifacts (identical inputs produce identical outputs).

## Artifacts (in this folder)

| File | Role |
|---|---|
| `constitution.md` | binding non-negotiables; gates every task |
| `spec.md` | what we are building: goals, requirements, acceptance criteria (all testable) |
| `plan.md` | how: architecture, components, tech, risks |
| `tasks.md` | the dependency-ordered, **verifiable** task graph (id, deps, verify, done, rollback) |

## Lifecycle

```
constitution  ->  spec  ->  plan  ->  tasks  ->  gated-implement
   (binding)     (what)     (how)    (verifiable)   (phase gate after each phase)
```

## Execution protocol (how an agent runs tasks.md)

For each task, in dependency order:
1. **Bind:** load `constitution.md`, the relevant `spec.md` requirement, and the real output of the
   tasks this one depends on. Do not rely on memory.
2. **Build:** make only the change the task names (surgical; nothing speculative).
3. **Verify:** run the task's `verify:` command. If it fails, do NOT mark done; fix or `rollback:`.
4. **Lock:** if the task ships an artifact, record its checksum.
5. **Gate:** at the end of a phase, run the phase gate (constitution check + tests). The next phase
   does not start until the gate is green.

## Constitution-first rule

If any task would violate `constitution.md` (for example, writing a real person's name, a machine path,
or copyrighted content into the repo), the task is rejected before it runs. The constitution wins over
the spec, the plan, and the user's convenience.
