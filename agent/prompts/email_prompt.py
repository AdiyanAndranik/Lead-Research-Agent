EMAIL_SYSTEM_PROMPT = """You are an expert B2B cold email copywriter for an AI engineer.

The sender's profile:
- Name: {sender_name}
- Role: AI Engineer & Automation Specialist
- Core offer: Production-grade AI agents, RAG pipelines, and automation systems
- Track record: Helps startups cut manual workflows by 60-80%
- Style: Direct, specific, no fluff — engineers talk to engineers

Rules for every email:
1. Subject line: 6 words max, specific to THIS company, no clickbait
2. Opening: Reference something SPECIFIC about the company (not generic praise)
3. Pain: Name a specific pain point they likely have based on research
4. Value: One concrete thing the sender can do for them
5. CTA: One soft ask — a call, a question, or a reply
6. Length: 80-120 words for body. Shorter is better.
7. NO: "I hope this finds you well", "I came across your company", "synergy", "leverage"
8. NO: Generic AI buzzwords — be specific about what you'd actually build

Tone guide:
- conversational: casual but professional, like a peer reaching out
- formal: respectful and structured, appropriate for enterprise contacts
- brief: extremely short, 3-4 sentences max, get to the point immediately"""


def build_email_prompt(
    company_name: str,
    company_description: str | None,
    product_offering: str | None,
    pain_points: list[str],
    tech_signals: list[str],
    funding_signals: str | None,
    score_reasoning: str | None,
    tone: str,
    angle: str,
    sender_name: str = "Gor",
) -> str:
    pain_str = "\n".join(f"- {p}" for p in pain_points[:3]) if pain_points else "- Manual workflows likely based on product type"
    tech_str = ", ".join(tech_signals[:5]) if tech_signals else "Not detected"

    angle_instructions = {
        "pain": "Lead with the pain point. Make them feel understood before offering anything.",
        "opportunity": "Lead with a specific opportunity or outcome they could achieve.",
        "social_proof": "Lead with a relevant result or pattern you've seen with similar companies.",
    }

    return f"""Write 3 cold email variants for this lead.

COMPANY: {company_name}
WHAT THEY DO: {company_description or 'Not available'}
PRODUCT: {product_offering or 'Not available'}
PAIN POINTS: 
{pain_str}
TECH STACK: {tech_str}
RECENT SIGNALS: {funding_signals or 'None found'}
SCORE REASONING: {score_reasoning or 'Strong ICP fit'}

SENDER NAME: {sender_name}
TONE: {tone}
ANGLE FOR ALL 3 VARIANTS: {angle_instructions.get(angle, angle_instructions['pain'])}

CRITICAL REQUIREMENTS:
- Each email body should be 50-100 words. Concise and specific beats long and generic.
- Reference {company_name} specifically by name at least once in the body
- Use at least 2 specific details from the research above
- Never use phrases like "companies like yours" or "similar companies" — be specific
- The CTA must be a specific question, not a generic "let's chat"

Write exactly 3 variants:
- Variant 1 (pain_first): Open with their specific pain, then offer solution, then specific CTA
- Variant 2 (opportunity_first): Open with a concrete outcome they could achieve, then how, then CTA
- Variant 3 (social_proof_first): Open with a specific result pattern, connect to {company_name}, then CTA

Respond ONLY in this JSON format:
{{
  "variants": [
    {{
      "variant": "pain_first",
      "subject_line": "subject here — max 6 words, specific to {company_name}",
      "body": "full email body here — MUST be 80-120 words",
      "personalization_signals": ["specific detail used 1", "specific detail used 2"]
    }},
    {{
      "variant": "opportunity_first", 
      "subject_line": "subject here — max 6 words",
      "body": "full email body here — MUST be 80-120 words",
      "personalization_signals": ["specific detail used 1", "specific detail used 2"]
    }},
    {{
      "variant": "social_proof_first",
      "subject_line": "subject here — max 6 words", 
      "body": "full email body here — MUST be 80-120 words",
      "personalization_signals": ["specific detail used 1", "specific detail used 2"]
    }}
  ]
}}"""