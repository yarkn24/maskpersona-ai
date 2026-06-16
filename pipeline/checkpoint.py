"""Checkpointing so an interrupted ingestion resumes from where it stopped.

Production uses a SQLite checkpointer under work/<slug>/checkpoints.db. Tests use an in-memory saver.
"""
from __future__ import annotations

from pathlib import Path


def sqlite_checkpointer(slug: str):
    """Return a SQLite checkpointer (context-managed) for a persona's ingestion run."""
    from langgraph.checkpoint.sqlite import SqliteSaver
    db = Path("work") / slug / "checkpoints.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver.from_conn_string(str(db))


def memory_checkpointer():
    """In-memory checkpointer for tests / dry runs."""
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
