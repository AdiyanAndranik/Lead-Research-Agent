from enum import Enum
from pydantic import BaseModel
from backend.app.schemas.lead_input import ParsedLead


class ValidationStatus(str, Enum):
    VALID = "valid"
    DUPLICATE_IN_BATCH = "duplicate_in_batch"
    DUPLICATE_IN_DB = "duplicate_in_db"
    BLACKLISTED = "blacklisted"
    INVALID = "invalid"


class LeadValidationReport(BaseModel):
    lead: ParsedLead
    status: ValidationStatus
    warnings: list[str] = []
    errors: list[str] = []

    @property
    def is_accepted(self) -> bool:
        return self.status == ValidationStatus.VALID


class BatchValidationResult(BaseModel):
    accepted: list[LeadValidationReport]
    rejected: list[LeadValidationReport]
    total_submitted: int
    total_accepted: int
    total_rejected: int
    duplicate_in_batch: int
    duplicate_in_db: int
    invalid: int

    @classmethod
    def from_reports(
        cls, reports: list[LeadValidationReport], total_submitted: int
    ) -> "BatchValidationResult":
        accepted = [r for r in reports if r.is_accepted]
        rejected = [r for r in reports if not r.is_accepted]

        return cls(
            accepted=accepted,
            rejected=rejected,
            total_submitted=total_submitted,
            total_accepted=len(accepted),
            total_rejected=len(rejected),
            duplicate_in_batch=sum(
                1 for r in rejected
                if r.status == ValidationStatus.DUPLICATE_IN_BATCH
            ),
            duplicate_in_db=sum(
                1 for r in rejected
                if r.status == ValidationStatus.DUPLICATE_IN_DB
            ),
            invalid=sum(
                1 for r in rejected
                if r.status == ValidationStatus.INVALID
            ),
        )