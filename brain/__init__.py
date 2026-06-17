"""MaskPersona AI brain package: swappable knowledge-store adapters."""
from .base import Brain, Hit, Chunk, read_knowledge_chunks
from .inmemory_adapter import InMemoryBrain
from .registry import get_brain

__all__ = ["Brain", "Hit", "Chunk", "read_knowledge_chunks", "InMemoryBrain", "get_brain"]
