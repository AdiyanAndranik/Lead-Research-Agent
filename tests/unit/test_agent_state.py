from agent.state import ResearchState


def test_initial_state():
    state = ResearchState(
        lead_id="test-id",
        company_name="Linear",
        domain="linear.app",
    )
    assert state.company_name == "Linear"
    assert state.domain == "linear.app"
    assert state.iteration_count == 0
    assert state.is_complete is False
    assert state.messages == []
    assert state.tools_used == []


def test_state_defaults():
    state = ResearchState(
        lead_id="test-id",
        company_name="Stripe",
    )
    assert state.domain is None
    assert state.max_iterations == 3
    assert state.pain_points == []
    assert state.tech_stack == {}


def test_state_with_all_fields():
    state = ResearchState(
        lead_id="test-id",
        company_name="Notion",
        domain="notion.so",
        industry="Productivity",
        size_estimate="500-1000 employees",
        pain_points=["manual workflows", "poor integrations"],
        tools_used=["scrape_homepage", "search_company_news"],
        iteration_count=2,
        is_complete=True,
    )
    assert state.industry == "Productivity"
    assert len(state.pain_points) == 2
    assert state.iteration_count == 2
    assert state.is_complete is True