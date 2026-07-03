import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.lead import Lead, LeadStatus
from backend.app.models.pipeline_run import PipelineRun, RunStatus
from backend.app.schemas.lead_input import ParsedLead
from backend.app.schemas.validation import BatchValidationResult

logger = logging.getLogger(__name__)


def create_pipeline_run(
    session: Session,
    *,
    total_leads: int,
    min_score_threshold: int = 6,
    email_tone: str = "conversational",
    email_angle: str = "pain",
    target_company_size: str = "any",
    custom_scoring_instructions: str | None = None,
) -> PipelineRun:
    """Create and persist a new PipelineRun record."""
    run = PipelineRun(
        id=uuid.uuid4(),
        status=RunStatus.RUNNING,
        total_leads=total_leads,
        min_score_threshold=min_score_threshold,
        email_tone=email_tone,
        email_angle=email_angle,
        target_company_size=target_company_size,
        custom_scoring_instructions=custom_scoring_instructions,
        created_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    logger.info(f"Created pipeline run {run.id} with {total_leads} leads")
    return run


def save_leads_to_db(
    session: Session,
    pipeline_run_id: uuid.UUID,
    leads: list[ParsedLead],
) -> list[Lead]:
    """Persist validated leads to the database."""
    db_leads = []
    for parsed in leads:
        lead = Lead(
            id=uuid.uuid4(),
            pipeline_run_id=pipeline_run_id,
            raw_input=parsed.raw_input,
            company_name=parsed.company_name,
            domain=parsed.domain,
            linkedin_url=parsed.linkedin_url,
            status=LeadStatus.QUEUED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(lead)
        db_leads.append(lead)

    session.commit()
    logger.info(f"Saved {len(db_leads)} leads for run {pipeline_run_id}")
    return db_leads


def dispatch_lead_tasks(
    pipeline_run_id: str,
    lead_ids: list[str],
) -> list[str]:
    """
    Dispatch one Celery task per lead, then chain a finalize task.
    Returns list of Celery task IDs for tracking.
    """
    from celery import chord
    from backend.app.tasks.lead_tasks import (
        process_lead_task,
        finalize_pipeline_run_task,
    )

    # Create a chord: run all lead tasks in parallel,
    # then call finalize when ALL are done
    lead_signatures = [
        process_lead_task.s(lead_id, pipeline_run_id)
        for lead_id in lead_ids
    ]

    pipeline_chord = chord(lead_signatures)(
        finalize_pipeline_run_task.s(pipeline_run_id)
    )

    task_ids = [sig.id for sig in lead_signatures]
    logger.info(
        f"Dispatched {len(task_ids)} tasks for pipeline run {pipeline_run_id}"
    )
    return task_ids


def launch_pipeline(
    session: Session,
    validation_result: BatchValidationResult,
    *,
    min_score_threshold: int = 6,
    email_tone: str = "conversational",
    email_angle: str = "pain",
    target_company_size: str = "any",
    custom_scoring_instructions: str | None = None,
) -> dict:
    """
    Full pipeline launch:
    1. Create PipelineRun record
    2. Save leads to DB
    3. Dispatch Celery tasks
    Returns a summary dict for the API response.
    """
    accepted_leads = [r.lead for r in validation_result.accepted]

    if not accepted_leads:
        return {
            "pipeline_run_id": None,
            "status": "no_valid_leads",
            "accepted": 0,
            "rejected": validation_result.total_rejected,
            "task_ids": [],
        }

    # 1. Create run
    run = create_pipeline_run(
        session,
        total_leads=len(accepted_leads),
        min_score_threshold=min_score_threshold,
        email_tone=email_tone,
        email_angle=email_angle,
        target_company_size=target_company_size,
        custom_scoring_instructions=custom_scoring_instructions,
    )

    # 2. Save leads
    db_leads = save_leads_to_db(session, run.id, accepted_leads)

    # 3. Dispatch tasks
    lead_ids = [str(lead.id) for lead in db_leads]
    task_ids = dispatch_lead_tasks(str(run.id), lead_ids)

    return {
        "pipeline_run_id": str(run.id),
        "status": "running",
        "accepted": len(accepted_leads),
        "rejected": validation_result.total_rejected,
        "duplicate_in_batch": validation_result.duplicate_in_batch,
        "duplicate_in_db": validation_result.duplicate_in_db,
        "task_ids": task_ids,
    }
