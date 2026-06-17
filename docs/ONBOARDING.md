# Onboarding (minimum effort)

The user provides one input: a name. Everything else is automatic or a single confirmation.

## Flow
1. **Name.** The user types a public figure's name.
2. **Confirm identity.** The onboarding agent looks the name up and shows one line:
   "NAME (role/affiliation). Correct person? (y/n)". One y/n.
3. **Public-figure gate.** It verifies they are a genuine public figure with public content. A private
   individual is refused (Constitution Article 3).
4. **Scope.** Narrow figure: ingest everything. Broad figure (many fields): offer a short list of
   detected topics and ask which to fix on; free-form scope outside the detected topics is not accepted.
5. **Volume estimate.** "Estimated ~N videos, ~H hours, ~Z GB, ~F files. Proceed? (y/n)".
6. **Build.** It writes a schema-valid `persona.yaml`, then ingestion, brain, citations, and the
   rendered agent follow.

## Optional extras (no mandatory manual steps)
The core install and demo require no API keys. Two optional extras unlock additional capabilities:
- **Voice isolation:** `pip install "maskpersona-ai[voice]"`. Models download automatically on first run.
- **Exa web search:** `pip install "maskpersona-ai[search]"` and add `EXA_API_KEY=...` to `.env`.
  Without it, persona agents fall back to built-in WebSearch/WebFetch tools.
The offline demo (`make demo`) works with neither extra installed.

## Agents involved
`installer/helpers/onboarding_agent.md` (lookup, gate, scope, volume, write config) and
`installer/helpers/render_agent.md` (fill templates). Both receive the hidden injection preamble.

## Try it without a real figure
`make demo` stands up the fictional John Doe persona offline, so the flow can be seen end to end with
no downloads and no real-person data.
