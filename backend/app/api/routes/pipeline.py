import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.pipeline_run import PipelineRun
from backend.app.models.lead import Lead
from backend.app.schemas.pipeline import PipelineStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.get(
    "/{run_id}",
    response_model=PipelineStatusResponse,
    summary="Get pipeline run status",
    description="Returns the current status and progress of a pipeline run.",
)
async def get_pipeline_status(
    run_id: str,
    session: AsyncSession = Depends(get_db),
):
    import uuid
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pipeline run ID format.")

    result = await session.execute(
        select(PipelineRun).where(PipelineRun.id == run_uuid)
    )
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline run {run_id} not found.",
        )

    return PipelineStatusResponse(
        pipeline_run_id=str(run.id),
        status=run.status.value,
        total_leads=run.total_leads,
        processed_leads=run.processed_leads,
        failed_leads=run.failed_leads,
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


@router.get(
    "/{run_id}/leads",
    summary="Get all leads for a pipeline run",
    description="Returns all leads and their current processing status.",
)
async def get_pipeline_leads(
    run_id: str,
    session: AsyncSession = Depends(get_db),
):
    import uuid
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pipeline run ID format.")

    result = await session.execute(
        select(Lead).where(Lead.pipeline_run_id == run_uuid)
    )
    leads = result.scalars().all()

    return {
        "pipeline_run_id": run_id,
        "total": len(leads),
        "leads": [
            {
                "id": str(lead.id),
                "company_name": lead.company_name,
                "domain": lead.domain,
                "status": lead.status.value,
                "created_at": lead.created_at.isoformat(),
            }
            for lead in leads
        ],
    }
