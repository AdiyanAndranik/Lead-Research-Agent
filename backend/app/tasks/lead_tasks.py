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


settings.configure_langsmith()

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

        from agent.validators import validate_research_result
        validation = validate_research_result(final_state)

        if not validation.is_valid:
            logger.warning(
                f"Research quality low for {lead.company_name} "
                f"(score: {validation.quality_score:.2f}): {validation.issues}"
            )

        # Persist research results regardless of quality
        # (low quality leads will get lower scores later)
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
            scrape_duration_seconds=validation.quality_score,  # reuse field as quality proxy
            created_at=datetime.now(timezone.utc),
        )
        session.add(research)

        # Update lead
        size_estimate = final_state.get("size_estimate") or ""
        lead.industry = (final_state.get("industry") or "")[:254]
        lead.size_estimate = size_estimate[:99] if size_estimate else None
        lead.tech_signals = final_state.get("tech_signals", [])
        lead.status = LeadStatus.SCORING
        lead.updated_at = datetime.now(timezone.utc)
        session.commit()

        # ── Milestone 4: Lead scoring ──
        from agent.scoring import score_lead
        from backend.app.models.score_result import ScoreResult

        # Get pipeline run config for threshold
        pipeline_run = session.query(PipelineRun).filter(
            PipelineRun.id == uuid.UUID(pipeline_run_id)
        ).first()
        min_threshold = pipeline_run.min_score_threshold if pipeline_run else 6

        # Build research dict for scorer
        research_data = {
            "company_description": research.company_description,
            "product_offering": research.product_offering,
            "industry": lead.industry,
            "size_estimate": lead.size_estimate,
            "pain_points": research.pain_points or [],
            "funding_signals": research.funding_signals,
            "tech_signals": lead.tech_signals or [],
        }

        score_output = asyncio.run(score_lead(
            company_name=lead.company_name,
            research=research_data,
            min_score_threshold=min_threshold,
        ))

        # Persist score result
        score_record = ScoreResult(
            id=uuid.uuid4(),
            lead_id=uuid.UUID(lead_id),
            overall_score=score_output.overall_score,
            icp_fit_score=score_output.icp_fit.score,
            pain_alignment_score=score_output.pain_alignment.score,
            tech_maturity_score=score_output.tech_maturity.score,
            timing_score=score_output.timing.score,
            budget_signal_score=score_output.budget_signal.score,
            reasoning=score_output.overall_reasoning,
            dimension_reasoning={
                "icp_fit": score_output.icp_fit.reasoning,
                "pain_alignment": score_output.pain_alignment.reasoning,
                "tech_maturity": score_output.tech_maturity.reasoning,
                "timing": score_output.timing.reasoning,
                "budget_signal": score_output.budget_signal.reasoning,
            },
            recommended_action=score_output.recommended_action,
            confidence=score_output.confidence,
            passed_threshold=score_output.passed_threshold,
            created_at=datetime.now(timezone.utc),
        )
        session.add(score_record)

        logger.info(
            f"Scored {lead.company_name}: {score_output.overall_score}/10 "
            f"({'PASS' if score_output.passed_threshold else 'FAIL'}) "
            f"— {score_output.recommended_action}"
        )

        # Update lead status based on score
        if score_output.passed_threshold:
            lead.status = LeadStatus.GENERATING_EMAIL
        else:
            lead.status = LeadStatus.SKIPPED

        lead.updated_at = datetime.now(timezone.utc)
        session.commit()

        # ── Milestone 5: Email generation ──
        if score_output.passed_threshold:
            from agent.email_generator import generate_emails
            from backend.app.models.email_draft import EmailDraft, EmailVariant, EmailStatus

            email_output = asyncio.run(generate_emails(
                company_name=lead.company_name,
                research=research_data,
                score_reasoning=score_output.overall_reasoning,
                tone=pipeline_run.email_tone if pipeline_run else "conversational",
                angle=pipeline_run.email_angle if pipeline_run else "pain",
            ))

            variant_map = {
                "pain_first": EmailVariant.PAIN_FIRST,
                "opportunity_first": EmailVariant.OPPORTUNITY_FIRST,
                "social_proof_first": EmailVariant.SOCIAL_PROOF_FIRST,
            }

            for draft in email_output.drafts:
                is_primary = draft.variant == email_output.primary_variant
                email_record = EmailDraft(
                    id=uuid.uuid4(),
                    lead_id=uuid.UUID(lead_id),
                    variant=variant_map.get(draft.variant, EmailVariant.PAIN_FIRST),
                    is_primary=is_primary,
                    subject_line=draft.subject_line[:499],
                    body=draft.body,
                    status=EmailStatus.DRAFT,
                    word_count=draft.word_count,
                    personalization_signals_count=len(draft.personalization_signals),
                    quality_flags=email_output.quality_flags,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(email_record)

            session.commit()
            logger.info(
                f"Generated {len(email_output.drafts)} email variants "
                f"for {lead.company_name}"
            )

        if score_output.passed_threshold:
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
        