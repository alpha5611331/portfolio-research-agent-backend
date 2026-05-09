import json

from app.services.llm import get_llm
from app.state import ResearchState

SYSTEM = """You are a research planner. Given a research question, break it into 3-5 focused subtopics.
Return ONLY a JSON array of subtopic strings. Example: ["subtopic 1", "subtopic 2", "subtopic 3"]"""


async def planner_node(state: ResearchState) -> dict:
    llm = get_llm()
    response = await llm.ainvoke([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Research question: {state['query']}"},
    ])
    try:
        subtopics = json.loads(response.content)
        if not isinstance(subtopics, list):
            subtopics = [state["query"]]
    except (json.JSONDecodeError, Exception):
        subtopics = [state["query"]]

    return {"subtopics": subtopics[:5]}
