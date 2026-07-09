import logging
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from agent.state import ResearchState
from agent.llm import get_research_llm
from agent.tools.web_scraper import scrape_homepage, scrape_about_page
from agent.tools.news_search import search_company_news, search_company_funding
from agent.tools.tech_detector import detect_tech_stack
from agent.retry_utils import with_groq_retry

logger = logging.getLogger(__name__)

RESEARCH_TOOLS = [
    scrape_homepage,
    scrape_about_page,
    search_company_news,
    search_company_funding,
    detect_tech_stack,
]

SYSTEM_PROMPT = """You are a B2B sales research agent. Your job is to research companies 
to help an AI engineer identify potential clients who need AI/automation services.

For each company you research:
1. Scrape their homepage to understand what they do
2. Search for recent news (funding, product launches, growth signals)
3. Detect their tech stack to assess technical maturity
4. If the company seems interesting, also scrape their about page

Focus on finding:
- What the company does and their core product
- Company size signals (headcount, funding stage)
- Pain points that AI/automation could solve
- Recent growth or change signals (new funding, hiring, pivots)
- Technical sophistication of their team

Be efficient — use 2-4 tools maximum per company. Stop when you have enough context."""


@with_groq_retry(max_retries=4, base_delay=15.0)
async def _call_llm_with_retry(llm_with_tools, messages):
    """LLM call wrapped with rate limit retry logic."""
    return await llm_with_tools.ainvoke(messages)


async def research_node(state: ResearchState) -> dict:
    """
    Main research node — uses LLM with tools to research a company.
    """
    logger.info(f"Research node: {state.company_name}")

    llm = get_research_llm()
    llm_with_tools = llm.bind_tools(RESEARCH_TOOLS)

    domain_info = f" (website: {state.domain})" if state.domain else ""
    user_message = HumanMessage(
        content=f"Research this company for me: {state.company_name}{domain_info}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        user_message,
    ] + state.messages

    tools_used = list(state.tools_used)
    iteration = state.iteration_count

    while iteration < state.max_iterations:
        try:
            response = await _call_llm_with_retry(llm_with_tools, messages)
        except Exception as e:
            logger.error(f"LLM call failed after retries: {e}")
            return {
                "messages": messages[2:],
                "tools_used": tools_used,
                "iteration_count": iteration,
                "error": str(e),
            }

        messages.append(response)
        iteration += 1

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tools_used.append(tool_name)

            logger.info(f"Calling tool: {tool_name} with {tool_args}")
            tool_result = await _execute_tool(tool_name, tool_args)

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )

    return {
        "messages": messages[2:],
        "tools_used": tools_used,
        "iteration_count": iteration,
    }


async def _execute_tool(tool_name: str, tool_args: dict) -> str:
    tool_map = {
        "scrape_homepage": scrape_homepage,
        "scrape_about_page": scrape_about_page,
        "search_company_news": search_company_news,
        "search_company_funding": search_company_funding,
        "detect_tech_stack": detect_tech_stack,
    }
    tool_fn = tool_map.get(tool_name)
    if not tool_fn:
        return f"Unknown tool: {tool_name}"
    try:
        return str(await tool_fn.ainvoke(tool_args))
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return f"Tool {tool_name} failed: {str(e)}"
    