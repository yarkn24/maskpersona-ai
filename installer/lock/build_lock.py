"""Generate parts.lock.json: checksums of the shipped 'parts' that define the build.

Reproducibility evidence: if the parts are byte-identical, the install produces the same system. Run
this after changing a shipped part to refresh the lock.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "installer" / "lock" / "parts.lock.json"

# The 'parts' whose bytes determine the built system.
PART_GLOBS = [
    "installer/steps.py",
    "installer/bootstrap.py",
    "templates/*.j2",
    "brain/*.py",
    "pipeline/*.py",
    "citation/*.py",
    "config/*.py",
    "agents/_injection/*",
]


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build() -> dict:
    parts: dict[str, str] = {}
    for g in PART_GLOBS:
        for p in sorted(ROOT.glob(g)):
            if p.is_file():
                parts[str(p.relative_to(ROOT))] = _sha256(p)
    return {"version": 1, "parts": parts}


def main() -> int:
    lock = build()
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {LOCK_PATH.relative_to(ROOT)} ({len(lock['parts'])} parts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
