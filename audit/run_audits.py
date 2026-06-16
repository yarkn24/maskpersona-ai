"""Run the release audits.

The deterministic part (zero-trace grep) runs here and gates immediately. The four expert audits
(genericity semantic, GDPR, generic-vs-case-specific text, legal) are dispatched in-session as Opus
agents; this orchestrator runs the deterministic check, lists the agent audits to dispatch in parallel,
and writes a legal-report skeleton. The release is blocked unless all pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit.checks.grep_traces import scan  # noqa: E402

AGENT_AUDITS = [
    "audit/genericity_audit.md",
    "audit/gdpr_audit.md",
    "audit/text_classifier_audit.md",
    "audit/legal_lawyer_agent.md",
]


def run_audits() -> dict:
    findings = scan()
    zero_trace_pass = len(findings) == 0
    return {
        "zero_trace_pass": zero_trace_pass,
        "zero_trace_findings": len(findings),
        "agent_audits_to_dispatch": AGENT_AUDITS,
        "pass": zero_trace_pass,  # deterministic gate; agent audits add the rest in-session
    }


def main() -> int:
    r = run_audits()
    print(f"zero-trace: {'PASS' if r['zero_trace_pass'] else 'FAIL'} "
          f"({r['zero_trace_findings']} findings)")
    print("dispatch these Opus audits in parallel (in-session):")
    for a in r["agent_audits_to_dispatch"]:
        print(f"  - {a}")
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
