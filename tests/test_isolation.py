"""Isolation guarantees for MaskPersona AI.

Two different personas never share a brain, wing, or work directory; the John Doe demo never bleeds into
a user persona's runtime; and the build entrypoints never silently fall back to the John Doe example
config (constitution Art.1: the only example identity is John Doe, and it stays in its own slug).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import PersonaConfig, load_config  # noqa: E402
from config.schema import Persona  # noqa: E402


def _cfg(name: str) -> PersonaConfig:
    """A minimal validated config for a persona, with framework defaults filled."""
    return PersonaConfig.model_validate(
        {"persona": {"name": name, "is_public_figure": True, "identity_confirmed": True}}
    )


def _namespaced(slug: str, value: str) -> bool:
    """A per-persona location must carry the slug (hyphen form) or the wing form (underscore)."""
    return slug in value or slug.replace("-", "_") in value


def test_two_personas_get_distinct_isolated_locations():
    a = _cfg("John Doe")
    b = _cfg("Jane Roe")
    assert (a.persona.slug, b.persona.slug) == ("john-doe", "jane-roe")

    a_locs = [a.brain.palace_path, a.brain.wing, str(a.work_dir),
              a.voice.fingerprint_path, a.citations.index_path,
              a.schedule.label, a.eval.langsmith_project]
    b_locs = [b.brain.palace_path, b.brain.wing, str(b.work_dir),
              b.voice.fingerprint_path, b.citations.index_path,
              b.schedule.label, b.eval.langsmith_project]

    for la, lb in zip(a_locs, b_locs):
        assert la != lb, f"isolation collision: {la!r} == {lb!r}"
        assert _namespaced(a.persona.slug, la)
        assert _namespaced(b.persona.slug, lb)

    # Neither persona's locations contain the other's slug in any form (no bleed-through).
    a_blob, b_blob = " ".join(a_locs), " ".join(b_locs)
    assert "jane-roe" not in a_blob and "jane_roe" not in a_blob
    assert "john-doe" not in b_blob and "john_doe" not in b_blob


def test_demo_john_doe_does_not_bleed_into_user_persona():
    demo = load_config(ROOT / "demo" / "john_doe" / "persona.yaml")
    user = _cfg("Jane Roe")

    assert demo.persona.slug == "john-doe"
    assert demo.brain.backend == "inmemory"  # the demo runs offline, sharing no palace
    assert user.persona.slug == "jane-roe"

    assert demo.brain.wing != user.brain.wing
    assert demo.brain.palace_path != user.brain.palace_path
    assert str(demo.work_dir) != str(user.work_dir)

    for loc in (user.brain.palace_path, user.brain.wing, str(user.work_dir),
                user.voice.fingerprint_path, user.citations.index_path):
        assert "john-doe" not in loc and "john_doe" not in loc


def test_loader_has_no_silent_fallback_to_the_example():
    # A missing config raises instead of quietly loading the John Doe example config.
    with pytest.raises(FileNotFoundError):
        load_config(ROOT / "config" / "does_not_exist_persona.yaml")


def test_build_entrypoints_do_not_default_to_the_john_doe_example():
    # The ingestion/eval CLIs must require an explicit persona, never defaulting to the example config.
    for rel in ("pipeline/run_ingest.py", "eval/run_eval.py", "eval/gen_questions.py"):
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert "persona.example.yaml" not in src, (
            f"{rel} still references the John Doe example config as a default")


def test_persona_can_never_be_marked_endorsed():
    # An isolated persona can never be presented as the real person's endorsed opinion.
    with pytest.raises(Exception):
        Persona(name="Jane Roe", endorsed=True)
