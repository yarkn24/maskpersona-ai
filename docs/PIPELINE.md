# Ingestion pipeline (LangGraph)

The build pipeline is a linear LangGraph (`pipeline/graph.py`) over `IngestState` (`pipeline/state.py`),
with SQLite checkpointing (`pipeline/checkpoint.py`) and human-in-the-loop interrupts
(`pipeline/interrupts.py`).

## Nodes (in order)
1. `discover` find candidate public videos (search query + seed urls), dedup against exclude ids.
2. `assess_breadth` narrow vs broad figure.
3. `estimate_volume` rough videos/hours/GB/files estimate.
4. `classify_solo_vs_panel` tag each video by speaker count (precondition for fingerprinting).
5. `extract_voice_fingerprint` learn the figure's voice from SOLO videos.
6. `isolate_by_voice` keep only panel turns matching the fingerprint (biometric; no vocab guess).
7. `harvest_articles` fetch public articles into knowledge files.
8. `write_knowledge` emit knowledge_src/*.md (number and split decided by the ingestion agent).
9. `brain_ingest` mine into the brain and sync.
10. `refresh_citations` rebuild the citation index from signature claims.

## Human gates (bounded; pick from offered options)
After `discover` (confirm identity + video count), after `estimate_volume` (approve volume), after
`isolate_by_voice` (include low-confidence turns?). See `pipeline/interrupts.py`.

## Resume
A SQLite checkpoint per persona under `work/<slug>/checkpoints.db`. If a long run dies (e.g. a
transcription crash), `python -m pipeline.run_ingest --resume` continues from the last completed node
without re-downloading or re-transcribing finished videos.

## Lazy ML
Heavy dependencies (yt-dlp, whisper, sherpa-onnx) are imported lazily inside the node that needs them,
so the graph wiring and tests run without the ML stack installed.
