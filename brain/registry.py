"""Pick a Brain backend from config."""
from __future__ import annotations

from .base import Brain


def get_brain(cfg) -> Brain:
    """Return a Brain instance for the given PersonaConfig (cfg.brain.backend)."""
    backend = cfg.brain.backend
    if backend == "inmemory":
        from .inmemory_adapter import InMemoryBrain
        return InMemoryBrain(wing=cfg.brain.wing)
    if backend == "mempalace":
        from .mempalace_adapter import MempalaceBrain
        return MempalaceBrain(
            palace_path=cfg.brain.palace_path,
            wing=cfg.brain.wing,
            search_results=cfg.brain.search_results,
        )
    raise ValueError(f"unknown brain backend: {backend!r}")
