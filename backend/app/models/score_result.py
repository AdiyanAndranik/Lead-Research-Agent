import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class ScoreResult(Base):
    __tablename__ = "score_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id"), nullable=False, unique=True
    )

    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    icp_fit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pain_alignment_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tech_maturity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timing_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_signal_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    dimension_reasoning: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    passed_threshold: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    lead: Mapped["Lead"] = relationship(back_populates="score_result")

    