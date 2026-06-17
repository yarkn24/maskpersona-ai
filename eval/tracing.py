"""Trace eval runs to LangSmith if configured, else to local JSONL.

If LANGSMITH_API_KEY is set, runs are traced to LangSmith (free tier). If not, the same records are
written to work/<slug>/traces/*.jsonl with an identical schema, so the auditor loop works the same
offline. The rest of the system never has to care which backend is active.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path


class _LocalTracer:
    def __init__(self, project: str, out_dir: Path) -> None:
        self.project = project
        out_dir.mkdir(parents=True, exist_ok=True)
        self.path = out_dir / f"{project}-{int(time.time())}.jsonl"

    def log(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    @property
    def backend(self) -> str:
        return "local"


class _LangSmithTracer:
    def __init__(self, project: str) -> None:
        from langsmith import Client  # lazy
        self.project = project
        self.client = Client()

    def log(self, record: dict) -> None:
        self.client.create_run(
            name=record.get("id", "eval"),
            run_type="chain",
            project_name=self.project,
            inputs={"question": record.get("question")},
            outputs={"answer": record.get("answer"), "scores": record.get("scores")},
        )

    @property
    def backend(self) -> str:
        return "langsmith"


def get_tracer(cfg):
    """Return a tracer: LangSmith if LANGSMITH_API_KEY is set, else local JSONL."""
    project = cfg.eval.langsmith_project
    if os.getenv("LANGSMITH_API_KEY"):
        try:
            return _LangSmithTracer(project)
        except Exception:
            pass  # fall back to local if the client cannot init
    out_dir = Path("work") / cfg.persona.slug / "traces"
    return _LocalTracer(project, out_dir)
