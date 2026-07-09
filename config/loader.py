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
    """Fill only the framework-level fields the user left unset (model ids, thresholds).

    Every top-level key in defaults.yaml must be mapped here or it is dead config -- editing it
    would silently have no effect on the loaded PersonaConfig.
    """
    raw = dict(raw)

    voice = dict(raw.get("voice") or {})
    if not voice.get("embedding_model"):
        voice["embedding_model"] = defaults.get("voice", {}).get("embedding_model", "")
    if not voice.get("whisper_model"):
        voice["whisper_model"] = defaults.get("transcription", {}).get("model", "")
    for key in ("match_threshold", "min_solo_seconds"):
        if key not in voice and key in defaults.get("voice", {}):
            voice[key] = defaults["voice"][key]
    raw["voice"] = voice

    brain = dict(raw.get("brain") or {})
    for key in ("search_results",):
        if key not in brain and key in defaults.get("brain", {}):
            brain[key] = defaults["brain"][key]
    raw["brain"] = brain

    ev = dict(raw.get("eval") or {})
    for key in ("num_questions", "pass_threshold", "flexibility_threshold"):
        if key not in ev and key in defaults.get("eval", {}):
            ev[key] = defaults["eval"][key]
    raw["eval"] = ev

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
