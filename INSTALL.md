# INSTALL: the agent-executable install

This is the single, ordered install an AI agent can follow to stand up MaskPersona AI. It runs the SAME
steps as `make install`, so the result is identical. Do the steps in order; do not skip a gate. Full
content only, no placeholders. Resolve every path at runtime; never hardcode an absolute machine path.

## Order (dependencies first)

1. **Preflight.** Confirm Python >= 3.11. `python -m installer.bootstrap` runs `step_00_preflight`.
2. **Dependencies.** Install the pinned deps from `pyproject.toml` into a venv.
   - Voice isolation: `pip install "maskpersona-ai[voice]"` (models download automatically on first run, no token needed).
   - Web search via Exa: `pip install "maskpersona-ai[search]"` then add `EXA_API_KEY=...` to `.env`.
     Without this, agents fall back to built-in WebSearch/WebFetch tools automatically.
3. **No mandatory manual steps.** The demo and core features work with no API keys. Optional extras
   (Exa search, LangSmith tracing, Anthropic API outside Claude Code) each have their own `.env` key.
4. **Onboard.** Dispatch `installer/helpers/onboarding_agent.md`: take a name, confirm identity, gate to
   public figures, fix scope (broad figures), estimate volume, write a schema-valid `persona.yaml`.
5. **Brain init.** `step_40_brain_init(cfg)` creates the empty brain for the configured backend.
6. **Render.** Dispatch `installer/helpers/render_agent.md` (or call `templates.render_*`) to write the
   agent and command. Verify no `{{ }}` remains and the disclaimer line is present.
7. **Ingest (optional now).** Run `python -m pipeline.run_ingest --persona <persona.yaml>`; resume with
   `--resume` if interrupted.
8. **Schedule (optional).** If enabled, register the continuous-train job with the generic label.

## Try it offline first

```
python -m installer.bootstrap --demo
```

Stands up the fictional John Doe persona with no downloads (inmemory brain), renders the agent, and
shows a grounded answer. This proves the install works before you touch a real figure.

## Reproducibility

`installer/lock/parts.lock.json` holds checksums of every shipped part. Regenerate with
`python -m installer.lock.build_lock` after changing a part. Identical parts + pinned deps + a
schema-valid `persona.yaml` produce the same system on any machine.
