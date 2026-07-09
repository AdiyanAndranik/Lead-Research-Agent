import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _extract_text(html: str, max_chars: int = 4000) -> str:
    """Extract clean readable text from HTML."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "meta"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())
    return text[:max_chars]


async def _fetch_with_httpx(url: str, timeout: float = 10.0) -> str:
    """Fast httpx fetch — works for server-rendered sites."""
    async with httpx.AsyncClient(
        headers=SCRAPE_HEADERS,
        follow_redirects=True,
        timeout=timeout,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def _fetch_with_playwright(url: str, timeout: float = 15.0) -> str:
    """
    Playwright fetch — handles JS-rendered sites (Next.js, React SPAs).
    Falls back to httpx result if Playwright fails.
    """
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            page = await browser.new_page(
                user_agent=SCRAPE_HEADERS["User-Agent"]
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
            # Wait for main content to render
            await page.wait_for_timeout(2000)
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        logger.warning(f"Playwright failed for {url}: {e} — falling back to httpx")
        raise


async def _smart_fetch(url: str) -> str:
    """
    Smart fetch strategy:
    1. Try httpx first (fast, lightweight)
    2. If content is too short (likely JS-rendered), try Playwright
    3. If Playwright fails, use httpx result anyway
    """
    # Step 1: httpx
    try:
        html = await _fetch_with_httpx(url)
        text = _extract_text(html)

        # If we got meaningful content, use it
        if len(text) > 500:
            logger.info(f"httpx scrape successful for {url} ({len(text)} chars)")
            return text

        # Content too short — likely JS-rendered, try Playwright
        logger.info(f"httpx got thin content ({len(text)} chars), trying Playwright")
        httpx_text = text  # save as fallback

    except Exception as e:
        logger.warning(f"httpx failed for {url}: {e}")
        httpx_text = ""

    # Step 2: Playwright
    try:
        html = await _fetch_with_playwright(url)
        text = _extract_text(html)
        if len(text) > 200:
            logger.info(f"Playwright scrape successful for {url} ({len(text)} chars)")
            return text
    except Exception as e:
        logger.warning(f"Playwright also failed for {url}: {e}")

    # Step 3: return whatever httpx got, even if thin
    return httpx_text or f"Could not fetch content from {url}"


@tool
async def scrape_homepage(domain: str) -> str:
    """
    Scrape the homepage of a company website.
    Uses Playwright for JS-rendered sites with httpx fallback.
    Input: domain name like 'linear.app' or 'stripe.com'
    """
    url = f"https://{domain}"
    try:
        content = await _smart_fetch(url)
        return f"Homepage content for {domain}:\n{content}"
    except Exception as e:
        return f"Could not scrape homepage for {domain}: {str(e)}"


@tool
async def scrape_about_page(domain: str) -> str:
    """
    Scrape the about/company page of a website.
    Tries multiple common about page paths.
    Input: domain name like 'linear.app' or 'stripe.com'
    """
    about_paths = ["/about", "/about-us", "/company", "/our-story", "/team"]

    for path in about_paths:
        url = f"https://{domain}{path}"
        try:
            content = await _smart_fetch(url)
            if len(content) > 300:
                return f"About page content for {domain}{path}:\n{content}"
        except Exception:
            continue

    return f"No about page found for {domain}"