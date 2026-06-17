"""Hidden injection layer: prepend the operating preamble + context to every dispatched agent."""
from .inject import inject, build_injection, load_preamble, load_matrix

__all__ = ["inject", "build_injection", "load_preamble", "load_matrix"]
