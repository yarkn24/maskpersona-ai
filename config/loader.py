"""Load, validate, and resolve persona configuration.

Reads a persona.yaml, applies framework defaults, validates against the schema, and resolves
runtime paths. A malformed config raises a clear error (Specs: schema validation is a build gate).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .schema import PersonaConfig

HERE = Path(__file__).resolve().parent
DEFAULTS_PATH = HERE / "defaults.yaml"


def load_defaults() -> dict[str, Any]:
    with DEFAULTS_PATH.open() as f:
        return yaml.safe_load(f) or {}


def _apply_defaults(raw: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    """Fill only the framework-level fields the user left unset (voice model ids, thresholds)."""
    raw = dict(raw)
    voice = dict(raw.get("voice") or {})
    if not voice.get("embedding_model"):
        voice["embedding_model"] = defaults.get("voice", {}).get("embedding_model", "")
    raw["voice"] = voice
    return raw


def load_config(path: str | Path) -> PersonaConfig:
    """Load and validate a persona.yaml into a PersonaConfig. Raises on malformed input."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"persona config not found: {p}")
    with p.open() as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict) or "persona" not in raw:
        raise ValueError(f"invalid persona config (missing 'persona'): {p}")
    raw = _apply_defaults(raw, load_defaults())
    return PersonaConfig.model_validate(raw)


def dump_config(cfg: PersonaConfig, path: str | Path) -> None:
    """Write a PersonaConfig back to YAML."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        yaml.safe_dump(cfg.model_dump(mode="json"), f, sort_keys=False, allow_unicode=True)
