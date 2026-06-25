import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class ResearchResult(Base):
    __tablename__ = "research_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id"), nullable=False, unique=True
    )

    homepage_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    about_page_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_offering: Mapped[str | None] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recent_news: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    funding_signals: Mapped[str | None] = mapped_column(Text, nullable=True)
    pain_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    tools_used: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    scrape_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    lead: Mapped["Lead"] = relationship(back_populates="research_result")

    