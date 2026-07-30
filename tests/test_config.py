"""T01 verify: schema loads, example validates, malformed rejected, defaults filled, Art.2 enforced."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_config, PersonaConfig, slugify  # noqa: E402
from config.loader import _apply_defaults, load_defaults  # noqa: E402
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


def test_defaults_yaml_transcription_model_actually_wired():
    """Regression: defaults.yaml's transcription.model used to have zero effect (only
    voice.embedding_model was mapped in _apply_defaults). A bare config must now pick it up, and an
    explicit user override in persona.yaml must still win."""
    bare = {"persona": {"name": "x", "is_public_figure": True, "identity_confirmed": True}}
    cfg = PersonaConfig.model_validate(_apply_defaults(bare, load_defaults()))
    assert cfg.voice.whisper_model == "large-v3"

    override = {"persona": {"name": "x", "is_public_figure": True, "identity_confirmed": True},
               "voice": {"whisper_model": "tiny"}}
    merged = _apply_defaults(override, load_defaults())
    assert merged["voice"]["whisper_model"] == "tiny"


def test_defaults_yaml_eval_and_brain_fields_wired():
    bare = {"persona": {"name": "x", "is_public_figure": True, "identity_confirmed": True}}
    cfg = PersonaConfig.model_validate(_apply_defaults(bare, load_defaults()))
    assert cfg.eval.num_questions == 100
    assert cfg.brain.search_results == 6


def test_work_dir_is_cwd_independent_repo_anchored(monkeypatch, tmp_path):
    """Regression: work_dir used to be Path("work")/slug, a CWD-relative path. Running from any
    directory other than the repo root scattered ingestion state and broke --resume."""
    monkeypatch.chdir(tmp_path)  # simulate running from a totally different directory
    cfg = PersonaConfig.model_validate(
        {"persona": {"name": "CWD Test", "is_public_figure": True, "identity_confirmed": True}})
    assert cfg.work_dir.is_absolute()
    assert str(cfg.work_dir).startswith(str(ROOT))
    assert str(tmp_path) not in str(cfg.work_dir)


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
