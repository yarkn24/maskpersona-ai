# Voice-fingerprint isolation

> **IMPORTANT: MaskPersona AI does NOT synthesize, clone, or generate audio.** The voice fingerprint is a
> numerical speaker-identity vector used only to filter which speech turns in a recording belong to the
> subject. It cannot produce speech. If you need voice synthesis, this is the wrong tool.

## The problem
In a multi-speaker panel, which turns belong to the figure? A naive approach guesses by "who uses the
most domain vocabulary", which is fragile: a host who keeps repeating the topic words gets misattributed.

## The method (`pipeline/voice.py`)
1. **Learn the voice from solo videos.** Solo videos are single-speaker, so they are clean. Embed each
   solo segment (speaker-embedding model) and average into one normalized **fingerprint**
   (`build_fingerprint`).
2. **Isolate panels by biometric match.** For each panel turn, embed it and take the cosine similarity
   to the fingerprint. Keep the turn only if similarity is above the configured threshold (`isolate`).
3. **Low-confidence gate.** If no turn matches well, `IsolationResult.low_confidence` is set and the
   pipeline raises the `confirm_low_confidence` human interrupt before writing anything to the brain.

## Why it is better
It is a biometric identity match, not a topic guess. The pure logic (cosine, fingerprint, isolate) is
dependency-free and unit-tested with synthetic embeddings; the actual audio embedding (sherpa-onnx) is
behind the `Embedder` protocol and imported lazily.

## Degraded mode
If a figure has no solo content (only panels), there is no fingerprint seed. The system does NOT fall
back to a vocabulary heuristic; it drops to a manual/low-confidence mode and asks the user.

## Biometric data (important)
A voice fingerprint that uniquely recognizes a person's voice is a **biometric identifier**, and under
GDPR a **special category of personal data (Article 9)**. The public-figure posture does NOT exempt it.
The fingerprint (`*.npy`) and audio stay local under git-ignored `work/`, should be deleted when no
longer needed, and require a lawful basis. If you cannot establish one, set `voice.enabled: false` to
skip fingerprinting entirely. See `DISCLAIMER.md` and `docs/LEGAL.md`.

## Language handling
The persona's source content language is `language.content` in `persona.yaml` ("auto" by default).
- **Transcription** is one multilingual Whisper model (large-v3, 99 languages). There is no per-language
  pack to install; the language is auto-detected per video, or pinned via `language.content`.
- **Speaker embedding** routes by content language. A speaker model captures voice TIMBRE, not words,
  and the default (wespeaker ResNet34-LM, trained on VoxCeleb2 across 145 nationalities) is multilingual,
  so it works for any language (Turkish, Spanish, French, ...). Only Chinese gets a dedicated model
  (CN-Celeb); every other language uses the default. The chosen model is verified against the live
  release before download and falls back to the English VoxCeleb default if a language-specific asset
  is missing. See `pipeline/voice.py::resolve_speaker_model`.

## Requirements
No account or access token. The default speaker-embedding model is wespeaker ResNet34-LM trained on
VoxCeleb2, the same model family the earlier pyannote path used, ONNX-exported and pulled once from a
public release; it runs on CPU via ONNX Runtime with no PyTorch. `pip install "maskpersona-ai[voice]"`
is the whole setup. Transcription (openai-whisper) downloads its weights automatically on first use.
Model filenames live in `pipeline/voice.py` (routing) and `config/defaults.yaml` (override) so they
survive vendor churn. Model weights carry their own licenses (permissive for these assets), distinct
from this project's MIT license.
