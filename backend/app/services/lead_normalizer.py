from backend.app.schemas.lead_input import ParsedLead
from backend.app.core.url_utils import (
    normalize_domain,
    is_blacklisted,
    is_domain_reachable,
    extract_company_name_from_domain,
)


class NormalizationResult:
    def __init__(self, lead: ParsedLead, warnings: list[str]):
        self.lead = lead
        self.warnings = warnings
        self.is_valid = len([w for w in warnings if w.startswith("ERROR")]) == 0


def normalize_lead(lead: ParsedLead, validate_dns: bool = False) -> NormalizationResult:
    """
    Run a ParsedLead through normalization and optional validation.

    Steps:
    1. Normalize domain casing and format
    2. Check domain is not blacklisted
    3. Optionally check DNS resolution
    4. Clean up company name
    """
    warnings: list[str] = []
    updated = lead.model_copy()

    # Step 1: normalize domain
    if updated.domain:
        updated = updated.model_copy(
            update={"domain": normalize_domain(updated.domain)}
        )

    # Step 2: blacklist check
    if updated.domain and is_blacklisted(updated.domain):
        warnings.append(f"ERROR: domain {updated.domain} is a blacklisted platform")
        updated = updated.model_copy(update={"domain": None})

    # Step 3: DNS check (optional — slow, skip in tests)
    if validate_dns and updated.domain:
        if not is_domain_reachable(updated.domain):
            warnings.append(
                f"WARNING: domain {updated.domain} did not resolve in DNS"
            )

    # Step 4: clean company name
    company_name = updated.company_name.strip()

    # If name looks like a URL (user put URL in name field), extract domain
    if company_name.startswith(("http://", "https://")) or (
        "." in company_name and " " not in company_name
    ):
        from backend.app.core.url_utils import extract_domain
        extracted = extract_domain(company_name)
        if extracted and not updated.domain:
            updated = updated.model_copy(update={"domain": normalize_domain(extracted)})
        company_name = extract_company_name_from_domain(
            extracted or company_name.split(".")[0]
        )
        warnings.append(
            f"INFO: extracted company name '{company_name}' from URL in name field"
        )

    # Title-case the company name if it's all lowercase or all uppercase
    if company_name == company_name.lower() or company_name == company_name.upper():
        company_name = company_name.title()

    updated = updated.model_copy(update={"company_name": company_name})

    return NormalizationResult(lead=updated, warnings=warnings)


def normalize_batch(
    leads: list[ParsedLead],
    validate_dns: bool = False,
) -> tuple[list[ParsedLead], list[ParsedLead], dict[str, list[str]]]:
    """
    Normalize a batch of leads.

    Returns:
    - valid_leads: leads that passed normalization
    - invalid_leads: leads that failed (blacklisted, etc.)
    - warnings_map: company_name → list of warning strings
    """
    valid: list[ParsedLead] = []
    invalid: list[ParsedLead] = []
    warnings_map: dict[str, list[str]] = {}

    for lead in leads:
        result = normalize_lead(lead, validate_dns=validate_dns)
        if result.warnings:
            warnings_map[result.lead.company_name] = result.warnings
        if result.is_valid:
            valid.append(result.lead)
        else:
            invalid.append(result.lead)

    return valid, invalid, warnings_map


