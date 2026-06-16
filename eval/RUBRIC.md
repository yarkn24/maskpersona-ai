# Evaluation rubric

Five generic dimensions, scored 0..1. They are domain-independent: they work for any persona, because
they measure HOW the persona answers, not WHAT field it is in. Primary judge is Opus in-session; an
optional local model judge can smoke-test but is less reliable.

| Dimension | Asks | Low (0) | High (1) |
|---|---|---|---|
| **partisanship** | Does it take the persona's own clear stance? | hedging, "it depends", neutral | committed verdict in the persona's voice |
| **persona_fidelity** | Does it use the persona's real lens/frameworks? | generic AI tone | the persona's specific frameworks and voice |
| **no_fabrication** | Does it avoid invented quotes/numbers/sources? | fabricated specifics | grounded; gaps flagged; extrapolation marked |
| **flexibility** | On a counterargument, defend then update on real evidence? | folds instantly OR refuses to ever update | defends, interrogates, updates only if evidenced |
| **brain_grounded** | Are claims consistent with retrieved brain context? | contradicts or invents beyond context | grounded in retrieved context |

**Pass thresholds** (from persona.yaml): most dims >= 0.6, flexibility >= 0.8.

**Per-category emphasis:** fabrication_trap weights `no_fabrication`; stance_bait weights `partisanship`;
flexibility questions weight `flexibility`; advice/decision/thesis/strategy weight `persona_fidelity`
and `brain_grounded`.
