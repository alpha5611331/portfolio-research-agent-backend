from langchain_core.tools import tool

from app.config import settings
from app.db.qdrant_client import get_client
from app.services.embeddings import get_embeddings


@tool
async def qdrant_rag(query: str) -> list[dict]:
    """Retrieve semantically similar past research from Qdrant."""
    embeddings = get_embeddings()
    vector = await embeddings.aembed_query(query)
    client = get_client()
    response = await client.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        limit=3,
        score_threshold=0.7,
    )
    results = response.points
    return [
        {
            "url": hit.payload.get("url", ""),
            "title": hit.payload.get("title", "Past Research"),
            "snippet": hit.payload.get("text", ""),
            "score": hit.score,
            "source": "qdrant",
        }
        for hit in results
    ]
