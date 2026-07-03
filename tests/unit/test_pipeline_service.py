import uuid
from unittest.mock import MagicMock, patch
from backend.app.schemas.lead_input import ParsedLead
from backend.app.schemas.validation import (
    BatchValidationResult,
    LeadValidationReport,
    ValidationStatus,
)
from backend.app.services.pipeline_service import (
    create_pipeline_run,
    save_leads_to_db,
)
from backend.app.models.pipeline_run import RunStatus
from backend.app.models.lead import LeadStatus


def make_parsed_lead(company: str, domain: str | None = None) -> ParsedLead:
    return ParsedLead(
        raw_input=company,
        company_name=company,
        domain=domain,
    )


def make_mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


def test_create_pipeline_run():
    session = make_mock_session()

    def refresh_side_effect(obj):
        obj.id = uuid.uuid4()

    session.refresh.side_effect = refresh_side_effect

    run = create_pipeline_run(session, total_leads=5)

    assert session.add.called
    assert session.commit.called
    assert run.status == RunStatus.RUNNING
    assert run.total_leads == 5


def test_create_pipeline_run_custom_config():
    session = make_mock_session()
    session.refresh.side_effect = lambda obj: setattr(obj, "id", uuid.uuid4())

    run = create_pipeline_run(
        session,
        total_leads=3,
        min_score_threshold=8,
        email_tone="formal",
        email_angle="opportunity",
    )

    assert run.min_score_threshold == 8
    assert run.email_tone == "formal"
    assert run.email_angle == "opportunity"


def test_save_leads_to_db():
    session = make_mock_session()
    run_id = uuid.uuid4()

    leads = [
        make_parsed_lead("Linear", "linear.app"),
        make_parsed_lead("Stripe", "stripe.com"),
    ]

    db_leads = save_leads_to_db(session, run_id, leads)

    assert len(db_leads) == 2
    assert session.add.call_count == 2
    assert session.commit.called

    for db_lead in db_leads:
        assert db_lead.pipeline_run_id == run_id
        assert db_lead.status == LeadStatus.QUEUED


def test_save_leads_preserves_domain():
    session = make_mock_session()
    run_id = uuid.uuid4()

    leads = [make_parsed_lead("Linear", "linear.app")]
    db_leads = save_leads_to_db(session, run_id, leads)

    assert db_leads[0].domain == "linear.app"
    assert db_leads[0].company_name == "Linear"