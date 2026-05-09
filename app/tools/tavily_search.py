from langchain_core.tools import tool
from tavily import TavilyClient

from app.config import settings


@tool
def tavily_search(query: str) -> list[dict]:
    """Search the web for current information on a topic."""
    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(query=query, max_results=5, include_raw_content=False)
    return [
        {
            "url": r["url"],
            "title": r.get("title", ""),
            "snippet": r.get("content", ""),
            "score": r.get("score", 0.0),
        }
        for r in response.get("results", [])
    ]
