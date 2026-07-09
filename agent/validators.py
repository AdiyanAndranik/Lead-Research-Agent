import logging
from agent.state import ResearchState

logger = logging.getLogger(__name__)

# Minimum content required for a valid research result
MIN_DESCRIPTION_LENGTH = 30
MIN_PAIN_POINTS = 1


class ResearchValidationResult:
    def __init__(self, is_valid: bool, issues: list[str], quality_score: float):
        self.is_valid = is_valid
        self.issues = issues
        self.quality_score = quality_score  # 0.0 to 1.0


def validate_research_result(state: dict) -> ResearchValidationResult:
    """
    Validate that the research summary has minimum required quality.
    Returns a validation result with quality score and any issues found.
    """
    issues = []
    score_components = []

    # Check company description
    description = state.get("company_description") or ""
    if len(description) < MIN_DESCRIPTION_LENGTH:
        issues.append("Company description too short or missing")
        score_components.append(0.0)
    else:
        score_components.append(1.0)

    # Check product offering
    product = state.get("product_offering") or ""
    if not product:
        issues.append("Product offering missing")
        score_components.append(0.0)
    else:
        score_components.append(1.0)

    # Check industry
    industry = state.get("industry") or ""
    if not industry:
        issues.append("Industry classification missing")
        score_components.append(0.5)
    else:
        score_components.append(1.0)

    # Check pain points
    pain_points = state.get("pain_points") or []
    if len(pain_points) < MIN_PAIN_POINTS:
        issues.append("No pain points identified")
        score_components.append(0.0)
    else:
        score_components.append(1.0)

    # Check tools were actually used
    tools_used = state.get("tools_used") or []
    if len(tools_used) < 2:
        issues.append("Too few research tools used — research may be incomplete")
        score_components.append(0.3)
    else:
        score_components.append(1.0)

    quality_score = sum(score_components) / len(score_components)
    is_valid = quality_score >= 0.5 and "Company description too short or missing" not in issues

    if issues:
        logger.warning(
            f"Research validation issues: {issues} "
            f"(quality score: {quality_score:.2f})"
        )
    else:
        logger.info(f"Research validation passed (quality score: {quality_score:.2f})")

    return ResearchValidationResult(
        is_valid=is_valid,
        issues=issues,
        quality_score=quality_score,
    )

