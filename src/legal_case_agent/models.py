from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Summary(StrictModel):
    case_type: str = "待核实"
    parties: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    stage: str = "待核实"
    sources: list[str] = Field(default_factory=list)


class TimelineEvent(StrictModel):
    date: str
    event: str
    actors: list[str] = Field(default_factory=list)
    confidence: str = "待核实"
    sources: list[str]


class EvidenceItem(StrictModel):
    name: str
    purpose: str
    authenticity: str
    legality: str
    relevance: str
    risks: list[str] = Field(default_factory=list)
    sources: list[str]


class Issue(StrictModel):
    title: str
    claimant_position: str = "待核实"
    respondent_position: str = "待核实"
    known_facts: list[str] = Field(default_factory=list)
    verification_needed: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class CaseReport(StrictModel):
    summary: Summary
    timeline: list[TimelineEvent]
    evidence: list[EvidenceItem]
    issues: list[Issue]
    missing_materials: list[str]
    hearing_checklist: list[str]
    manual_review: list[str]
