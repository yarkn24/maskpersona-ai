"""CLI to run/resume the ingestion pipeline for a persona.

  python -m pipeline.run_ingest --persona <path/to/persona.yaml> [--resume]

Checkpointing means --resume continues from the last completed node (e.g. after a transcription crash)
without re-downloading or re-transcribing finished videos.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import load_config  # noqa: E402
from pipeline.graph import build_graph  # noqa: E402
from pipeline.checkpoint import sqlite_checkpointer  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", required=True,
                    help="path to a persona.yaml produced by onboarding (offline demo: 'make demo')")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(args.persona)
    # Constitution Art.3: ingestion processes a confirmed public figure only. The onboarding gate sets
    # these flags; refuse to ingest otherwise so the build never silently processes a private individual.
    if not (cfg.persona.is_public_figure and cfg.persona.identity_confirmed):
        raise SystemExit(
            "public-figure gate not passed (constitution Art.3): run onboarding so the target is a "
            "confirmed public figure (is_public_figure and identity_confirmed true) before ingesting")
    slug = cfg.persona.slug
    with sqlite_checkpointer(slug) as cp:
        graph = build_graph(checkpointer=cp)
        config = {"configurable": {"thread_id": slug}}
        init = {"slug": slug, "config": cfg, "errors": [], "approvals": {}}
        # Run to the first interrupt (or completion). The front-end resumes after each gate.
        state = graph.invoke(None if args.resume else init, config=config)
        print(f"ingestion paused/finished for {slug}; brain_status={state.get('brain_status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
