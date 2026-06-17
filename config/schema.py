"""MaskPersona AI configuration schema.

Single source of truth for every per-figure value. All the values that, in a one-off persona bot,
would be hardcoded (name, paths, domain vocab, search query, claims) live here as validated fields.

Constitution Article 2: no absolute machine paths. Path fields must be home-rooted (tilde) or
repo-relative; a hardcoded absolute user-home path is rejected. Paths resolve at runtime, per machine.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def slugify(name: str) -> str:
    """A filesystem/command/wing-safe slug derived from a display name."""
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    return re.sub(r"-+", "-", s).strip("-")


def _reject_machine_path(v: Optional[str]) -> Optional[str]:
    """Enforce Article 2: no absolute machine paths baked into config."""
    if v is None:
        return v
    if v.startswith("/Users/") or v.startswith("/home/") or re.match(r"^[A-Za-z]:\\", v):
        raise ValueError(
            f"absolute machine path not allowed (constitution Art.2): {v!r}; "
            "use '~/...' or a repo-relative path"
        )
    return v


def resolve_path(v: str) -> Path:
    """Resolve a config path at runtime (expand ~, leave repo-relative as-is)."""
    return Path(v).expanduser()


class Persona(BaseModel):
    name: str
    slug: str = ""  # auto-derived from name if empty
    role: str = ""
    bio: str = ""
    lens: str = ""
    is_public_figure: bool = False  # set True only after the public-figure gate
    identity_confirmed: bool = False  # set True only after the y/n confirm
    endorsed: bool = False  # always False -> drives the disclaimer line

    @field_validator("endorsed")
    @classmethod
    def _endorsed_must_be_false(cls, v: bool) -> bool:
        # Invariant (not just convention): a persona is never the real person's endorsed opinion.
        if v:
            raise ValueError("endorsed must be False: a persona is unendorsed by design")
        return v

    @model_validator(mode="after")
    def _fill_slug(self) -> "Persona":
        if not self.slug:
            self.slug = slugify(self.name)
        return self


class Language(BaseModel):
    output: str = "en"  # the language the persona answers in
    content: str = "auto"  # the persona's SOURCE content language (their talks/articles), e.g. "tr",
    # "zh", "es"; "auto" = detect per video. Drives transcription language and speaker-model routing.
    input_normalization: Literal["none", "diacritic"] = "none"
    diacritic_map: dict[str, str] = Field(default_factory=dict)


class Domain(BaseModel):
    field: str = ""
    topics: list[str] = Field(default_factory=list)  # starts empty; ingestion agent fills
    scope_mode: Literal["niche", "broad"] = "niche"
    fixed_topics: list[str] = Field(default_factory=list)  # chosen at scope_gate for broad figures
    question_categories: list[str] = Field(
        default_factory=lambda: [
            "advice", "decision", "thesis", "strategy",
            "flexibility", "fabrication_trap", "stance_bait",
        ]
    )


class Brain(BaseModel):
    backend: Literal["mempalace", "inmemory"] = "mempalace"
    palace_path: str = ""  # default ~/personaforge_brains/<slug>
    wing: str = ""  # default <slug-as-wing>
    search_results: int = 6

    _v = field_validator("palace_path")(_reject_machine_path)


class Sources(BaseModel):
    video_search_query: str = ""
    video_search_count: int = 50
    seed_video_urls: list[str] = Field(default_factory=list)
    article_urls: list[str] = Field(default_factory=list)
    exclude_ids: list[str] = Field(default_factory=list)


class Voice(BaseModel):
    enabled: bool = True
    embedding_model: str = ""  # default from config/defaults.yaml
    fingerprint_path: str = ""  # default work/<slug>/voice_fingerprint.npy
    match_threshold: float = 0.50  # cosine similarity to accept a panel turn
    min_solo_seconds: int = 120  # min clean solo audio to trust a fingerprint

    _v = field_validator("fingerprint_path")(_reject_machine_path)


class SignatureClaim(BaseModel):
    key: str
    phrase: str


class Citations(BaseModel):
    signature_claims: list[SignatureClaim] = Field(default_factory=list)  # starts empty
    index_path: str = ""  # default work/<slug>/citations_index.csv

    _v = field_validator("index_path")(_reject_machine_path)


class Search(BaseModel):
    enabled: bool = True
    result_count: int = 10  # Exa results per search_person call
    use_autoprompt: bool = True  # Exa autoprompt rewrites query for better recall


class Schedule(BaseModel):
    enabled: bool = False
    label: str = ""  # default personaforge.<slug>.train (no owner name)
    cron: str = "0 4 * * 0"  # weekly


class Sizing(BaseModel):
    """Volume estimate shown to the user before any heavy ingestion runs."""
    est_videos: Optional[int] = None
    est_hours: Optional[float] = None
    est_gb: Optional[float] = None
    est_files: Optional[int] = None


class Eval(BaseModel):
    num_questions: int = 100
    pass_threshold: float = 0.6
    flexibility_threshold: float = 0.8
    langsmith_project: str = ""  # default personaforge-<slug>


class FidelityGate(BaseModel):
    """Runtime self-check: before sending, the persona rates how well its draft is grounded in the
    figure's public content, and gates on that score. Token-efficient by design (the persona self-rates
    inline; no extra model call per answer)."""
    enabled: bool = True
    send_threshold: float = 0.75   # score >= this -> send the answer
    floor: float = 0.50            # score < this  -> refuse to answer, ask for more context
    max_attempts: int = 2          # rounds (re-search brain, then grill the user) to raise the score

    @model_validator(mode="after")
    def _check_band(self) -> "FidelityGate":
        if not (0.0 <= self.floor <= self.send_threshold <= 1.0):
            raise ValueError("fidelity gate requires 0 <= floor <= send_threshold <= 1")
        if self.max_attempts < 0:
            raise ValueError("fidelity gate max_attempts must be >= 0")
        return self


class PersonaConfig(BaseModel):
    """The whole persona.yaml. Onboarding produces this; everything else reads it."""
    persona: Persona
    language: Language = Field(default_factory=Language)
    domain: Domain = Field(default_factory=Domain)
    brain: Brain = Field(default_factory=Brain)
    sources: Sources = Field(default_factory=Sources)
    voice: Voice = Field(default_factory=Voice)
    citations: Citations = Field(default_factory=Citations)
    search: Search = Field(default_factory=Search)
    schedule: Schedule = Field(default_factory=Schedule)
    sizing: Sizing = Field(default_factory=Sizing)
    eval: Eval = Field(default_factory=Eval)
    fidelity: FidelityGate = Field(default_factory=FidelityGate)

    @model_validator(mode="after")
    def _fill_dependent_defaults(self) -> "PersonaConfig":
        slug = self.persona.slug
        if not self.brain.palace_path:
            self.brain.palace_path = f"~/personaforge_brains/{slug}"
        if not self.brain.wing:
            self.brain.wing = slug.replace("-", "_")
        if not self.voice.fingerprint_path:
            self.voice.fingerprint_path = f"work/{slug}/voice_fingerprint.npy"
        if not self.citations.index_path:
            self.citations.index_path = f"work/{slug}/citations_index.csv"
        if not self.schedule.label:
            self.schedule.label = f"personaforge.{slug}.train"
        if not self.eval.langsmith_project:
            self.eval.langsmith_project = f"personaforge-{slug}"
        return self

    @property
    def work_dir(self) -> Path:
        return Path("work") / self.persona.slug
