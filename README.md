# Research Agent — Backend

FastAPI + LangGraph multi-agent backend for the [AI Research Command Center](https://github.com/alpha5611331/portfolio-research-agent-backend).

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Agent framework | LangGraph `StateGraph` |
| LLM | `langchain-openai` (`ChatOpenAI`) — OpenAI + Groq via `base_url` |
| Web search | Tavily Python client |
| Vector DB | Qdrant (`qdrant-client`) |
| Streaming | WebSocket + LangGraph `.astream_events()` |
| Validation | Pydantic v2 + pydantic-settings |
| Package manager | uv |
| Linter | Ruff |
| Tests | pytest + pytest-asyncio |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Qdrant running at `localhost:6333` (Docker: `docker run -p 6333:6333 qdrant/qdrant`)
- API keys: OpenAI, Groq, Tavily

## Setup

```bash
uv sync
cp .env.example .env  # fill in your keys
```

## Environment Variables

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=research_sessions
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

## Run

```bash
uv run uvicorn main:app --reload --port 8000
```

## API

```
POST   /api/research          Submit query → returns session_id
GET    /api/research/{id}     Get full session result
GET    /api/sessions          List past sessions
DELETE /api/sessions/{id}     Delete session

WS     /ws/{session_id}       Real-time agent event stream
```

### WebSocket Event Schema

```json
{
  "event": "PLAN_CREATED | SEARCH_DONE | RAG_DONE | SOURCES_COLLECTED | SUMMARY_CHUNK | SUMMARY_DONE | REPORT_CHUNK | REPORT_DONE | ERROR",
  "session_id": "uuid",
  "timestamp": "ISO-8601",
  "agent": "planner | researcher | summarizer | synthesizer",
  "subtopic": "optional string",
  "data": {}
}
```

## Agent Pipeline

```
START → planner → [Send × N subtopics] → researcher (×N, parallel)
                                              ↓ (merge)
                                          summarizer
                                              ↓
                                          synthesizer → END
```

Each Researcher node runs a tool-calling loop with two LangChain tools:
- `tavily_search` — web search via Tavily API
- `qdrant_rag` — semantic retrieval from past research sessions

## Development

```bash
# Lint + format
uv run ruff check .
uv run ruff format .

# Tests
uv run pytest
```
