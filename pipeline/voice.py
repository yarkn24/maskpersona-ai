"""Voice-fingerprint speaker isolation.

The figure's voice is learned from their SOLO videos (clean, single-speaker) as a fingerprint, then in
multi-speaker panels only the turns whose voice matches that fingerprint are kept. This replaces the
fragile "which speaker uses the most domain vocabulary" guess with a biometric match.

The pure logic here (cosine, fingerprint, isolate) is dependency-free and unit-tested. The actual
embedding of audio uses the wespeaker-voxceleb-resnet34 ONNX model via sherpa-onnx, imported lazily
so this module and its tests run without the heavy ML stack installed. The model is pulled once from
a public release: no account and no access token, and it runs on CPU (no PyTorch for this step).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence

import numpy as np


class Embedder(Protocol):
    """Maps an audio segment (file path or waveform) to a speaker embedding vector."""

    def embed(self, audio) -> np.ndarray: ...


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def build_fingerprint(embeddings: Sequence[np.ndarray]) -> np.ndarray:
    """Average the (L2-normalized) solo embeddings into one fingerprint vector."""
    if not embeddings:
        raise ValueError("no solo embeddings: cannot build a voice fingerprint")
    norm = []
    for e in embeddings:
        e = np.asarray(e, dtype=float)
        n = np.linalg.norm(e)
        norm.append(e / n if n else e)
    fp = np.mean(norm, axis=0)
    n = np.linalg.norm(fp)
    return fp / n if n else fp


def matches(embedding: np.ndarray, fingerprint: np.ndarray, threshold: float) -> bool:
    return cosine(embedding, fingerprint) >= threshold


@dataclass
class Turn:
    text: str
    start: float
    end: float
    embedding: np.ndarray | None = None  # filled by the embedding step
    speaker: str | None = None           # optional debug/label


@dataclass
class IsolationResult:
    kept: list[Turn] = field(default_factory=list)
    dropped: list[Turn] = field(default_factory=list)
    low_confidence: bool = False  # best match below threshold -> ask a human


def isolate(turns: Sequence[Turn], fingerprint: np.ndarray, threshold: float) -> IsolationResult:
    """Keep only the turns whose voice embedding matches the fingerprint."""
    res = IsolationResult()
    best = 0.0
    for t in turns:
        if t.embedding is None:
            res.dropped.append(t)
            continue
        sim = cosine(t.embedding, fingerprint)
        best = max(best, sim)
        (res.kept if sim >= threshold else res.dropped).append(t)
    # If nothing matched well, flag for the human-in-the-loop low-confidence interrupt.
    res.low_confidence = (not res.kept) or (best < threshold)
    return res


def extract_fingerprint(solo_audio_segments: Sequence, embedder: Embedder) -> np.ndarray:
    """Embed each solo segment and average into a fingerprint (real path uses sherpa-onnx)."""
    return build_fingerprint([embedder.embed(seg) for seg in solo_audio_segments])


# Speaker-embedding model: wespeaker ResNet34 trained on VoxCeleb (English) with large-margin (LM)
# fine-tuning, ONNX-exported and served from the sherpa-onnx public model release
# (k2-fsa/sherpa-onnx, tag "speaker-recongition-models"). No account and no access token.
_MODEL_HOST = "github.com"
_MODEL_REPO = "k2-fsa/sherpa-onnx"
_MODEL_TAG = "speaker-recongition-models"  # upstream release tag's own spelling; do not "correct" it
_DEFAULT_MODEL = "wespeaker_en_voxceleb_resnet34_LM.onnx"

# Speaker-model routing by the persona's SOURCE content language.
# IMPORTANT (researched): a speaker-embedding model captures voice TIMBRE, not words, and the default
# model is trained on VoxCeleb2 (145 nationalities, multilingual), so it works for ANY language
# (Turkish, Spanish, French, ...). Only Chinese has a clearly better dedicated model (CN-Celeb).
# So this map is intentionally tiny: Chinese -> CN-Celeb; every other language -> the default.
_LANG_SPEAKER_MODELS = {
    "zh": "wespeaker_zh_cnceleb_resnet34_LM.onnx",
    "zh-cn": "wespeaker_zh_cnceleb_resnet34_LM.onnx",
    "zh-tw": "wespeaker_zh_cnceleb_resnet34_LM.onnx",
    "cn": "wespeaker_zh_cnceleb_resnet34_LM.onnx",
    "chinese": "wespeaker_zh_cnceleb_resnet34_LM.onnx",
}


def resolve_speaker_model(language: str | None = None, configured: str | None = None) -> str:
    """Pick the speaker-embedding model filename for a persona.

    Precedence: an explicit `configured` filename (set in voice config) wins; otherwise route by the
    persona's content `language`. Chinese content gets the CN-Celeb model; every other language
    (including "auto" and unknown) gets the multilingual VoxCeleb2 default, which is not tied to the
    spoken language. English is therefore the guaranteed fallback.
    """
    if configured and configured.strip().lower() not in ("", "auto", _DEFAULT_MODEL.lower()):
        return configured
    if language:
        key = language.strip().lower()
        if key in _LANG_SPEAKER_MODELS:
            return _LANG_SPEAKER_MODELS[key]
        # tolerate codes like "zh_CN" / "zh-Hans"
        if key.split("-")[0].split("_")[0] in _LANG_SPEAKER_MODELS:
            return _LANG_SPEAKER_MODELS[key.split("-")[0].split("_")[0]]
    return _DEFAULT_MODEL


def speaker_model_url(filename: str = _DEFAULT_MODEL) -> str:
    """Build the public download URL for a sherpa-onnx speaker-embedding model."""
    scheme = "https"
    return f"{scheme}://{_MODEL_HOST}/{_MODEL_REPO}/releases/download/{_MODEL_TAG}/{filename}"


def _release_asset_names() -> set[str]:
    """Best-effort: filenames in the live speaker-model release. Empty set if the check itself fails."""
    try:
        import json
        import urllib.request
        scheme = "https"
        api = f"{scheme}://api.{_MODEL_HOST}/repos/{_MODEL_REPO}/releases/tags/{_MODEL_TAG}"
        with urllib.request.urlopen(api, timeout=20) as r:  # nosec - public read-only API
            data = json.load(r)
        return {a.get("name", "") for a in data.get("assets", [])}
    except Exception:
        return set()


def ensure_speaker_model(filename: str = _DEFAULT_MODEL, dest_dir: str | Path | None = None) -> Path:
    """Download the ONNX speaker-embedding model once into a local cache and return its path.

    Pulls from the sherpa-onnx public model release (no token). Skips the download if already present.
    Before fetching a non-default model, confirms it is actually published in the live release; if it
    is not (or has been renamed), falls back to the always-present English VoxCeleb default so the
    install never breaks on a missing asset.
    """
    if filename != _DEFAULT_MODEL:
        names = _release_asset_names()
        if names and filename not in names:
            filename = _DEFAULT_MODEL
    base = Path(dest_dir).expanduser() if dest_dir else Path("~/.cache/MaskPersona AI/voice").expanduser()
    base.mkdir(parents=True, exist_ok=True)
    target = base / filename
    if target.exists() and target.stat().st_size > 0:
        return target
    import urllib.request
    with urllib.request.urlopen(speaker_model_url(filename), timeout=120) as r:  # nosec - public model asset
        data = r.read()
    target.write_bytes(data)
    return target


class SherpaOnnxEmbedder:
    """Real embedder. Imported lazily so the rest of the system needs no onnxruntime/sherpa-onnx.

    Uses sherpa-onnx with the wespeaker-voxceleb-resnet34 ONNX speaker-embedding model. The weights
    are pulled once from the sherpa-onnx public model release: no account and no access token.
    Inference runs on CPU via ONNX Runtime (no PyTorch for this step). When a file path is given,
    audio is loaded to 16 kHz mono via openai-whisper's ffmpeg-based loader; a pre-decoded float32
    waveform is also accepted directly.

    Model selection: pass the persona's content `language` to pick the right model (Chinese -> CN-Celeb;
    any other language -> the multilingual VoxCeleb2 default). An explicit `model_path` overrides routing.
    """

    SAMPLE_RATE = 16000

    def __init__(
        self,
        model_path: str | Path | None = None,
        language: str | None = None,
        configured_model: str | None = None,
    ) -> None:
        if model_path:
            self.model_path = str(Path(model_path).expanduser())
        else:
            # Route by content language (Chinese -> CN-Celeb, else multilingual default), then
            # download once. Validates against the live release and falls back to English if needed.
            self.model_path = str(ensure_speaker_model(resolve_speaker_model(language, configured_model)))
        self._extractor = None

    def _ensure(self):
        if self._extractor is None:
            import sherpa_onnx  # lazy
            cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=self.model_path)
            self._extractor = sherpa_onnx.SpeakerEmbeddingExtractor(cfg)
        return self._extractor

    def _waveform(self, audio) -> np.ndarray:
        if isinstance(audio, (str, Path)):
            import whisper  # openai-whisper: ffmpeg-based 16 kHz mono float32 loader
            return np.asarray(whisper.load_audio(str(audio)), dtype=np.float32)
        return np.asarray(audio, dtype=np.float32)

    def embed(self, audio) -> np.ndarray:
        extractor = self._ensure()
        wav = self._waveform(audio)
        stream = extractor.create_stream()
        stream.accept_waveform(self.SAMPLE_RATE, wav)
        stream.input_finished()
        return np.asarray(extractor.compute(stream), dtype=float)
