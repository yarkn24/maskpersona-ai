"""T06 verify: known demo phrase maps to its source; unrelated phrase has no match; gate works."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_config  # noqa: E402
from citation import cite, is_persona_segment, build_index  # noqa: E402

DEMO_KNOWLEDGE = ROOT / "demo" / "john_doe" / "knowledge_src"


def test_verbatim_phrase_maps_to_source():
    hits = cite("a business without a revenue model is a hobby", DEMO_KNOWLEDGE)
    assert hits, "expected a verbatim hit"
    assert hits[0].kind == "verbatim"
    assert hits[0].source == "01_revenue_model.md"


def test_unrelated_phrase_no_match():
    assert cite("xylophone quantum penguin orbit", DEMO_KNOWLEDGE) == []


def test_corpus_gate_accepts_real_rejects_fake():
    assert is_persona_segment("growth funded by burn is not traction", DEMO_KNOWLEDGE) is True
    assert is_persona_segment("the weather in tokyo is mild today", DEMO_KNOWLEDGE) is False


def test_build_index_marks_verbatim(tmp_path):
    cfg = load_config(ROOT / "demo" / "john_doe" / "persona.yaml")
    out = tmp_path / "citations_index.csv"
    rows = build_index(cfg, DEMO_KNOWLEDGE, out_path=out)
    assert out.exists()
    by_key = {r["key"]: r for r in rows}
    assert by_key["revenue_model_first"]["kind"] == "verbatim"
    assert by_key["revenue_model_first"]["source"] == "01_revenue_model.md"
