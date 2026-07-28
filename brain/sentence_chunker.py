"""Groups Whisper segments into sentence-bounded chunks for the knowledge brain.

Whisper segments are time-sliced, not sentence-aware: a segment routinely ends mid-word
or mid-sentence, and writing segments verbatim as knowledge chunks (the previous behavior)
produced chunks that start with a fragment of the prior sentence. This module re-joins
segment text, splits on real sentence boundaries (pysbd, rule-based, 0 dependencies), and
regroups sentences into ~`sentences_per_chunk`-sentence chunks, each carrying a timestamp
range recovered by re-locating the sentence text in the joined string.

Non-contiguous input (e.g. panel turns with a dropped speaker's segment in between) is
split into independent runs first, so a sentence group is never assembled by splicing
text across a real time gap.
"""
from __future__ import annotations

from dataclasses import dataclass

import pysbd

DEFAULT_SENTENCES_PER_CHUNK = 4
DEFAULT_MAX_GAP_S = 1.5


@dataclass
class SentenceChunk:
    text: str
    start: float
    end: float


_SEGMENTER_CACHE: dict[str, "pysbd.Segmenter"] = {}


def _segmenter(language: str | None) -> "pysbd.Segmenter":
    lang = (language or "en").split("-")[0].lower()
    if lang not in _SEGMENTER_CACHE:
        try:
            _SEGMENTER_CACHE[lang] = pysbd.Segmenter(language=lang, clean=False)
        except ValueError:  # language not in pysbd's supported set -> English rules as fallback
            _SEGMENTER_CACHE.setdefault("en", pysbd.Segmenter(language="en", clean=False))
            _SEGMENTER_CACHE[lang] = _SEGMENTER_CACHE["en"]
    return _SEGMENTER_CACHE[lang]


def _split_into_runs(segments: list[dict], max_gap_s: float) -> list[list[dict]]:
    """Split segments at any gap wider than max_gap_s (a dropped/isolated-out segment)."""
    runs: list[list[dict]] = []
    current: list[dict] = []
    prev_end = None
    for s in segments:
        text = (s.get("text") or "").strip()
        if not text:
            continue
        start, end = float(s["start"]), float(s["end"])
        if prev_end is not None and start - prev_end > max_gap_s and current:
            runs.append(current)
            current = []
        current.append({"start": start, "end": end, "text": text})
        prev_end = end
    if current:
        runs.append(current)
    return runs


def _char_to_time_spans(run: list[dict]) -> tuple[str, list[tuple[int, int, float, float]]]:
    """Join a run's segment texts with single spaces; return (joined_text, char->time spans)."""
    parts: list[str] = []
    spans: list[tuple[int, int, float, float]] = []
    pos = 0
    for s in run:
        if parts:
            parts.append(" ")
            pos += 1
        start_pos = pos
        parts.append(s["text"])
        pos += len(s["text"])
        spans.append((start_pos, pos, s["start"], s["end"]))
    return "".join(parts), spans


def _time_for_range(spans: list[tuple[int, int, float, float]], char_start: int, char_end: int) -> tuple[float, float]:
    """Time range covering every span the [char_start, char_end) range overlaps."""
    t_start = t_end = None
    for s0, s1, ts, te in spans:
        if s1 <= char_start or s0 >= char_end:
            continue
        t_start = ts if t_start is None else min(t_start, ts)
        t_end = te if t_end is None else max(t_end, te)
    if t_start is None and spans:  # boundary rounding edge case -> nearest span
        t_start, t_end = spans[0][2], spans[0][3]
    return t_start or 0.0, t_end or 0.0


def _chunk_one_run(run: list[dict], language: str | None, sentences_per_chunk: int) -> list[SentenceChunk]:
    joined, spans = _char_to_time_spans(run)
    if not joined:
        return []
    sentences = [s.strip() for s in _segmenter(language).segment(joined) if s.strip()]
    if not sentences:
        return []

    chunks: list[SentenceChunk] = []
    cursor = 0
    group: list[str] = []
    group_start = 0
    for sent in sentences:
        idx = joined.find(sent, cursor)
        if idx == -1:
            idx = joined.find(sent)  # pysbd whitespace normalization drift -> search from the start
        if idx == -1:
            continue  # cannot locate this sentence in the source text; drop rather than mis-time it
        if not group:
            group_start = idx
        group.append(sent)
        cursor = idx + len(sent)
        if len(group) >= sentences_per_chunk:
            t0, t1 = _time_for_range(spans, group_start, cursor)
            chunks.append(SentenceChunk(text=" ".join(group), start=t0, end=t1))
            group = []
    if group:
        t0, t1 = _time_for_range(spans, group_start, cursor)
        chunks.append(SentenceChunk(text=" ".join(group), start=t0, end=t1))
    return chunks


def chunk_segments(segments: list[dict], language: str | None = None,
                   sentences_per_chunk: int = DEFAULT_SENTENCES_PER_CHUNK,
                   max_gap_s: float = DEFAULT_MAX_GAP_S) -> list[SentenceChunk]:
    """Turn Whisper-style [{start, end, text}] segments into sentence-boundary-safe chunks.

    Every chunk boundary is a real sentence boundary (pysbd), never a Whisper segment
    boundary, so a chunk never starts or ends mid-word or mid-sentence.
    """
    chunks: list[SentenceChunk] = []
    for run in _split_into_runs(segments, max_gap_s):
        chunks.extend(_chunk_one_run(run, language, sentences_per_chunk))
    return chunks
