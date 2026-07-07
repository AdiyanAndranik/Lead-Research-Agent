import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import ResearchState
from agent.llm import get_research_llm

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT = """You are analyzing research data about a company to produce a structured summary.

Based on the research conversation provided, extract and structure the following information.
Respond ONLY with a valid JSON object — no markdown, no backticks, no explanation.

Required JSON structure:
{
  "company_description": "2-3 sentence description of what the company does",
  "product_offering": "their main product or service in 1-2 sentences",
  "industry": "one short industry label e.g. DevTools, FinTech, HR Tech, E-commerce",
  "size_estimate": "estimated company size e.g. '10-50 employees' or 'Series A startup'",
  "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "funding_signals": "any funding or investment information found, or null",
  "tech_signals": ["technology 1", "technology 2"],
  "ai_automation_opportunity": "1-2 sentences on how AI/automation could help this company specifically"
}

If information is not available for a field, use null for strings or [] for arrays.
Do not invent information — only use what was found in the research."""


async def summarize_node(state: ResearchState) -> dict:
    """
    Summarize all research tool outputs into a structured ResearchSummary.
    This is the final node before the agent exits.
    """
    logger.info(f"Summarize node: {state.company_name}")

    llm = get_research_llm()

    # Build a summary of what was researched
    research_context = _build_research_context(state)

    messages = [
        SystemMessage(content=SUMMARIZE_PROMPT),
        HumanMessage(content=research_context),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    # Parse JSON response
    try:
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse summarizer response: {e}\nRaw: {raw}")
        data = {}

    return {
        "company_description": data.get("company_description"),
        "product_offering": data.get("product_offering"),
        "industry": data.get("industry"),
        "size_estimate": data.get("size_estimate"),
        "pain_points": data.get("pain_points", []),
        "funding_signals": data.get("funding_signals"),
        "tech_signals": data.get("tech_signals", []),
        "is_complete": True,
    }


def _build_research_context(state: ResearchState) -> str:
    """Build a text summary of all research gathered for the summarizer."""
    parts = [f"Company: {state.company_name}"]

    if state.domain:
        parts.append(f"Domain: {state.domain}")

    if state.messages:
        parts.append("\n--- Research conversation ---")
        for msg in state.messages:
            role = type(msg).__name__.replace("Message", "")
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if content.strip():
                parts.append(f"{role}: {content[:1000]}")

    if state.tools_used:
        parts.append(f"\nTools used: {', '.join(set(state.tools_used))}")

    return "\n".join(parts)

