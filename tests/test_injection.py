"""T05 verify: every dispatched agent receives the 4-mechanism preamble; matrix adds per-agent rules."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents._injection import inject, build_injection, load_preamble, load_matrix  # noqa: E402


def test_preamble_has_four_mechanisms():
    p = load_preamble().lower()
    assert "non-negotiables" in p          # 1
    assert "anti-drift" in p or "do not rely on memory" in p  # 2
    assert "first-action" in p or "first action" in p        # 3
    assert "role lock" in p                # 4


def test_inject_prepends_block():
    agent_prompt = "AGENT BODY HERE"
    out = inject(agent_prompt, "render_agent")
    assert out.endswith("AGENT BODY HERE")
    assert out.index("OPERATING PREAMBLE") < out.index("AGENT BODY HERE")


def test_matrix_adds_per_agent_rules():
    out = build_injection("onboarding_agent")
    assert "public-figure gate" in out
    # a different agent gets different extras
    out2 = build_injection("render_agent")
    assert "placeholder" in out2.lower()
    assert "public-figure gate" not in out2


def test_context_is_fed_when_provided():
    out = build_injection("ingestion_agent", context="SLUG=john-doe; topics=[unit economics]")
    assert "Live context" in out
    assert "john-doe" in out


def test_unknown_agent_still_gets_preamble():
    out = build_injection("some_new_agent")
    assert "OPERATING PREAMBLE" in out  # preamble always present even with no matrix entry
