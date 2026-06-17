"""T09 verify: auditor only touches allowlisted targets; forbidden refused; clustering + stop work."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from auditor.run_auditor import is_allowed, apply_change, cluster_failures, should_stop  # noqa: E402


def test_allowed_target_passes():
    assert is_allowed("templates/persona-agent.md.j2") is True
    assert is_allowed("agents/_injection/preamble.md") is True


def test_forbidden_target_refused():
    assert is_allowed("demo/john_doe/persona.yaml") is False
    assert is_allowed("specs/constitution.md") is False
    assert is_allowed("config/secret.env") is False


def test_apply_refuses_forbidden_and_logs():
    rec = apply_change({"target": "specs/constitution.md", "action": "weaken", "reason": "x"})
    assert rec["applied"] is False
    assert "not on allowlist" in rec["refused_reason"]


def test_apply_allows_allowlisted():
    rec = apply_change({"target": "agents/_injection/preamble.md", "action": "tune", "reason": "low partisanship"})
    assert rec["applied"] is True


def test_cluster_failures_groups_by_dimension():
    records = [
        {"id": "q1", "scores": {"partisanship": 0.3, "no_fabrication": 0.9}},
        {"id": "q2", "scores": {"partisanship": 0.8, "no_fabrication": 0.4}},
    ]
    clusters = cluster_failures(records, {"partisanship": 0.6, "no_fabrication": 0.6})
    assert clusters["partisanship"] == ["q1"]
    assert clusters["no_fabrication"] == ["q2"]


def test_stop_condition_on_all_pass():
    assert should_stop(0, dims_pass=True, improved=True, history=[True]) is True
    assert should_stop(0, dims_pass=False, improved=True, history=[True]) is False
    # no improvement for 2 rounds -> stop
    assert should_stop(1, dims_pass=False, improved=False, history=[False, False]) is True
