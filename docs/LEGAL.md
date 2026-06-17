# Legal and compliance notes

These are notes, not legal advice. The shipped legal audit (`audit/legal_lawyer_agent.md`) produces
drafts for a qualified attorney to review.

## Posture by design
- **Public figures only.** Onboarding verifies a genuine public figure and refuses private individuals.
- **Public content only.** The system uses publicly accessible material on the user's own machine.
- **No bundled or redistributed content.** The repo ships no third-party copyrighted material; generated
  transcripts and audio stay local and git-ignored. The only knowledge files in the repo are the
  fictional `demo/john_doe/` set.
- **Unendorsed persona, always disclosed.** Every answer carries a standing disclaimer; `endorsed` is
  always false. See `DISCLAIMER.md`.

## Areas the legal audit covers
1. **Privacy / data protection (DPIA).** Whether personal data is processed, and whether minimization
   and a lawful basis hold; for the biometric voice fingerprint a full DPIA (GDPR Art. 35) is likely
   required. Jurisdictional assumptions (e.g. GDPR) are surfaced for the user to confirm.
2. **Open-source license compliance.** Dependency licenses vs the project's MIT license; no shipped
   copyrighted content.
3. **Persona / right-of-publicity.** Personality-rights and publicity considerations for modeling a
   public figure; transparency that output is AI-generated and unendorsed; no impersonation for deception.

## Biometric voice data (highest sensitivity)
Voice isolation (`pipeline/voice.py`) builds a **voice fingerprint** (a speaker-embedding vector) to
uniquely recognize the figure's voice. This is generally a **biometric identifier** and, under GDPR, a
**special category of personal data (Article 9)**. The public-figure posture does NOT exempt Article 9
data. Treat it as the highest-sensitivity processing in the system:
- **No GDPR Art. 9 exemption applies by default.** "Manifestly made public by the data subject"
  (Art. 9(2)(e)) does NOT cover building a biometric voiceprint: the EDPB reads it with a high threshold,
  and purpose-limitation binds the use; publishing a talk is not making one's voiceprint public. The only
  realistic basis is explicit consent (Art. 9(2)(a)); without it, run with `voice.enabled: false`.
- **A DPIA is likely mandatory (Art. 35).** Biometric data combined with innovative technology and the
  systematic matching of sources triggers a Data Protection Impact Assessment, and where high residual
  risk remains, prior consultation with the supervisory authority (Art. 36). Run it before processing.
- **Inform the data subject (Art. 14).** Because the data is gathered from third-party public sources
  rather than from the figure, the Art. 14 information duty applies (equivalent transparency/notice
  obligations exist under most modern data-protection frameworks);
  the disproportionate-effort exception is not automatic.
- **UK.** Under UK GDPR the result is the same: ICO biometric-recognition guidance (Mar 2024) treats a
  voiceprint as special-category data needing explicit consent, and the Data (Use and Access) Act 2025
  does not relax special-category data.
- The fingerprint (`*.npy`) and downloaded audio stay local under git-ignored `work/`. Set a
  **retention and deletion schedule** and delete them when no longer needed (Art. 5(1)(e); the biometric
  statutes expect this); the tool provides no automatic expiry or purge.
- A lawful basis for the biometric processing is required; if none, run with `voice.enabled: false`
  (the system degrades to a manual/low-confidence mode and builds no fingerprint). Privacy-by-default
  (GDPR Art. 25(2)) favors leaving voice off unless you have explicit consent; the shipped default is on.
- Some jurisdictions have dedicated biometric-privacy statutes in addition to GDPR.

## Jurisdiction-specific data-protection law
If you are subject to a national or regional data-protection law in addition to GDPR (for example, a
national implementation, a state biometric statute, or another sectoral law), that law applies to your
processing. The publisher ships no real data and is not the data controller; these duties fall on the
user. Key principles that apply across most jurisdictions:
- **The voice fingerprint is special-category personal data** (biometric data used to uniquely identify
  a natural person). Most modern data-protection frameworks (GDPR Art. 9, and equivalent provisions
  elsewhere) require explicit consent or another specific statutory basis to process it. For an
  unconsented public figure, explicit consent is the only realistic basis. With no explicit consent,
  run with `voice.enabled: false`; the system then builds no biometric fingerprint.
- **"Public figure" / "publicly available" is NOT, by itself, a lawful basis for special-category
  data.** A figure who published a talk made their speech public, not a biometric voiceprint derived
  from it; purpose-limitation means fingerprinting for identification is a distinct purpose, and the
  "made public by the data subject" exception does not cover it under GDPR or equivalent frameworks.
- When you model a real person you are the **data controller**: transparency/notice obligations,
  security, and retention/deletion duties are yours. Delete `work/<slug>/` and
  `~/personaforge_brains/<slug>` when done.
