import csv
import io
import re
from backend.app.schemas.lead_input import ParsedLead, ParseResult
from backend.app.core.url_utils import (
    extract_domain,
    extract_linkedin_url,
    extract_company_name_from_domain,
    looks_like_url,
)


def parse_single_line(line: str) -> ParsedLead | None:
    """
    Parse one line of text into a ParsedLead.

    Handles these formats:
    - "Linear"
    - "https://linear.app"
    - "Linear, linear.app"
    - "Linear | linear.app"
    - "https://linkedin.com/company/linear"
    """
    line = line.strip()
    if not line:
        return None

    raw_input = line
    company_name: str | None = None
    domain: str | None = None
    linkedin_url: str | None = None
    confidence: float = 1.0

    # Check for LinkedIn URL first — it's unambiguous
    linkedin_url = extract_linkedin_url(line)
    if linkedin_url:
        # Extract slug as company name fallback
        slug = linkedin_url.split("/company/")[-1]
        company_name = slug.replace("-", " ").title()
        confidence = 0.8  # name from slug is a guess
        return ParsedLead(
            raw_input=raw_input,
            company_name=company_name,
            domain=domain,
            linkedin_url=linkedin_url,
            parse_confidence=confidence,
        )

    # Check for separator — "Company, domain.com" or "Company | domain.com"
    separator_match = re.split(r"[,|]\s*", line, maxsplit=1)
    if len(separator_match) == 2:
        left, right = separator_match[0].strip(), separator_match[1].strip()

        if looks_like_url(right):
            company_name = left
            domain = extract_domain(right)
        elif looks_like_url(left):
            domain = extract_domain(left)
            company_name = right
        else:
            # Neither looks like a URL — treat first part as name
            company_name = left
            confidence = 0.7

        if not company_name and domain:
            company_name = extract_company_name_from_domain(domain)
            confidence = 0.75

        return ParsedLead(
            raw_input=raw_input,
            company_name=company_name or left,
            domain=domain,
            linkedin_url=linkedin_url,
            parse_confidence=confidence,
        )

    # Plain URL with no separator
    if looks_like_url(line):
        domain = extract_domain(line)
        if domain:
            company_name = extract_company_name_from_domain(domain)
            confidence = 0.85
        else:
            company_name = line
            confidence = 0.5
        return ParsedLead(
            raw_input=raw_input,
            company_name=company_name,
            domain=domain,
            linkedin_url=None,
            parse_confidence=confidence,
        )

    # Plain company name — no URL signals at all
    return ParsedLead(
        raw_input=raw_input,
        company_name=line,
        domain=None,
        linkedin_url=None,
        parse_confidence=1.0,
    )


def parse_text_input(text: str) -> list[ParsedLead]:
    """Parse a newline-separated block of text."""
    lines = text.strip().splitlines()
    results = []
    for line in lines:
        parsed = parse_single_line(line)
        if parsed:
            results.append(parsed)
    return results


def parse_csv_input(content: bytes) -> list[ParsedLead]:
    """
    Parse a CSV file. Flexible column detection:
    - Looks for columns named: company, name, url, domain, linkedin
    - Falls back to treating first column as company name, second as URL
    """
    text = content.decode("utf-8-sig")  # handle BOM from Excel exports
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        return []

    # Normalize column names
    fieldnames = [f.strip().lower() for f in reader.fieldnames]

    def find_col(*candidates: str) -> str | None:
        for c in candidates:
            if c in fieldnames:
                return reader.fieldnames[fieldnames.index(c)]
        return None

    name_col = find_col("company", "company_name", "name")
    url_col = find_col("url", "website", "domain", "homepage")
    linkedin_col = find_col("linkedin", "linkedin_url")

    results = []
    for row in reader:
        # Build a synthetic line from available columns
        parts = []
        if name_col and row.get(name_col, "").strip():
            parts.append(row[name_col].strip())
        if url_col and row.get(url_col, "").strip():
            parts.append(row[url_col].strip())
        if linkedin_col and row.get(linkedin_col, "").strip():
            parts.append(row[linkedin_col].strip())

        if not parts:
            # Fall back to first two columns
            values = list(row.values())
            parts = [v.strip() for v in values[:2] if v.strip()]

        if parts:
            line = ", ".join(parts)
            parsed = parse_single_line(line)
            if parsed:
                results.append(parsed)

    return results


def parse_json_input(data: list[dict]) -> list[ParsedLead]:
    """
    Parse a JSON array of objects.
    Accepts any reasonable key names.
    """
    results = []
    for item in data:
        keys = {k.lower().strip(): v for k, v in item.items()}

        company = (
            keys.get("company")
            or keys.get("company_name")
            or keys.get("name")
            or ""
        ).strip()

        url = (
            keys.get("url")
            or keys.get("website")
            or keys.get("domain")
            or ""
        ).strip()

        linkedin = (
            keys.get("linkedin")
            or keys.get("linkedin_url")
            or ""
        ).strip()

        # Build synthetic line and reuse single-line parser
        parts = [p for p in [company, url or linkedin] if p]
        if parts:
            line = ", ".join(parts)
            parsed = parse_single_line(line)
            if parsed:
                results.append(parsed)

    return results


def deduplicate(leads: list[ParsedLead]) -> tuple[list[ParsedLead], int]:
    """
    Remove duplicate leads within a batch.
    Deduplication key: normalized domain (if available) or lowercased company name.
    """
    seen: set[str] = set()
    unique: list[ParsedLead] = []
    removed = 0

    for lead in leads:
        key = (lead.domain or lead.company_name.lower().strip())
        if key in seen:
            removed += 1
        else:
            seen.add(key)
            unique.append(lead)

    return unique, removed


def run_parser(
    *,
    text: str | None = None,
    csv_content: bytes | None = None,
    json_data: list[dict] | None = None,
) -> ParseResult:
    """
    Main entry point. Accepts any one input format,
    parses it, deduplicates, and returns a ParseResult.
    """
    if text is not None:
        raw_leads = parse_text_input(text)
    elif csv_content is not None:
        raw_leads = parse_csv_input(csv_content)
    elif json_data is not None:
        raw_leads = parse_json_input(json_data)
    else:
        raise ValueError("Must provide one of: text, csv_content, json_data")

    total_submitted = len(raw_leads)
    unique_leads, duplicates_removed = deduplicate(raw_leads)

    return ParseResult(
        parsed=unique_leads,
        duplicates_removed=duplicates_removed,
        invalid_removed=0,
        total_submitted=total_submitted,
    )


