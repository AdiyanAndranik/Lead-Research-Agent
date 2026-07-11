import json
import logging
from agent.llm import get_email_llm
from agent.schemas.email import EmailDraftOutput, EmailGenerationOutput
from agent.prompts.email_prompt import EMAIL_SYSTEM_PROMPT, build_email_prompt
from agent.retry_utils import with_groq_retry

logger = logging.getLogger(__name__)


def _count_words(text: str) -> int:
    return len(text.split())


def _check_quality(body: str, personalization_signals: list[str]) -> list[str]:
    """
    Run quality checks on a generated email.
    Returns list of quality flags (warnings).
    """
    flags = []

    words = _count_words(body)
    if words > 150:
        flags.append(f"Too long ({words} words — aim for 80-120)")
    if words < 40:
        flags.append(f"Too short ({words} words — aim for 40-120)")

    # Check for banned phrases
    banned = [
        "i hope this finds you",
        "i came across",
        "synergy",
        "leverage",
        "touch base",
        "circle back",
        "game changer",
        "revolutionary",
        "cutting-edge",
    ]
    body_lower = body.lower()
    for phrase in banned:
        if phrase in body_lower:
            flags.append(f"Contains banned phrase: '{phrase}'")

    # Check personalization
    if len(personalization_signals) < 2:
        flags.append("Low personalization — fewer than 2 specific signals used")

    return flags


def _parse_email_response(raw: str) -> list[dict]:
    """Parse LLM response into list of email variant dicts."""
    clean = raw.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else clean
        if clean.startswith("json"):
            clean = clean[4:]
    data = json.loads(clean.strip())
    return data.get("variants", [])


@with_groq_retry(max_retries=4, base_delay=15.0)
async def _call_email_llm(llm, messages: list) -> str:
    response = await llm.ainvoke(messages)
    return response.content


async def generate_emails(
    company_name: str,
    research: dict,
    score_reasoning: str | None,
    tone: str = "conversational",
    angle: str = "pain",
    sender_name: str = "And",
) -> EmailGenerationOutput:
    """
    Generate 3 personalized email variants for a lead.

    Args:
        company_name: Name of the company
        research: Research results dict
        score_reasoning: Why the lead scored well (used for context)
        tone: Email tone (conversational/formal/brief)
        angle: Primary angle (pain/opportunity/social_proof)
        sender_name: Name to sign emails with

    Returns:
        EmailGenerationOutput with 3 variants and quality flags
    """
    logger.info(f"Generating emails for: {company_name}")

    llm = get_email_llm()

    prompt = build_email_prompt(
        company_name=company_name,
        company_description=research.get("company_description"),
        product_offering=research.get("product_offering"),
        pain_points=research.get("pain_points") or [],
        tech_signals=research.get("tech_signals") or [],
        funding_signals=research.get("funding_signals"),
        score_reasoning=score_reasoning,
        tone=tone,
        angle=angle,
        sender_name=sender_name,
    )

    from langchain_core.messages import HumanMessage, SystemMessage
    messages = [
        SystemMessage(content=EMAIL_SYSTEM_PROMPT.format(sender_name=sender_name)),
        HumanMessage(content=prompt),
    ]

    raw = await _call_email_llm(llm, messages)

    try:
        variants_data = _parse_email_response(raw)
        drafts = []
        all_flags = []

        for v in variants_data:
            body = v.get("body", "")
            signals = v.get("personalization_signals", [])
            flags = _check_quality(body, signals)
            all_flags.extend(flags)

            drafts.append(EmailDraftOutput(
                variant=v.get("variant", "unknown"),
                subject_line=v.get("subject_line", ""),
                body=body,
                word_count=_count_words(body),
                personalization_signals=signals,
            ))

        # Primary variant matches the requested angle
        angle_to_variant = {
            "pain": "pain_first",
            "opportunity": "opportunity_first",
            "social_proof": "social_proof_first",
        }
        primary = angle_to_variant.get(angle, "pain_first")

        return EmailGenerationOutput(
            drafts=drafts,
            primary_variant=primary,
            quality_flags=list(set(all_flags)),
        )

    except Exception as e:
        logger.error(f"Email generation failed for {company_name}: {e}\nRaw: {raw}")
        return _fallback_email(company_name, sender_name)


def _fallback_email(company_name: str, sender_name: str) -> EmailGenerationOutput:
    """Fallback when email generation fails."""
    body = (
        f"Hi,\n\n"
        f"I noticed {company_name} is building something interesting. "
        f"I help startups ship AI features faster — agents, RAG pipelines, automation. "
        f"Worth a quick chat?\n\n"
        f"Best,\n{sender_name}"
    )
    draft = EmailDraftOutput(
        variant="pain_first",
        subject_line=f"AI engineering for {company_name}",
        body=body,
        word_count=_count_words(body),
        personalization_signals=[company_name],
    )
    return EmailGenerationOutput(
        drafts=[draft],
        primary_variant="pain_first",
        quality_flags=["Fallback email used — generation failed"],
    )

