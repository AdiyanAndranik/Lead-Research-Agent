import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential


SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _extract_text(html: str, max_chars: int = 3000) -> str:
    """Extract clean text from HTML, truncated to max_chars."""
    soup = BeautifulSoup(html, "lxml")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = " ".join(text.split())
    return text[:max_chars]


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=6),
    reraise=True,
)
async def _fetch_url(url: str, timeout: float = 10.0) -> str:
    """Fetch a URL and return cleaned text content."""
    async with httpx.AsyncClient(
        headers=SCRAPE_HEADERS,
        follow_redirects=True,
        timeout=timeout,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return _extract_text(response.text)


@tool
async def scrape_homepage(domain: str) -> str:
    """
    Scrape the homepage of a company website.
    Returns cleaned text content from the page.
    Input: domain name like 'linear.app' or 'stripe.com'
    """
    url = f"https://{domain}"
    try:
        content = await _fetch_url(url)
        return f"Homepage content for {domain}:\n{content}"
    except Exception as e:
        return f"Could not scrape homepage for {domain}: {str(e)}"


@tool
async def scrape_about_page(domain: str) -> str:
    """
    Scrape the about page of a company website.
    Tries common about page URLs.
    Input: domain name like 'linear.app' or 'stripe.com'
    """
    about_paths = ["/about", "/about-us", "/company", "/our-story"]

    for path in about_paths:
        url = f"https://{domain}{path}"
        try:
            content = await _fetch_url(url)
            if len(content) > 200:  # meaningful content found
                return f"About page content for {domain}{path}:\n{content}"
        except Exception:
            continue

    return f"No about page found for {domain}"

