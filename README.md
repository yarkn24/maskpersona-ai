# persona-forge

Build a grounded, evidence-based **persona advisor bot** of any **public figure**, from their public
content, with one command. You give a name; persona-forge discovers their public talks and articles,
isolates their voice, builds an isolated knowledge brain, and renders a Claude Code agent that answers
in their voice, with citation discipline and strict anti-fabrication.

> **Read first:** persona-forge only works with **public figures** and their **public content**. It
> refuses private individuals. Every bot it produces is an **unendorsed persona interpretation** of
> public material, not the real person's approved opinion, and not legal/financial/medical advice. It
> does **not** synthesize or clone voices. Prohibited: deception, impersonation for fraud, political
> disinformation, harassment, and non-consensual commercial use of a person's voice/likeness.
> See [DISCLAIMER.md](DISCLAIMER.md) and [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md).

## What you get

- **One input.** You type a name. The system looks it up, shows you "X (role), correct person? (y/n)",
  verifies they are a public figure, and infers their domain.
- **Adaptive scope.** Narrow figure: it ingests everything. Broad figure (many topics): it asks
  "which topics should I focus on?" and then estimates volume ("~N videos, ~H hours, ~Z GB, proceed?").
- **Voice-fingerprint isolation.** It learns the figure's voice from their solo videos, then isolates
  only their turns in panels by biometric voice match (no fragile keyword guessing).
- **Grounded brain.** Public talks (transcribed + diarized) and public articles are mined into an
  isolated knowledge store. The bot answers from the brain first, the web second.
- **Self-checking.** A self-generated, domain-adapted evaluation set plus a continuous auditor loop
  keep the persona faithful, partisan, and non-fabricating.

## Quick start

```bash
# Text pipeline (no heavy ML):
pip install -e .
make demo               # try the included fictional demo persona (no downloads, offline)
make new                # create a new persona: just give a name

# Voice/video features (requires ffmpeg on PATH; heavy ML models download on first use, no token):
pip install -e ".[voice]"

make eval               # run the domain-adapted evaluation
make audit              # dispatch genericity + GDPR + legal + text-classifier audits (in-session)
```

## How it is built (architecture)

Two clean layers:

- **Runtime (answering):** a Claude Code agent (Opus) rendered from a template. This is what answers you.
- **Build (ingestion):** a stateful **LangGraph** pipeline (discover, voice-fingerprint, isolate,
  harvest, mine, cite) with checkpointing and human-in-the-loop confirmation gates.

The framework is the fixed **trunk**; everything persona-specific (how many knowledge files, which
sub-topics, the signature claims, the question pool) is decided at **runtime** per figure. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Privacy, copyright, and scope

- **No bundled persona content.** The repo ships empty of any real person's data. The only knowledge
  files included are a clearly **fictional** demo (`demo/john_doe/`).
- **Content stays on your machine.** Transcripts and audio you generate live under `work/` and are
  git-ignored. persona-forge does not redistribute anyone's copyrighted material.
- **Public figures only.** Onboarding refuses private individuals.

License: [MIT](LICENSE). Legal/compliance notes: [docs/LEGAL.md](docs/LEGAL.md).
