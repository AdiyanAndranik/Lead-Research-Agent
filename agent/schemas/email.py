from pydantic import BaseModel
from enum import Enum


class EmailTone(str, Enum):
    CONVERSATIONAL = "conversational"
    FORMAL = "formal"
    BRIEF = "brief"


class EmailAngle(str, Enum):
    PAIN_FIRST = "pain"
    OPPORTUNITY_FIRST = "opportunity"
    SOCIAL_PROOF_FIRST = "social_proof"


class EmailDraftOutput(BaseModel):
    variant: str
    subject_line: str
    body: str
    word_count: int
    personalization_signals: list[str]
    

class EmailGenerationOutput(BaseModel):
    drafts: list[EmailDraftOutput]
    primary_variant: str
    quality_flags: list[str]

    