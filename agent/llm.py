from langchain_groq import ChatGroq
from backend.app.core.config import settings


def get_research_llm() -> ChatGroq:
    """
    LLM for the research agent.
    Uses Llama 3.3 70B on Groq — fast and free tier available.
    """
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0,        # deterministic for research tasks
        max_tokens=4096,
    )


def get_scoring_llm() -> ChatGroq:
    """
    LLM for scoring — same model, slightly higher temperature
    to allow nuanced reasoning.
    """
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=2048,
    )


def get_email_llm() -> ChatGroq:
    """
    LLM for email generation — higher temperature for creativity.
    """
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.4,
        max_tokens=1024,
    )
