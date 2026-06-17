"""T07 verify: biometric isolation keeps the right speaker; graph compiles; no vocab heuristic exists."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.voice import Turn, build_fingerprint, isolate, cosine, extract_fingerprint  # noqa: E402
from pipeline.graph import build_graph  # noqa: E402
from pipeline.checkpoint import memory_checkpointer  # noqa: E402


# Synthetic 2-speaker fixture: speaker A ~ [1,0], speaker B ~ [0,1].
A = np.array([1.0, 0.05])
B = np.array([0.05, 1.0])


class FakeEmbedder:
    """Maps a labelled segment to a deterministic vector (stands in for the sherpa-onnx embedder in tests)."""
    def embed(self, audio):
        return A if audio == "A" else B


def test_build_fingerprint_from_solo():
    fp = extract_fingerprint(["A", "A"], FakeEmbedder())
    assert cosine(fp, A) > 0.99
    assert cosine(fp, B) < 0.2


def test_isolate_keeps_only_matching_speaker():
    fp = build_fingerprint([A, A])
    turns = [
        Turn("A says unit economics", 0, 5, embedding=A, speaker="A"),
        Turn("B the host asks a question", 5, 9, embedding=B, speaker="B"),
        Turn("A again on revenue", 9, 14, embedding=A, speaker="A"),
    ]
    res = isolate(turns, fp, threshold=0.5)
    kept_text = " ".join(t.text for t in res.kept)
    assert "A says" in kept_text and "A again" in kept_text
    assert "host" not in kept_text
    assert res.low_confidence is False


def test_isolate_flags_low_confidence_when_no_match():
    fp = build_fingerprint([A, A])
    turns = [Turn("only the host speaks", 0, 5, embedding=B, speaker="B")]
    res = isolate(turns, fp, threshold=0.6)
    assert res.kept == []
    assert res.low_confidence is True  # triggers the human-in-the-loop interrupt


def test_graph_compiles_with_checkpointer():
    g = build_graph(checkpointer=memory_checkpointer())
    assert g is not None
    # the interrupt points exist as nodes
    assert "discover" in g.get_graph().nodes


def test_no_vocabulary_heuristic_in_pipeline():
    # Constitution / design: speaker isolation is biometric, not a domain-vocab guess.
    bad = ("vocab_score", "strict_vocab", "persona_vocab", "host_markers")
    for py in (ROOT / "pipeline").rglob("*.py"):
        text = py.read_text(encoding="utf-8").lower()
        for token in bad:
            assert token not in text, f"{py.name} contains forbidden heuristic token {token!r}"
