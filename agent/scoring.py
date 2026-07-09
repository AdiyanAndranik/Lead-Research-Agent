import json
import logging
from agent.llm import get_scoring_llm
from agent.schemas.scoring import ScoreOutput, DimensionScore
from agent.prompts.scoring_prompt import SCORING_SYSTEM_PROMPT, build_scoring_prompt
from agent.retry_utils import with_groq_retry

logger = logging.getLogger(__name__)


def _calculate_weighted_score(
    icp: int,
    pain: int,
    tech: int,
    timing: int,
    budget: int,
) -> int:
    """
    Calculate weighted overall score.
    ICP(30%) + Pain(25%) + Tech(20%) + Timing(15%) + Budget(10%)
    """
    weighted = (
        icp * 0.30
        + pain * 0.25
        + tech * 0.20
        + timing * 0.15
        + budget * 0.10
    )
    return round(weighted)


@with_groq_retry(max_retries=4, base_delay=15.0)
async def _call_scoring_llm(llm, messages: list) -> str:
    response = await llm.ainvoke(messages)
    return response.content


async def score_lead(
    company_name: str,
    research: dict,
    min_score_threshold: int = 6,
) -> ScoreOutput:
    """
    Score a lead using LLM with structured output.

    Args:
        company_name: Name of the company
        research: Dict of research results from ResearchResult model
        min_score_threshold: Minimum score to trigger email generation

    Returns:
        ScoreOutput with all dimension scores and reasoning
    """
    logger.info(f"Scoring lead: {company_name}")

    llm = get_scoring_llm()

    prompt = build_scoring_prompt(
        company_name=company_name,
        company_description=research.get("company_description"),
        product_offering=research.get("product_offering"),
        industry=research.get("industry"),
        size_estimate=research.get("size_estimate"),
        pain_points=research.get("pain_points") or [],
        funding_signals=research.get("funding_signals"),
        tech_signals=research.get("tech_signals") or [],
        recent_news=None,
        min_score_threshold=min_score_threshold,
    )

    from langchain_core.messages import HumanMessage, SystemMessage
    messages = [
        SystemMessage(content=SCORING_SYSTEM_PROMPT),
        HumanMessage(content=prompt + "\n\nRespond ONLY in this JSON format:\n" + _score_json_schema()),
    ]

    raw = await _call_scoring_llm(llm, messages)

    try:
        data = _parse_json_response(raw)
        return _build_score_output(data, min_score_threshold)
    except Exception as e:
        logger.error(f"Failed to parse scoring response for {company_name}: {e}\nRaw: {raw}")
        return _fallback_score(company_name, min_score_threshold)


def _score_json_schema() -> str:
    return """{
  "icp_fit_score": 7,
  "icp_fit_reasoning": "explanation",
  "pain_alignment_score": 8,
  "pain_alignment_reasoning": "explanation",
  "tech_maturity_score": 6,
  "tech_maturity_reasoning": "explanation",
  "timing_score": 7,
  "timing_reasoning": "explanation",
  "budget_signal_score": 6,
  "budget_signal_reasoning": "explanation",
  "overall_reasoning": "2-3 sentence summary of why this lead scored this way",
  "recommended_action": "one of: prioritize / nurture / deprioritize",
  "confidence": 0.85
}"""


def _parse_json_response(raw: str) -> dict:
    """Parse LLM response, stripping markdown fences if present."""
    clean = raw.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else clean
        if clean.startswith("json"):
            clean = clean[4:]
    return json.loads(clean.strip())


def _build_score_output(data: dict, min_score_threshold: int) -> ScoreOutput:
    """Build a validated ScoreOutput from parsed LLM response."""
    icp = max(1, min(10, int(data.get("icp_fit_score", 5))))
    pain = max(1, min(10, int(data.get("pain_alignment_score", 5))))
    tech = max(1, min(10, int(data.get("tech_maturity_score", 5))))
    timing = max(1, min(10, int(data.get("timing_score", 5))))
    budget = max(1, min(10, int(data.get("budget_signal_score", 5))))

    overall = _calculate_weighted_score(icp, pain, tech, timing, budget)
    passed = overall >= min_score_threshold

    return ScoreOutput(
        overall_score=overall,
        confidence=float(data.get("confidence", 0.7)),
        icp_fit=DimensionScore(
            score=icp,
            reasoning=data.get("icp_fit_reasoning", ""),
        ),
        pain_alignment=DimensionScore(
            score=pain,
            reasoning=data.get("pain_alignment_reasoning", ""),
        ),
        tech_maturity=DimensionScore(
            score=tech,
            reasoning=data.get("tech_maturity_reasoning", ""),
        ),
        timing=DimensionScore(
            score=timing,
            reasoning=data.get("timing_reasoning", ""),
        ),
        budget_signal=DimensionScore(
            score=budget,
            reasoning=data.get("budget_signal_reasoning", ""),
        ),
        overall_reasoning=data.get("overall_reasoning", ""),
        recommended_action=data.get("recommended_action", "nurture"),
        passed_threshold=passed,
    )


def _fallback_score(company_name: str, min_score_threshold: int) -> ScoreOutput:
    """
    Fallback score when LLM parsing fails.
    Returns a conservative mid-range score.
    """
    logger.warning(f"Using fallback score for {company_name}")
    dim = DimensionScore(score=5, reasoning="Could not parse LLM response")
    return ScoreOutput(
        overall_score=5,
        confidence=0.1,
        icp_fit=dim,
        pain_alignment=dim,
        tech_maturity=dim,
        timing=dim,
        budget_signal=dim,
        overall_reasoning="Scoring failed — manual review required",
        recommended_action="nurture",
        passed_threshold=5 >= min_score_threshold,
    )
