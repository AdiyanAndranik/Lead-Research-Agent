import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class LeadStatus(str, PyEnum):
    QUEUED = "queued"
    RESEARCHING = "researching"
    SCORING = "scoring"
    GENERATING_EMAIL = "generating_email"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    SKIPPED = "skipped"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pipeline_runs.id"), nullable=False
    )

    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.QUEUED, nullable=False
    )

    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_estimate: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tech_signals: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    pipeline_run: Mapped["PipelineRun"] = relationship(back_populates="leads")
    research_result: Mapped["ResearchResult | None"] = relationship(
        back_populates="lead", uselist=False
    )
    score_result: Mapped["ScoreResult | None"] = relationship(
        back_populates="lead", uselist=False
    )
    email_drafts: Mapped[list["EmailDraft"]] = relationship(back_populates="lead")

    