- **Cross-border.** The voice models run locally, so audio stays on your machine, but
  Exa/WebSearch queries about the figure may transfer data to third-country processors; you own the
  lawful basis for that transfer. A non-commercial, clearly labeled research use may qualify for
  exemptions under applicable law, but this is fact-specific and does not by itself cover the biometric
  fingerprinting step.
- Modeling a real person's voice, name, or image may also engage **personality rights** and expose you
  to **non-pecuniary damages** claims under applicable civil law. Post-mortem personality and
  publicity rights may apply; heirs and close relatives may have independent claims.
- **Deceased figures.** Many data-protection laws protect only living natural persons; post-mortem
  protection runs through personality-rights and publicity-rights law, and heirs may assert claims in
  their own right. Confirm the applicable rules in your jurisdiction.

## United States
US right-of-publicity and biometric law is mostly **state law**; the user is responsible for the
analysis for their figure, use, and state:
- **Right of publicity, including AI voice replicas.** Voice and likeness are protected under California
  Civ. Code 3344 and 3344.1 (the latter's "digital replica" right for deceased personalities added by
  AB 1836, in force Jan 1 2026; living performers covered by AB 2602, in force Jan 1 2025), New York
  Civil Rights Law 50-51 (and 50-f for deceased performers), and the **Tennessee ELVIS Act of 2024**,
  which protects an individual's voice regardless of whether the use features the real voice or an
  AI-generated replica. This tool produces no audio replica, so these mainly bite on the persona's text
  in a commercial, advertising, or endorsement context; a non-commercial, clearly labeled, transformative
  research use is the lowest-risk use. The federal **NO FAKES Act** (reintroduced Apr 9 2025) is pending
  and targets replicas, which this tool does not generate.
- **Biometric privacy.** A voice fingerprint is a "voiceprint" under the Illinois **BIPA** (740 ILCS 14),
  whose Section 15(b) notice-and-written-release duty binds any private entity regardless of commercial
  purpose and carries a private right of action. The **Texas CUBI** and **Washington (RCW 19.375)**
  statutes are similar but gated to a commercial purpose and are enforced by the state, not private suit.
  All require notice, prior consent, and a retention/destruction schedule before collection; "publicly
  available" is not an exemption. MaskPersona AI collects nothing; you do, locally, when you run it. If
  you cannot meet these, run with `voice.enabled: false`.
- **False endorsement (Lanham Act 43(a)) and FTC impersonation.** The enforced `endorsed=false` invariant
  and the "not the real person" disclaimer reduce false-endorsement exposure; do not imply endorsement.
  The FTC's operative impersonation rule (16 CFR 461, eff. Apr 2024) covers government and business, not
  individuals, and in its Dec 26 2024 final action the FTC declined to adopt the proposed
  means-and-instrumentalities ("reason to know") provision that would have reached tool publishers; an
  individual-impersonation extension remains proposed, not final.
- **Publisher vs user.** Under Sony (1984) a tool with substantial non-infringing uses is not
  contributorily liable merely by existing, and under Grokster (2005) liability attaches to active
  inducement of misuse. MaskPersona AI is a general-purpose instrument with clear lawful uses that does
  not market or induce misuse (ACCEPTABLE_USE.md, the public-figure gate, `endorsed=false`, no audio
  synthesis); the user chooses the use and bears the use-specific risk.
- **Copyright / fair use.** Processing lawfully accessible public content without redistributing it is
  the lowest-risk posture: Bartz v. Anthropic (2025) found training on lawfully acquired works
  transformative, but also held that using pirated copies is NOT fair use (a $1.5B settlement followed).
  **Never ingest pirated or paywalled sources.**

## Controller and lawful basis
When run against a real figure, **the user is the data controller**, not this project. "Publicly
available" is not, by itself, a lawful basis. The user owns the lawful basis, retention/deletion, and
any commercial/endorsement and post-mortem-rights implications.

Retention note: the mined knowledge brain is personal data and lives outside the repo at
`~/personaforge_brains/<slug>`. `make clean` clears `work/<slug>/` (transcripts, audio, fingerprint)
but does NOT touch the brain, so delete that directory yourself when retiring a persona. There is no
automatic expiry on any of this; set a retention schedule and delete on it.

## Dependency and model licenses
The project code is MIT; dependencies are pinned in `pyproject.toml` (see `NOTICE`). The voice models
download at runtime from public release assets (no account or access token) and carry **their own
licenses** distinct from this project's LICENSE; you remain responsible for honoring each weight's
license before redistribution. No third-party copyrighted content is shipped.

## Your responsibility
Comply with the source platforms' terms and your jurisdiction's law (data protection including GDPR
Article 9 for the voice fingerprint, biometric-privacy statutes, publicity/personality rights including
post-mortem). Do not present the bot as the real person or imply endorsement. If unsure, consult an attorney.
