# Disclaimer and responsible use

MaskPersona AI produces an **unendorsed persona interpretation** of a public figure, built from their
**public content**. Please read before using.

## What a MaskPersona AI bot is and is not

- **Is:** an AI agent that reasons in the style of, and grounded in, a public figure's publicly
  available talks and writing.
- **Is not:** the real person, their employer, or anyone who has reviewed or approved the output. It
  is not legal, financial, medical, or professional advice.

Every answer carries a standing disclaimer to this effect.

## Hard limits enforced by the tool

1. **Public figures only.** Onboarding verifies the target is a genuine public figure with public
   content and **refuses private individuals**. Do not attempt to model a private person.
2. **Public content only.** The tool uses publicly accessible material. It does not access private,
   paywalled, improperly obtained, or non-consensual data.
3. **No content redistribution.** Transcripts and audio are processed locally under `work/` and are
   never committed or redistributed by this repository.
4. **Grounded, not fabricated.** The persona is built to refuse inventing quotes, numbers, or events,
   and to mark extrapolation explicitly.

## Biometric data (voice fingerprint)

Voice isolation builds a **voice fingerprint**: a speaker-embedding vector used to recognize the
figure's voice and isolate their turns in panels. **MaskPersona AI does not synthesize, clone, or
generate audio**; the fingerprint is a numerical identity vector used only to filter which speech turns
belong to the subject, and it cannot produce speech.

A voice embedding used to uniquely identify a person is generally a **biometric identifier** and, under
GDPR, a **special category of personal data (Article 9)** for which "manifestly made public" is not a
basis; explicit consent is the realistic one. Under applicable data-protection law in many jurisdictions,
a voice fingerprint is special-category personal data for which explicit consent is the only realistic
lawful basis for an unconsented public figure. In the US it is a "voiceprint" under the Illinois
**BIPA** (Section 15(b) binds any private entity and carries a private right of action) and the
Texas/Washington statutes (gated to a commercial purpose); all require notice, prior consent, and a
retention schedule. "Public figure" and "public content" do **not** by themselves provide a lawful basis
for processing special-category data.

- The fingerprint (`*.npy`) and any downloaded audio are processed **locally** on your machine, under
  git-ignored `work/`, and are never committed or redistributed by this tool.
- You should delete the audio and the fingerprint when they are no longer needed, and you must have a
  lawful basis for the biometric processing in your jurisdiction. Privacy-by-default (GDPR Art. 25(2))
  favors leaving voice off unless you have explicit consent.
- If you cannot establish a lawful basis, run with `voice.enabled: false` (the system then degrades to
  a manual/low-confidence mode and does not build a biometric fingerprint).

## You are the data controller

When you run MaskPersona AI against a real figure, **you** are the data controller for that processing,
not this project. "Publicly available" is not, on its own, a lawful basis. You are responsible for the
lawful basis, retention/deletion, and any commercial or endorsement implications, including
**post-mortem** personality/publicity rights where they apply. For a deceased figure, post-mortem
publicity and personality rights may still apply under applicable law in your jurisdiction; heirs may
also have independent claims.

The data you generate is personal data: transcripts, audio, and the voice fingerprint under
`work/<slug>/`, plus the mined knowledge brain under `~/personaforge_brains/<slug>`. Delete it when no
longer needed; `make clean` clears `work/` but not the brain directory, which you remove yourself.

## Your responsibilities

- Comply with the source platforms' terms of service and with applicable law in your jurisdiction,
  including data protection (GDPR Art. 9, US BIPA / state biometric statutes, and other applicable
  data-protection law for the voice fingerprint), and right-of-publicity / personality rights. Voice is
  specifically protected against AI replicas under the **Tennessee ELVIS Act (2024)**, California
  Civ. Code 3344, and personality-rights law in many jurisdictions; post-mortem rights and
  non-pecuniary damages claims may also apply.
- Do not present the bot as the real person or imply endorsement, and take extra care with any
  commercial use.
- Read and follow [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md). Do not use it to harass, defame, deceive,
  impersonate for fraud, run political disinformation, or commercially exploit a person's voice, name,
  or likeness without consent.

If you are unsure whether your use is lawful, consult a qualified attorney. The legal notes shipped
with this tool (`docs/LEGAL.md`, `ACCEPTABLE_USE.md`) are **drafts for review, not legal advice**.
