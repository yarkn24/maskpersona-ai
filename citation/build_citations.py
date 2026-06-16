"""Build the citation index from a persona's signature claims.

For each claim in persona.yaml `citations.signature_claims`, look it up in the knowledge corpus and
record whether it is verbatim, approximate, or unfound (paraphrase). Writes a CSV the persona agent
can consult to ground or qualify a quote. The claims are config-driven, never hardcoded.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .cite import cite


def build_index(cfg, knowledge_dir: str | Path, out_path: str | Path | None = None) -> list[dict]:
    """Return rows [{key, kind, source, snippet}] and optionally write them to a CSV."""
    dmap = cfg.language.diacritic_map or None
    rows: list[dict] = []
    for claim in cfg.citations.signature_claims:
        hits = cite(claim.phrase, knowledge_dir, k=1, diacritic_map=dmap)
        if hits:
            h = hits[0]
            rows.append({"key": claim.key, "kind": h.kind, "source": h.source, "snippet": h.snippet})
        else:
            rows.append({"key": claim.key, "kind": "paraphrase", "source": "", "snippet": ""})

    out_path = out_path or cfg.citations.index_path
    if out_path:
        p = Path(out_path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["key", "kind", "source", "snippet"])
            w.writeheader()
            w.writerows(rows)
    return rows
