"""Build the LangGraph ingestion graph.

Linear pipeline (discover -> ... -> refresh_citations) with checkpointing and human-in-the-loop
interrupts. LangGraph orchestrates ONLY this build pipeline; answering stays a Claude Code agent.
"""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from .state import IngestState
from .nodes import NODE_SEQUENCE
from .interrupts import INTERRUPT_AFTER


def build_graph(checkpointer=None):
    """Compile the ingestion graph. A checkpointer is required for interrupts/resume."""
    g = StateGraph(IngestState)
    prev = START
    for name, fn in NODE_SEQUENCE:
        g.add_node(name, fn)
        g.add_edge(prev, name)
        prev = name
    g.add_edge(prev, END)
    if checkpointer is not None:
        return g.compile(checkpointer=checkpointer, interrupt_after=INTERRUPT_AFTER)
    return g.compile()
