# ADR-001: Tech Stack Decision

**Project:** Lead Research & Outreach Agent  


---

## Context

We are building a production-grade agentic AI pipeline that:
- Ingests company leads from multiple input formats
- Autonomously researches each company using multiple tools
- Scores lead quality using an LLM with structured reasoning
- Generates personalized outreach emails with human review
- Exports results to CRMs and triggers email sends

---

## Decisions

### Backend: Python + FastAPI

**Chosen:** Python 3.12 + FastAPI 0.110+

| Alternative | Reason rejected |
|-------------|----------------|
| Django | Too much overhead for an API-first service |
| Node.js + Express | Python has a significantly better AI/ML ecosystem; LangGraph is Python-native |
| Flask | No async support out of the box; lacks automatic OpenAPI generation |

FastAPI gives us native async/await (critical for concurrent LLM calls), automatic OpenAPI docs at `/docs`, and deep Pydantic v2 integration — the same models used for request validation are reused for LLM structured output.

---

### Agent Orchestration: LangGraph

**Chosen:** LangGraph 0.2+

| Alternative | Reason rejected |
|-------------|----------------|
| LangChain AgentExecutor | Deprecated pattern; no explicit state management |
| CrewAI | Less control over graph edges; better suited to roleplay-style multi-agent |
| AutoGen | Heavier; better suited to conversational multi-agent scenarios |

LangGraph gives us an explicit state machine where every node, edge, and state transition is visible and debuggable. Conditional routing (score ≥ 7 → generate email, else → deprioritize) is a first-class feature. LangSmith tracing works out of the box.

---

### LLM Provider: Groq (Llama 3.3 70B)

**Chosen:** Groq API — free tier — running Llama 3.3 70B Instruct

| Alternative | Reason rejected |
|-------------|----------------|
| OpenAI GPT-4o | Paid; no meaningful free tier for development |
| Anthropic Claude | Paid; no free tier |
| Ollama local | Unpredictable quality on structured tasks; requires GPU |

Groq's free tier provides fast inference (up to 500k tokens/day) on Llama 3.3 70B, which performs at GPT-4-level on structured output tasks. The LangChain-Groq integration is a drop-in replacement for any other provider.

---

### Database: PostgreSQL + SQLAlchemy + Alembic

**Chosen:** PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic

| Alternative | Reason rejected |
|-------------|----------------|
| SQLite | Not suitable for concurrent async workers |
| MongoDB | Structured data benefits from relational integrity |

PostgreSQL JSONB columns store variable-length research results and LLM outputs. Alembic migrations give us version-controlled schema changes. SQLAlchemy 2.0 async keeps DB calls non-blocking.

---

### Task Queue: Celery + Redis

**Chosen:** Celery 5.3+ + Redis 7

| Alternative | Reason rejected |
|-------------|----------------|
| FastAPI BackgroundTasks | In-process only; no persistence or retry logic |
| RQ | Simpler but fewer features |
| Kafka | Massive overkill for this scale |

Each lead becomes an independent Celery task — parallelizable, retriable with exponential backoff, with dead-letter handling for persistent failures. Redis doubles as queue broker and caching layer.

---

### Web Scraping: Playwright + BeautifulSoup

**Chosen:** Playwright (headless browser) + BeautifulSoup (HTML parsing)

| Alternative | Reason rejected |
|-------------|----------------|
| Scrapy | Heavy framework; overkill for per-lead scraping |
| Requests + lxml | Cannot handle JavaScript-rendered pages |
| Selenium | Slower than Playwright; older API |

Playwright handles JS-rendered sites (React/Next.js homepages) that `requests` cannot reach. BeautifulSoup handles HTML extraction cleanly.

---

### Tech Detection: python-wappalyzer (open source)

**Chosen:** python-wappalyzer (community library, free)

| Alternative | Reason rejected |
|-------------|----------------|
| Wappalyzer API | Paid after free tier |
| BuiltWith API | Paid |

python-wappalyzer runs Wappalyzer's open-source detection rules locally with no API cost. Sufficient for detecting frontend frameworks, analytics tools, CRM signals.

---

### News Search: Serper API

**Chosen:** Serper API — free tier (100 searches/month)

| Alternative | Reason rejected |
|-------------|----------------|
| Google Custom Search API | 100 queries/day free but complex setup |
| SerpAPI | Paid after trial |
| DuckDuckGo scraping | Against ToS; fragile |

Serper provides a clean JSON API over Google Search results. 100 free searches/month is sufficient for a portfolio project.

---

### Observability: LangSmith + structlog

**Chosen:** LangSmith (free developer tier) + structlog

| Alternative | Reason rejected |
|-------------|----------------|
| LangFuse | Good alternative; LangSmith has tighter LangGraph integration |
| Raw print logging | Not parseable; no search or aggregation |

LangSmith traces every LLM call with inputs, outputs, latency, and token usage. structlog produces JSON-structured logs compatible with any log aggregator.

---

### Frontend: React + Vite + TanStack

**Chosen:** React 18 + Vite + TanStack Table + React Query

| Alternative | Reason rejected |
|-------------|----------------|
| Next.js | SSR not needed for a dashboard application |
| Streamlit | Looks like a prototype, not a product |
| Plain HTML | No component model; unmaintainable at dashboard scale |

---

### Containerization: Docker + Docker Compose

**Chosen:** Docker + Docker Compose v2

Single `docker compose up` spins up the entire stack. Same Compose file (with overrides) targets production. Eliminates environment inconsistency.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│         (Vite + TanStack + React Query)              │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / WebSocket
┌────────────────────▼────────────────────────────────┐
│                FastAPI Backend                       │
│         (REST API + WebSocket server)                │
└──────┬─────────────┬──────────────┬─────────────────┘
       │             │              │
┌──────▼───┐  ┌──────▼──┐  ┌───────▼─────────────────┐
│ Postgres │  │  Redis  │  │    Celery Workers         │
│          │  │         │  │  ┌─────────────────────┐  │
└──────────┘  └─────────┘  │  │  LangGraph Agent    │  │
                            │  │  ┌───────────────┐  │  │
                            │  │  │ Web scraper   │  │  │
                            │  │  │ News search   │  │  │
                            │  │  │ Tech detect   │  │  │
                            │  │  └───────────────┘  │  │
                            │  │   Groq API calls     │  │
                            │  └─────────────────────┘  │
                            └───────────────────────────┘
```

---

*Next: ADR-002 — Agent state design and LangGraph graph topology.*