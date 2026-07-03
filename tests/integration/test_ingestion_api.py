import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from backend.app.main import app


# Mock the DB session and pipeline launch so tests don't need a real DB
@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=[]))
    )))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_launch_result():
    return {
        "pipeline_run_id": "00000000-0000-0000-0000-000000000001",
        "status": "running",
        "accepted": 2,
        "rejected": 0,
        "duplicate_in_batch": 0,
        "duplicate_in_db": 0,
        "task_ids": ["task-1", "task-2"],
    }


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ingest_text_endpoint_validation(mock_session, mock_launch_result):
    with (
        patch("backend.app.api.routes.ingestion.validate_batch") as mock_validate,
        patch("backend.app.api.routes.ingestion.launch_pipeline") as mock_launch,
        patch("backend.app.db.session.get_db", return_value=mock_session),
    ):
        from backend.app.schemas.validation import BatchValidationResult
        from backend.app.schemas.lead_input import ParsedLead

        lead = ParsedLead(
            raw_input="Linear",
            company_name="Linear",
            domain="linear.app",
        )
        from backend.app.schemas.validation import LeadValidationReport, ValidationStatus
        mock_validate.return_value = BatchValidationResult(
            accepted=[LeadValidationReport(lead=lead, status=ValidationStatus.VALID)],
            rejected=[],
            total_submitted=1,
            total_accepted=1,
            total_rejected=0,
            duplicate_in_batch=0,
            duplicate_in_db=0,
            invalid=0,
        )
        mock_launch.return_value = mock_launch_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/ingest/text",
                json={"text": "Linear, linear.app"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["validation"]["total_submitted"] == 1


@pytest.mark.asyncio
async def test_ingest_empty_text_still_processes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/ingest/text",
            json={"text": "   "},
        )
    # Empty text returns no_valid_leads, not a 500
    assert response.status_code == 200
    data = response.json()
    assert data["validation"]["total_accepted"] == 0