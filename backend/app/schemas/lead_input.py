from pydantic import BaseModel, field_validator
from typing import Optional


class RawLeadInput(BaseModel):
    """A single raw lead as provided by the user — before any normalization."""
    raw: str

    @field_validator("raw")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Lead input cannot be empty")
        return v.strip()


class ParsedLead(BaseModel):
    """A lead after parsing and normalization — ready to be stored."""
    raw_input: str
    company_name: str
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_duplicate: bool = False
    parse_confidence: float = 1.0  # how confident we are in the parsed result


class ParseResult(BaseModel):
    """Result of parsing a full batch of leads."""
    parsed: list[ParsedLead]
    duplicates_removed: int
    invalid_removed: int
    total_submitted: int

    @property
    def accepted(self) -> int:
        return len(self.parsed)
    


    