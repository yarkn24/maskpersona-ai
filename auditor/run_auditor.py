"""Bounded, evidence-driven self-improvement harness.

The Sonnet auditor agent (agents/auditor_agent.md) reads eval traces and proposes optimizations. THIS
harness enforces the bounds: it only applies changes whose target is on the allowlist, logs every
applied change for reversal, and stops at the stop condition. The harness is testable without an LLM;
the proposing is the agent's job, the guarding is the harness's.
"""
from __future__ import annotations

import fnmatch
import json
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ALLOWLIST_PATH = HERE / "allowed_changes.yaml"
CHANGE_LOG = HERE / "change_log"


def load_allowlist() -> dict:
    return yaml.safe_load(ALLOWLIST_PATH.read_text(encoding="utf-8")) or {}


def is_allowed(target: str, allowlist: dict | None = None) -> bool:
    """A target is allowed if it matches an allow glob and no forbid glob."""
    allowlist = allowlist or load_allowlist()
    allow = allowlist.get("allow", [])
    forbid = allowlist.get("forbid", [])
    base = target.split("#", 1)[0]  # strip a sub-key fragment for glob matching
    if any(fnmatch.fnmatch(base, f) for f in forbid):
        return False
    return any(target == a or base == a.split("#", 1)[0] or fnmatch.fnmatch(base, a.split("#", 1)[0])
               for a in allow)


def cluster_failures(records: list[dict], thresholds: dict) -> dict:
    """Group failing answers by the rubric dimension they failed."""
    clusters: dict[str, list] = {}
    for r in records:
        for dim, score in (r.get("scores") or {}).items():
            thr = thresholds.get(dim, 0.6)
            if score < thr:
                clusters.setdefault(dim, []).append(r["id"])
    return clusters


def apply_change(change: dict, allowlist: dict | None = None) -> dict:
    """Guarded apply: only if the target is allowed. Returns a log record; does not fabricate."""
    target = change.get("target", "")
    allowed = is_allowed(target, allowlist)
    rec = {
        "ts": int(time.time()),
        "target": target,
        "action": change.get("action"),
        "reason": change.get("reason"),
        "applied": bool(allowed),
        "refused_reason": None if allowed else "target not on allowlist",
    }
    CHANGE_LOG.mkdir(parents=True, exist_ok=True)
    with (CHANGE_LOG / "changes.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def should_stop(round_idx: int, dims_pass: bool, improved: bool, history: list[bool],
                allowlist: dict | None = None) -> bool:
    allowlist = allowlist or load_allowlist()
    sc = allowlist.get("stop_condition", {})
    if sc.get("all_dims_pass") and dims_pass:
        return True
    if round_idx + 1 >= sc.get("max_rounds", 5):
        return True
    noimp = sc.get("no_improvement_rounds", 2)
    if len(history) >= noimp and not any(history[-noimp:]):
        return True
    return False
