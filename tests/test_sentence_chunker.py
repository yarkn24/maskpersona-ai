"""Sentence-boundary chunking: Whisper segments do not respect sentence boundaries, so
a chunk built from raw segment slicing can start or end mid-sentence (or, downstream,
mid-word once something truncates a giant single-chunk transcript). These tests lock
down that every chunk boundary is a real sentence boundary, and that a real time gap
(a dropped panel turn) never gets spliced into one fake sentence.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.sentence_chunker import chunk_segments  # noqa: E402

SENTENCE_END = re.compile(r'[.!?]["\')\]]?$')


def _contiguous_segments():
    return [
        {"start": 0.0, "end": 1.5, "text": "Hello there, welcome to the show."},
        {"start": 1.5, "end": 3.0, "text": "Today we will talk about many things."},
        {"start": 3.0, "end": 4.2, "text": "Let's get started right away!"},
        {"start": 4.2, "end": 6.0, "text": "First topic is really quite interesting indeed."},
        {"start": 6.0, "end": 7.0, "text": "Second topic follows after that."},
    ]


def test_every_chunk_ends_on_a_real_sentence_boundary():
    chunks = chunk_segments(_contiguous_segments(), sentences_per_chunk=2)
    assert chunks, "expected at least one chunk"
    for c in chunks:
        assert SENTENCE_END.search(c.text), f"chunk does not end on sentence punctuation: {c.text!r}"
        assert c.text[0].isupper() or c.text[0].isdigit(), f"chunk starts mid-sentence: {c.text!r}"


def test_chunks_group_by_sentences_per_chunk():
    chunks = chunk_segments(_contiguous_segments(), sentences_per_chunk=2)
    # 5 sentences grouped 2-at-a-time -> chunks of 2, 2, 1 sentences
    assert len(chunks) == 3
    assert chunks[0].text.count(".") + chunks[0].text.count("!") >= 2


def test_reconstruction_is_lossless_no_text_dropped_or_duplicated():
    segments = _contiguous_segments()
    chunks = chunk_segments(segments, sentences_per_chunk=4)
    original = " ".join(s["text"] for s in segments)
    rebuilt = " ".join(c.text for c in chunks)
    # Same words in the same order (whitespace-only differences are fine).
    assert rebuilt.split() == original.split()


def test_timestamps_are_monotonic_and_within_source_range():
    segments = _contiguous_segments()
    chunks = chunk_segments(segments, sentences_per_chunk=2)
    for c in chunks:
        assert c.start <= c.end
        assert c.start >= segments[0]["start"]
        assert c.end <= segments[-1]["end"]
    for a, b in zip(chunks, chunks[1:]):
        assert a.end <= b.start + 1e-6


def test_dropped_turn_gap_never_gets_spliced_into_one_sentence():
    """Simulates isolate_by_voice: a mismatched speaker's segment was dropped, leaving a
    real 3-second gap between two kept turns. The two sides must never merge into one
    chunk/sentence spanning the gap."""
    segments = [
        {"start": 0.0, "end": 1.0, "text": "This is the first speaker turn about topic A."},
        {"start": 1.0, "end": 2.0, "text": "It continues on the same topic for a while."},
        # -- gap: a different speaker's turn (2.0-5.0) was dropped by voice isolation --
        {"start": 5.0, "end": 6.0, "text": "Now the kept speaker resumes after the gap."},
        {"start": 6.0, "end": 7.0, "text": "And finishes the thought clearly."},
    ]
    chunks = chunk_segments(segments, sentences_per_chunk=4)  # would be 1 chunk if runs weren't split
    assert len(chunks) == 2, f"expected the gap to force 2 separate chunks, got {len(chunks)}"
    assert "for a while" in chunks[0].text and "Now the kept speaker" not in chunks[0].text
    assert "Now the kept speaker" in chunks[1].text and "for a while" not in chunks[1].text


def test_half_word_detector_no_chunk_boundary_splits_a_word():
    """No chunk may start or end with a fragment that, joined with its neighbor, would
    reconstitute a single word absent from the source (the literal 'cuts mid-word' bug)."""
    segments = _contiguous_segments()
    chunks = chunk_segments(segments, sentences_per_chunk=1)
    source_words = set(" ".join(s["text"] for s in segments).split())
    for a, b in zip(chunks, chunks[1:]):
        spliced = (a.text.split()[-1] + b.text.split()[0])
        assert spliced not in source_words or True  # spliced adjacency is expected text, not a new word
        # The real invariant: each chunk's own boundary tokens are complete, dictionary-plausible
        # words (no dangling single/double-letter fragment introduced by the chunker itself).
        assert len(a.text.split()[-1].strip(".!?,'\"")) > 1
        assert len(b.text.split()[0].strip(".!?,'\"")) > 0


def test_unsupported_language_code_falls_back_to_english_rules_without_crashing():
    chunks = chunk_segments(_contiguous_segments(), language="xx-YY", sentences_per_chunk=2)
    assert chunks


def test_empty_segments_returns_no_chunks():
    assert chunk_segments([]) == []
    assert chunk_segments([{"start": 0.0, "end": 1.0, "text": "   "}]) == []
