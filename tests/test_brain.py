"""T03 verify: inmemory brain mines demo knowledge, returns relevant hits; registry selects backend."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_config  # noqa: E402
from brain import InMemoryBrain, get_brain  # noqa: E402

DEMO_KNOWLEDGE = ROOT / "demo" / "john_doe" / "knowledge_src"


def test_inmemory_mines_demo():
    b = InMemoryBrain()
    n = b.mine(DEMO_KNOWLEDGE)
    assert n >= 3  # at least one chunk per demo file
    assert b.status()["items"] == n


def test_search_returns_relevant_hit():
    b = InMemoryBrain()
    b.mine(DEMO_KNOWLEDGE)
    hits = b.search("how should I think about unit economics and burn?", k=3)
    assert hits, "expected at least one hit"
    # the unit-economics chunk should rank above the fundraising one for this query
    assert "unit" in hits[0].text.lower() or "burn" in hits[0].text.lower()


def test_search_unrelated_low_or_empty():
    b = InMemoryBrain()
    b.mine(DEMO_KNOWLEDGE)
    hits = b.search("xylophone quantum penguin", k=3)
    assert hits == []  # no token overlap -> no false positives


def test_registry_selects_inmemory():
    cfg = load_config(ROOT / "demo" / "john_doe" / "persona.yaml")
    b = get_brain(cfg)
    assert b.__class__.__name__ == "InMemoryBrain"
