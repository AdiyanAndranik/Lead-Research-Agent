from pydantic import BaseModel, Field
from typing import Optional
from backend.app.schemas.validation import LeadValidationReport


class PipelineConfig(BaseModel):
    min_score_threshold: int = Field(default=6, ge=1, le=10)
    email_tone: str = Field(default="conversational")
    email_angle: str = Field(default="pain")
    target_company_size: str = Field(default="any")
    custom_scoring_instructions: Optional[str] = None


class TextIngestionRequest(BaseModel):
    text: str = Field(
        ...,
        description="Newline-separated list of companies. "
                    "Accepts names, URLs, LinkedIn URLs, or mixed.",
        json_schema_extra={"example": "Linear, linear.app\nhttps://stripe.com\nNotion"},
    )
    config: PipelineConfig = Field(default_factory=PipelineConfig)


class JSONIngestionRequest(BaseModel):
    leads: list[dict] = Field(
        ...,
        description="Array of lead objects with any of: company, url, linkedin fields.",
        json_schema_extra={
            "example": [
                {"company": "Linear", "url": "linear.app"},
                {"company": "Stripe", "url": "stripe.com"},
            ]
        },
    )
    config: PipelineConfig = Field(default_factory=PipelineConfig)


class ValidationSummary(BaseModel):
    total_submitted: int
    total_accepted: int
    total_rejected: int
    duplicate_in_batch: int
    duplicate_in_db: int
    invalid: int
    rejected_details: list[LeadValidationReport]


class PipelineLaunchResponse(BaseModel):
    pipeline_run_id: Optional[str]
    status: str
    validation: ValidationSummary
    task_ids: list[str]
    message: str


class PipelineStatusResponse(BaseModel):
    pipeline_run_id: str
    status: str
    total_leads: int
    processed_leads: int
    failed_leads: int
    created_at: str
    completed_at: Optional[str]

