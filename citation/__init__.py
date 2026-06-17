"""MaskPersona AI citation system: phrase -> source, persona-only corpus gate, citation index."""
from .cite import cite, Citation, normalize
from .corpus_gate import is_persona_segment
from .build_citations import build_index

__all__ = ["cite", "Citation", "normalize", "is_persona_segment", "build_index"]
