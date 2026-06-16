"""The single master installer.

`make install` (human) and `FORGE_INSTALL.md` (an agent) both run THESE ordered steps, so the result is
identical on every machine. Dependencies first; there are no mandatory manual steps or access tokens
(optional extras like Exa are surfaced but never required); the demo path stands up a persona offline.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from installer import steps  # noqa: E402


def run_demo() -> dict:
    pf = steps.step_00_preflight()
    if not pf["ok"]:
        print("preflight failed: need Python >= 3.11")
        return {"ok": False}
    demo = steps.step_60_demo()
    print("persona-forge demo (offline, fictional John Doe):")
    print(f"  brain backend : {demo['backend']}")
    print(f"  knowledge mined: {demo['mined']} chunks")
    print(f"  rendered to    : {demo['rendered']}")
    print(f"  sample Q       : {demo['sample_q']}")
    print(f"  grounded top   : {demo['grounded_top']}")
    return demo


def run_full() -> dict:
    order = [steps.step_00_preflight(), steps.step_10_deps(), steps.step_25_exa_key()]
    for r in order:
        print(f"  [{r['step']}] " + ("ok" if r.get("ok", r.get("present")) else "ATTENTION") +
              (f"  {r.get('note','')}" if r.get("note") else ""))
    print("\nNext: onboard a persona. Give a name; the onboarding agent does the lookup, the")
    print("public-figure gate, scope, and volume estimate, then writes persona.yaml. See FORGE_INSTALL.md.")
    return {"ok": True}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="persona-forge")
    ap.add_argument("--demo", action="store_true", help="stand up the fictional demo offline")
    ap.add_argument("--onboard", action="store_true", help="start onboarding a new persona")
    args = ap.parse_args(argv)
    if args.demo:
        out = run_demo()
        return 0 if out.get("ok") else 1
    run_full()
    if args.onboard:
        print("\n(onboarding is an in-session agent step; see installer/helpers/onboarding_agent.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
