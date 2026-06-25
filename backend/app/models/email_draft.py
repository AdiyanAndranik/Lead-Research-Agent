import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class EmailVariant(str, PyEnum):
    PAIN_FIRST = "pain_first"
    OPPORTUNITY_FIRST = "opportunity_first"
    SOCIAL_PROOF_FIRST = "social_proof_first"


class EmailStatus(str, PyEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"


class EmailDraft(Base):
    __tablename__ = "email_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id"), nullable=False
    )

    variant: Mapped[EmailVariant] = mapped_column(Enum(EmailVariant), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    subject_line: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus), default=EmailStatus.DRAFT
    )
    reviewer_edits: Mapped[str | None] = mapped_column(Text, nullable=True)
    edit_distance: Mapped[int | None] = mapped_column(Integer, nullable=True)

    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    personalization_signals_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_flags: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    lead: Mapped["Lead"] = relationship(back_populates="email_drafts")
    