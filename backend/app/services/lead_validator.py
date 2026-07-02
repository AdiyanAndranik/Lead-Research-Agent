from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.lead import Lead
from backend.app.schemas.lead_input import ParsedLead
from backend.app.schemas.validation import (
    BatchValidationResult,
    LeadValidationReport,
    ValidationStatus,
)
from backend.app.core.url_utils import is_blacklisted, normalize_domain


def _dedup_key(lead: ParsedLead) -> str:
    """
    Canonical key for deduplication.
    Prefer domain over company name — more reliable signal.
    """
    if lead.domain:
        return normalize_domain(lead.domain)
    return lead.company_name.lower().strip()


def deduplicate_batch(
    leads: list[ParsedLead],
) -> list[LeadValidationReport]:
    """
    Detect duplicates within a single batch.
    First occurrence wins — rest are marked DUPLICATE_IN_BATCH.
    """
    seen: dict[str, int] = {}  # key → index of first occurrence
    reports: list[LeadValidationReport] = []

    for lead in leads:
        key = _dedup_key(lead)
        if key in seen:
            reports.append(
                LeadValidationReport(
                    lead=lead,
                    status=ValidationStatus.DUPLICATE_IN_BATCH,
                    errors=[
                        f"Duplicate of '{leads[seen[key]].company_name}' in this batch"
                    ],
                )
            )
        else:
            seen[key] = leads.index(lead)
            reports.append(
                LeadValidationReport(
                    lead=lead,
                    status=ValidationStatus.VALID,
                )
            )

    return reports


async def check_duplicates_in_db(
    reports: list[LeadValidationReport],
    pipeline_run_id: str,
    session: AsyncSession,
) -> list[LeadValidationReport]:
    """
    For leads that passed batch dedup, check if they already
    exist in the DB from a previous pipeline run.
    """
    # Only check leads that are still valid
    valid_reports = [r for r in reports if r.is_accepted]
    if not valid_reports:
        return reports

    # Collect domains and names to check
    domains = [r.lead.domain for r in valid_reports if r.lead.domain]
    names = [r.lead.company_name.lower() for r in valid_reports]

    # Single query — check if any lead with matching domain or name exists
    stmt = select(Lead.domain, Lead.company_name).where(
        or_(
            Lead.domain.in_(domains),
            Lead.company_name.in_(names),
        )
    )
    result = await session.execute(stmt)
    existing_rows = result.fetchall()

    existing_domains = {row.domain for row in existing_rows if row.domain}
    existing_names = {row.company_name.lower() for row in existing_rows}

    updated: list[LeadValidationReport] = []
    for report in reports:
        if not report.is_accepted:
            updated.append(report)
            continue

        lead = report.lead
        is_db_dup = (
            (lead.domain and lead.domain in existing_domains)
            or lead.company_name.lower() in existing_names
        )

        if is_db_dup:
            updated.append(
                LeadValidationReport(
                    lead=lead,
                    status=ValidationStatus.DUPLICATE_IN_DB,
                    errors=["This company was already processed in a previous run"],
                )
            )
        else:
            updated.append(report)

    return updated


def validate_lead_content(
    report: LeadValidationReport,
) -> LeadValidationReport:
    """
    Content-level validation on a single lead.
    Checks: blacklist, minimum name length, obviously bad inputs.
    """
    errors = list(report.errors)
    warnings = list(report.warnings)

    lead = report.lead

    # Must have a company name of reasonable length
    if len(lead.company_name.strip()) < 2:
        errors.append("Company name is too short to be valid")

    # Check blacklisted domain
    if lead.domain and is_blacklisted(lead.domain):
        errors.append(f"Domain '{lead.domain}' is a blacklisted platform")

    # Warn on low parse confidence
    if lead.parse_confidence < 0.7:
        warnings.append(
            f"Low parse confidence ({lead.parse_confidence:.0%}) "
            "— please verify company name is correct"
        )

    # Warn if no domain and no linkedin
    if not lead.domain and not lead.linkedin_url:
        warnings.append(
            "No domain or LinkedIn URL found "
            "— research quality may be lower"
        )

    if errors:
        return LeadValidationReport(
            lead=lead,
            status=ValidationStatus.INVALID,
            errors=errors,
            warnings=warnings,
        )

    return LeadValidationReport(
        lead=lead,
        status=report.status,
        errors=errors,
        warnings=warnings,
    )


async def validate_batch(
    leads: list[ParsedLead],
    pipeline_run_id: str,
    session: AsyncSession,
    check_db: bool = True,
) -> BatchValidationResult:
    """
    Full validation pipeline for a batch of parsed leads.

    Steps:
    1. Content validation (blacklist, name length, confidence)
    2. Batch deduplication
    3. Database deduplication (optional — skip in unit tests)
    """
    total_submitted = len(leads)

    # Step 1: content validation on each lead
    content_reports = [
        validate_lead_content(
            LeadValidationReport(lead=lead, status=ValidationStatus.VALID)
        )
        for lead in leads
    ]

    # Step 2: batch dedup (only on content-valid leads)
    valid_content = [r.lead for r in content_reports if r.is_accepted]
    invalid_content = [r for r in content_reports if not r.is_accepted]

    dedup_reports = deduplicate_batch(valid_content)

    # Step 3: DB dedup
    if check_db:
        dedup_reports = await check_duplicates_in_db(
            dedup_reports, pipeline_run_id, session
        )

    all_reports = invalid_content + dedup_reports
    return BatchValidationResult.from_reports(all_reports, total_submitted)
