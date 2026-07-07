from typing import Annotated, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel


class ResearchState(BaseModel):
    """
    Full state of the research agent for one lead.
    Every field is immutable per step — LangGraph creates a new state copy on each transition.
    """

    # Lead identity
    lead_id: str
    company_name: str
    domain: str | None = None
    linkedin_url: str | None = None

    # Message history — add_messages handles merging
    messages: Annotated[list[BaseMessage], add_messages] = []

    # Tool outputs — populated as tools run
    homepage_content: str | None = None
    about_content: str | None = None
    news_results: list[dict] = []
    tech_stack: dict = {}

    # Final research summary — populated by summarize_node
    company_description: str | None = None
    product_offering: str | None = None
    pain_points: list[str] = []
    funding_signals: str | None = None
    size_estimate: str | None = None
    industry: str | None = None

    # Execution metadata
    tools_used: list[str] = []
    iteration_count: int = 0
    max_iterations: int = 3
    error: str | None = None
    is_complete: bool = False

    class ConfigDict:
        arbitrary_types_allowed = True

        