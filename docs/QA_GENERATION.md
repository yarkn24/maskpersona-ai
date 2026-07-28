# QA-pair generation and semantic retrieval

A separate, opt-in enhancement layer on top of the ingested knowledge brain: for every knowledge
chunk, generate one or more plausible QUESTIONS a reader might ask that the chunk answers, so the
persona can match a semantically-worded question directly to the exact source text instead of
relying only on keyword overlap.

## Anti-fabrication by construction

The **answer** in every QA pair is always the chunk's own text, verbatim. It is never written or
paraphrased by an LLM. The only LLM-dependent step is phrasing the **question** -- and even a badly
or hallucinated-phrased question can only make retrieval worse (a mismatched question), never
produce a false claim in the answer.

## Schema (`brain/qa_pairs.py`)

```json
{"id": "qa_0001_0", "question": "...", "answer": "<verbatim chunk text>", "source": "video_abc.md"}
```

`work/<slug>/qa_pairs.jsonl`, one JSON object per line (`PersonaConfig.qa.qa_pairs_path`).

## Generating pairs (`pipeline/qa_gen.py`)

Mirrors `eval/run_eval.py`'s existing pattern exactly: `run(knowledge_dir, out_path, ask_fn, ...)`
takes an **injectable** `ask_fn(chunk_text) -> list[str]`, so the module is testable without any
model. A standalone CLI run (`python -m pipeline.qa_gen --persona persona.yaml`) with no `ask_fn`
wired is a dry-run stub (0 pairs), same shape as `eval.run_eval`'s `_dry_answer`.

**Production wiring** (not automated inside the LangGraph pipeline -- the graph nodes stay
deterministic/local-only by design, see `docs/PIPELINE.md`): run this as a follow-on step in a
Claude Code session after ingestion completes. For each knowledge chunk, dispatch a **Sonnet or
Haiku** subagent (QA phrasing is grunt work; Opus is reserved for the persona's own answers, never
used for this generation step) with a prompt such as:

> Read this chunk of {{ name }}'s public content. Write 1-3 short, natural questions a reader might
> ask that this chunk directly and fully answers. One question per line, no numbering, no preamble.
>
> Chunk:
> {{ chunk_text }}

Collect the returned lines as the `ask_fn` result and call `pipeline.qa_gen.run(...)` with it. The
generated pairs are written to `qa_pairs.jsonl` **and** materialized as `knowledge_src/qa_*.md`
files (`brain/qa_pairs.write_qa_knowledge_md`), so the next `brain_ingest` (`mine()`) call also
feeds them into the mempalace/inmemory brain like any other knowledge file -- no `Brain` interface
change was needed for this.

## Retrieval (`brain/qa_search.py`)

Hybrid: idf-weighted lexical overlap over the **question** field (0 dependencies, always available,
mirrors `brain/inmemory_adapter.py`'s exact scoring) blended with an optional local embedding
similarity layer.

**Embedding model: `intfloat/multilingual-e5-small`** (MIT license, ~100 languages, 384-dim,
12-layer, sentence-transformers-compatible). Installed via the optional `qa` extra
(`pip install -e ".[qa]"`); without it, QA search still works via lexical matching alone.

Why this model and not the more commonly defaulted-to `all-MiniLM-L6-v2`:
- MaskPersona AI builds personas of **any public figure**, not English-only, so a multilingual model
  is a real requirement here, not a nice-to-have (`pysbd`'s own sentence-chunking already supports 22
  languages for the same reason). `all-MiniLM-L6-v2` and `bge-small-en-v1.5` are both English-only
  despite general popularity.
- `multilingual-e5-small` is built on the same lightweight architecture class (12-layer, 384-dim) as
  the popular small English models, so it does not trade away the "keep the core light" footprint the
  rest of this repo follows for optional ML deps (`voice` extra, `openai-whisper`/`sherpa-onnx`).
- Community benchmarking flags `all-MiniLM-L6-v2` specifically as weak on modern retrieval-quality
  measures ("achieved only 56% Top-5 accuracy and 28% Top-1, among the lowest scores" per a
  Supermemory embedding-model benchmark referenced in a 2026 Hacker News discussion,
  news.ycombinator.com/item?id=46081800) -- a newer small model was worth the one extra research
  pass rather than defaulting to the most-copied name.
- `multilingual-e5-small` scores 81.70 semantic-similarity on the Polish MTEB benchmark
  (arxiv.org/pdf/2405.10138, "PL-MTEB: Polish Massive Text Embedding Benchmark"), evidence it holds
  up reasonably outside English, which is the actual requirement here.

`QASearch.search()` returns an empty list when no hit clears `min_score` -- the persona runtime
treats that as "no confident QA hit" and falls back to the broader keyword brain search (see
`templates/persona-agent.md.j2`, "How you query your brain").

**Runtime invocation** (the persona agent has Bash/Read/WebSearch/WebFetch tools, no direct Python
import path, so it shells out exactly like the existing `brain/web.py` search call):
```bash
python3 -c "from brain.qa_search import search_qa_pairs; [print(h.score, h.text) for h in search_qa_pairs('<qa_pairs.jsonl path>', '<question>')]"
```
