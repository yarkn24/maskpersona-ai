# Constitution: MaskPersona AI

Binding non-negotiables. Under the **Specs** system these gate every task: a task that would violate
any article is rejected before it runs. The constitution wins over the spec, the plan, and convenience.

## Article 1: Zero real-person data
No real person's name, biography, quote, path, transcript, audio, or dataset appears anywhere in this
repository. The only example identity permitted is the fictional placeholder **John Doe**. Real
persona content exists only at runtime, under git-ignored `work/<slug>/`, on the user's own machine.

## Article 2: Runtime-resolved paths
No absolute machine path is hardcoded. Every path resolves at runtime from the user's home directory,
a repo-relative location, or `persona.yaml`. The system must run identically on any machine.

## Article 3: Public figures only
Onboarding verifies the target is a genuine public figure with public content and refuses private
individuals. The framework processes only publicly accessible material.

## Article 4: No bundled or redistributed content
The repo ships no third-party copyrighted content. Generated transcripts and audio stay local and
git-ignored. The only knowledge files in the repo are the clearly fictional `demo/john_doe/` set.

## Article 5: No verbatim third-party text; no persona-specific names hardcoded
Techniques may be learned from public material, but no verbatim third-party system text is copied into
the repo; only abstract, re-implemented patterns. Third-party tool and library names (e.g. LangGraph,
mempalace, yt-dlp, Exa) are unavoidable and allowed. The constraint is that no real persona's company
or product names are hardcoded anywhere in the framework; those exist only in runtime-generated files
under git-ignored `work/`.

## Article 6: Grounded, not fabricated
The persona runtime answers brain-first, web-second, takes a clear stance, cites sources, and refuses
to invent quotes, numbers, or events. Extrapolation beyond evidence is marked explicitly.

## Article 7: Bounded freedom (trunk vs branches)
The framework is the fixed trunk: schema, pipeline logic, adapters, templates' behavior skeleton,
audits, installer order, injection layer. Persona-specific shape (how many knowledge files, sub-topics,
claims, questions) is decided freely at runtime within the borders the trunk draws and enforces.

## Article 8: Determinism
Pinned dependencies, locked part checksums, and schema-validated config make the build reproducible.
The same inputs produce the same artifacts on every machine.

## Article 9: English repo
All code, docs, comments, and prompts in the repo are in English. The persona's output language is a
runtime configuration value, not a repo-level choice.

## Enforcement
Articles are checked by: schema validation (config), the public-figure gate (onboarding), the audit
swarm at build end (genericity, GDPR/legal, generic-vs-case-specific text), and the auditor allowlist.
A violation is a build failure, not a warning.
