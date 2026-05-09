from langchain_core.tools import tool
from app.db.qdrant_client import get_client
from app.services.embeddings import get_embeddings
from app.config import settings


@tool
async def qdrant_rag(query: str) -> list[dict]:
    """Retrieve semantically similar past research from Qdrant."""
    embeddings = get_embeddings()
    vector = await embeddings.aembed_query(query)
    client = get_client()
    results = await client.search(
        collection_name=settings.qdrant_collection,
        query_vector=vector,
        limit=3,
        score_threshold=0.7,
    )
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
