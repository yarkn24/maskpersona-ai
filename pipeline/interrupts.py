"""Human-in-the-loop interrupt points (all bounded: the user only picks from offered options).

These are the nodes after which the graph pauses for a human decision:
- after `discover`: confirm identity ("X (role), correct person? y/n") and the video count.
- after `estimate_volume`: approve the volume estimate before any heavy ingestion.
- after `isolate_by_voice`: if a panel's best voice match was below threshold, confirm before writing it.

LangGraph pauses (interrupt_after) at these node names; the caller resumes after collecting the answer.
"""

INTERRUPT_AFTER = ["discover", "estimate_volume", "isolate_by_voice"]

# Human-readable prompts the front-end shows at each pause.
PROMPTS = {
    "discover": "Found {n} videos for '{query}'. Confirm this is the right public figure and proceed? (y/n)",
    "estimate_volume": "Estimated ~{est_videos} videos, ~{est_hours}h, ~{est_gb} GB. Proceed? (y/n)",
    "isolate_by_voice": "Some panel turns matched the voice weakly. Include the low-confidence turns? (y/n)",
}
