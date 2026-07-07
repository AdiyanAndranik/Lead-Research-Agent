import httpx
from langchain_core.tools import tool


# Common tech stack signals we look for in page source
TECH_SIGNALS = {
    "React": ["react", "_next", "__NEXT_DATA__"],
    "Next.js": ["__NEXT_DATA__", "_next/static"],
    "Vue.js": ["vue.js", "__vue__"],
    "Angular": ["ng-version", "angular"],
    "Tailwind": ["tailwind"],
    "Vercel": ["vercel", "_vercel"],
    "Stripe": ["stripe.com/v3", "js.stripe.com"],
    "Segment": ["segment.com/analytics", "cdn.segment"],
    "Intercom": ["intercom", "widget.intercom.io"],
    "HubSpot": ["hubspot", "hs-scripts"],
    "Salesforce": ["salesforce", "pardot"],
    "Zendesk": ["zendesk", "zdassets"],
    "AWS": ["amazonaws.com", "cloudfront.net"],
    "Google Analytics": ["gtag", "google-analytics", "UA-"],
    "Mixpanel": ["mixpanel"],
    "Amplitude": ["amplitude"],
    "Sentry": ["sentry.io", "browser.sentry-cdn"],
    "Datadog": ["datadog"],
    "Kubernetes": ["kubernetes"],
    "GraphQL": ["graphql"],
}


@tool
async def detect_tech_stack(domain: str) -> str:
    """
    Detect the technology stack used by a company's website.
    Looks for common framework and tool signals in page source.
    Input: domain name like 'linear.app' or 'stripe.com'
    """
    url = f"https://{domain}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        async with httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            timeout=10.0,
        ) as client:
            response = await client.get(url)
            source = response.text.lower()

        detected = []
        for tech, signals in TECH_SIGNALS.items():
            if any(signal.lower() in source for signal in signals):
                detected.append(tech)

        if not detected:
            return f"No specific tech stack signals detected for {domain}."

        return (
            f"Detected tech stack for {domain}:\n"
            + ", ".join(detected)
            + f"\n\nThis suggests: "
            + _interpret_stack(detected)
        )

    except Exception as e:
        return f"Tech detection failed for {domain}: {str(e)}"


def _interpret_stack(techs: list[str]) -> str:
    """Generate a human-readable interpretation of the detected stack."""
    signals = []

    if any(t in techs for t in ["React", "Next.js", "Vue.js", "Angular"]):
        signals.append("modern JavaScript frontend")
    if any(t in techs for t in ["Segment", "Mixpanel", "Amplitude"]):
        signals.append("data-mature team with analytics infrastructure")
    if any(t in techs for t in ["Intercom", "Zendesk"]):
        signals.append("established customer support tooling")
    if any(t in techs for t in ["HubSpot", "Salesforce"]):
        signals.append("sales/marketing automation in place")
    if "Stripe" in techs:
        signals.append("payment processing — likely a SaaS product")
    if any(t in techs for t in ["Sentry", "Datadog"]):
        signals.append("engineering team that cares about observability")
    if "Vercel" in techs:
        signals.append("likely a startup using modern deployment infrastructure")

    return "; ".join(signals) if signals else "general web technology stack"
