from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from openai import BadRequestError

from app.services.llm import get_llm
from app.state import ResearchState, SubtopicResult
from app.tools.tavily_search import tavily_search

TOOLS = [tavily_search]
SYSTEM = """You are a research assistant. Collect sources on the given subtopic using the available tools.
Call tavily_search to find web results. Collect at least 3 sources."""


def _add_source(item: dict, sources: list[dict], seen_urls: set[str]) -> None:
    url = item.get("url", "")
    if url and url not in seen_urls:
        seen_urls.add(url)
        sources.append(item)


async def researcher_node(state: ResearchState, subtopic: str) -> dict:
    llm = get_llm().bind_tools(TOOLS)
    messages = [
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"Research this subtopic thoroughly: {subtopic}"),
    ]

    sources: list[dict] = []
    seen_urls: set[str] = set()

    for _ in range(4):
        try:
            response = await llm.ainvoke(messages)
        except BadRequestError:
            # Model failed to produce a valid tool call (common with some Groq models).
            # Fall back to a direct search so the pipeline still gets results.
            fallback = await tavily_search.ainvoke({"query": subtopic})
            if isinstance(fallback, list):
                for item in fallback:
                    _add_source(item, sources, seen_urls)
            break

        messages.append(response)

        if not response.tool_calls:
            break

        for call in response.tool_calls:
            tool = next((t for t in TOOLS if t.name == call["name"]), None)
            if tool is None:
                continue
            result = await tool.ainvoke(call["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
            if isinstance(result, list):
                for item in result:
                    _add_source(item, sources, seen_urls)

    result: SubtopicResult = {"subtopic": subtopic, "sources": sources, "summary": ""}
    return {"results": [result]}
