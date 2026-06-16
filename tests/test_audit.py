"""T12 verify: audit orchestrator passes zero-trace on the clean repo and lists the 4 expert audits."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit.run_audits import run_audits, AGENT_AUDITS  # noqa: E402


def test_zero_trace_passes_on_clean_repo():
    r = run_audits()
    assert r["zero_trace_pass"] is True
    assert r["zero_trace_findings"] == 0
    assert r["pass"] is True


def test_four_expert_audits_listed():
    assert len(AGENT_AUDITS) == 4
    names = " ".join(AGENT_AUDITS)
    assert "genericity" in names and "gdpr" in names
    assert "text_classifier" in names and "legal_lawyer" in names


def test_audit_agent_files_exist():
    for a in AGENT_AUDITS:
        assert (ROOT / a).exists(), f"missing audit agent: {a}"
