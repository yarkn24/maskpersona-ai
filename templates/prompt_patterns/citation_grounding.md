# Pattern: citation grounding

**Goal:** every concrete claim is tied to a source, so the persona cannot drift into fabrication.

**Technique:**
- Bind each asserted fact to evidence: a brain hit, a verified verbatim quote, or a marked extrapolation.
- Use direct-quote formatting ONLY for text that was actually retrieved this turn. Paraphrase otherwise.
- Verify the source of a specific attribution before naming it; if it cannot be confirmed, stay generic
  ("somewhere I have said ...") rather than inventing a precise source.
- Never produce a source label or timestamp to satisfy a format; if there is no source, say so.

**Where applied in MaskPersona AI:** the "Citation discipline" block of `persona-agent.md.j2`, backed by
the `citation/` system (verbatim phrase -> source, gated by a persona-only corpus).
