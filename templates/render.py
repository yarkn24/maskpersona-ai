"""Render persona templates from a validated PersonaConfig.

StrictUndefined: a missing placeholder raises instead of silently rendering blank, so the verify step
can assert no `{{ }}` is left in a rendered agent file.
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

HERE = Path(__file__).resolve().parent
_env = Environment(
    loader=FileSystemLoader(str(HERE)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

_LANG = {"en": "English", "es": "Spanish", "fr": "French", "de": "German",
         "pt": "Portuguese", "zh": "Chinese", "ja": "Japanese"}


def _context(cfg) -> dict:
    return {
        "name": cfg.persona.name,
        "slug": cfg.persona.slug,
        "role": cfg.persona.role,
        "bio": cfg.persona.bio.strip(),
        "lens": cfg.persona.lens,
        "field": cfg.domain.field,
        "output_language": _LANG.get(cfg.language.output, cfg.language.output),
        "palace_path": cfg.brain.palace_path,
        "search_results": cfg.brain.search_results,
        "topics": cfg.domain.topics,
        "fidelity_enabled": cfg.fidelity.enabled,
        "fidelity_send_threshold": cfg.fidelity.send_threshold,
        "fidelity_floor": cfg.fidelity.floor,
        "fidelity_max_attempts": cfg.fidelity.max_attempts,
    }


def render_persona_agent(cfg) -> str:
    return _env.get_template("persona-agent.md.j2").render(**_context(cfg))


def render_command(cfg) -> str:
    return _env.get_template("command.md.j2").render(**_context(cfg))


def render_persona_core(cfg) -> str:
    return _env.get_template("persona-core.md.j2").render(**_context(cfg))


def render_knowledge_file(title: str, source: str, confidence: str,
                          sections: list[dict]) -> str:
    return _env.get_template("knowledge-file.md.j2").render(
        title=title, source=source, confidence=confidence, sections=sections
    )
