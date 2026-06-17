# Pattern: re-injection reminder

**Goal:** the few rules that must never break are repeated right before generation, so they do not get
lost as context grows.

**Technique:**
- Restate the top non-negotiables immediately before the model acts, every time, not just once at the
  start. Repetition of the critical few is a feature.
- Keep the reminder short and high-priority (the 2 to 3 rules that matter most), not the whole prompt.
- Pair it with context re-binding: feed the needed live context each turn rather than trusting memory.

**Where applied in MaskPersona AI:** the "Non-negotiables (re-read before every answer)" block of
`persona-agent.md.j2`, and the hidden injection layer (`agents/_injection/`) that prepends these to
every dispatched agent.
