from agent.validators import validate_research_result


def make_state(**kwargs):
    defaults = {
        "company_description": "Retool is a platform for building internal tools quickly.",
        "product_offering": "A drag-and-drop builder for internal dashboards and admin panels.",
        "industry": "DevTools",
        "size_estimate": "200-500 employees",
        "pain_points": ["slow internal tool development", "engineering bottleneck"],
        "funding_signals": "Series C $45M raised",
        "tech_signals": ["React", "AWS"],
        "tools_used": ["scrape_homepage", "search_company_news", "detect_tech_stack"],
    }
    defaults.update(kwargs)
    return defaults


def test_valid_research_passes():
    result = validate_research_result(make_state())
    assert result.is_valid is True
    assert result.quality_score >= 0.8
    assert result.issues == []


def test_missing_description_fails():
    result = validate_research_result(make_state(company_description=""))
    assert result.is_valid is False
    assert any("description" in i for i in result.issues)


def test_missing_product_lowers_score():
    result = validate_research_result(make_state(product_offering=""))
    assert result.quality_score < 1.0
    assert any("product" in i.lower() for i in result.issues)


def test_no_pain_points_fails():
    result = validate_research_result(make_state(pain_points=[]))
    assert any("pain points" in i for i in result.issues)


def test_few_tools_lowers_score():
    result = validate_research_result(make_state(tools_used=["scrape_homepage"]))
    assert result.quality_score < 1.0


def test_quality_score_range():
    result = validate_research_result(make_state())
    assert 0.0 <= result.quality_score <= 1.0