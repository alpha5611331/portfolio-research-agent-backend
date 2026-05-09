from app.services.llm import get_llm
from app.state import ResearchState

SYSTEM = """You are a research synthesizer. Merge the subtopic summaries into a structured report with:
## Executive Summary
## Key Findings
## Detailed Analysis (one section per subtopic)
## References

Be comprehensive, analytical, and cite sources throughout."""


async def synthesizer_node(state: ResearchState) -> dict:
    llm = get_llm()

    summaries = "\n\n".join(f"### {r['subtopic']}\n{r['summary']}" for r in state["results"])
    all_sources = [s for r in state["results"] for s in r["sources"]]
    sources_list = "\n".join(f"- {s['url']}: {s['title']}" for s in all_sources)

    response = await llm.ainvoke(
        [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": f"Query: {state['query']}\n\nSubtopic Summaries:\n{summaries}\n\nAll Sources:\n{sources_list}",
            },
        ]
    )
    report = response.content

    return {"report": report}
