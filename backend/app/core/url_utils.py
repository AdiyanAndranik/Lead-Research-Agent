import re
from urllib.parse import urlparse


LINKEDIN_COMPANY_PATTERN = re.compile(
    r"linkedin\.com/company/([a-zA-Z0-9\-_%]+)"
)

# Common prefixes that aren't real company names
NOISE_PREFIXES = {"the", "a", "an"}

# TLDs we recognize as domain signals when found in plain text
COMMON_TLDS = {".com", ".io", ".ai", ".co", ".app", ".dev", ".net", ".org"}


def extract_domain(raw: str) -> str | None:
    """
    Extract the root domain from any input:
    - https://linear.app/changelog  → linear.app
    - linear.app                    → linear.app
    - www.linear.app                → linear.app
    - Linear                        → None
    """
    raw = raw.strip()

    # If it looks like a URL, parse it properly
    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        hostname = parsed.hostname or ""
        return _strip_www(hostname) or None

    # If it contains a dot and no spaces, treat as bare domain
    if "." in raw and " " not in raw:
        return _strip_www(raw.split("/")[0]) or None

    # Check if it ends with a known TLD (e.g. "linear.app")
    for tld in COMMON_TLDS:
        if raw.lower().endswith(tld):
            return _strip_www(raw) or None

    return None


def extract_linkedin_url(raw: str) -> str | None:
    """
    Extract and normalize a LinkedIn company URL.
    - https://linkedin.com/company/linear/  → https://linkedin.com/company/linear
    - linkedin.com/company/linear           → https://linkedin.com/company/linear
    """
    match = LINKEDIN_COMPANY_PATTERN.search(raw)
    if match:
        slug = match.group(1).rstrip("/")
        return f"https://www.linkedin.com/company/{slug}"
    return None


def extract_company_name_from_domain(domain: str) -> str:
    """
    Make a best-guess company name from a domain.
    - linear.app   → Linear
    - stripe.com   → Stripe
    - notion.so    → Notion
    """
    # Remove TLD
    base = domain.split(".")[0]
    # Remove hyphens, capitalize
    name = base.replace("-", " ").replace("_", " ").title()
    return name


def _strip_www(domain: str) -> str:
    if domain.startswith("www."):
        return domain[4:]
    return domain


def looks_like_url(text: str) -> bool:
    return (
        text.startswith(("http://", "https://"))
        or ("." in text and " " not in text)
    )



