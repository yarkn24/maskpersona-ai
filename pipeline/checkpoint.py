"""Checkpointing so an interrupted ingestion resumes from where it stopped.

Production uses a SQLite checkpointer under work/<slug>/checkpoints.db. Tests use an in-memory saver.
"""
from __future__ import annotations

from pathlib import Path

# Same repo-root anchor as PersonaConfig.work_dir (config/schema.py) -- this file only has the slug
# string, not a PersonaConfig instance, so it computes the anchor independently rather than
# recreating a CWD-relative "work/" path that would break --resume outside the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent


def sqlite_checkpointer(slug: str):
    """Return a SQLite checkpointer (context-managed) for a persona's ingestion run."""
    from langgraph.checkpoint.sqlite import SqliteSaver
    db = _REPO_ROOT / "work" / slug / "checkpoints.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver.from_conn_string(str(db))


def memory_checkpointer():
    """In-memory checkpointer for tests / dry runs."""
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
