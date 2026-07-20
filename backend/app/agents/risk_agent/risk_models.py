from pydantic import BaseModel, Field

class RiskFactorModel(BaseModel):
    name: str = Field(description="Name/Code of the risk factor (e.g., repeat_offending)")
    label: str = Field(description="Display label of the risk factor")
    score: float = Field(description="Calculated score contribution for this factor")
    max_score: float = Field(description="Maximum possible score for this factor")
    reason: str = Field(description="Textual explanation of why this score contribution was generated")

class BehavioralTagModel(BaseModel):
    code: str = Field(description="Short uppercase code of the tag, e.g. REPEAT_OFFENDER")
    label: str = Field(description="Display label of the tag, e.g. Repeat Offender")
    reason: str = Field(description="Explanation of why the tag was assigned")
    evidence: str | None = Field(None, description="Detailed evidence supporting this tag assignment")

class OffenderRiskProfile(BaseModel):
    person_id: str = Field(description="Unique aggregate identifier of the person")
    name: str = Field(description="Suspect name")
    risk_score: float = Field(description="Prioritization score from 0 to 100")
    risk_level: str = Field(description="Risk Level category (LOW, MEDIUM, HIGH, CRITICAL)")
    risk_factors: list[RiskFactorModel] = Field(default_factory=list, description="List of risk score factors")
    behavioral_tags: list[BehavioralTagModel] = Field(default_factory=list, description="List of behavioral tagging records")
    district: str = Field(description="Primary district associated with the offender")
    case_count: int = Field(description="Total number of cases linked to this offender")

class RiskSummaryResponse(BaseModel):
    total_offenders_analyzed: int
    risk_distribution: dict[str, int] = Field(
        description="Count of offenders per risk level (low, medium, high, critical)"
    )

class RiskAgentResponse(BaseModel):
    agent: str = "RiskAgent"
    status: str = "success"
    summary: str = Field(description="Gemini-generated briefing summary explaining the risk factors")
    details: OffenderRiskProfile | list[OffenderRiskProfile]
