from typing import Annotated

from typing_extensions import TypedDict


class SubtopicResult(TypedDict):
    subtopic: str
    sources: list[dict]
    summary: str


def merge_results(a: list[SubtopicResult], b: list[SubtopicResult]) -> list[SubtopicResult]:
    return a + b


class ResearchState(TypedDict):
    query: str
    session_id: str
    subtopics: list[str]
    results: Annotated[list[SubtopicResult], merge_results]
    report: str
    error: str | None
