import re
import socket
from urllib.parse import urlparse


LINKEDIN_COMPANY_PATTERN = re.compile(
    r"linkedin\.com/company/([a-zA-Z0-9\-_%]+)"
)

COMMON_TLDS = {".com", ".io", ".ai", ".co", ".app", ".dev", ".net", ".org", ".so", ".xyz"}

# Domains that are not companies — filter these out
BLACKLISTED_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "google.com", "facebook.com", "twitter.com", "instagram.com",
    "youtube.com", "wikipedia.org", "reddit.com", "github.com",
}


def normalize_url(raw: str) -> str:
    """
    Ensure a URL has a scheme so urlparse works correctly.
    - linear.app        → https://linear.app
    - http://linear.app → http://linear.app (unchanged)
    """
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        return "https://" + raw
    return raw


def extract_domain(raw: str) -> str | None:
    """
    Extract clean root domain from any input.

    Examples:
    - https://linear.app/changelog    → linear.app
    - https://www.stripe.com          → stripe.com
    - linear.app                      → linear.app
    - www.notion.so/product           → notion.so
    - Linear                          → None
    """
    raw = raw.strip()
    if not raw:
        return None

    # Normalize to have a scheme
    if not raw.startswith(("http://", "https://")):
        # Only treat as URL if it has a dot and no spaces
        if "." not in raw or " " in raw:
            return None
        raw = "https://" + raw

    try:
        parsed = urlparse(raw)
        hostname = parsed.hostname or ""
        if not hostname:
            return None
        domain = _strip_www(hostname).lower()
        return domain if domain else None
    except Exception:
        return None


def extract_linkedin_url(raw: str) -> str | None:
    """
    Extract and normalize a LinkedIn company URL.

    Examples:
    - https://www.linkedin.com/company/linear/  → https://www.linkedin.com/company/linear
    - linkedin.com/company/linear-app           → https://www.linkedin.com/company/linear-app
    """
    if not raw:
        return None
    match = LINKEDIN_COMPANY_PATTERN.search(raw)
    if match:
        slug = match.group(1).rstrip("/")
        return f"https://www.linkedin.com/company/{slug}"
    return None


def extract_company_name_from_domain(domain: str) -> str:
    """
    Best-guess company name from a domain.

    Examples:
    - linear.app        → Linear
    - stripe.com        → Stripe
    - retool.com        → Retool
    - my-company.io     → My Company
    """
    if not domain:
        return ""
    base = domain.split(".")[0]
    name = base.replace("-", " ").replace("_", " ").title()
    return name


def is_blacklisted(domain: str) -> bool:
    """Return True if this domain is a generic platform, not a company."""
    return domain.lower() in BLACKLISTED_DOMAINS


def is_domain_reachable(domain: str, timeout: float = 3.0) -> bool:
    """
    Check if a domain resolves in DNS.
    This is a lightweight check — just DNS lookup, no HTTP request.
    Returns True if reachable, False if not found or times out.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(domain, None)
        return True
    except (socket.gaierror, socket.timeout):
        return False


def normalize_domain(domain: str) -> str:
    """
    Final normalization pass on an already-extracted domain.
    Lowercases, strips trailing dots and slashes.

    - Linear.App  → linear.app
    - stripe.com/ → stripe.com
    """
    return domain.lower().strip().rstrip("./")


def looks_like_url(text: str) -> bool:
    """Return True if text looks like it contains a URL or domain."""
    text = text.strip()
    return (
        text.startswith(("http://", "https://"))
        or ("." in text and " " not in text and len(text) > 4)
    )


def build_homepage_url(domain: str) -> str:
    """Build a clean homepage URL from a domain."""
    domain = normalize_domain(domain)
    return f"https://{domain}"


def _strip_www(domain: str) -> str:
    if domain.startswith("www."):
        return domain[4:]
    return domain

