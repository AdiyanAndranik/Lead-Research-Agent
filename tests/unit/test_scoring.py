import pytest
from agent.scoring import _calculate_weighted_score, _build_score_output, _fallback_score


def test_weighted_score_calculation():
    # All 10s should give 10
    assert _calculate_weighted_score(10, 10, 10, 10, 10) == 10


def test_weighted_score_all_fives():
    assert _calculate_weighted_score(5, 5, 5, 5, 5) == 5


def test_weighted_score_high_icp():
    # High ICP (30% weight) should pull score up
    score = _calculate_weighted_score(10, 5, 5, 5, 5)
    assert score > 5


def test_weighted_score_low_budget_minimal_impact():
    # Budget is only 10% — low budget shouldn't kill the score
    high = _calculate_weighted_score(8, 8, 8, 8, 8)
    low_budget = _calculate_weighted_score(8, 8, 8, 8, 1)
    assert high - low_budget <= 2


def test_build_score_output_passes_threshold():
    data = {
        "icp_fit_score": 8,
        "icp_fit_reasoning": "Good ICP fit",
        "pain_alignment_score": 8,
        "pain_alignment_reasoning": "Clear pain",
        "tech_maturity_score": 7,
        "tech_maturity_reasoning": "Modern stack",
        "timing_score": 7,
        "timing_reasoning": "Recent funding",
        "budget_signal_score": 7,
        "budget_signal_reasoning": "Series A",
        "overall_reasoning": "Strong fit overall",
        "recommended_action": "prioritize",
        "confidence": 0.9,
    }
    result = _build_score_output(data, min_score_threshold=6)
    assert result.overall_score >= 6
    assert result.passed_threshold is True
    assert result.recommended_action == "prioritize"


def test_build_score_output_fails_threshold():
    data = {
        "icp_fit_score": 3,
        "icp_fit_reasoning": "Poor fit",
        "pain_alignment_score": 3,
        "pain_alignment_reasoning": "No pain",
        "tech_maturity_score": 3,
        "tech_maturity_reasoning": "Legacy stack",
        "timing_score": 3,
        "timing_reasoning": "Contracting",
        "budget_signal_score": 3,
        "budget_signal_reasoning": "No budget",
        "overall_reasoning": "Poor fit",
        "recommended_action": "deprioritize",
        "confidence": 0.8,
    }
    result = _build_score_output(data, min_score_threshold=6)
    assert result.overall_score < 6
    assert result.passed_threshold is False


def test_fallback_score():
    result = _fallback_score("TestCo", min_score_threshold=6)
    assert result.overall_score == 5
    assert result.confidence == 0.1
    assert result.passed_threshold is False


def test_score_clamped_to_valid_range():
    # Even if LLM returns out-of-range values, they get clamped
    data = {
        "icp_fit_score": 15,  # too high
        "icp_fit_reasoning": "r",
        "pain_alignment_score": -1,  # too low
        "pain_alignment_reasoning": "r",
        "tech_maturity_score": 5,
        "tech_maturity_reasoning": "r",
        "timing_score": 5,
        "timing_reasoning": "r",
        "budget_signal_score": 5,
        "budget_signal_reasoning": "r",
        "overall_reasoning": "r",
        "recommended_action": "nurture",
        "confidence": 0.5,
    }
    result = _build_score_output(data, min_score_threshold=6)
    assert 1 <= result.icp_fit.score <= 10
    assert 1 <= result.pain_alignment.score <= 10