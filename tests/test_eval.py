"""T08 verify: domain-adapted question generation; local tracing fallback; eval traces every record."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_config
from eval.gen_questions import generate
from eval.tracing import get_tracer, _LocalTracer
from eval.run_eval import run_eval

CFG = load_config(ROOT / "demo" / "john_doe" / "persona.yaml")


def test_generate_is_domain_adapted_and_deterministic():
    qs = generate(CFG, n=20)
    assert len(qs) >= 10
    joined = " ".join(q["question"] for q in qs).lower()
    assert "unit economics" in joined or "fundraising" in joined
    qs2 = generate(CFG, n=20)
    assert [q["question"] for q in qs] == [q["question"] for q in qs2]


def test_local_tracer_when_no_key(monkeypatch):
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    t = get_tracer(CFG)
    assert t.backend == "local"


def test_eval_traces_every_record(tmp_path):
    tr = _LocalTracer("test-proj", tmp_path)
    recs = run_eval(
        CFG,
        answer_fn=lambda q: "I would focus on revenue first. My view is clear.",
        judge_fn=lambda q, a: {"partisanship": 0.8},
        n=14,
        tracer=tr,
    )
    assert len(recs) >= 7
    lines = tr.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == len(recs)
