from app.state import ResearchState
from app.services.llm import get_llm
from app.db.qdrant_client import get_client
from app.services.embeddings import get_embeddings
from app.config import settings
from qdrant_client.models import PointStruct
import uuid

SYSTEM = """You are a research synthesizer. Merge the subtopic summaries into a structured report with:
## Executive Summary
## Key Findings
## Detailed Analysis (one section per subtopic)
## References

Be comprehensive, analytical, and cite sources throughout."""


async def synthesizer_node(state: ResearchState) -> dict:
    llm = get_llm(state["provider"], state["model"])

    summaries = "\n\n".join(
        f"### {r['subtopic']}\n{r['summary']}" for r in state["results"]
    )
    all_sources = [s for r in state["results"] for s in r["sources"]]
    sources_list = "\n".join(f"- {s['url']}: {s['title']}" for s in all_sources)

    response = await llm.ainvoke([
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": f"Query: {state['query']}\n\nSubtopic Summaries:\n{summaries}\n\nAll Sources:\n{sources_list}",
        },
    ])
    report = response.content

    await _index_in_qdrant(state, report, all_sources)

    return {"report": report}


async def _index_in_qdrant(state: ResearchState, report: str, sources: list[dict]) -> None:
    try:
        embeddings = get_embeddings()
        client = get_client()
        vector = await embeddings.aembed_query(report[:2000])
        await client.upsert(
            collection_name=settings.qdrant_collection,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "session_id": state["session_id"],
                        "query": state["query"],
                        "text": report[:1000],
                        "url": sources[0]["url"] if sources else "",
                        "title": f"Research: {state['query'][:60]}",
                    },
                )
            ],
        )
    except Exception:
        pass
