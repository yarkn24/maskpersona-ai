"""Media helpers for the ingestion pipeline: audio download, transcription, waveform slicing.

Heavy dependencies (yt-dlp, openai-whisper) are imported lazily inside each function, so importing this
module costs nothing and the graph-wiring tests run without the ML/network stack. Real runs need ffmpeg
on PATH and the openai-whisper package (the `[voice]` extra); yt-dlp is a base dependency.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000  # whisper and sherpa-onnx both operate on 16 kHz mono audio


def download_audio(url: str, dest_dir: str | Path, video_id: str) -> Path:
    """Download one video's audio to <dest_dir>/<video_id>.wav (16 kHz mono). Resume-safe: skips if present."""
    dest = Path(dest_dir).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    wav = dest / f"{video_id}.wav"
    if wav.exists() and wav.stat().st_size > 0:
        return wav
    import yt_dlp  # lazy
    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": str(dest / f"{video_id}.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        "postprocessor_args": ["-ar", str(SAMPLE_RATE), "-ac", "1"],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return wav


def load_waveform(audio_path: str | Path) -> np.ndarray:
    """Load audio as a 16 kHz mono float32 waveform via whisper's ffmpeg-based loader."""
    import whisper  # lazy (openai-whisper)
    return np.asarray(whisper.load_audio(str(audio_path)), dtype=np.float32)


def transcribe_audio(audio_path: str | Path, language: str | None = None,
                     model_size: str = "base") -> list[dict]:
    """Transcribe to timestamped segments [{start, end, text}] with openai-whisper.

    `language` is a code like "tr"/"en"; None or "auto" lets whisper detect per file. `model_size`
    trades accuracy for speed/size ("base" by default; "large-v3" is the most accurate multilingual model).
    """
    import whisper  # lazy
    model = whisper.load_model(model_size)
    lang = None if (not language or language == "auto") else language
    result = model.transcribe(str(audio_path), language=lang, verbose=False)
    return [
        {"start": float(s["start"]), "end": float(s["end"]), "text": (s.get("text") or "").strip()}
        for s in result.get("segments", [])
    ]


def slice_waveform(wav: np.ndarray, start: float, end: float,
                   sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Return the [start, end] (seconds) slice of a waveform array."""
    a = max(0, int(start * sample_rate))
    b = min(len(wav), int(end * sample_rate))
    return wav[a:b] if b > a else wav[:0]
