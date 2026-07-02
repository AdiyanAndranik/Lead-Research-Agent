import pytest
from backend.app.schemas.lead_input import ParsedLead
from backend.app.schemas.validation import ValidationStatus
from backend.app.services.lead_validator import (
    deduplicate_batch,
    validate_lead_content,
    LeadValidationReport,
)


def make_lead(
    company: str,
    domain: str | None = None,
    confidence: float = 1.0,
) -> ParsedLead:
    return ParsedLead(
        raw_input=company,
        company_name=company,
        domain=domain,
        parse_confidence=confidence,
    )


# ── Content validation ────────────────────────────────────────────────

def test_valid_lead_passes():
    lead = make_lead("Linear", domain="linear.app")
    report = validate_lead_content(
        LeadValidationReport(lead=lead, status=ValidationStatus.VALID)
    )
    assert report.is_accepted is True
    assert report.errors == []


def test_short_name_rejected():
    lead = make_lead("A")
    report = validate_lead_content(
        LeadValidationReport(lead=lead, status=ValidationStatus.VALID)
    )
    assert report.is_accepted is False
    assert report.status == ValidationStatus.INVALID


def test_blacklisted_domain_rejected():
    lead = make_lead("Gmail", domain="gmail.com")
    report = validate_lead_content(
        LeadValidationReport(lead=lead, status=ValidationStatus.VALID)
    )
    assert report.is_accepted is False


def test_low_confidence_adds_warning():
    lead = make_lead("Linear", domain="linear.app", confidence=0.5)
    report = validate_lead_content(
        LeadValidationReport(lead=lead, status=ValidationStatus.VALID)
    )
    assert report.is_accepted is True
    assert any("confidence" in w for w in report.warnings)


def test_no_domain_adds_warning():
    lead = make_lead("Some Company")
    report = validate_lead_content(
        LeadValidationReport(lead=lead, status=ValidationStatus.VALID)
    )
    assert report.is_accepted is True
    assert any("domain" in w for w in report.warnings)


# ── Batch deduplication ───────────────────────────────────────────────

def test_no_duplicates_all_valid():
    leads = [
        make_lead("Linear", domain="linear.app"),
        make_lead("Stripe", domain="stripe.com"),
        make_lead("Notion", domain="notion.so"),
    ]
    reports = deduplicate_batch(leads)
    assert all(r.is_accepted for r in reports)


def test_duplicate_domain_caught():
    leads = [
        make_lead("Linear", domain="linear.app"),
        make_lead("Linear App", domain="linear.app"),  # same domain
    ]
    reports = deduplicate_batch(leads)
    accepted = [r for r in reports if r.is_accepted]
    rejected = [r for r in reports if not r.is_accepted]
    assert len(accepted) == 1
    assert len(rejected) == 1
    assert rejected[0].status == ValidationStatus.DUPLICATE_IN_BATCH


def test_duplicate_name_caught():
    leads = [
        make_lead("Linear"),
        make_lead("linear"),  # same name, different case
    ]
    reports = deduplicate_batch(leads)
    rejected = [r for r in reports if not r.is_accepted]
    assert len(rejected) == 1


def test_first_occurrence_wins():
    leads = [
        make_lead("Linear", domain="linear.app"),
        make_lead("Linear", domain="linear.app"),
    ]
    reports = deduplicate_batch(leads)
    accepted = [r for r in reports if r.is_accepted]
    assert accepted[0].lead.company_name == "Linear"