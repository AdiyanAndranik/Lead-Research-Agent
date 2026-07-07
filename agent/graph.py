import logging
from langgraph.graph import StateGraph, END
from agent.state import ResearchState
from agent.nodes.research_node import research_node
from agent.nodes.summarize_node import summarize_node

logger = logging.getLogger(__name__)


def should_continue(state: ResearchState) -> str:
    """
    Routing function - decides whether to continue researching or summarize.
    """
    if state.error:
        return "summarize"
    if state.iteration_count >= state.max_iterations:
        return "summarize"
    if state.is_complete:
        return END
    return "summarize"


def build_research_graph() -> StateGraph:
    """
    Build and compile the research agent graph.

    Graph topology:
    START → research → should_continue → summarize → END
                            ↓
                          END (on error or max iterations)
    """
    graph = StateGraph(ResearchState)

    graph.add_node("research", research_node)
    graph.add_node("summarize", summarize_node)

    graph.set_entry_point("research")

    graph.add_conditional_edges(
        "research",
        should_continue,
        {
            "summarize": "summarize",
            END: END
        },
    )

    graph.add_edge("summarize", END)

    return graph.compile()


research_graph = build_research_graph()