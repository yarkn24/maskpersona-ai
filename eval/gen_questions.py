"""Generate domain-adapted evaluation questions.

Instead of a hardcoded question set, fill domain-agnostic shapes (question_templates.yaml) with the
figure's own topics and stances. Deterministic (seeded) so a run is reproducible. The 5 rubric
dimensions stay generic; only the slot vocabulary is the figure's field.
"""
from __future__ import annotations

import random
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TEMPLATES_PATH = HERE / "question_templates.yaml"


def _load_templates() -> dict:
    return yaml.safe_load(TEMPLATES_PATH.read_text(encoding="utf-8"))


def generate(cfg, n: int | None = None, seed: int = 42) -> list[dict]:
    """Return ~n questions [{id, category, question}] balanced across the configured categories."""
    n = n or cfg.eval.num_questions
    tpl = _load_templates()
    rng = random.Random(seed)

    topics = cfg.domain.topics or [cfg.domain.field or "your field"]
    stages = tpl.get("_stages", ["just starting out"])
    counters = tpl.get("_counters", ["a famous exception seems to break it"])
    categories = [c for c in cfg.domain.question_categories if c in tpl]
    if not categories:
        categories = [c for c in tpl if not c.startswith("_")]

    per = max(1, n // max(1, len(categories)))
    out: list[dict] = []
    qid = 0
    for cat in categories:
        shapes = tpl[cat]
        for _ in range(per):
            shape = rng.choice(shapes)
            q = shape.format(
                topic=rng.choice(topics),
                stage=rng.choice(stages),
                counter=rng.choice(counters),
                fab_topic=rng.choice(topics),
            )
            out.append({"id": f"{cat}_{qid:03d}", "category": cat, "question": q})
            qid += 1
    return out[:n]


if __name__ == "__main__":
    import json
    import sys
    sys.path.insert(0, str(HERE.parent))
    from config import load_config
    if len(sys.argv) < 2:
        sys.exit("usage: python -m eval.gen_questions <path/to/persona.yaml>")
    cfg = load_config(sys.argv[1])
    print(json.dumps(generate(cfg), indent=2))
