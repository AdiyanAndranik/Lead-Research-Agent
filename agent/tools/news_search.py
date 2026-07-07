import httpx
from langchain_core.tools import tool
from backend.app.core.config import settings


@tool
async def search_company_news(company_name: str) -> str:
    """
    Search for recent news about a company using Serper API.
    Returns recent press coverage, funding announcements, and product launches.
    Input: company name like 'Linear' or 'Stripe'
    """
    if not settings.serper_api_key:
        return f"News search unavailable — no Serper API key configured."

    query = f"{company_name} funding OR product launch OR announcement 2024 OR 2025"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": settings.serper_api_key,
                    "Content-Type": "application/json",
                },
                json={"q": query, "num": 5, "gl": "us", "hl": "en"},
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic", [])[:5]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            date = item.get("date", "")
            results.append(f"- {title} ({date}): {snippet}")

        if not results:
            return f"No recent news found for {company_name}."

        return f"Recent news for {company_name}:\n" + "\n".join(results)

    except Exception as e:
        return f"News search failed for {company_name}: {str(e)}"


@tool
async def search_company_funding(company_name: str) -> str:
    """
    Search specifically for funding and investment information about a company.
    Input: company name like 'Linear' or 'Stripe'
    """
    if not settings.serper_api_key:
        return f"Search unavailable — no Serper API key configured."

    query = f"{company_name} series funding raised investors valuation"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": settings.serper_api_key,
                    "Content-Type": "application/json",
                },
                json={"q": query, "num": 3, "gl": "us", "hl": "en"},
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic", [])[:3]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            results.append(f"- {title}: {snippet}")

        if not results:
            return f"No funding information found for {company_name}."

        return f"Funding info for {company_name}:\n" + "\n".join(results)

    except Exception as e:
        return f"Funding search failed for {company_name}: {str(e)}"
    



    