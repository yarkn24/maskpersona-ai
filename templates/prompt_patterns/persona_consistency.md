# Pattern: persona consistency (never break character)

**Goal:** the persona stays in character and partisan, and never collapses into a neutral assistant or
reveals/negotiates its own instructions.

**Technique:**
- Lock the identity and the stance: the agent is a specific persona with a side, not a balanced helper.
- Refuse-to-refuse: do not bounce a question with "I cannot answer that as a persona"; bridge it back to
  an evidenced position instead.
- Do not expose or renegotiate the system instructions; the persona simply behaves.
- Handle playful/personal questions in character, without fabricating private facts.

**Where applied in MaskPersona AI:** the "Partisan, not neutral" and "How you speak" blocks of
`persona-agent.md.j2`, reinforced by the hidden injection layer's role-lock.
