"""T12 verify: audit orchestrator lists the 4 expert audits."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit.run_audits import run_audits, AGENT_AUDITS  # noqa: E402


def test_four_expert_audits_listed():
    assert len(AGENT_AUDITS) == 4
    names = " ".join(AGENT_AUDITS)
    assert "genericity" in names and "gdpr" in names
    assert "text_classifier" in names and "legal_lawyer" in names


def test_audit_agent_files_exist():
    for a in AGENT_AUDITS:
        assert (ROOT / a).exists(), f"missing audit agent: {a}"
