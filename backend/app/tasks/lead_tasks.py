import uuid
import logging
from datetime import datetime, timezone
from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.worker import celery_app
from backend.app.core.config import settings
from backend.app.models.lead import Lead, LeadStatus
from backend.app.models.pipeline_run import PipelineRun, RunStatus

logger = logging.getLogger(__name__)

# Sync engine for Celery workers (Celery doesn't support async)
sync_engine = create_engine(
    settings.database_url_sync,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SyncSession = sessionmaker(bind=sync_engine)


def get_sync_session() -> Session:
    return SyncSession()


class BaseTaskWithRetry(Task):
    """
    Base Celery task class with automatic retry on failure.
    All lead processing tasks inherit from this.
    """
    abstract = True
    max_retries = 3
    default_retry_delay = 60  # seconds

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            f"Task {self.name} failed permanently",
            extra={
                "task_id": task_id,
                "exception": str(exc),
                "args": args,
            },
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(
            f"Task {self.name} retrying",
            extra={
                "task_id": task_id,
                "exception": str(exc),
                "retry_count": self.request.retries,
            },
        )


@celery_app.task(
    bind=True,
    base=BaseTaskWithRetry,
    name="tasks.process_lead",
    max_retries=3,
    default_retry_delay=30,
)
def process_lead_task(self, lead_id: str, pipeline_run_id: str) -> dict:
    """
    Main pipeline task for a single lead.
    Runs the full research → score → email pipeline.
    """
    import asyncio
    from agent.graph import research_graph
    from agent.state import ResearchState

    session = get_sync_session()
    try:
        lead = session.query(Lead).filter(Lead.id == uuid.UUID(lead_id)).first()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return {"status": "error", "message": "Lead not found"}

        logger.info(f"Processing lead: {lead.company_name}")

        # Update status to researching
        lead.status = LeadStatus.RESEARCHING
        lead.updated_at = datetime.now(timezone.utc)
        session.commit()

        # Build initial state
        initial_state = ResearchState(
            lead_id=lead_id,
            company_name=lead.company_name,
            domain=lead.domain,
            linkedin_url=lead.linkedin_url,
        )

        # Run the research graph
        final_state = asyncio.run(research_graph.ainvoke(initial_state))

        # Persist research results
        from backend.app.models.research_result import ResearchResult
        research = ResearchResult(
            id=uuid.uuid4(),
            lead_id=uuid.UUID(lead_id),
            company_description=final_state.get("company_description"),
            product_offering=final_state.get("product_offering"),
            pain_points=final_state.get("pain_points", []),
            funding_signals=final_state.get("funding_signals"),
            tech_stack={"detected": final_state.get("tech_signals", [])},
            tools_used=final_state.get("tools_used", []),
            created_at=datetime.now(timezone.utc),
        )
        session.add(research)

        # Update lead with industry and size
        lead.industry = final_state.get("industry")
        lead.size_estimate = final_state.get("size_estimate")
        lead.tech_signals = final_state.get("tech_signals", [])
        lead.status = LeadStatus.SCORING
        lead.updated_at = datetime.now(timezone.utc)
        session.commit()

        # ── Milestone 4: scoring will be called here ──
        # ── Milestone 5: email generation will be called here ──

        lead.status = LeadStatus.AWAITING_REVIEW
        lead.updated_at = datetime.now(timezone.utc)
        session.commit()

        return {
            "status": "success",
            "lead_id": lead_id,
            "company_name": lead.company_name,
            "research_complete": True,
        }

    except Exception as exc:
        session.rollback()
        lead = session.query(Lead).filter(Lead.id == uuid.UUID(lead_id)).first()
        if lead:
            lead.status = LeadStatus.FAILED
            lead.error_message = str(exc)
            lead.retry_count = self.request.retries
            lead.updated_at = datetime.now(timezone.utc)
            session.commit()

        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))

    finally:
        session.close()


@celery_app.task(
    bind=True,
    name="tasks.finalize_pipeline_run",
)
def finalize_pipeline_run_task(self, pipeline_run_id: str) -> dict:
    """
    Called after all leads in a run are processed.
    Updates the PipelineRun status to COMPLETED.
    """
    session = get_sync_session()
    try:
        run = session.query(PipelineRun).filter(
            PipelineRun.id == uuid.UUID(pipeline_run_id)
        ).first()

        if not run:
            return {"status": "error", "message": "Pipeline run not found"}

        # Count final statuses
        leads = session.query(Lead).filter(
            Lead.pipeline_run_id == uuid.UUID(pipeline_run_id)
        ).all()

        processed = sum(
            1 for l in leads
            if l.status not in (LeadStatus.QUEUED, LeadStatus.RESEARCHING)
        )
        failed = sum(1 for l in leads if l.status == LeadStatus.FAILED)

        run.status = RunStatus.COMPLETED
        run.processed_leads = processed
        run.failed_leads = failed
        run.completed_at = datetime.now(timezone.utc)
        session.commit()

        logger.info(
            f"Pipeline run {pipeline_run_id} completed: "
            f"{processed} processed, {failed} failed"
        )

        return {
            "status": "completed",
            "pipeline_run_id": pipeline_run_id,
            "processed": processed,
            "failed": failed,
        }

    finally:
        session.close()
        