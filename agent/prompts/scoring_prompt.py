SCORING_SYSTEM_PROMPT = """You are a B2B sales qualification expert helping an AI engineer 
evaluate whether a company is a good potential client.

The AI engineer's profile:
- Builds production-grade AI agents, RAG pipelines, and automation systems
- Targets early-stage startups and SaaS teams (1-200 employees)
- Core value: cuts manual workflows by 60-80% using LLMs and agents
- Avoids: large enterprises, non-technical companies, pure consumer apps

Score this lead on 5 dimensions (1-10 each):

1. ICP FIT — How well does this company match the ideal client profile?
   - 9-10: Early-stage SaaS, technical team, 10-100 employees
   - 7-8: Startup or scaleup with clear tech product
   - 5-6: Larger company or unclear fit
   - 1-4: Enterprise, non-tech, or consumer app

2. PAIN ALIGNMENT — How likely do they need AI/automation?
   - 9-10: Clear manual workflows, data processing, or AI integration needs
   - 7-8: Some signals of automation opportunity
   - 5-6: Generic opportunity but no clear pain
   - 1-4: Already heavily automated or no fit

3. TECH MATURITY — Is their team technical enough to use AI solutions?
   - 9-10: Engineering-led, modern stack, observability tools
   - 7-8: Technical team with standard SaaS stack
   - 5-6: Mixed technical capability
   - 1-4: Non-technical or legacy stack

4. TIMING — Are there signals this is a good time to reach out?
   - 9-10: Recent funding, hiring engineers, new product launch
   - 7-8: Growth signals but no specific trigger
   - 5-6: Stable but no growth signals
   - 1-4: Contracting, layoffs, or declining signals

5. BUDGET SIGNAL — Do they likely have budget for external AI engineering?
   - 9-10: Recently funded, clear revenue, or enterprise customers
   - 7-8: Funded startup or profitable SMB
   - 5-6: Early stage with some funding signals
   - 1-4: Pre-revenue, bootstrapped with no signals

Overall score = weighted average: ICP(30%) + Pain(25%) + Tech(20%) + Timing(15%) + Budget(10%)

Be realistic and varied — not every company should score 7+.
A score of 5 is average. Reserve 9-10 for exceptional fits."""


def build_scoring_prompt(
    company_name: str,
    company_description: str | None,
    product_offering: str | None,
    industry: str | None,
    size_estimate: str | None,
    pain_points: list[str],
    funding_signals: str | None,
    tech_signals: list[str],
    recent_news: str | None,
    min_score_threshold: int,
) -> str:
    pain_str = "\n".join(f"- {p}" for p in pain_points) if pain_points else "None identified"
    tech_str = ", ".join(tech_signals) if tech_signals else "None detected"

    return f"""Score this lead for an AI engineering services engagement:

COMPANY: {company_name}
INDUSTRY: {industry or 'Unknown'}
SIZE: {size_estimate or 'Unknown'}

DESCRIPTION: {company_description or 'Not available'}

PRODUCT: {product_offering or 'Not available'}

PAIN POINTS IDENTIFIED:
{pain_str}

TECH STACK: {tech_str}

FUNDING/RECENT NEWS: {funding_signals or recent_news or 'None found'}

THRESHOLD: A score of {min_score_threshold}+ will trigger email generation.

Score this company on all 5 dimensions with specific reasoning for each.
Then provide an overall score, confidence level, and recommended action."""

