# Demo persona: John Doe (FICTIONAL)

Everything in this folder is **invented**. "John Doe" is not a real person, and the quotes are not
real quotes. This demo exists only to exercise MaskPersona AI end to end with zero downloads and zero
real-person data:

- `persona.yaml` is a complete, schema-valid config (brain backend `inmemory`, so it runs offline).
- `knowledge_src/*.md` are hand-written fictional knowledge files that illustrate the knowledge-file
  schema (Title / Source / Confidence / `##` sections with quotes).

`make demo` mines these into an in-memory brain, renders the persona agent, and answers a few
questions, proving the pipeline works without touching any real figure's content.

The real pipeline never ships content like this: for an actual figure, knowledge files are generated
at runtime under git-ignored `work/<slug>/knowledge_src/`, and their number and topic split are
decided by the ingestion agent, not fixed here.
