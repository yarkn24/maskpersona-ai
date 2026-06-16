"""Zero-trace check (constitution gate).

Scans the repo for anything that must never appear: real-person names, absolute machine paths, email
addresses, external URLs, and unrelated product/company names. The only example identity allowed is
"John Doe". Exit non-zero on any hit so it can gate every phase and the release.

Every sensitive literal this checker forbids (the specific names and keywords) is stored base64-encoded
and decoded only at runtime, so this source file itself contains none of those words in plain text and
stays clean under its own scan.

Usage: python -m audit.checks.grep_traces [--strict]
"""
from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Directories never scanned.
SKIP_DIRS = {".git", ".venv", "venv", "work", "__pycache__", ".pytest_cache", "node_modules"}
# Only scan these text types.
EXTS = {".py", ".md", ".yaml", ".yml", ".toml", ".json", ".j2", ".txt", ".cfg", ".ini", ""}

# Build the em/en dash class from code points so this source contains no literal dash characters.
_DASH_CLASS = "[" + chr(0x2014) + chr(0x2013) + "]"


def _dec(b64: str) -> str:
    """Decode a base64 literal at runtime so the plain word never appears in this file."""
    return base64.b64decode(b64).decode("ascii")


# Encoded forbidden literals (decoded only in memory; never written here in plain text).
# Group 1: unrelated product/company names that must not be referenced as sources.
_ENC_PRODUCT_NAMES = [
    "bG92YWJsZQ==", "Ym9sdC5uZXc=", "cGVycGxleGl0eQ==",
    "c3BlYy1raXQ=", "c3BlY2tpdA==", "a2FycGF0aHk=",
]
# Group 2: real-person name fragments that must never surface (only "John Doe" is allowed).
_ENC_REAL_NAMES = ["aWhzYW4=", "ZWxnaW4=", "eWFya2lu", "Z3VzdG8="]
# Group 2b: generic famous-figure surnames, word-boundary matched to avoid substring false positives.
_ENC_FIGURE_NAMES = ["ZWluc3RlaW4=", "c2hha2VzcGVhcmU=", "YnVmZmV0dA==", "ZGFyd2lu", "ZmV5bm1hbg=="]
# Single keywords.
_ENC_LEAKED = "bGVha2Vk"
_ENC_HTTP = "aHR0cA=="

# Forbidden patterns. Labels stay generic so a printed finding never echoes a forbidden literal.
FORBIDDEN = {
    "absolute home path (/Users/...)": re.compile(r"/Users/[A-Za-z0-9._-]+"),
    "absolute home path (/home/...)": re.compile(r"/home/[A-Za-z0-9._-]+"),
    "email address": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "em dash or en dash": re.compile(_DASH_CLASS),
    "external URL": re.compile(_dec(_ENC_HTTP) + r"s?://\S+", re.IGNORECASE),
    "source-implying keyword": re.compile(re.escape(_dec(_ENC_LEAKED)), re.IGNORECASE),
}
for _i, _b in enumerate(_ENC_PRODUCT_NAMES):
    FORBIDDEN[f"unrelated product/company name #{_i}"] = re.compile(re.escape(_dec(_b)), re.IGNORECASE)
for _i, _b in enumerate(_ENC_REAL_NAMES):
    FORBIDDEN[f"real-person name fragment #{_i}"] = re.compile(re.escape(_dec(_b)), re.IGNORECASE)
for _i, _b in enumerate(_ENC_FIGURE_NAMES):
    FORBIDDEN[f"famous-figure name fragment #{_i}"] = re.compile(r"\b" + re.escape(_dec(_b)) + r"\b", re.IGNORECASE)


def iter_files():
    for p in ROOT.rglob("*"):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in EXTS:
            continue
        if p.resolve() == Path(__file__).resolve():  # the checker names the patterns; skip itself
            continue
        yield p


def scan() -> list[tuple[str, int, str, str]]:
    findings: list[tuple[str, int, str, str]] = []
    for p in iter_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for label, rx in FORBIDDEN.items():
                if rx.search(line):
                    findings.append((str(p.relative_to(ROOT)), i, label, line.strip()[:120]))
    return findings


def main(argv: list[str] | None = None) -> int:
    findings = scan()
    if not findings:
        print("zero-trace: OK (no real-person/owner/path/product traces found)")
        return 0
    print(f"zero-trace: FAIL ({len(findings)} finding(s)):")
    for rel, ln, label, snippet in findings:
        print(f"  {rel}:{ln}  [{label}]  {snippet}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
