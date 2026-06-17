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
from . import media


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
    # For broad figures with chosen topics the run ingests a subset; this estimate stays an upper bound.
    n = len(vids)
    hours = round(n * 12 / 60, 1)
    gb = round(n * 12 * 15 / 1024, 2)
    files = max(1, n // 2)
    return {"sizing": {"est_videos": n, "est_hours": hours, "est_gb": gb, "est_files": files}}


def classify_solo_vs_panel(state: IngestState) -> dict:
    """Tag each video solo/panel by a fast speaker count, so fingerprinting uses only clean solo audio."""
    cfg = state["config"]
    out: list[dict] = []
    errors: list[str] = []
    if not cfg.voice.enabled:
        return {"discovered": [dict(v) for v in state.get("discovered", [])]}
    from .voice import SherpaOnnxEmbedder, cosine
    audio_dir = cfg.work_dir / "audio"
    embedder = None
    for v in state.get("discovered", []):
        v = dict(v)
        v.setdefault("kind", "unknown")
        try:
            wav = media.load_waveform(media.download_audio(v["url"], audio_dir, v["id"]))
            if embedder is None:
                embedder = SherpaOnnxEmbedder(
                    language=cfg.language.content,
                    configured_model=cfg.voice.embedding_model or None,
                )
            v["kind"] = _speaker_count_kind(wav, embedder, cosine, cfg.voice.match_threshold)
        except Exception as ex:  # best-effort: an unclassifiable video is left "unknown" and skipped by fingerprint
            errors.append(f"classify {v.get('id')}: {ex!r}")
        out.append(v)
    return {"discovered": out, "errors": state.get("errors", []) + errors}


def _speaker_count_kind(wav, embedder, cosine, threshold, window_s: float = 3.0, max_windows: int = 8) -> str:
    """Embed a few evenly spaced windows and greedily cluster by cosine; 'solo' if one speaker dominates."""
    import numpy as np
    total = len(wav) / media.SAMPLE_RATE
    if total < window_s * 2:
        return "solo"  # too short to host a multi-speaker panel
    n = min(max_windows, max(2, int(total // (window_s * 4))))
    clusters: list[list] = []  # each entry: [centroid_vector, count]
    for s in np.linspace(0.0, max(0.0, total - window_s), n):
        seg = media.slice_waveform(wav, float(s), float(s) + window_s)
        if len(seg) < int(window_s * media.SAMPLE_RATE * 0.5):
            continue
        emb = embedder.embed(seg)
        for c in clusters:
            if cosine(emb, c[0]) >= threshold:
                c[0] = (c[0] * c[1] + emb) / (c[1] + 1)
                c[1] += 1
                break
        else:
            clusters.append([emb, 1])
    if not clusters:
        return "unknown"
    seen = sum(c[1] for c in clusters)
    dominant = max(c[1] for c in clusters)
    return "solo" if (len(clusters) == 1 or dominant / seen >= 0.8) else "panel"


def transcribe(state: IngestState) -> dict:
    """Download each video's audio and transcribe it to timestamped segments (whisper, lazy).

    Per-video try/except keeps one failure from aborting the run. SOLO videos are clean single-speaker,
    so their full transcript is written straight to knowledge; PANEL videos wait for voice isolation.
    """
    import json
    cfg = state["config"]
    if not cfg.voice.enabled:
        return {"transcripts": state.get("transcripts", {})}
    audio_dir = cfg.work_dir / "audio"
    tdir = cfg.work_dir / "transcripts"
    tdir.mkdir(parents=True, exist_ok=True)
    kdir = cfg.work_dir / "knowledge_src"
    kdir.mkdir(parents=True, exist_ok=True)
    transcripts = dict(state.get("transcripts", {}))
    errors: list[str] = []
    for v in state.get("discovered", []):
        vid = v["id"]
        tpath = tdir / f"{vid}.json"
        try:
            if tpath.exists():  # resume-safe: skip already-transcribed videos
                transcripts[vid] = str(tpath)
                continue
            wav_path = media.download_audio(v["url"], audio_dir, vid)
            segments = media.transcribe_audio(wav_path, language=cfg.language.content)
            tpath.write_text(json.dumps(segments, ensure_ascii=False), encoding="utf-8")
            transcripts[vid] = str(tpath)
            if v.get("kind") == "solo":  # clean single speaker -> keep the whole transcript
                _write_transcript_md(kdir, vid, v.get("title", ""), segments)
        except Exception as ex:
            errors.append(f"transcribe {vid}: {ex!r}")
    return {"transcripts": transcripts, "errors": state.get("errors", []) + errors}


def _write_transcript_md(kdir: Path, video_id: str, title: str, segments: list[dict]) -> None:
    text = " ".join(s["text"] for s in segments).strip()
    if not text:
        return
    (kdir / f"video_{video_id}.md").write_text(
        f"# {title or video_id}\nsource: video:{video_id}\n\n{text}\n", encoding="utf-8")


def extract_voice_fingerprint(state: IngestState) -> dict:
    """Build the figure's voice fingerprint from their SOLO videos and save it (sherpa-onnx, lazy)."""
    cfg = state["config"]
    fp_path = str(Path(cfg.voice.fingerprint_path).expanduser())
    if not cfg.voice.enabled:
        return {"fingerprint_path": fp_path}
    import numpy as np
    from .voice import SherpaOnnxEmbedder, build_fingerprint
    Path(fp_path).parent.mkdir(parents=True, exist_ok=True)
    audio_dir = cfg.work_dir / "audio"
    solo = [v for v in state.get("discovered", []) if v.get("kind") == "solo"]
    errors: list[str] = []
    embeddings: list = []
    try:
        if solo:
            embedder = SherpaOnnxEmbedder(
                language=cfg.language.content,
                configured_model=cfg.voice.embedding_model or None,
            )
            collected = 0.0
            for v in solo:
                wav_path = audio_dir / f"{v['id']}.wav"
                if not wav_path.exists():
                    wav_path = media.download_audio(v["url"], audio_dir, v["id"])
                wav = media.load_waveform(wav_path)
                embeddings.append(embedder.embed(wav))
                collected += len(wav) / media.SAMPLE_RATE
                if collected >= cfg.voice.min_solo_seconds:
                    break
    except Exception as ex:
        errors.append(f"fingerprint: {ex!r}")
    if embeddings:
        np.save(fp_path, build_fingerprint(embeddings))
    else:
        errors.append("fingerprint: no solo audio; panels cannot be voice-isolated")
    return {"fingerprint_path": fp_path, "errors": state.get("errors", []) + errors}


def isolate_by_voice(state: IngestState) -> dict:
    """In panel videos, keep only the turns whose voice embedding matches the fingerprint (biometric)."""
    import json
    cfg = state["config"]
    isolated = dict(state.get("isolated", {}))
    if not cfg.voice.enabled:
        return {"isolated": isolated}
    fp_path = Path(cfg.voice.fingerprint_path).expanduser()
    if not fp_path.exists():  # no fingerprint -> nothing to match panels against
        return {"isolated": isolated,
                "errors": state.get("errors", []) + ["isolate: no fingerprint; panels skipped"]}
    import numpy as np
    from .voice import Turn, isolate as voice_isolate, SherpaOnnxEmbedder
    fingerprint = np.load(fp_path)
    audio_dir = cfg.work_dir / "audio"
    tdir = cfg.work_dir / "transcripts"
    kdir = cfg.work_dir / "knowledge_src"
    kdir.mkdir(parents=True, exist_ok=True)
    embedder = None
    errors: list[str] = []
    low_confidence: list[str] = []
    for v in [d for d in state.get("discovered", []) if d.get("kind") == "panel"]:
        vid = v["id"]
        tpath = tdir / f"{vid}.json"
        if not tpath.exists():
            continue
        try:
            segments = json.loads(tpath.read_text(encoding="utf-8"))
            wav = media.load_waveform(audio_dir / f"{vid}.wav")
            if embedder is None:
                embedder = SherpaOnnxEmbedder(
                    language=cfg.language.content,
                    configured_model=cfg.voice.embedding_model or None,
                )
            turns = []
            for s in segments:
                seg = media.slice_waveform(wav, s["start"], s["end"])
                turns.append(Turn(text=s["text"], start=s["start"], end=s["end"],
                                  embedding=embedder.embed(seg) if len(seg) else None))
            res = voice_isolate(turns, fingerprint, cfg.voice.match_threshold)
            isolated[vid] = [t.text for t in res.kept]
            kept_text = " ".join(t.text for t in res.kept).strip()
            if kept_text:
                _write_kept_md(kdir, vid, v.get("title", ""), kept_text)
            if res.low_confidence:
                low_confidence.append(vid)
        except Exception as ex:
            errors.append(f"isolate {vid}: {ex!r}")
    out: dict = {"isolated": isolated, "errors": state.get("errors", []) + errors}
    if low_confidence:  # surfaced by the human-in-the-loop interrupt after this node
        out["approvals"] = {**state.get("approvals", {}), "low_confidence_panels": low_confidence}
    return out


def _write_kept_md(kdir: Path, video_id: str, title: str, text: str) -> None:
    (kdir / f"panel_{video_id}.md").write_text(
        f"# {title or video_id}\nsource: video:{video_id} (voice-isolated)\n\n{text}\n", encoding="utf-8")


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
