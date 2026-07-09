from pydantic import BaseModel, Field

class DimensionScore(BaseModel):
    score: int = Field(ge=1, le=10)
    reasoning: str


class ScoreOutput(BaseModel):
    """
    Structured output from the lead scoring LLM.
    Every field is required — the LLM must justify every score.
    """
    overall_score: int = Field(ge=1, le=10)
    confidence: float = Field(ge=0.0, le=1.0)

    icp_fit: DimensionScore
    pain_alignment: DimensionScore
    tech_maturity: DimensionScore
    timing: DimensionScore
    budget_signal: DimensionScore

    overall_reasoning: str
    recommended_action: str
    passed_threshold: bool



    