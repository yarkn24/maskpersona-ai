"""T04 verify: rendering with John Doe config yields a complete agent file (no placeholders, disclaimer)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_config  # noqa: E402
from templates import render_persona_agent, render_command, render_persona_core  # noqa: E402

CFG = load_config(ROOT / "demo" / "john_doe" / "persona.yaml")


def test_agent_renders_fully():
    out = render_persona_agent(CFG)
    assert "{{" not in out and "}}" not in out  # no leftover placeholders
    assert "John Doe" in out
    assert "name: john-doe" in out  # frontmatter slug


def test_agent_has_nonnegotiables_and_disclaimer():
    out = render_persona_agent(CFG).lower()
    assert "brain first" in out
    assert "partisan" in out
    assert "forged persona" in out and "ai-generated" in out  # standing AI-output label


def test_agent_has_fidelity_gate():
    out = render_persona_agent(CFG).lower()
    assert "fidelity self-check" in out          # the silent self-gate section renders
    assert "0.75" in out and "0.5" in out         # send threshold + floor from config
    assert "do not answer" in out                 # the < floor refusal branch


def test_command_renders():
    out = render_command(CFG)
    assert "{{" not in out
    assert "$ARGUMENTS" in out
    assert "john-doe" in out


def test_core_renders():
    out = render_persona_core(CFG)
    assert "{{" not in out
    assert "John Doe" in out
