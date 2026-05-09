from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from app.state import ResearchState
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.summarizer import summarizer_node
from app.agents.synthesizer import synthesizer_node


def fan_out(state: ResearchState) -> list[Send]:
    return [Send("researcher", {**state, "_subtopic": st}) for st in state["subtopics"]]


async def researcher_wrapper(state: ResearchState) -> dict:
    subtopic = state.get("_subtopic", state["subtopics"][0])
    return await researcher_node(state, subtopic)


def build_graph() -> StateGraph:
    builder = StateGraph(ResearchState)

    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_wrapper)
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("synthesizer", synthesizer_node)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges("planner", fan_out, ["researcher"])
    builder.add_edge("researcher", "summarizer")
    builder.add_edge("summarizer", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()


graph = build_graph()
