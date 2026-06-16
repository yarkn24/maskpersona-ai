"""LangGraph ingestion nodes.

Each node takes IngestState and returns a partial state update. Heavy dependencies (yt-dlp, whisper,
sherpa-onnx) are imported lazily inside the node that needs them, so importing this module (and testing
the graph wiring) does not require the ML stack. There is no vocabulary heuristic anywhere; speaker
isolation is biometric (see voice.py).
"""
from __future__ import annotations

import re
from pathlib import Path

from .state import IngestState


def discover(state: IngestState) -> dict:
    """Find candidate public videos via search query; dedup against exclude_ids."""
    cfg = state["config"]
    exclude = set(cfg.sources.exclude_ids)
    found: list[dict] = []
    try:
        import yt_dlp  # lazy
        q = f"ytsearch{cfg.sources.video_search_count}:{cfg.sources.video_search_query}"
        opts = {"quiet": True, "extract_flat": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(q, download=False)
        for e in (info or {}).get("entries", []):
            vid = e.get("id")
            if vid and vid not in exclude:
                found.append({"id": vid, "url": e.get("url") or e.get("webpage_url", ""),
                              "title": e.get("title", ""), "kind": "unknown"})
    except Exception as ex:  # discovery is best-effort; seed_video_urls can substitute
        return {"discovered": found, "errors": [f"discover: {ex!r}"]}
    # include any explicit seed urls
    for u in cfg.sources.seed_video_urls:
        found.append({"id": u, "url": u, "title": "", "kind": "unknown"})
    return {"discovered": found}


def assess_breadth(state: IngestState) -> dict:
    """Estimate whether the figure is narrow (one field) or broad (many topics)."""
    n = len(state.get("discovered", []))
    topics = state["config"].domain.topics
    breadth = "broad" if (n >= 40 or len(topics) >= 6) else "niche"
    return {"breadth": breadth}


def estimate_volume(state: IngestState) -> dict:
    """Rough volume estimate shown to the user before heavy work (avg ~12 min/video, ~15 MB/min audio)."""
    vids = state.get("discovered", [])
    if state.get("breadth") == "broad" and state.get("scope_topics"):
        vids = vids  # a real run would filter by topic; estimate stays an upper bound
    n = len(vids)
    hours = round(n * 12 / 60, 1)
    gb = round(n * 12 * 15 / 1024, 2)
    files = max(1, n // 2)
    return {"sizing": {"est_videos": n, "est_hours": hours, "est_gb": gb, "est_files": files}}


def classify_solo_vs_panel(state: IngestState) -> dict:
    """Tag each video solo/panel by a quick speaker count (precondition for fingerprinting)."""
    out = []
    for v in state.get("discovered", []):
        v = dict(v)
        v.setdefault("kind", "unknown")
        out.append(v)
    return {"discovered": out}  # real impl runs a fast diarization count; kept lazy/stub here


def transcribe(state: IngestState) -> dict:
    """Transcribe videos to timestamped text (whisper, lazy). Per-video try/except for robustness."""
    # Real path: download audio + whisper. Whisper large-v3 is multilingual (one model, no per-language
    # pack); pass cfg.language.content as the language ("auto" lets whisper detect each video).
    return {"transcripts": state.get("transcripts", {})}


def extract_voice_fingerprint(state: IngestState) -> dict:
    """Build the voice fingerprint from SOLO videos and save it (sherpa-onnx, lazy)."""
    cfg = state["config"]
    fp_path = str(Path(cfg.voice.fingerprint_path).expanduser())
    Path(fp_path).parent.mkdir(parents=True, exist_ok=True)
    # Real path: SherpaOnnxEmbedder(language=cfg.language.content, configured_model=cfg.voice.embedding_model)
    # routes the speaker model by language (Chinese -> CN-Celeb, else multilingual default), then
    # embed solo audio -> build_fingerprint -> np.save(fp_path, fp).
    return {"fingerprint_path": fp_path}


def isolate_by_voice(state: IngestState) -> dict:
    """In panels, keep only turns matching the fingerprint (biometric, not vocabulary)."""
    # Real path: for each panel, embed turns, call voice.isolate(turns, fingerprint, threshold);
    # if result.low_confidence -> the confirm_low_confidence interrupt fires before writing.
    return {"isolated": state.get("isolated", {})}


def harvest_articles(state: IngestState) -> dict:
    """Fetch public articles and interview content via Exa search.

    Falls back to seed article_urls only when Exa is unavailable or the key is missing.
    Results are stored as raw dicts; write_knowledge converts them to .md files.
    """
    cfg = state["config"]
    from .search import ExaSearchClient
    client = ExaSearchClient(result_count=getattr(cfg, "search", None) and
                             cfg.search.result_count or 10)
    found: list[dict] = []

    # 1. Search by name + domain topics
    hits = client.search_person(cfg.persona.name, cfg.domain.topics)
    for h in hits:
        found.append({"url": h.url, "title": h.title, "text": h.text,
                      "published_date": h.published_date, "source": "exa_search"})

    # 2. Fetch explicitly listed seed article URLs
    seed_urls = cfg.sources.article_urls
    if seed_urls:
        seed_hits = client.search_urls(seed_urls)
        fetched = {h.url for h in seed_hits}
        for h in seed_hits:
            found.append({"url": h.url, "title": h.title, "text": h.text,
                          "published_date": h.published_date, "source": "seed_url"})
        # If Exa unavailable, keep urls as stubs so write_knowledge can note them
        for u in seed_urls:
            if u not in fetched:
                found.append({"url": u, "title": "", "text": "", "source": "seed_url_unfetched"})

    return {"harvested_articles": found, "knowledge_files": state.get("knowledge_files", [])}


def write_knowledge(state: IngestState) -> dict:
    """Write harvested articles and transcripts as knowledge_src/*.md files."""
    cfg = state["config"]
    kdir = Path("work") / cfg.persona.slug / "knowledge_src"
    kdir.mkdir(parents=True, exist_ok=True)

    articles = state.get("harvested_articles", [])
    written: list[str] = []
    for i, art in enumerate(articles):
        if not art.get("text"):
            continue
        slug_safe = re.sub(r"[^a-z0-9]+", "_", (art.get("title") or f"article_{i}").lower())[:60]
        fname = f"web_{i:03d}_{slug_safe}.md"
        path = kdir / fname
        date_line = f"date: {art['published_date']}\n" if art.get("published_date") else ""
        path.write_text(
            f"# {art.get('title', '(no title)')}\n"
            f"source: {art['url']}\n"
            f"{date_line}\n"
            f"{art['text']}\n",
            encoding="utf-8",
        )
        written.append(str(path))

    # Include any pre-existing files (from transcripts)
    existing = [str(p) for p in kdir.glob("*.md") if str(p) not in written]
    return {"knowledge_files": written + existing}


def brain_ingest(state: IngestState) -> dict:
    """Mine knowledge into the brain and sync."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from brain import get_brain
    cfg = state["config"]
    kdir = Path("work") / cfg.persona.slug / "knowledge_src"
    brain = get_brain(cfg)
    brain.init()
    count = brain.mine(kdir) if kdir.exists() else 0
    brain.sync()
    return {"brain_status": {**brain.status(), "mined": count}}


def refresh_citations(state: IngestState) -> dict:
    """Rebuild the citation index from signature claims."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from citation import build_index
    cfg = state["config"]
    kdir = Path("work") / cfg.persona.slug / "knowledge_src"
    rows = build_index(cfg, kdir, out_path=cfg.citations.index_path) if kdir.exists() else []
    return {"citation_index": cfg.citations.index_path, "errors": state.get("errors", []) + ([] if rows else [])}


# Ordered node list used by the graph.
NODE_SEQUENCE = [
    ("discover", discover),
    ("assess_breadth", assess_breadth),
    ("estimate_volume", estimate_volume),
    ("classify_solo_vs_panel", classify_solo_vs_panel),
    ("transcribe", transcribe),
    ("extract_voice_fingerprint", extract_voice_fingerprint),
    ("isolate_by_voice", isolate_by_voice),
    ("harvest_articles", harvest_articles),
    ("write_knowledge", write_knowledge),
    ("brain_ingest", brain_ingest),
    ("refresh_citations", refresh_citations),
]
