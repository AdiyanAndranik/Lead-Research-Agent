import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Integer, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class RunStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="runstatus", create_type=False),
        default=RunStatus.PENDING,
        nullable=False,
    )
    total_leads: Mapped[int] = mapped_column(Integer, default=0)
    processed_leads: Mapped[int] = mapped_column(Integer, default=0)
    failed_leads: Mapped[int] = mapped_column(Integer, default=0)

    min_score_threshold: Mapped[int] = mapped_column(Integer, default=6)
    email_tone: Mapped[str] = mapped_column(String(50), default="conversational")
    email_angle: Mapped[str] = mapped_column(String(50), default="pain")
    target_company_size: Mapped[str] = mapped_column(String(50), default="any")
    custom_scoring_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    leads: Mapped[list["Lead"]] = relationship(back_populates="pipeline_run")

    