"""Hidden injection layer.

Prepends the operating preamble (and per-agent extras + re-bound live context) to every dispatched
agent's prompt, keeping the critical rules and the needed context present on every turn so agents do
not drift as the conversation grows.
"""
from __future__ import annotations

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PREAMBLE_PATH = HERE / "preamble.md"
MATRIX_PATH = HERE / "matrix.yaml"


def load_preamble() -> str:
    return PREAMBLE_PATH.read_text(encoding="utf-8")


def load_matrix() -> dict:
    if not MATRIX_PATH.exists():
        return {}
    return yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8")) or {}


def build_injection(agent_name: str, context: str | None = None) -> str:
    """Build the full injected block for an agent: preamble + per-agent extra rules + live context."""
    parts = [load_preamble()]
    extras = (load_matrix().get(agent_name) or {}).get("rules") or []
    if extras:
        lines = "\n".join(f"- {r}" for r in extras)
        parts.append(f"## Extra rules for `{agent_name}`\n{lines}")
    if context:
        parts.append(
            "## Live context (re-bound this turn; do not trust memory)\n" + context.strip()
        )
    return "\n\n".join(parts)


def inject(agent_prompt: str, agent_name: str, context: str | None = None) -> str:
    """Return the agent prompt with the injection block prepended."""
    block = build_injection(agent_name, context)
    return f"{block}\n\n---\n\n{agent_prompt}"
