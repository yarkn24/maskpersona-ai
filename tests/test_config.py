"""T01 verify: schema loads, example validates, malformed rejected, defaults filled, Art.2 enforced."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_config, PersonaConfig, slugify  # noqa: E402
from config.schema import Brain  # noqa: E402


def test_example_validates():
    cfg = load_config(ROOT / "config" / "persona.example.yaml")
    assert isinstance(cfg, PersonaConfig)
    assert cfg.persona.name == "John Doe"


def test_dependent_defaults_filled():
    cfg = load_config(ROOT / "config" / "persona.example.yaml")
    assert cfg.persona.slug == "john-doe"
    assert cfg.brain.palace_path == "~/personaforge_brains/john-doe"
    assert cfg.brain.wing == "john_doe"
    assert cfg.schedule.label == "personaforge.john-doe.train"
    assert cfg.eval.langsmith_project == "personaforge-john-doe"
    assert cfg.voice.fingerprint_path == "work/john-doe/voice_fingerprint.npy"


def test_slugify():
    assert slugify("John Doe") == "john-doe"
    assert slugify("  Ada  L.  ") == "ada-l"


def test_malformed_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not_a_persona: true\n")
    with pytest.raises(ValueError):
        load_config(bad)


def test_absolute_machine_path_rejected():
    # Constitution Article 2: a hardcoded absolute user-home path must be rejected.
    # Built by concatenation so this test file itself contains no literal home path.
    machine_path = "/" + "Users" + "/someone/brain"
    with pytest.raises(Exception):
        Brain(palace_path=machine_path)


def test_endorsed_is_false_by_default():
    cfg = load_config(ROOT / "config" / "persona.example.yaml")
    assert cfg.persona.endorsed is False


def test_endorsed_true_is_rejected():
    # Invariant: a persona is unendorsed by design; endorsed=True must not validate.
    from config.schema import Persona
    with pytest.raises(Exception):
        Persona(name="Test Person", endorsed=True)
