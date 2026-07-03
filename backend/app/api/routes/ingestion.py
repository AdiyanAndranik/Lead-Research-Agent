import logging
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.schemas.pipeline import (
    JSONIngestionRequest,
    PipelineConfig,
    PipelineLaunchResponse,
    TextIngestionRequest,
    ValidationSummary,
)
from backend.app.services.lead_parser import run_parser
from backend.app.services.lead_validator import validate_batch
from backend.app.services.pipeline_service import launch_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["Ingestion"])


def _build_response(launch_result: dict, validation_result) -> PipelineLaunchResponse:
    """Build a consistent API response from launch and validation results."""
    rejected_details = [r for r in validation_result.rejected]

    return PipelineLaunchResponse(
        pipeline_run_id=launch_result.get("pipeline_run_id"),
        status=launch_result["status"],
        validation=ValidationSummary(
            total_submitted=validation_result.total_submitted,
            total_accepted=validation_result.total_accepted,
            total_rejected=validation_result.total_rejected,
            duplicate_in_batch=validation_result.duplicate_in_batch,
            duplicate_in_db=validation_result.duplicate_in_db,
            invalid=validation_result.invalid,
            rejected_details=rejected_details,
        ),
        task_ids=launch_result.get("task_ids", []),
        message=(
            f"Pipeline started: {validation_result.total_accepted} leads queued, "
            f"{validation_result.total_rejected} rejected."
            if launch_result["status"] == "running"
            else "No valid leads found — pipeline not started."
        ),
    )


@router.post(
    "/text",
    response_model=PipelineLaunchResponse,
    summary="Submit leads as plain text",
    description="Submit a newline-separated list of companies. "
                "Accepts names, URLs, LinkedIn URLs, or any mix.",
)
async def ingest_text(
    request: TextIngestionRequest,
    session: AsyncSession = Depends(get_db),
):
    parse_result = run_parser(text=request.text)
    validation_result = await validate_batch(
        leads=parse_result.parsed,
        pipeline_run_id="new",
        session=session,
    )

    from sqlalchemy.orm import Session
    from backend.app.db.session import engine
    from sqlalchemy import create_engine as _ce
    from backend.app.core.config import settings

    sync_engine = _ce(settings.database_url_sync)
    SyncSession = __import__("sqlalchemy.orm", fromlist=["sessionmaker"]).sessionmaker(
        bind=sync_engine
    )
    sync_session = SyncSession()

    try:
        launch_result = launch_pipeline(
            sync_session,
            validation_result,
            **request.config.model_dump(),
        )
    finally:
        sync_session.close()
        sync_engine.dispose()

    return _build_response(launch_result, validation_result)


@router.post(
    "/csv",
    response_model=PipelineLaunchResponse,
    summary="Submit leads via CSV file upload",
    description="Upload a CSV file. Flexible column detection: "
                "company/name, url/website/domain, linkedin columns.",
)
async def ingest_csv(
    file: UploadFile = File(...),
    min_score_threshold: int = Form(default=6),
    email_tone: str = Form(default="conversational"),
    email_angle: str = Form(default="pain"),
    target_company_size: str = Form(default="any"),
    custom_scoring_instructions: str = Form(default=None),
    session: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are accepted. Please upload a .csv file.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    parse_result = run_parser(csv_content=content)
    validation_result = await validate_batch(
        leads=parse_result.parsed,
        pipeline_run_id="new",
        session=session,
    )

    config = PipelineConfig(
        min_score_threshold=min_score_threshold,
        email_tone=email_tone,
        email_angle=email_angle,
        target_company_size=target_company_size,
        custom_scoring_instructions=custom_scoring_instructions or None,
    )

    from backend.app.core.config import settings
    from sqlalchemy import create_engine as _ce
    from sqlalchemy.orm import sessionmaker as _sm

    sync_engine = _ce(settings.database_url_sync)
    sync_session = _sm(bind=sync_engine)()
    try:
        launch_result = launch_pipeline(
            sync_session, validation_result, **config.model_dump()
        )
    finally:
        sync_session.close()
        sync_engine.dispose()

    return _build_response(launch_result, validation_result)


@router.post(
    "/json",
    response_model=PipelineLaunchResponse,
    summary="Submit leads as JSON array",
    description="Submit a JSON array of lead objects. "
                "Accepts any of: company, name, url, website, linkedin fields.",
)
async def ingest_json(
    request: JSONIngestionRequest,
    session: AsyncSession = Depends(get_db),
):
    parse_result = run_parser(json_data=request.leads)
    validation_result = await validate_batch(
        leads=parse_result.parsed,
        pipeline_run_id="new",
        session=session,
    )

    from backend.app.core.config import settings
    from sqlalchemy import create_engine as _ce
    from sqlalchemy.orm import sessionmaker as _sm

    sync_engine = _ce(settings.database_url_sync)
    sync_session = _sm(bind=sync_engine)()
    try:
        launch_result = launch_pipeline(
            sync_session, validation_result, **request.config.model_dump()
        )
    finally:
        sync_session.close()
        sync_engine.dispose()

    return _build_response(launch_result, validation_result)
