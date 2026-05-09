from app.state import ResearchState
from app.services.llm import get_llm

SYSTEM = """You are a research summarizer. Given a subtopic and its collected sources, write a clear,
concise 2-3 paragraph summary. Include key facts, cite sources by URL where relevant."""


async def summarizer_node(state: ResearchState) -> dict:
    llm = get_llm()
    updated_results = []

    for result in state["results"]:
        sources_text = "\n".join(
            f"- [{s['title']}]({s['url']}): {s['snippet']}" for s in result["sources"]
        )
        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": f"Subtopic: {result['subtopic']}\n\nSources:\n{sources_text}",
            },
        ])
        updated_results.append({**result, "summary": response.content})

    return {"results": updated_results}
